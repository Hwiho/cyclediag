"""Tests for cyclediag feature extraction."""

from __future__ import annotations

import pandas as pd
import pytest

from cyclediag.features.extract import FeatureConfig, extract_features_table


def _sample_df() -> pd.DataFrame:
    rows = []
    for leg, st, q_sign in (("charge", "charge", 1), ("discharge", "discharge", -1)):
        for i in range(20):
            rows.append({
                "cycle": 1,
                "step_type": st,
                "voltage": 3.0 + i * 0.05,
                "capacity": abs(i * 2.0),
                "current": 0.05 * q_sign,
                "time": float(i),
            })
    return pd.DataFrame(rows)


def test_extract_features_table_one_cycle():
    df = _sample_df()
    out = extract_features_table(df, filepath="cell_a.csv", config=FeatureConfig())
    assert len(out) == 2
    assert set(out["leg"]) == {"charge", "discharge"}
    assert out["f_Q_max"].notna().all()
    assert "cell_id" in out.columns
    assert out["cell_id"].iloc[0] == "cell_a"


def test_extract_requires_cycle_column():
    with pytest.raises(ValueError):
        extract_features_table(pd.DataFrame({"voltage": [3.0]}))
