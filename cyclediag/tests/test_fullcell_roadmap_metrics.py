"""Tests for roadmap §5.6 / §5.7 / §5.9 full-cell modules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cyclediag.features.curve_fit import fit_curve_params
from cyclediag.features.dqv_stats import dqv_stats, q_on_v_grid
from cyclediag.features.overpotential import eta_curve, reff_shape_fit
from cyclediag.diagnosis.engine import diagnose_feature_table


def test_eta_curve_positive_on_slower_rate():
    q = np.linspace(0, 70, 200)
    v_c3 = 4.1 - 1.5 * (q / 70.0)
    v_05 = v_c3 - 0.05  # more polarized
    out = eta_curve(q, v_c3, q, v_05)
    assert out["eta_valid"]
    assert out["eta_SOC50"] == pytest.approx(0.05, abs=0.01)
    assert out["eta_mean"] == pytest.approx(0.05, abs=0.01)


def test_reff_shape_fit():
    eta = {20.0: 0.06, 50.0: 0.05, 80.0: 0.04}
    r = {20.0: 1.8, 50.0: 1.5, 80.0: 1.2}
    out = reff_shape_fit(eta, r)
    assert out["Reff_scale"] is not None
    assert out["Reff_shape_fit_r2"] is not None and out["Reff_shape_fit_r2"] > 0.95


def test_dqv_stats_detects_capacity_loss():
    v = np.linspace(4.2, 2.5, 300)
    q_ref = 70 * (4.2 - v) / (4.2 - 2.5)
    q_n = 0.9 * q_ref
    v_grid = np.linspace(2.6, 4.1, 200)
    qr = q_on_v_grid(v, q_ref, v_grid)
    qn = q_on_v_grid(v, q_n, v_grid)
    st = dqv_stats(qn, qr, v_grid, ref_cycle=3)
    assert st["dQV_min"] < 0
    assert st["dQV_log_var"] is not None
    assert st["dQV_var"] > 0


def test_curve_fit_recovers_lam_scale():
    q = np.linspace(0, 70, 250)
    v_ref = 4.15 - 1.4 * (q / 70.0) - 0.1 * np.sin(2 * np.pi * q / 70.0)
    s_true, o_true, dr_mohm = 0.92, 1.5, 8.0
    i = 38.0
    q_n = q.copy()
    v_n = np.interp(s_true * q_n + o_true, q, v_ref) - i * (dr_mohm / 1000.0)
    fit = fit_curve_params(q, v_ref, q_n, v_n, i_n=i)
    assert fit["fit_scale"] == pytest.approx(s_true, rel=0.05)
    assert fit["LAM_curve_proxy"] == pytest.approx((1 - s_true) * 100, rel=0.15)
    assert fit["R_curve_proxy"] == pytest.approx(dr_mohm, rel=0.35)


def test_diagnosis_blends_quality_and_keeps_est_null():
    df = pd.DataFrame({
        "cell_id": ["A"] * 3,
        "cycle": [1, 50, 100],
        "SoHQ": [100.0, 90.0, 80.0],
        "CE": [99.5, 99.0, 98.0],
        "CI": [0.5, 1.0, 2.0],
        "quality_score": [0.9, 0.8, 0.1],
        "LAM_curve_proxy": [0.0, 3.0, 8.0],
        "mech_vs_chem_ratio": [1.0, 1.2, 1.5],
        "R_ohmic_soc50": [1.0, 1.3, 1.8],
        "R_ohmic_frac_soc50": [0.4, 0.45, 0.55],
    })
    out = diagnose_feature_table(df, baseline_cycle=1)
    assert "diagnosis_state" in out.columns
    assert out["LLI_est"].isna().all() or out["LLI_est"].isnull().all()
    assert out.loc[out["cycle"] == 100, "diagnosis_state"].iloc[0] == "insufficient_data"
    assert float(out.loc[out["cycle"] == 50, "diagnosis_quality_score"].iloc[0]) > 0
