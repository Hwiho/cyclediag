"""Load PNE-style cycler CSV into a normalized DataFrame."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd

# Logical name -> default column name (pne_studio presets aligned)
PNE_DEFAULT_COLUMNS: dict[str, str] = {
    "cycle": "CycleIndex",
    "voltage": "Voltage(V)",
    "capacity": "ChargeCapacity",
    "step_type": "StepType",
    "current": "Current(A)",
    "time": "TotalTime_sec",
    "data_point": "Data_Point",
}


@dataclass
class ColumnMap:
    """Maps logical fields to CSV column names."""

    cycle: str = "CycleIndex"
    voltage: str = "Voltage(V)"
    capacity: str = "ChargeCapacity"
    step_type: str = "StepType"
    current: str = "Current(A)"
    time: str = "TotalTime_sec"
    step_time: str = "StepTime_sec"
    data_point: str = "Data_Point"
    discharge_capacity: str = "DischargeCapacity"
    temperature: str = "Temperature"

    @classmethod
    def pne_default(cls) -> ColumnMap:
        return cls()

    @classmethod
    def studio_default(cls) -> ColumnMap:
        """PNE Studio / pne_studio2 UI column names."""
        return cls(
            cycle="TotalCycle",
            voltage="Voltage",
            capacity="Capacity",
            step_type="StepType",
            current="Current",
            time="TotalTime_sec",
            step_time="StepTime_sec",
            data_point="Data_Point",
            discharge_capacity="DischargeCapacity",
            temperature="Temperature",
        )


def _resolve_column(
    df: pd.DataFrame,
    name: str,
    aliases: tuple[str, ...] = (),
    *,
    exclude: set[str] | None = None,
) -> str | None:
    """Resolve a logical column, preferring alias order over CSV column order.

    Example: prefer ``StepTime_sec (sec)`` over empty ``StepTime`` when both exist.
    """
    exclude = exclude or set()
    if name in df.columns and name not in exclude:
        return name

    def _norm(label: str) -> str:
        return str(label).split("(")[0].replace(" ", "").replace("_", "").lower()

    # Alias priority first (more specific names listed before bare names).
    for alias in (name, *aliases):
        a = _norm(alias)
        for col in df.columns:
            if col in exclude:
                continue
            if _norm(col) == a:
                return col
    return None


_CYCLE_ALIASES = ("TotalCycle", "CycleIndex", "CycleNum", "Cycle")
_VOLTAGE_ALIASES = ("Voltage", "Voltage(V)")
_CHARGE_CAP_ALIASES = ("Capacity", "ChargeCapacity")
_DISCHARGE_CAP_ALIASES = ("DischargeCapacity",)
_STEP_ALIASES = ("StepType", "Step")
_CURRENT_ALIASES = ("Current", "Current(A)", "AvgCurrent", "AvgCurrent(A)", "Current(mA)")
_TIME_ALIASES = ("TotalTime_sec", "TotalTime")
_STEP_TIME_ALIASES = ("StepTime_sec", "StepTime")
_TEMP_ALIASES = ("Temperature", "Temp", "CellTemp", "Aux_Temperature", "AuxTemp")


def normalize_cycler_dataframe(
    df: pd.DataFrame,
    column_map: ColumnMap | Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Rename raw cycler columns to logical names (in-memory, no file read)."""
    if column_map is None:
        cmap = ColumnMap.pne_default()
    elif isinstance(column_map, ColumnMap):
        cmap = column_map
    else:
        cmap = ColumnMap(**dict(column_map))

    rename: dict[str, str] = {}
    used: set[str] = set()

    def _map(logical: str, preferred: str, aliases: tuple[str, ...]) -> None:
        resolved = _resolve_column(df, preferred, aliases, exclude=used)
        if resolved:
            rename[resolved] = logical
            used.add(resolved)

    _map("cycle", cmap.cycle, _CYCLE_ALIASES)
    _map("voltage", cmap.voltage, _VOLTAGE_ALIASES)
    _map("step_type", cmap.step_type, _STEP_ALIASES)
    _map("current", cmap.current, _CURRENT_ALIASES)
    _map("time", cmap.time, _TIME_ALIASES)
    _map("step_time", cmap.step_time, _STEP_TIME_ALIASES)
    _map("data_point", cmap.data_point, ("Data_Point", "DataPoint"))
    _map("temperature", cmap.temperature, _TEMP_ALIASES)

    charge_cap = _resolve_column(df, cmap.capacity, _CHARGE_CAP_ALIASES, exclude=used)
    if charge_cap:
        rename[charge_cap] = "charge_capacity"
        used.add(charge_cap)

    discharge_cap = _resolve_column(
        df, cmap.discharge_capacity, _DISCHARGE_CAP_ALIASES, exclude=used,
    )
    if discharge_cap:
        rename[discharge_cap] = "discharge_capacity"
        used.add(discharge_cap)

    out = df.rename(columns=rename)

    if "charge_capacity" in out.columns:
        out["capacity"] = out["charge_capacity"]
    elif "discharge_capacity" in out.columns:
        out["capacity"] = out["discharge_capacity"]

    numeric_cols = (
        "cycle", "voltage", "capacity", "charge_capacity", "discharge_capacity",
        "current", "time", "step_time", "data_point", "temperature",
    )
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "cycle" in out.columns:
        out = out.dropna(subset=["cycle"])
        out["cycle"] = out["cycle"].astype(int)
    return out


def load_cycler_csv(
    path: str,
    column_map: ColumnMap | Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Load CSV and rename to logical column names where possible."""
    df = pd.read_csv(path, on_bad_lines="skip")
    return normalize_cycler_dataframe(df, column_map)
