"""Compare dQ/dV peak detection: Savitzky-Golay window 21 vs 31.

Usage:
  python cyclediag/tools/compare_sg_window_peaks.py --input path/to/raw.csv --cycles 10,50,80
"""

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

from cyclediag.features.dqdv_peaks import (  # noqa: E402
    DqdvPeakConfig,
    _smooth,
    find_dqdv_peaks,
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


def _peaks_for_leg(
    cycle_df: pd.DataFrame,
    leg: str,
    cfg: DqdvPeakConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]] | None:
    seg = leg_segment(cycle_df, leg, charge_text="charge", discharge_text="discharge")
    seg = prepare_leg_segment_for_dqdv(seg, leg)
    col = _capacity_col(seg, leg)
    if seg.empty or col is None or "voltage" not in seg.columns:
        return None
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, cfg)
    if len(vx) < 5:
        return None
    y_smooth = _smooth(dqdv, window=cfg.sg_window, poly=cfg.sg_poly)
    peaks = find_dqdv_peaks(v, q, config=cfg)
    return vx, dqdv, y_smooth, peaks


def _fmt_peaks(peaks: list[dict]) -> str:
    if not peaks:
        return "-"
    return "; ".join(f"P{i+1} {p['V']:.4f}V H={p['H']:.2g}" for i, p in enumerate(peaks))


def _delta_v(peaks_a: list[dict], peaks_b: list[dict]) -> list[float]:
    n = max(len(peaks_a), len(peaks_b))
    out: list[float] = []
    for i in range(n):
        if i < len(peaks_a) and i < len(peaks_b):
            out.append(abs(float(peaks_a[i]["V"]) - float(peaks_b[i]["V"])))
    return out


def save_compare_figure(
    *,
    vx: np.ndarray,
    dqdv: np.ndarray,
    y21: np.ndarray,
    y31: np.ndarray,
    peaks21: list[dict],
    peaks31: list[dict],
    tc: int,
    leg: str,
    out_png: Path,
) -> None:
    colors21 = plt.cm.Blues(np.linspace(0.5, 0.9, max(len(peaks21), 1)))
    colors31 = plt.cm.Oranges(np.linspace(0.5, 0.9, max(len(peaks31), 1)))

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, facecolor="white")
    for ax, y_smooth, peaks, w, colors, color_line in (
        (axes[0], y21, peaks21, 21, colors21, "#1d4ed8"),
        (axes[1], y31, peaks31, 31, colors31, "#c2410c"),
    ):
        ax.plot(vx, dqdv, color="#94a3b8", lw=0.8, alpha=0.7, label="dQ/dV raw")
        ax.plot(vx, y_smooth, color=color_line, lw=2.0, label=f"SG w={w}")
        for i, pk in enumerate(peaks):
            v_pk = float(pk["V"])
            j = int(np.argmin(np.abs(vx - v_pk)))
            ax.axvline(v_pk, color=colors[i % len(colors)], ls="--", lw=0.9, alpha=0.6)
            ax.scatter([v_pk], [y_smooth[j]], s=100, c=[colors[i % len(colors)]],
                       edgecolors="#111", linewidths=1.0, zorder=5)
            ax.annotate(f"P{i+1}", xy=(v_pk, y_smooth[j]), xytext=(6, 8),
                        textcoords="offset points", fontsize=9, fontweight="bold")
        ax.set_ylabel("dQ/dV")
        ax.set_title(f"Ch022 TC={tc} | {leg} | SG window={w} | {len(peaks)} peaks")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)

    axes[1].set_xlabel("Voltage (V)")
    fig.suptitle(f"Peak detection: SG w=21 (top) vs w=31 (bottom) | TC={tc} {leg}", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def compare(
    csv_path: Path,
    cycles: list[int],
    out_dir: Path,
    *,
    windows: tuple[int, ...] = (21, 31),
) -> list[dict]:
    if len(windows) != 2:
        raise ValueError("This tool compares exactly two SG windows")
    w_lo, w_hi = windows
    cfg_lo = DqdvPeakConfig(sg_window=w_lo)
    cfg_hi = DqdvPeakConfig(sg_window=w_hi)

    df = load_cycler_csv(str(csv_path), column_map=_studio_column_map())
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    for tc in cycles:
        cycle_df = df[df["cycle"] == tc].copy()
        if cycle_df.empty:
            records.append({"tc": tc, "leg": "", "status": "missing"})
            continue
        for leg in ("charge", "discharge"):
            r_lo = _peaks_for_leg(cycle_df, leg, cfg_lo)
            r_hi = _peaks_for_leg(cycle_df, leg, cfg_hi)
            if r_lo is None or r_hi is None:
                records.append({"tc": tc, "leg": leg, "status": "no_data"})
                continue
            vx, dqdv, y21, peaks21 = r_lo
            _, _, y31, peaks31 = r_hi
            dv = _delta_v(peaks21, peaks31)
            rec = {
                "tc": tc,
                "leg": leg,
                "status": "ok",
                f"n_w{w_lo}": len(peaks21),
                f"n_w{w_hi}": len(peaks31),
                f"peaks_w{w_lo}": _fmt_peaks(peaks21),
                f"peaks_w{w_hi}": _fmt_peaks(peaks31),
                "max_dV_match": max(dv) if dv else None,
                "mean_dV_match": float(np.mean(dv)) if dv else None,
            }
            records.append(rec)
            png = out_dir / f"tc{tc:04d}_{leg}_sg{w_lo}_vs_{w_hi}.png"
            save_compare_figure(
                vx=vx, dqdv=dqdv, y21=y21, y31=y31,
                peaks21=peaks21, peaks31=peaks31,
                tc=tc, leg=leg, out_png=png,
            )

    csv_out = out_dir / f"sg{w_lo}_vs_{w_hi}_comparison.csv"
    if records:
        fields = list(records[0].keys())
        with csv_out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(records)

    summary_path = out_dir / "README.txt"
    same_count = sum(
        1 for r in records
        if r.get("status") == "ok" and r.get(f"n_w{w_lo}") == r.get(f"n_w{w_hi}")
    )
    ok_count = sum(1 for r in records if r.get("status") == "ok")
    summary_path.write_text(
        f"SG window comparison: w={w_lo} vs w={w_hi}\n"
        f"source: {csv_path}\n"
        f"cycles: {cycles}\n"
        f"legs compared: {ok_count}\n"
        f"same peak count: {same_count}/{ok_count}\n",
        encoding="utf-8",
    )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare SG window 21 vs 31 peak detection")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--cycles", type=str, required=True, help="Comma-separated TotalCycle")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "example" / "docs" / "peak_review")
    parser.add_argument("--tag", type=str, default="sg_compare")
    parser.add_argument("--w1", type=int, default=21)
    parser.add_argument("--w2", type=int, default=31)
    args = parser.parse_args()

    cycles = [int(x.strip()) for x in args.cycles.split(",") if x.strip()]
    out_dir = args.out_dir / args.tag
    records = compare(args.input, cycles, out_dir, windows=(args.w1, args.w2))

    print(f"Output: {out_dir}")
    for r in records:
        if r.get("status") != "ok":
            print(f"  TC{r.get('tc')} {r.get('leg')}: {r.get('status')}")
            continue
        w1, w2 = args.w1, args.w2
        same = "SAME" if r[f"n_w{w1}"] == r[f"n_w{w2}"] else "DIFF"
        print(
            f"  TC{r['tc']:3d} {r['leg']:9s} [{same}] "
            f"n={r[f'n_w{w1}']}/{r[f'n_w{w2}']} "
            f"mean|dV|={r['mean_dV_match']:.4f}V max|dV|={r['max_dV_match']:.4f}V"
            if r.get("mean_dV_match") is not None else
            f"  TC{r['tc']:3d} {r['leg']:9s} [{same}] n={r[f'n_w{w1}']}/{r[f'n_w{w2}']}"
        )


if __name__ == "__main__":
    main()
