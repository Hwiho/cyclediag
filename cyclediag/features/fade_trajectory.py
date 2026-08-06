"""SoHQ fade exponent + bilinear knee — IMPROVEMENT_ROADMAP §5.12 (feasible subset).

Implements:
- power-law fade fit: SoHQ ≈ 100 - a * N^b  → fade_exponent_b
- bilinear (Bacon-Watts-lite) knee: two linear segments with free breakpoint

Does NOT require half-cell or temperature. Aged-HC calibrated absolute modes remain out of scope.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _clean_sohq_series(features: pd.DataFrame) -> pd.DataFrame:
    if features is None or features.empty or "cycle" not in features.columns:
        return pd.DataFrame(columns=["cycle", "SoHQ"])
    d = features[["cycle"]].copy()
    sohq = None
    for col in ("SoHQ", "sohq", "dchgCapa"):
        if col in features.columns:
            sohq = pd.to_numeric(features[col], errors="coerce")
            if col != "SoHQ" and col == "dchgCapa":
                # normalize to % of early median if SoHQ absent
                base = float(sohq[sohq >= 10].median()) if (sohq >= 10).any() else np.nan
                if np.isfinite(base) and base > 0:
                    sohq = sohq / base * 100.0
            break
    if sohq is None:
        return pd.DataFrame(columns=["cycle", "SoHQ"])
    d["SoHQ"] = sohq
    d["cycle"] = pd.to_numeric(d["cycle"], errors="coerce")
    d = d.dropna()
    # exclude tiny SOC-step / pulse-like SoHQ dips
    d = d[d["SoHQ"] >= 40.0]
    return d.sort_values("cycle")


def fit_fade_exponent(
    cycles: np.ndarray,
    sohq: np.ndarray,
    *,
    sohq0: float | None = None,
) -> dict[str, Any]:
    """Fit SoHQ = sohq0 - a * cycle^b (b = fade_exponent_b)."""
    out: dict[str, Any] = {
        "fade_exponent_b": None,
        "fade_exponent_a": None,
        "fade_exponent_b_se": None,
        "fade_fit_r2": None,
        "fade_sohq0": None,
    }
    n = np.asarray(cycles, dtype=float)
    y = np.asarray(sohq, dtype=float)
    m = np.isfinite(n) & np.isfinite(y) & (n > 0)
    n, y = n[m], y[m]
    if len(n) < 8:
        return out
    y0 = float(sohq0) if sohq0 is not None else float(np.nanmedian(y[: max(3, len(y) // 10)]))
    if not np.isfinite(y0) or y0 <= 0:
        return out
    loss = np.clip(y0 - y, 1e-6, None)

    def _f(x, a, b):
        return a * np.power(x, b)

    try:
        popt, pcov = curve_fit(
            _f, n, loss, p0=(0.01, 1.0),
            bounds=([1e-8, 0.2], [50.0, 4.0]),
            maxfev=8000,
        )
        a, b = float(popt[0]), float(popt[1])
        yhat = y0 - _f(n, a, b)
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        se = None
        if pcov is not None and np.isfinite(pcov[1, 1]):
            se = float(np.sqrt(max(pcov[1, 1], 0.0)))
        out.update({
            "fade_exponent_b": b,
            "fade_exponent_a": a,
            "fade_exponent_b_se": se,
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
    # search breakpoints excluding edges
    for i in range(4, len(n) - 4):
        n1, y1 = n[: i + 1], y[: i + 1]
        n2, y2 = n[i:], y[i:]
        if len(n1) < 4 or len(n2) < 4:
            continue
        s1, i1 = np.polyfit(n1, y1, 1)
        s2, i2 = np.polyfit(n2, y2, 1)
        yhat = np.concatenate([s1 * n1 + i1, s2 * n2[1:] + i2])
        # align lengths
        y_use = np.concatenate([y1, y2[1:]])
        if len(yhat) != len(y_use):
            continue
        ss_res = float(np.sum((y_use - yhat) ** 2))
        ss_tot = float(np.sum((y_use - np.mean(y_use)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
        # prefer steeper after (more negative slope) as knee
        score = r2 + 0.05 * max(0.0, float(s1 - s2))  # s2 more negative → larger
        if best is None or score > best[0]:
            best = (score, float(n[i]), float(s1), float(s2), r2)

    if best is None:
        return out
    _, knee, s1, s2, r2 = best
    severity = float(max(0.0, s1 - s2))  # increase in fade rate
    out.update({
        "knee_cycle_bw": knee,
        "knee_severity": severity,
        "knee_slope_before": s1,
        "knee_slope_after": s2,
        "knee_fit_r2": r2,
    })
    return out


def attach_fade_trajectory(features: pd.DataFrame) -> pd.DataFrame:
    """Broadcast cell-level fade/knee metrics onto all rows."""
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
