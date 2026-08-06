"""Full-cell degradation-mode diagnosis (LLI / LAM / impedance …)."""

from __future__ import annotations

from .engine import diagnose_feature_table, diagnosis_wide_columns
from .schema import DIAGNOSIS_VERSION_FULLCELL, DiagnosisResult

__all__ = [
    "DIAGNOSIS_VERSION_FULLCELL",
    "DiagnosisResult",
    "diagnose_feature_table",
    "diagnosis_wide_columns",
]
