"""Report layers for indicator scoring — Health / Mechanism / Protocol anchors.

Does not assign degradation modes. Used by the indicator-score track to present
results without mixing in causal interpretation.
"""

from __future__ import annotations

from typing import Iterable

from cyclediag.features.indicator_registry import ROLE_TARGET, family_of, role_of

LAYER_HEALTH = "health"
LAYER_MECHANISM = "mechanism"
LAYER_ANCHOR = "protocol_anchor"

_ANCHOR_EXACT = frozenset({
    "Q_relax", "Q_relax_pct", "Q_relax_dcir", "Q_relax_dcir_pct",
    "Q_relax_rpt", "Q_relax_rpt_pct",
    "ocv_parallel_shift", "delta_ocv_spread_20_80",
    "ocv_spread_20_80", "ocv_spread_50_80", "ocv_spread_20_50",
    "PER", "RCF",
})
_ANCHOR_PREFIXES = (
    "R_ohmic_", "R_ct_", "A_diff_", "tau_ct_", "R_30s_total_",
    "R_recovery_", "V_inf_rest_", "V_inf_est_",
    "self_discharge_rate_", "relax_completeness_",
)


def report_layer(col: str) -> str:
    """Classify a column into health / mechanism / protocol_anchor."""
    if role_of(col) == ROLE_TARGET or family_of(col) in (
        "capacity_discharge", "capacity_charge", "capacity_legacy",
    ):
        return LAYER_HEALTH
    base = col[6:] if col.startswith("delta_") else col
    if base in _ANCHOR_EXACT or col in _ANCHOR_EXACT:
        return LAYER_ANCHOR
    if any(base.startswith(p) or col.startswith(p) for p in _ANCHOR_PREFIXES):
        return LAYER_ANCHOR
    return LAYER_MECHANISM


def annotate_layers(frame, *, column: str = "feature"):
    """Add a ``report_layer`` column to an indicator summary table."""
    if frame is None or frame.empty or column not in frame.columns:
        return frame
    out = frame.copy()
    out["report_layer"] = [report_layer(str(n)) for n in out[column]]
    return out


def split_by_layer(summary, *, column: str = "feature") -> dict[str, object]:
    """Return {layer: subframe} for a scored indicator summary."""
    ann = annotate_layers(summary, column=column)
    if ann is None or ann.empty:
        return {LAYER_HEALTH: ann, LAYER_MECHANISM: ann, LAYER_ANCHOR: ann}
    return {
        layer: ann[ann["report_layer"] == layer].reset_index(drop=True)
        for layer in (LAYER_HEALTH, LAYER_MECHANISM, LAYER_ANCHOR)
    }


def layer_order(cols: Iterable[str]) -> list[str]:
    """Stable order: health, mechanism, anchors."""
    rank = {LAYER_HEALTH: 0, LAYER_MECHANISM: 1, LAYER_ANCHOR: 2}
    return sorted(cols, key=lambda c: (rank.get(report_layer(c), 9), c))
