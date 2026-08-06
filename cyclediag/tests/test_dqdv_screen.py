"""Tests for dQ/dV indicator screening."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.analysis.dqdv_screen import (
    compare_cells_dqdv,
    dqdv_trajectory_long,
    screen_dqdv_by_file,
    screen_dqdv_indicators,
)


def _dqdv_features(n: int = 50, cell: str = "A", v_drift: float = 0.0) -> pd.DataFrame:
    cycles = np.arange(1, n + 1)
    peak_v = 3.7 + cycles * 0.0001 + v_drift
    peak_h = 50 - cycles * 0.2
    return pd.DataFrame({
        "cell_id": cell,
        "file": f"{cell}.csv",
        "cycle": cycles,
        "dchgCapa": 100 - cycles * 0.5,
        "SoHQ": 100 - cycles * 0.5,
        "chg_dQdV_peak1_V": peak_v,
        "chg_dQdV_peak1": peak_h,
        "dchg_dQdV_peak1_V": 3.3 + cycles * 0.00005,
        "dchg_dQdV_peak1": 40 - cycles * 0.1,
    })


def test_screen_dqdv_finds_peak_v_drift():
    df = _dqdv_features(60)
    out = screen_dqdv_indicators(df)
    assert not out.empty
    assert "chg_dQdV_peak1_V" in out["feature"].values
    row = out[out["feature"] == "chg_dQdV_peak1_V"].iloc[0]
    assert row["metric"] == "V"
    assert row["delta_V_mV"] is not None


def test_compare_dqdv_two_cells():
    a = _dqdv_features(40, "cell_A")
    b = _dqdv_features(40, "cell_B", v_drift=0.05)
    both = pd.concat([a, b], ignore_index=True)
    cmp = compare_cells_dqdv(both)
    assert not cmp.empty
    assert "chg_dQdV_peak1_V" in cmp["feature"].values


def test_trajectory_long():
    df = _dqdv_features(10)
    long = dqdv_trajectory_long(df)
    assert not long.empty
    assert "indicator" in long.columns
    assert long["cycle"].nunique() == 10


def test_screen_by_file():
    both = pd.concat([_dqdv_features(30, "A"), _dqdv_features(30, "B")], ignore_index=True)
    out = screen_dqdv_by_file(both)
    assert len(out["cell_id"].unique()) == 2
