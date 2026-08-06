"""CC/CV region detection — shared algorithm with pne_studio2 (fallback: local)."""

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
        from .cv_region import (  # noqa: F401
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
