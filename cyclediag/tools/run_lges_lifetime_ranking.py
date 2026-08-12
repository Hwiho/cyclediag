"""Rank LGES extract indicators by Spearman correlation with cell lifetime.

Lifetime = max tagged routine cycle count per cell.
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from cyclediag.features.indicator_registry import primary_indicator_columns
from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_features_table
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv

warnings.filterwarnings("ignore", category=RuntimeWarning)

DEFAULT_CELLS = [
    ("DOE1/set4_SJ900", "M01Ch022"),
    ("DOE1/set4_SJ900", "M01Ch024"),
    ("DOE1/set4_SJ900", "M01Ch025"),
    ("DOE2/SJ1300_dry", "M01Ch010"),
    ("DOE2/SJ1300_dry", "M01Ch011"),
    ("DOE2/SJ1300_dry", "M01Ch012"),
]

# Pre-exported tagged LGES tables (skip slow re-extract when present)
PREEXPORTED: dict[str, Path] = {
    "M01Ch022": Path("example/output/set4/M01Ch022_cycle_indicators_tagged_full.csv"),
    "M01Ch025": Path("example/output/set4/M01Ch025_cycle_indicators_tagged_full.csv"),
}

DOE2_IDS = {"M01Ch022", "M01Ch024", "M01Ch025", "M01Ch010", "M01Ch011", "M01Ch012"}

# Ranking indicators against lifetime is circular for anything computed from
# the health target itself. Roles and duplicate families are handled by the
# indicator registry; only this leakage guard is specific to the tool.
TARGET_DERIVED = {
    "dSoHQ_dN",
    "d2SoHQ",
    "CE",
    "CE_rev",
    "CE_local_20",
}


def _feature_cols(feat: pd.DataFrame) -> list[str]:
    cols = [
        c for c in primary_indicator_columns(feat)
        if c not in TARGET_DERIVED
        and pd.to_numeric(feat[c], errors="coerce").notna().sum() > 0
    ]
    return sorted(set(cols))


def _tagged_routine_cycles(raw: pd.DataFrame) -> list[int]:
    se = raw.groupby(["cycle", "StepNo"], as_index=False).tail(1)
    prot = build_protocol_exclusion(se)
    flags = detect_protocol_flags(se)
    routine = flags[
        (flags["protocol_kind"] == "routine") & (~flags["cycle"].isin(prot.excluded))
    ].sort_values("cycle")
    return [int(c) for c in routine["cycle"]]


def _extract_cell(csv_path: Path, cell_id: str) -> pd.DataFrame:
    cmap = ColumnMap.studio_default()
    raw = load_cycler_csv(str(csv_path), column_map=cmap)
    tagged_raw = _tagged_routine_cycles(raw)
    if not tagged_raw:
        return pd.DataFrame()
    cfg = LgesExtractConfig(cell_id=cell_id, baseline_cycle=tagged_raw[0])
    table = extract_lges_features_table(
        raw,
        cycles=tagged_raw,
        filepath=str(csv_path),
        config=cfg,
        raw_df=raw,
    )
    if table.empty:
        return table
    raw_to_tag = {r: i for i, r in enumerate(tagged_raw, start=1)}
    out = table.copy()
    out["cycle"] = pd.to_numeric(out["cycle"], errors="coerce")
    out["tagged_cycle"] = out["cycle"].map(lambda c: raw_to_tag.get(int(c)) if pd.notna(c) else None)
    out["tagged_source"] = "routine"
    out = out[out["tagged_cycle"].notna()].sort_values("tagged_cycle")
    return out


def _load_preexported(path: Path, *, cell_id: str, arm: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["cell_id"] = cell_id
    df["arm"] = arm
    if "tagged_cycle" not in df.columns and "cycle" in df.columns:
        df["tagged_cycle"] = pd.to_numeric(df["cycle"], errors="coerce")
    return df


def _load(fixtures_root: Path, cells: list[tuple[str, str]], *, cache_dir: Path | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    parts: list[pd.DataFrame] = []
    life_rows: list[dict] = []
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
    for arm, cid in cells:
        cache_path = cache_dir / f"{cid}_tagged.parquet" if cache_dir else None
        df = pd.DataFrame()
        if cache_path is not None and cache_path.exists():
            df = pd.read_parquet(cache_path)
            print(f"cache {cid}: rows={len(df)}")
        elif cid in PREEXPORTED and PREEXPORTED[cid].exists():
            df = _load_preexported(PREEXPORTED[cid], cell_id=cid, arm=arm)
            print(f"preexport {cid}: rows={len(df)}")
        else:
            p = fixtures_root / arm / f"{cid}_raw.csv"
            if not p.exists():
                print(f"skip missing {p}")
                continue
            print(f"extract {cid} …", flush=True)
            df = _extract_cell(p, cid)
            if df.empty:
                print(f"empty {cid}")
                continue
            df["arm"] = arm
            if cache_path is not None:
                df.to_parquet(cache_path, index=False)
        if df.empty:
            continue
        if "arm" not in df.columns:
            df["arm"] = arm
        df["arm"] = arm
        tmax = int(df["tagged_cycle"].max())
        sohq_eol = float(
            pd.to_numeric(df.loc[df["tagged_cycle"] >= tmax - 2, "SoHQ"], errors="coerce").mean()
        )
        life_rows.append(
            {
                "cell_id": cid,
                "arm": arm,
                "life_tagged": tmax,
                "life_raw_max": int(df["cycle"].max()),
                "sohq_eol": sohq_eol,
            }
        )
        parts.append(df)
        print(f"ok {cid}: life={tmax} tagged, SoHQ_EOL~{sohq_eol:.1f}%")
    if not parts:
        return pd.DataFrame(), pd.DataFrame()
    return pd.concat(parts, ignore_index=True), pd.DataFrame(life_rows)


def _cell_stats(feat: pd.DataFrame, cols: list[str], *, early_n: int = 30) -> pd.DataFrame:
    rows: list[dict] = []
    for _, g in feat.groupby("cell_id"):
        g = g.sort_values("tagged_cycle")
        t = pd.to_numeric(g["tagged_cycle"], errors="coerce")
        early = g[t <= min(early_n, int(t.max()))]
        late_thr = float(t.quantile(0.8))
        late = g[t >= late_thr]
        eol = g[t >= t.max() - 4]
        out: dict = {"cell_id": g["cell_id"].iloc[0], "arm": g["arm"].iloc[0]}
        for col in cols:
            s = pd.to_numeric(g[col], errors="coerce")
            se = pd.to_numeric(early[col], errors="coerce")
            sl = pd.to_numeric(late[col], errors="coerce")
            seol = pd.to_numeric(eol[col], errors="coerce")
            if s.notna().sum() < 5:
                continue
            out[f"early_{col}"] = float(se.mean()) if se.notna().any() else np.nan
            out[f"late_{col}"] = float(sl.mean()) if sl.notna().any() else np.nan
            out[f"eol_{col}"] = float(seol.mean()) if seol.notna().any() else np.nan
            if np.isfinite(out[f"late_{col}"]) and np.isfinite(out[f"early_{col}"]):
                out[f"delta_{col}"] = out[f"late_{col}"] - out[f"early_{col}"]
            else:
                out[f"delta_{col}"] = np.nan
            if s.notna().sum() >= 8 and s.std() > 1e-12:
                tt = t[s.notna()]
                ss = s[s.notna()]
                out[f"slope_{col}"] = float(np.polyfit(tt, ss, 1)[0])
        rows.append(out)
    return pd.DataFrame(rows)


def _rank_vs_life(merged: pd.DataFrame, cols: list[str], *, min_cells: int = 5) -> pd.DataFrame:
    windows = ("early", "late", "eol", "delta", "slope")
    rows: list[dict] = []
    y = pd.to_numeric(merged["life_tagged"], errors="coerce")
    for w in windows:
        pref = f"{w}_"
        for col in cols:
            key = pref + col
            if key not in merged.columns:
                continue
            x = pd.to_numeric(merged[key], errors="coerce")
            mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
            n = int(mask.sum())
            if n < min_cells or x[mask].std() < 1e-12:
                continue
            r, p = spearmanr(x[mask], y[mask])
            rows.append(
                {
                    "window": w,
                    "feature": col,
                    "spearman_r": float(r),
                    "abs_r": abs(float(r)),
                    "p_value": float(p),
                    "n_cells": n,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["abs_r", "n_cells"], ascending=[False, False]).reset_index(drop=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixtures",
        type=Path,
        default=Path("example/fixtures/doe"),
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/lges_lifetime_ranking"),
    )
    p.add_argument("--early-n", type=int, default=30)
    p.add_argument("--doe2-only", action="store_true")
    p.add_argument("--cache", type=Path, default=None, help="Parquet cache dir (default: out/cache)")
    args = p.parse_args()

    cells = DEFAULT_CELLS
    if args.doe2_only:
        cells = [c for c in DEFAULT_CELLS if c[1] in DOE2_IDS]

    cache_dir = args.cache if args.cache is not None else args.out / "cache"
    feat, life = _load(args.fixtures, cells, cache_dir=cache_dir)
    if feat.empty:
        raise SystemExit("No features extracted.")
    cols = _feature_cols(feat)
    stats = _cell_stats(feat, cols, early_n=args.early_n)
    merged = stats.merge(life, on=["cell_id", "arm"], how="inner")

    rank_all = _rank_vs_life(merged, cols, min_cells=5)
    args.out.mkdir(parents=True, exist_ok=True)
    life.to_csv(args.out / "cell_lifetime.csv", index=False)
    rank_all.to_csv(args.out / "lges_vs_lifetime_spearman.csv", index=False)

    doe2_ids = DOE2_IDS
    m2 = merged[merged["cell_id"].isin(doe2_ids)]
    rank_doe2 = _rank_vs_life(m2, cols, min_cells=4)
    rank_doe2.to_csv(args.out / "lges_vs_lifetime_spearman_DOE2.csv", index=False)

    print("\n=== Cell lifetimes (tagged routine cycles) ===")
    print(life.sort_values("life_tagged").to_string(index=False))

    print(f"\n=== TOP 30 overall (n={len(merged)} cells) ===")
    for _, r in rank_all.head(30).iterrows():
        print(
            f"{r['abs_r']:.3f}  r={r['spearman_r']:+.3f}  p={r['p_value']:.3g}  "
            f"[{r['window']}]  {r['feature']}"
        )

    print(f"\n=== DOE2 TOP 15 (n={len(m2)} cells) ===")
    print(life[life["cell_id"].isin(doe2_ids)].sort_values("life_tagged").to_string(index=False))
    for _, r in rank_doe2.head(15).iterrows():
        print(
            f"{r['abs_r']:.3f}  r={r['spearman_r']:+.3f}  p={r['p_value']:.3g}  "
            f"[{r['window']}]  {r['feature']}"
        )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
