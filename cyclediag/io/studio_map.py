"""Shared column map for LGES / Studio raw CSV exports."""

from __future__ import annotations

import pandas as pd

from .cycler_csv import ColumnMap


def studio_column_map() -> ColumnMap:
    """ColumnMap for Ensol Studio-style raw CSV headers.

    Prefer Ah headers (SJ900). Aliases still match ``ChargeCapacity (mAh)``.
    """
    cmap = ColumnMap.studio_default()
    cmap.cycle = "TotalCycle"
    cmap.voltage = "Voltage (V)"
    cmap.capacity = "ChargeCapacity (Ah)"
    cmap.discharge_capacity = "DischargeCapacity (Ah)"
    cmap.step_type = "StepType"
    cmap.current = "Current (A)"
    return cmap


def capacity_col(seg: pd.DataFrame, leg: str) -> str | None:
    """Logical capacity column name for charge or discharge leg."""
    col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if col in seg.columns:
        return col
    return "capacity" if "capacity" in seg.columns else None
