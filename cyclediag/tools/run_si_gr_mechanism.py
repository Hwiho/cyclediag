"""Run Si/Gr mechanism analysis on DOE2 cells (C/3 RPT cycles)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.analysis.doe_compare import load_doe2_arms, _cell_id_from_path
from cyclediag.analysis.si_gr_mechanism import (
    compare_arms_bol_normalized,
    compute_mechanism_indicators,
)
from cyclediag.features.cell_meta import CellProtocolMeta
from cyclediag.features.curve_fit import fit_curve_three_param
from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_features_table
from cyclediag.io.cycle_protocol import build_protocol_exclusion
from cyclediag.features.rpt_metrics import attach_rcf


def _load_raw(path: Path, encoding: str) -> pd.DataFrame:
    from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

    df = pd.read_csv(path, encoding=encoding, on_bad_lines="skip")
    return normalize_cycler_dataframe(df, ColumnMap.studio_default())


def _rpt_c3_mask(raw_df: pd.DataFrame, features: pd.DataFrame, meta: CellProtocolMeta) -> pd.Series:
    """Keep C/3 RPT discharge cycles (capa-check full cycles), exclude 0.5C routine."""
    excl = build_protocol_exclusion(raw_df)
    capa = set(excl.capa_full_cycles) | set(excl.rpt_cycles)
    if not capa and "cycle" in features.columns:
        # fallback: |I| near rpt current
        i_rpt = meta.rpt_current_a
        by_cyc = raw_df.groupby("cycle")["current"].apply(
            lambda s: float(pd.to_numeric(s, errors="coerce").abs().median())
        )
        capa = set(int(c) for c, med in by_cyc.items() if np.isfinite(med) and abs(med - i_rpt) < 5.0)
    mask = features["cycle"].astype(int).isin(capa)
    return mask


def _attach_curve_fits(
    features: pd.DataFrame,
    raw_df: pd.DataFrame,
    *,
    baseline_cycle: int,
    i_rpt_a: float,
) -> pd.DataFrame:
    out = features.copy()
    fit_cols = [
        "dchg_fit_scale", "dchg_fit_offset", "dchg_fit_dR",
        "dchg_fit_residual_rms", "dchg_fit_residual_max",
        "dchg_fit_residual_argmax_SOC", "dchg_fit_r2",
        "dchg_fit_corr_s_o", "dchg_fit_degenerate_flag", "LLI_vs_R_ratio",
    ]
    for c in fit_cols:
        if c not in out.columns:
            out[c] = np.nan

    base_rows = out[out["cycle"] == baseline_cycle]
    if base_rows.empty:
        return out
    base_cyc = int(base_rows.iloc[0]["cycle"])
    g0 = raw_df[raw_df["cycle"] == base_cyc]
    if g0.empty:
        return out

    from cyclediag.features.segment_utils import leg_segment

    d0 = leg_segment(
        g0, "discharge",
        charge_text="charge", discharge_text="discharge",
    )
    if d0.empty:
        return out
    q_ref = pd.to_numeric(d0.get("discharge_capacity", d0.get("capacity")), errors="coerce").to_numpy(float)
    v_ref = pd.to_numeric(d0["voltage"], errors="coerce").to_numpy(float)
    m = np.isfinite(q_ref) & np.isfinite(v_ref)
    q_ref, v_ref = q_ref[m], v_ref[m]

    for idx, row in out.iterrows():
        cyc = int(row["cycle"])
        g = raw_df[raw_df["cycle"] == cyc]
        if g.empty:
            continue
        d = leg_segment(
            g, "discharge",
            charge_text="charge", discharge_text="discharge",
        )
        if d.empty:
            continue
        qn = pd.to_numeric(d.get("discharge_capacity", d.get("capacity")), errors="coerce").to_numpy(float)
        vn = pd.to_numeric(d["voltage"], errors="coerce").to_numpy(float)
        mn = np.isfinite(qn) & np.isfinite(vn)
        qn, vn = qn[mn], vn[mn]
        if len(qn) < 20:
            continue
        fit = fit_curve_three_param(q_ref, v_ref, qn, vn, I_A=i_rpt_a)
        for k, v in fit.items():
            out.at[idx, k] = v
    return out


def run_si_gr_analysis(
    *,
    fixtures_root: Path,
    out_dir: Path,
    encoding: str = "cp949",
    cells: list[str] | None = None,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = CellProtocolMeta()
    arm_a, arm_b = load_doe2_arms(fixtures_root)
    arms = [arm_a, arm_b]

    all_feats: list[pd.DataFrame] = []
    for arm in arms:
        for path in arm.paths:
            cid = _cell_id_from_path(path)
            if cells and cid not in cells:
                continue
            print(f"extract {arm.arm_id}/{cid} …", flush=True)
            raw = _load_raw(path, encoding)
            cfg = LgesExtractConfig(
                enrich_assb=True,
                expected_pulse_current=meta.dcir_pulse_current_a,
                rest_current_max=meta.rest_current_max_a,
            )
            feats = extract_lges_features_table(raw, filepath=str(path), config=cfg, raw_df=raw)
            if feats.empty:
                continue
            feats["arm"] = arm.arm_id
            feats["cell_id"] = cid

            rpt_mask = _rpt_c3_mask(raw, feats, meta)
            rpt_cycles = set(feats.loc[rpt_mask, "cycle"].astype(int))
            feats = feats[feats["cycle"].isin(rpt_cycles)].copy()
            if feats.empty:
                print(f"  skip {cid}: no C/3 RPT cycles", flush=True)
                continue

            excl = build_protocol_exclusion(raw)
            feats = attach_rcf(feats, rpt_cycles=excl.rpt_cycles)

            bc = int(feats["cycle"].min())
            feats = _attach_curve_fits(feats, raw, baseline_cycle=bc, i_rpt_a=meta.rpt_current_a)
            all_feats.append(feats)

    if not all_feats:
        raise RuntimeError("No RPT features extracted")

    combined = pd.concat(all_feats, ignore_index=True)
    combined.to_csv(out_dir / "rpt_features.csv", index=False)

    mech = compute_mechanism_indicators(combined)
    mech.to_csv(out_dir / "mechanism_by_cycle.csv", index=False)

    arm_cmp = compare_arms_bol_normalized(combined)
    arm_cmp.to_csv(out_dir / "arm_compare_bol_norm.csv", index=False)

    # summary table per cell (latest RPT cycle)
    summary_rows = []
    for (arm, cid), grp in mech.groupby(["arm", "cell_id"], sort=False):
        last = grp.sort_values("cycle").iloc[-1]
        summary_rows.append({
            "arm": arm,
            "cell_id": cid,
            "cycle": int(last["cycle"]),
            "Q_total": last.get("dchgCapa"),
            "Q_cliff_abs": last.get("dchg_Q_cliff_abs"),
            "Q_cliff_frac": last.get("Q_cliff_frac"),
            "SOC0_to_mid": last.get("dchg_dVdQ_SOC0_to_mid_ratio"),
            "fit_s": last.get("dchg_fit_scale"),
            "fit_o": last.get("dchg_fit_offset"),
            "fit_dR": last.get("dchg_fit_dR"),
            "LLI_vs_R": last.get("LLI_vs_R_ratio"),
            "resid_argmax_SOC": last.get("dchg_fit_residual_argmax_SOC"),
            "RCF": last.get("RCF"),
            "mechanism_state": last.get("mechanism_state"),
            "score_H1": last.get("score_H1"),
            "score_H2": last.get("score_H2"),
            "mechanism_crossover_cycle": last.get("mechanism_crossover_cycle"),
            "fade_ratio_Si_Gr": last.get("fade_ratio_Si_Gr"),
        })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_dir / "mechanism_summary.csv", index=False)

    report = {
        "n_cells": len(summary),
        "n_cycles": int(len(mech)),
        "cells": summary.to_dict(orient="records"),
    }
    (out_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main() -> None:
    p = argparse.ArgumentParser(description="Si/Gr mechanism analysis (C/3 RPT)")
    p.add_argument("--fixtures", type=Path, default=Path("example/fixtures"))
    p.add_argument("--out", type=Path, default=Path("example/output/si_gr_mechanism"))
    p.add_argument("--encoding", default="cp949")
    p.add_argument("--cells", nargs="*", default=None)
    args = p.parse_args()
    run_si_gr_analysis(
        fixtures_root=args.fixtures,
        out_dir=args.out,
        encoding=args.encoding,
        cells=args.cells,
    )


if __name__ == "__main__":
    main()
