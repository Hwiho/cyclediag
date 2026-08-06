"""Electrode-side hypothesis diagnosis (v1.1 — validated methodology).

Level: ``hypothesis_bol_ocp``.
Changes vs v1.0:
- Peak attribution uses synthetic full-cell OCP peaks (not cathode-vs-Li V).
- Peak boost is Δhits vs baseline (BOL hits do not inflate PE).
- ``contact_loss`` maps to **contact_stack** first; NE label only with Si co-sign.
- SOC feature boosts ignore missing/zero sentinel values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cyclediag.diagnosis.halfcell.ocp_library import (
    OcpLibrary,
    fullcell_ocp_peak_voltages,
    load_ocp_library,
)
from cyclediag.diagnosis.schema import score_column_name

PE_MODES = ("LAM_PE",)
# Ohmic/contact is stack-level until Si co-sign justifies NE hypothesis
CONTACT_MODES = ("contact_loss",)
SHARED_MODES = ("LLI", "interface_R", "SE_decomposition", "microshort", "solid_diffusion")

PE_FEATURE_EVIDENCE = (
    ("eta_argmax_SOC", "high"),
    ("hyst_area_high", "increase"),
    ("dchg_fit_residual_argmax_SOC", "high"),
    ("LAM_curve_proxy", "increase"),
)
# Si chemo-mechanical co-sign for NE hypothesis (not used alone as NE score core)
SI_NE_COSIGN = (
    ("hyst_area_low", "increase"),
    ("Q_relax_pct", "increase"),
    ("mech_vs_chem_ratio", "increase"),
    ("tau_CV", "increase"),
    ("chgCVcapa", "increase"),
)
NE_FEATURE_EVIDENCE = (
    ("eta_argmax_SOC", "low"),
    ("hyst_area_low", "increase"),
    ("dchg_fit_residual_argmax_SOC", "low"),
) + SI_NE_COSIGN


@dataclass
class ElectrodeSideResult:
    cycle: int | None = None
    PE_side_score: float | None = None
    NE_side_score: float | None = None
    contact_stack_score: float | None = None
    shared_side_score: float | None = None
    dominant_electrode: str = "unknown"
    # PE | NE_hypothesis | contact_stack | shared | mixed | unknown
    dominance_margin: float | None = None
    PE_top_modes: list[str] = field(default_factory=list)
    NE_top_modes: list[str] = field(default_factory=list)
    shared_top_modes: list[str] = field(default_factory=list)
    PE_supporting: list[str] = field(default_factory=list)
    NE_supporting: list[str] = field(default_factory=list)
    pe_peak_hits: int = 0
    pe_peak_hits_delta: int = 0
    si_cosign: float = 0.0
    electrode_confidence: float = 0.0
    electrode_diagnosis_level: str = "hypothesis_bol_ocp"
    electrode_diagnosis_note: str = (
        "v1.1 hypothesis: FC-OCP peak Δhits; contact_stack vs NE only with Si co-sign; "
        "not aged half-cell calibrated."
    )
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle,
            "PE_side_score": self.PE_side_score,
            "NE_side_score": self.NE_side_score,
            "contact_stack_score": self.contact_stack_score,
            "shared_side_score": self.shared_side_score,
            "dominant_electrode": self.dominant_electrode,
            "dominance_margin": self.dominance_margin,
            "PE_top_modes": ",".join(self.PE_top_modes),
            "NE_top_modes": ",".join(self.NE_top_modes),
            "shared_top_modes": ",".join(self.shared_top_modes),
            "PE_supporting": ",".join(self.PE_supporting),
            "NE_supporting": ",".join(self.NE_supporting),
            "pe_peak_hits": self.pe_peak_hits,
            "pe_peak_hits_delta": self.pe_peak_hits_delta,
            "si_cosign": self.si_cosign,
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
    support: list[str] = []
    hits = 0.0
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
            # Ignore missing stamped as 0
            if 5.0 < cur_f < 95.0 and cur_f >= 60.0:
                hits += 1
                support.append(f"{feat}={cur_f:.1f}(highSOC)")
        elif rule == "low":
            if 5.0 < cur_f < 95.0 and cur_f <= 40.0:
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
            elif cur_f > 0 and feat.endswith("_proxy"):
                hits += 0.3
                support.append(f"{feat}present")
    boost = hits / max(n, 1)
    return float(min(1.0, boost)), support


def attribute_fullcell_peaks_to_fc_ocp(
    row: dict[str, Any],
    fc_peak_vs: list[float],
    *,
    tol_v: float = 0.06,
) -> tuple[int, list[str]]:
    """Count full-cell dQ/dV peaks near **synthetic full-cell OCP** peaks."""
    hits = 0
    labels: list[str] = []
    if not fc_peak_vs:
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
            for pv in fc_peak_vs:
                if abs(fv - pv) <= tol_v:
                    hits += 1
                    labels.append(f"{key}≈FC_OCP({pv:.3f})")
                    break
    return hits, labels


def diagnose_electrode_side(
    row: dict[str, Any],
    *,
    baseline_row: dict[str, Any] | None = None,
    ocp_library: OcpLibrary | None = None,
    fc_ocp_peaks: list[float] | None = None,
    baseline_peak_hits: int = 0,
) -> ElectrodeSideResult:
    out = ElectrodeSideResult(cycle=int(row["cycle"]) if row.get("cycle") is not None else None)

    pe_mode_scores = [(m, s) for m in PE_MODES if (s := _get_score(row, m)) is not None]
    contact_scores = [(m, s) for m in CONTACT_MODES if (s := _get_score(row, m)) is not None]
    shared_mode_scores = [(m, s) for m in SHARED_MODES if (s := _get_score(row, m)) is not None]

    pe_boost, pe_feat = _feature_boost(row, baseline_row, PE_FEATURE_EVIDENCE)
    ne_boost, ne_feat = _feature_boost(row, baseline_row, NE_FEATURE_EVIDENCE)
    si_boost, si_feat = _feature_boost(row, baseline_row, SI_NE_COSIGN)
    out.si_cosign = si_boost

    peaks = fc_ocp_peaks
    if peaks is None and ocp_library is not None:
        peaks = fullcell_ocp_peak_voltages(ocp_library)
    pe_peak_hits, pe_peak_labels = attribute_fullcell_peaks_to_fc_ocp(row, peaks or [])
    out.pe_peak_hits = pe_peak_hits
    out.pe_peak_hits_delta = max(0, pe_peak_hits - int(baseline_peak_hits))

    pe_core = float(np.nanmean([s for _, s in pe_mode_scores])) if pe_mode_scores else 0.0
    contact_core = float(np.nanmean([s for _, s in contact_scores])) if contact_scores else 0.0
    sh_core = float(np.nanmean([s for _, s in shared_mode_scores])) if shared_mode_scores else 0.0

    # Only *new* peaks vs baseline boost PE (BOL fingerprint no longer pads PE)
    pe_peak_boost = min(0.15, 0.04 * out.pe_peak_hits_delta)
    pe_score = float(np.clip(0.75 * pe_core + 0.20 * pe_boost + pe_peak_boost, 0.0, 1.0))
    contact_score = float(np.clip(contact_core, 0.0, 1.0))
    # NE hypothesis score: contact × Si co-sign (without co-sign, NE stays low)
    ne_score = float(np.clip(0.55 * contact_core * (0.35 + 0.65 * si_boost) + 0.25 * ne_boost, 0.0, 1.0))
    sh_score = float(np.clip(sh_core, 0.0, 1.0))

    out.PE_side_score = pe_score
    out.NE_side_score = ne_score
    out.contact_stack_score = contact_score
    out.shared_side_score = sh_score
    out.PE_top_modes = [m for m, _ in sorted(pe_mode_scores, key=lambda x: -x[1])[:3]]
    out.NE_top_modes = [m for m, _ in sorted(contact_scores, key=lambda x: -x[1])[:3]]
    out.shared_top_modes = [m for m, _ in sorted(shared_mode_scores, key=lambda x: -x[1])[:4]]
    out.PE_supporting = pe_feat + pe_peak_labels[:3]
    out.NE_supporting = ne_feat + si_feat[:3]

    # Dominance among PE / contact_stack / NE_hypothesis / shared
    scores = {
        "PE": pe_score,
        "contact_stack": contact_score,
        "NE_hypothesis": ne_score,
        "shared": sh_score,
    }
    # Prefer NE_hypothesis over contact_stack when Si co-sign strong and NE close to contact
    if si_boost >= 0.25 and ne_score >= contact_score - 0.05 and ne_score >= 0.25:
        ranking_key = {"PE": pe_score, "NE_hypothesis": ne_score, "shared": sh_score}
    else:
        ranking_key = {"PE": pe_score, "contact_stack": contact_score, "shared": sh_score}

    ordered = sorted(ranking_key.items(), key=lambda x: -x[1])
    top_name, top_val = ordered[0]
    second_val = ordered[1][1] if len(ordered) > 1 else 0.0
    margin = top_val - second_val
    out.dominance_margin = margin

    if top_val < 0.18:
        out.dominant_electrode = "unknown"
    elif margin < 0.06 and top_val >= 0.22:
        out.dominant_electrode = "mixed"
    elif top_name == "NE_hypothesis":
        out.dominant_electrode = "NE"
    elif top_name == "contact_stack":
        out.dominant_electrode = "contact_stack"
    else:
        out.dominant_electrode = top_name

    n_ev = len(pe_mode_scores) + len(contact_scores) + len(pe_feat) + len(si_feat)
    cov = min(1.0, n_ev / 8.0)
    sep = min(1.0, (margin or 0) / 0.2)
    ocp_ok = 1.0 if (peaks and len(peaks) > 0) else 0.3
    out.electrode_confidence = float(np.clip(0.35 * cov + 0.35 * sep + 0.30 * ocp_ok, 0.0, 1.0))

    dom = out.dominant_electrode
    if dom == "PE":
        out.narrative = (
            f"PE-side hypothesis leads (PE={pe_score:.2f}, contact={contact_score:.2f}, "
            f"NE_hyp={ne_score:.2f}). Top: {', '.join(out.PE_top_modes) or 'n/a'}."
        )
    elif dom == "NE":
        out.narrative = (
            f"NE hypothesis (contact×Si co-sign): NE_hyp={ne_score:.2f}, "
            f"contact_stack={contact_score:.2f}, si_cosign={si_boost:.2f}."
        )
    elif dom == "contact_stack":
        out.narrative = (
            f"Contact/stack ohmic pattern leads (contact={contact_score:.2f}) without strong Si co-sign "
            f"(si_cosign={si_boost:.2f}) — not electrode-resolved."
        )
    elif dom == "mixed":
        out.narrative = (
            f"Mixed signals (PE={pe_score:.2f}, contact={contact_score:.2f}, "
            f"NE_hyp={ne_score:.2f}, Δ={margin:.2f})."
        )
    elif dom == "shared":
        out.narrative = f"Shared modes lead (shared={sh_score:.2f}): {', '.join(out.shared_top_modes) or 'n/a'}."
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
    if features is None or features.empty:
        return features
    out = features.copy()
    lib = ocp_library
    if lib is None:
        try:
            lib = load_ocp_library(halfcell_dir)
        except Exception:
            lib = OcpLibrary(meta={"error": "load_failed"})
    fc_peaks = fullcell_ocp_peak_voltages(lib)

    base = {}
    if baseline_cycle is not None and "cycle" in out.columns:
        hit = out[out["cycle"] == baseline_cycle]
        if not hit.empty:
            base = hit.iloc[0].to_dict()
    elif "cycle" in out.columns and not out.empty:
        base = out.sort_values("cycle").iloc[0].to_dict()

    base_hits = 0
    if base:
        base_hits, _ = attribute_fullcell_peaks_to_fc_ocp(base, fc_peaks)

    cols = [c for c in ElectrodeSideResult().to_dict().keys() if c != "cycle"]
    for c in cols:
        if c not in out.columns:
            if c.endswith(("modes", "supporting", "note", "narrative", "level", "electrode")):
                out[c] = pd.Series([None] * len(out), dtype=object)
            else:
                out[c] = np.nan

    for idx, row in out.iterrows():
        res = diagnose_electrode_side(
            row.to_dict(),
            baseline_row=base,
            ocp_library=lib,
            fc_ocp_peaks=fc_peaks,
            baseline_peak_hits=base_hits,
        )
        for k, v in res.to_dict().items():
            if k == "cycle":
                continue
            out.at[idx, k] = v
    return out


def _label_side(row: pd.Series) -> str:
    dom = str(row.get("dominant_electrode") or "unknown")
    if dom in ("PE", "NE", "shared", "mixed", "contact_stack"):
        return dom
    return "unknown"


def segment_electrode_trajectory(
    features: pd.DataFrame,
    *,
    min_segment_cycles: int = 3,
    margin_flip: float = 0.05,
    lean_eps: float = 0.05,
    routine_only: bool = True,
) -> pd.DataFrame:
    """Segment by PE vs contact/NE lean with dwell hysteresis.

    When ``cycle_role`` is present and ``routine_only``, C/3 RPT and DCIR pulse
    cycles are excluded — mid-life SoHQ bumps are protocol RPT, not lean flips.
    """
    if features is None or features.empty or "cycle" not in features.columns:
        return pd.DataFrame()

    d = features.sort_values("cycle").copy()
    if routine_only and "cycle_role" in d.columns:
        rout = d["cycle_role"].astype(str).eq("routine_05c")
        if int(rout.sum()) >= max(min_segment_cycles, 8):
            d = d.loc[rout].copy()
    sohq = pd.to_numeric(d.get("SoHQ"), errors="coerce")
    d = d[sohq.fillna(0) >= 50.0]
    if d.empty:
        d = features.sort_values("cycle").copy()
        if routine_only and "cycle_role" in d.columns:
            rout = d["cycle_role"].astype(str).eq("routine_05c")
            if rout.any():
                d = d.loc[rout].copy()

    pe = pd.to_numeric(d.get("PE_side_score"), errors="coerce")
    ne = pd.to_numeric(d.get("NE_side_score"), errors="coerce")
    contact = pd.to_numeric(d.get("contact_stack_score"), errors="coerce")
    if contact.isna().all():
        contact = pd.to_numeric(d.get("contact_loss_score"), errors="coerce")
    # Lean axis: PE minus max(contact, NE_hyp) — contact is the main rival historically
    rival = np.fmax(ne.to_numpy(dtype=float), contact.to_numpy(dtype=float))
    delta = pe.to_numpy(dtype=float) - rival

    def _lean(dv: float) -> str:
        if not np.isfinite(dv):
            return "unknown"
        if dv >= lean_eps:
            return "PE"
        if dv <= -lean_eps:
            return "contact_or_NE"
        return "mixed"

    d = d.assign(
        _pe=pe, _ne=ne, _contact=contact, _delta=delta,
        _lean=[_lean(float(x)) if np.isfinite(x) else "unknown" for x in delta],
        _side=d.apply(_label_side, axis=1),
        _lam=pd.to_numeric(d.get("LAM_PE_pattern_score"), errors="coerce"),
        _cl=pd.to_numeric(d.get("contact_loss_score"), errors="coerce"),
    )

    knee = None
    if "knee_cycle_bw" in d.columns and d["knee_cycle_bw"].notna().any():
        knee = float(d["knee_cycle_bw"].dropna().iloc[0])

    breaks = [0]
    last_break = 0
    for i in range(1, len(d)):
        prev, cur = d.iloc[i - 1], d.iloc[i]
        changed = False
        if prev["_lean"] != cur["_lean"] and "unknown" not in (prev["_lean"], cur["_lean"]):
            changed = True
        if knee is not None:
            pc, cc = float(prev["cycle"]), float(cur["cycle"])
            if pc < knee <= cc:
                changed = True
        if changed and (i - last_break) >= min_segment_cycles:
            breaks.append(i)
            last_break = i
    breaks.append(len(d))

    rows: list[dict[str, Any]] = []
    seg_id = 0
    for a, b in zip(breaks[:-1], breaks[1:]):
        chunk = d.iloc[a:b]
        if chunk.empty:
            continue
        if len(chunk) < min_segment_cycles and rows:
            rows[-1]["cycle_end"] = int(chunk["cycle"].iloc[-1])
            rows[-1]["n_points"] = int(rows[-1]["n_points"] + len(chunk))
            if "SoHQ" in chunk.columns:
                rows[-1]["SoHQ_end"] = float(chunk["SoHQ"].iloc[-1])
            continue
        seg_id += 1
        pe_m = float(np.nanmean(chunk["_pe"]))
        ne_m = float(np.nanmean(chunk["_ne"]))
        cl_m = float(np.nanmean(chunk["_contact"]))
        sh_m = float(np.nanmean(pd.to_numeric(chunk.get("shared_side_score"), errors="coerce")))
        rival_m = max(ne_m, cl_m)
        dlt = pe_m - rival_m
        if abs(dlt) < lean_eps:
            dom = "mixed"
            rel = "PE" if dlt >= 0 else "contact_or_NE"
        elif dlt > 0:
            dom, rel = "PE", "PE"
        else:
            # Distinguish NE hypothesis vs contact_stack via mean si_cosign / labels
            si_m = float(np.nanmean(pd.to_numeric(chunk.get("si_cosign"), errors="coerce")))
            vote = chunk["_side"].value_counts()
            if si_m >= 0.25 or (len(vote) and vote.index[0] == "NE"):
                dom, rel = "NE", "NE"
            else:
                dom, rel = "contact_stack", "contact_stack"
        rows.append({
            "segment": seg_id,
            "cycle_start": int(chunk["cycle"].iloc[0]),
            "cycle_end": int(chunk["cycle"].iloc[-1]),
            "n_points": int(len(chunk)),
            "SoHQ_start": float(chunk["SoHQ"].iloc[0]) if "SoHQ" in chunk.columns else None,
            "SoHQ_end": float(chunk["SoHQ"].iloc[-1]) if "SoHQ" in chunk.columns else None,
            "dominant_electrode": dom,
            "relative_dominant": rel,
            "PE_side_score_mean": pe_m,
            "NE_side_score_mean": ne_m,
            "contact_stack_score_mean": cl_m,
            "shared_side_score_mean": sh_m,
            "dominance_margin_mean": abs(dlt),
            "PE_top_modes": str(chunk["PE_top_modes"].dropna().iloc[0]) if "PE_top_modes" in chunk and chunk["PE_top_modes"].notna().any() else None,
            "NE_top_modes": str(chunk["NE_top_modes"].dropna().iloc[0]) if "NE_top_modes" in chunk and chunk["NE_top_modes"].notna().any() else None,
            "shared_top_modes": str(chunk["shared_top_modes"].dropna().iloc[0]) if "shared_top_modes" in chunk and chunk["shared_top_modes"].notna().any() else None,
            "electrode_confidence_mean": float(
                np.nanmean(pd.to_numeric(chunk.get("electrode_confidence"), errors="coerce").to_numpy(dtype=float))
            ) if "electrode_confidence" in chunk.columns else None,
            "LAM_PE_mean": float(np.nanmean(chunk["_lam"])),
            "contact_loss_mean": float(np.nanmean(chunk["_cl"])),
            "LLI_mean": float(np.nanmean(pd.to_numeric(chunk.get("LLI_pattern_score"), errors="coerce"))) if "LLI_pattern_score" in chunk else None,
            "si_cosign_mean": float(np.nanmean(pd.to_numeric(chunk.get("si_cosign"), errors="coerce"))),
            "fade_exponent_b": float(chunk["fade_exponent_b"].iloc[0]) if "fade_exponent_b" in chunk and pd.notna(chunk["fade_exponent_b"].iloc[0]) else None,
            "knee_cycle_bw": knee,
            "crosses_knee": bool(knee is not None and chunk["cycle"].min() <= knee <= chunk["cycle"].max()),
        })
    return pd.DataFrame(rows)
