"""Three-parameter discharge curve fit — separates scale (LAM), offset (LLI), dR (impedance)."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import least_squares

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, DEFAULT_DQDV_PEAK_CONFIG, compute_dvdq


def _fit_weights(q: np.ndarray, v: np.ndarray, config: DqdvPeakConfig) -> np.ndarray:
    """w_k = 1 / (1 + (|dV/dQ|_k / median(|dV/dQ|))^2) — down-weight cliff ends."""
    qx, dvdq = compute_dvdq(q, v, config)
    if len(qx) < 5:
        return np.ones(len(q), dtype=float)
    mag = np.abs(dvdq)
    med = float(np.nanmedian(mag[np.isfinite(mag) & (mag > 0)]))
    if not np.isfinite(med) or med <= 0:
        med = 1.0
    w_grid = 1.0 / (1.0 + (mag / med) ** 2)
    # map back to reference q nodes via interpolation
    q_ref = np.asarray(q, dtype=float)
    order = np.argsort(q_ref)
    qr, wr = qx, w_grid
    if len(qr) < 2:
        return np.ones(len(q_ref), dtype=float)
    return np.interp(q_ref[order], qr, wr, left=wr[0], right=wr[-1])


def _model_v(q: np.ndarray, v_ref: np.ndarray, q_ref: np.ndarray, s: float, o: float, dR_mohm: float, i_a: float) -> np.ndarray:
    """V_N(Q) ≈ interp(V_ref, s·Q + o) − I·ΔR [V]."""
    q_shift = s * q + o
    v_interp = np.interp(q_shift, q_ref, v_ref, left=np.nan, right=np.nan)
    return v_interp - abs(i_a) * (dR_mohm / 1000.0)


def fit_curve_three_param(
    q_ref: np.ndarray,
    v_ref: np.ndarray,
    q_n: np.ndarray,
    v_n: np.ndarray,
    *,
    I_A: float,
    config: DqdvPeakConfig | None = None,
) -> dict[str, Any]:
    """Fit V_N(Q) ≈ V_ref(s·Q + o) − I·ΔR on discharge curves (same leg, same rate only).

    Returns scale, offset, dR, residual metrics, corr_s_o, degenerate_flag, r2.
    """
    cfg = config or DEFAULT_DQDV_PEAK_CONFIG
    out: dict[str, Any] = {
        "dchg_fit_scale": None,
        "dchg_fit_offset": None,
        "dchg_fit_dR": None,
        "dchg_fit_residual_rms": None,
        "dchg_fit_residual_max": None,
        "dchg_fit_residual_argmax_SOC": None,
        "dchg_fit_r2": None,
        "dchg_fit_corr_s_o": None,
        "dchg_fit_degenerate_flag": False,
        "LLI_vs_R_ratio": None,
    }

    q_ref = np.asarray(q_ref, dtype=float)
    v_ref = np.asarray(v_ref, dtype=float)
    q_n = np.asarray(q_n, dtype=float)
    v_n = np.asarray(v_n, dtype=float)
    m = np.isfinite(q_ref) & np.isfinite(v_ref)
    q_ref, v_ref = q_ref[m], v_ref[m]
    m2 = np.isfinite(q_n) & np.isfinite(v_n)
    q_n, v_n = q_n[m2], v_n[m2]
    if len(q_ref) < 20 or len(q_n) < 20:
        return out

    order_r = np.argsort(q_ref)
    q_ref, v_ref = q_ref[order_r], v_ref[order_r]
    order_n = np.argsort(q_n)
    q_n, v_n = q_n[order_n], v_n[order_n]
    qmax = float(np.nanmax(q_n))
    if qmax <= 1e-9:
        return out

    w = _fit_weights(q_n, v_n, cfg)
    w = np.clip(w, 0.05, 1.0)

    x0 = np.array([1.0, 0.0, 0.0], dtype=float)
    bounds_lo = np.array([0.5, -0.3 * qmax, -5.0])
    bounds_hi = np.array([1.2, 0.3 * qmax, 50.0])

    def residuals(p: np.ndarray) -> np.ndarray:
        s, o, dR = float(p[0]), float(p[1]), float(p[2])
        pred = _model_v(q_n, v_ref, q_ref, s, o, dR, I_A)
        err = np.where(np.isfinite(pred), v_n - pred, 0.0)
        return err * np.sqrt(w)

    try:
        res = least_squares(
            residuals,
            x0,
            bounds=(bounds_lo, bounds_hi),
            loss="soft_l1",
            max_nfev=4000,
        )
    except Exception:
        return out

    s, o, dR = (float(x) for x in res.x)
    pred = _model_v(q_n, v_ref, q_ref, s, o, dR, I_A)
    resid = v_n - pred
    fin = np.isfinite(resid)
    if fin.sum() < 5:
        return out

    r = resid[fin]
    ss_res = float(np.sum(r ** 2))
    ss_tot = float(np.sum((v_n[fin] - np.mean(v_n[fin])) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else None

    # Jacobian for corr(s,o)
    corr_so = None
    deg = False
    try:
        jac = res.jac
        if jac is not None and jac.shape[0] >= 3 and jac.shape[1] >= 2:
            j2 = jac[:, :2]
            c = np.corrcoef(j2.T)[0, 1] if j2.shape[0] > 2 else 0.0
            if np.isfinite(c):
                corr_so = float(c)
                deg = abs(corr_so) > 0.9
    except Exception:
        pass

    argmax_i = int(np.nanargmax(np.abs(resid[fin])))
    q_fin = q_n[fin]
    q_at_max = float(q_fin[argmax_i])
    resid_soc = (1.0 - q_at_max / qmax) * 100.0 if qmax > 0 else None

    rms = float(np.sqrt(np.mean(r ** 2)))
    rmax = float(np.max(np.abs(r)))

    # unit-normalized LLI vs R ratio: |o|/Qmax per mΩ of dR
    lli_r = None
    if abs(dR) > 1e-6:
        lli_r = abs(o) / qmax / (abs(dR) / 1000.0 + 1e-12)

    out.update({
        "dchg_fit_scale": s if not deg else None,
        "dchg_fit_offset": o if not deg else None,
        "dchg_fit_dR": dR,
        "dchg_fit_residual_rms": rms,
        "dchg_fit_residual_max": rmax,
        "dchg_fit_residual_argmax_SOC": resid_soc,
        "dchg_fit_r2": r2,
        "dchg_fit_corr_s_o": corr_so,
        "dchg_fit_degenerate_flag": deg,
        "LLI_vs_R_ratio": lli_r,
    })
    return out
