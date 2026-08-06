"""Re-check dQ/dV peaks with SG w=31 + voltage band assign (shoulder split).

Usage:
  python cyclediag/tools/review_banded_peaks.py --input raw.csv --start 70 --end 90
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import (  # noqa: E402
    DqdvPeakConfig,
    _smooth,
    find_dqdv_peaks,
    find_dqdv_peaks_banded,
    charge_discharge_bands,
    prepare_dqdv_arrays,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv  # noqa: E402
from cyclediag.features.segment_utils import leg_segment  # noqa: E402
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv  # noqa: E402


def _studio_column_map() -> ColumnMap:
    cmap = ColumnMap.studio_default()
    cmap.cycle = "TotalCycle"
    cmap.voltage = "Voltage (V)"
    cmap.capacity = "ChargeCapacity (mAh)"
    cmap.discharge_capacity = "DischargeCapacity (mAh)"
    cmap.step_type = "StepType"
    cmap.current = "Current (mA)"
    return cmap


def _capacity_col(seg: pd.DataFrame, leg: str) -> str | None:
    col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if col in seg.columns:
        return col
    return "capacity" if "capacity" in seg.columns else None


def _fmt_peaks(peaks: list[dict], *, band: bool = False) -> str:
    if not peaks:
        return "-"
    parts = []
    for i, p in enumerate(peaks, start=1):
        tag = p.get("band", f"P{i}")
        parts.append(f"{tag} {p['V']:.4f}V H={p['H']:.2g}")
    return "; ".join(parts)


def save_review_png(
    *,
    vx: np.ndarray,
    dqdv: np.ndarray,
    y_smooth: np.ndarray,
    peaks_std: list[dict],
    peaks_band: list[dict],
    bands: tuple[tuple[float, float, str], ...],
    tc: int,
    leg: str,
    out_png: Path,
    cfg: DqdvPeakConfig,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 6), facecolor="white")
    ax.plot(vx, dqdv, color="#cbd5e1", lw=0.8, alpha=0.75, label="dQ/dV raw")
    ax.plot(vx, y_smooth, color="#64748b", lw=1.2, label=f"SG w={cfg.sg_window}")

    for v_min, v_max, label in bands:
        ax.axvspan(v_min, v_max, alpha=0.07, color="#f59e0b")
        ax.text((v_min + v_max) / 2, ax.get_ylim()[1] * 0.02, label,
                ha="center", va="bottom", fontsize=7, color="#92400e", transform=ax.get_transData())

    for i, pk in enumerate(peaks_std):
        v_pk = float(pk["V"])
        j = int(np.argmin(np.abs(vx - v_pk)))
        ax.scatter([v_pk], [y_smooth[j]], s=90, marker="s", c="#3b82f6", edgecolors="#111",
                   linewidths=0.8, zorder=5, label="w31 standard" if i == 0 else "")
        ax.annotate(f"S{i+1}", (v_pk, y_smooth[j]), fontsize=8, color="#1d4ed8",
                    xytext=(4, 10), textcoords="offset points")

    band_colors = plt.cm.Set1(np.linspace(0, 0.85, max(len(peaks_band), 1)))
    for i, pk in enumerate(peaks_band):
        v_pk = float(pk["V"])
        j = int(np.argmin(np.abs(vx - v_pk)))
        c = band_colors[i % len(band_colors)]
        ax.scatter([v_pk], [y_smooth[j]], s=130, c=[c], edgecolors="#111", linewidths=1.0, zorder=6,
                   label="band assign" if i == 0 else "")
        ax.annotate(
            pk.get("band", f"B{i+1}"),
            (v_pk, y_smooth[j]),
            fontsize=9,
            fontweight="bold",
            color=c,
            xytext=(6, -14 if i % 2 else 12),
            textcoords="offset points",
        )

    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("dQ/dV")
    ax.set_title(
        f"Ch022 TC{tc} {leg} | standard n={len(peaks_std)} vs band n={len(peaks_band)} | SG w={cfg.sg_window}"
    )
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)
    fig.savefig(out_png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def review_range(
    csv_path: Path,
    cycle_start: int,
    cycle_end: int,
    out_dir: Path,
    *,
    cfg: DqdvPeakConfig | None = None,
) -> list[dict]:
    cfg = cfg or DqdvPeakConfig(sg_window=31)
    df = load_cycler_csv(str(csv_path), column_map=_studio_column_map())
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    for tc in range(cycle_start, cycle_end + 1):
        cyc = df[df["cycle"] == tc].copy()
        if cyc.empty:
            continue
        for leg in ("charge", "discharge"):
            seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
            seg = prepare_leg_segment_for_dqdv(seg, leg)
            col = _capacity_col(seg, leg)
            if seg.empty or col is None or "voltage" not in seg.columns:
                continue
            v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
            q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
            bands = charge_discharge_bands(leg)
            peaks_std = find_dqdv_peaks(v, q, config=cfg)
            peaks_band = find_dqdv_peaks_banded(v, q, bands, config=cfg)
            vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, cfg)
            y_smooth = _smooth(dqdv, window=cfg.sg_window, poly=cfg.sg_poly)

            rec = {
                "tc": tc,
                "leg": leg,
                "n_standard": len(peaks_std),
                "n_banded": len(peaks_band),
                "standard_peaks": _fmt_peaks(peaks_std),
                "banded_peaks": _fmt_peaks(peaks_band, band=True),
                "delta_n": len(peaks_band) - len(peaks_std),
            }
            records.append(rec)

            png = out_dir / f"tc{tc:04d}_{leg}_band_review.png"
            save_review_png(
                vx=vx, dqdv=dqdv, y_smooth=y_smooth,
                peaks_std=peaks_std, peaks_band=peaks_band, bands=bands,
                tc=tc, leg=leg, out_png=png, cfg=cfg,
            )

    csv_out = out_dir / f"tc{cycle_start}_{cycle_end}_band_peak_review.csv"
    if records:
        with csv_out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            w.writeheader()
            w.writerows(records)

    charge_recs = [r for r in records if r["leg"] == "charge"]
    diff_std = sum(1 for r in charge_recs if r["delta_n"] != 0)
    (out_dir / "README.txt").write_text(
        "Peak review: SG w=31 standard find_peaks vs voltage band assign\n"
        f"source: {csv_path}\n"
        f"cycles: {cycle_start}-{cycle_end}\n\n"
        "Charge bands: P1_low 3.48-3.62 | P2_shoulder 3.60-3.78 | "
        "P3_main 3.78-3.94 | P4_high 3.94-4.12\n"
        "Discharge bands: P1_low 3.05-3.28 | P2_mid 3.55-3.78 | P3_high 3.82-4.00\n\n"
        f"Charge cycles where band != standard count: {diff_std}/{len(charge_recs)}\n",
        encoding="utf-8",
    )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Review banded vs standard peaks")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--start", type=int, default=70)
    parser.add_argument("--end", type=int, default=90)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--sg-window", type=int, default=31)
    args = parser.parse_args()

    cfg = DqdvPeakConfig(sg_window=args.sg_window)
    records = review_range(args.input, args.start, args.end, args.out_dir, cfg=cfg)

    print(f"Output: {args.out_dir}")
    print(f"{'TC':>4} {'leg':9} {'std':>3} {'band':>4}  banded peaks")
    for r in records:
        if r["leg"] != "charge":
            continue
        flag = " *" if r["delta_n"] != 0 else ""
        print(f"{r['tc']:4d} {r['leg']:9} {r['n_standard']:3d} {r['n_banded']:4d}{flag}  {r['banded_peaks']}")


if __name__ == "__main__":
    main()
