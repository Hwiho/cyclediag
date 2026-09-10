"""Score dQ/dV cycle quality (noise, peak count) for golden cycle selection."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import (  # noqa: E402
    DEFAULT_DQDV_PEAK_CONFIG,
    _noise_mad,
    _smooth,
    find_dqdv_peaks,
    prepare_dqdv_arrays,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv  # noqa: E402
from cyclediag.features.segment_utils import leg_segment  # noqa: E402
from cyclediag.io.cycler_csv import load_cycler_csv  # noqa: E402
from cyclediag.io.studio_map import capacity_col, studio_column_map  # noqa: E402


def score_cycles(csv_path: Path, *, cfg=DEFAULT_DQDV_PEAK_CONFIG) -> list[dict]:
    df = load_cycler_csv(str(csv_path), column_map=studio_column_map())
    cycles = sorted(int(c) for c in df["cycle"].dropna().unique())
    rows: list[dict] = []

    for tc in cycles:
        cyc = df[df["cycle"] == tc]
        for leg in ("charge", "discharge"):
            seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
            seg = prepare_leg_segment_for_dqdv(seg, leg)
            col = capacity_col(seg, leg)
            if seg.empty or col is None or "voltage" not in seg.columns:
                rows.append({"tc": tc, "leg": leg, "ok": False})
                continue
            v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
            q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
            vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, cfg)
            if len(vx) < 5:
                rows.append({"tc": tc, "leg": leg, "ok": False})
                continue
            y_smooth = _smooth(dqdv, window=cfg.sg_window, poly=cfg.sg_poly)
            mad = _noise_mad(dqdv, y_smooth)
            ymax = float(np.nanmax(np.abs(y_smooth))) if len(y_smooth) else 0.0
            noise_ratio = mad / ymax if ymax > 0 else 999.0
            hf = float(np.nanstd(np.diff(y_smooth))) if len(y_smooth) > 2 else 999.0
            peaks = find_dqdv_peaks(v, q, config=cfg)
            rows.append({
                "tc": tc,
                "leg": leg,
                "ok": True,
                "n_peaks": len(peaks),
                "noise_ratio": noise_ratio,
                "hf_std": hf,
                "ymax": ymax,
                "peak_vs": [float(p["V"]) for p in peaks],
                "peak_hs": [abs(float(p["H"])) for p in peaks],
                "n_pts": len(seg),
            })

    by_tc: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("ok"):
            by_tc[int(r["tc"])].append(r)

    scores: list[dict] = []
    for tc, legs in by_tc.items():
        if len(legs) < 2:
            continue
        ch = next(x for x in legs if x["leg"] == "charge")
        dc = next(x for x in legs if x["leg"] == "discharge")
        peak_pen = abs(ch["n_peaks"] - 3) + abs(dc["n_peaks"] - 3)
        noise = (ch["noise_ratio"] + dc["noise_ratio"]) / 2.0
        hf = (ch["hf_std"] + dc["hf_std"]) / 2.0
        pts_ok = min(ch["n_pts"], dc["n_pts"]) >= 100
        quality = noise * 3.0 + hf * 0.15 + peak_pen * 0.25
        if not pts_ok:
            quality += 5.0
        scores.append({
            "tc": tc,
            "quality": quality,
            "noise_ratio": noise,
            "hf_std": hf,
            "ch_peaks": ch["n_peaks"],
            "dc_peaks": dc["n_peaks"],
            "ch_V": ch["peak_vs"],
            "dc_V": dc["peak_vs"],
            "ch_H": ch["peak_hs"],
            "dc_H": dc["peak_hs"],
        })

    scores.sort(key=lambda x: x["quality"])
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Score dQ/dV cycle quality")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--check", type=str, default="", help="Comma-separated TC to rank-check")
    args = parser.parse_args()

    scores = score_cycles(args.input)
    out = args.out or args.input.parent / f"{args.input.stem}_cycle_quality.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "tc", "quality", "noise_ratio", "hf_std",
                "ch_peaks", "dc_peaks", "ch_V", "dc_V", "ch_H", "dc_H",
            ],
        )
        w.writeheader()
        for s in scores:
            row = dict(s)
            row["ch_V"] = "|".join(f"{v:.5f}" for v in s["ch_V"])
            row["dc_V"] = "|".join(f"{v:.5f}" for v in s["dc_V"])
            row["ch_H"] = "|".join(f"{h:.4g}" for h in s["ch_H"])
            row["dc_H"] = "|".join(f"{h:.4g}" for h in s["dc_H"])
            w.writerow(row)

    print(f"Scored {len(scores)} cycles -> {out}")
    print(f"TOP {args.top} low-noise cycles:")
    for s in scores[: args.top]:
        ch_v = ", ".join(f"{v:.3f}" for v in s["ch_V"])
        dc_v = ", ".join(f"{v:.3f}" for v in s["dc_V"])
        print(
            f"  TC{s['tc']:4d} q={s['quality']:.4f} noise={s['noise_ratio']:.4f} "
            f"peaks={s['ch_peaks']}/{s['dc_peaks']} chV=[{ch_v}] dcV=[{dc_v}]"
        )

    if args.check.strip():
        picks = [int(x.strip()) for x in args.check.split(",") if x.strip()]
        for pick in picks:
            match = next((s for s in scores if s["tc"] == pick), None)
            if match is None:
                print(f"  USER TC{pick}: not found")
                continue
            rank = scores.index(match) + 1
            print(
                f"  USER TC{pick}: rank {rank}/{len(scores)} "
                f"quality={match['quality']:.4f} noise={match['noise_ratio']:.4f} "
                f"peaks={match['ch_peaks']}/{match['dc_peaks']}"
            )


if __name__ == "__main__":
    main()
