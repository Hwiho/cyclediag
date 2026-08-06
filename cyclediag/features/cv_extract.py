"""Extract per-cycle CC/CV metrics from a normalized cycler DataFrame."""

from __future__ import annotations

import pandas as pd

from .cc_cv import CvRegionInfo, detect_cv_region


def extract_cv_regions_table(
    df: pd.DataFrame,
    *,
    cycles: list[int] | None = None,
    charge_step: str = "charge",
    discharge_step: str = "discharge",
) -> pd.DataFrame:
    """One row per (cycle, leg) with CC/CV boundary metrics."""
    if "cycle" not in df.columns:
        raise ValueError("DataFrame must have logical 'cycle' column")

    v_col = "voltage" if "voltage" in df.columns else None
    q_col = "capacity" if "capacity" in df.columns else None
    t_col = "time" if "time" in df.columns else None
    st_col = "step_type" if "step_type" in df.columns else None
    if not v_col or not st_col:
        raise ValueError("Need voltage and step_type columns")

    cycle_list = cycles if cycles is not None else sorted(df["cycle"].dropna().unique().astype(int))
    rows: list[dict] = []

    for cyc in cycle_list:
        cyc_df = df[df["cycle"] == cyc]
        if cyc_df.empty:
            continue
        for leg, st_text in (("charge", charge_step.lower()), ("discharge", discharge_step.lower())):
            seg = cyc_df[cyc_df[st_col].astype(str).str.lower() == st_text]
            if seg.empty:
                continue
            info: CvRegionInfo = detect_cv_region(
                seg, v_col=v_col, q_col=q_col, t_col=t_col,
            )
            rows.append({
                "cycle": int(cyc),
                "leg": leg,
                "has_cv": info.has_cv,
                "cv_start_index": info.cv_start_index,
                "n_cc": info.n_cc,
                "n_cv": info.n_cv,
                "cc_q_frac": info.cc_q_frac,
                "cv_time_s": info.cv_time_s,
                "v_cc_end": info.v_cc_end,
                "q_cc_end": info.q_cc_end,
                "v_cv_start": info.v_cv_start,
                "q_cv_start": info.q_cv_start,
                "current_col": info.current_col,
                "method": info.method,
            })

    return pd.DataFrame(rows)
