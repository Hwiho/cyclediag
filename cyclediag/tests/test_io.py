"""Tests for cyclediag IO normalization."""

from pathlib import Path

import pandas as pd

from cyclediag.io.cycler_csv import load_cycler_csv, normalize_cycler_dataframe


def test_load_synthetic_csv(tmp_path: Path):
    csv = tmp_path / "cell.csv"
    pd.DataFrame(
        {
            "CycleIndex": [1, 1, 1],
            "Voltage(V)": [3.0, 3.5, 4.0],
            "ChargeCapacity": [0.0, 0.5, 1.0],
            "StepType": ["Charge", "Charge", "Charge"],
        }
    ).to_csv(csv, index=False)
    df = load_cycler_csv(str(csv))
    assert "cycle" in df.columns
    assert len(df) == 3
    assert df["voltage"].iloc[-1] == 4.0


def test_normalize_dual_capacity_and_step_time():
    raw = pd.DataFrame({
        "TotalCycle": [1, 1, 1, 1],
        "StepType": ["charge", "rest", "discharge", "rest"],
        "Voltage": [3.5, 4.2, 3.8, 3.3],
        "Capacity": [100.0, 100.0, 100.0, 100.0],
        "DischargeCapacity": [0.0, 0.0, 95.0, 95.0],
        "Current": [1.0, 0.0, -1.0, 0.0],
        "TotalTime_sec": [0.0, 10.0, 20.0, 80.0],
        "StepTime_sec": [0.0, 5.0, 0.0, 60.0],
        "Temperature": [25.0, 25.1, 25.2, 25.0],
    })
    out = normalize_cycler_dataframe(raw)
    assert "charge_capacity" in out.columns
    assert "discharge_capacity" in out.columns
    assert "step_time" in out.columns
    assert "temperature" in out.columns
    assert out["discharge_capacity"].max() == 95.0
