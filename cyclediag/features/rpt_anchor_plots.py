"""Matplotlib figures for RPT-anchored peak assign visualization."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, prepare_dqdv_arrays, _smooth
from cyclediag.features.dqdv_segment import (
    prepare_leg_segment_for_dqdv,
    split_capacity_runs,
    stitch_capacity_runs,
)
from cyclediag.features.segment_utils import leg_segment

ZONE_COLORS = {
    "hard": "#2E7D32",
    "soft": "#F9A825",
    "interpolated": "#90A4AE",
    "unknown": "#B0BEC5",
}

DEFAULT_CHARGE_PEAKS = ("P2_shoulder", "P3_main", "P4_high")
DEFAULT_DISCHARGE_PEAKS = ("P2_mid", "P3_high")


def _checkpoint_life_cycles(meta: dict[str, Any] | None) -> list[int]:
    if not meta:
        return []
    return [int(c["life_cycle"]) for c in meta.get("checkpoints", [])]


def plot_assign_trajectory(
    assign_df: pd.DataFrame,
    *,
    leg: str = "charge",
    peak_ids: tuple[str, ...] | None = None,
    meta: dict[str, Any] | None = None,
    title: str = "",
) -> Figure:
    """V_expected vs V_observed per peak; background bands for assign zones."""
    work = assign_df[assign_df["leg"] == leg].copy()
    if work.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.set_title("No assign data")
        return fig

    peak_ids = peak_ids or tuple(
        pid for pid in work["peak_id"].dropna().unique()
        if str(pid).startswith("P")
    )
    if leg == "charge":
        peak_ids = tuple(p for p in DEFAULT_CHARGE_PEAKS if p in set(work["peak_id"])) or peak_ids
    else:
        peak_ids = tuple(p for p in DEFAULT_DISCHARGE_PEAKS if p in set(work["peak_id"])) or peak_ids

    fig, ax = plt.subplots(figsize=(11, 5))
    ckpt_lives = _checkpoint_life_cycles(meta)
    ymax = -np.inf
    ymin = np.inf

    for pid in peak_ids:
        sub = work[work["peak_id"] == pid].sort_values("cycle")
        if sub.empty:
            continue
        cyc = sub["cycle"].to_numpy(dtype=float)
        v_exp = sub["V_expected"].to_numpy(dtype=float)
        v_obs = sub["V_observed"].to_numpy(dtype=float)
        zones = sub["assign_zone"].astype(str).to_numpy()

        ax.plot(cyc, v_exp, "--", linewidth=1.0, color="#546E7A", alpha=0.7, label=f"{pid} expected")
        for zone in ("hard", "soft", "interpolated"):
            mask = zones == zone
            if mask.any():
                ax.scatter(
                    cyc[mask], v_obs[mask],
                    s=18, c=ZONE_COLORS[zone], alpha=0.85,
                    label=f"{pid} obs ({zone})" if pid == peak_ids[0] else None,
                    edgecolors="none",
                )
        miss = ~np.isfinite(v_obs)
        if miss.any():
            ax.scatter(
                cyc[miss], v_exp[miss], s=24, facecolors="none",
                edgecolors="#C62828", linewidths=1.2, marker="x",
            )
        ymin = min(ymin, np.nanmin(np.r_[v_exp, v_obs]))
        ymax = max(ymax, np.nanmax(np.r_[v_exp, v_obs]))

    for life in ckpt_lives:
        ax.axvline(life, color="#1565C0", linestyle=":", linewidth=0.9, alpha=0.6)
        ax.axvspan(life - 10, life + 10, color="#1565C0", alpha=0.04)
        ax.text(life, ymax, f" RPT@{life}", fontsize=7, color="#1565C0", va="bottom")

    ax.set_xlabel("Cycle (life)")
    ax.set_ylabel("Peak V (V)")
    ax.set_title(title or f"RPT anchor assign — {leg}")
    ax.grid(True, alpha=0.25)
    legend_handles = [
        Patch(facecolor=ZONE_COLORS["hard"], label="hard ±10"),
        Patch(facecolor=ZONE_COLORS["soft"], label="soft ±30"),
        Patch(facecolor=ZONE_COLORS["interpolated"], label="interpolated"),
    ]
    ax.legend(handles=legend_handles, loc="best", fontsize=8)
    fig.tight_layout()
    return fig


def plot_residual_mv(
    assign_df: pd.DataFrame,
    *,
    leg: str = "charge",
    peak_ids: tuple[str, ...] | None = None,
    title: str = "",
) -> Figure:
    """Residual V_observed − V_expected in mV."""
    work = assign_df[assign_df["leg"] == leg].copy()
    work["residual_mV"] = (work["V_observed"] - work["V_expected"]) * 1000.0
    work = work[np.isfinite(work["residual_mV"])]

    fig, ax = plt.subplots(figsize=(11, 4))
    if work.empty:
        ax.set_title("No residual data")
        return fig

    peak_ids = peak_ids or tuple(sorted(work["peak_id"].dropna().unique()))
    for pid in peak_ids:
        sub = work[work["peak_id"] == pid].sort_values("cycle")
        if sub.empty:
            continue
        ax.plot(sub["cycle"], sub["residual_mV"], marker=".", linewidth=1.0, label=str(pid))

    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axhline(30, color="#EF9A9A", linewidth=0.6, linestyle="--")
    ax.axhline(-30, color="#EF9A9A", linewidth=0.6, linestyle="--")
    ax.set_xlabel("Cycle")
    ax.set_ylabel("V_obs − V_exp (mV)")
    ax.set_title(title or f"Assign residual — {leg}")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def plot_confidence_strip(
    assign_df: pd.DataFrame,
    *,
    leg: str = "charge",
    title: str = "",
) -> Figure:
    """Assign confidence vs cycle (one row per peak_id)."""
    work = assign_df[assign_df["leg"] == leg].copy()
    peak_ids = sorted(work["peak_id"].dropna().unique())
    fig, axes = plt.subplots(len(peak_ids) or 1, 1, figsize=(11, 1.8 * max(len(peak_ids), 1)), sharex=True)
    if not peak_ids:
        axes.set_title("No data")
        return fig
    if len(peak_ids) == 1:
        axes = [axes]

    for ax, pid in zip(axes, peak_ids):
        sub = work[work["peak_id"] == pid].sort_values("cycle")
        colors = [ZONE_COLORS.get(str(z), "#B0BEC5") for z in sub["assign_zone"]]
        ax.scatter(sub["cycle"], sub["assign_confidence"], c=colors, s=22, edgecolors="none")
        ax.set_ylabel(str(pid), fontsize=8)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.2)
    axes[-1].set_xlabel("Cycle")
    fig.suptitle(title or f"Assign confidence — {leg}", fontsize=10)
    fig.tight_layout()
    return fig


def _leg_vq_arrays(df: pd.DataFrame, cycle: int, leg: str) -> tuple[np.ndarray, np.ndarray] | None:
    cyc = df[df["cycle"] == cycle]
    if cyc.empty:
        return None
    seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
    seg = prepare_leg_segment_for_dqdv(seg, leg)
    col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if col not in seg.columns:
        col = "capacity"
    if seg.empty or col not in seg.columns or "voltage" not in seg.columns:
        return None
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
    m = np.isfinite(v) & np.isfinite(q)
    v, q = v[m], q[m]
    if len(v) < 4:
        return None
    return v, q


def _trim_dqdv_edge_artifacts(
    vx: np.ndarray,
    yy: np.ndarray,
    *,
    edge_frac: float = 0.06,
    floor_frac: float = 0.35,
) -> tuple[np.ndarray, np.ndarray]:
    """Drop V-edge points where SG / windowing pulls dQ/dV toward zero."""
    if len(vx) < 30:
        return vx, yy
    order = np.argsort(vx)
    vx, yy = vx[order], yy[order]
    n = len(vx)
    lo = max(2, int(n * edge_frac))
    hi = n - lo
    core = yy[lo:hi]
    peak = float(np.nanmax(np.abs(core))) if len(core) else 0.0
    if peak <= 0:
        return vx, yy
    floor = peak * floor_frac
    keep = np.abs(yy) >= floor
    # Always keep a contiguous middle band if edges are weak.
    if keep.sum() < 20:
        return vx[lo:hi], yy[lo:hi]
    # Keep largest contiguous True run.
    best = (0, 0)
    start = None
    for i, ok in enumerate(keep):
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    if start is not None and len(keep) - start > best[1] - best[0]:
        best = (start, len(keep))
    a, b = best
    if b - a < 20:
        return vx[lo:hi], yy[lo:hi]
    return vx[a:b], yy[a:b]


def _dqdv_curve_from_vq(
    v: np.ndarray,
    q: np.ndarray,
    *,
    sg_window: int = 21,
    interp_axis: str = "Q",
) -> tuple[np.ndarray, np.ndarray] | None:
    dqcfg = DqdvPeakConfig(sg_window=sg_window, interp_axis=interp_axis)
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
    if len(vx) < 5:
        return None
    y = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)
    m = np.isfinite(vx) & np.isfinite(y)
    vx, y = vx[m], y[m]
    if len(vx) < 5:
        return None
    return _trim_dqdv_edge_artifacts(vx, y)


def _leg_dqdv_curve(df: pd.DataFrame, cycle: int, leg: str) -> tuple[np.ndarray, np.ndarray] | None:
    vq = _leg_vq_arrays(df, cycle, leg)
    if vq is None:
        return None
    axis = "V" if leg == "discharge" else "Q"
    return _dqdv_curve_from_vq(*vq, interp_axis=axis)


def leg_voltage_span(df: pd.DataFrame, cycle: int, leg: str) -> float | None:
    """Voltage span of a prepared leg segment, or None if too short."""
    vq = _leg_vq_arrays(df, int(cycle), leg)
    if vq is None:
        return None
    v = vq[0]
    if len(v) < 25:
        return None
    return float(np.nanmax(v) - np.nanmin(v))


def collect_leg_capacity_runs(
    df: pd.DataFrame,
    cycles: list[int] | tuple[int, ...],
    leg: str,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Gather monotonic capacity runs across one or more raw cycles."""
    runs: list[tuple[np.ndarray, np.ndarray]] = []
    for cyc in cycles:
        vq = _leg_vq_arrays(df, int(cyc), leg)
        if vq is None:
            continue
        runs.extend(split_capacity_runs(*vq))
    return runs


def merge_rpt_block_vq(
    df: pd.DataFrame,
    cycles: list[int] | tuple[int, ...],
    leg: str,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Build one continuous V/Q sweep from an RPT/capacheck block.

    Discharge capacheck often splits a full sweep across TC109/110/111 with
    capacity-counter resets. Merging those runs recovers the full V span for
    overlay (e.g. ~4.08→2.50 V instead of a single partial subcycle).
    """
    runs = collect_leg_capacity_runs(df, cycles, leg)
    if not runs:
        return None
    stitched = stitch_capacity_runs(runs, leg=leg)
    if stitched is not None:
        return stitched
    # Fallback: longest single run or single-cycle raw arrays.
    best: tuple[float, np.ndarray, np.ndarray] | None = None
    for vr, qr in runs:
        span = float(np.nanmax(vr) - np.nanmin(vr))
        score = span * 1000.0 + min(len(vr), 500) * 0.1
        if best is None or score > best[0]:
            best = (score, vr, qr)
    if best is None:
        return None
    return best[1], best[2]


def _leg_dqdv_curves_for_cycles(
    df: pd.DataFrame,
    cycles: list[int] | tuple[int, ...] | int,
    leg: str,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return one dQ/dV curve per clean capacity run (no cross-run stitching).

    Stitching Q across RPT subcycles recovers V coverage but injects joint
    spikes into the derivative. Overlay draws each run separately. Capacheck
    discharge forces V-axis interp so each partial sweep keeps its V span.
    """
    if isinstance(cycles, (int, np.integer)):
        curve = _leg_dqdv_curve(df, int(cycles), leg)
        return [curve] if curve is not None else []
    cyc_list = [int(c) for c in cycles]
    runs = collect_leg_capacity_runs(df, cyc_list, leg)
    axis = "V" if leg == "discharge" else "Q"
    curves: list[tuple[np.ndarray, np.ndarray]] = []
    for vr, qr in runs:
        if len(vr) < 25:
            continue
        span = float(np.nanmax(vr) - np.nanmin(vr))
        if span < 0.12:
            continue
        curve = _dqdv_curve_from_vq(vr, qr, interp_axis=axis)
        if curve is None:
            continue
        vx, yy = curve
        ymax = float(np.nanmax(np.abs(yy))) if len(yy) else 0.0
        if not np.isfinite(ymax) or ymax < 3.0:
            continue
        curves.append((vx, yy))
    if curves:
        # Cover high→low V with complementary runs (capacheck is split in V).
        curves.sort(key=lambda c: (-float(np.nanmax(c[0])), -float(np.nanmax(np.abs(c[1])))))
        kept: list[tuple[np.ndarray, np.ndarray]] = []
        covered_lo = np.inf
        for vx, yy in curves:
            lo, hi = float(np.nanmin(vx)), float(np.nanmax(vx))
            amp = float(np.nanmax(np.abs(yy)))
            if amp < 25.0:
                continue
            if not kept:
                kept.append((vx, yy))
                covered_lo = lo
                continue
            if lo < covered_lo - 0.05 and hi >= covered_lo - 0.30:
                # Exclusive V: keep only the portion below already-covered range.
                mask = vx < covered_lo - 0.01
                if mask.sum() < 25:
                    continue
                kept.append((vx[mask], yy[mask]))
                covered_lo = min(covered_lo, float(np.nanmin(vx[mask])))
            if covered_lo <= 2.7 or len(kept) >= 5:
                break
        return kept or curves[:1]
    single = best_rpt_cycle_for_leg(df, cyc_list, leg)
    if single is None:
        return []
    curve = _leg_dqdv_curve(df, single, leg)
    return [curve] if curve is not None else []


def _leg_dqdv_curve_for_cycles(
    df: pd.DataFrame,
    cycles: list[int] | tuple[int, ...] | int,
    leg: str,
) -> tuple[np.ndarray, np.ndarray] | None:
    curves = _leg_dqdv_curves_for_cycles(df, cycles, leg)
    if not curves:
        return None
    # Prefer the widest-V curve (for callers that need a single series).
    return max(curves, key=lambda c: float(np.nanmax(c[0]) - np.nanmin(c[0])))


def best_rpt_cycle_for_leg(
    df: pd.DataFrame,
    candidate_cycles: list[int] | tuple[int, ...],
    leg: str,
) -> int | None:
    """Pick the RPT/capacheck cycle with the richest dQ/dV segment for one leg.

    Prefer a single cycle when it already covers a wide V span (typical charge).
    For fragmented discharge blocks, callers should use ``merge_rpt_block_vq`` /
    ``plot_rpt_routine_dqdv_overlay(..., rpt_cycles=...)`` instead of one cycle.
    """
    best: tuple[float, int] | None = None
    for cyc in candidate_cycles:
        curve = _leg_dqdv_curve(df, int(cyc), leg)
        if curve is None:
            continue
        vx, _y = curve
        if len(vx) < 20:
            continue
        v_span = float(np.nanmax(vx) - np.nanmin(vx))
        score = v_span * 1000.0 + min(len(vx), 500) * 0.1
        if best is None or score > best[0]:
            best = (score, int(cyc))
    return best[1] if best is not None else None


def plot_rpt_routine_dqdv_overlay(
    df: pd.DataFrame,
    *,
    routine_cycle: int,
    rpt_cycle: int | None = None,
    rpt_cycles: list[int] | tuple[int, ...] | None = None,
    leg: str = "charge",
    assign_row: pd.DataFrame | None = None,
    title: str = "",
) -> Figure:
    """Overlay dQ/dV: routine 0.5C vs RPT/capacheck 0.33C at one checkpoint.

    Pass ``rpt_cycles`` (full capacheck block) to stitch fragmented discharge
    sweeps. ``rpt_cycle`` remains for single-cycle charge overlays / labels.
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    rout = _leg_dqdv_curve(df, routine_cycle, leg)

    rpt_curves: list[tuple[np.ndarray, np.ndarray]] = []
    if rpt_cycles is not None and len(list(rpt_cycles)) > 0:
        cyc_list = [int(c) for c in rpt_cycles]
        rpt_curves = _leg_dqdv_curves_for_cycles(df, cyc_list, leg)
        if leg == "discharge" and len(cyc_list) > 1:
            rpt_label = f"RPT block {min(cyc_list)}–{max(cyc_list)}"
        elif rpt_cycle is not None:
            rpt_label = f"RPT TC{int(rpt_cycle)}"
        else:
            rpt_label = f"RPT TC{cyc_list[0]}"
    else:
        if rpt_cycle is None:
            raise ValueError("Provide rpt_cycle or rpt_cycles")
        one = _leg_dqdv_curve(df, int(rpt_cycle), leg)
        if one is not None:
            rpt_curves = [one]
        rpt_label = f"RPT TC{int(rpt_cycle)}"

    if rout is None and not rpt_curves:
        ax.set_title("No dQ/dV data for selected cycles")
        return fig

    if rout is not None:
        ax.plot(rout[0], rout[1], linewidth=1.4, color="#E65100", label=f"routine TC{routine_cycle}")
    for i, (vx, yy) in enumerate(rpt_curves):
        ax.plot(
            vx, yy, linewidth=1.4, color="#1565C0", alpha=0.95 if i == 0 else 0.75,
            label=rpt_label if i == 0 else "_nolegend_",
        )

    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("dQ/dV")
    ax.set_title(title or f"dQ/dV overlay — {leg} (green=expected, red=obs, purple=split)")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.25)

    if assign_row is not None and not assign_row.empty:
        sub = assign_row[
            (assign_row["cycle"] == routine_cycle) & (assign_row["leg"] == leg)
        ]
        y_top = ax.get_ylim()[1]
        for _, row in sub.iterrows():
            v_exp = row.get("V_expected")
            if np.isfinite(v_exp):
                ax.axvline(float(v_exp), color="#2E7D32", linestyle="--", linewidth=0.9, alpha=0.7)
            v_obs = row.get("V_observed")
            method = str(row.get("assign_method", ""))
            if np.isfinite(v_obs):
                color = "#6A1B9A" if method == "rpt_window_split" else "#C62828"
                ax.axvline(float(v_obs), color=color, linestyle="-", linewidth=1.0, alpha=0.75)
                pid = str(row.get("peak_id", ""))
                ax.text(float(v_obs), y_top, f" {pid}", fontsize=6, color=color, rotation=90, va="top")

    fig.tight_layout()
    return fig
