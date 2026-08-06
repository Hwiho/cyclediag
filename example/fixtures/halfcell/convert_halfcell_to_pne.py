"""Convert BioLogic half-cell exports to pne_studio *_raw.csv format."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

DEFAULT_CURRENT_MA = 2.756


def convert_bio_logic_txt(txt_path: Path, out_dir: Path) -> tuple[Path, int, int]:
    df = pd.read_csv(txt_path, sep="\t", engine="python")
    time = df["time/s"].astype(float).values
    cap = df["Capacity/mA.h"].astype(float).values
    volt = df["Ewe/V"].astype(float).values

    dcap = np.diff(cap, prepend=cap[0])
    resets = np.where(dcap < -0.01)[0]
    bounds = [0] + list(resets) + [len(df)]

    rows = []
    cycle = 0
    prev_trend = None
    for i in range(len(bounds) - 1):
        s, e = bounds[i], bounds[i + 1]
        seg_volt = volt[s:e]
        dv = seg_volt[-1] - seg_volt[0]
        if dv > 0.01:
            trend = "charge"
        elif dv < -0.01:
            trend = "discharge"
        else:
            trend = "rest"

        if trend == "discharge" and prev_trend != "discharge":
            cycle += 1
        prev_trend = trend

        seg_cap = cap[s:e] - cap[s]
        seg_time = time[s:e]
        for j in range(e - s):
            rows.append(
                {
                    "TotalCycle": cycle,
                    "Voltage": seg_volt[j],
                    "Capacity": seg_cap[j],
                    "StepType": trend,
                    "TotalTime_sec": seg_time[j],
                }
            )

    out = pd.DataFrame(rows)
    out_path = out_dir / f"{txt_path.stem}_raw.csv"
    out.to_csv(out_path, index=False)
    return out_path, len(out), int(out["TotalCycle"].max())


def convert_time_voltage(
    time: np.ndarray,
    voltage: np.ndarray,
    *,
    current_ma: float = DEFAULT_CURRENT_MA,
) -> pd.DataFrame:
    time = np.asarray(time, dtype=float)
    voltage = np.asarray(voltage, dtype=float)

    dt = np.diff(time, prepend=time[0])
    resets = np.where(dt < -0.01)[0]
    bounds = [0] + list(resets) + [len(time)]

    rows = []
    cycle = 0
    prev_trend = None

    for i in range(len(bounds) - 1):
        s, e = bounds[i], bounds[i + 1]
        seg_t = time[s:e]
        seg_v = voltage[s:e]
        dv = seg_v[-1] - seg_v[0]
        if dv > 0.01:
            trend = "charge"
        elif dv < -0.01:
            trend = "discharge"
        else:
            trend = "rest"

        if trend == "discharge" and prev_trend != "discharge":
            cycle += 1
        elif cycle == 0 and trend in ("charge", "rest"):
            cycle = 1
        prev_trend = trend

        t0 = seg_t[0]
        for j in range(e - s):
            cap = (seg_t[j] - t0) / 3600.0 * current_ma
            rows.append(
                {
                    "TotalCycle": cycle,
                    "Voltage": seg_v[j],
                    "Capacity": cap,
                    "StepType": trend,
                    "TotalTime_sec": seg_t[j],
                }
            )

    return pd.DataFrame(rows)


def convert_cathode_xlsx(xlsx_path: Path, out_dir: Path) -> list[tuple[Path, int, int]]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    rows = [row for row in wb["Sheet1"].iter_rows(values_only=True)]
    wb.close()

    outputs: list[tuple[Path, int, int]] = []
    channels = [
        ("ch1", 0, 1),
        ("ch2", 2, 3),
    ]
    for stem, ti, vi in channels:
        data = [(r[ti], r[vi]) for r in rows if r[ti] is not None and r[vi] is not None]
        arr = np.array(data, dtype=float)
        out = convert_time_voltage(arr[:, 0], arr[:, 1])
        out_path = out_dir / f"cathode_halfcell_{stem}_raw.csv"
        out.to_csv(out_path, index=False)
        outputs.append((out_path, len(out), int(out["TotalCycle"].max())))
    return outputs


def convert_folder(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)

    for txt in sorted(folder.glob("*.txt")):
        out_path, nrows, ncycles = convert_bio_logic_txt(txt, folder)
        print(f"{txt.name} -> {out_path.name}: {nrows} rows, {ncycles} cycles")

    xlsx = folder.parent / "cathode_halfcell.xlsx"
    if folder.name == "cathode_halfcell" and xlsx.exists():
        for out_path, nrows, ncycles in convert_cathode_xlsx(xlsx, folder):
            print(f"cathode_halfcell.xlsx -> {out_path.name}: {nrows} rows, {ncycles} cycles")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "folder",
        nargs="?",
        default=r"c:\Halfcell\cathode_halfcell",
        help="Half-cell folder containing BioLogic txt files",
    )
    args = parser.parse_args()
    convert_folder(Path(args.folder))


if __name__ == "__main__":
    main()
