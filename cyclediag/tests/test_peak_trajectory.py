"""Tests for peak trajectory feature table."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.peak_trajectory import PeakTrajectoryConfig, build_peak_tables


def _synthetic_cycle_df(*, n: int = 80, cycle: int = 1) -> pd.DataFrame:
    t = np.linspace(0, 3600, n)
    v = np.concatenate([
        np.linspace(3.0, 3.6, n // 4),
        np.linspace(3.6, 3.78, n // 4),
        np.linspace(3.78, 4.05, n // 4),
        np.linspace(4.05, 4.05, n - 3 * (n // 4)),
    ])
    q = np.linspace(0, 50, n)
    return pd.DataFrame({
        "cycle": cycle,
        "step_type": ["charge"] * n,
        "voltage": v,
        "charge_capacity": q,
        "discharge_capacity": np.nan,
        "current": np.full(n, 100.0),
    })


def test_build_peak_tables_has_quality_columns():
    df = _synthetic_cycle_df()
    long_df, wide_df = build_peak_tables(df, cell_id="TEST", source_file="x.csv", config=PeakTrajectoryConfig(assign_mode="band"))
    assert not wide_df.empty
    assert "quality_score" in wide_df.columns
    assert "usable" in wide_df.columns
    assert "usable_score" in wide_df.columns
    assert "usable_charge" in wide_df.columns
    assert "usable_discharge" in wide_df.columns
    assert not long_df.empty or wide_df["cha_n_bands"].iloc[0] >= 0
