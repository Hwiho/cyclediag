"""Probe SJ900 StepEnd data for RPT exclusion and life-segment hints."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.features.stepemd_extract import extract_stepemd_features_table
from cyclediag.io.stepemd_csv import discover_stepemd_files


DATA_ROOT = Path(r"C:\00207966_260304_set1_SJ900_45도 0.5C cycle_no1_")
POST_RPT_EXCLUDE = 5
ROUTINE_STEPS = 4
DCHG_ROUTINE_MIN_AH = 50.0


def detect_rpt_blocks(raw: pd.DataFrame) -> tuple[set[int], pd.DataFrame]:
    """Return RPT/special cycle ids and per-cycle diagnostic flags."""
    rows = []
    rpt_cycles: set[int] = set()
    for cyc, grp in raw.groupby("TotalCycle"):
        cyc_i = int(cyc)
        n_steps = len(grp)
        caps = pd.to_numeric(grp.get("DischargeCapacity"), errors="coerce")
        dchg_mah = float(caps.max()) if caps.notna().any() else 0.0
        dchg_ah = dchg_mah / 1000.0 if dchg_mah > 200 else dchg_mah
        cur = pd.to_numeric(grp["Current"], errors="coerce").fillna(0.0)
        i_unique = int(cur.round(3).nunique())

        is_non_routine_steps = n_steps != ROUTINE_STEPS
        is_low_dchg = 0 < dchg_ah < DCHG_ROUTINE_MIN_AH
        is_multi_current = i_unique >= 4
        likely_rpt = is_non_routine_steps or is_low_dchg

        if likely_rpt:
            rpt_cycles.add(cyc_i)

        rows.append({
            "cycle": cyc_i,
            "n_steps": n_steps,
            "dchg_Ah": round(dchg_ah, 4),
            "i_unique": i_unique,
            "is_non_routine_steps": is_non_routine_steps,
            "is_low_dchg": is_low_dchg,
            "is_multi_current": is_multi_current,
            "likely_rpt": likely_rpt,
        })

    flags = pd.DataFrame(rows).sort_values("cycle")
    return rpt_cycles, flags


def rpt_blocks(sorted_rpt: list[int]) -> list[list[int]]:
    if not sorted_rpt:
        return []
    blocks: list[list[int]] = []
    blk = [sorted_rpt[0]]
    for c in sorted_rpt[1:]:
        if c == blk[-1] + 1:
            blk.append(c)
        else:
            blocks.append(blk)
            blk = [c]
    blocks.append(blk)
    return blocks


def excluded_cycles(rpt_cycles: set[int], post_exclude: int = POST_RPT_EXCLUDE) -> set[int]:
    bad = set(rpt_cycles)
    for block in rpt_blocks(sorted(rpt_cycles)):
        end = block[-1]
        for k in range(1, post_exclude + 1):
            bad.add(end + k)
    return bad


def fade_rate_pct_per_cycle(df: pd.DataFrame) -> float | None:
    if len(df) < 5:
        return None
    y = pd.to_numeric(df["SoHQ"], errors="coerce")
    x = pd.to_numeric(df["cycle"], errors="coerce")
    ok = y.notna() & x.notna()
    if ok.sum() < 5:
        return None
    slope, _ = np.polyfit(x[ok], y[ok], 1)
    return float(slope)


def piecewise_2seg(cycles: np.ndarray, sohq: np.ndarray) -> dict | None:
    """Simple 2-breakpoint search minimizing SSE (usable cycles only)."""
    n = len(cycles)
    if n < 20:
        return None
    best = None
    for i in range(8, n - 16):
        for j in range(i + 8, n - 8):
            c1, c2, c3 = cycles[:i], cycles[i:j], cycles[j:]
            y1, y2, y3 = sohq[:i], sohq[i:j], sohq[j:]
            if len(c1) < 5 or len(c2) < 5 or len(c3) < 5:
                continue
            s1 = np.polyfit(c1, y1, 1)
            s2 = np.polyfit(c2, y2, 1)
            s3 = np.polyfit(c3, y3, 1)
            pred = np.concatenate([
                np.polyval(s1, c1),
                np.polyval(s2, c2),
                np.polyval(s3, c3),
            ])
            sse = float(np.sum((sohq - pred) ** 2))
            if best is None or sse < best["sse"]:
                best = {
                    "bp1": int(cycles[i]),
                    "bp2": int(cycles[j]),
                    "slope1": float(s1[0]),
                    "slope2": float(s2[0]),
                    "slope3": float(s3[0]),
                    "sse": sse,
                }
    return best


def analyze_file(path: Path) -> dict:
    raw = pd.read_csv(path, encoding="cp949", low_memory=False)
    rpt_cycles, flags = detect_rpt_blocks(raw)
    excl = excluded_cycles(rpt_cycles)
    blocks = rpt_blocks(sorted(rpt_cycles))

    feat = extract_stepemd_features_table(path).sort_values("cycle")
    feat["usable"] = ~feat["cycle"].isin(excl)
    usable = feat[feat["usable"]].copy()

    pw = None
    if len(usable) >= 20:
        c = usable["cycle"].to_numpy(dtype=float)
        y = pd.to_numeric(usable["SoHQ"], errors="coerce").to_numpy(dtype=float)
        ok = np.isfinite(y)
        pw = piecewise_2seg(c[ok], y[ok])

    return {
        "cell_id": path.parent.name,
        "file": str(path),
        "n_cycles": int(feat["cycle"].nunique()),
        "n_rpt_cycles": len(rpt_cycles),
        "rpt_blocks": blocks,
        "n_excluded_total": len(excl),
        "n_usable": int(usable["cycle"].nunique()),
        "fade_all_pct_per_cyc": fade_rate_pct_per_cycle(feat),
        "fade_usable_pct_per_cyc": fade_rate_pct_per_cycle(usable),
        "sohq_end": float(pd.to_numeric(feat["SoHQ"], errors="coerce").iloc[-1]),
        "piecewise_3seg": pw,
        "flags": flags,
        "excluded_cycles": sorted(excl),
        "usable_cycles": usable["cycle"].astype(int).tolist(),
    }


def main() -> None:
    files = discover_stepemd_files(DATA_ROOT)
    out_dir = Path(__file__).resolve().parents[2] / "example" / "docs" / "sj900_set1_life_segments"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for path in files:
        res = analyze_file(path)
        cid = res["cell_id"]
        flags = res.pop("flags")
        excl = res.pop("excluded_cycles")
        usable = res.pop("usable_cycles")
        blocks = res.pop("rpt_blocks")
        pw = res.pop("piecewise_3seg")

        flags.to_csv(out_dir / f"{cid}_rpt_flags.csv", index=False)
        with open(out_dir / f"{cid}_exclude.json", "w", encoding="utf-8") as f:
            json.dump({
                "rpt_blocks": blocks,
                "excluded_cycles": excl,
                "usable_cycles": usable,
                "post_rpt_exclude": POST_RPT_EXCLUDE,
            }, f, indent=2)

        row = dict(res)
        row["rpt_block_starts"] = [b[0] for b in blocks]
        row["piecewise_bp1"] = pw["bp1"] if pw else None
        row["piecewise_bp2"] = pw["bp2"] if pw else None
        row["slope_seg1"] = pw["slope1"] if pw else None
        row["slope_seg2"] = pw["slope2"] if pw else None
        row["slope_seg3"] = pw["slope3"] if pw else None
        summary_rows.append(row)

        print(f"\n=== {cid} ===")
        print(f"  total cycles: {res['n_cycles']}")
        print(f"  RPT blocks ({len(blocks)}): {blocks}")
        print(f"  excluded (RPT + {POST_RPT_EXCLUDE} after each block): {res['n_excluded_total']} cycles")
        print(f"  usable for fade/segment: {res['n_usable']}")
        if res["fade_usable_pct_per_cyc"] is not None:
            print(f"  fade (usable): {res['fade_usable_pct_per_cyc']:.4f} %SoHQ/cycle")
        if pw:
            print(f"  3-seg breakpoints (usable): {pw['bp1']}, {pw['bp2']}")
            print(f"    slopes: {pw['slope1']:.4f} / {pw['slope2']:.4f} / {pw['slope3']:.4f} %/cyc")

    pd.DataFrame(summary_rows).to_csv(out_dir / "summary_rpt_exclude.csv", index=False)
    print(f"\nOutput: {out_dir}")


if __name__ == "__main__":
    main()
