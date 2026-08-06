"""ΔQ(V) statistics — IMPROVEMENT_ROADMAP §5.7 (Severson-style)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

from cyclediag.features.segment_utils import leg_segment


def _discharge_qv(
    cycle_df: pd.DataFrame,
    *,
    rest_current_max: float = 0.5,
) -> tuple[np.ndarray, np.ndarray] | None:
    if cycle_df is None or cycle_df.empty:
        return None
    seg = leg_segment(
        cycle_df,
        "discharge",
        charge_text="charge",
        discharge_text="discharge",
        rest_current_max=rest_current_max,
    )
    if seg.empty or "voltage" not in seg.columns:
        return None
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = None
    for col in ("discharge_capacity", "capacity"):
        if col in seg.columns:
            q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
            break
    if q is None:
        return None
    m = np.isfinite(v) & np.isfinite(q)
    v, q = v[m], q[m]
    if len(v) < 8:
        return None
    # Q(V): sort by V descending for discharge (high→low)
    order = np.argsort(v)[::-1]
    v, q = v[order], q[order]
    keep = np.ones(len(v), dtype=bool)
    keep[1:] = np.abs(np.diff(v)) > 1e-6
    return v[keep], q[keep]


def q_on_v_grid(
    v: np.ndarray,
    q: np.ndarray,
    v_grid: np.ndarray,
) -> np.ndarray:
    # v is descending; interp needs ascending
    order = np.argsort(v)
    return np.interp(v_grid, v[order], q[order])


def common_v_range(
    curves: list[tuple[np.ndarray, np.ndarray]],
    *,
    trim_pct: float = 1.0,
) -> tuple[float, float] | None:
    if not curves:
        return None
    lo = max(float(np.nanpercentile(v, trim_pct)) for v, _ in curves)
    hi = min(float(np.nanpercentile(v, 100.0 - trim_pct)) for v, _ in curves)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi - lo < 0.05:
        return None
    return lo, hi


def dqv_stats(
    q_n: np.ndarray,
    q_ref: np.ndarray,
    v_grid: np.ndarray,
    *,
    ref_cycle: int | None = None,
    eps: float = 1e-12,
) -> dict[str, Any]:
    dQ = q_n - q_ref
    m = np.isfinite(dQ)
    if m.sum() < 10:
        return {
            "dQV_min": None, "dQV_mean": None, "dQV_var": None, "dQV_log_var": None,
            "dQV_skew": None, "dQV_kurtosis": None, "dQV_argmin_V": None,
            "dQV_ref_cycle": ref_cycle, "dQV_valid_V_range": None,
        }
    d = dQ[m]
    vg = v_grid[m]
    var = float(np.var(d))
    i_min = int(np.argmin(d))
    return {
        "dQV_min": float(np.min(d)),
        "dQV_mean": float(np.mean(d)),
        "dQV_var": var,
        "dQV_log_var": float(np.log10(var + eps)),
        "dQV_skew": float(skew(d, bias=False)) if len(d) > 3 else None,
        "dQV_kurtosis": float(kurtosis(d, bias=False, fisher=True)) if len(d) > 3 else None,
        "dQV_argmin_V": float(vg[i_min]),
        "dQV_ref_cycle": ref_cycle,
        "dQV_valid_V_range": float(vg.max() - vg.min()),
    }


def attach_dqv_stats(
    features: pd.DataFrame,
    raw_df: pd.DataFrame,
    *,
    ref_cycle: int | None,
    rest_current_max: float = 0.5,
    n_grid: int = 1000,
    cycle_list: list[int] | None = None,
) -> pd.DataFrame:
    """Attach ΔQ(V) stats vs baseline discharge curve."""
    out = features.copy()
    cols = [
        "dQV_min", "dQV_mean", "dQV_var", "dQV_log_var", "dQV_skew", "dQV_kurtosis",
        "dQV_argmin_V", "dQV_ref_cycle", "dQV_valid_V_range",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = np.nan if c != "dQV_ref_cycle" else None

    if ref_cycle is None or raw_df is None or raw_df.empty:
        return out

    ref_raw = raw_df[raw_df["cycle"] == int(ref_cycle)]
    ref_curve = _discharge_qv(ref_raw, rest_current_max=rest_current_max)
    if ref_curve is None:
        return out

    cycles = cycle_list or sorted(int(c) for c in out["cycle"].dropna().unique())
    sample_curves = [ref_curve]
    # probe a few cycles for common V range
    for c in cycles[:: max(1, len(cycles) // 5)][:5]:
        cur = _discharge_qv(raw_df[raw_df["cycle"] == int(c)], rest_current_max=rest_current_max)
        if cur is not None:
            sample_curves.append(cur)
    vr = common_v_range(sample_curves)
    if vr is None:
        return out
    v_lo, v_hi = vr
    v_grid = np.linspace(v_lo, v_hi, n_grid)
    q_ref = q_on_v_grid(ref_curve[0], ref_curve[1], v_grid)

    for cyc in cycles:
        cur = _discharge_qv(raw_df[raw_df["cycle"] == int(cyc)], rest_current_max=rest_current_max)
        if cur is None:
            continue
        # skip SOC-step / pulse cycles
        if float(np.nanmax(cur[1]) - np.nanmin(cur[1])) < 40.0:
            continue
        q_n = q_on_v_grid(cur[0], cur[1], v_grid)
        stats = dqv_stats(q_n, q_ref, v_grid, ref_cycle=int(ref_cycle))
        mask = out["cycle"] == int(cyc)
        for k, val in stats.items():
            if k not in out.columns:
                continue
            out.loc[mask, k] = val
    return out
