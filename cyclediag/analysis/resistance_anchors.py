"""Sparse DC-IR / landmark resistance summary for the protocol-anchor layer."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

_COMPONENT_COLS = (
    "R_ohmic_soc20", "R_ohmic_soc50", "R_ohmic_soc80",
    "R_ct_soc20", "R_ct_soc50", "R_ct_soc80",
    "A_diff_soc20", "A_diff_soc50", "A_diff_soc80",
    "R_30s_total_soc20", "R_30s_total_soc50", "R_30s_total_soc80",
    "R_SOC_slope", "R_ratio_20_50", "R_ratio_80_50",
    "R_recovery_tau1_soc50", "R_recovery_tau2_soc50",
)
_LANDMARK_COLS = (
    "EoC_dchgR_0p1s", "EoC_dchgR_10s", "EoC_dchgR_30s", "EoC_dchgR_60s",
    "EoD_chgR_0p1s", "EoD_chgR_10s", "EoD_chgR_30s", "EoD_chgR_60s",
    "EoC_dchgR_10_60_ratio", "EoD_chgR_10_60_ratio",
)


def resistance_anchor_table(features: pd.DataFrame) -> pd.DataFrame:
    """One row per cycle that has any DC-IR component populated."""
    if features is None or features.empty:
        return pd.DataFrame()
    cols = [c for c in _COMPONENT_COLS if c in features.columns]
    if not cols:
        return pd.DataFrame()
    m = features[cols].notna().any(axis=1)
    keep = ["cycle", "cell_id"] if "cell_id" in features.columns else ["cycle"]
    keep = [c for c in keep if c in features.columns]
    return features.loc[m, keep + cols].copy()


def landmark_resistance_trend(
    features: pd.DataFrame,
    *,
    routine_only: bool = True,
) -> pd.DataFrame:
    """Early/late medians of landmark R on routine rows."""
    from cyclediag.models.indicator_scoring import filter_scoring_rows

    if features is None or features.empty:
        return pd.DataFrame()
    df = filter_scoring_rows(features, routine_only=routine_only)
    cols = [c for c in _LANDMARK_COLS if c in df.columns]
    if not cols or "cycle" not in df.columns:
        return pd.DataFrame()
    cyc = pd.to_numeric(df["cycle"], errors="coerce")
    early = df.loc[cyc <= cyc.quantile(0.2)]
    late = df.loc[cyc >= cyc.quantile(0.8)]
    rows: list[dict[str, Any]] = []
    for col in cols:
        e = pd.to_numeric(early[col], errors="coerce")
        l = pd.to_numeric(late[col], errors="coerce")
        # drop extreme protocol leftovers even on routine (IQR fence)
        for series_name, s in (("early", e), ("late", l)):
            pass
        e_med = float(e.median()) if e.notna().any() else np.nan
        l_med = float(l.median()) if l.notna().any() else np.nan
        rows.append({
            "feature": col,
            "early_median": e_med,
            "late_median": l_med,
            "delta": l_med - e_med if np.isfinite(e_med) and np.isfinite(l_med) else np.nan,
            "n_early": int(e.notna().sum()),
            "n_late": int(l.notna().sum()),
        })
    return pd.DataFrame(rows)
