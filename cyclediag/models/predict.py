"""Unsupervised diagnosis MVP — z-score anomaly score."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.family_registry import anomaly_feature_list

NUMERIC_PREFIX = "f_"
FLAG_WATCH = 0.55
FLAG_ALERT = 0.75
_META_COLS = frozenset({
    "cell_id", "file", "cycle", "leg", "feature_set", "cv_method",
    "has_cv", "anomaly_score", "flag", "top_features",
})


def _numeric_feature_cols(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        if c in _META_COLS:
            continue
        if not pd.api.types.is_numeric_dtype(df[c]):
            continue
        if c.startswith(NUMERIC_PREFIX) or c.startswith(("EoC_", "EoD_", "chg_", "dchg_", "delta_", "CE", "SoHQ")):
            cols.append(c)
            continue
        if c in ("CE", "CE_rev", "dchgCapa", "chgCapa", "chgCCcapa", "chgCVcapa", "chgCapa_CCratio", "chgCVtime"):
            cols.append(c)
    return cols


def _anomaly_input_cols(df: pd.DataFrame) -> list[str]:
    """Prefer §4.1 family representatives to avoid correlated double-counting."""
    available = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    fam = anomaly_feature_list(available)
    if len(fam) >= 3:
        return fam
    return _numeric_feature_cols(df)


def predict_features(
    features: pd.DataFrame,
    *,
    reference: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add anomaly_score, flag, top_features to feature rows.

  Uses reference median/std when provided; otherwise leave-one-out style
  stats across the input batch (MVP only — not for production eval).
  Anomaly inputs prefer family representatives (§4.1) when available.
    """
    if features is None or features.empty:
        return pd.DataFrame()

    cols = _anomaly_input_cols(features)
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
