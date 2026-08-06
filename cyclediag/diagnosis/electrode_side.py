"""Electrode-side (PE/NE) hypothesis diagnosis from full-cell features + BOL OCP.

Level: hypothesis only (`electrode_diagnosis_level=hypothesis_bol_ocp`).
Does NOT emit absolute LAM_PE/LAM_NE % without aged half-cell truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cyclediag.diagnosis.halfcell.ocp_library import OcpLibrary, load_ocp_library
from cyclediag.diagnosis.schema import score_column_name

# Mode → electrode side mapping for ASSB Si-rich (hypothesis)
PE_MODES = ("LAM_PE",)
NE_MODES = ("contact_loss",)  # Si chemo-mechanical contact is NE-driven primary path
SHARED_MODES = ("LLI", "interface_R", "SE_decomposition", "microshort", "solid_diffusion")

# Extra feature evidence (not mode scores) assigned to sides
PE_FEATURE_EVIDENCE = (
    ("eta_argmax_SOC", "high"),          # high SOC limitation → PE
    ("hyst_area_high", "increase"),
    ("dchg_fit_residual_argmax_SOC", "high"),
    ("LAM_curve_proxy", "increase"),
)
NE_FEATURE_EVIDENCE = (
    ("eta_argmax_SOC", "low"),           # low SOC limitation → NE/Si
    ("hyst_area_low", "increase"),
    ("dchg_fit_residual_argmax_SOC", "low"),
    ("tau_CV", "increase"),
    ("chgCVcapa", "increase"),
    ("R_ohmic_soc50", "increase"),
    ("mech_vs_chem_ratio", "increase"),
)


@dataclass
class ElectrodeSideResult:
    cycle: int | None = None
    PE_side_score: float | None = None
    NE_side_score: float | None = None
    shared_side_score: float | None = None
    dominant_electrode: str = "unknown"  # PE | NE | shared | mixed | unknown
    dominance_margin: float | None = None
    PE_top_modes: list[str] = field(default_factory=list)
    NE_top_modes: list[str] = field(default_factory=list)
    shared_top_modes: list[str] = field(default_factory=list)
    PE_supporting: list[str] = field(default_factory=list)
    NE_supporting: list[str] = field(default_factory=list)
    pe_peak_hits: int = 0
    electrode_confidence: float = 0.0
    electrode_diagnosis_level: str = "hypothesis_bol_ocp"
    electrode_diagnosis_note: str = (
        "Hypothesis from full-cell patterns + BOL OCP peak attribution; "
        "not aged half-cell calibrated."
    )
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle,
            "PE_side_score": self.PE_side_score,
            "NE_side_score": self.NE_side_score,
            "shared_side_score": self.shared_side_score,
            "dominant_electrode": self.dominant_electrode,
            "dominance_margin": self.dominance_margin,
            "PE_top_modes": ",".join(self.PE_top_modes),
            "NE_top_modes": ",".join(self.NE_top_modes),
            "shared_top_modes": ",".join(self.shared_top_modes),
            "PE_supporting": ",".join(self.PE_supporting),
            "NE_supporting": ",".join(self.NE_supporting),
            "pe_peak_hits": self.pe_peak_hits,
            "electrode_confidence": self.electrode_confidence,
            "electrode_diagnosis_level": self.electrode_diagnosis_level,
            "electrode_diagnosis_note": self.electrode_diagnosis_note,
            "electrode_narrative": self.narrative,
        }


def _get_score(row: dict[str, Any], mode: str) -> float | None:
    col = score_column_name(mode)
    val = row.get(col, row.get(mode))
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    return f if np.isfinite(f) else None


def _feature_boost(row: dict[str, Any], baseline: dict[str, Any] | None, specs: tuple) -> tuple[float, list[str]]:
    """Return (boost 0–1, supporting labels)."""
    support: list[str] = []
    hits = 0
    n = 0
    for feat, rule in specs:
        n += 1
        cur = row.get(feat)
        try:
            cur_f = float(cur) if cur is not None and not (isinstance(cur, float) and np.isnan(cur)) else None
        except (TypeError, ValueError):
            cur_f = None
        if cur_f is None or not np.isfinite(cur_f):
            continue
        if rule == "high":
            if cur_f >= 60.0:
                hits += 1
                support.append(f"{feat}={cur_f:.1f}(highSOC)")
        elif rule == "low":
            if cur_f <= 40.0:
                hits += 1
                support.append(f"{feat}={cur_f:.1f}(lowSOC)")
        elif rule == "increase":
            base_f = None
            if baseline and feat in baseline:
                try:
                    base_f = float(baseline[feat])
                except (TypeError, ValueError):
                    base_f = None
            if base_f is not None and np.isfinite(base_f):
                if cur_f > base_f * 1.05 + 1e-9:
                    hits += 1
                    support.append(f"{feat}↑")
            elif cur_f > 0:
                # no baseline: weak presence signal
                hits += 0.4
                support.append(f"{feat}present")
    boost = hits / max(n, 1)
    return float(min(1.0, boost)), support


def attribute_fullcell_peaks_to_pe(
    row: dict[str, Any],
    pe_peak_vs: list[float],
    *,
    tol_v: float = 0.06,
) -> tuple[int, list[str]]:
    """Count full-cell charge dQ/dV peak voltages near cathode OCP peaks."""
    hits = 0
    labels: list[str] = []
    if not pe_peak_vs:
        return 0, labels
    for i in range(1, 7):
        for key in (f"chg_dQdV_peak{i}_V", f"dchg_dQdV_peak{i}_V"):
            val = row.get(key)
            try:
                fv = float(val)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(fv):
                continue
            for pv in pe_peak_vs:
                if abs(fv - pv) <= tol_v:
                    hits += 1
                    labels.append(f"{key}≈PE({pv:.3f})")
                    break
    return hits, labels


def diagnose_electrode_side(
    row: dict[str, Any],
    *,
    baseline_row: dict[str, Any] | None = None,
    ocp_library: OcpLibrary | None = None,
) -> ElectrodeSideResult:
    """Hypothesis PE/NE side diagnosis for one cycle feature row."""
    out = ElectrodeSideResult(cycle=int(row["cycle"]) if row.get("cycle") is not None else None)

    pe_mode_scores: list[tuple[str, float]] = []
    ne_mode_scores: list[tuple[str, float]] = []
    shared_mode_scores: list[tuple[str, float]] = []

    for m in PE_MODES:
        s = _get_score(row, m)
        if s is not None:
            pe_mode_scores.append((m, s))
    for m in NE_MODES:
        s = _get_score(row, m)
        if s is not None:
            ne_mode_scores.append((m, s))
    for m in SHARED_MODES:
        s = _get_score(row, m)
        if s is not None:
            shared_mode_scores.append((m, s))

    pe_boost, pe_feat = _feature_boost(row, baseline_row, PE_FEATURE_EVIDENCE)
    ne_boost, ne_feat = _feature_boost(row, baseline_row, NE_FEATURE_EVIDENCE)

    pe_peak_hits = 0
    pe_peak_labels: list[str] = []
    if ocp_library is not None:
        pe_vs = ocp_library.cathode_peak_voltages(leg="charge")
        if not pe_vs:
            pe_vs = ocp_library.cathode_peak_voltages(leg="discharge")
        pe_peak_hits, pe_peak_labels = attribute_fullcell_peaks_to_pe(row, pe_vs)
        out.pe_peak_hits = pe_peak_hits

    pe_core = float(np.nanmean([s for _, s in pe_mode_scores])) if pe_mode_scores else 0.0
    ne_core = float(np.nanmean([s for _, s in ne_mode_scores])) if ne_mode_scores else 0.0
    sh_core = float(np.nanmean([s for _, s in shared_mode_scores])) if shared_mode_scores else 0.0

    # peak attribution lightly boosts PE confidence/score
    pe_peak_boost = min(0.25, 0.05 * pe_peak_hits)
    pe_score = float(np.clip(0.70 * pe_core + 0.25 * pe_boost + pe_peak_boost, 0.0, 1.0))
    ne_score = float(np.clip(0.70 * ne_core + 0.30 * ne_boost, 0.0, 1.0))
    sh_score = float(np.clip(sh_core, 0.0, 1.0))

    out.PE_side_score = pe_score
    out.NE_side_score = ne_score
    out.shared_side_score = sh_score
    out.PE_top_modes = [m for m, _ in sorted(pe_mode_scores, key=lambda x: -x[1])[:3]]
    out.NE_top_modes = [m for m, _ in sorted(ne_mode_scores, key=lambda x: -x[1])[:3]]
    out.shared_top_modes = [m for m, _ in sorted(shared_mode_scores, key=lambda x: -x[1])[:4]]
    out.PE_supporting = pe_feat + pe_peak_labels[:4]
    out.NE_supporting = ne_feat

    # dominance
    margin = abs(pe_score - ne_score)
    out.dominance_margin = margin
    if max(pe_score, ne_score, sh_score) < 0.2:
        out.dominant_electrode = "unknown"
    elif sh_score >= max(pe_score, ne_score) + 0.08 and sh_score >= 0.35:
        out.dominant_electrode = "shared"
    elif margin < 0.08 and max(pe_score, ne_score) >= 0.25:
        out.dominant_electrode = "mixed"
    elif pe_score > ne_score:
        out.dominant_electrode = "PE"
    else:
        out.dominant_electrode = "NE"

    # confidence: evidence coverage + separation + optional OCP library
    n_ev = len(pe_mode_scores) + len(ne_mode_scores) + len(pe_feat) + len(ne_feat)
    cov = min(1.0, n_ev / 8.0)
    sep = min(1.0, margin / 0.25)
    ocp_ok = 1.0 if (ocp_library and (ocp_library.cathode or ocp_library.anode)) else 0.3
    out.electrode_confidence = float(np.clip(0.35 * cov + 0.35 * sep + 0.30 * ocp_ok, 0.0, 1.0))

    # narrative
    dom = out.dominant_electrode
    if dom == "PE":
        out.narrative = (
            f"PE-side hypothesis dominates (PE={pe_score:.2f} > NE={ne_score:.2f}). "
            f"Top PE modes: {', '.join(out.PE_top_modes) or 'n/a'}."
        )
    elif dom == "NE":
        out.narrative = (
            f"NE-side hypothesis dominates (NE={ne_score:.2f} > PE={pe_score:.2f}). "
            f"For ASSB Si-rich, contact_loss is treated as NE-driven. "
            f"Top NE modes: {', '.join(out.NE_top_modes) or 'n/a'}."
        )
    elif dom == "mixed":
        out.narrative = (
            f"Mixed PE/NE signals (PE={pe_score:.2f}, NE={ne_score:.2f}, Δ={margin:.2f}). "
            "Both electrodes likely contribute; need aged half-cell to separate amounts."
        )
    elif dom == "shared":
        out.narrative = (
            f"Shared/cell-level modes lead (shared={sh_score:.2f}): "
            f"{', '.join(out.shared_top_modes) or 'n/a'}."
        )
    else:
        out.narrative = "Insufficient electrode-side evidence for this cycle."

    return out


def attach_electrode_side_diagnosis(
    features: pd.DataFrame,
    *,
    baseline_cycle: int | None = None,
    halfcell_dir: str | Path | None = None,
    ocp_library: OcpLibrary | None = None,
) -> pd.DataFrame:
    """Append PE/NE hypothesis columns to a diagnosed feature table."""
    if features is None or features.empty:
        return features
    out = features.copy()
    lib = ocp_library
    if lib is None:
        try:
            lib = load_ocp_library(halfcell_dir)
        except Exception:
            lib = OcpLibrary(meta={"error": "load_failed"})

    base = {}
    if baseline_cycle is not None and "cycle" in out.columns:
        hit = out[out["cycle"] == baseline_cycle]
        if not hit.empty:
            base = hit.iloc[0].to_dict()
    elif "cycle" in out.columns and not out.empty:
        base = out.sort_values("cycle").iloc[0].to_dict()

    cols = list(ElectrodeSideResult().to_dict().keys())
    # skip duplicate cycle
    cols = [c for c in cols if c != "cycle"]
    for c in cols:
        if c not in out.columns:
            if c.endswith(("modes", "supporting", "note", "narrative", "level", "electrode")):
                out[c] = pd.Series([None] * len(out), dtype=object)
            else:
                out[c] = np.nan

    for idx, row in out.iterrows():
        res = diagnose_electrode_side(row.to_dict(), baseline_row=base, ocp_library=lib)
        payload = res.to_dict()
        for k, v in payload.items():
            if k == "cycle":
                continue
            out.at[idx, k] = v
    return out
