"""TC70 shoulder zoom analysis at ~3.75 V."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, find_dqdv_peaks, prepare_dqdv_arrays, _smooth
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


def get_curve(tc: int):
    cyc = df[df["cycle"] == tc]
    seg = leg_segment(cyc, "charge", charge_text="charge", discharge_text="discharge")
    seg = prepare_leg_segment_for_dqdv(seg, "charge")
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(seg["charge_capacity"], errors="coerce").to_numpy(dtype=float)
    return v, q


def local_maxima(vx, ys, v_lo=3.60, v_hi=3.85):
    mask = (vx >= v_lo) & (vx <= v_hi)
    sub_v, sub_y = vx[mask], ys[mask]
    locs = []
    for i in range(1, len(sub_y) - 1):
        if sub_y[i] > sub_y[i - 1] and sub_y[i] > sub_y[i + 1]:
            locs.append((float(sub_v[i]), float(sub_y[i])))
    return locs


out = ROOT / "example/docs/peak_review/sj900_set4_ch022_tc70_shoulder_zoom"
out.mkdir(parents=True, exist_ok=True)

configs = [
    ("w21", DqdvPeakConfig(sg_window=21)),
    ("w31", DqdvPeakConfig(sg_window=31)),
    ("w27", DqdvPeakConfig(sg_window=27)),
    ("w31_mad2.5", DqdvPeakConfig(sg_window=31, mad_prominence_factor=2.5)),
]

v, q = get_curve(70)
fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="white")
for ax, (name, cfg) in zip(axes.flat, configs):
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, cfg)
    ys = _smooth(dqdv, window=cfg.sg_window, poly=cfg.sg_poly)
    peaks = find_dqdv_peaks(v, q, config=cfg)
    ax.plot(vx, dqdv, color="#cbd5e1", lw=0.8, label="raw dQ/dV")
    ax.plot(vx, ys, color="#1d4ed8", lw=2, label=f"SG {name}")
    for i, pk in enumerate(peaks):
        vp = float(pk["V"])
        j = int(np.argmin(np.abs(vx - vp)))
        ax.axvline(vp, color="#dc2626", ls="--", lw=0.8, alpha=0.6)
        ax.scatter([vp], [ys[j]], s=80, c="#dc2626", edgecolors="k", zorder=5)
        ax.annotate(f"P{i+1}\n{vp:.3f}", (vp, ys[j]), fontsize=8, xytext=(5, 8), textcoords="offset points")
    # mark local max not assigned
    locs = local_maxima(vx, ys)
    assigned = {round(float(p["V"]), 3) for p in peaks}
    for lv, lh in locs:
        if not any(abs(lv - a) < 0.015 for a in assigned):
            ax.scatter([lv], [lh], s=120, facecolors="none", edgecolors="#f59e0b", linewidths=2, zorder=6)
            ax.annotate(f"local\n{lv:.3f}", (lv, lh), fontsize=7, color="#b45309", xytext=(5, -18), textcoords="offset points")
    ax.set_xlim(3.48, 3.95)
    ax.set_title(f"TC70 charge | {name} | n={len(peaks)} peaks")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
fig.suptitle("TC70 charge: ~3.75 V shoulder (orange ring = local max not assigned as peak)", fontsize=11)
fig.tight_layout()
fig.savefig(out / "tc0070_four_param_zoom.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# TC70 vs 79/80
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), facecolor="white")
for ax, w in zip(axes, [21, 31]):
    for tc, color, lw in [(70, "#2563eb", 2.5), (79, "#dc2626", 1.8), (80, "#16a34a", 1.8)]:
        vv, qq = get_curve(tc)
        cfg = DqdvPeakConfig(sg_window=w)
        vx, dqdv, _, _ = prepare_dqdv_arrays(vv, qq, cfg)
        ys = _smooth(dqdv, window=w, poly=3)
        ax.plot(vx, ys, color=color, lw=lw, label=f"TC{tc}")
        peaks = find_dqdv_peaks(vv, qq, config=cfg)
        for pk in peaks:
            vp = float(pk["V"])
            if 3.5 <= vp <= 3.9:
                j = int(np.argmin(np.abs(vx - vp)))
                ax.scatter([vp], [ys[j]], s=60, c=color, edgecolors="k", zorder=5)
    ax.set_xlim(3.52, 3.88)
    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("dQ/dV")
    ax.set_title(f"TC70 vs TC79/80 | SG w={w}")
    ax.grid(alpha=0.3)
    ax.legend()
fig.suptitle("Does TC70 have same shoulder split as TC79/80?", fontsize=12)
fig.tight_layout()
fig.savefig(out / "tc70_vs_79_80_w21_w31.png", dpi=160, bbox_inches="tight")
plt.close(fig)

print("=== TC70 analysis 3.60-3.85 V ===")
v, q = get_curve(70)
for w in [21, 27, 31]:
    cfg = DqdvPeakConfig(sg_window=w)
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, cfg)
    ys = _smooth(dqdv, window=w, poly=3)
    peaks = find_dqdv_peaks(v, q, config=cfg)
    locs = local_maxima(vx, ys)
    pk_str = ", ".join(f"{p['V']:.4f}V" for p in peaks)
    loc_str = ", ".join(f"{x[0]:.4f}V" for x in locs)
    print(f"w={w}: assigned peaks [{pk_str}]")
    print(f"      local maxima 3.60-3.85: [{loc_str}]")

print(f"\nSaved: {out}")
