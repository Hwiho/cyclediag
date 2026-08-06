"""Signal-based CC/CV detection (label-independent) — IMPROVEMENT_ROADMAP §5.14."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class SignalCvResult:
    has_cv: bool
    cv_start_index: int | None
    chgCCcapa: float | None
    chgCVcapa: float | None
    chgCVtime: float | None
    chgCapa_CCratio: float | None
    chgCapa_CCratio_norm: float | None
    Q_CV_at_Tref: float | None
    tau_CV: float | None
    I_inf_norm: float | None
    cv_detect_method: str
    cv_detect_mismatch_pct: float | None
    column_cv_ah: float | None


def _finite_diff(y: np.ndarray, t: np.ndarray) -> np.ndarray:
    out = np.full_like(y, np.nan, dtype=float)
    if len(y) < 2:
        return out
    dt = np.diff(t)
    dy = np.diff(y)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.where(np.abs(dt) > 1e-12, dy / dt, np.nan)
    out[1:] = d
    out[0] = d[0] if len(d) else np.nan
    return out


def detect_cv_signal(
    seg: pd.DataFrame,
    *,
    v_col: str = "voltage",
    i_col: str | None = None,
    q_col: str | None = None,
    t_col: str | None = None,
    v_cutoff_margin_v: float = 0.015,
    dvdt_max_v_per_min: float = 0.0002,  # 0.2 mV/min
    t_ref_s: float = 1800.0,
    column_cv_ah: float | None = None,
) -> SignalCvResult:
    """Detect CV on a charge leg from V/I/t signals (roadmap §5.14)."""
    empty = SignalCvResult(
        has_cv=False,
        cv_start_index=None,
        chgCCcapa=None,
        chgCVcapa=None,
        chgCVtime=None,
        chgCapa_CCratio=None,
        chgCapa_CCratio_norm=None,
        Q_CV_at_Tref=None,
        tau_CV=None,
        I_inf_norm=None,
        cv_detect_method="failed",
        cv_detect_mismatch_pct=None,
        column_cv_ah=column_cv_ah,
    )
    if seg is None or seg.empty or v_col not in seg.columns:
        return empty

    n = len(seg)
    if n < 8:
        empty.cv_detect_method = "too_short"
        return empty

    if i_col is None:
        for c in ("current", "Current", "AvgCurrent"):
            if c in seg.columns:
                i_col = c
                break
    if t_col is None:
        for c in ("step_time", "time", "StepTime_sec"):
            if c in seg.columns:
                t_col = c
                break
    if q_col is None:
        for c in ("charge_capacity", "capacity"):
            if c in seg.columns:
                q_col = c
                break

    v = pd.to_numeric(seg[v_col], errors="coerce").to_numpy(dtype=float)
    if i_col is None or t_col is None:
        empty.cv_detect_method = "no_current_or_time"
        return empty
    i = pd.to_numeric(seg[i_col], errors="coerce").to_numpy(dtype=float)
    t = pd.to_numeric(seg[t_col], errors="coerce").to_numpy(dtype=float)
    q = (
        pd.to_numeric(seg[q_col], errors="coerce").to_numpy(dtype=float)
        if q_col is not None
        else np.full(n, np.nan)
    )

    v_cut = float(np.nanpercentile(v[np.isfinite(v)], 99))
    didt = _finite_diff(i, t)
    dvdt = _finite_diff(v, t)  # V/s
    dvdt_per_min = dvdt * 60.0

    mask = (
        np.isfinite(v)
        & np.isfinite(i)
        & np.isfinite(t)
        & (v >= v_cut - v_cutoff_margin_v)
        & (didt < 0)
        & (np.abs(dvdt_per_min) < dvdt_max_v_per_min)
    )

    # longest True run
    best_a = best_b = -1
    a = None
    for idx, flag in enumerate(mask):
        if flag and a is None:
            a = idx
        elif not flag and a is not None:
            if best_a < 0 or (idx - a) > (best_b - best_a):
                best_a, best_b = a, idx
            a = None
    if a is not None and (best_a < 0 or (n - a) > (best_b - best_a)):
        best_a, best_b = a, n

    method = "signal"
    if best_a < 0 or best_b - best_a < 3:
        # fallback: current drop below 92% of early median (legacy)
        i_abs = np.abs(i)
        early = i_abs[: max(n // 2, 4)]
        early = early[np.isfinite(early) & (early > 0)]
        if len(early) < 4:
            return empty
        thr = float(np.median(early)) * 0.92
        below = np.isfinite(i_abs) & (i_abs < thr)
        # require near cutoff
        below &= np.isfinite(v) & (v >= v_cut - v_cutoff_margin_v)
        best_a = best_b = -1
        a = None
        for idx, flag in enumerate(below):
            if flag and a is None:
                a = idx
            elif not flag and a is not None:
                if best_a < 0 or (idx - a) > (best_b - best_a):
                    best_a, best_b = a, idx
                a = None
        if a is not None and (best_a < 0 or (n - a) > (best_b - best_a)):
            best_a, best_b = a, n
        method = "current_drop"
        if best_a < 0 or best_b - best_a < 3:
            # still no CV — treat as CC-only
            q_tot = float(np.nanmax(q) - np.nanmin(q)) if np.isfinite(q).sum() >= 2 else None
            empty.chgCCcapa = abs(q_tot) if q_tot is not None else None
            empty.chgCVcapa = 0.0
            empty.chgCVtime = 0.0
            empty.chgCapa_CCratio = 100.0 if empty.chgCCcapa else None
            empty.cv_detect_method = "no_cv"
            if column_cv_ah is not None and column_cv_ah > 0:
                empty.cv_detect_mismatch_pct = 100.0
            return empty

    cv_sl = slice(best_a, best_b)
    t0 = float(t[best_a]) if np.isfinite(t[best_a]) else 0.0
    t1 = float(t[best_b - 1]) if np.isfinite(t[best_b - 1]) else t0
    cv_time = max(0.0, t1 - t0)

    q_start = float(q[0]) if np.isfinite(q[0]) else float(np.nanmin(q))
    q_cc_end = float(q[best_a]) if np.isfinite(q[best_a]) else None
    q_end = float(q[best_b - 1]) if np.isfinite(q[best_b - 1]) else float(np.nanmax(q))
    if q_cc_end is None or not np.isfinite(q_start):
        return empty

    cc_capa = abs(q_cc_end - q_start)
    cv_capa = abs(q_end - q_cc_end)
    total = cc_capa + cv_capa
    cc_ratio = (cc_capa / total * 100.0) if total > 1e-12 else None

    # tau_CV: I = I0*exp(-t/tau) + I_inf on CV window
    tau_cv = None
    i_inf_norm = None
    q_cv_tref = None
    cc_ratio_norm = None
    try:
        tt = t[cv_sl] - t0
        ii = np.abs(i[cv_sl])
        m = np.isfinite(tt) & np.isfinite(ii) & (tt >= 0)
        tt, ii = tt[m], ii[m]
        if len(tt) >= 8 and float(np.nanmax(tt)) > 10:
            from scipy.optimize import curve_fit

            def _f(x, i0, tau, iinf):
                return i0 * np.exp(-x / np.maximum(tau, 1e-3)) + iinf

            i_cc = float(np.nanmedian(np.abs(i[: max(best_a, 4)])))
            p0 = (float(ii[0] - ii[-1]), 200.0, float(ii[-1]))
            popt, _ = curve_fit(
                _f, tt, ii, p0=p0,
                bounds=([0, 1.0, 0], [max(i_cc * 2, 1e-6), 1e5, max(i_cc, 1e-6)]),
                maxfev=5000,
            )
            i0, tau_cv, iinf = (float(x) for x in popt)
            i_inf_norm = (iinf / i_cc) if i_cc > 1e-12 else None
            # Q at T_ref via integrated exponential (Ah if I in A, t in s)
            t_end = min(float(t_ref_s), float(tt[-1]))
            # ∫_0^{T} (I0 e^{-t/τ} + Iinf) dt
            q_as = i0 * tau_cv * (1.0 - np.exp(-t_end / tau_cv)) + iinf * t_end
            q_cv_tref = abs(q_as) / 3600.0  # A·s → Ah
            tot_n = cc_capa + q_cv_tref
            cc_ratio_norm = (cc_capa / tot_n * 100.0) if tot_n > 1e-12 else None
    except Exception:
        tau_cv = None

    mismatch = None
    if column_cv_ah is not None and column_cv_ah > 0 and cv_capa > 0:
        mismatch = abs(cv_capa - column_cv_ah) / column_cv_ah * 100.0
        if mismatch > 10.0:
            method = method + "+column_mismatch"

    return SignalCvResult(
        has_cv=True,
        cv_start_index=int(best_a),
        chgCCcapa=cc_capa,
        chgCVcapa=cv_capa,
        chgCVtime=cv_time,
        chgCapa_CCratio=cc_ratio,
        chgCapa_CCratio_norm=cc_ratio_norm if cc_ratio_norm is not None else cc_ratio,
        Q_CV_at_Tref=q_cv_tref,
        tau_CV=tau_cv,
        I_inf_norm=i_inf_norm,
        cv_detect_method=method,
        cv_detect_mismatch_pct=mismatch,
        column_cv_ah=column_cv_ah,
    )


def signal_cv_to_row(res: SignalCvResult) -> dict[str, Any]:
    return {
        "chgCCcapa": res.chgCCcapa,
        "chgCVcapa": res.chgCVcapa if res.chgCVcapa is not None else 0.0,
        "chgCVtime": res.chgCVtime if res.chgCVtime is not None else 0.0,
        "chgCapa_CCratio": res.chgCapa_CCratio,
        "chgCapa_CCratio_norm": res.chgCapa_CCratio_norm,
        "Q_CV_at_Tref": res.Q_CV_at_Tref,
        "tau_CV": res.tau_CV,
        "I_inf_norm": res.I_inf_norm,
        "cv_detect_method": res.cv_detect_method,
        "cv_detect_mismatch_pct": res.cv_detect_mismatch_pct,
    }
