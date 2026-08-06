"""dQ/dV filter parameter sweep — IMPROVEMENT_ROADMAP §5.1.

Usage:
  python -m cyclediag.tools.diagnose_dqdv_filter_sweep \\
    --input path/to/raw.csv --rpt-cycle 107 --routine-cycle 50 --leg discharge
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths, savgol_filter

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv  # noqa: E402

GRID = {
    "n_interp": [500, 1500, 3000],
    "sg_window": [7, 11, 21, 31],
    "sg_poly": [3],
    "merge_dv": [0.012, 0.006, 0.003],
    "min_distance_frac": [0.04, 0.015],
}
PROM_FRAC = 0.02
MIN_WIDTH = 5


def _leg_mask(df: pd.DataFrame, leg: str, rest_current_max: float) -> pd.Series:
    cur = pd.to_numeric(df["current"], errors="coerce")
    active = cur.abs() > rest_current_max
    if leg == "discharge":
        m = active & (cur < 0)
    else:
        m = active & (cur > 0)
    if m.sum() < 50:
        m = active & (cur > 0) if leg == "discharge" else active & (cur < 0)
    return m


def _dqdv(q: np.ndarray, v: np.ndarray, n_interp: int, sg_window: int, sg_poly: int):
    q = np.abs(q - q[0])
    order = np.argsort(q)
    q, v = q[order], v[order]
    _, uid = np.unique(np.round(q, 9), return_index=True)
    q, v = q[uid], v[uid]
    if len(q) < 20:
        return None
    qg = np.linspace(float(q.min()), float(q.max()), n_interp)
    vg = np.interp(qg, q, v)
    win = int(sg_window)
    if win % 2 == 0:
        win += 1
    win = int(np.clip(win, sg_poly + 2, max(sg_poly + 2, (len(qg) // 2) * 2 - 1)))
    vs = savgol_filter(vg, win, sg_poly)
    qs = savgol_filter(qg, win, sg_poly)
    dv = np.gradient(vs)
    dq = np.gradient(qs)
    with np.errstate(divide="ignore", invalid="ignore"):
        dqdv = np.where(np.abs(dv) > 1e-9, dq / dv, np.nan)
    # fill nan
    s = pd.Series(dqdv).interpolate(limit_direction="both").to_numpy()
    return qg, vs, np.abs(s), win


def _merge_peaks(v: np.ndarray, idx: np.ndarray, h: np.ndarray, merge_dv: float) -> np.ndarray:
    if len(idx) == 0:
        return idx
    keep = [int(idx[0])]
    for i in idx[1:]:
        i = int(i)
        last = keep[-1]
        if abs(float(v[i]) - float(v[last])) < merge_dv:
            if h[i] > h[last]:
                keep[-1] = i
        else:
            keep.append(i)
    return np.asarray(keep, dtype=int)


def evaluate_combo(q, v, *, n_interp, sg_window, sg_poly, merge_dv, min_distance_frac):
    got = _dqdv(q, v, n_interp, sg_window, sg_poly)
    if got is None:
        return {"n_peaks": -1}
    qg, vs, dqdv, win = got
    ah_per_pt = float(np.median(np.abs(np.diff(qg))))
    mv_per_pt = float(np.median(np.abs(np.diff(vs)))) * 1000.0
    smooth_Ah = ah_per_pt * win
    smooth_mV = mv_per_pt * win
    span = float(np.nanmax(dqdv) - np.nanmin(dqdv))
    if span <= 0:
        return {"n_peaks": 0, "smooth_mV": smooth_mV}
    prom = PROM_FRAC * span
    dist = max(1, int(min_distance_frac * n_interp))
    idx, props = find_peaks(dqdv, prominence=prom, distance=dist, width=MIN_WIDTH)
    h = dqdv[idx] if len(idx) else np.array([])
    idx = _merge_peaks(vs, idx, h, merge_dv)
    rs_min = rs_med = np.nan
    if len(idx) >= 2:
        widths = peak_widths(dqdv, idx, rel_height=0.5)[0]
        wV = widths * float(np.median(np.abs(np.diff(vs))))
        rs = []
        for a, b, wa, wb in zip(idx[:-1], idx[1:], wV[:-1], wV[1:]):
            rs.append(abs(float(vs[b]) - float(vs[a])) / (1.18 * (wa + wb) + 1e-15))
        rs_min, rs_med = float(np.min(rs)), float(np.median(rs))
    risk = smooth_mV / max(merge_dv * 1000.0, 1e-9)
    return {
        "n_peaks": int(len(idx)),
        "ah_per_pt": ah_per_pt,
        "mv_per_pt": mv_per_pt,
        "smooth_Ah": smooth_Ah,
        "smooth_mV": smooth_mV,
        "min_dist_Ah": ah_per_pt * min_distance_frac * n_interp,
        "Rs_min": rs_min,
        "Rs_med": rs_med,
        "smooth_vs_merge": risk,
        "artifact_risk": "HIGH" if risk >= 1.0 else ("MED" if risk >= 0.4 else "LOW"),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="§5.1 dQ/dV filter sweep diagnostic")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--rpt-cycle", type=int, required=True)
    p.add_argument("--routine-cycle", type=int, required=True)
    p.add_argument("--leg", choices=("charge", "discharge"), default="discharge")
    p.add_argument("--rest-current-max", type=float, default=0.5)
    p.add_argument("--out-dir", type=Path, default=Path("example/docs/peak_review/filter_sweep"))
    args = p.parse_args()

    df = load_cycler_csv(str(args.input), column_map=ColumnMap.studio_default())
    rows = []
    legs = {}
    for label, cyc in (("rpt", args.rpt_cycle), ("routine", args.routine_cycle)):
        g = df[df["cycle"] == cyc]
        m = _leg_mask(g, args.leg, args.rest_current_max)
        seg = g.loc[m]
        if len(seg) < 50:
            raise SystemExit(f"{label} cycle {cyc} leg {args.leg}: samples < 50")
        qcol = "discharge_capacity" if args.leg == "discharge" and "discharge_capacity" in seg.columns else "capacity"
        if args.leg == "charge" and "charge_capacity" in seg.columns:
            qcol = "charge_capacity"
        q = pd.to_numeric(seg[qcol], errors="coerce").to_numpy(dtype=float)
        v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
        legs[label] = (q, v)

    for n_interp in GRID["n_interp"]:
        for sg_window in GRID["sg_window"]:
            for sg_poly in GRID["sg_poly"]:
                for merge_dv in GRID["merge_dv"]:
                    for min_df in GRID["min_distance_frac"]:
                        row = {
                            "n_interp": n_interp,
                            "sg_window": sg_window,
                            "sg_poly": sg_poly,
                            "merge_dv": merge_dv,
                            "min_distance_frac": min_df,
                        }
                        for label, (q, v) in legs.items():
                            ev = evaluate_combo(
                                q, v,
                                n_interp=n_interp,
                                sg_window=sg_window,
                                sg_poly=sg_poly,
                                merge_dv=merge_dv,
                                min_distance_frac=min_df,
                            )
                            for k, val in ev.items():
                                row[f"{label}_{k}"] = val
                        rows.append(row)

    res = pd.DataFrame(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "sweep_results.csv"
    res.to_csv(csv_path, index=False)

    # verdict
    valid = res[(res["rpt_n_peaks"] >= 0) & (res["routine_n_peaks"] >= 0)]
    rpt_ref = float(valid["rpt_n_peaks"].median()) if len(valid) else 0
    recovered = valid[
        (valid["routine_n_peaks"] >= valid["rpt_n_peaks"])
        & (valid["routine_n_peaks"] >= rpt_ref)
    ].copy()
    verdict = "B_artifact" if len(recovered) else "A_physical_merge"
    if len(recovered):
        recovered = recovered.sort_values(
            by=["routine_Rs_min", "routine_smooth_mV"],
            ascending=[False, True],
        )
    summary = [
        f"verdict={verdict}",
        f"rpt_ref_median_peaks={rpt_ref}",
        f"n_recovered={len(recovered)}",
        f"baseline_row sg21/n500/merge12: see csv",
        "",
        "top recommendations:",
    ]
    show = recovered.head(10) if len(recovered) else valid.sort_values("routine_Rs_min", ascending=False).head(10)
    summary.append(show.to_string(index=False))
    (args.out_dir / "sweep_summary.txt").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary[:8]))
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
