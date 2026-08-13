"""Coverage for the P0–P3 two-track follow-ups (roadmap §4.6)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cyclediag.analysis.indicator_layers import (
    LAYER_ANCHOR,
    LAYER_HEALTH,
    LAYER_MECHANISM,
    report_layer,
    split_by_layer,
)
from cyclediag.analysis.lli_kinetic_split import classify_ocv_parallel_shift
from cyclediag.analysis.resistance_anchors import landmark_resistance_trend, resistance_anchor_table
from cyclediag.analysis.sohq_interval_compare import interval_feature_deltas, knee_split_summary
from cyclediag.diagnosis.constraints import confidence_multiplier, constraint_flags
from cyclediag.diagnosis.engine import diagnose_feature_table
from cyclediag.diagnosis.pattern_scoring import load_mode_weights
from cyclediag.features.enrich_assb import attach_q_relax_from_dcir_blocks
from cyclediag.features.indicator_registry import ROLE_META, ROLE_QC, family_of, role_of

_CONFIG_DIR = Path(__file__).resolve().parents[1] / "diagnosis" / "config"


def test_report_layers_split_capacity_mechanism_anchor():
    assert report_layer("SoHQ") == LAYER_HEALTH
    assert report_layer("dchgCapa") == LAYER_HEALTH
    assert report_layer("hyst_frac_low") == LAYER_MECHANISM
    assert report_layer("Q_relax_pct") == LAYER_ANCHOR
    assert report_layer("R_ohmic_soc50") == LAYER_ANCHOR
    summary = pd.DataFrame({
        "feature": ["SoHQ", "hyst_frac_low", "Q_relax_pct"],
        "indicator_score": [0.9, 0.5, 0.3],
    })
    layers = split_by_layer(summary)
    assert list(layers[LAYER_HEALTH]["feature"]) == ["SoHQ"]
    assert list(layers[LAYER_MECHANISM]["feature"]) == ["hyst_frac_low"]
    assert list(layers[LAYER_ANCHOR]["feature"]) == ["Q_relax_pct"]


def test_q_relax_dual_aliases_and_primary_prefers_rpt():
    feats = pd.DataFrame({
        "cycle": [10, 11, 12, 13, 14],
        "dchgCapa": [70.0, 69.5, 20.0, 19.5, 19.0],
    })
    # DCIR block at 12..; RPT pair as 10,11; also synthetic RPT block [10,11]
    out = attach_q_relax_from_dcir_blocks(
        feats, dcir_blocks=[[12, 13, 14]], rpt_blocks=[[10, 11]],
    )
    assert out.loc[out["cycle"] == 10, "Q_relax_rpt"].notna().all()
    assert out.loc[out["cycle"] == 10, "Q_relax_source"].iloc[0] == "rpt_block"
    assert out.loc[out["cycle"] == 10, "Q_relax"].iloc[0] == pytest.approx(
        float(out.loc[out["cycle"] == 10, "Q_relax_rpt"].iloc[0])
    )
    # Pre-DCIR pair (10,11) also fills dcir alias on those rows
    assert out.loc[out["cycle"] == 10, "Q_relax_dcir"].notna().all()
    assert family_of("Q_relax_rpt_pct") == "q_relax"
    assert family_of("Q_relax_dcir") == "q_relax"
    assert role_of("Q_relax_source") == ROLE_META
    assert role_of("Q_relax_rpt_significant") == ROLE_QC


def test_q_relax_falls_back_to_dcir_when_no_rpt():
    feats = pd.DataFrame({
        "cycle": [8, 9, 10, 11, 12],
        "dchgCapa": [70.0, 69.8, 20.0, 19.5, 19.0],
    })
    out = attach_q_relax_from_dcir_blocks(feats, dcir_blocks=[[10, 11, 12]], rpt_blocks=[])
    row = out.loc[out["cycle"] == 8].iloc[0]
    assert row["Q_relax_source"] == "dcir_pre"
    assert pd.notna(row["Q_relax_dcir"])
    assert row["Q_relax"] == pytest.approx(float(row["Q_relax_dcir"]))


def test_constraints_cap_contact_and_skip_protocol():
    cfg = {"constraints": {"stack_pressure_MPa": None, "halfcell_calibrated": False}}
    flags = constraint_flags({"temperature_available": False}, cfg)
    assert "no_temperature_log" in flags
    assert "stack_pressure_unknown" in flags
    assert "halfcell_uncalibrated" in flags
    assert confidence_multiplier("contact_loss", flags) < 0.7
    assert confidence_multiplier("LLI", flags) == pytest.approx(0.95)
    assert confidence_multiplier("LLI", ["protocol_excluded"]) == 0.0


def test_diagnosis_skips_protocol_excluded_rows():
    df = pd.DataFrame({
        "cell_id": ["A"] * 6,
        "file": ["a.csv"] * 6,
        "cycle": list(range(1, 7)),
        "protocol_kind": ["routine", "routine", "rpt", "routine", "dcir", "routine"],
        "protocol_excluded": [False, False, True, False, True, False],
        "SoHQ": [100, 99, 98, 97, 96, 95],
        "CE": [99.5, 99.4, 101.0, 99.2, 99.0, 99.1],
        "delta_dchg_V_cutoff_margin": [0.0, -0.01, -0.5, -0.03, -0.4, -0.05],
        "delta_EoD_restV_end": [0.0, 0.01, 0.2, 0.02, 0.3, 0.04],
        "VE": [0.95, 0.94, 0.5, 0.93, 0.4, 0.92],
    })
    out = diagnose_feature_table(
        df, config_path=_CONFIG_DIR / "mode_weights_fullcell_v1.json", routine_only=True,
    )
    scored = out["diagnosis_scored_row"].astype(bool)
    assert scored.sum() == 4
    assert not bool(out.loc[out["cycle"] == 3, "diagnosis_scored_row"].iloc[0])
    assert "protocol_excluded" in str(out.loc[out["cycle"] == 3, "diagnosis_constraints"].iloc[0])


def test_mode_weights_use_cliff_abs_and_hyst_bands():
    full = load_mode_weights(_CONFIG_DIR / "mode_weights_fullcell_v1.json")
    assb = load_mode_weights(_CONFIG_DIR / "mode_weights_assb_si_v1.json")
    lam = [t["feature"] for t in full["modes"]["LAM_NE"]["evidence"]]
    assert "dchg_dVdQ_SOC0_cliff_width_abs" in lam
    assert "dchg_Q_cliff_abs" in lam
    assert "dchg_dVdQ_post_cliff" in lam
    contact = [t["feature"] for t in full["modes"]["contact"]["evidence"]]
    assert "hyst_frac_low" in contact
    assert "hyst_area_low" not in contact  # same hysteresis_low family
    assert "delta_hyst_area" not in contact
    impedance = [t["feature"] for t in full["modes"]["impedance"]["evidence"]]
    assert "delta_hyst_area" not in impedance
    cl = [t["feature"] for t in assb["modes"]["contact_loss"]["evidence"]]
    assert "hyst_frac_low" in cl
    assert "dchg_dVdQ_SOC0_cliff_width_abs" in cl
    # CE demoted on both configs for LLI
    for cfg in (full, assb):
        ce_w = next(t["weight"] for t in cfg["modes"]["LLI"]["evidence"] if t["feature"] == "CE")
        assert ce_w < 0.5


def test_lli_kinetic_split_labels():
    n = 20
    rng = np.random.default_rng(0)
    shift = np.linspace(0, 0.1, n)
    # R30 tracks shift → kinetic
    kin = pd.DataFrame({
        "ocv_parallel_shift": shift,
        "R_30s_total_soc50": shift * 10 + rng.normal(0, 0.001, n),
        "delta_EoD_restV_end": rng.normal(0, 0.01, n),
    })
    assert classify_ocv_parallel_shift(kin)["label"] == "kinetic_termination_dominant"
    # EoD tracks shift, R does not → LLI
    lli = pd.DataFrame({
        "ocv_parallel_shift": shift,
        "R_30s_total_soc50": rng.normal(1.0, 0.01, n),
        "delta_EoD_restV_end": shift + rng.normal(0, 0.001, n),
    })
    assert classify_ocv_parallel_shift(lli)["label"] == "lli_dominant"


def test_sohq_interval_and_knee():
    rows = []
    for i in range(40):
        sohq = 100.0 - i * 1.0
        rows.append({
            "cell_id": "C",
            "cycle": i + 1,
            "SoHQ": sohq,
            "hyst_frac_low": 0.1 + 0.01 * i,
        })
    df = pd.DataFrame(rows)
    deltas = interval_feature_deltas(df, columns=["hyst_frac_low"])
    assert not deltas.empty
    assert set(deltas["band"]) & {"95-90", "90-80", "80-70", "70-60"}
    knee = knee_split_summary(df, knee_sohq=80.0)
    assert knee["knee_sohq"] == pytest.approx(80.0)
    assert knee["knee_cycle"] is not None


def test_resistance_anchor_helpers():
    df = pd.DataFrame({
        "cycle": [1, 2, 10, 11, 50, 51],
        "cell_id": ["A"] * 6,
        "protocol_kind": ["routine"] * 6,
        "protocol_excluded": [False] * 6,
        "R_ohmic_soc50": [np.nan, np.nan, 0.5, np.nan, np.nan, 0.8],
        "EoC_dchgR_10s": [10.0, 11.0, 12.0, 13.0, 20.0, 22.0],
    })
    anchors = resistance_anchor_table(df)
    assert len(anchors) == 2
    trend = landmark_resistance_trend(df, routine_only=True)
    assert not trend.empty
    row = trend[trend["feature"] == "EoC_dchgR_10s"].iloc[0]
    assert row["late_median"] > row["early_median"]
