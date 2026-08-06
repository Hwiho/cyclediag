"""Load LGES StepEnd (per-step summary) CSV files."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe


def parse_step_duration_s(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s:
        return None
    if ":" not in s:
        try:
            return float(s)
        except ValueError:
            return None
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h, m, sec = parts
            return int(h) * 3600 + int(m) * 60 + float(sec)
        if len(parts) == 2:
            m, sec = parts
            return int(m) * 60 + float(sec)
    except ValueError:
        return None
    return None


def cell_id_from_path(path: str | Path) -> str:
    p = Path(path)
    parent = p.parent.name
    m = re.match(r"^(M\d+Ch\d+)", parent)
    if m:
        return m.group(1)
    return parent or p.stem


def load_stepemd_csv(
    path: str | Path,
    *,
    encoding: str = "cp949",
) -> pd.DataFrame:
    """Load StepEnd CSV and add leg labels from current sign."""
    path = Path(path)
    raw = pd.read_csv(path, encoding=encoding, on_bad_lines="skip", low_memory=False)
    cmap = ColumnMap(
        cycle="TotalCycle",
        voltage="Voltage",
        capacity="Capacity",
        step_type="StepType",
        current="Current",
        time="TotalTime",
        step_time="StepTime",
        discharge_capacity="DischargeCapacity",
        temperature="Temp",
    )
    df = normalize_cycler_dataframe(raw, column_map=cmap)
    if "StepNo" in raw.columns:
        df["step_no"] = pd.to_numeric(raw["StepNo"], errors="coerce")
    else:
        df["step_no"] = np.arange(len(df))
    for extra in ("AvgVoltage", "Impedance"):
        if extra in raw.columns:
            df[extra] = raw[extra]
    cur = pd.to_numeric(df.get("current"), errors="coerce").fillna(0.0)

    def _leg(i: float) -> str:
        if i > 0.05:
            return "charge"
        if i < -0.05:
            return "discharge"
        return "rest"

    df["step_type"] = cur.map(_leg)
    if "step_time" in df.columns:
        df["step_time_s"] = df["step_time"].map(parse_step_duration_s)
    else:
        df["step_time_s"] = None
    df["cell_id"] = cell_id_from_path(path)
    df["file"] = str(path)
    return df


def discover_stepemd_files(root: str | Path) -> list[Path]:
    root = Path(root)
    return sorted(root.rglob("*StepEnd.csv"))
