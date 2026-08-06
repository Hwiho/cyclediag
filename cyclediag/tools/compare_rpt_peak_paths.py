"""Compare §7-4 peak counts: original vs current detector paths."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, prepare_dqdv_arrays, _smooth
from cyclediag.features.peak_evolution import PeakEvolutionConfig, _cycle_curve, _select_cycles_by_rate
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv
from cyclediag.io.stepemd_csv import load_stepemd_csv

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "example/docs/features/M01Ch022/00207966_260304_set4_SJ900_45도 0.5C cycle_no1_2_4_[Ch22]__QN_mono_#1_raw.csv"
STEP = ROOT / "example/docs/features/M01Ch022/00207966_260304_set4_SJ900_45도 0.5C cycle_no1_2_4_[Ch22]__QN_mono_#1_stepend.csv"
OUT = ROOT / "example/output/peak_evolution_ch22_v2/rpt_peak_path_compare.json"


def _count(y: np.ndarray, *, prom_frac: float = 0.02) -> tuple[int, list[int]]:
    y = np.asarray(y, dtype=float)
    if not np.isfinite(y).any() or float(np.nanmax(np.abs(y))) <= 0:
        return 0, []
    ys = np.nan_to_num(np.abs(y), nan=0.0)
    prom = prom_frac * float(np.nanmax(ys))
    idx, _ = find_peaks(ys, prominence=prom, distance=max(5, len(ys) // 25))
    return int(len(idx)), [int(i) for i in idx]


def main() -> None:
    raw = load_cycler_csv(RAW, column_map=ColumnMap.studio_default())
    step = load_stepemd_csv(STEP)
    cfg = PeakEvolutionConfig()
    cycles = _select_cycles_by_rate(raw, step, "C/3", cfg)[:4]
    cases = [
        ("v1_original_dqdv_sg11_n500_full", DqdvPeakConfig(n_interp=500, sg_window=11, sg_poly=3), "dqdv", None),
        ("v1_like_dvdq_sg11_n500_full", DqdvPeakConfig(n_interp=500, sg_window=11, sg_poly=3), "dvdq", None),
        ("v2_dvdq_sg7_n2500_full", DqdvPeakConfig(n_interp=2500, sg_window=7, sg_poly=3, merge_v_sep_v=0.003), "dvdq", None),
        ("v2_dvdq_sg7_n2500_Q015_085", DqdvPeakConfig(n_interp=2500, sg_window=7, sg_poly=3, merge_v_sep_v=0.003), "dvdq", (0.15, 0.85)),
        ("v2_dqdv_sg7_n2500_full", DqdvPeakConfig(n_interp=2500, sg_window=7, sg_poly=3, merge_v_sep_v=0.003), "dqdv", None),
        ("v2_dqdv_sg7_n2500_Q015_085", DqdvPeakConfig(n_interp=2500, sg_window=7, sg_poly=3, merge_v_sep_v=0.003), "dqdv", (0.15, 0.85)),
    ]
    rows = []
    for label, dcfg, sig, qroi in cases:
        for cyc in cycles:
            got = _cycle_curve(raw, int(cyc), cfg)
            if got is None:
                continue
            v, q, total_q = got
            vx, dqdv, qx, dvdq = prepare_dqdv_arrays(v, q, dcfg)
            y = dvdq if sig == "dvdq" else dqdv
            qn = qx / total_q if total_q > 0 else np.full_like(qx, np.nan)
            if qroi is not None:
                y = np.where((qn >= qroi[0]) & (qn <= qroi[1]), y, np.nan)
            y_s = _smooth(np.nan_to_num(y, nan=0.0), window=dcfg.sg_window, poly=3)
            n, idx = _count(y_s)
            peak_q = [float(qn[i]) for i in idx if i < len(qn) and np.isfinite(qn[i])]
            peak_v = [float(vx[i]) for i in idx if i < len(vx) and np.isfinite(vx[i])]
            rows.append({
                "case": label,
                "cycle": int(cyc),
                "signal": sig,
                "q_roi": qroi,
                "n_peaks": n,
                "peak_Q_norm": peak_q,
                "peak_V": peak_v,
                "n_outside_015_085": int(sum(1 for qq in peak_q if qq < 0.15 or qq > 0.85)),
                "n_inside_015_085": int(sum(1 for qq in peak_q if 0.15 <= qq <= 0.85)),
            })
    summary = {}
    for label, *_ in cases:
        sub = [r for r in rows if r["case"] == label]
        summary[label] = {
            "max_n_peaks": max((r["n_peaks"] for r in sub), default=0),
            "by_cycle": {str(r["cycle"]): r["n_peaks"] for r in sub},
            "peak_Q_norm_example": next((r["peak_Q_norm"] for r in sub if r["n_peaks"]), []),
        }
    out = {"cycles": cycles, "summary": summary, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
