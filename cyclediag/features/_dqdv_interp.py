"""Interpolation helpers for dQ/dV / dV/dQ processing."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

MIN_DV_V_FOR_DQDV = 0.001  # 1 mV — skip |dV| smaller than this after Q-axis interp
CAPACITY_RESET_DROP_AH = 0.5  # Ah — treat as step counter reset within one leg


def resolve_dqdv_interp_axis(
    v: np.ndarray,
    q: np.ndarray,
    axis: str,
    *,
    reset_drop: float = CAPACITY_RESET_DROP_AH,
) -> str:
    """Use V-axis when a leg has mid-step capacity-counter resets.

    PNE raw CSV often resets ``ChargeCapacity`` / ``DischargeCapacity`` between
    substeps (Step Charge, RPT capacheck, DC-IR blocks). Q-uniform interpolation
    then keeps only the first segment and collapses the dQ/dV voltage span.
    """
    axis = str(axis).strip().upper()
    if axis != "Q":
        return axis
    v_arr = np.asarray(v, dtype=float)
    q_arr = np.asarray(q, dtype=float)
    valid = np.isfinite(v_arr) & np.isfinite(q_arr)
    v_arr, q_arr = v_arr[valid], q_arr[valid]
    if len(q_arr) < 4:
        return axis
    if (np.diff(q_arr) < -float(reset_drop)).any():
        return "V"
    return axis


def auto_monotonic(df_part: pd.DataFrame, col: str) -> tuple[pd.DataFrame, str]:
    """Return monotonic subset on *col* (cummax/cummin dedup)."""
    if len(df_part) < 2:
        return df_part.copy(), "increase"
    start_val = df_part[col].iloc[0]
    end_val = df_part[col].iloc[-1]
    direction = "increase" if end_val > start_val else "decrease"

    df_mono = df_part.copy()
    if direction == "increase":
        df_mono["_mono"] = df_mono[col].cummax()
        df_mono = df_mono.drop_duplicates(subset=["_mono"], keep="first")
        return df_mono.drop(columns=["_mono"]), direction
    df_mono["_mono"] = df_mono[col].cummin()
    df_mono = df_mono.drop_duplicates(subset=["_mono"], keep="first")
    return df_mono.drop(columns=["_mono"]), direction


def normalize_deriv_mode(mode: str) -> str:
    """Return ``smooth_then_diff`` or ``diff_then_smooth``."""
    key = str(mode or "").strip().lower().replace(" ", "_")
    if key in ("smooth_then_diff", "state_smooth"):
        return "smooth_then_diff"
    return "diff_then_smooth"


def smooth_state_columns(
    df: pd.DataFrame,
    v_col: str,
    q_col: str,
    *,
    window: int = 21,
    poly: int = 3,
) -> pd.DataFrame:
    """Savitzky-Golay smooth V and Q on a uniform grid before differentiation."""
    out = df.copy()
    w = int(window)
    if w % 2 == 0:
        w += 1
    p = int(poly)
    if w < p + 2:
        w = p + 3 if (p + 3) % 2 else p + 2
    for col in (v_col, q_col):
        if col not in out.columns:
            continue
        y = pd.to_numeric(out[col], errors="coerce").to_numpy(dtype=float)
        if len(y) < 5 or not np.isfinite(y).any():
            continue
        if len(y) < w or len(y) <= p:
            continue
        try:
            out[col] = savgol_filter(y, w, p)
        except ValueError:
            continue
    return out


def interpolate_dqdv_segment(
    df_part: pd.DataFrame,
    v_col: str,
    q_col: str,
    *,
    axis: str = "V",
    num_points: int,
) -> pd.DataFrame:
    """Resample charge/discharge leg for dQ/dV.

    axis ``V`` — uniform voltage grid (legacy).
    axis ``Q`` — uniform capacity grid; reduces high-V knee artifacts.
    """
    if df_part.empty or num_points < 2:
        return df_part.copy()

    axis = str(axis).strip().upper()
    if axis not in ("V", "Q"):
        axis = "V"

    x_col = v_col if axis == "V" else q_col
    y_col = q_col if axis == "V" else v_col

    half_df, direction = auto_monotonic(df_part, x_col)
    if len(half_df) < 2:
        return df_part.copy()

    xp = pd.to_numeric(half_df[x_col], errors="coerce").to_numpy(dtype=float)
    yp = pd.to_numeric(half_df[y_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(xp) & np.isfinite(yp)
    xp, yp = xp[valid], yp[valid]
    if len(xp) < 2:
        return df_part.copy()

    if direction == "increase":
        x_interp = np.linspace(float(xp.min()), float(xp.max()), num_points)
        y_interp = np.interp(x_interp, xp, yp)
    else:
        xp_rev, yp_rev = xp[::-1], yp[::-1]
        x_interp = np.linspace(float(xp_rev.min()), float(xp_rev.max()), num_points)
        y_interp = np.interp(x_interp, xp_rev, yp_rev)
        x_interp, y_interp = x_interp[::-1], y_interp[::-1]

    if axis == "V":
        out = pd.DataFrame({v_col: x_interp, q_col: y_interp})
    else:
        out = pd.DataFrame({v_col: y_interp, q_col: x_interp})
        out = out.sort_values(q_col, kind="mergesort").reset_index(drop=True)
        v_series = pd.to_numeric(out[v_col], errors="coerce")
        if len(v_series) >= 2 and float(v_series.iloc[-1]) >= float(v_series.iloc[0]):
            out["_vmono"] = v_series.cummax()
        else:
            out["_vmono"] = v_series.cummin()
        out = out.drop_duplicates(subset=["_vmono"], keep="first").drop(columns=["_vmono"])
        out = out.reset_index(drop=True)
    return out


def apply_dqdv_derivatives(
    df: pd.DataFrame,
    v_col: str,
    q_col: str,
    *,
    interp_axis: str = "V",
    min_dv: float = MIN_DV_V_FOR_DQDV,
) -> pd.DataFrame:
    """Add dQ/dV and dV/dQ columns; Q-axis mode skips tiny |dV| diffs."""
    out = df.copy()
    out["dV"] = out[v_col].diff()
    out["dQ"] = out[q_col].diff()
    axis = str(interp_axis).strip().upper()
    if axis == "Q":
        dv = out["dV"].abs()
        out["dQ/dV"] = np.where(dv >= min_dv, out["dQ"] / out["dV"], np.nan)
    else:
        out["dQ/dV"] = out["dQ"] / out["dV"]
    out["dV/dQ"] = out["dV"] / out["dQ"]
    out.replace([np.inf, -np.inf], np.nan, inplace=True)
    out.dropna(subset=["dQ/dV", v_col], inplace=True)
    return out


def build_dqdv_from_segment(
    df_part: pd.DataFrame,
    v_col: str,
    q_col: str,
    *,
    axis: str = "Q",
    num_points: int = 500,
    use_interp: bool = True,
    deriv_mode: str = "smooth_then_diff",
    sg_window: int = 21,
    sg_poly: int = 3,
    min_dv: float = MIN_DV_V_FOR_DQDV,
) -> pd.DataFrame:
    """Interpolate (optional), optionally smooth V/Q, then compute dQ/dV."""
    if df_part is None or df_part.empty:
        return pd.DataFrame()

    axis = str(axis).strip().upper()
    if axis not in ("V", "Q"):
        axis = "Q"
    v_series = pd.to_numeric(df_part[v_col], errors="coerce").to_numpy(dtype=float)
    q_series = pd.to_numeric(df_part[q_col], errors="coerce").to_numpy(dtype=float)
    axis = resolve_dqdv_interp_axis(v_series, q_series, axis)
    mode = normalize_deriv_mode(deriv_mode)

    if use_interp:
        grid = interpolate_dqdv_segment(
            df_part, v_col, q_col, axis=axis, num_points=max(int(num_points), 2),
        )
    else:
        grid = df_part.copy()

    if grid.empty or len(grid) < 2:
        return pd.DataFrame()

    work = grid
    if mode == "smooth_then_diff":
        work = smooth_state_columns(
            work, v_col, q_col, window=sg_window, poly=sg_poly,
        )

    return apply_dqdv_derivatives(
        work, v_col, q_col, interp_axis=axis if use_interp else "Q", min_dv=min_dv,
    )
