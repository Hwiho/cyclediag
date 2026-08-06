"""Tests for §5.12 fade exponent + bilinear knee."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.fade_trajectory import (
    attach_fade_trajectory,
    fit_bilinear_knee,
    fit_fade_exponent,
)
from cyclediag.features.family_registry import anomaly_feature_list
from cyclediag.models.predict import predict_features


def test_fit_fade_exponent_recovers_power():
    n = np.arange(1, 201, dtype=float)
    y = 100.0 - 0.02 * np.power(n, 1.4)
    out = fit_fade_exponent(n, y, sohq0=100.0)
    assert out["fade_exponent_b"] is not None
    assert abs(out["fade_exponent_b"] - 1.4) < 0.15
    assert out["fade_fit_r2"] is not None and out["fade_fit_r2"] > 0.95


def test_fit_bilinear_knee_finds_breakpoint():
    n = np.arange(1, 301, dtype=float)
    y = np.where(n < 180, 100 - 0.02 * n, 100 - 0.02 * 180 - 0.12 * (n - 180))
    out = fit_bilinear_knee(n, y)
    assert out["knee_cycle_bw"] is not None
    assert 150 <= out["knee_cycle_bw"] <= 210
    assert out["knee_severity"] is not None and out["knee_severity"] > 0


def test_attach_fade_trajectory_broadcast():
    df = pd.DataFrame({
        "cycle": list(range(1, 101)),
        "SoHQ": [100 - 0.15 * i - (0.3 * max(0, i - 60)) for i in range(1, 101)],
    })
    out = attach_fade_trajectory(df)
    assert out["fade_exponent_b"].notna().all()
    assert out["knee_cycle_bw"].notna().all()
    assert out["fade_exponent_b"].nunique() == 1


def test_anomaly_uses_family_reps_when_present():
    df = pd.DataFrame({
        "cell_id": ["a", "b"],
        "SoHQ": [100.0, 70.0],
        "CE": [99.5, 98.0],
        "R_ohmic_soc50": [1.0, 3.0],
        "mech_vs_chem_ratio": [1.0, 2.5],
        "PER": [1.0, 1.8],
        "RCF": [1.0, 0.7],
        "dQV_log_var": [-2.0, -1.0],
        "LAM_curve_proxy": [0.0, 5.0],
        "self_discharge_rate_soc80": [0.0, 0.01],
        "hyst_area_low": [0.02, 0.08],
        "R_ct_soc50": [2.0, 4.0],
        "VE": [95.0, 90.0],
    })
    reps = anomaly_feature_list(list(df.columns))
    assert "SoHQ" in reps
    assert "PER" in reps
    out = predict_features(df)
    assert "anomaly_score" in out.columns
    assert out["anomaly_score"].notna().all()
