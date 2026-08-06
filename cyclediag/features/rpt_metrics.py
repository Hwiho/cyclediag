"""RPT-derived metrics: Q_relax, RCF, PER — IMPROVEMENT_ROADMAP §5.10."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cyclediag.features.cell_meta import CellProtocolMeta

# Confirmed noise floor from SJ900 Ch22 TC107–108
Q_RELAX_NOISE_FLOOR_PCT = 0.065


def _q_dchg(row) -> float | None:
    if hasattr(row, "_asdict"):
        data = row._asdict()
    elif isinstance(row, pd.Series):
        data = row.to_dict()
    elif isinstance(row, dict):
        data = row
    else:
        data = dict(getattr(row, "_asdict", lambda: {})())
    for col in ("dchgCapa", "dchg_capa", "DischargeCapacity"):
        if col not in data or data[col] is None:
            continue
        try:
            v = float(data[col])
        except (TypeError, ValueError):
            continue
        if np.isfinite(v):
            return v
    return None


def compute_q_relax_for_blocks(
    features: pd.DataFrame,
    rpt_blocks: list[list[int]],
    *,
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT,
) -> pd.DataFrame:
    """One row per RPT block with Q_relax between cycle1 and cycle2."""
    if features.empty or "cycle" not in features.columns:
        return pd.DataFrame()
    by = features.set_index("cycle", drop=False)
    rows: list[dict[str, Any]] = []
    for block in rpt_blocks:
        if len(block) < 2:
            continue
        c1, c2 = int(block[0]), int(block[1])
        if c1 not in by.index or c2 not in by.index:
            continue
        q1 = _q_dchg(by.loc[c1] if not isinstance(by.loc[c1], pd.DataFrame) else by.loc[c1].iloc[0])
        q2 = _q_dchg(by.loc[c2] if not isinstance(by.loc[c2], pd.DataFrame) else by.loc[c2].iloc[0])
        if q1 is None or q2 is None or q2 == 0:
            continue
        q_relax = q2 - q1
        q_relax_pct = q_relax / q2 * 100.0
        rows.append({
            "rpt_block_c1": c1,
            "rpt_block_c2": c2,
            "Q_relax": q_relax,
            "Q_relax_pct": q_relax_pct,
            "Q_relax_significant": abs(q_relax_pct) > noise_floor_pct,
            "Q_rpt_c1": q1,
            "Q_rpt_c2": q2,
        })
    return pd.DataFrame(rows)


def attach_q_relax_to_features(
    features: pd.DataFrame,
    rpt_blocks: list[list[int]],
    *,
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT,
) -> pd.DataFrame:
    """Broadcast block Q_relax onto both RPT cycles (and NaN elsewhere)."""
    out = features.copy()
    for col in ("Q_relax", "Q_relax_pct", "Q_relax_significant"):
        if col not in out.columns:
            out[col] = np.nan if col != "Q_relax_significant" else None
    block_df = compute_q_relax_for_blocks(out, rpt_blocks, noise_floor_pct=noise_floor_pct)
    if block_df.empty:
        return out
    for _, br in block_df.iterrows():
        for c in (int(br["rpt_block_c1"]), int(br["rpt_block_c2"])):
            mask = out["cycle"] == c
            out.loc[mask, "Q_relax"] = br["Q_relax"]
            out.loc[mask, "Q_relax_pct"] = br["Q_relax_pct"]
            out.loc[mask, "Q_relax_significant"] = br["Q_relax_significant"]
    return out


def attach_rcf(
    features: pd.DataFrame,
    *,
    routine_mask: pd.Series | None = None,
    rpt_cycles: set[int] | None = None,
) -> pd.DataFrame:
    """RCF(N) = Q_0.5C(N) / Q_C3(nearest RPT cycle2)."""
    out = features.copy()
    if "RCF" not in out.columns:
        out["RCF"] = np.nan
    if out.empty or "cycle" not in out.columns:
        return out

    rpt = sorted(rpt_cycles or [])
    if not rpt:
        # heuristic: cycles with |I| lower — use capa from protocol if present
        if "cycle_role" in out.columns:
            rpt = sorted(out.loc[out["cycle_role"].astype(str).str.contains("RPT", case=False, na=False), "cycle"].astype(int))
    if len(rpt) < 1:
        return out

    by = {int(r.cycle): _q_dchg(r) for r in out.itertuples()}
    rpt_q = {c: by.get(c) for c in rpt if by.get(c)}

    def nearest_rpt(c: int) -> int | None:
        if not rpt_q:
            return None
        return min(rpt_q.keys(), key=lambda x: abs(x - c))

    for idx, row in out.iterrows():
        c = int(row["cycle"])
        if routine_mask is not None and not bool(routine_mask.loc[idx]):
            continue
        q = _q_dchg(row)
        nr = nearest_rpt(c)
        if q is None or nr is None or not rpt_q.get(nr):
            continue
        out.at[idx, "RCF"] = q / float(rpt_q[nr])
    return out


def attach_per(
    features: pd.DataFrame,
    *,
    eta_soc50_col: str = "eta_SOC50",
    r_dcir_50_col: str = "R_30s_total_soc50",
    dI_A: float | None = None,
    protocol_meta: CellProtocolMeta | None = None,
) -> pd.DataFrame:
    """PER = η(SOC50) / (ΔI · R_DCIR_50)."""
    pm = protocol_meta or CellProtocolMeta()
    delta_i = float(dI_A) if dI_A is not None else pm.per_delta_i_a
    out = features.copy()
    if "PER" not in out.columns:
        out["PER"] = np.nan
    if eta_soc50_col not in out.columns or r_dcir_50_col not in out.columns:
        return out
    for idx, row in out.iterrows():
        eta = row.get(eta_soc50_col)
        r = row.get(r_dcir_50_col)
        try:
            eta_f = float(eta)
            r_f = float(r)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(eta_f) or not np.isfinite(r_f) or r_f <= 0 or delta_i <= 0:
            continue
        # R in mΩ → Ω
        out.at[idx, "PER"] = eta_f / (delta_i * (r_f / 1000.0))
    return out
