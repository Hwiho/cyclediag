"""DOE cathode-arm comparison: early parameters + degradation mechanism deltas.

Designed for DOE3 (same Si-on-Gr anode; cathode arms differ, e.g. S83S vs Bimodal).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cyclediag.features.cycle_roles import routine_mask


EARLY_FEATURES = (
    "SoHQ", "CE", "VE", "EE",
    "chg_dQdV_peak1_V", "chg_dQdV_peak2_V", "chg_dQdV_peak3_V",
    "dchg_dQdV_peak1_V", "dchg_dQdV_peak2_V",
    "hyst_area_low", "hyst_area_high",
    "dchg_plateau_width", "delta_dchg_plateau_V",
    "RCF", "PER", "eta_max", "eta_argmax_SOC",
    "R_ohmic_soc50", "R_ct_soc50", "mech_vs_chem_ratio", "R_ohmic_growth_100",
    "Q_relax_pct", "LAM_curve_proxy", "LLI_curve_proxy",
    "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
    "PE_side_score", "contact_stack_score", "NE_side_score", "si_cosign",
    "fade_exponent_b", "knee_cycle_bw",
)

MECH_FEATURES = (
    "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
    "interface_R_score", "solid_diffusion_score",
    "PE_side_score", "contact_stack_score", "NE_side_score", "si_cosign",
    "R_ohmic_growth_100", "mech_vs_chem_ratio", "RCF", "PER",
    "SoHQ", "Q_relax_pct",
)


def estimate_q_nominal_ah(raw: pd.DataFrame) -> float:
    """Early full-capacity discharge median (Ah)."""
    qs: list[float] = []
    for cyc, g in raw.groupby("cycle"):
        if int(cyc) > 20:
            break
        q = pd.to_numeric(g.get("discharge_capacity"), errors="coerce")
        if q is None or q.isna().all():
            continue
        qm = float(q.max())
        if qm > 200:  # mAh
            qm /= 1000.0
        if qm >= 10:
            qs.append(qm)
    if not qs:
        return 72.0
    return float(np.median(qs))


def estimate_pulse_current_a(raw: pd.DataFrame) -> float:
    """Robust 1C-ish pulse magnitude from top |I| percentiles."""
    peaks: list[float] = []
    for _, g in raw.groupby("cycle"):
        i = pd.to_numeric(g.get("current"), errors="coerce")
        if i is None or i.isna().all():
            continue
        peaks.append(float(i.abs().max()))
    if not peaks:
        return 70.0
    arr = np.asarray(peaks, dtype=float)
    # top 5% median ≈ pulse; fall back to max
    thr = float(np.quantile(arr, 0.95))
    hot = arr[arr >= thr]
    return float(np.median(hot)) if len(hot) else float(np.max(arr))


def early_window_summary(
    feats: pd.DataFrame,
    *,
    sohq_min: float = 90.0,
    max_cycle: int = 50,
    n_points: int = 8,
) -> dict[str, Any]:
    """Median early routine parameters (BOL / early-life fingerprint)."""
    d = feats.sort_values("cycle").copy()
    if "cycle_role" in d.columns:
        d = d.loc[routine_mask(d)]
    sohq = pd.to_numeric(d.get("SoHQ"), errors="coerce")
    d = d.loc[(pd.to_numeric(d["cycle"], errors="coerce") <= max_cycle) & (sohq >= sohq_min)]
    if d.empty:
        d = feats.sort_values("cycle").head(n_points)
    d = d.head(n_points)
    out: dict[str, Any] = {
        "n_early_points": int(len(d)),
        "cycle_start": int(d["cycle"].iloc[0]) if len(d) else None,
        "cycle_end": int(d["cycle"].iloc[-1]) if len(d) else None,
    }
    for col in EARLY_FEATURES:
        if col not in d.columns:
            continue
        s = pd.to_numeric(d[col], errors="coerce")
        if s.notna().any():
            out[f"early_{col}"] = float(s.median())
    return out


def late_window_summary(
    feats: pd.DataFrame,
    *,
    sohq_max: float = 95.0,
    n_points: int = 8,
) -> dict[str, Any]:
    d = feats.sort_values("cycle").copy()
    if "cycle_role" in d.columns:
        d = d.loc[routine_mask(d)]
    sohq = pd.to_numeric(d.get("SoHQ"), errors="coerce")
    d = d.loc[sohq.notna() & (sohq <= sohq_max)]
    if len(d) < n_points:
        d = feats.sort_values("cycle").tail(n_points)
    else:
        d = d.tail(n_points)
    out: dict[str, Any] = {
        "n_late_points": int(len(d)),
        "cycle_start": int(d["cycle"].iloc[0]) if len(d) else None,
        "cycle_end": int(d["cycle"].iloc[-1]) if len(d) else None,
        "SoHQ_end": float(pd.to_numeric(d["SoHQ"], errors="coerce").iloc[-1]) if len(d) and "SoHQ" in d else None,
    }
    for col in MECH_FEATURES:
        if col not in d.columns:
            continue
        s = pd.to_numeric(d[col], errors="coerce")
        if s.notna().any():
            out[f"late_{col}"] = float(s.median())
    return out


def mechanism_delta(early: dict[str, Any], late: dict[str, Any]) -> dict[str, Any]:
    """Late − early for mechanism scores (positive = grew with aging)."""
    out: dict[str, Any] = {}
    for col in MECH_FEATURES:
        e, l = early.get(f"early_{col}"), late.get(f"late_{col}")
        if e is None or l is None:
            continue
        if not (np.isfinite(e) and np.isfinite(l)):
            continue
        out[f"delta_{col}"] = float(l - e)
    return out


def arm_aggregate(cell_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Mean±std across replicate cells in one cathode arm."""
    if not cell_rows:
        return {}
    df = pd.DataFrame(cell_rows)
    out: dict[str, Any] = {"n_cells": int(len(df))}
    for col in df.columns:
        if col in ("cell_id", "arm", "path"):
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        if s.notna().sum() == 0:
            continue
        out[f"{col}_mean"] = float(s.mean())
        out[f"{col}_std"] = float(s.std(ddof=0)) if len(s) > 1 else 0.0
    return out


def compare_arms(
    arm_a: dict[str, Any],
    arm_b: dict[str, Any],
    *,
    name_a: str,
    name_b: str,
) -> pd.DataFrame:
    """Table of mean differences (B − A) for early + delta mechanism keys."""
    keys = sorted({
        k[:-5] for k in set(arm_a) | set(arm_b)
        if k.endswith("_mean") and (
            k.startswith("early_") or k.startswith("delta_") or k.startswith("late_SoHQ")
            or k.startswith("fade_") or k.startswith("knee_")
        )
    })
    rows = []
    for key in keys:
        a = arm_a.get(f"{key}_mean")
        b = arm_b.get(f"{key}_mean")
        if a is None or b is None:
            continue
        sa = arm_a.get(f"{key}_std", 0.0) or 0.0
        sb = arm_b.get(f"{key}_std", 0.0) or 0.0
        diff = float(b - a)
        # rough effect size vs pooled std
        pooled = float(np.sqrt(0.5 * (sa ** 2 + sb ** 2)))
        rows.append({
            "metric": key,
            f"{name_a}_mean": a,
            f"{name_a}_std": sa,
            f"{name_b}_mean": b,
            f"{name_b}_std": sb,
            f"diff_{name_b}_minus_{name_a}": diff,
            "pooled_std": pooled,
            "effect_size": (diff / pooled) if pooled > 1e-9 else None,
            "family": (
                "early" if key.startswith("early_") else
                "delta_aging" if key.startswith("delta_") else
                "life"
            ),
        })
    return pd.DataFrame(rows).sort_values(
        by=["family", "effect_size"],
        key=lambda s: s.abs() if s.name == "effect_size" else s,
        ascending=[True, False],
    )


def top_differences(cmp: pd.DataFrame, *, family: str, n: int = 8) -> pd.DataFrame:
    d = cmp.loc[cmp["family"] == family].copy()
    if d.empty or "effect_size" not in d.columns:
        return d
    d["abs_eff"] = pd.to_numeric(d["effect_size"], errors="coerce").abs()
    return d.sort_values("abs_eff", ascending=False).head(n)


def summarize_mechanism_contrast(
    cmp: pd.DataFrame,
    *,
    name_a: str,
    name_b: str,
) -> str:
    """Human-readable cathode-arm contrast narrative."""
    lines = [
        f"## 열화기작 대비 요약 ({name_b} − {name_a})",
        "",
        "동일 음극(Si-on-Gr) · 양극만 다른 DOE에서, 초반 fingerprint와 "
        "수명 중 점수 증가(Δ=late−early)를 비교한다.",
        "",
    ]
    early = top_differences(cmp, family="early", n=6)
    aging = top_differences(cmp, family="delta_aging", n=6)
    if not early.empty:
        lines.append("### 초반부터 다른 파라미터")
        for _, r in early.iterrows():
            eff = r.get("effect_size")
            eff_s = f"{eff:+.2f}σ" if eff is not None and np.isfinite(eff) else "n/a"
            lines.append(
                f"- `{r['metric']}`: {name_a}={r[f'{name_a}_mean']:.4g} → "
                f"{name_b}={r[f'{name_b}_mean']:.4g} (Δ={r[f'diff_{name_b}_minus_{name_a}']:+.4g}, {eff_s})"
            )
        lines.append("")
    if not aging.empty:
        lines.append("### 열화와 함께 갈라지는 기작 (Δ late−early)")
        for _, r in aging.iterrows():
            eff = r.get("effect_size")
            eff_s = f"{eff:+.2f}σ" if eff is not None and np.isfinite(eff) else "n/a"
            metric = str(r["metric"]).replace("delta_", "")
            lines.append(
                f"- `{metric}` 증가량: {name_a}={r[f'{name_a}_mean']:+.4g} vs "
                f"{name_b}={r[f'{name_b}_mean']:+.4g} (차이 {r[f'diff_{name_b}_minus_{name_a}']:+.4g}, {eff_s})"
            )
        lines.append("")
    lines.append(
        "> 해석 주의: PE_side / LAM_PE_pattern은 NCM 이차입자 **activity/isolation pattern**이며 "
        "절대 LAM%가 아니다. contact_stack은 전극 미분해 스택/접촉 가설이다."
    )
    return "\n".join(lines)
