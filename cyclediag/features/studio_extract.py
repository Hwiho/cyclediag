"""Shared LGES feature extraction for Studio GUI and offline tools."""

from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd

from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_features_table


def extract_lges_for_file(
    df: pd.DataFrame,
    filepath: str,
    cycles: Iterable[int],
    config: LgesExtractConfig,
) -> pd.DataFrame:
    """Extract LGES indicators for one loaded dataframe + cycle list."""
    cycle_list = sorted({int(c) for c in cycles})
    if not cycle_list or df is None or df.empty:
        return pd.DataFrame()
    return extract_lges_features_table(
        df,
        cycles=cycle_list,
        filepath=filepath,
        config=config,
        raw_df=df,
    )


def collect_lges_features(
    items: Sequence[tuple[pd.DataFrame, str, list[int], LgesExtractConfig]],
) -> pd.DataFrame:
    """Concatenate LGES tables from multiple (df, path, cycles, config) tuples."""
    frames: list[pd.DataFrame] = []
    for df, path, cycles, cfg in items:
        table = extract_lges_for_file(df, path, cycles, cfg)
        if not table.empty:
            frames.append(table)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
