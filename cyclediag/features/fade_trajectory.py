"""Capacity fade trajectory: power-law fade + bilinear knee (Bacon-Watts style).

When ``cycle_role`` is present (see ``cycle_roles.attach_cycle_roles``), fade/knee
fits use **routine 0.5C** SoHQ only. Mid-life SoHQ spikes from C/3 RPT are not
treated as trajectory noise — they are a different protocol and must be excluded
from continuous fade estimation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _clean_sohq_series(features: pd.DataFrame) -> pd.DataFrame:
    """Return cycle, SoHQ suitable for fade/knee fitting.

    Preference order:
    1. ``cycle_role == routine_05c`` (excludes C/3 RPT and DCIR pulse)
    2. legacy: drop ``is_pulse_cycle``, keep finite SoHQ/capa
    """
    if features is None or features.empty or "SoHQ" not in features.columns:
        return pd.DataFrame(columns=["cycle", "SoHQ"])
    df = features.copy()
    if "cycle" not in df.columns:
        df = df.reset_index().rename(columns={"index": "cycle"})
    df["SoHQ"] = pd.to_numeric(df["SoHQ"], errors="coerce")
    df["cycle"] = pd.to_numeric(df["cycle"], errors="coerce")

    if "cycle_role" in df.columns:
        role = df["cycle_role"].astype(str)
        use = df.loc[role.eq("routine_05c")].copy()
        # Fall back if role tagging failed for most rows
        if len(use) < max(8, int(0.2 * len(df))):
            use = df.copy()
            if "is_pulse_cycle" in use.columns:
                use = use.loc[~use["is_pulse_cycle"].fillna(False)].copy()
    else:
        use = df
        if "is_pulse_cycle" in use.columns:
            use = use.loc[~use["is_pulse_cycle"].fillna(False)].copy()

    use = use.loc[np.isfinite(use["cycle"]) & np.isfinite(use["SoHQ"])].copy()
    if "capa_Ah" in use.columns:
        capa = pd.to_numeric(use["capa_Ah"], errors="coerce")
        use = use.loc[capa.notna() & (capa > 0)].copy()
    use = use.sort_values("cycle").drop_duplicates("cycle", keep="last")
    return use[["cycle", "SoHQ"]]


def fit_fade_exponent(
    cycles: np.ndarray,
    sohq: np.ndarray,
    sohq0: float | None = None,
) -> dict[str, Any]:
    """Fit SoHQ(n) ≈ sohq0 * (1 - a * n^b). Returns a, b, se(b), r2."""
    out: dict[str, Any] = {
        "fade_exponent_b": None,
        "fade_exponent_a": None,
        "fade_exponent_b_se": None,
        "fade_fit_r2": None,
        "fade_sohq0": None,
    }
    n = np.asarray(cycles, dtype=float)
    y = np.asarray(sohq, dtype=float)
    m = np.isfinite(n) & np.isfinite(y) & (n >= 1) & (y > 0)
    n, y = n[m], y[m]
    if len(n) < 8:
        return out
    if sohq0 is not None and np.isfinite(sohq0) and float(sohq0) > 0:
        y0 = float(sohq0)
    else:
        y0 = float(np.nanmedian(y[: max(3, len(y) // 20)]))
        if not np.isfinite(y0) or y0 <= 0:
            y0 = float(np.nanmax(y))
    y_frac = np.clip(y / y0, 1e-6, 1.5)

    def model(nn: np.ndarray, a: float, b: float) -> np.ndarray:
        return 1.0 - a * np.power(nn, b)

    try:
        popt, pcov = curve_fit(
            model,
            n,
            y_frac,
            p0=(1e-4, 0.8),
            bounds=([0.0, 0.05], [0.5, 3.0]),
            maxfev=20000,
        )
        a, b = float(popt[0]), float(popt[1])
        se_b = float(np.sqrt(pcov[1, 1])) if np.isfinite(pcov[1, 1]) else None
        yhat = model(n, a, b)
        ss_res = float(np.sum((y_frac - yhat) ** 2))
        ss_tot = float(np.sum((y_frac - np.mean(y_frac)) ** 2))
        out.update({
            "fade_exponent_b": b,
            "fade_exponent_a": a,
            "fade_exponent_b_se": se_b,
            "fade_fit_r2": (1.0 - ss_res / ss_tot) if ss_tot > 1e-12 else None,
            "fade_sohq0": y0,
        })
    except Exception:
        return out
    return out


def fit_bilinear_knee(
    cycles: np.ndarray,
    sohq: np.ndarray,
) -> dict[str, Any]:
    """Two-segment linear model; breakpoint = knee_cycle_bw."""
    out: dict[str, Any] = {
        "knee_cycle_bw": None,
        "knee_severity": None,
        "knee_slope_before": None,
        "knee_slope_after": None,
        "knee_fit_r2": None,
        "knee_method": "bilinear",
    }
    n = np.asarray(cycles, dtype=float)
    y = np.asarray(sohq, dtype=float)
    m = np.isfinite(n) & np.isfinite(y)
    n, y = n[m], y[m]
    if len(n) < 12:
        return out
    order = np.argsort(n)
    n, y = n[order], y[order]

    best = None
    for i in range(4, len(n) - 4):
        n1, y1 = n[: i + 1], y[: i + 1]
        n2, y2 = n[i:], y[i:]
        if len(n1) < 4 or len(n2) < 4:
            continue
        s1, i1 = np.polyfit(n1, y1, 1)
        s2, i2 = np.polyfit(n2, y2, 1)
        yhat = np.concatenate([s1 * n1 + i1, s2 * n2[1:] + i2])
        y_use = np.concatenate([y1, y2[1:]])
        if len(yhat) != len(y_use):
            continue
        ss_res = float(np.sum((y_use - yhat) ** 2))
        ss_tot = float(np.sum((y_use - np.mean(y_use)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
        score = r2 + 0.05 * max(0.0, float(s1 - s2))
        if best is None or score > best[0]:
            best = (score, float(n[i]), float(s1), float(s2), r2)

    if best is None:
        return out
    _, knee, s1, s2, r2 = best
    severity = float(max(0.0, s1 - s2))
    out.update({
        "knee_cycle_bw": knee,
        "knee_severity": severity,
        "knee_slope_before": s1,
        "knee_slope_after": s2,
        "knee_fit_r2": r2,
    })
    return out


def attach_fade_trajectory(features: pd.DataFrame) -> pd.DataFrame:
    """Broadcast cell-level fade/knee metrics onto all rows (routine SoHQ when roles exist)."""
    out = features.copy()
    cols = [
        "fade_exponent_b", "fade_exponent_a", "fade_exponent_b_se", "fade_fit_r2", "fade_sohq0",
        "knee_cycle_bw", "knee_severity", "knee_slope_before", "knee_slope_after",
        "knee_fit_r2", "knee_method",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = np.nan if c != "knee_method" else None

    series = _clean_sohq_series(out)
    if len(series) < 8:
        return out
    n = series["cycle"].to_numpy(dtype=float)
    y = series["SoHQ"].to_numpy(dtype=float)
    fade = fit_fade_exponent(n, y)
    knee = fit_bilinear_knee(n, y)
    for k, v in {**fade, **knee}.items():
        out[k] = v
    return out
