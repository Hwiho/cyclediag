"""Tests for Phase 4 peak tracking."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.peak_tracking import (
    add_cycle_derivatives,
    build_peak_tracking_tables,
    enrich_tracking_long,
    golden_reference_table,
)


def _sample_long() -> pd.DataFrame:
    rows = []
    for tc in (10, 20, 30):
        for leg, band, v0 in (
            ("charge", "P3_main", 3.80),
            ("discharge", "P3_high", 3.90),
        ):
            rows.append({
                "cell_id": "T",
                "cycle": tc,
                "leg": leg,
                "band": band,
                "peak_id": band,
                "V": v0 + tc * 0.0001,
                "H": 80.0 - tc * 0.1 if leg == "charge" else -80.0 + tc * 0.05,
                "assign_confidence": 0.9,
                "band_height_frac": 0.5,
                "usable": True,
                "usable_leg": True,
            })
    out = pd.DataFrame(rows)
    out["H_abs"] = out["H"].abs()
    return out


def _sample_wide() -> pd.DataFrame:
    return pd.DataFrame({
        "cycle": [10, 20, 30],
        "usable": [True, True, True],
        "usable_charge": [True, True, True],
        "usable_discharge": [True, True, True],
    })


def test_golden_reference_median():
    long_df = _sample_long()
    golden = golden_reference_table(long_df, good_cycles=[10])
    assert not golden.empty
    row = golden[(golden["leg"] == "charge") & (golden["peak_id"] == "P3_main")].iloc[0]
    assert abs(row["V_golden"] - 3.801) < 0.01


def test_enrich_tracking_has_phase4_columns():
    long_df = _sample_long()
    wide_df = _sample_wide()
    out = enrich_tracking_long(long_df, wide_df, good_cycles=[10])
    for col in (
        "H_norm", "dV_vs_golden", "dH_vs_golden", "dV_dcycle", "dH_dcycle", "V_golden",
    ):
        assert col in out.columns
    assert out["H_norm"].notna().any()


def test_cycle_derivatives():
    df = _sample_long()
    out = add_cycle_derivatives(df)
    ch = out[(out["leg"] == "charge") & (out["peak_id"] == "P3_main")].sort_values("cycle")
    assert ch["dV_dcycle"].iloc[1:].notna().all()


def test_build_peak_tracking_tables():
    long_df = _sample_long()
    wide_df = _sample_wide()
    tracking, golden, summary = build_peak_tracking_tables(long_df, wide_df, [10])
    assert len(tracking) == len(long_df)
    assert not golden.empty
    assert not summary.empty
    assert "dV_dcycle_mean" in summary.columns
