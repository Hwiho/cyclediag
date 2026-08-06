"""Tests for cyclediag predict MVP."""

from __future__ import annotations

import pandas as pd

from cyclediag.models.predict import predict_features


def test_predict_adds_score_and_flag():
    df = pd.DataFrame({
        "cell_id": ["a", "b"],
        "f_Q_max": [100.0, 50.0],
        "f_V_avg": [3.7, 3.7],
    })
    out = predict_features(df)
    assert "anomaly_score" in out.columns
    assert "flag" in out.columns
    assert len(out) == 2
