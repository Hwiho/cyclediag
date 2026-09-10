"""Batch overlay: charge dQ/dV SG w21 vs w31 for a cycle range (shoulder compare)."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, find_dqdv_peaks
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv
from cyclediag.tools.compare_sg_window_peaks import _peaks_for_leg, _fmt_peaks


def _studio_column_map() -> ColumnMap:
    cmap = ColumnMap.studio_default()
    cmap.cycle = "TotalCycle"
    cmap.voltage = "Voltage (V)"
    cmap.capacity = "ChargeCapacity (mAh)"
    cmap.discharge_capacity = "DischargeCapacity (mAh)"
    cmap.step_type = "StepType"
    cmap.current = "Current (mA)"
    return cmap


def _mid_peak_count(peaks: list[dict], v_lo: float = 3.5, v_hi: float = 3.88) -> int:
    return sum(1 for p in peaks if v_lo <= float(p["V"]) <= v_hi)


def export_range_compare(
    csv_path: Path,
    cycle_start: int,
    cycle_end: int,
    out_dir: Path,
    *,
    v_zoom: tuple[float, float] = (3.48, 4.06),
) -> None:
    cfg21 = DqdvPeakConfig(sg_window=21)
    cfg31 = DqdvPeakConfig(sg_window=31)
    cfg27 = DqdvPeakConfig(sg_window=27)
    cfg31_mad25 = DqdvPeakConfig(sg_window=31, mad_prominence_factor=2.5)

    configs = [
        ("w21", cfg21),
        ("w31", cfg31),
        ("w27", cfg27),
        ("w31_mad2.5", cfg31_mad25),
    ]

    df = load_cycler_csv(str(csv_path), column_map=_studio_column_map())
    cycles = list(range(cycle_start, cycle_end + 1))
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for tc in cycles:
        cyc = df[df["cycle"] == tc]
        row: dict = {"tc": tc}
        for name, cfg in configs:
            r = _peaks_for_leg(cyc, "charge", cfg)
            if r is None:
                row[f"n_{name}"] = None
                row[f"mid_{name}"] = None
                row[f"peaks_{name}"] = ""
                continue
            _, _, _, peaks = r
            row[f"n_{name}"] = len(peaks)
            row[f"mid_{name}"] = _mid_peak_count(peaks)
            row[f"peaks_{name}"] = _fmt_peaks(peaks)
        records.append(row)

    csv_out = out_dir / "tc_range_param_summary.csv"
    fields = ["tc"]
    for name, _ in configs:
        fields.extend([f"n_{name}", f"mid_{name}", f"peaks_{name}"])
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(records)

    # Overlay all cycles: w21 vs w31 (charge, zoom)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="white", sharey=True)
    colors = plt.cm.plasma(np.linspace(0.1, 0.95, len(cycles)))

    for ax_idx, (wname, cfg) in enumerate([("w21", cfg21), ("w31", cfg31)]):
        ax = axes[ax_idx]
        for tc, c in zip(cycles, colors):
            cyc = df[df["cycle"] == tc]
            r = _peaks_for_leg(cyc, "charge", cfg)
            if r is None:
                continue
            vx, _, y_s, peaks = r
            n_mid = _mid_peak_count(peaks)
            lw = 2.2 if tc in (79, 80) else 1.0
            alpha = 1.0 if tc in (79, 80) else 0.55
            ax.plot(vx, y_s, color=c, lw=lw, alpha=alpha, label=f"TC{tc} n={len(peaks)} mid={n_mid}")
            for pk in peaks:
                v_pk = float(pk["V"])
                if v_zoom[0] <= v_pk <= v_zoom[1]:
                    j = int(np.argmin(np.abs(vx - v_pk)))
                    ax.scatter([v_pk], [y_s[j]], s=18 if tc not in (79, 80) else 40,
                               c=[c], edgecolors="k", linewidths=0.3, zorder=4)
        ax.set_xlim(*v_zoom)
        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("dQ/dV (SG smooth)")
        ax.set_title(f"Charge TC{cycle_start}-{cycle_end} | SG {wname}")
        ax.grid(alpha=0.3)

    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=7, fontsize=6, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"Ch022 charge shoulder region | TC{cycle_start}-{cycle_end}", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_dir / f"tc{cycle_start}_{cycle_end}_charge_overlay_w21_w31.png",
                dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # 4-panel param compare for shoulder cycles 77-83
    shoulder_cycles = [77, 78, 79, 80, 81, 82, 83]
    fig, axes = plt.subplots(len(shoulder_cycles), 4, figsize=(16, 2.2 * len(shoulder_cycles)),
                             facecolor="white", sharex=True)
    if len(shoulder_cycles) == 1:
        axes = np.array([axes])
    col_titles = [c[0] for c in configs]

    for ri, tc in enumerate(shoulder_cycles):
        cyc = df[df["cycle"] == tc]
        for ci, (name, cfg) in enumerate(configs):
            ax = axes[ri, ci]
            r = _peaks_for_leg(cyc, "charge", cfg)
            if r is None:
                ax.set_title(f"TC{tc} {name}: no data", fontsize=8)
                continue
            vx, dqdv, y_s, peaks = r
            ax.plot(vx, y_s, color="#334155", lw=1.2)
            for i, pk in enumerate(peaks):
                v_pk = float(pk["V"])
                j = int(np.argmin(np.abs(vx - v_pk)))
                ax.scatter([v_pk], [y_s[j]], s=35, c="#dc2626", edgecolors="k", linewidths=0.4, zorder=5)
                ax.annotate(f"P{i+1}", (v_pk, y_s[j]), fontsize=6, xytext=(2, 3), textcoords="offset points")
            ax.set_xlim(*v_zoom)
            ax.set_title(f"TC{tc} {name}: n={len(peaks)} mid={_mid_peak_count(peaks)}", fontsize=8)
            ax.grid(alpha=0.25)
            if ri == len(shoulder_cycles) - 1:
                ax.set_xlabel("V (V)", fontsize=7)
        axes[ri, 0].set_ylabel(f"TC{tc}", fontsize=8, rotation=0, labelpad=28)

    for ci, title in enumerate(col_titles):
        axes[0, ci].annotate(title, xy=(0.5, 1.35), xycoords="axes fraction",
                             ha="center", fontsize=10, fontweight="bold")

    fig.suptitle("Shoulder cycles TC77-83: w21 / w31 / w27 / w31+mad2.5", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_dir / "tc77_83_four_param_grid.png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Peak count heatmap-style text summary
    diff_lines = ["tc,n_w21,n_w31,n_w27,n_w31_mad2.5,mid_w21,mid_w31,diff_21_31"]
    for row in records:
        n21, n31 = row.get("n_w21"), row.get("n_w31")
        diff = "" if n21 is None or n31 is None else str(n21 != n31)
        diff_lines.append(
            f"{row['tc']},{n21},{n31},{row.get('n_w27')},{row.get('n_w31_mad2.5')},"
            f"{row.get('mid_w21')},{row.get('mid_w31')},{diff}"
        )
    (out_dir / "peak_count_diff_flag.csv").write_text("\n".join(diff_lines) + "\n", encoding="utf-8")

    n_diff = sum(1 for r in records if r.get("n_w21") != r.get("n_w31"))
    print(f"Output: {out_dir}")
    print(f"Cycles {cycle_start}-{cycle_end}: w21 vs w31 peak count differs on {n_diff}/{len(records)} cycles")
    for r in records:
        if r.get("n_w21") != r.get("n_w31"):
            print(f"  TC{r['tc']}: w21={r['n_w21']} mid={r['mid_w21']} | w31={r['n_w31']} mid={r['mid_w31']}")
            print(f"    w21: {r['peaks_w21']}")
            print(f"    w31: {r['peaks_w31']}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--start", type=int, default=70)
    p.add_argument("--end", type=int, default=90)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()
    export_range_compare(args.input, args.start, args.end, args.out_dir)


if __name__ == "__main__":
    main()
