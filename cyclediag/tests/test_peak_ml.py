"""Tests for peak ML train/predict."""

from __future__ import annotations

import pandas as pd

from cyclediag.models.peak_ml import PeakMlConfig, predict_peak_model, train_peak_model


def _sample_features() -> pd.DataFrame:
    rows = []
    for cycle in range(1, 21):
        base = 3.7 + 0.001 * cycle
        rows.append({
            "cycle": cycle,
            "usable": cycle not in (19, 20),
            "band_gap_total": 0,
            "cha_P2_shoulder_V": base,
            "cha_P2_shoulder_H": 85 + cycle * 0.1,
            "cha_P3_main_V": base + 0.03,
            "cha_P3_main_H": 87 - cycle * 0.05,
            "dis_P2_mid_V": 3.68,
            "dis_P2_mid_H": -60,
            "d_cha_P2_shoulder_V": 0.001 * cycle,
            "d_cha_P3_main_H": -0.05 * cycle,
        })
    return pd.DataFrame(rows)


def test_train_and_predict_peak_model(tmp_path):
    df = _sample_features()
    good = [2, 3, 4, 5, 6]
    bundle = train_peak_model(df, good_cycles=good, config=PeakMlConfig(require_usable=False))
    bundle.save(tmp_path)

    pred = predict_peak_model(df, bundle)
    assert "ml_anomaly_score" in pred.columns
    assert "ml_flag" in pred.columns
    assert len(pred) == len(df)
    assert pred.loc[pred["cycle"] == 20, "ml_raw_score"].iloc[0] >= pred.loc[pred["cycle"] == 3, "ml_raw_score"].iloc[0]
