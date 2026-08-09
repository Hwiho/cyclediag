"""CC/CV region detection — vendored copy, optional pne_studio override."""

from __future__ import annotations

try:
    from pne_studio2.core.cv_region import (  # noqa: F401
        CvRegionInfo,
        detect_cv_region,
        resolve_current_column,
        trim_to_cc_end,
    )
except ImportError:
    try:
        from pne_studio.core.cv_region import (  # noqa: F401
            CvRegionInfo,
            detect_cv_region,
            resolve_current_column,
            trim_to_cc_end,
        )
    except ImportError:
        from cyclediag.features._cv_region import (  # noqa: F401
            CvRegionInfo,
            detect_cv_region,
            resolve_current_column,
            trim_to_cc_end,
        )

__all__ = [
    "CvRegionInfo",
    "detect_cv_region",
    "resolve_current_column",
    "trim_to_cc_end",
]
