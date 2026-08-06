"""Run diagnostic prompt Q1-Q14 on SJ900 set4 Ch22. Internal tool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cyclediag.analysis.rpt_recovery import analyze_rpt_recovery, apply_recovery_correction
from cyclediag.analysis.sohq_inflection import detect_sohq_inflections
from cyclediag.features.dqdv_peaks import DqdvPeakConfig, find_dqdv_peaks, find_dvdq_peaks
from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_cycle_row
from cyclediag.features.signal_cv import detect_cv_signal
from cyclediag.features.stepemd_extract import extract_stepemd_features_table
from cyclediag.io.cycle_protocol import POST_RPT_EXCLUDE, build_protocol_exclusion
from cyclediag.io.cycler_csv import load_cycler_csv
from cyclediag.io.stepemd_csv import load_stepemd_csv
from cyclediag.io.studio_map import studio_column_map

RAW = sorted((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*raw.csv"))[0]
STEP = sorted((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*stepend.csv"))[0]
OUT = ROOT / "example/output/diagnostic_prompt_ch22.json"

RPT_CYCLES = [4, 5, 6, 109, 110, 111, 214, 215, 216, 319, 320, 321, 424, 425, 426, 529, 530, 531]


def discharge_leg(raw: pd.DataFrame, cycle: int) -> pd.DataFrame:
    g = raw[raw["cycle"] == cycle].copy()
    cur = pd.to_numeric(g["current"], errors="coerce")
    m = cur < -1.0
    return g.loc[m].sort_values("step_time" if "step_time" in g.columns else "time")


def local_noise(x: np.ndarray, w: int = 15) -> np.ndarray:
    out = np.full(len(x), np.nan)
    for i in range(w, len(x) - w):
        s = slice(i - w, i + w + 1)
        t = np.arange(-w, w + 1)
        p = np.polyfit(t, x[s], 1)
        out[i] = np.std(x[s] - np.polyval(p, t))
    return out


def q1_noise_by_voltage(seg: pd.DataFrame) -> dict:
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    Q = pd.to_numeric(seg.get("discharge_capacity", seg.get("capacity")), errors="coerce").to_numpy(float)
    Q = np.abs(Q - Q[0])
    sigma_V = local_noise(V) * 1000
    dV = np.abs(np.gradient(V)) * 1000
    df = pd.DataFrame({"V": V, "sigma_V_mV": sigma_V, "dV_mV": dV})
    df = df.dropna()
    df["bin"] = pd.cut(df["V"], 5)
    tab = df.groupby("bin", observed=True).agg(
        sigma_V_mV=("sigma_V_mV", "median"),
        dV_mV=("dV_mV", "median"),
    )
    tab["ratio"] = tab["sigma_V_mV"] / tab["dV_mV"].replace(0, np.nan)
    return {
        "cycle": int(seg["cycle"].iloc[0]),
        "table": {str(k): v for k, v in tab.to_dict("index").items()},
        "ratio_max_over_min": float(tab["ratio"].max() / tab["ratio"].min()) if tab["ratio"].min() > 0 else None,
    }


def q2_quantization(seg: pd.DataFrame, label: str) -> dict:
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    d = np.abs(np.diff(V))
    d = d[d > 0]
    small = np.unique(np.round(d[d < 0.02], 6))[:20]
    dec = seg["voltage"].astype(str).str.split(".", expand=True)
    max_dec = int(dec[1].str.len().max()) if dec.shape[1] > 1 else 0
    return {
        "label": label,
        "min_dV": float(d.min()) if len(d) else None,
        "median_dt_s": float(np.median(np.diff(pd.to_numeric(seg["step_time"], errors="coerce")))),
        "unique_small_dV": small.tolist(),
        "max_decimal_places": max_dec,
        "n_points": len(V),
    }


def dqdv_metrics(seg: pd.DataFrame, sg_window: int = 21) -> dict:
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    Q = pd.to_numeric(seg.get("discharge_capacity", seg.get("capacity")), errors="coerce").to_numpy(float)
    Q = np.abs(Q - Q[0])
    cfg = DqdvPeakConfig(n_interp=500, sg_window=sg_window, sg_poly=3, merge_v_sep_v=0.012)
    peaks = find_dqdv_peaks(V, Q, config=cfg)
    # rebuild grid for spacing
    order = np.argsort(Q)
    q, v = Q[order], V[order]
    _, uid = np.unique(np.round(q, 9), return_index=True)
    q, v = q[uid], v[uid]
    qg = np.linspace(q.min(), q.max(), cfg.n_interp)
    vg = np.interp(qg, q, v)
    win = sg_window if sg_window % 2 == 1 else sg_window + 1
    vs = savgol_filter(vg, win, cfg.sg_poly)
    mv_per = float(np.median(np.abs(np.diff(vs))) * 1000)
    ah_per = float(np.median(np.abs(np.diff(qg))))
    return {
        "ah_per_point": ah_per,
        "mv_per_point": mv_per,
        "effective_smooth_mV": mv_per * sg_window,
        "merge_threshold_mV": 12.0,
        "ratio_smooth_over_merge": (mv_per * sg_window) / 12.0,
        "n_peaks": len(peaks),
    }


def noise_uniformity_dqdv_vs_dvdq(seg: pd.DataFrame) -> dict:
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    Q = pd.to_numeric(seg.get("discharge_capacity", seg.get("capacity")), errors="coerce").to_numpy(float)
    Q = np.abs(Q - Q[0])
    cfg = DqdvPeakConfig(n_interp=500, sg_window=21, sg_poly=3)
    order = np.argsort(Q)
    q, v = Q[order], V[order]
    _, uid = np.unique(np.round(q, 9), return_index=True)
    q, v = q[uid], v[uid]
    qg = np.linspace(q.min(), q.max(), 500)
    vg = np.interp(qg, q, v)
    vs = savgol_filter(vg, 21, 3)
    qs = savgol_filter(qg, 21, 3)
    dv = np.gradient(vs)
    dq = np.gradient(qs)
    with np.errstate(divide="ignore", invalid="ignore"):
        dqdv = np.where(np.abs(dv) > 1e-9, dq / dv, np.nan)
        dvdq = np.where(np.abs(dq) > 1e-9, dv / dq, np.nan)
    dqdv = pd.Series(dqdv).interpolate(limit_direction="both").to_numpy()
    dvdq = pd.Series(dvdq).interpolate(limit_direction="both").to_numpy()
    # bin by V
    bins = pd.cut(vg, 5)
    def cv_noise(y):
        parts = []
        for b in bins.categories:
            m = bins == b
            if m.sum() < 10:
                continue
            parts.append(float(np.nanstd(y[m]) / (np.nanmean(np.abs(y[m])) + 1e-12)))
        return float(np.std(parts) / (np.mean(parts) + 1e-12)) if parts else None
    return {
        "dqdv_relative_cv_across_V_bins": cv_noise(dqdv),
        "dvdq_relative_cv_across_V_bins": cv_noise(dvdq),
        "dvdq_more_uniform": cv_noise(dvdq) < cv_noise(dqdv) if cv_noise(dqdv) and cv_noise(dvdq) else None,
    }


def main():
    raw = load_cycler_csv(str(RAW), column_map=studio_column_map())
    step = load_stepemd_csv(STEP)
    feat_all = extract_stepemd_features_table(step_df=step, path=STEP)

    out: dict = {"raw": str(RAW), "step": str(STEP)}

    # Q1
    seg50 = discharge_leg(raw, 50)
    out["Q1"] = q1_noise_by_voltage(seg50)

    # Q2
    out["Q2"] = {
        "routine_tc50": q2_quantization(seg50, "routine_tc50_discharge"),
        "dcir_tc5": q2_quantization(raw[raw["cycle"] == 5], "dcir_tc5_full_cycle"),
        "dcir_pulse_only": q2_quantization(
            raw[(raw["cycle"] == 5) & (pd.to_numeric(raw["current"], errors="coerce").abs() > 50)],
            "dcir_tc5_pulse",
        ),
    }

    # Q3
    protocol = build_protocol_exclusion(step)
    rpt_rows = feat_all[feat_all["cycle"].isin(RPT_CYCLES)][["cycle", "dchgCapa", "SoHQ"]].copy()
    rout = feat_all[~feat_all["cycle"].isin(protocol.excluded)]
    # compare capa_full before RPT
    capa = feat_all[feat_all["cycle"].isin([107, 108])][["cycle", "dchgCapa", "SoHQ"]]
    out["Q3"] = {
        "rpt_rows_with_sohq": rpt_rows.to_dict(orient="records"),
        "sohq_nonnull_total": int(feat_all["SoHQ"].notna().sum()),
        "POST_RPT_EXCLUDE": POST_RPT_EXCLUDE,
        "n_excluded": len(protocol.excluded),
        "apply_protocol_exclusion_in": "cyclediag/features/peak_export.py (peak tables only)",
        "lges_extract_sohq": "apply_lges_delta_features: SoHQ for ALL cycles incl RPT",
        "sohq_inflection_input": "detect_sohq_inflections(features) uses full table SoHQ col, no protocol filter",
        "capa_full_107_108": capa.to_dict(orient="records"),
    }

    # Q4-Q7 rpt recovery
    result = analyze_rpt_recovery(feat_all, step, cell_id="M01Ch022", post_window=40)
    blocks = result.blocks_table()
    corrected = apply_recovery_correction(result)
    blocks["Q_rev_fraction"] = blocks.apply(
        lambda r: r["rpt_recovery_amplitude"] / (100 - r["pre_rpt_anchor_sohq"])
        if pd.notna(r["rpt_recovery_amplitude"]) and pd.notna(r["pre_rpt_anchor_sohq"])
        else np.nan,
        axis=1,
    )
    out["Q4"] = blocks.to_dict(orient="records")
    out["Q5"] = blocks[["block_id", "block_end", "Q_rev_fraction", "rpt_recovery_amplitude", "pre_rpt_anchor_sohq"]].to_dict(orient="records")
    out["Q6"] = {
        "overlay_n_points": len(result.overlay_table()),
        "mean_recovery_cycles_to_90pct": None,  # filled below
    }
    ov = result.overlay_table()
    if not ov.empty:
        # cycles until recovery < 10% of A per block
        times = []
        for bid, grp in ov.groupby("block_id"):
            bl = blocks[blocks["block_id"] == bid]
            if bl.empty or pd.isna(bl.iloc[0]["rpt_recovery_amplitude"]):
                continue
            a = bl.iloc[0]["rpt_recovery_amplitude"]
            hit = grp[grp["recovery_component"] < 0.1 * a]
            if not hit.empty:
                times.append(int(hit["rel_cycle"].iloc[0]))
        out["Q6"]["mean_recovery_cycles_to_90pct"] = float(np.mean(times)) if times else None

    out["Q7"] = result.bump_segments.to_dict(orient="records")
    out["Q9"] = {
        "bump_onset_block_id": result.onset.bump_onset_block_id if result.onset else None,
        "bump_onset_cycle": result.onset.bump_onset_cycle if result.onset else None,
        "knee_onset_cycle": result.onset.knee_onset_cycle if result.onset else None,
        "bump_precedes_knee": result.onset.bump_precedes_knee if result.onset else None,
    }

    # Q8 knee sensitivity
    def knee_at(df, col="SoHQ", win=None):
        sub = df[["cycle", col]].dropna()
        sub = sub.rename(columns={col: "SoHQ"})
        if len(sub) < 40:
            return None
        r = detect_sohq_inflections(sub, smooth_window=win, max_breaks=2, method="hybrid", min_seg_points=20)
        if r is None or not r.inflections:
            return None
        return [bp.cycle for bp in r.inflections]

    rout_feat = feat_all[~feat_all["cycle"].isin(protocol.rpt_cycles)].copy()
    corr_rout = corrected[corrected["cycle_role"] == "routine"][["cycle", "SoHQ_corrected"]].rename(columns={"SoHQ_corrected": "SoHQ"})
    anc = result.anchors.dropna(subset=["anchor_sohq"])
    anc_df = anc.rename(columns={"anchor_cycle": "cycle", "anchor_sohq": "SoHQ"})
    wins = [None, 11, 21, 41, 81]
    out["Q8"] = {
        "algorithm": "hybrid: piecewise SSE breakpoints then curvature fallback (sohq_inflection.py:detect_sohq_inflections)",
        "windows": {str(w): knee_at(rout_feat, win=w) for w in wins},
        "corrected_routine": {str(w): knee_at(corr_rout, win=w) for w in wins},
        "anchor_only": knee_at(anc_df, win=11) if len(anc_df) >= 4 else None,
    }

    # Q12 CV on TC50
    g50 = raw[raw["cycle"] == 50]
    chg = g50[pd.to_numeric(g50["current"], errors="coerce") > 1]
    steprow = feat_all[feat_all["cycle"] == 50].iloc[0]
    col_cv = float(pd.to_numeric(chg.get("charge_capacity", chg.get("ChargeCapacity")), errors="coerce").max()) if "charge_capacity" in chg.columns or "ChargeCapacity" in chg.columns else None
    if col_cv and col_cv > 500:
        col_cv = col_cv / 1000
    cv_sig = detect_cv_signal(chg, column_cv_ah=col_cv)
    out["Q12"] = {
        "cycle": 50,
        "raw_ChargeCVCapacity_max_Ah": col_cv,
        "feature_chgCVcapa": float(steprow.get("chgCVcapa", 0)) if "chgCVcapa" in steprow else None,
        "signal_cv_chgCVcapa": cv_sig.chgCVcapa,
        "signal_cv_has_cv": cv_sig.has_cv,
        "signal_cv_method": cv_sig.cv_detect_method,
        "stepemd_chgCV": None,
    }
    if "chgCVcapa" in feat_all.columns:
        out["Q12"]["feature_table_chgCVcapa_tc50"] = float(feat_all.loc[feat_all["cycle"] == 50, "chgCVcapa"].iloc[0])

    # Q13 Q14
    seg_routine = discharge_leg(raw, 50)
    seg_rpt = discharge_leg(raw, 107)  # capa full ~C/3
    out["Q13"] = {"routine_tc50": dqdv_metrics(seg_routine), "rpt_tc107": dqdv_metrics(seg_rpt, sg_window=21)}
    out["Q14"] = noise_uniformity_dqdv_vs_dvdq(seg_routine)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
