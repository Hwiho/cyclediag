"""Unsupervised diagnosis MVP — z-score anomaly score."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.indicator_registry import primary_indicator_columns

FLAG_WATCH = 0.55
FLAG_ALERT = 0.75


def anomaly_feature_cols(df: pd.DataFrame) -> list[str]:
    """Input pool for the anomaly score: one representative per indicator family.

    The score is a mean over |z|, so a physical signal that owns several
    aliases would otherwise weight the score by its alias count. The registry
    also keeps health targets, protocol covariates, QC provenance and
    diagnosis outputs out of the pool.
    """
    return primary_indicator_columns(df)


def predict_features(
    features: pd.DataFrame,
    *,
    reference: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add anomaly_score, flag, top_features to feature rows.

  Uses reference median/std when provided; otherwise leave-one-out style
  stats across the input batch (MVP only — not for production eval).
    """
    if features is None or features.empty:
        return pd.DataFrame()

    cols = anomaly_feature_cols(features)
    if not cols:
        out = features.copy()
        out["anomaly_score"] = np.nan
        out["flag"] = "ok"
        out["top_features"] = ""
        return out

    ref = reference if reference is not None and not reference.empty else features
    med = ref[cols].median(numeric_only=True)
    std = ref[cols].std(numeric_only=True).replace(0, np.nan)

    out = features.copy()
    scores = []
    tops = []
    for _, row in features.iterrows():
        z = ((row[cols] - med) / std).abs()
        z = z.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        score = float(np.clip(z.mean() / 3.0, 0.0, 1.0)) if len(z) else 0.0
        scores.append(score)
        if len(z):
            top = z.sort_values(ascending=False).head(3)
            tops.append(", ".join(f"{k}={v:.2g}" for k, v in top.items()))
        else:
            tops.append("")

    out["anomaly_score"] = scores
    out["flag"] = [
        "alert" if s >= FLAG_ALERT else ("watch" if s >= FLAG_WATCH else "ok")
        for s in scores
    ]
    out["top_features"] = tops
    return out
