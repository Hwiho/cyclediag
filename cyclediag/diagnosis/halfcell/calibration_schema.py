"""Half-cell ↔ full-cell calibration record schema (define now, use in Phase 3)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CALIBRATION_SCHEMA_VERSION = "hc_calibration_v0"


@dataclass
class CalibrationRecord:
    """Compare full-cell estimates with half-cell / harvested-electrode truth."""

    cell_id: str
    chemistry: str | None = None
    aged_cycle_ref: int | float | None = None
    fullcell: dict[str, Any] = field(default_factory=dict)
    halfcell: dict[str, Any] = field(default_factory=dict)
    calibration: dict[str, Any] = field(default_factory=lambda: {
        "status": "pending",
        "LLI_scale": None,
        "LAM_PE_scale": None,
        "LAM_NE_scale": None,
        "residual": None,
    })
    schema_version: str = CALIBRATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationRecord:
        validate_calibration_record(data)
        return cls(
            cell_id=str(data["cell_id"]),
            chemistry=data.get("chemistry"),
            aged_cycle_ref=data.get("aged_cycle_ref"),
            fullcell=dict(data.get("fullcell") or {}),
            halfcell=dict(data.get("halfcell") or {}),
            calibration=dict(data.get("calibration") or {}),
            schema_version=str(data.get("schema_version", CALIBRATION_SCHEMA_VERSION)),
        )


def validate_calibration_record(data: dict[str, Any]) -> None:
    """Raise ValueError if required calibration fields are missing."""
    if not isinstance(data, dict):
        raise ValueError("calibration record must be a dict")
    if not data.get("cell_id"):
        raise ValueError("calibration record requires cell_id")
    if "fullcell" not in data or not isinstance(data["fullcell"], dict):
        raise ValueError("calibration record requires fullcell dict")
    if "halfcell" not in data or not isinstance(data["halfcell"], dict):
        raise ValueError("calibration record requires halfcell dict")
    # fullcell may only have pattern scores (Level 1) — estimates optional
    fc = data["fullcell"]
    if not any(
        k in fc
        for k in (
            "LLI_pattern_score", "LAM_PE_pattern_score", "LAM_NE_pattern_score",
            "LLI_est", "LAM_PE_est", "LAM_NE_est",
        )
    ):
        raise ValueError(
            "fullcell must include at least one LLI/LAM pattern_score or est field"
        )
