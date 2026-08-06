"""Phase 3 half-cell calibration adapter (stub — does not replace full-cell outputs)."""

from __future__ import annotations

from typing import Any, Sequence

from cyclediag.diagnosis.schema import (
    DIAGNOSIS_VERSION_HC_CALIBRATED,
    DiagnosisResult,
)

from .calibration_schema import CalibrationRecord, validate_calibration_record


class HalfCellCalibrationNotReady(NotImplementedError):
    """Raised until Phase 3 half-cell calibration is implemented."""


def calibrate(
    fullcell_results: Sequence[DiagnosisResult] | dict[str, DiagnosisResult],
    halfcell_truth: dict[str, Any],
    *,
    chemistry: str | None = None,
    cell_id: str = "",
    aged_cycle_ref: int | float | None = None,
) -> list[DiagnosisResult]:
    """Map full-cell diagnosis → hc_calibrated DiagnosisResult list.

    Contract (Phase 3):
    - ``diagnosis_version`` becomes ``hc_calibrated_v1``
    - original full-cell fields are preserved by the caller (parallel columns)
    - this function must **never** mutate full-cell Level-1/2 columns in place

    Currently raises :class:`HalfCellCalibrationNotReady`.
    """
    # Validate inputs early so callers can exercise schema without half-cell data files
    if isinstance(fullcell_results, dict):
        results = list(fullcell_results.values())
    else:
        results = list(fullcell_results)

    fc_payload: dict[str, Any] = {"diagnosis_version": "fullcell_v1"}
    for r in results:
        if r.degradation_mode == "LLI":
            fc_payload["LLI_pattern_score"] = r.estimate
            fc_payload["LLI_est"] = None
        elif r.degradation_mode == "LAM_PE":
            fc_payload["LAM_PE_pattern_score"] = r.estimate
        elif r.degradation_mode == "LAM_NE":
            fc_payload["LAM_NE_pattern_score"] = r.estimate

    record = {
        "schema_version": "hc_calibration_v0",
        "cell_id": cell_id or "unknown",
        "chemistry": chemistry,
        "aged_cycle_ref": aged_cycle_ref,
        "fullcell": fc_payload,
        "halfcell": halfcell_truth,
        "calibration": {"status": "pending"},
    }
    validate_calibration_record(record)
    _ = CalibrationRecord.from_dict(record)
    _ = DIAGNOSIS_VERSION_HC_CALIBRATED

    raise HalfCellCalibrationNotReady(
        "Half-cell calibration (Phase 3) is not implemented yet. "
        "Full-cell pattern scores remain valid under diagnosis_version=fullcell_v1. "
        "Use CalibrationRecord schema to store paired fullcell/halfcell truth for later."
    )
