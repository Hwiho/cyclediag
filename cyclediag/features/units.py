"""Capacity / current unit helpers — prefer header units over value heuristics."""

from __future__ import annotations

import re
from typing import Any


_UNIT_RE = re.compile(
    r"\((?P<u>m?ah|a|ma|v|mv|ohm|mohm|s|sec|celsius|degc|°c)\)",
    re.IGNORECASE,
)


def parse_unit_from_header(header: str | None) -> str | None:
    if not header:
        return None
    h = str(header)
    m = _UNIT_RE.search(h)
    if m:
        return m.group("u").lower().replace("°", "deg")
    hl = h.lower().replace(" ", "")
    if hl.endswith("mah") or "capacity(mah)" in hl:
        return "mah"
    if hl.endswith("(ah)") or hl.endswith("_ah"):
        return "ah"
    if "current(ma)" in hl or hl.endswith("ma"):
        return "ma"
    if "current(a)" in hl:
        return "a"
    return None


def capacity_to_ah(
    q: Any,
    *,
    unit: str | None = None,
    header: str | None = None,
) -> float | None:
    """Convert capacity to Ah using explicit unit / header; never guess from magnitude."""
    try:
        v = float(q)
    except (TypeError, ValueError):
        return None
    if not (v == v):  # NaN
        return None
    u = (unit or parse_unit_from_header(header) or "").lower()
    if u in {"mah", "mah"}:
        return v / 1000.0
    if u in {"ah", "a·h", "a*h"}:
        return v
    # Logical columns after normalize are already Ah for Studio Ah exports.
    # Do NOT divide large values — that heuristic breaks ~72 Ah cells.
    return v


def current_to_a(
    i: Any,
    *,
    unit: str | None = None,
    header: str | None = None,
) -> float | None:
    try:
        v = float(i)
    except (TypeError, ValueError):
        return None
    if not (v == v):
        return None
    u = (unit or parse_unit_from_header(header) or "").lower()
    if u == "ma":
        return v / 1000.0
    return v
