"""Tests for 3-parameter discharge curve fit."""

from __future__ import annotations

import numpy as np
import pytest

from cyclediag.features.curve_fit import fit_curve_three_param


def _ref_curve(n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    q = np.linspace(0, 60, n)
    v = 4.1 - 0.4 * (q / 60) - 0.05 * np.sin(q / 5)
    return q, v


def test_three_param_recovers_synthetic():
    q_ref, v_ref = _ref_curve()
    s_true, o_true, dr_true = 0.92, 2.5, 8.0
    i_a = 25.0
    q_n = q_ref.copy()
    v_n = np.interp(s_true * q_n + o_true, q_ref, v_ref) - i_a * (dr_true / 1000.0)
    fit = fit_curve_three_param(q_ref, v_ref, q_n, v_n, I_A=i_a)
    assert not fit["dchg_fit_degenerate_flag"]
    assert fit["dchg_fit_scale"] == pytest.approx(s_true, rel=0.02)
    assert fit["dchg_fit_offset"] == pytest.approx(o_true, rel=0.02)
    assert fit["dchg_fit_dR"] == pytest.approx(dr_true, rel=0.05)


def test_h1_residual_argmax_low_soc():
    """Si tail removal → residual peaks in low-SOC (rear) region."""
    q_ref, v_ref = _ref_curve()
    c_gr, c_si = 40.0, 20.0
    q_full = np.linspace(0, c_gr + c_si, 500)
    v_gr = np.interp(q_full, q_ref, v_ref)
    v_si = 3.5 - 0.3 * ((q_full - c_gr) / c_si)
    v_full = np.where(q_full < c_gr, v_gr, v_si)
    q_h1 = q_full[q_full <= c_gr + 4.0]
    v_h1 = v_full[q_full <= c_gr + 4.0]
    fit = fit_curve_three_param(q_ref, v_ref, q_h1, v_h1, I_A=25.0)
    soc = fit.get("dchg_fit_residual_argmax_SOC")
    assert soc is not None and soc < 40.0
