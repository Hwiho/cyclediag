"""Tests for Si/Gr mechanism classifier."""

from __future__ import annotations

import pandas as pd

from cyclediag.analysis.si_gr_mechanism import classify_mechanism


def test_impedance_only_gate():
    row = {
        "dchg_fit_dR": 10.0,
        "dchgCapa": 70.0,
        "dchgCapa_bol": 70.0,
        "RCF": 0.85,
        "RCF_bol": 1.0,
    }
    res = classify_mechanism(row)
    assert res["mechanism_state"] == "impedance_only"


def test_undetermined_with_few_evidence():
    res = classify_mechanism({"dchgCapa": 60.0})
    assert res["mechanism_state"] == "undetermined"


def test_h1_scores_higher_with_cliff_stable():
    row = {
        "Q_cliff_abs_slope_100": 0.02,
        "Q_cliff_frac_slope_100": 0.1,
        "SOC0_to_mid_ratio_slope_100": 0.15,
        "dchg_fit_residual_argmax_SOC": 15.0,
        "LLI_vs_R_ratio": 0.3,
        "fade_ratio_Si_Gr": 3.0,
        "dchgCapa": 55.0,
        "dchgCapa_bol": 70.0,
    }
    res = classify_mechanism(row)
    assert res["score_H1"] > res["score_H2"]
