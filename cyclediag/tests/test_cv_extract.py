"""Tests for cyclediag CV region extraction."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cyclediag.features.cv_extract import extract_cv_regions_table


def _norm_cc_cv_df() -> pd.DataFrame:
    n_cc, n_cv = 80, 40
    q_cc = np.linspace(0, 85, n_cc)
    v_cc = np.linspace(3.0, 4.2, n_cc)
    i_cc = np.full(n_cc, 1.0)
    q_cv = np.linspace(85, 100, n_cv)
    v_cv = np.full(n_cv, 4.2)
    i_cv = np.linspace(0.5, 0.05, n_cv)
    return pd.DataFrame({
        "cycle": [1] * (n_cc + n_cv),
        "step_type": ["charge"] * (n_cc + n_cv),
        "voltage": np.concatenate([v_cc, v_cv]),
        "capacity": np.concatenate([q_cc, q_cv]),
        "current": np.concatenate([i_cc, i_cv]),
        "time": np.arange(n_cc + n_cv) * 10.0,
    })


def test_extract_cv_regions_table():
    df = _norm_cc_cv_df()
    out = extract_cv_regions_table(df, cycles=[1])
    assert len(out) == 1
    row = out.iloc[0]
    assert row["has_cv"]
    assert row["cv_start_index"] == 80
    assert row["cc_q_frac"] == pytest.approx(0.85, rel=0.02)
