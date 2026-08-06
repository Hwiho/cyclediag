"""Export dQ/dV curve + numbered peak assignment PNGs for manual review.

Usage:
  python cyclediag/tools/export_dqdv_peak_review.py
  python cyclediag/tools/export_dqdv_peak_review.py --input path/to/cell_raw.csv --tagged 1
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
    DEFAULT_DQDV_PEAK_CONFIG,
    DqdvPeakConfig,
    _smooth,
    find_dqdv_peaks,
    prepare_dqdv_arrays,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv  # noqa: E402
from cyclediag.features.segment_utils import leg_segment  # noqa: E402
from cyclediag.io.classification_pairs import (  # noqa: E402
    classification_path_for_raw,
    load_pair_cycles,
    resolve_tagged_raw_cycle,
    tagged_entries,
)
from cyclediag.io.cycler_csv import load_cycler_csv  # noqa: E402
from cyclediag.io.studio_map import studio_column_map  # noqa: E402

DEFAULT_SAMPLE = (
    ROOT
    / "_vendor"
    / "Ensol_PNE_framework"
    / "Test_raw"
    / "구동압별"
    / "3.0 MPa"
    / "cycle"
    / "07100395_260205_이규남_구동압별_cycle(RPT)_1–100cyc_3.0MPa"
    / "M01Ch009[009]"
    / "07100395_260205_이규남_구동압별_cycle(RPT)_1–100cyc_3.0MPa_[Ch9]__QN_mono_#9_raw.csv"
)


def _capacity_array(seg: pd.DataFrame, leg: str) -> np.ndarray | None:
    col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if col not in seg.columns:
        col = "capacity"
    if col not in seg.columns:
        return None
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
    return q if np.isfinite(q).any() else None


def _peak_index_on_grid(vx: np.ndarray, v_peak: float) -> int:
    return int(np.argmin(np.abs(vx - v_peak)))


def resolve_export_cycle(
    csv_path: Path,
    df: pd.DataFrame,
    *,
    raw_cycle: int | None,
    tagged_number: int | None,
) -> tuple[int, str, int | None]:
    """Return (raw_total_cycle, subtitle, tagged_number)."""
    pair_cycles: dict[int, str] = {}
    cls_path = classification_path_for_raw(csv_path)
    if cls_path is not None:
        pair_cycles = load_pair_cycles(cls_path)

    if raw_cycle is not None:
        label = pair_cycles.get(raw_cycle, "")
        tagged = None
        if label:
            import re
            m = re.match(r"(?i)cycle-?(\d+)", label)
            if m:
                tagged = int(m.group(1))
        return int(raw_cycle), label or f"raw TC={raw_cycle}", tagged

    tagged_n = 1 if tagged_number is None else int(tagged_number)
    resolved = resolve_tagged_raw_cycle(pair_cycles, tagged_n)
    if resolved is not None:
        raw, label = resolved
        return raw, label, tagged_n

    if pair_cycles:
        entries = tagged_entries(pair_cycles)
        hint = ", ".join(f"{t}->{r}" for t, r, _ in entries[:5])
        raise ValueError(
            f"No tagged Cycle-{tagged_n:03d} in classification. "
            f"Available: {hint}{'...' if len(entries) > 5 else ''}"
        )

    raw = int(df["cycle"].min())
    return raw, f"raw TC={raw} (no Cycle-N in classification)", None


def save_leg_review_figure(
    *,
    vx: np.ndarray,
    dqdv: np.ndarray,
    peaks: list[dict],
    leg: str,
    cycle_label: str,
    source_label: str,
    out_png: Path,
    cfg: DqdvPeakConfig,
) -> None:
    y_smooth = _smooth(dqdv, window=cfg.sg_window, poly=cfg.sg_poly)

    fig = plt.figure(figsize=(12, 7.5), facecolor="white")
    gs = fig.add_gridspec(2, 1, height_ratios=[3.2, 1.0], hspace=0.28)
    ax = fig.add_subplot(gs[0, 0])
    ax_tbl = fig.add_subplot(gs[1, 0])
    ax_tbl.axis("off")

    ax.plot(vx, dqdv, color="#94a3b8", lw=0.9, alpha=0.85, label="dQ/dV (Q-grid 500pt)")
    ax.plot(vx, y_smooth, color="#047857", lw=2.2, label=f"dQ/dV SG w={cfg.sg_window}")

    colors = plt.cm.Set1(np.linspace(0, 0.85, max(len(peaks), 1)))
    for i, pk in enumerate(peaks):
        j = _peak_index_on_grid(vx, float(pk["V"]))
        c = colors[i % len(colors)]
        v_pk = float(pk["V"])
        y_pk = float(y_smooth[j])
        ax.axvline(v_pk, color=c, ls="--", lw=1.0, alpha=0.55)
        ax.scatter([v_pk], [y_pk], s=140, c=[c], edgecolors="#111", linewidths=1.2, zorder=6)
        ax.annotate(
            f"P{i + 1}",
            xy=(v_pk, y_pk),
            xytext=(8, 12 if i % 2 == 0 else -18),
            textcoords="offset points",
            fontsize=11,
            fontweight="bold",
            color=c,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=c, alpha=0.9),
        )

    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("dQ/dV")
    ax.set_title(f"{source_label} | {cycle_label} | {leg} | Q-interp {cfg.n_interp}pt")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)

    rows = [["Peak#", "V (V)", "H (height)", "Note"]]
    for i, pk in enumerate(peaks, start=1):
        rows.append([f"P{i}", f"{float(pk['V']):.5f}", f"{float(pk['H']):.6g}", "assigned"])
    if len(peaks) == 0:
        rows.append(["-", "-", "-", "no peak passed filters"])

    table = ax_tbl.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.5)
    for (row, _col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#e2e8f0")
            cell.set_text_props(fontweight="bold")

    fig.savefig(out_png, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def export_review(
    csv_path: Path,
    out_dir: Path,
    *,
    raw_cycle: int | None = None,
    tagged_number: int | None = 1,
    charge_text: str = "charge",
    discharge_text: str = "discharge",
    cfg: DqdvPeakConfig | None = None,
) -> list[dict]:
    cfg = cfg or DEFAULT_DQDV_PEAK_CONFIG
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_cycler_csv(str(csv_path), column_map=studio_column_map())
    cycle, cycle_label, tagged = resolve_export_cycle(
        csv_path, df, raw_cycle=raw_cycle, tagged_number=tagged_number,
    )
    cycle_df = df[df["cycle"] == cycle].copy()
    if cycle_df.empty:
        raise ValueError(f"raw cycle {cycle} not found in {csv_path.name}")

    stem = csv_path.stem.replace("_raw", "")
    file_tag = f"tagged{tagged:03d}" if tagged is not None else f"raw{cycle:04d}"
    records: list[dict] = []

    for leg in ("charge", "discharge"):
        seg = leg_segment(
            cycle_df,
            leg,
            charge_text=charge_text,
            discharge_text=discharge_text,
        )
        seg = prepare_leg_segment_for_dqdv(seg, leg)
        q = _capacity_array(seg, leg)
        if seg.empty or q is None or "voltage" not in seg.columns:
            continue
        v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
        peaks = find_dqdv_peaks(v, q, config=cfg)
        vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, cfg)
        if len(vx) == 0:
            continue

        png_name = f"{file_tag}_{leg}_dqdv_peaks.png"
        save_leg_review_figure(
            vx=vx,
            dqdv=dqdv,
            peaks=peaks,
            leg=leg,
            cycle_label=cycle_label,
            source_label=stem,
            out_png=out_dir / png_name,
            cfg=cfg,
        )

        for i, pk in enumerate(peaks, start=1):
            records.append({
                "file": csv_path.name,
                "tagged_cycle": tagged if tagged is not None else "",
                "raw_total_cycle": cycle,
                "pair_label": cycle_label,
                "leg": leg,
                "peak_num": i,
                "V": pk["V"],
                "H": pk["H"],
                "png": png_name,
            })

    csv_out = out_dir / f"{file_tag}_peak_assignment.csv"
    if records:
        with csv_out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            w.writeheader()
            w.writerows(records)
    else:
        csv_out.write_text("no peaks\n", encoding="utf-8")

    (out_dir / "README.txt").write_text(
        "dQ/dV peak review export\n"
        f"source: {csv_path}\n"
        f"cycle: {cycle_label} (raw TotalCycle={cycle})\n"
        f"tagged_cycle: {tagged if tagged is not None else 'n/a'}\n"
        f"Q-interp: {cfg.n_interp} points, axis={cfg.interp_axis}\n"
        "prep: trim low-Q start + CV trim (charge)\n",
        encoding="utf-8",
    )
    return records


def main():
    parser = argparse.ArgumentParser(description="Export dQ/dV + peak assignment PNGs")
    parser.add_argument("--input", type=Path, default=DEFAULT_SAMPLE if DEFAULT_SAMPLE.exists() else None)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "example" / "docs" / "peak_review")
    parser.add_argument("--cycle", type=int, default=None, help="Raw TotalCycle (overrides --tagged)")
    parser.add_argument("--tagged", type=int, default=1, help="Tagged Cycle-N number (default: 1)")
    parser.add_argument("--tag", type=str, default="", help="Output subfolder name")
    args = parser.parse_args()

    if args.input is None or not args.input.exists():
        print("No input CSV. Use --input path/to/*_raw.csv")
        sys.exit(1)

    out_tag = args.tag.strip() or "tagged_cycle_export"
    out_dir = args.out_dir / out_tag
    records = export_review(
        args.input,
        out_dir,
        raw_cycle=args.cycle,
        tagged_number=None if args.cycle is not None else args.tagged,
    )
    print(f"Output folder: {out_dir}")
    for r in records:
        print(
            f"  {r['leg']} P{r['peak_num']}: V={r['V']:.5f} H={r['H']:.6g} "
            f"(raw TC={r['raw_total_cycle']}) -> {r['png']}"
        )
    if not records:
        print("  (no peaks exported)")


if __name__ == "__main__":
    main()
