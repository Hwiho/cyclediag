"""Temporary: TC80 charge peak parameter sweep."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, find_dqdv_peaks
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv

raw = ROOT / "example/docs/peak_review/_tmp_raw/00207966_260304_set4_SJ900_45도 0.5C cycle_no1_2_4_[Ch22]__QN_mono_#1_raw.csv"
cmap = ColumnMap.studio_default()
cmap.cycle = "TotalCycle"
cmap.voltage = "Voltage (V)"
cmap.capacity = "ChargeCapacity (mAh)"
cmap.discharge_capacity = "DischargeCapacity (mAh)"
cmap.step_type = "StepType"
cmap.current = "Current (mA)"
df = load_cycler_csv(str(raw), column_map=cmap)
cyc = df[df["cycle"] == 80]
seg = leg_segment(cyc, "charge", charge_text="charge", discharge_text="discharge")
seg = prepare_leg_segment_for_dqdv(seg, "charge")
v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
q = pd.to_numeric(seg["charge_capacity"], errors="coerce").to_numpy(dtype=float)

base = DqdvPeakConfig(sg_window=31)


def run(cfg: DqdvPeakConfig, label: str) -> None:
    peaks = find_dqdv_peaks(v, q, config=cfg)
    mid = [p for p in peaks if 3.5 <= p["V"] <= 3.85]
    vs = ", ".join(f"{p['V']:.3f}" for p in peaks)
    print(f"{label:42s} total={len(peaks)} mid={len(mid)}  [{vs}]")


print("=== TC80 charge parameter sweep ===\n")
run(base, "DEFAULT w31")

print("\n--- sg_window ---")
for w in [21, 25, 27, 29, 31]:
    run(replace(base, sg_window=w), f"sg_window={w}")

print("\n--- merge_v_sep_v (post-merge) ---")
for m in [0.004, 0.006, 0.008, 0.010, 0.012, 0.020]:
    run(replace(base, merge_v_sep_v=m), f"merge_v_sep_v={m}")

print("\n--- prominence_frac ---")
for p in [0.008, 0.010, 0.012, 0.015, 0.02, 0.025]:
    run(replace(base, prominence_frac=p), f"prominence_frac={p}")

print("\n--- min_distance_frac ---")
for d in [0.015, 0.02, 0.025, 0.03, 0.04, 0.05]:
    run(replace(base, min_distance_frac=d), f"min_distance_frac={d}")

print("\n--- mad_prominence_factor ---")
for m in [2.0, 3.0, 4.0, 5.0]:
    run(replace(base, mad_prominence_factor=m), f"mad_prominence_factor={m}")

print("\n--- combos (w31 + split mid) ---")
combos = [
    ("w31 + merge 0.006", replace(base, merge_v_sep_v=0.006)),
    ("w31 + merge 0.004", replace(base, merge_v_sep_v=0.004)),
    ("w31 + prom 0.012", replace(base, prominence_frac=0.012)),
    ("w31 + dist 0.02", replace(base, min_distance_frac=0.02)),
    ("w31 + dist 0.015", replace(base, min_distance_frac=0.015)),
    ("w27 + prom 0.012", replace(base, sg_window=27, prominence_frac=0.012)),
    ("w29 + prom 0.012", replace(base, sg_window=29, prominence_frac=0.012)),
    ("w31 + prom0.012 + dist0.02", replace(base, prominence_frac=0.012, min_distance_frac=0.02)),
]
for label, cfg in combos:
    run(cfg, label)

# neighbor consistency check for promising configs
print("\n=== Neighbor TC77-83 with candidate configs ===")
cycles = list(range(77, 84))
candidates = [
    ("w31 default", base),
    ("w21", replace(base, sg_window=21)),
    ("w31 prom0.012", replace(base, prominence_frac=0.012)),
    ("w31 dist0.02", replace(base, min_distance_frac=0.02)),
    ("w29 prom0.012", replace(base, sg_window=29, prominence_frac=0.012)),
]
for name, cfg in candidates:
    counts = []
    for tc in cycles:
        cyc = df[df["cycle"] == tc]
        seg = leg_segment(cyc, "charge", charge_text="charge", discharge_text="discharge")
        seg = prepare_leg_segment_for_dqdv(seg, "charge")
        vv = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
        qq = pd.to_numeric(seg["charge_capacity"], errors="coerce").to_numpy(dtype=float)
        n = len(find_dqdv_peaks(vv, qq, config=cfg))
        counts.append(str(n))
    print(f"{name:22s}  " + " ".join(f"TC{c}={n}" for c, n in zip(cycles, counts)))
