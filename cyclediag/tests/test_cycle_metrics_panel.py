"""Tests for cycle metric catalog + trend analysis."""

from __future__ import annotations

import pandas as pd

from cyclediag.analysis.cycle_trend import (
    analyze_all_metrics,
    analyze_series,
    extract_cycle_metric_table,
    narrative_from_trends,
)
from cyclediag.analysis.metric_catalog import available_metrics, get_metric


def _fake_traj() -> pd.DataFrame:
    n = 20
    return pd.DataFrame({
        "cycle": list(range(10, 10 + n)),
        "cycle_role": ["routine_05c"] * n,
        "SoHQ": [98 - 0.4 * i for i in range(n)],
        "R_ohmic_soc50": [1.0 + 0.02 * i for i in range(n)],
        "R_ct_soc50": [0.8 + 0.005 * i for i in range(n)],
        "mech_vs_chem_ratio": [1.2 + 0.03 * i for i in range(n)],
        "LAM_PE_pattern_score": [0.2 + 0.02 * i for i in range(n)],
        "contact_loss_score": [0.1 + 0.015 * i for i in range(n)],
        "VE": [0.90 - 0.001 * i for i in range(n)],
    })


def test_catalog_has_core_metrics():
    assert get_metric("SoHQ") is not None
    assert get_metric("mech_vs_chem_ratio").aging_hint == "increase"
    assert get_metric("R_ohmic_soc50").unit == "mΩ"


def test_analyze_sohq_decreasing():
    tr = analyze_series(_fake_traj(), "SoHQ")
    assert tr["n"] >= 10
    assert tr["trend_label"] == "decreasing"
    assert tr["vs_expectation"] == "matches_aging"
    assert tr["delta_late_early"] < 0


def test_extract_and_narrative():
    df = _fake_traj()
    avail = available_metrics(df.columns)
    assert len(avail) >= 5
    table = extract_cycle_metric_table(df)
    assert "cycle" in table.columns and "SoHQ" in table.columns
    trends = analyze_all_metrics(df)
    assert not trends.empty
    text = narrative_from_trends(trends, cell_id="TEST")
    assert "트렌드 요약" in text
    assert "SoHQ" in text or "용량" in text
