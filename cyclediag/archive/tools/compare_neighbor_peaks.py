"""Zoom compare charge dQ/dV peaks around a center cycle (neighbor window)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, _smooth, find_dqdv_peaks, prepare_dqdv_arrays
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv
from cyclediag.tools.compare_sg_window_peaks import _capacity_col, _peaks_for_leg


def _studio_column_map() -> ColumnMap:
    cmap = ColumnMap.studio_default()
    cmap.cycle = "TotalCycle"
    cmap.voltage = "Voltage (V)"
    cmap.capacity = "ChargeCapacity (mAh)"
    cmap.discharge_capacity = "DischargeCapacity (mAh)"
    cmap.step_type = "StepType"
    cmap.current = "Current (mA)"
    return cmap


def plot_neighbor_panel(
    csv_path: Path,
    center_tc: int,
    radius: int,
    out_dir: Path,
    *,
    sg_window: int = 31,
    v_zoom: tuple[float, float] = (3.45, 4.08),
) -> None:
    cfg = DqdvPeakConfig(sg_window=sg_window)
    df = load_cycler_csv(str(csv_path), column_map=_studio_column_map())
    cycles = [center_tc + d for d in range(-radius, radius + 1)]
    out_dir.mkdir(parents=True, exist_ok=True)

    # Panel: all cycles overlaid (charge, w31)
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), facecolor="white")

    colors = plt.cm.viridis(np.linspace(0.15, 0.9, len(cycles)))
    mid_ax = axes[0]
    full_ax = axes[1]

    summary_lines: list[str] = []

    for tc, c in zip(cycles, colors):
        cyc = df[df["cycle"] == tc]
        r = _peaks_for_leg(cyc, "charge", cfg)
        if r is None:
            summary_lines.append(f"TC{tc}: no data")
            continue
        vx, dqdv, y_s, peaks = r
        label = f"TC{tc}" + (" *" if tc == center_tc else "")
        mid_ax.plot(vx, y_s, color=c, lw=1.8, alpha=0.9, label=label)
        full_ax.plot(vx, y_s, color=c, lw=1.4, alpha=0.85, label=label)
        for i, pk in enumerate(peaks):
            v_pk = float(pk["V"])
            if v_zoom[0] <= v_pk <= v_zoom[1]:
                mid_ax.axvline(v_pk, color=c, ls=":", lw=0.8, alpha=0.5)
        summary_lines.append(
            f"TC{tc}: n={len(peaks)} | "
            + ", ".join(f"P{i+1}@{p['V']:.3f}" for i, p in enumerate(peaks))
        )

    mid_ax.set_xlim(*v_zoom)
    mid_ax.set_ylabel("dQ/dV (SG smooth)")
    mid_ax.set_title(f"Ch022 charge | SG w={sg_window} | zoom {v_zoom[0]:.2f}-{v_zoom[1]:.2f} V | TC{center_tc}±{radius}")
    mid_ax.grid(alpha=0.3)
    mid_ax.legend(loc="upper right", fontsize=8, ncol=2)

    full_ax.set_xlabel("Voltage (V)")
    full_ax.set_ylabel("dQ/dV (SG smooth)")
    full_ax.set_title("Full charge dQ/dV (same cycles)")
    full_ax.grid(alpha=0.3)
    full_ax.legend(loc="upper right", fontsize=8, ncol=2)

    fig.tight_layout()
    panel_png = out_dir / f"tc{center_tc}_pm{radius}_charge_overlay_w{sg_window}.png"
    fig.savefig(panel_png, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Per-cycle detail with w21 vs w31 for charge only
    cfg21 = DqdvPeakConfig(sg_window=21)
    for tc in cycles:
        cyc = df[df["cycle"] == tc]
        r21 = _peaks_for_leg(cyc, "charge", cfg21)
        r31 = _peaks_for_leg(cyc, "charge", cfg)
        if r21 is None or r31 is None:
            continue
        vx, dqdv, y21, p21 = r21
        _, _, y31, p31 = r31

        fig, ax = plt.subplots(1, 1, figsize=(11, 5), facecolor="white")
        ax.plot(vx, dqdv, color="#cbd5e1", lw=0.7, label="raw")
        ax.plot(vx, y21, color="#1d4ed8", lw=1.6, alpha=0.85, label="SG w=21")
        ax.plot(vx, y31, color="#c2410c", lw=2.0, alpha=0.9, label="SG w=31")
        for peaks, color, off in ((p21, "#1d4ed8", -12), (p31, "#c2410c", 12)):
            for i, pk in enumerate(peaks):
                v_pk = float(pk["V"])
                j = int(np.argmin(np.abs(vx - v_pk)))
                ax.scatter([v_pk], [y31[j] if color == "#c2410c" else y21[j]],
                           s=80, c=color, edgecolors="#111", linewidths=0.8, zorder=5)
                tag = f"{'21' if color=='#1d4ed8' else '31'}-P{i+1}"
                ax.annotate(tag, xy=(v_pk, y31[j] if color == "#c2410c" else y21[j]),
                            xytext=(4, off), textcoords="offset points", fontsize=7, color=color)
        ax.set_xlim(*v_zoom)
        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("dQ/dV")
        ax.set_title(
            f"TC{tc} charge | w21: {len(p21)} peaks vs w31: {len(p31)} peaks"
            + ("  <<< center" if tc == center_tc else "")
        )
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out_dir / f"tc{tc:04d}_charge_w21_w31_zoom.png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    readme = out_dir / "README.txt"
    readme.write_text(
        f"Neighbor peak compare | center TC={center_tc} | radius={radius}\n"
        f"SG window focus: {sg_window}\n"
        f"zoom: {v_zoom[0]}-{v_zoom[1]} V\n\n"
        + "\n".join(summary_lines)
        + "\n",
        encoding="utf-8",
    )
    print(f"Saved to {out_dir}")
    for line in summary_lines:
        print(" ", line)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--center", type=int, default=80)
    p.add_argument("--radius", type=int, default=3)
    p.add_argument("--sg-window", type=int, default=31)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()
    plot_neighbor_panel(
        args.input, args.center, args.radius, args.out_dir, sg_window=args.sg_window,
    )


if __name__ == "__main__":
    main()
