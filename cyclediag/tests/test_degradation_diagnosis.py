"""Tests for full-cell LLI/LAM pattern diagnosis (no half-cell required)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from cyclediag.diagnosis import diagnose_feature_table
from cyclediag.diagnosis.halfcell import (
    CalibrationRecord,
    HalfCellCalibrationNotReady,
    calibrate,
    validate_calibration_record,
)
from cyclediag.diagnosis.pattern_scoring import load_mode_weights, score_all_modes_for_row
from cyclediag.diagnosis.schema import DIAGNOSIS_VERSION_FULLCELL

_FULLCELL_CFG = Path(__file__).resolve().parents[1] / "diagnosis" / "config" / "mode_weights_fullcell_v1.json"


def _synthetic_feature_table(n: int = 30) -> pd.DataFrame:
    rows = []
    for i in range(n):
        frac = i / max(1, n - 1)
        rows.append({
            "cell_id": "SYN",
            "file": "syn.csv",
            "cycle": i + 1,
            "SoHQ": 100.0 - 15.0 * frac,
            "CE": 99.5 - 1.5 * frac,
            "delta_dchg_V_cutoff_margin": -0.08 * frac,
            "delta_EoD_restV_end": 0.12 * frac,
            "delta_EoC_restV_end": -0.04 * frac,
            "delta_dchg_dVdQ_SOC0": 8.0 * frac,
            "dchg_dVdQ_SOC0_to_mid_ratio": 2.0 + 3.0 * frac,
            "dchg_dVdQ_SOC0_cliff_width": 4.0,
            "EoD_chgR_10s_inc": 40.0 * frac,
            "EoC_dchgR_10s_inc": 35.0 * frac,
            "EoC_dchgR_60s_inc": 50.0 * frac,
            "EoD_chgR_60s_inc": 45.0 * frac,
            "chgCVtime": 50.0 + 200.0 * frac,
            "chgCapa_CCratio": 95.0 - 10.0 * frac,
            "dchg_shape_DTW": 0.02 * frac,
            "delta_hyst_area": 0.2 * frac,
            "delta_hyst_max_dV": 0.1 * frac,
            "EoC_restV_tau": 300.0 + 200.0 * frac,
            "diagnosis_should_not_block": True,
        })
    return pd.DataFrame(rows)


def test_load_default_weights():
    cfg = load_mode_weights(_FULLCELL_CFG)
    assert "LLI" in cfg["modes"]
    assert "LAM_NE" in cfg["modes"]
    assert cfg["diagnosis_version"] == DIAGNOSIS_VERSION_FULLCELL


def test_pattern_scores_without_halfcell():
    df = _synthetic_feature_table()
    out = diagnose_feature_table(df, config_path=_FULLCELL_CFG)
    assert "LLI_pattern_score" in out.columns
    assert "LAM_PE_pattern_score" in out.columns
    assert "LAM_NE_pattern_score" in out.columns
    assert "impedance_pattern_score" in out.columns
    assert out["diagnosis_version"].iloc[-1] == DIAGNOSIS_VERSION_FULLCELL
    # late life should show elevated LLI / LAM_NE / impedance vs early
    early = float(out["LLI_pattern_score"].iloc[2])
    late = float(out["LLI_pattern_score"].iloc[-1])
    assert late > early
    assert out["LLI_confidence"].iloc[-1] > 0
    assert isinstance(out["LLI_supporting_features"].iloc[-1], str)
    assert out["LLI_supporting_features"].iloc[-1]
    # Level 2/3 left null
    assert pd.isna(out["LLI_est"].iloc[-1]) or out["LLI_est"].iloc[-1] is None
    assert pd.isna(out["LLI_est_hc_calibrated"].iloc[-1]) or out["LLI_est_hc_calibrated"].iloc[-1] is None


def test_halfcell_absence_does_not_disable():
    """Acceptance: no half-cell files → diagnosis still runs."""
    row = _synthetic_feature_table(n=5).iloc[-1].to_dict()
    results = score_all_modes_for_row(row, load_mode_weights(_FULLCELL_CFG))
    assert "LLI" in results
    assert results["LLI"].estimate is not None


def test_calibration_schema_validates():
    rec = {
        "schema_version": "hc_calibration_v0",
        "cell_id": "M01Ch022",
        "chemistry": "SJ900",
        "aged_cycle_ref": 502,
        "fullcell": {
            "diagnosis_version": "fullcell_v1",
            "LLI_pattern_score": 0.81,
            "supporting_features": ["delta_dchg_V_cutoff_margin"],
        },
        "halfcell": {
            "source": "harvested",
            "PE_reversible_capacity_frac": 0.94,
            "NE_reversible_capacity_frac": 0.90,
            "LLI_proxy": 0.11,
        },
        "calibration": {"status": "pending"},
    }
    validate_calibration_record(rec)
    obj = CalibrationRecord.from_dict(rec)
    assert obj.cell_id == "M01Ch022"
    assert obj.fullcell["LLI_pattern_score"] == 0.81


def test_calibrate_stub_raises_not_ready():
    df = _synthetic_feature_table(n=3)
    out = diagnose_feature_table(df, config_path=_FULLCELL_CFG)
    row = out.iloc[-1]
    from cyclediag.diagnosis.schema import DiagnosisResult

    results = {
        "LLI": DiagnosisResult(
            degradation_mode="LLI",
            estimate=float(row["LLI_pattern_score"]),
            confidence=float(row["LLI_confidence"]),
            supporting_features=str(row["LLI_supporting_features"]).split(","),
            diagnosis_valid=True,
        ),
        "LAM_PE": DiagnosisResult(
            degradation_mode="LAM_PE",
            estimate=float(row["LAM_PE_pattern_score"]),
            diagnosis_valid=True,
        ),
        "LAM_NE": DiagnosisResult(
            degradation_mode="LAM_NE",
            estimate=float(row["LAM_NE_pattern_score"]),
            diagnosis_valid=True,
        ),
    }
    with pytest.raises(HalfCellCalibrationNotReady):
        calibrate(
            results,
            {"PE_reversible_capacity_frac": 0.9, "NE_reversible_capacity_frac": 0.88},
            chemistry="SJ900",
            cell_id="SYN",
        )


def test_json_sidecar(tmp_path: Path):
    df = _synthetic_feature_table(n=5)
    side = tmp_path / "diag.json"
    diagnose_feature_table(df, config_path=_FULLCELL_CFG, write_json_sidecar=side)
    payload = json.loads(side.read_text(encoding="utf-8"))
    assert isinstance(payload, list) and len(payload) >= 5
    assert payload[0]["diagnosis_version"] == DIAGNOSIS_VERSION_FULLCELL
    assert "degradation_mode" in payload[0]
