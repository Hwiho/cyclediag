"""η(SOC) from dual-rate curves + Reff shape fit — IMPROVEMENT_ROADMAP §5.9."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cyclediag.features.segment_utils import leg_segment


def _vq_discharge(
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
    # discharge: Q usually increases; ensure Q ascending for interp
    order = np.argsort(q)
    q, v = q[order], v[order]
    keep = np.ones(len(q), dtype=bool)
    keep[1:] = np.diff(q) > 1e-9
    return q[keep], v[keep]


def eta_curve(
    q_low: np.ndarray,
    v_low: np.ndarray,
    q_high: np.ndarray,
    v_high: np.ndarray,
    *,
    n_grid: int = 200,
) -> dict[str, Any]:
    """Overpotential on shared Q: eta = V_C3 - V_0.5C (discharge)."""
    empty: dict[str, Any] = {
        "eta_SOC20": None, "eta_SOC50": None, "eta_SOC80": None,
        "eta_max": None, "eta_argmax_SOC": None,
        "eta_mean": None, "eta_slope_lowSOC": None,
        "eta_valid": False,
    }
    q_lo = max(float(q_low.min()), float(q_high.min()))
    q_hi = min(float(q_low.max()), float(q_high.max()))
    if not np.isfinite(q_lo) or not np.isfinite(q_hi) or q_hi - q_lo < 1e-3:
        return empty
    qg = np.linspace(q_lo, q_hi, n_grid)
    vl = np.interp(qg, q_low, v_low)
    vh = np.interp(qg, q_high, v_high)
    eta = vl - vh  # C/3 higher V than 0.5C on discharge → eta > 0 typically
    q_tot = q_hi - q_lo
    # SOC from remaining capacity on discharge: SOC=100 at Q=q_lo, 0 at Q=q_hi
    soc = (1.0 - (qg - q_lo) / q_tot) * 100.0

    def at_soc(target: float) -> float | None:
        i = int(np.argmin(np.abs(soc - target)))
        val = float(eta[i])
        return val if np.isfinite(val) else None

    i_max = int(np.nanargmax(np.abs(eta))) if np.isfinite(eta).any() else None
    out = {
        "eta_SOC20": at_soc(20.0),
        "eta_SOC50": at_soc(50.0),
        "eta_SOC80": at_soc(80.0),
        "eta_max": float(eta[i_max]) if i_max is not None else None,
        "eta_argmax_SOC": float(soc[i_max]) if i_max is not None else None,
        "eta_mean": float(np.nanmean(eta)) if np.isfinite(eta).any() else None,
        "eta_slope_lowSOC": None,
        "eta_valid": True,
        "_soc": soc,
        "_eta": eta,
    }
    low = (soc >= 0.0) & (soc <= 30.0) & np.isfinite(eta)
    if low.sum() >= 5:
        slope, _ = np.polyfit(soc[low], eta[low], 1)
        out["eta_slope_lowSOC"] = float(slope)
    return out


def reff_shape_fit(
    eta_soc: dict[float, float],
    r_dcir: dict[float, float],
) -> dict[str, Any]:
    """Fit scale so scale·eta_shape(s) ≈ R_DCIR(s) at SOC 20/50/80."""
    out: dict[str, Any] = {
        "Reff_scale": None,
        "Reff_shape_fit_r2": None,
        "Reff_resid_soc20": None,
        "Reff_resid_soc50": None,
        "Reff_resid_soc80": None,
    }
    socs = (20.0, 50.0, 80.0)
    if 50.0 not in eta_soc or not np.isfinite(eta_soc.get(50.0, np.nan)):
        return out
    eta50 = float(eta_soc[50.0])
    if abs(eta50) < 1e-9:
        return out
    shape = []
    rvals = []
    used = []
    for s in socs:
        if s not in eta_soc or s not in r_dcir:
            continue
        e, r = float(eta_soc[s]), float(r_dcir[s])
        if not (np.isfinite(e) and np.isfinite(r)):
            continue
        shape.append(e / eta50)
        rvals.append(r)
        used.append(s)
    if len(shape) < 2:
        return out
    sh = np.asarray(shape, dtype=float)
    rv = np.asarray(rvals, dtype=float)
    # least squares: scale * shape ≈ R
    denom = float(np.dot(sh, sh))
    if denom < 1e-15:
        return out
    scale = float(np.dot(sh, rv) / denom)
    pred = scale * sh
    ss_res = float(np.sum((rv - pred) ** 2))
    ss_tot = float(np.sum((rv - np.mean(rv)) ** 2))
    out["Reff_scale"] = scale
    out["Reff_shape_fit_r2"] = (1.0 - ss_res / ss_tot) if ss_tot > 1e-15 else None
    for s, resid in zip(used, rv - pred):
        out[f"Reff_resid_soc{int(s)}"] = float(resid)
    return out


def compute_eta_for_pair(
    rpt_df: pd.DataFrame,
    routine_df: pd.DataFrame,
    *,
    rest_current_max: float = 0.5,
    r_dcir_by_soc: dict[float, float] | None = None,
) -> dict[str, Any]:
    """C/3 RPT vs nearest 0.5C routine overpotential (+ optional Reff fit)."""
    low = _vq_discharge(rpt_df, rest_current_max=rest_current_max)
    high = _vq_discharge(routine_df, rest_current_max=rest_current_max)
    if low is None or high is None:
        return {
            "eta_SOC20": None, "eta_SOC50": None, "eta_SOC80": None,
            "eta_max": None, "eta_argmax_SOC": None,
            "eta_mean": None, "eta_slope_lowSOC": None,
            "eta_valid": False,
            "Reff_scale": None, "Reff_shape_fit_r2": None,
            "Reff_resid_soc20": None, "Reff_resid_soc50": None, "Reff_resid_soc80": None,
        }
    eta = eta_curve(low[0], low[1], high[0], high[1])
    result = {k: v for k, v in eta.items() if not k.startswith("_")}
    if r_dcir_by_soc and eta.get("eta_valid"):
        eta_map = {
            20.0: eta.get("eta_SOC20"),
            50.0: eta.get("eta_SOC50"),
            80.0: eta.get("eta_SOC80"),
        }
        eta_map = {k: float(v) for k, v in eta_map.items() if v is not None and np.isfinite(v)}
        result.update(reff_shape_fit(eta_map, r_dcir_by_soc))
    else:
        result.setdefault("Reff_scale", None)
        result.setdefault("Reff_shape_fit_r2", None)
        for s in (20, 50, 80):
            result.setdefault(f"Reff_resid_soc{s}", None)
    return result


def nearest_routine_after_rpt(
    cycles: list[int],
    rpt_cycle: int,
    *,
    exclude: int = 5,
    pulse_set: set[int] | None = None,
) -> int | None:
    """First non-pulse cycle at least `exclude` after RPT block end."""
    pulse_set = pulse_set or set()
    target = int(rpt_cycle) + int(exclude)
    cands = [c for c in cycles if c >= target and c not in pulse_set]
    return min(cands) if cands else None
