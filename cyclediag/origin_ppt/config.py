"""Paths and layout for dVdQ@SOC0 Origin OLE slides.

Mirrors data_analysis/hppc_analysis: 16:9 960×540 pt, Origin graph OLE paste.
"""

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent.parent
_AX_CANDIDATES = (
    PACKAGE / "template" / "260417_AX가속화_양식.pptx",
    ROOT / "data_analysis" / "slides" / "template" / "260417_AX가속화_양식.pptx",
)
AX_TEMPLATE = next((p for p in _AX_CANDIDATES if p.exists()), _AX_CANDIDATES[-1])
CACHE_DIR = PACKAGE / "cache"
WORK_OPJU = CACHE_DIR / "work.opju"
XY_CACHE = ROOT / "example" / "output" / "dvdq_soc0_slides" / "origin_xy"


def default_out(deck_id: str, *, backend: str = "origin") -> Path:
    suffix = "ole" if backend == "origin" else "mpl"
    folder = ROOT / "example" / "output" / f"{deck_id}_slides"
    if deck_id == "dvdq_soc0" and backend == "origin":
        return folder / "dVdQ_SOC0_SJ900_SJ1300_ole.pptx"
    return folder / f"{deck_id}_SJ900_SJ1300_{suffix}.pptx"


DEFAULT_OUT = default_out("dvdq_soc0")

ARM_CSV = ROOT / "example" / "output" / "crossover_vs_sohq" / "present_1600x1000" / "dvdq_soc0_arm"
TAGGED = {
    "SJ900": ROOT / "example" / "output" / "set4" / "dvdq_soc0" / "SJ900_dvdq_soc0_tagged.csv",
    "SJ1300": ROOT / "example" / "output" / "SJ1300_dry" / "dvdq_soc0" / "SJ1300_dvdq_soc0_tagged.csv",
}
MECHANISM = ROOT / "example" / "output" / "si_gr_mechanism" / "mechanism_summary.csv"
RAW_CELLS = {
    "M01Ch022": (ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv", "set4_SJ900"),
    "M01Ch024": (ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv", "set4_SJ900"),
    "M01Ch025": (ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv", "set4_SJ900"),
    "M01Ch010": (ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv", "SJ1300_dry"),
    "M01Ch011": (ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv", "SJ1300_dry"),
    "M01Ch012": (ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv", "SJ1300_dry"),
}

PP_PASTE_OLE_OBJECT = 10
PP_LAYOUT_BLANK = 12
PP_SAVE_AS_OPENXML = 24
MSO_TRUE = -1
MSO_FALSE = 0
MSO_EMBEDDED_OLE_OBJECT = 7
MSO_TEXT_HORIZONTAL = 1
ORIGIN_OLE_PROG_ID = "origin95.graph"

SLIDE_W = 960.0
SLIDE_H = 540.0
BODY_LEFT = 38.0
BODY_TOP = 92.0
BODY_WIDTH = 884.0
BODY_BOTTOM = 505.0
BODY_HEIGHT = BODY_BOTTOM - BODY_TOP
GRAPH_GAP = 12.0

CELL_COLOR = {
    "M01Ch022": "#1565c0",
    "M01Ch024": "#2e7d32",
    "M01Ch025": "#00838f",
    "M01Ch010": "#c62828",
    "M01Ch011": "#ef6c00",
    "M01Ch012": "#6a1b9a",
}
ARM_CELLS = {
    "SJ900": ("M01Ch022", "M01Ch024"),
    "SJ1300": ("M01Ch010", "M01Ch011", "M01Ch012"),
}
OVERLAY_CELLS = {
    "SJ900": ("M01Ch022", "M01Ch024", "M01Ch025"),
    "SJ1300": ("M01Ch010", "M01Ch011", "M01Ch012"),
}
PROFILE_CELLS = {
    "SJ900": "M01Ch022",
    "SJ1300": "M01Ch012",
}
PANEL_ORDER = (
    ("SJ900", "M01Ch022"),
    ("SJ900", "M01Ch024"),
    ("SJ900", "M01Ch025"),
    ("SJ1300", "M01Ch010"),
    ("SJ1300", "M01Ch011"),
    ("SJ1300", "M01Ch012"),
)
