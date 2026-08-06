"""Tests for StepEnd feature extraction."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from cyclediag.features.stepemd_extract import extract_stepemd_cycle_row


def test_stepemd_cycle_row_synthetic():
    cyc = pd.DataFrame({
        "cycle": [2, 2, 2, 2],
        "step_no": [5, 6, 7, 8],
        "step_type": ["charge", "rest", "discharge", "rest"],
        "voltage": [4.201, 4.161, 2.5, 3.017],
        "current": [3.872, 0.0, -25.82, 0.0],
        "charge_capacity": [70.814, 0, 0, 0],
        "discharge_capacity": [0, 0, 70.375, 0],
        "AvgVoltage": [3.872, 0, 3.418, 0],
        "step_time_s": [10983.0, 1800.0, 9813.0, 1800.0],
    })
    row = extract_stepemd_cycle_row(cyc, cell_id="T", filepath="t.csv")
    assert row is not None
    assert abs(row["dchgCapa"] - 70.375) < 0.01
    assert abs(row["EoD_restV_end"] - 3.017) < 0.01
