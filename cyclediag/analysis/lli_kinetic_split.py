"""Separate LLI-like OCV parallel shift from kinetic early-termination.

Track B helper. Does not change indicator scores.
Rule (roadmap): parallel shift correlated with R30 → kinetic termination share;
shift with weak R change + rising EoD rest V → LLI share.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def classify_ocv_parallel_shift(
    features: pd.DataFrame,
    *,
    shift_col: str = "ocv_parallel_shift",
    r_col: str = "R_30s_total_soc50",
    eod_col: str = "delta_EoD_restV_end",
    min_points: int = 4,
) -> dict[str, Any]:
    """Return a soft label for the dominant driver of OCV parallel shift."""
    out: dict[str, Any] = {
        "label": "insufficient_data",
        "corr_shift_R30": np.nan,
        "corr_shift_EoD": np.nan,
        "n": 0,
        "note": "",
    }
    if features is None or features.empty:
        return out
    need = [c for c in (shift_col, r_col, eod_col) if c in features.columns]
    if shift_col not in features.columns:
        out["note"] = f"missing {shift_col}"
        return out
    s = pd.to_numeric(features[shift_col], errors="coerce")
    r = pd.to_numeric(features[r_col], errors="coerce") if r_col in features.columns else None
    e = pd.to_numeric(features[eod_col], errors="coerce") if eod_col in features.columns else None
    m = s.notna()
    if r is not None:
        m = m & r.notna()
    if e is not None:
        m = m & e.notna()
    n = int(m.sum())
    out["n"] = n
    if n < min_points:
        out["note"] = f"need>={min_points} paired points"
        return out

    corr_r = float(s[m].corr(r[m])) if r is not None else np.nan
    corr_e = float(s[m].corr(e[m])) if e is not None else np.nan
    out["corr_shift_R30"] = corr_r
    out["corr_shift_EoD"] = corr_e

    # High |corr| with R30 → kinetic termination; with EoD rest and weak R → LLI
    if np.isfinite(corr_r) and abs(corr_r) >= 0.6 and (
        not np.isfinite(corr_e) or abs(corr_r) >= abs(corr_e)
    ):
        out["label"] = "kinetic_termination_dominant"
        out["note"] = "ocv_parallel_shift tracks R30"
    elif np.isfinite(corr_e) and abs(corr_e) >= 0.5 and (
        not np.isfinite(corr_r) or abs(corr_r) < 0.4
    ):
        out["label"] = "lli_dominant"
        out["note"] = "ocv_parallel_shift tracks EoD rest with weak R30 link"
    elif np.isfinite(corr_r) and np.isfinite(corr_e) and abs(corr_r) >= 0.4 and abs(corr_e) >= 0.4:
        out["label"] = "mixed_lli_kinetic"
        out["note"] = "both R30 and EoD rest correlate with shift"
    else:
        out["label"] = "indeterminate"
        out["note"] = "correlations below decision thresholds"
    return out
