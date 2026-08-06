"""Si/Gr degradation mechanism discrimination (H1 / H2 / mixed / impedance_only)."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

MECHANISM_STATES = (
    "H1_dominant",
    "H2_dominant",
    "mixed",
    "impedance_only",
    "undetermined",
)

# Evidence keys: positive contribution to H1 or H2 when sign matches expectation
_EVIDENCE_H1: tuple[tuple[str, str, float], ...] = (
    ("Q_cliff_abs_slope_100", "near_zero", 1.2),
    ("Q_cliff_frac_slope_100", "positive", 1.0),
    ("SOC0_to_mid_ratio_slope_100", "positive", 1.3),
    ("dchg_fit_residual_argmax_SOC", "low_soc", 1.0),
    ("LLI_vs_R_ratio", "small", 0.8),
    ("fade_ratio_Si_Gr", "large", 1.0),
)

_EVIDENCE_H2: tuple[tuple[str, str, float], ...] = (
    ("Q_cliff_abs_slope_100", "negative", 1.3),
    ("LLI_vs_R_ratio", "large", 1.2),
    ("dchg_fit_residual_argmax_SOC", "dispersed", 0.7),
    ("fade_ratio_Si_Gr", "near_one", 1.1),
    ("dchg_fit_scale_slope_100", "negative", 0.9),
)


def _slope_per_100cycles(
    df: pd.DataFrame,
    col: str,
    *,
    window: int = 100,
) -> float | None:
    if col not in df.columns or "cycle" not in df.columns:
        return None
    sub = df[["cycle", col]].copy()
    sub[col] = pd.to_numeric(sub[col], errors="coerce")
    sub = sub.dropna().sort_values("cycle")
    if len(sub) < 5:
        return None
    x = sub["cycle"].to_numpy(dtype=float)
    y = sub[col].to_numpy(dtype=float)
    if len(x) >= window:
        x, y = x[-window:], y[-window:]
    if len(x) < 3:
        return None
    coef = np.polyfit(x, y, 1)
    return float(coef[0] * 100.0)


def _neutral_score() -> float:
    return 0.0


def _signed_contribution(value: float | None, expectation: str, *, toward: str) -> float:
    """Return signed evidence in [-1, 1]; missing → 0 (neutral)."""
    if value is None or not np.isfinite(value):
        return _neutral_score()

    if expectation == "near_zero":
        # H1: cliff abs slope ~ 0
        return float(np.clip(1.0 - abs(value) / 0.5, -1.0, 1.0)) if toward == "H1" else float(
            np.clip(abs(value) / 0.5 - 0.2, -1.0, 1.0)
        )
    if expectation == "negative":
        return float(np.clip(-value / 0.3, -1.0, 1.0))
    if expectation == "positive":
        return float(np.clip(value / 0.3, -1.0, 1.0))
    if expectation == "low_soc":
        # residual argmax SOC < 30 → H1
        return float(np.clip((30.0 - value) / 30.0, -1.0, 1.0))
    if expectation == "dispersed":
        return float(np.clip((value - 40.0) / 40.0, -1.0, 1.0))
    if expectation == "small":
        return float(np.clip(1.0 - value / 2.0, -1.0, 1.0))
    if expectation == "large":
        return float(np.clip(value / 3.0 - 0.5, -1.0, 1.0))
    if expectation == "near_one":
        return float(np.clip(1.0 - abs(value - 1.0) / 0.5, -1.0, 1.0))
    return _neutral_score()


def _weighted_mean_signed(terms: list[tuple[float, float]]) -> float:
    if not terms:
        return 0.0
    wsum = sum(abs(w) for _, w in terms)
    if wsum <= 0:
        return 0.0
    return float(sum(s * w for s, w in terms) / wsum)


def classify_mechanism(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    """Classify one cycle row. See work-order §3 STEP 0–4."""
    if isinstance(row, pd.Series):
        data = row.to_dict()
    else:
        data = dict(row)

    evidence_used: list[dict[str, Any]] = []

    # STEP 0 — impedance_only gate
    fit_dR = data.get("dchg_fit_dR")
    q_total = data.get("dchgCapa")
    q_bol = data.get("dchgCapa_bol")
    rcf = data.get("RCF")
    rcf_bol = data.get("RCF_bol")

    cap_maintained = False
    if q_total is not None and q_bol is not None:
        try:
            cap_maintained = abs(float(q_total) / float(q_bol) - 1.0) < 0.03
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    rcf_drop = False
    if rcf is not None and rcf_bol is not None:
        try:
            rcf_drop = float(rcf) < float(rcf_bol) * 0.95
        except (TypeError, ValueError):
            pass
    elif rcf is not None:
        rcf_drop = float(rcf) < 0.95

    dR_large = fit_dR is not None and np.isfinite(fit_dR) and abs(float(fit_dR)) > 2.0

    if dR_large and cap_maintained and rcf_drop:
        return {
            "mechanism_state": "impedance_only",
            "score_H1": 0.0,
            "score_H2": 0.0,
            "confidence": 0.7,
            "evidence_used": [{"gate": "impedance_only", "fit_dR": fit_dR, "RCF": rcf}],
        }

    # STEP 1 — evidence count
    h1_terms: list[tuple[float, float]] = []
    h2_terms: list[tuple[float, float]] = []

    for key, exp, w in _EVIDENCE_H1:
        val = data.get(key)
        if val is not None:
            try:
                vf = float(val)
            except (TypeError, ValueError):
                continue
            s = _signed_contribution(vf, exp, toward="H1")
            h1_terms.append((s, w))
            evidence_used.append({"key": key, "value": vf, "score_H1": s, "weight": w})

    for key, exp, w in _EVIDENCE_H2:
        val = data.get(key)
        if val is not None:
            try:
                vf = float(val)
            except (TypeError, ValueError):
                continue
            s = _signed_contribution(vf, exp, toward="H2")
            h2_terms.append((s, w))
            evidence_used.append({"key": key, "value": vf, "score_H2": s, "weight": w})

    n_ev = len({e["key"] for e in evidence_used})
    if n_ev < 2:
        return {
            "mechanism_state": "undetermined",
            "score_H1": _weighted_mean_signed(h1_terms),
            "score_H2": _weighted_mean_signed(h2_terms),
            "confidence": 0.2,
            "evidence_used": evidence_used,
        }

    score_h1 = _weighted_mean_signed(h1_terms)
    score_h2 = _weighted_mean_signed(h2_terms)

    # STEP 3
    if abs(score_h1 - score_h2) < 0.15:
        state = "mixed"
    elif score_h1 > score_h2:
        state = "H1_dominant"
    else:
        state = "H2_dominant"

    conf = float(np.clip(0.3 + 0.35 * n_ev / 6.0 + 0.35 * abs(score_h1 - score_h2), 0.0, 1.0))

    return {
        "mechanism_state": state,
        "score_H1": score_h1,
        "score_H2": score_h2,
        "confidence": conf,
        "evidence_used": evidence_used,
    }


def compute_mechanism_indicators(
    features: pd.DataFrame,
    *,
    baseline_cycle: int | None = None,
    group_cols: tuple[str, ...] = ("cell_id", "file"),
) -> pd.DataFrame:
    """Derive mechanism slopes and ratios from a per-cycle feature table."""
    if features.empty:
        return pd.DataFrame()

    out_rows: list[dict[str, Any]] = []
    groups = [("__all__", features)]
    if all(c in features.columns for c in group_cols):
        groups = list(features.groupby(list(group_cols), sort=False))

    for _, grp in groups:
        g = grp.sort_values("cycle").copy()
        if baseline_cycle is None:
            bc = int(g["cycle"].min())
        else:
            bc = int(baseline_cycle)
        bol = g[g["cycle"] == bc]
        if bol.empty:
            bol = g.iloc[:1]
        bol_row = bol.iloc[0]

        bol_q = bol_row.get("dchgCapa")
        bol_cliff = bol_row.get("dchg_Q_cliff_abs") or bol_row.get("Q_cliff_abs")
        bol_ratio = bol_row.get("dchg_dVdQ_SOC0_to_mid_ratio")
        bol_rcf = bol_row.get("RCF")
        bol_cgr = bol_row.get("dchg_Q_high_V")
        bol_csi = bol_row.get("dchg_Q_low_V")

        for _, row in g.iterrows():
            r = row.to_dict()
            r["dchgCapa_bol"] = bol_q
            r["RCF_bol"] = bol_rcf

            q_cliff = r.get("dchg_Q_cliff_abs") or r.get("Q_cliff_abs")
            q_tot = r.get("dchgCapa")
            if q_cliff is not None and q_tot is not None and np.isfinite(q_cliff) and np.isfinite(q_tot) and q_tot > 0:
                r["Q_cliff_frac"] = float(q_cliff) / float(q_tot)
            else:
                r["Q_cliff_frac"] = None

            if bol_cliff and q_cliff and np.isfinite(bol_cliff) and float(bol_cliff) > 0:
                r["Q_cliff_abs_norm_bol"] = float(q_cliff) / float(bol_cliff)
            else:
                r["Q_cliff_abs_norm_bol"] = None

            if bol_ratio and r.get("dchg_dVdQ_SOC0_to_mid_ratio") is not None and float(bol_ratio) > 0:
                r["SOC0_to_mid_ratio_norm_bol"] = (
                    float(r["dchg_dVdQ_SOC0_to_mid_ratio"]) / float(bol_ratio)
                )
            else:
                r["SOC0_to_mid_ratio_norm_bol"] = None

            c_gr = r.get("dchg_Q_high_V")
            c_si = r.get("dchg_Q_low_V")
            if bol_cgr and bol_csi and c_gr is not None and c_si is not None:
                try:
                    fade_gr = 1.0 - float(c_gr) / float(bol_cgr) if float(bol_cgr) > 0 else None
                    fade_si = 1.0 - float(c_si) / float(bol_csi) if float(bol_csi) > 0 else None
                    if fade_gr is not None and fade_si is not None and abs(fade_gr) > 1e-6:
                        r["fade_ratio_Si_Gr"] = fade_si / fade_gr
                    else:
                        r["fade_ratio_Si_Gr"] = None
                    r["C_Gr_abs"] = c_gr
                    r["C_Si_abs"] = c_si
                    if q_tot and float(q_tot) > 0:
                        r["C_Gr_frac"] = float(c_gr) / float(q_tot) if c_gr else None
                except (TypeError, ValueError, ZeroDivisionError):
                    r["fade_ratio_Si_Gr"] = None
            else:
                r["fade_ratio_Si_Gr"] = None

            if r.get("dchg_fit_scale") is not None and r.get("dchg_fit_offset") is not None:
                s = float(r["dchg_fit_scale"])
                o = abs(float(r["dchg_fit_offset"]))
                if s < 1.0 and (1.0 - s) > 1e-6:
                    r["LLI_LAM_ratio"] = o / (1.0 - s)
                else:
                    r["LLI_LAM_ratio"] = None

            out_rows.append(r)

    wide = pd.DataFrame(out_rows)
    if wide.empty:
        return wide

    slope_cols = {
        "Q_cliff_abs_slope_100": "dchg_Q_cliff_abs",
        "Q_cliff_frac_slope_100": "Q_cliff_frac",
        "SOC0_to_mid_ratio_slope_100": "dchg_dVdQ_SOC0_to_mid_ratio",
        "RCF_slope_100": "RCF",
        "dchg_fit_scale_slope_100": "dchg_fit_scale",
    }
    for out_col, src in slope_cols.items():
        wide[out_col] = np.nan
        if src not in wide.columns:
            continue
        if "cell_id" in wide.columns:
            for _, sub in wide.groupby("cell_id", sort=False):
                sl = _slope_per_100cycles(sub, src)
                wide.loc[sub.index, out_col] = sl
        else:
            sl = _slope_per_100cycles(wide, src)
            wide[out_col] = sl

    # classify each row
    mech_cols = []
    for idx, row in wide.iterrows():
        res = classify_mechanism(row)
        for k in ("mechanism_state", "score_H1", "score_H2", "confidence"):
            wide.at[idx, k] = res[k]
        mech_cols.append(res.get("evidence_used"))
    wide["mechanism_evidence_json"] = [json.dumps(e, ensure_ascii=False) for e in mech_cols]

    # crossover cycle: sign of score_H1 - score_H2 flips
    wide["mechanism_crossover_cycle"] = None
    if "cell_id" in wide.columns:
        for _, sub in wide.groupby("cell_id", sort=False):
            sub = sub.sort_values("cycle")
            diff = pd.to_numeric(sub["score_H1"], errors="coerce") - pd.to_numeric(
                sub["score_H2"], errors="coerce"
            )
            sign = np.sign(diff)
            flip = None
            for i in range(1, len(sign)):
                if np.isfinite(sign.iloc[i - 1]) and np.isfinite(sign.iloc[i]) and sign.iloc[i - 1] != sign.iloc[i]:
                    flip = int(sub.iloc[i]["cycle"])
                    break
            if flip is not None:
                wide.loc[sub.index, "mechanism_crossover_cycle"] = flip
    return wide


def compare_arms_bol_normalized(
    features: pd.DataFrame,
    *,
    arm_col: str = "arm",
    baseline_cycle: int | None = None,
) -> pd.DataFrame:
    """BOL-normalized arm comparison (no absolute cross-arm comparison)."""
    if arm_col not in features.columns:
        return pd.DataFrame()
    mech = compute_mechanism_indicators(features, baseline_cycle=baseline_cycle)
    cols = [
        arm_col, "cycle",
        "Q_cliff_abs_norm_bol", "SOC0_to_mid_ratio_norm_bol",
        "fade_ratio_Si_Gr", "mechanism_state", "score_H1", "score_H2",
        "LLI_vs_R_ratio", "dchg_fit_dR", "RCF",
    ]
    present = [c for c in cols if c in mech.columns]
    return mech[present].copy()
