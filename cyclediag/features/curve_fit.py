"""3-parameter same-leg curve match — IMPROVEMENT_ROADMAP §5.6.

Proxies only (LAM_curve_proxy / LLI_curve_proxy / R_curve_proxy).
Does NOT emit Level-2 ``*_est`` columns (half-cell / template required).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from cyclediag.features.segment_utils import leg_segment


def _leg_vq(
    cycle_df: pd.DataFrame,
    leg: str,
    *,
    rest_current_max: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, float] | None:
    """Return (Q, V, I_med) for one leg. Q ascending."""
    if cycle_df is None or cycle_df.empty:
        return None
    seg = leg_segment(
        cycle_df,
        leg,
        charge_text="charge",
        discharge_text="discharge",
        rest_current_max=rest_current_max,
    )
    if seg.empty or "voltage" not in seg.columns:
        return None
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q_col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if q_col not in seg.columns:
        q_col = "capacity" if "capacity" in seg.columns else None
    if q_col is None:
        return None
    q = pd.to_numeric(seg[q_col], errors="coerce").to_numpy(dtype=float)
    i = None
    if "current" in seg.columns:
        i = pd.to_numeric(seg["current"], errors="coerce").to_numpy(dtype=float)
    m = np.isfinite(v) & np.isfinite(q)
    v, q = v[m], q[m]
    if i is not None:
        i = i[m]
    if len(v) < 10:
        return None
    order = np.argsort(q)
    q, v = q[order], v[order]
    if i is not None:
        i = i[order]
    keep = np.ones(len(q), dtype=bool)
    keep[1:] = np.diff(q) > 1e-9
    q, v = q[keep], v[keep]
    i_med = float(np.nanmedian(np.abs(i[keep]))) if i is not None else 1.0
    if not np.isfinite(i_med) or i_med <= 0:
        i_med = 1.0
    return q, v, i_med


def fit_curve_params(
    q_ref: np.ndarray,
    v_ref: np.ndarray,
    q_n: np.ndarray,
    v_n: np.ndarray,
    *,
    i_n: float = 1.0,
) -> dict[str, Any]:
    """Fit V_N(Q) ≈ V_ref(s·Q + o) - I·dR  (dR in Ω; report mΩ)."""
    empty = {
        "fit_scale": None, "fit_offset": None, "fit_dR": None,
        "fit_residual_rms": None, "fit_residual_max": None,
        "fit_residual_argmax_SOC": None, "fit_r2": None,
        "fit_corr_s_o": None, "fit_degenerate_flag": None,
        "LAM_curve_proxy": None, "LLI_curve_proxy": None, "R_curve_proxy": None,
    }
    q_max = float(np.nanmax(q_ref))
    if not np.isfinite(q_max) or q_max <= 0:
        return empty

    # weights: suppress steep ends
    dv = np.gradient(v_n, q_n)
    med = float(np.nanmedian(np.abs(dv[np.isfinite(dv)]))) if np.isfinite(dv).any() else 1.0
    w = 1.0 / (1.0 + (np.abs(dv) / max(med, 1e-9)) ** 2)
    w = np.where(np.isfinite(w), w, 1.0)

    i_abs = abs(float(i_n)) if np.isfinite(i_n) and i_n != 0 else 1.0

    def resid(p):
        s, o, dr_ohm = p
        q_src = s * q_n + o
        v_model = np.interp(q_src, q_ref, v_ref, left=np.nan, right=np.nan) - i_abs * dr_ohm
        r = (v_n - v_model) * np.sqrt(w)
        return np.where(np.isfinite(r), r, 0.0)

    bounds = (
        [0.5, -0.3 * q_max, -0.005],
        [1.2, 0.3 * q_max, 0.050],
    )
    try:
        sol = least_squares(
            resid, x0=[1.0, 0.0, 0.0], bounds=bounds,
            loss="soft_l1", ftol=1e-8, xtol=1e-8, max_nfev=200,
        )
    except Exception:
        return empty

    s, o, dr_ohm = (float(x) for x in sol.x)
    q_src = s * q_n + o
    v_model = np.interp(q_src, q_ref, v_ref) - i_abs * dr_ohm
    resid_v = v_n - v_model
    m = np.isfinite(resid_v)
    if m.sum() < 10:
        return empty
    rv = resid_v[m]
    ss_res = float(np.sum(rv ** 2))
    ss_tot = float(np.sum((v_n[m] - np.mean(v_n[m])) ** 2))
    i_arg = int(np.argmax(np.abs(rv)))
    q_arg = float(q_n[m][i_arg])
    # Jacobian correlation s vs o
    corr_so = None
    deg = False
    try:
        J = sol.jac
        if J is not None and J.shape[1] >= 2:
            c = np.corrcoef(J[:, 0], J[:, 1])[0, 1]
            if np.isfinite(c):
                corr_so = float(c)
                deg = abs(corr_so) > 0.9
    except Exception:
        pass

    return {
        "fit_scale": s,
        "fit_offset": o,
        "fit_dR": dr_ohm * 1000.0,  # mΩ
        "fit_residual_rms": float(np.sqrt(np.mean(rv ** 2)) * 1000.0),
        "fit_residual_max": float(np.max(np.abs(rv)) * 1000.0),
        "fit_residual_argmax_SOC": (q_arg / float(np.nanmax(q_n))) * 100.0,
        "fit_r2": (1.0 - ss_res / ss_tot) if ss_tot > 1e-15 else None,
        "fit_corr_s_o": corr_so,
        "fit_degenerate_flag": deg or (s >= 1.199) or (s <= 0.501),
        # Bound-saturated scale is not usable LAM evidence — leave null
        "LAM_curve_proxy": (None if (s >= 1.199 or s <= 0.501) else (1.0 - s) * 100.0),
        "LLI_curve_proxy": (o / q_max) * 100.0,
        "R_curve_proxy": dr_ohm * 1000.0,
    }


def attach_curve_fit(
    features: pd.DataFrame,
    raw_df: pd.DataFrame,
    *,
    ref_cycle: int | None,
    rest_current_max: float = 0.5,
    legs: tuple[str, ...] = ("discharge",),
    cycle_list: list[int] | None = None,
) -> pd.DataFrame:
    """Attach same-leg 3-param fit vs baseline (proxies, not *_est)."""
    out = features.copy()
    if ref_cycle is None or raw_df is None or raw_df.empty:
        return out

    ref_raw = raw_df[raw_df["cycle"] == int(ref_cycle)]
    cycles = cycle_list or sorted(int(c) for c in out["cycle"].dropna().unique())

    for leg in legs:
        prefix = "dchg" if leg == "discharge" else "chg"
        keys = [
            f"{prefix}_fit_scale", f"{prefix}_fit_offset", f"{prefix}_fit_dR",
            f"{prefix}_fit_residual_rms", f"{prefix}_fit_residual_max",
            f"{prefix}_fit_residual_argmax_SOC", f"{prefix}_fit_r2",
            f"{prefix}_fit_corr_s_o", f"{prefix}_fit_degenerate_flag",
        ]
        for k in keys:
            if k not in out.columns:
                out[k] = np.nan if "flag" not in k else None
        # shared proxies from discharge preferred
        for k in ("LAM_curve_proxy", "LLI_curve_proxy", "R_curve_proxy"):
            if k not in out.columns:
                out[k] = np.nan

        ref = _leg_vq(ref_raw, leg, rest_current_max=rest_current_max)
        if ref is None:
            continue
        q_ref, v_ref, _ = ref

        for cyc in cycles:
            cur_raw = raw_df[raw_df["cycle"] == int(cyc)]
            cur = _leg_vq(cur_raw, leg, rest_current_max=rest_current_max)
            if cur is None:
                continue
            q_n, v_n, i_n = cur
            # skip SOC-step / pulse cycles — full capa only
            if float(np.nanmax(q_n) - np.nanmin(q_n)) < 40.0:
                continue
            fit = fit_curve_params(q_ref, v_ref, q_n, v_n, i_n=i_n)
            mask = out["cycle"] == int(cyc)
            mapping = {
                f"{prefix}_fit_scale": fit["fit_scale"],
                f"{prefix}_fit_offset": fit["fit_offset"],
                f"{prefix}_fit_dR": fit["fit_dR"],
                f"{prefix}_fit_residual_rms": fit["fit_residual_rms"],
                f"{prefix}_fit_residual_max": fit["fit_residual_max"],
                f"{prefix}_fit_residual_argmax_SOC": fit["fit_residual_argmax_SOC"],
                f"{prefix}_fit_r2": fit["fit_r2"],
                f"{prefix}_fit_corr_s_o": fit["fit_corr_s_o"],
                f"{prefix}_fit_degenerate_flag": fit["fit_degenerate_flag"],
            }
            for k, val in mapping.items():
                out.loc[mask, k] = val
            if leg == "discharge":
                for k in ("LAM_curve_proxy", "LLI_curve_proxy", "R_curve_proxy"):
                    out.loc[mask, k] = fit[k]
    return out
