"""Join peak tracking tables with StepEnd cycle features (SoHQ, capacity)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.features.stepemd_extract import extract_stepemd_features_table

STEPEND_CYCLE_COLS = (
    "SoHQ",
    "chgCapa",
    "dchgCapa",
    "CE",
    "CE_rev",
    "delta_chgCapa",
    "delta_dchgCapa",
    "EoC_restV_end",
    "EoD_restV_end",
    "delta_EoC_restV_end",
    "delta_EoD_restV_end",
)


def discover_stepend_for_raw(raw_path: str | Path) -> Path | None:
    """Guess StepEnd CSV next to raw export (*_raw.csv → *_stepend.csv)."""
    raw_path = Path(raw_path)
    stem = raw_path.stem
    if stem.endswith("_raw"):
        stem = stem[: -len("_raw")]
    for suffix in ("_stepend.csv", "_StepEnd.csv", "StepEnd.csv"):
        cand = raw_path.with_name(stem + suffix)
        if cand.exists():
            return cand
    alt = raw_path.parent / f"{stem}_stepend.csv"
    return alt if alt.exists() else None


def load_stepemd_cycle_table(
    stepemd_path: str | Path | None = None,
    *,
    step_df: pd.DataFrame | None = None,
    encoding: str = "cp949",
) -> pd.DataFrame:
    """Per-cycle StepEnd features including SoHQ."""
    table = extract_stepemd_features_table(
        stepemd_path, step_df=step_df, encoding=encoding,
    )
    if table.empty:
        return table
    keep = ["cell_id", "cycle", *[c for c in STEPEND_CYCLE_COLS if c in table.columns]]
    return table[keep].copy()


def merge_stepemd_into_wide(wide_df: pd.DataFrame, stepemd_df: pd.DataFrame) -> pd.DataFrame:
    """Attach SoHQ/capacity columns to per-cycle wide peak table."""
    if wide_df.empty or stepemd_df.empty:
        return wide_df.copy()
    cols = [c for c in stepemd_df.columns if c not in ("cell_id", "cycle")]
    out = wide_df.merge(stepemd_df[["cycle", *cols]], on="cycle", how="left")
    return out


def merge_stepemd_into_tracking(tracking_df: pd.DataFrame, stepemd_df: pd.DataFrame) -> pd.DataFrame:
    """Attach SoHQ/capacity to long peak tracking rows."""
    if tracking_df.empty or stepemd_df.empty:
        return tracking_df.copy()
    cols = [c for c in stepemd_df.columns if c not in ("cell_id", "cycle")]
    return tracking_df.merge(stepemd_df[["cycle", *cols]], on="cycle", how="left")


def correlate_peaks_with_fade(
    merged_wide: pd.DataFrame,
    *,
    usable_only: bool = True,
    target_cols: tuple[str, ...] = ("SoHQ", "dchgCapa", "chgCapa"),
) -> pd.DataFrame:
    """Pearson correlation: peak V/H/delta cols vs fade indicators."""
    work = merged_wide.copy()
    if usable_only and "usable" in work.columns:
        work = work[work["usable"]]

    peak_cols = [
        c for c in work.columns
        if c.endswith("_V") or c.endswith("_H") or c.startswith("d_cha_") or c.startswith("d_dis_")
    ]
    rows: list[dict] = []
    for pcol in peak_cols:
        x = pd.to_numeric(work[pcol], errors="coerce")
        if x.notna().sum() < 8:
            continue
        for tcol in target_cols:
            if tcol not in work.columns:
                continue
            y = pd.to_numeric(work[tcol], errors="coerce")
            mask = x.notna() & y.notna()
            if mask.sum() < 8:
                continue
            corr = float(x[mask].corr(y[mask]))
            if not np.isfinite(corr):
                continue
            rows.append({
                "peak_feature": pcol,
                "target": tcol,
                "pearson_r": corr,
                "n": int(mask.sum()),
            })
    if not rows:
        return pd.DataFrame(columns=["peak_feature", "target", "pearson_r", "n"])
    out = pd.DataFrame(rows)
    return out.sort_values("pearson_r", key=abs, ascending=False)
