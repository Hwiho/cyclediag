"""Unsupervised anomaly rollup — thin wrapper over the indicator scoring track.

Prefer ``cyclediag.models.indicator_scoring.score_indicators`` for new code.
This module keeps the historical ``anomaly_score`` / ``flag`` / ``top_features``
column names for callers that have not migrated yet.

Causal mode scores (LLI / LAM / …) live in ``cyclediag.diagnosis`` and are
never produced here.
"""

from __future__ import annotations

import pandas as pd

from cyclediag.features.indicator_registry import primary_indicator_columns
from cyclediag.models.indicator_scoring import FLAG_ALERT, FLAG_WATCH, score_indicators

__all__ = [
    "FLAG_ALERT",
    "FLAG_WATCH",
    "anomaly_feature_cols",
    "predict_features",
]


def anomaly_feature_cols(df: pd.DataFrame) -> list[str]:
    """Input pool for the anomaly score: one representative per indicator family."""
    return primary_indicator_columns(df)


def predict_features(
    features: pd.DataFrame,
    *,
    reference: pd.DataFrame | None = None,
    raw_df: pd.DataFrame | None = None,
    routine_only: bool = True,
) -> pd.DataFrame:
    """Add anomaly_score, flag, top_features to feature rows.

    Delegates to :func:`score_indicators` (indicator track). By default only
    routine cycles contribute to the score so RPT / DC-IR spikes do not dominate.
    Pass ``routine_only=False`` to restore the historical all-rows behaviour.
    """
    if features is None or features.empty:
        return pd.DataFrame()

    result = score_indicators(
        features,
        reference=reference,
        raw_df=raw_df,
        routine_only=routine_only,
        grain="cycle",
    )
    out = result.cycle_scores
    if out.empty:
        out = features.copy()
        out["anomaly_score"] = pd.NA
        out["flag"] = "ok"
        out["top_features"] = ""
        return out

    # Historical column names for downstream compatibility.
    out = out.copy()
    out["anomaly_score"] = out["indicator_score"]
    out["flag"] = out["indicator_flag"]
    out["top_features"] = out["indicator_top"]
    return out
