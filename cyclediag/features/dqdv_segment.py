"""Preprocess charge/discharge leg before dQ/dV (match pne_studio dQ/dV plot prep)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .cc_cv import detect_cv_region, trim_to_cc_end

CAPACITY_RESET_DROP = 0.5  # Ah — mid-leg counter reset threshold
DCIR_PULSE_RATIO = 1.8  # |I|_pulse / |I|_cc — drop high-current DC-IR pulses


def trim_leading_low_capacity(df_part: pd.DataFrame, q_col: str, min_frac: float = 0.005) -> pd.DataFrame:
    if q_col not in df_part.columns or len(df_part) < 4:
        return df_part
    q = pd.to_numeric(df_part[q_col], errors="coerce")
    q_max = q.max()
    if q_max is None or pd.isna(q_max) or float(q_max) <= 0:
        return df_part
    threshold = min_frac * float(q_max)
    start = 0
    for i, val in enumerate(q):
        if pd.notna(val) and float(val) >= threshold:
            start = max(0, i - 1)
            break
    if start > 0:
        return df_part.iloc[start:].copy().reset_index(drop=True)
    return df_part


def exclude_dcir_pulse_rows(
    seg: pd.DataFrame,
    *,
    current_col: str = "current",
    pulse_ratio: float = DCIR_PULSE_RATIO,
    min_active_a: float = 1.0,
) -> pd.DataFrame:
    """Drop high-|I| DC-IR pulse samples interleaved in a discharge leg.

    Capacheck blocks often insert short high-current pulses (~3× C/3) between
    normal CC discharge steps. Those pulses reset capacity counters and corrupt
    dQ/dV. Keep only points near the dominant lower-|I| CC current.
    """
    if seg is None or seg.empty:
        return seg
    col = current_col if current_col in seg.columns else None
    if col is None:
        for cand in ("Current", "AvgCurrent (A)", "current_a"):
            if cand in seg.columns:
                col = cand
                break
    if col is None:
        return seg

    i_abs = pd.to_numeric(seg[col], errors="coerce").abs()
    active = i_abs[i_abs >= float(min_active_a)]
    if len(active) < 30:
        return seg

    i_max = float(active.max())
    cc = active[active < i_max / float(pulse_ratio)]
    if len(cc) < 20:
        return seg

    i_cc = float(cc.median())
    if i_cc <= 0:
        return seg
    # Pulse cluster: clearly above CC (e.g. 77A vs 26A).
    is_pulse = i_abs > i_cc * float(pulse_ratio)
    if not bool(is_pulse.any()):
        return seg
    # Keep CC (+ tiny currents at step edges); drop pulse points.
    out = seg.loc[~is_pulse].copy().reset_index(drop=True)
    return out if len(out) >= 10 else seg


def prepare_leg_segment_for_dqdv(
    seg: pd.DataFrame,
    leg: str,
    *,
    exclude_dcir: bool = True,
) -> pd.DataFrame:
    if seg is None or seg.empty:
        return seg
    q_col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if q_col not in seg.columns:
        q_col = "capacity"
    if q_col not in seg.columns:
        return seg
    out = trim_leading_low_capacity(seg, q_col)
    if leg == "discharge" and exclude_dcir:
        out = exclude_dcir_pulse_rows(out)
    if leg == "charge" and "voltage" in out.columns:
        info = detect_cv_region(
            out,
            v_col="voltage",
            q_col=q_col if q_col in out.columns else None,
            t_col="time" if "time" in out.columns else None,
        )
        out = trim_to_cc_end(out, info, include_boundary=False)
    return out


def split_capacity_runs(
    v: np.ndarray,
    q: np.ndarray,
    *,
    reset_drop: float = CAPACITY_RESET_DROP,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Split V/Q arrays on mid-leg capacity-counter resets."""
    v = np.asarray(v, dtype=float)
    q = np.asarray(q, dtype=float)
    m = np.isfinite(v) & np.isfinite(q)
    v, q = v[m], q[m]
    if len(v) < 2:
        return []
    runs: list[tuple[np.ndarray, np.ndarray]] = []
    start = 0
    for i in range(1, len(q)):
        if q[i] < q[i - 1] - float(reset_drop):
            if i - start >= 2:
                runs.append((v[start:i].copy(), q[start:i].copy()))
            start = i
    if len(q) - start >= 2:
        runs.append((v[start:].copy(), q[start:].copy()))
    return runs


def stitch_capacity_runs(
    runs: list[tuple[np.ndarray, np.ndarray]],
    *,
    leg: str = "discharge",
    min_points: int = 15,
    min_v_span: float = 0.05,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Greedy-cover voltage with monotonic Q runs, then stitch Q continuously.

    Capacheck discharge often spans several TotalCycle values and resets the
    capacity counter between substeps. Overlay/dQ/dV needs one V-ordered
    chain covering high→low V (discharge) or low→high V (charge).
    """
    usable: list[tuple[float, float, float, np.ndarray, np.ndarray]] = []
    for vr, qr in runs:
        if len(vr) < min_points:
            continue
        v_lo, v_hi = float(np.nanmin(vr)), float(np.nanmax(vr))
        span = v_hi - v_lo
        if span < min_v_span:
            continue
        # Prefer more Q transferred in the run.
        q_span = float(np.nanmax(qr) - np.nanmin(qr))
        usable.append((v_hi, v_lo, q_span * span, vr, qr))
    if not usable:
        return None

    if leg == "discharge":
        usable.sort(key=lambda t: (-t[0], -t[2]))  # high V first
    else:
        usable.sort(key=lambda t: (t[1], -t[2]))  # low V first

    selected: list[tuple[np.ndarray, np.ndarray]] = []
    covered_lo = np.inf
    covered_hi = -np.inf
    for v_hi, v_lo, _score, vr, qr in usable:
        if not selected:
            selected.append((vr, qr))
            covered_lo, covered_hi = v_lo, v_hi
            continue
        # Need meaningful new coverage outside current [covered_lo, covered_hi].
        if leg == "discharge":
            extends = v_lo < covered_lo - 0.02
            overlaps_ok = v_hi >= covered_lo - 0.20
        else:
            extends = v_hi > covered_hi + 0.02
            overlaps_ok = v_lo <= covered_hi + 0.20
        if extends and overlaps_ok:
            selected.append((vr, qr))
            covered_lo = min(covered_lo, v_lo)
            covered_hi = max(covered_hi, v_hi)

    if not selected:
        return None

    # Order selected segments along the leg direction.
    if leg == "discharge":
        selected.sort(key=lambda r: -float(np.nanmax(r[0])))
    else:
        selected.sort(key=lambda r: float(np.nanmin(r[0])))

    v_parts: list[np.ndarray] = []
    q_parts: list[np.ndarray] = []
    q_offset = 0.0
    # Exclusive V coverage to avoid backtracking at stitch joints (dQ/dV spikes).
    next_v_limit = np.inf if leg == "discharge" else -np.inf
    for vr, qr in selected:
        if leg == "discharge":
            if float(vr[0]) < float(vr[-1]):
                vr = vr[::-1]
                qr = qr[::-1]
            keep = vr <= next_v_limit
            if keep.sum() < 5:
                continue
            vr, qr = vr[keep], qr[keep]
            next_v_limit = float(vr[-1]) - 1e-4
        else:
            if float(vr[0]) > float(vr[-1]):
                vr = vr[::-1]
                qr = qr[::-1]
            keep = vr >= next_v_limit
            if keep.sum() < 5:
                continue
            vr, qr = vr[keep], qr[keep]
            next_v_limit = float(vr[-1]) + 1e-4

        if float(qr[-1]) < float(qr[0]):
            qr = float(qr[0]) - (qr - float(qr[0]))
            qr = qr - float(qr[0])
        else:
            qr = qr - float(qr[0])
        v_parts.append(vr)
        q_parts.append(qr + q_offset)
        q_offset = float(q_parts[-1][-1])

    if not v_parts:
        return None

    v_out = np.concatenate(v_parts)
    q_out = np.concatenate(q_parts)
    # Drop points that reverse the V trend (keeps stitch joints clean).
    keep = np.zeros(len(v_out), dtype=bool)
    keep[0] = True
    last = float(v_out[0])
    for i in range(1, len(v_out)):
        vv = float(v_out[i])
        if leg == "discharge":
            if vv < last - 1e-6:
                keep[i] = True
                last = vv
        else:
            if vv > last + 1e-6:
                keep[i] = True
                last = vv
    v_out, q_out = v_out[keep], q_out[keep]
    if len(v_out) < 5:
        return None
    return v_out, q_out
