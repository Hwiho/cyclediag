"""Validation diagnostics for electrode-side / pattern scoring methodology."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def lam_pe_ceiling_stats(features: pd.DataFrame, *, ceiling: float = 0.3095, tol: float = 1e-4) -> dict[str, Any]:
    s = pd.to_numeric(features.get("LAM_PE_pattern_score"), errors="coerce").dropna()
    if s.empty:
        return {"n": 0, "ceiling_frac": None, "nunique": 0}
    at = (s - ceiling).abs() <= tol
    return {
        "n": int(len(s)),
        "ceiling_frac": float(at.mean()),
        "nunique": int(s.nunique()),
        "min": float(s.min()),
        "max": float(s.max()),
        "mean": float(s.mean()),
    }


def lean_leave_one_out_sensitivity(features: pd.DataFrame) -> dict[str, Any]:
    """How much Δ lean correlates with contact_loss vs LAM_PE (dominance check)."""
    d = features.dropna(subset=["PE_side_score"]).copy()
    if "contact_stack_score" in d.columns:
        rival = pd.to_numeric(d["contact_stack_score"], errors="coerce")
    else:
        rival = pd.to_numeric(d.get("NE_side_score"), errors="coerce")
    if len(d) < 5:
        return {"n": len(d)}
    delta = pd.to_numeric(d["PE_side_score"], errors="coerce") - rival
    cl = pd.to_numeric(d.get("contact_loss_score"), errors="coerce")
    lam = pd.to_numeric(d.get("LAM_PE_pattern_score"), errors="coerce")
    out: dict[str, Any] = {"n": int(len(d))}
    if cl.notna().sum() > 3:
        out["corr_delta_contact"] = float(delta.corr(cl))
    if lam.notna().sum() > 3:
        out["corr_delta_lam_pe"] = float(delta.corr(lam))
    out["note"] = "Δ lean should not be a near-proxy of contact alone after v1.3"
    return out


def peak_attribution_sanity(features: pd.DataFrame) -> dict[str, Any]:
    hits = pd.to_numeric(features.get("pe_peak_hits"), errors="coerce")
    dhit = pd.to_numeric(features.get("pe_peak_hits_delta"), errors="coerce")
    if hits is None or hits.isna().all():
        return {"available": False}
    early = features.nsmallest(5, "cycle") if "cycle" in features.columns else features.head(5)
    late = features.nlargest(5, "cycle") if "cycle" in features.columns else features.tail(5)
    return {
        "available": True,
        "mean_hits": float(hits.mean()),
        "mean_hits_delta": float(dhit.mean()) if dhit is not None and dhit.notna().any() else None,
        "early_mean_delta": float(pd.to_numeric(early.get("pe_peak_hits_delta"), errors="coerce").mean()),
        "late_mean_delta": float(pd.to_numeric(late.get("pe_peak_hits_delta"), errors="coerce").mean()),
    }


def q_relax_coverage(features: pd.DataFrame) -> dict[str, Any]:
    """Fraction of routine rows with Q_relax (should be high after FF fix)."""
    d = features
    if "cycle_role" in d.columns:
        rout = d[d["cycle_role"].astype(str).eq("routine_05c")]
    else:
        rout = d
    qr = pd.to_numeric(rout.get("Q_relax_pct"), errors="coerce")
    n = int(len(rout))
    nn = int(qr.notna().sum()) if qr is not None else 0
    return {
        "routine_n": n,
        "q_relax_nonnull": nn,
        "coverage": float(nn / n) if n else None,
    }


def residual_soc_domain_check(features: pd.DataFrame) -> dict[str, Any]:
    """Sanity: discharge residual argmax SOC should mostly sit in (5, 95)."""
    s = pd.to_numeric(features.get("dchg_fit_residual_argmax_SOC"), errors="coerce").dropna()
    if s.empty:
        return {"available": False}
    return {
        "available": True,
        "n": int(len(s)),
        "median": float(s.median()),
        "frac_in_5_95": float(((s > 5) & (s < 95)).mean()),
        "frac_near_0_or_100": float(((s <= 5) | (s >= 95)).mean()),
    }


def role_counts(features: pd.DataFrame) -> dict[str, Any]:
    if "cycle_role" not in features.columns:
        return {"available": False}
    return {"available": True, "counts": features["cycle_role"].astype(str).value_counts().to_dict()}


def summarize_validation(features: pd.DataFrame) -> dict[str, Any]:
    return {
        "lam_pe": lam_pe_ceiling_stats(features),
        "lean_sensitivity": lean_leave_one_out_sensitivity(features),
        "peak_attribution": peak_attribution_sanity(features),
        "q_relax_coverage": q_relax_coverage(features),
        "residual_soc": residual_soc_domain_check(features),
        "cycle_roles": role_counts(features),
        "n_rows": int(len(features)),
        "methodology_version": "electrode_side_v1_3",
        "chemistry": "ASSB_SJ900_Si_on_Gr",
    }
