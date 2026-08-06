"""Tests for cycle indicator offline export."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from cyclediag.features.cycle_indicators_export import (
    INSPECT_COLS,
    export_cycle_indicators,
    summarize_cycle_indicators,
    write_cycle_indicator_workbook,
)
from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_features_table
from cyclediag.tests.test_lges_extract import _cycle_df


def test_write_cycle_indicator_workbook(tmp_path: Path):
    df = pd.concat([_cycle_df(1), _cycle_df(2, q_scale=0.95)], ignore_index=True)
    feats = extract_lges_features_table(
        df, filepath="cellA.csv", config=LgesExtractConfig(cell_id="cellA"),
    )
    out = write_cycle_indicator_workbook(feats, tmp_path / "ind.xlsx")
    assert out.is_file()
    sheets = pd.read_excel(out, sheet_name=None)
    assert "Inspect" in sheets and "Full" in sheets and "Meta" in sheets
    for col in ("EoC_restV_end", "EoD_restV_end", "EoC_dchgR_10s", "SoHQ"):
        assert col in sheets["Inspect"].columns


def test_export_from_csv_file(tmp_path: Path):
    # Studio-style raw CSV
    n = 95
    raw = pd.DataFrame({
        "TotalCycle": [1] * n + [2] * n,
        "StepType": (
            ["charge"] * 30 + ["rest"] * 15 + ["discharge"] * 30 + ["rest"] * 20
        ) * 2,
        "Voltage": [4.1] * (2 * n),
        "Capacity": [3000.0] * (2 * n),
        "DischargeCapacity": ([0.0] * 45 + [2850.0] * 50) * 2,
        "Current": ([1.0] * 30 + [0.0] * 15 + [-1.0] * 30 + [0.0] * 20) * 2,
        "TotalTime_sec": list(range(2 * n)),
        "StepTime_sec": (list(range(n))) * 2,
    })
    csv_path = tmp_path / "demo_raw.csv"
    raw.to_csv(csv_path, index=False)

    result = export_cycle_indicators(csv_path, tmp_path / "out", tagged_only=False)
    assert result.out_xlsx is not None and result.out_xlsx.is_file()
    assert result.out_csv is not None and result.out_csv.is_file()
    assert result.out_pngs
    assert result.out_pngs[0].is_file()
    assert result.out_pngs[0].suffix == ".png"
    assert len(result.inspect) == 2
    assert "EoC_restV_init" in result.inspect.columns
    text = summarize_cycle_indicators(result.features)
    assert "rows=2" in text


def test_inspect_cols_subset():
    assert "EoC_restV_end" in INSPECT_COLS
    assert "EoD_chgR_10s" in INSPECT_COLS


def test_plot_overview_png(tmp_path: Path):
    from cyclediag.features.cycle_indicators_plots import plot_cycle_indicator_overview

    df = pd.concat([_cycle_df(1), _cycle_df(2, q_scale=0.95)], ignore_index=True)
    feats = extract_lges_features_table(
        df, filepath="cellA.csv", config=LgesExtractConfig(cell_id="cellA"),
    )
    out = plot_cycle_indicator_overview(feats, tmp_path / "ov.png")
    assert out is not None and out.is_file()
    assert out.stat().st_size > 1000


def test_sohq_rest_v_linear_proxy_png(tmp_path: Path):
    from cyclediag.features.cycle_indicators_plots import fit_sohq_from_rest_v_end, plot_sohq_rest_v_linear_proxy

    df = pd.concat(
        [_cycle_df(1), _cycle_df(2, q_scale=0.95), _cycle_df(3, q_scale=0.90)],
        ignore_index=True,
    )
    feats = extract_lges_features_table(
        df, filepath="cellA.csv", config=LgesExtractConfig(cell_id="cellA"),
    )
    fit, scored = fit_sohq_from_rest_v_end(feats)
    assert fit.n_points >= 3
    assert scored["SoHQ_hat"].notna().all()
    out = plot_sohq_rest_v_linear_proxy(feats, tmp_path / "sohq_proxy.png")
    assert out[0].is_file()


def test_tagged_export_with_classification(tmp_path: Path):
    n = 95
    raw = pd.DataFrame({
        "TotalCycle": [1] * n + [2] * n + [3] * n,
        "StepType": (
            ["charge"] * 30 + ["rest"] * 15 + ["discharge"] * 30 + ["rest"] * 20
        ) * 3,
        "Voltage": [4.1] * (3 * n),
        "Capacity": [3000.0] * (3 * n),
        "DischargeCapacity": ([0.0] * 45 + [2850.0] * 50) * 3,
        "Current": ([1.0] * 30 + [0.0] * 15 + [-1.0] * 30 + [0.0] * 20) * 3,
        "TotalTime_sec": list(range(3 * n)),
        "StepTime_sec": (list(range(n))) * 3,
    })
    csv_path = tmp_path / "demo_raw.csv"
    raw.to_csv(csv_path, index=False)
    pd.DataFrame({
        "TotalCycle": [1, 3],
        "PairLabel": ["Cycle-1", "Cycle-2"],
    }).to_csv(tmp_path / "demo_classification.csv", index=False)

    result = export_cycle_indicators(csv_path, tmp_path / "out", tagged_only=True, write_png=True)
    assert len(result.features) == 2
    assert list(result.features["tagged_cycle"]) == [1, 2]
    assert result.out_pngs