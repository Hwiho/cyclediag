"""Self-discharge / micro-short detection from long pre-pulse rests — §5.4."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _linreg_slope(t: np.ndarray, v: np.ndarray) -> float | None:
    m = np.isfinite(t) & np.isfinite(v)
    t, v = t[m], v[m]
    if len(t) < 5:
        return None
    A = np.vstack([t, np.ones(len(t))]).T
    slope, _ = np.linalg.lstsq(A, v, rcond=None)[0]
    return float(slope)


def fit_self_discharge_rest(
    t: np.ndarray,
    v: np.ndarray,
    *,
    late_window: tuple[float, float] = (1800.0, 3600.0),
) -> dict[str, Any]:
    """Estimate self-discharge rate [mV/h] from a long rest V(t)."""
    out: dict[str, Any] = {
        "self_discharge_rate": None,  # mV/h
        "sd_relax_tau1": None,
        "sd_relax_tau2": None,
        "sd_fit_valid": False,
        "sd_relax_residual_ratio": None,
        "sd_method": "none",
        "V_inf_rest": None,
        "relax_completeness": None,
    }
    t = np.asarray(t, dtype=float)
    v = np.asarray(v, dtype=float)
    m = np.isfinite(t) & np.isfinite(v) & (t >= 0)
    t, v = t[m], v[m]
    if len(t) < 30 or float(np.nanmax(t)) < 1800.0:
        out["sd_method"] = "rest_too_short"
        return out

    # preferred: dual-exp + linear leak
    try:
        def _f(x, vinf, c1, tau1, c2, tau2, k):
            return (
                vinf
                - c1 * np.exp(-x / np.maximum(tau1, 1.0))
                - c2 * np.exp(-x / np.maximum(tau2, 10.0))
                - k * x
            )

        vinf0 = float(v[-1])
        p0 = (vinf0, 0.01, 100.0, 0.01, 800.0, 1e-8)
        popt, _ = curve_fit(
            _f, t, v, p0=p0, maxfev=12000,
            bounds=(
                [vinf0 - 0.5, 0.0, 1.0, 0.0, 10.0, -1e-5],
                [vinf0 + 0.5, 1.0, 2000.0, 1.0, 5000.0, 1e-5],
            ),
        )
        vinf, c1, tau1, c2, tau2, k = (float(x) for x in popt)
        out["V_inf_rest"] = vinf
        amp = abs(c1) + abs(c2)
        if amp > 1e-9:
            tau_dom = max(tau1, tau2)
            c_dom = c1 if tau1 >= tau2 else c2
            remaining = abs(c_dom) * np.exp(-3600.0 / max(tau_dom, 1.0))
            out["relax_completeness"] = float(remaining / amp)
        out["self_discharge_rate"] = abs(k) * 3600.0 * 1000.0  # |dV/dt| as mV/h loss
        out["sd_relax_tau1"] = min(tau1, tau2)
        out["sd_relax_tau2"] = max(tau1, tau2)
        out["sd_method"] = "biexp_linear"
        out["sd_fit_valid"] = True
        # residual ratio check vs late linear
        late = (t >= late_window[0]) & (t <= late_window[1])
        if late.sum() >= 10:
            b = _linreg_slope(t[late], v[late])
            if b is not None and abs(b) > 1e-15:
                c_dom = c1 if tau1 > tau2 else c2
                tau_dom = max(tau1, tau2)
                relax_left = c_dom * np.exp(-1800.0 / max(tau_dom, 1.0))
                out["sd_relax_residual_ratio"] = float(relax_left / abs(b * 1800.0))
                if out["sd_relax_residual_ratio"] > 0.3:
                    out["sd_fit_valid"] = False
        return out
    except Exception:
        pass

    # fallback: late-window linear
    late = (t >= late_window[0]) & (t <= late_window[1])
    b = _linreg_slope(t[late], v[late]) if late.sum() >= 10 else None
    if b is None:
        out["sd_method"] = "fit_failed"
        return out
    out["self_discharge_rate"] = abs(b) * 3600.0 * 1000.0
    out["sd_method"] = "late_linear"
    out["sd_fit_valid"] = True
    late_v = v[late]
    out["V_inf_rest"] = float(np.nanmean(late_v[-max(5, len(late_v) // 10):]))
    return out


def extract_pre_pulse_rest(
    cycle_df: pd.DataFrame,
    *,
    rest_current_max: float = 0.5,
    min_rest_s: float = 1800.0,
    expected_pulse_current: float | None = 70.0,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Long rest immediately before a high-current pulse."""
    if "voltage" not in cycle_df.columns or "current" not in cycle_df.columns:
        return None
    i = pd.to_numeric(cycle_df["current"], errors="coerce").abs().to_numpy()
    v = pd.to_numeric(cycle_df["voltage"], errors="coerce").to_numpy()
    if "step_time" in cycle_df.columns:
        st = pd.to_numeric(cycle_df["step_time"], errors="coerce").to_numpy()
    elif "time" in cycle_df.columns:
        st = pd.to_numeric(cycle_df["time"], errors="coerce").to_numpy()
    else:
        return None

    if expected_pulse_current is not None:
        pulse = np.isfinite(i) & (i >= 0.7 * expected_pulse_current)
    else:
        pulse = np.isfinite(i) & (i > max(rest_current_max * 10, 50.0))
    if not pulse.any():
        return None
    p0 = int(np.argmax(pulse))
    # walk backward over rest
    j = p0 - 1
    while j > 0 and (not np.isfinite(i[j]) or i[j] <= rest_current_max):
        j -= 1
    start = j + 1
    if start >= p0:
        return None
    sl = slice(start, p0)
    # prefer step-local clock; if step_time resets, rebuild from cumulative
    t_raw = st[sl]
    if np.nanmax(t_raw) - np.nanmin(t_raw) < min_rest_s * 0.5:
        # step_time may restart each step — use length * dt estimate
        t = np.arange(p0 - start, dtype=float) * 0.1  # 10 Hz fallback
        if float(t[-1]) < min_rest_s:
            return None
        return t, v[sl]
    t = t_raw - float(t_raw[0])
    if float(np.nanmax(t)) < min_rest_s:
        return None
    return t, v[sl]


def self_discharge_for_cycle(
    cycle_df: pd.DataFrame,
    *,
    rest_current_max: float = 0.5,
    expected_pulse_current: float | None = 70.0,
) -> dict[str, Any]:
    pair = extract_pre_pulse_rest(
        cycle_df,
        rest_current_max=rest_current_max,
        expected_pulse_current=expected_pulse_current,
    )
    if pair is None:
        return {
            "self_discharge_rate": None,
            "sd_fit_valid": False,
            "sd_method": "no_rest",
            "V_inf_rest": None,
            "relax_completeness": None,
        }
    return fit_self_discharge_rest(*pair)
