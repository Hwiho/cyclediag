"""Physics/data constraints that cap causal-diagnosis confidence.

These do not change indicator scores (Track A). They only mark when a
physicochemical mode interpretation (Track B) is under-determined.
"""

from __future__ import annotations

from typing import Any, Mapping


def constraint_flags(
    row: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return active constraint tags for one cycle row."""
    flags: list[str] = []
    cfg = config or {}
    cons = cfg.get("constraints") or {}

    temp = row.get("temperature_available")
    if temp is False or temp == 0 or temp == "False":
        flags.append("no_temperature_log")

    if cons.get("stack_pressure_MPa") is None and row.get("stack_pressure_MPa") is None:
        flags.append("stack_pressure_unknown")

    if cons.get("halfcell_calibrated") is False:
        flags.append("halfcell_uncalibrated")

    # protocol contamination — diagnosis should not trust these rows
    if bool(row.get("protocol_excluded")):
        flags.append("protocol_excluded")
    kind = str(row.get("protocol_kind") or "")
    if kind and kind not in ("routine", "unknown", "nan", ""):
        flags.append(f"protocol_{kind}")

    return flags


def confidence_multiplier(
    mode: str,
    flags: list[str],
) -> float:
    """Down-weight mode confidence when constraints apply."""
    m = 1.0
    if "protocol_excluded" in flags or any(f.startswith("protocol_") for f in flags):
        # engine should skip these rows; if scored anyway, collapse confidence
        return 0.0
    if "no_temperature_log" in flags and mode in (
        "impedance", "interface_R", "solid_diffusion", "transport", "contact_loss", "contact",
    ):
        m *= 0.85
    if "stack_pressure_unknown" in flags and mode in ("contact_loss", "contact"):
        m *= 0.7
    if "halfcell_uncalibrated" in flags:
        # Level-3 absolute estimates unavailable — slight caution on all modes
        m *= 0.95
    return float(m)
