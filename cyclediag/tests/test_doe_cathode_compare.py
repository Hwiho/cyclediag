"""Tests for DOE cathode-arm comparison helpers."""

from __future__ import annotations

import pandas as pd

from cyclediag.analysis.doe_cathode_compare import (
    arm_aggregate,
    compare_arms,
    early_window_summary,
    mechanism_delta,
)


def test_early_and_delta_summaries():
    feats = pd.DataFrame({
        "cycle": [7, 10, 20, 100, 200],
        "cycle_role": ["routine_05c"] * 5,
        "SoHQ": [98, 97, 95, 85, 70],
        "LAM_PE_pattern_score": [0.2, 0.22, 0.25, 0.5, 0.7],
        "contact_loss_score": [0.1, 0.12, 0.15, 0.4, 0.55],
        "PE_side_score": [0.3, 0.3, 0.32, 0.5, 0.6],
        "contact_stack_score": [0.1, 0.12, 0.15, 0.4, 0.5],
        "NE_side_score": [0.05] * 5,
        "si_cosign": [0.1] * 5,
        "LLI_pattern_score": [0.1, 0.1, 0.12, 0.3, 0.4],
    })
    early = early_window_summary(feats)
    assert early["n_early_points"] >= 2
    assert "early_SoHQ" in early
    late = {"late_LAM_PE_pattern_score": 0.7, "late_contact_loss_score": 0.55,
            "late_PE_side_score": 0.6, "late_contact_stack_score": 0.5,
            "late_NE_side_score": 0.05, "late_si_cosign": 0.1, "late_LLI_pattern_score": 0.4,
            "late_SoHQ": 70.0}
    # build late via function
    from cyclediag.analysis.doe_cathode_compare import late_window_summary
    late = late_window_summary(feats)
    delta = mechanism_delta(early, late)
    assert delta["delta_LAM_PE_pattern_score"] > 0


def test_compare_arms_effect_size():
    rows_a = [{"early_SoHQ": 97.0, "delta_LAM_PE_pattern_score": 0.2, "cell_id": "a1"},
              {"early_SoHQ": 96.5, "delta_LAM_PE_pattern_score": 0.25, "cell_id": "a2"}]
    rows_b = [{"early_SoHQ": 95.0, "delta_LAM_PE_pattern_score": 0.5, "cell_id": "b1"},
              {"early_SoHQ": 94.5, "delta_LAM_PE_pattern_score": 0.55, "cell_id": "b2"}]
    aa, bb = arm_aggregate(rows_a), arm_aggregate(rows_b)
    cmp = compare_arms(aa, bb, name_a="S83S", name_b="Bimodal")
    assert not cmp.empty
    assert "diff_Bimodal_minus_S83S" in cmp.columns


def test_parse_arm_allows_letter_prefix():
    from cyclediag.tools.compare_doe_cathodes import parse_arm
    name, path = parse_arm("A=S83S:example/fixtures/doe/DOE3/S83S")
    assert name == "S83S"
    assert path.name == "S83S"
    name2, _ = parse_arm("Bimodal:example/fixtures/doe/DOE3/Bimodal")
    assert name2 == "Bimodal"
