"""Phase 4 — cycle-to-cycle peak tracking (V/H trajectories, H_norm, trends)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class GoldenPeakReference:
    """Median V/H reference per (leg, peak_id) from golden cycles."""

    leg: str
    peak_id: str
    v_ref: float
    h_ref: float
    h_abs_ref: float
    n_ref_cycles: int


def golden_reference_table(
    long_df: pd.DataFrame,
    good_cycles: list[int],
    *,
    usable_only: bool = True,
) -> pd.DataFrame:
    """Build golden reference medians from good cycles."""
    if long_df.empty or not good_cycles:
        return pd.DataFrame(columns=["leg", "peak_id", "V_golden", "H_golden", "H_abs_golden", "n_ref"])

    work = long_df[long_df["cycle"].isin(good_cycles)].copy()
    if usable_only and "usable_leg" in work.columns:
        work = work[work["usable_leg"]]
    if work.empty:
        work = long_df[long_df["cycle"].isin(good_cycles)].copy()

    rows: list[dict] = []
    for (leg, peak_id), grp in work.groupby(["leg", "band"], sort=False):
        v_med = grp["V"].median(numeric_only=True)
        h_med = grp["H"].median(numeric_only=True)
        if pd.isna(v_med) or pd.isna(h_med):
            continue
        h_abs = abs(float(h_med))
        rows.append({
            "leg": leg,
            "peak_id": peak_id,
            "V_golden": float(v_med),
            "H_golden": float(h_med),
            "H_abs_golden": h_abs if h_abs > 1e-12 else np.nan,
            "n_ref": int(grp["cycle"].nunique()),
        })
    return pd.DataFrame(rows)


def enrich_tracking_long(
    long_df: pd.DataFrame,
    wide_df: pd.DataFrame,
    good_cycles: list[int],
    *,
    usable_only_for_golden: bool = True,
) -> pd.DataFrame:
    """Add Phase 4 columns to long trajectory table."""
    if long_df.empty:
        return long_df.copy()

    out = long_df.copy()
    out["peak_id"] = out["band"]

    usable_map = dict(zip(wide_df["cycle"], wide_df.get("usable", False)))
    cha_map = dict(zip(wide_df["cycle"], wide_df.get("usable_charge", False)))
    dis_map = dict(zip(wide_df["cycle"], wide_df.get("usable_discharge", False)))

    if "usable" not in out.columns:
        out["usable"] = out["cycle"].map(usable_map)
    if "usable_leg" not in out.columns:
        out["usable_leg"] = out.apply(
            lambda r: cha_map.get(r["cycle"], False) if r["leg"] == "charge" else dis_map.get(r["cycle"], False),
            axis=1,
        )

    if "assign_confidence" not in out.columns:
        out["assign_confidence"] = np.nan
    if "band_height_frac" not in out.columns:
        out["band_height_frac"] = np.nan

    out["H_abs"] = out["H"].abs()
    out["good_cycle_ref"] = out["cycle"].isin(good_cycles)

    golden = golden_reference_table(out, good_cycles, usable_only=usable_only_for_golden)
    if golden.empty:
        out["V_golden"] = np.nan
        out["H_golden"] = np.nan
        out["H_abs_golden"] = np.nan
        out["H_norm"] = np.nan
        out["dV_vs_golden"] = np.nan
        out["dH_vs_golden"] = np.nan
        out["dH_abs_vs_golden"] = np.nan
    else:
        gcols = golden.rename(columns={"peak_id": "band"})
        out = out.merge(gcols, on=["leg", "band"], how="left")
        out["dV_vs_golden"] = out["V"] - out["V_golden"]
        out["dH_vs_golden"] = out["H"] - out["H_golden"]
        out["dH_abs_vs_golden"] = out["H_abs"] - out["H_abs_golden"]
        out["H_norm"] = np.where(
            out["H_abs_golden"].notna() & (out["H_abs_golden"] > 1e-12),
            out["H_abs"] / out["H_abs_golden"],
            np.nan,
        )

    out = add_cycle_derivatives(out)
    return out


def add_cycle_derivatives(track_df: pd.DataFrame) -> pd.DataFrame:
    """Per (leg, peak_id): dV/dcycle and dH/dcycle along sorted cycles."""
    if track_df.empty:
        return track_df.copy()

    out = track_df.copy()
    out["dV_dcycle"] = np.nan
    out["dH_dcycle"] = np.nan
    out["dH_abs_dcycle"] = np.nan

    for (_, _), grp in out.groupby(["leg", "peak_id"], sort=False):
        idx = grp.sort_values("cycle").index
        cyc = out.loc[idx, "cycle"].to_numpy(dtype=float)
        v = out.loc[idx, "V"].to_numpy(dtype=float)
        h = out.loc[idx, "H"].to_numpy(dtype=float)
        h_abs = out.loc[idx, "H_abs"].to_numpy(dtype=float)

        if len(cyc) < 2:
            continue
        dc = np.diff(cyc)
        valid = dc > 0
        if not valid.any():
            continue
        dv = np.diff(v)
        dh = np.diff(h)
        dh_abs = np.diff(h_abs)
        dV = np.full(len(cyc), np.nan)
        dH = np.full(len(cyc), np.nan)
        dHa = np.full(len(cyc), np.nan)
        dV[1:][valid] = dv[valid] / dc[valid]
        dH[1:][valid] = dh[valid] / dc[valid]
        dHa[1:][valid] = dh_abs[valid] / dc[valid]
        out.loc[idx, "dV_dcycle"] = dV
        out.loc[idx, "dH_dcycle"] = dH
        out.loc[idx, "dH_abs_dcycle"] = dHa

    return out


def tracking_summary_by_peak(
    track_df: pd.DataFrame,
    *,
    usable_only: bool = True,
) -> pd.DataFrame:
    """Per (leg, peak_id) summary stats for trend screening."""
    work = track_df.copy()
    if usable_only and "usable" in work.columns:
        work = work[work["usable"]]

    rows: list[dict] = []
    for (leg, peak_id), grp in work.groupby(["leg", "peak_id"], sort=False):
        g = grp.sort_values("cycle")
        rows.append({
            "leg": leg,
            "peak_id": peak_id,
            "n_cycles": int(g["cycle"].nunique()),
            "V_mean": float(g["V"].mean()),
            "V_std": float(g["V"].std(ddof=0)) if len(g) > 1 else 0.0,
            "H_abs_mean": float(g["H_abs"].mean()),
            "H_norm_mean": float(g["H_norm"].mean()) if g["H_norm"].notna().any() else np.nan,
            "dV_vs_golden_mean": float(g["dV_vs_golden"].mean()) if g["dV_vs_golden"].notna().any() else np.nan,
            "dV_dcycle_mean": float(g["dV_dcycle"].mean()) if g["dV_dcycle"].notna().any() else np.nan,
            "dH_abs_dcycle_mean": float(g["dH_abs_dcycle"].mean()) if g["dH_abs_dcycle"].notna().any() else np.nan,
            "assign_confidence_mean": float(g["assign_confidence"].mean())
            if g["assign_confidence"].notna().any() else np.nan,
        })
    return pd.DataFrame(rows)


def build_peak_tracking_tables(
    long_df: pd.DataFrame,
    wide_df: pd.DataFrame,
    good_cycles: list[int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (tracking_long, golden_ref, peak_summary)."""
    tracking = enrich_tracking_long(long_df, wide_df, good_cycles)
    golden = golden_reference_table(long_df, good_cycles)
    if not golden.empty:
        golden = golden.rename(columns={"peak_id": "peak_id"})
    summary = tracking_summary_by_peak(tracking)
    return tracking, golden, summary
