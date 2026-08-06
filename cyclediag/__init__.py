"""cyclediag — standalone cycle / voltage-profile diagnosis engine.

Self-contained replacement for ``cyclediag`` (no GUI, no ``pne_studio2`` dependency).
"""

from __future__ import annotations

__version__ = "1.0.0"

from cyclediag.api import (
    diagnose_csv,
    diagnose_dataframe,
    diagnose_folder,
    extract_features,
    screen_problems,
)

__all__ = [
    "__version__",
    "diagnose_csv",
    "diagnose_dataframe",
    "diagnose_folder",
    "extract_features",
    "screen_problems",
]
