"""Tests for BOL OCP library and PE/NE electrode-side hypothesis diagnosis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from cyclediag.diagnosis.electrode_side import diagnose_electrode_side
from cyclediag.diagnosis.halfcell.ocp_library import load_ocp_library


HALFCELL = Path("example/fixtures/halfcell")


@pytest.mark.skipif(not HALFCELL.exists(), reason="halfcell fixtures missing")
def test_load_ocp_library_bol():
    lib = load_ocp_library(HALFCELL)
    # may be empty if LFS pointers only — then skip soft
    if lib.meta.get("lfs_pointers") and not lib.cathode and not lib.anode:
        pytest.skip("halfcell LFS not smudged")
    assert lib.meta.get("n_anode_curves", 0) >= 1 or lib.meta.get("n_cathode_curves", 0) >= 1
    if lib.cathode:
        peaks = lib.cathode_peak_voltages(leg="charge") or lib.cathode_peak_voltages(leg="discharge")
        assert peaks
        assert all(3.0 < p < 4.4 for p in peaks)


def test_electrode_side_ne_dominance_contact_loss():
    row = {
        "cycle": 400,
        "LAM_PE_pattern_score": 0.35,
        "contact_loss_score": 0.85,
        "LLI_pattern_score": 0.2,
        "interface_R_score": 0.15,
        "solid_diffusion_score": 0.1,
        "eta_argmax_SOC": 25.0,
        "hyst_area_low": 0.08,
        "mech_vs_chem_ratio": 2.5,
    }
    base = {"hyst_area_low": 0.03, "mech_vs_chem_ratio": 1.2}
    res = diagnose_electrode_side(row, baseline_row=base)
    assert res.dominant_electrode == "NE"
    assert res.NE_side_score > res.PE_side_score
    assert res.electrode_diagnosis_level == "hypothesis_bol_ocp"


def test_electrode_side_pe_dominance_lam():
    row = {
        "cycle": 500,
        "LAM_PE_pattern_score": 0.82,
        "contact_loss_score": 0.30,
        "LLI_pattern_score": 0.25,
        "eta_argmax_SOC": 78.0,
        "hyst_area_high": 0.06,
        "LAM_curve_proxy": 8.0,
        "chg_dQdV_peak1_V": 3.74,
        "chg_dQdV_peak2_V": 4.01,
    }
    base = {"hyst_area_high": 0.02, "LAM_curve_proxy": 1.0}
    # fake OCP library via attributing peaks without library still works via features
    res = diagnose_electrode_side(row, baseline_row=base)
    assert res.dominant_electrode == "PE"
    assert res.PE_side_score > res.NE_side_score
