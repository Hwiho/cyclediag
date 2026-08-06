"""Classify cycle roles: routine 0.5C vs C/3 RPT vs DCIR pulse.

SJ900 set4 protocol (nominal ~72 Ah):
- routine CC ≈ 0.5C → |I|_med ≈ 36–39 A
- RPT CC ≈ C/3 (≈0.33C) → |I|_med ≈ 24–27 A  (appears as SoHQ “bumps”)
- DCIR pulse ≈ 1C → |I|_max ≈ 70–80 A

Mid-life SoHQ spikes are **not** fade noise — they are C/3 RPT capacity points.
Fade / lean / segment trajectories must use routine_05c; RPT is a dual-track anchor.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

# Defaults tuned for SJ900 ~72 Ah @ 45 °C fixtures
DEFAULT_Q_NOMINAL_AH = 72.0
ROUTINE_C_RATE = 0.5
RPT_C_RATE = 1.0 / 3.0
PULSE_C_RATE = 1.0


def _leg_median_abs_current(g: pd.DataFrame, *, rest_current_max: float = 1.0) -> float:
    i = pd.to_numeric(g.get("current"), errors="coerce")
    if i is None or i.isna().all():
        return float("nan")
    active = i[i.abs() > rest_current_max]
    if active.empty:
        return float(i.abs().max())
    return float(active.abs().median())


def classify_cycle_currents(
    raw_df: pd.DataFrame,
    *,
    q_nominal_ah: float = DEFAULT_Q_NOMINAL_AH,
    rest_current_max: float = 1.0,
) -> pd.DataFrame:
    """Per-cycle current stats + role label from raw time series."""
    i1c = float(q_nominal_ah) * PULSE_C_RATE
    i_rpt = float(q_nominal_ah) * RPT_C_RATE
    i_rout = float(q_nominal_ah) * ROUTINE_C_RATE
    rows: list[dict[str, Any]] = []
    for cyc, g in raw_df.groupby("cycle"):
        i = pd.to_numeric(g.get("current"), errors="coerce")
        imax = float(i.abs().max()) if i is not None and i.notna().any() else float("nan")
        imed = _leg_median_abs_current(g, rest_current_max=rest_current_max)
        role = "unknown"
        if np.isfinite(imax) and imax >= 0.75 * i1c:
            role = "dcir_pulse"
        elif np.isfinite(imed):
            if abs(imed - i_rpt) <= abs(imed - i_rout) and imed < 0.85 * i_rout:
                role = "rpt_c3"
            elif imed >= 0.85 * i_rout * 0.9:
                role = "routine_05c"
            else:
                role = "other_rate"
        rows.append({
            "cycle": int(cyc),
            "I_abs_max": imax,
            "I_abs_med_cc": imed,
            "cycle_role": role,
            "C_rate_med_est": (imed / i1c) if np.isfinite(imed) and i1c > 0 else None,
        })
    return pd.DataFrame(rows).sort_values("cycle")


def attach_cycle_roles(
    features: pd.DataFrame,
    raw_df: pd.DataFrame,
    *,
    q_nominal_ah: float = DEFAULT_Q_NOMINAL_AH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Merge cycle_role onto feature rows; also split SoHQ into dual tracks."""
    roles = classify_cycle_currents(raw_df, q_nominal_ah=q_nominal_ah)
    out = features.copy()
    if "cycle" not in out.columns:
        return out, roles
    drop = [c for c in ("cycle_role", "I_abs_max", "I_abs_med_cc", "C_rate_med_est") if c in out.columns]
    out = out.drop(columns=drop, errors="ignore")
    out = out.merge(roles, on="cycle", how="left")
    out = attach_dual_track_sohq(out)
    return out, roles


def attach_dual_track_sohq(features: pd.DataFrame) -> pd.DataFrame:
    """Split SoHQ into routine vs C/3 RPT series (NaN on the other role)."""
    out = features.copy()
    sohq = pd.to_numeric(out.get("SoHQ"), errors="coerce")
    out["SoHQ_mixed"] = sohq
    role = out.get("cycle_role")
    if role is None:
        out["SoHQ_routine"] = sohq
        out["SoHQ_rpt_c3"] = np.nan
        return out
    r = role.astype(str)
    out["SoHQ_routine"] = sohq.where(r.eq("routine_05c"))
    out["SoHQ_rpt_c3"] = sohq.where(r.eq("rpt_c3"))
    return out


def routine_mask(features: pd.DataFrame) -> pd.Series:
    if "cycle_role" not in features.columns:
        return pd.Series(True, index=features.index)
    return features["cycle_role"].fillna("unknown").eq("routine_05c")


def rpt_mask(features: pd.DataFrame) -> pd.Series:
    if "cycle_role" not in features.columns:
        return pd.Series(False, index=features.index)
    return features["cycle_role"].fillna("").eq("rpt_c3")


def summarize_rpt_anchors(features: pd.DataFrame) -> pd.DataFrame:
    """One row per C/3 RPT cycle with nearest routine SoHQ for rate-gap context."""
    if features is None or features.empty or "cycle" not in features.columns:
        return pd.DataFrame()
    d = features.sort_values("cycle").copy()
    if "cycle_role" not in d.columns:
        return pd.DataFrame()
    rpt = d.loc[rpt_mask(d)].copy()
    if rpt.empty:
        return pd.DataFrame()
    rout = d.loc[routine_mask(d)].copy()
    rows: list[dict[str, Any]] = []
    for _, r in rpt.iterrows():
        cyc = int(r["cycle"])
        sohq_r = float(r["SoHQ"]) if pd.notna(r.get("SoHQ")) else None
        # nearest routine before this RPT
        before = rout.loc[rout["cycle"] < cyc]
        after = rout.loc[rout["cycle"] > cyc]
        prev = before.iloc[-1] if not before.empty else None
        nxt = after.iloc[0] if not after.empty else None
        sohq_prev = float(prev["SoHQ"]) if prev is not None and pd.notna(prev.get("SoHQ")) else None
        sohq_next = float(nxt["SoHQ"]) if nxt is not None and pd.notna(nxt.get("SoHQ")) else None
        gap_prev = (
            sohq_r - sohq_prev
            if sohq_r is not None and sohq_prev is not None
            else None
        )
        rows.append({
            "cycle": cyc,
            "SoHQ_rpt_c3": sohq_r,
            "C_rate_med_est": float(r["C_rate_med_est"]) if pd.notna(r.get("C_rate_med_est")) else None,
            "I_abs_med_cc": float(r["I_abs_med_cc"]) if pd.notna(r.get("I_abs_med_cc")) else None,
            "cycle_routine_prev": int(prev["cycle"]) if prev is not None else None,
            "SoHQ_routine_prev": sohq_prev,
            "SoHQ_gap_vs_prev_routine": gap_prev,
            "cycle_routine_next": int(nxt["cycle"]) if nxt is not None else None,
            "SoHQ_routine_next": sohq_next,
            "note": "C/3 RPT capacity (not fade spike)",
        })
    return pd.DataFrame(rows)
