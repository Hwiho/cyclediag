"""Tests for indicator screening."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.analysis.indicator_screen import (
    compare_cells,
    screen_indicators,
    screen_indicators_by_file,
)


def _synthetic_features(n: int = 50, cell: str = "A") -> pd.DataFrame:
    cycles = np.arange(1, n + 1)
    return pd.DataFrame({
        "cell_id": cell,
        "file": f"{cell}.csv",
        "cycle": cycles,
        "dchgCapa": 100 - cycles * 0.5,
        "SoHQ": 100 - cycles * 0.5,
        "EoD_restV_end": 3.0 + cycles * 0.002,
        "CE": np.full(n, 99.5),
    })


def test_screen_finds_health_correlated_feature():
    df = _synthetic_features()
    out = screen_indicators(df)
    assert not out.empty
    assert "dchgCapa" in out["feature"].values or "SoHQ" in out["feature"].values
    top = out.iloc[0]
    assert top["severity"] > 0.3


def test_compare_two_cells():
    a = _synthetic_features(40, "cell_A")
    b = _synthetic_features(40, "cell_B")
    b["EoD_restV_end"] = b["EoD_restV_end"] + 0.15
    both = pd.concat([a, b], ignore_index=True)
    cmp = compare_cells(both)
    assert not cmp.empty
    assert "EoD_restV_end" in cmp["feature"].values


def test_screen_by_file():
    both = pd.concat([
        _synthetic_features(30, "A"),
        _synthetic_features(30, "B"),
    ], ignore_index=True)
    out = screen_indicators_by_file(both)
    assert len(out["cell_id"].unique()) == 2


def test_sohq_correlation_report_png(tmp_path):
    from cyclediag.analysis.indicator_screen_plots import plot_sohq_correlation_report

    df = _synthetic_features(40, "cell_A")
    out = plot_sohq_correlation_report(df, tmp_path / "sohq_corr.png")
    assert out is not None and out.is_file()
    assert out.stat().st_size > 1000
