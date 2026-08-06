"""Local dQ/dV interpolation (standalone; no pne_studio dependency)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


def _odd_window(window: int, n: int, poly: int) -> int:
    win = int(window)
    if win % 2 == 0:
        win += 1
    max_win = n if n % 2 == 1 else n - 1
    win = min(win, max_win)
    win = max(win, poly + 2 + ((poly + 2) % 2 == 0))
    if win % 2 == 0:
        win += 1
    if win > n:
        return 0
    return win


def _savgol(y: np.ndarray, window: int, poly: int) -> np.ndarray:
    win = _odd_window(window, len(y), poly)
    if win < poly + 2:
        return y.copy()
    return savgol_filter(y, window_length=win, polyorder=min(poly, win - 1), mode="interp")


def _capacity_has_reset(q: np.ndarray, drop: float = 1.0) -> bool:
    if len(q) < 4:
        return False
    dq = np.diff(q)
    return bool(np.any(dq < -abs(drop)))


def _interp_unique(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(x)
    x, y = x[order], y[order]
    # collapse duplicate x (keep last)
    keep = np.ones(len(x), dtype=bool)
    keep[:-1] = np.diff(x) > 1e-9
    return x[keep], y[keep]


def build_dqdv_from_segment(
    raw: pd.DataFrame,
    v_col: str,
    q_col: str,
    *,
    axis: str = "Q",
    num_points: int = 500,
    use_interp: bool = True,
    deriv_mode: str = "smooth_then_diff",
    sg_window: int = 21,
    sg_poly: int = 3,
) -> pd.DataFrame:
    """Build interpolated V/Q + dQ/dV + dV/dQ table from one leg segment.

    Returns empty DataFrame on failure. Columns: voltage, capacity, dQ/dV, dV/dQ.
    """
    empty = pd.DataFrame(columns=["voltage", "capacity", "dQ/dV", "dV/dQ"])
    if raw is None or raw.empty or v_col not in raw.columns or q_col not in raw.columns:
        return empty

    v = pd.to_numeric(raw[v_col], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(raw[q_col], errors="coerce").to_numpy(dtype=float)
    m = np.isfinite(v) & np.isfinite(q)
    v, q = v[m], q[m]
    if len(v) < 4:
        return empty

    axis_u = str(axis).strip().upper()
    n_pts = max(int(num_points), 2)

    # Mid-leg capacity counter reset → fall back to V-axis (discharge Q reset)
    if axis_u == "Q" and _capacity_has_reset(q):
        axis_u = "V"

    if axis_u == "Q":
        # Monotonic absolute capacity from leg start
        q_abs = np.abs(q - q[0])
        x, y = _interp_unique(q_abs, v)  # x=Q, y=V
        if len(x) < 4:
            return empty
        if use_interp:
            xg = np.linspace(float(x.min()), float(x.max()), n_pts)
            yg = np.interp(xg, x, y)
        else:
            xg, yg = x, y
        if deriv_mode == "smooth_then_diff":
            yg_s = _savgol(yg, sg_window, sg_poly)
            xg_s = _savgol(xg, sg_window, sg_poly)
        else:
            yg_s, xg_s = yg, xg
        dv = np.gradient(yg_s)
        dq = np.gradient(xg_s)
        with np.errstate(divide="ignore", invalid="ignore"):
            dvdq = np.where(np.abs(dq) > 1e-15, dv / dq, np.nan)
            dqdv = np.where(np.abs(dv) > 1e-9, dq / dv, np.nan)
        # fill tiny holes
        if np.isfinite(dqdv).sum() >= 2:
            ok = np.isfinite(dqdv)
            dqdv = np.interp(np.arange(len(dqdv)), np.flatnonzero(ok), dqdv[ok])
        return pd.DataFrame({
            "voltage": yg_s,
            "capacity": xg,
            "dQ/dV": dqdv,
            "dV/dQ": dvdq,
        })

    # V-axis
    x, y = _interp_unique(v, q)  # x=V, y=Q
    if len(x) < 4:
        return empty
    if use_interp:
        xg = np.linspace(float(x.min()), float(x.max()), n_pts)
        yg = np.interp(xg, x, y)
    else:
        xg, yg = x, y
    if deriv_mode == "smooth_then_diff":
        yg_s = _savgol(yg, sg_window, sg_poly)
        xg_s = _savgol(xg, sg_window, sg_poly)
    else:
        yg_s, xg_s = yg, xg
    dv = np.gradient(xg_s)
    dq = np.gradient(yg_s)
    with np.errstate(divide="ignore", invalid="ignore"):
        dqdv = np.where(np.abs(dv) > 1e-9, dq / dv, np.nan)
        dvdq = np.where(np.abs(dq) > 1e-15, dv / dq, np.nan)
    if np.isfinite(dqdv).sum() >= 2:
        ok = np.isfinite(dqdv)
        dqdv = np.interp(np.arange(len(dqdv)), np.flatnonzero(ok), dqdv[ok])
    return pd.DataFrame({
        "voltage": xg,
        "capacity": yg_s,
        "dQ/dV": dqdv,
        "dV/dQ": dvdq,
    })
