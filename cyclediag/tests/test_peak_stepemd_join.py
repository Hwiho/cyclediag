"""Tests for StepEnd + peak merge."""

from __future__ import annotations

import pandas as pd

from cyclediag.features.peak_stepemd_join import (
    correlate_peaks_with_fade,
    merge_stepemd_into_wide,
)


def test_merge_stepemd_and_correlate():
    wide = pd.DataFrame({
        "cycle": list(range(1, 11)),
        "usable": [True] * 10,
        "cha_P3_main_V": [3.80 + i * 0.01 for i in range(10)],
        "cha_P3_main_H": [80 - i for i in range(10)],
    })
    stepemd = pd.DataFrame({
        "cycle": list(range(1, 11)),
        "SoHQ": [100.0 - i * 2 for i in range(10)],
        "dchgCapa": [70.0 - i * 0.7 for i in range(10)],
    })
    merged = merge_stepemd_into_wide(wide, stepemd)
    assert "SoHQ" in merged.columns
    corr = correlate_peaks_with_fade(merged)
    assert not corr.empty
    row = corr[(corr["peak_feature"] == "cha_P3_main_V") & (corr["target"] == "SoHQ")]
    assert not row.empty
    assert row["pearson_r"].iloc[0] < 0
