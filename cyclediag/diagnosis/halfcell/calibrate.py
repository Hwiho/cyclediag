"""Phase 3 half-cell calibration adapter (stub — does not replace full-cell outputs).

BOL OCP fixtures enable library / peak-attribution prototypes only.
Aged half-cell truth is still required before filling ``*_est_hc_calibrated``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from cyclediag.diagnosis.schema import (
    DIAGNOSIS_VERSION_HC_CALIBRATED,
    DiagnosisResult,
)

from .calibration_schema import CalibrationRecord, validate_calibration_record
from .ocp_library import DEFAULT_HALFCELL_DIR, load_ocp_library


class HalfCellCalibrationNotReady(NotImplementedError):
    """Raised until Phase 3 aged half-cell calibration is implemented."""


def bol_ocp_prototype_status(
    halfcell_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Report what BOL OCP enables vs what remains blocked.

    Does **not** claim aged calibration readiness.
    """
    root = Path(halfcell_dir) if halfcell_dir else DEFAULT_HALFCELL_DIR
    lib = load_ocp_library(root)
    has_bol = bool(lib.anode or lib.cathode)
    aged = bool(lib.meta.get("aged_data"))
    return {
        "halfcell_dir": str(root),
        "bol_ocp_available": has_bol,
        "aged_ocp_available": aged,
        "n_anode_curves": int(lib.meta.get("n_anode_curves") or 0),
        "n_cathode_curves": int(lib.meta.get("n_cathode_curves") or 0),
        "calibration_status": (
            "aged_ready" if aged and has_bol
            else ("bol_prototype_only" if has_bol else "no_ocp")
        ),
        "may_fill_est_hc_calibrated": False if not aged else True,
        "allowed_now": [
            "ocp_library",
            "pe_peak_attribution",
            "electrode_side_hypothesis",
            "synthetic_fullcell_ocp_shape",
        ],
        "blocked_until_aged_hc": [
            "LLI_est_hc_calibrated",
            "LAM_PE_est_hc_calibrated",
            "LAM_NE_est_hc_calibrated",
            "stoich_window_absolute",
            "dma_quantify_degradation_modes",
        ],
        "note": (
            "BOL OCP supports hypothesis-level PE/NE attribution only; "
            "do not emit absolute *_est_hc_calibrated without aged half-cell truth."
        ),
    }


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

    Currently raises :class:`HalfCellCalibrationNotReady` until aged HC truth exists.
    Call :func:`bol_ocp_prototype_status` for BOL-only readiness.
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

    aged_ok = bool(halfcell_truth.get("aged_data") or halfcell_truth.get("aged_ocp"))
    status = "pending_aged_hc" if not aged_ok else "pending_fit"
    record = {
        "schema_version": "hc_calibration_v0",
        "cell_id": cell_id or "unknown",
        "chemistry": chemistry,
        "aged_cycle_ref": aged_cycle_ref,
        "fullcell": fc_payload,
        "halfcell": halfcell_truth,
        "calibration": {
            "status": status,
            "bol_prototype": bol_ocp_prototype_status(),
        },
    }
    validate_calibration_record(record)
    _ = CalibrationRecord.from_dict(record)
    _ = DIAGNOSIS_VERSION_HC_CALIBRATED

    raise HalfCellCalibrationNotReady(
        "Aged half-cell calibration (Phase 3) is not implemented yet. "
        f"BOL status={bol_ocp_prototype_status()['calibration_status']}. "
        "Full-cell pattern scores remain valid under diagnosis_version=fullcell_v1. "
        "Use CalibrationRecord schema + bol_ocp_prototype_status() for BOL library work."
    )
