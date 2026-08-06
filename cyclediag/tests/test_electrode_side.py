"""Tests for electrode-side v1.1 validated methodology."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cyclediag.diagnosis.electrode_side import diagnose_electrode_side, segment_electrode_trajectory
from cyclediag.diagnosis.halfcell.ocp_library import load_ocp_library, fullcell_ocp_peak_voltages
from cyclediag.diagnosis.pattern_scoring import _evidence_for_term, load_mode_weights
from cyclediag.features.enrich_assb import _find_pulse_cycles


HALFCELL = Path("example/fixtures/halfcell")


def test_pulse_thr_does_not_flag_half_c():
    # synthetic: 0.5C ~ 36 A must NOT flag; 1C ~ 70 A must
    df = pd.DataFrame({
        "cycle": [1] * 10 + [2] * 10,
        "current": [36.0] * 10 + [70.0] * 10,
    })
    pulses = _find_pulse_cycles(df, expected_pulse_current=70.0)
    assert 1 not in pulses
    assert 2 in pulses


def test_ce_out_of_range_skipped():
    feat, signed = _evidence_for_term(
        {"CE": 120.0},
        {"feature": "CE", "direction": "decrease_from_100", "weight": 1.0, "scale": 2.0},
        None,
    )
    assert feat == "CE"
    assert signed is None


def test_lam_curve_proxy_nonpositive_skipped():
    feat, signed = _evidence_for_term(
        {"LAM_curve_proxy": -20.0},
        {"feature": "LAM_curve_proxy", "direction": "increase", "weight": 1.0, "scale": 5.0},
        None,
    )
    assert signed is None


def test_r_ohmic_uses_baseline_delta():
    cfg = load_mode_weights()
    term = next(
        t for t in cfg["modes"]["contact_loss"]["evidence"]
        if t["feature"] == "R_ohmic_soc50"
    )
    assert term.get("use_baseline")
    # absolute high R at baseline → low evidence; growth vs baseline → high
    _, s0 = _evidence_for_term(
        {"R_ohmic_soc50": 2.0}, term, {"R_ohmic_soc50": 2.0},
    )
    _, s1 = _evidence_for_term(
        {"R_ohmic_soc50": 3.5}, term, {"R_ohmic_soc50": 2.0},
    )
    assert s0 is not None and abs(s0) < 0.2
    assert s1 is not None and s1 > 0.5
    # missing baseline → skip (no absolute saturation)
    _, s_skip = _evidence_for_term({"R_ohmic_soc50": 5.0}, term, None)
    assert s_skip is None


def test_baseline_required_skip():
    feat, signed = _evidence_for_term(
        {"R_ohmic_soc50": 4.0},
        {"feature": "R_ohmic_soc50", "direction": "increase", "weight": 1.0, "scale": 0.5, "use_baseline": True},
        {"R_ohmic_soc50": None},
    )
    assert signed is None


def test_discharge_residual_argmax_is_soc_not_dod():
    from cyclediag.features.curve_fit import fit_curve_params
    q = np.linspace(0, 100, 200)
    v_ref = 4.2 - 1.5 * (q / 100.0)
    # residual peak near end of discharge (high DOD) → low SOC
    v_n = v_ref.copy()
    v_n[-20:] -= 0.05
    out = fit_curve_params(q, v_ref, q, v_n, i_n=38.0, leg="discharge")
    assert out["fit_residual_argmax_SOC"] is not None
    assert out["fit_residual_argmax_DOD"] is not None
    assert out["fit_residual_argmax_SOC"] < 40.0
    assert abs(out["fit_residual_argmax_SOC"] + out["fit_residual_argmax_DOD"] - 100.0) < 1.0


def test_electrode_contact_stack_without_si_cosign():
    row = {
        "cycle": 300,
        "LAM_PE_pattern_score": 0.25,
        "contact_loss_score": 0.80,
        "LLI_pattern_score": 0.2,
        "eta_argmax_SOC": 0.0,  # must NOT count as low SOC
    }
    res = diagnose_electrode_side(row, baseline_row={})
    assert res.dominant_electrode in ("contact_stack", "mixed", "unknown")
    assert res.dominant_electrode != "NE"


def test_electrode_ne_with_si_cosign():
    row = {
        "cycle": 300,
        "LAM_PE_pattern_score": 0.25,
        "contact_loss_score": 0.80,
        "LLI_pattern_score": 0.2,
        "hyst_area_low": 0.10,
        "mech_vs_chem_ratio": 2.5,
        "Q_relax_pct": 0.5,
    }
    base = {"hyst_area_low": 0.02, "mech_vs_chem_ratio": 1.0, "Q_relax_pct": 0.1}
    res = diagnose_electrode_side(row, baseline_row=base)
    assert res.si_cosign > 0.2
    assert res.dominant_electrode in ("NE", "contact_stack", "mixed")
    assert res.NE_side_score > 0.3


def test_electrode_pe_dominance_lam():
    row = {
        "cycle": 500,
        "LAM_PE_pattern_score": 0.75,
        "contact_loss_score": 0.25,
        "LLI_pattern_score": 0.2,
        "eta_argmax_SOC": 78.0,
        "hyst_area_high": 0.06,
        "LAM_curve_proxy": 8.0,
    }
    base = {"hyst_area_high": 0.02, "LAM_curve_proxy": 1.0}
    res = diagnose_electrode_side(row, baseline_row=base)
    assert res.dominant_electrode == "PE"
    assert res.PE_side_score > res.contact_stack_score


def test_peak_boost_is_delta_vs_baseline():
    row = {"cycle": 100, "LAM_PE_pattern_score": 0.2, "contact_loss_score": 0.2,
           "chg_dQdV_peak1_V": 3.50, "chg_dQdV_peak2_V": 3.55}
    # same hits at baseline → delta 0 → no pe_peak pad beyond modes
    res0 = diagnose_electrode_side(
        row, baseline_row=row, fc_ocp_peaks=[3.50, 3.55], baseline_peak_hits=2,
    )
    assert res0.pe_peak_hits_delta == 0
    res1 = diagnose_electrode_side(
        row, baseline_row=row, fc_ocp_peaks=[3.50, 3.55], baseline_peak_hits=0,
    )
    assert res1.pe_peak_hits_delta >= 1
    assert (res1.PE_side_score or 0) >= (res0.PE_side_score or 0)


@pytest.mark.skipif(not HALFCELL.exists(), reason="halfcell fixtures missing")
def test_fc_ocp_peaks_not_raw_cathode_domain():
    lib = load_ocp_library(HALFCELL)
    if not lib.cathode or not lib.anode:
        pytest.skip("halfcell LFS not smudged")
    fc = fullcell_ocp_peak_voltages(lib)
    pe = lib.cathode_peak_voltages(leg="charge") or lib.cathode_peak_voltages(leg="discharge")
    # Synthetic FC peaks should generally sit below raw cathode-vs-Li peaks
    if fc and pe:
        assert max(fc) < max(pe) + 0.05


def test_segment_hysteresis_min_dwell():
    rows = []
    for cyc, pe, ne, dom in [
        (10, 0.2, 0.5, "NE"), (20, 0.2, 0.5, "NE"), (30, 0.2, 0.5, "NE"),
        (40, 0.55, 0.3, "PE"), (50, 0.55, 0.3, "PE"), (60, 0.55, 0.3, "PE"),
    ]:
        rows.append({
            "cycle": cyc, "SoHQ": 100 - cyc * 0.05,
            "PE_side_score": pe, "NE_side_score": ne * 0.5,
            "contact_stack_score": ne, "contact_loss_score": ne,
            "shared_side_score": 0.1, "dominant_electrode": dom,
            "si_cosign": 0.1, "LAM_PE_pattern_score": pe, "LLI_pattern_score": 0.2,
        })
    segs = segment_electrode_trajectory(pd.DataFrame(rows), min_segment_cycles=3, lean_eps=0.05)
    assert len(segs) >= 2
