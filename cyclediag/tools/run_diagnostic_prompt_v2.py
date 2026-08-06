"""cyclediag diagnostic prompt v2 — Ch22 primary, Ch25 reference. Internal tool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, savgol_filter
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cyclediag.analysis.rpt_recovery import analyze_rpt_recovery, apply_recovery_correction
from cyclediag.analysis.sohq_inflection import detect_sohq_inflections
from cyclediag.features.dcir_decompose import decompose_pulse_cycle, extract_pulse_trace
from cyclediag.features.dqdv_peaks import (
    DqdvPeakConfig,
    compute_dvdq,
    find_dqdv_peaks,
    find_dvdq_peaks,
    prepare_dqdv_arrays,
)
from cyclediag.features.ocv_drift import compute_ocv_drift_table
from cyclediag.features.self_discharge import extract_pre_pulse_rest, fit_self_discharge_rest
from cyclediag.features.signal_cv import detect_cv_signal
from cyclediag.features.stepemd_extract import extract_stepemd_features_table
from cyclediag.io.cycle_protocol import POST_RPT_EXCLUDE, build_protocol_exclusion
from cyclediag.io.cycler_csv import load_cycler_csv
from cyclediag.io.stepemd_csv import load_stepemd_csv
from cyclediag.io.studio_map import studio_column_map

RAW22 = sorted((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*raw.csv"))[0]
STEP22 = sorted((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*stepend.csv"))[0]
RAW25 = ROOT / "example/docs/peak_review/_tmp_raw/00207966_260304_set4_SJ900_45도 0.5C cycle_no1_2_4_[Ch25]__QN_mono_#4_raw.csv"
STEP25 = ROOT / "example/docs/peak_review/_tmp_raw/00207966_260304_set4_SJ900_45도 0.5C cycle_no1_2_4_[Ch25]__QN_mono_#4_stepend.csv"
SUBSET22 = ROOT / "example/output/set4_new/M01Ch022_new_subset.csv"
OUT = ROOT / "example/output/diagnostic_prompt_v2_ch22.json"

DCIR_BLOCKS = [[4, 5, 6], [109, 110, 111], [214, 215, 216], [319, 320, 321], [424, 425, 426], [529, 530, 531]]
SOC_MAP = {80: 0, 50: 1, 20: 2}  # index in block
CAPA_FULL = [3, 108, 213, 318, 423, 528]  # 1st C/3 of each block pair
RPT_BLOCK_MID = [5, 110, 215, 320, 425, 530]  # SOC50 DC-IR cycles


def leg_df(raw: pd.DataFrame, cycle: int, direction: str) -> pd.DataFrame:
    g = raw[raw["cycle"] == cycle].copy()
    cur = pd.to_numeric(g["current"], errors="coerce")
    if direction == "discharge":
        m = cur < -1.0
        cap = "discharge_capacity" if "discharge_capacity" in g.columns else "capacity"
    else:
        m = cur > 1.0
        cap = "charge_capacity" if "charge_capacity" in g.columns else "capacity"
    g = g.loc[m].sort_values("step_time" if "step_time" in g.columns else "time")
    return g, cap


def q_series(seg: pd.DataFrame, cap_col: str) -> np.ndarray:
    Q = pd.to_numeric(seg[cap_col], errors="coerce").to_numpy(float)
    return np.abs(Q - Q[0])


def local_noise(x: np.ndarray, w: int = 15) -> np.ndarray:
    out = np.full(len(x), np.nan)
    for i in range(w, len(x) - w):
        s = slice(i - w, i + w + 1)
        t = np.arange(-w, w + 1)
        p = np.polyfit(t, x[s], 1)
        out[i] = np.std(x[s] - np.polyval(p, t))
    return out


def wiggle_width_v(seg: pd.DataFrame, v_lo: float = 3.55, v_hi: float = 4.05) -> dict:
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    m = (V >= v_lo) & (V <= v_hi)
    if m.sum() < 10:
        return {"width_mV": None}
    vv = V[m]
    # second derivative sign changes as wiggle proxy
    dv = np.gradient(vv) * 1000
    d2 = np.gradient(dv)
    idx, _ = find_peaks(np.abs(d2), prominence=np.nanstd(d2) * 0.5)
    if len(idx) < 2:
        span = (float(vv.max()) - float(vv.min())) * 1000
        return {"width_mV": span, "method": "V_range"}
    span = (float(vv[idx[-1]]) - float(vv[idx[0]])) * 1000
    return {"width_mV": span, "n_inflections": len(idx), "method": "d2_peaks"}


def peak_table_dqdv_dvdq(seg: pd.DataFrame, cap_col: str, cfg: DqdvPeakConfig) -> dict:
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    Q = q_series(seg, cap_col)
    dqdv_peaks = find_dqdv_peaks(V, Q, config=cfg)
    dvdq_peaks = find_dvdq_peaks(Q, V, config=cfg)
    vx, dqdv, qx, dvdq = prepare_dqdv_arrays(V, Q, cfg)
    # valleys in dV/dQ (graphite stages) = peaks in -dV/dQ
    neg = -np.asarray(dvdq, float)
    y_s = savgol_filter(np.nan_to_num(neg), min(cfg.sg_window, len(neg) // 2 * 2 - 1), cfg.sg_poly) if len(neg) > cfg.sg_window else neg
    prom = 0.02 * max(float(np.nanmax(np.abs(y_s))), 1e-9)
    v_idx, v_props = find_peaks(y_s, prominence=prom, distance=max(5, int(cfg.n_interp * cfg.min_distance_frac)))
    valleys = []
    for i in v_idx:
        if vx[i] < 3.4 or vx[i] > 4.05:
            continue
        hw = v_props.get("widths", [np.nan])[list(v_idx).index(i)] if "widths" in v_props else np.nan
        valleys.append({
            "V": float(vx[i]),
            "Q": float(qx[i]),
            "H_neg_dvdq": float(y_s[i]),
            "width_pts": float(hw) if np.isfinite(hw) else None,
        })
    valleys.sort(key=lambda p: p["V"])
    # FWHM in mV for dQ/dV peaks in high-V
    hi_dqdv = [p for p in dqdv_peaks if p.get("V", 0) >= 3.5]
    hi_dqdv.sort(key=lambda p: p["V"])
    rows = []
    for j, p in enumerate(hi_dqdv, 1):
        i = int(np.argmin(np.abs(vx - p["V"])))
        half = abs(p["H"]) / 2
        left = right = i
        y = np.abs(dqdv)
        while left > 0 and y[left] > half:
            left -= 1
        while right < len(y) - 1 and y[right] > half:
            right += 1
        fwhm_mV = float(vx[right] - vx[left]) * 1000 if right > left else None
        rows.append({
            "idx": j,
            "V": p["V"],
            "Q": float(qx[i]) if i < len(qx) else None,
            "H_dqdv": p["H"],
            "fwhm_mV": fwhm_mV,
            "leg": "discharge",
        })
    return {
        "dqdv_highV_peaks": rows,
        "dvdq_highV_valleys_neg": valleys,
        "n_dqdv_total": len(dqdv_peaks),
        "n_dvdq_peaks": len(dvdq_peaks),
    }


def c_gr_from_features(peaks_info: dict, total_ah: float) -> dict:
    valleys = peaks_info.get("dvdq_highV_valleys_neg", [])
    if len(valleys) < 2:
        qs = [p["Q"] for p in peaks_info.get("dqdv_highV_peaks", []) if p.get("Q")]
        if len(qs) >= 2:
            gaps = [qs[i + 1] - qs[i] for i in range(len(qs) - 1)]
            c_gr = float(max(gaps)) if gaps else None
            src = "dqdv_peak_Q_gaps"
        else:
            return {"C_Gr_Ah": None, "source": "insufficient_features"}
    else:
        qs = [v["Q"] for v in valleys]
        gaps = [qs[i + 1] - qs[i] for i in range(len(qs) - 1)]
        c_gr = float(max(gaps))
        src = "dvdq_valley_Q_gaps_max"
    pct = 100.0 * c_gr / total_ah if c_gr and total_ah > 0 else None
    return {"C_Gr_Ah": c_gr, "C_Gr_pct": pct, "n_features": len(valleys) or len(peaks_info.get("dqdv_highV_peaks", [])), "source": src}


def effective_smooth_mV(seg: pd.DataFrame, cap_col: str, sg_window: int) -> dict:
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    Q = q_series(seg, cap_col)
    cfg = DqdvPeakConfig(n_interp=500, sg_window=sg_window, sg_poly=3)
    vx, _, qx, vs_arr = prepare_dqdv_arrays(V, Q, cfg)
    if len(vx) < 5:
        return {"effective_smooth_mV": None}
    vs = savgol_filter(vx, min(sg_window, len(vx) // 2 * 2 - 1), 3)
    mv = float(np.median(np.abs(np.diff(vs))) * 1000)
    return {"effective_smooth_mV": mv * sg_window, "mv_per_point": mv}


def fit_sd_cov(t, v):
    def _f(x, vinf, c1, tau1, c2, tau2, k):
        return vinf - c1 * np.exp(-x / max(tau1, 1.0)) - c2 * np.exp(-x / max(tau2, 10.0)) - k * x

    vinf0 = float(v[-1])
    p0 = (vinf0, 0.01, 100.0, 0.01, 800.0, 1e-8)
    popt, pcov = curve_fit(
        _f, t, v, p0=p0, maxfev=12000,
        bounds=([vinf0 - 0.5, 0.0, 1.0, 0.0, 10.0, -1e-5], [vinf0 + 0.5, 1.0, 2000.0, 1.0, 5000.0, 1e-5]),
    )
    corr = np.zeros((6, 6))
    if pcov is not None and np.all(np.isfinite(pcov)):
        d = np.sqrt(np.diag(pcov))
        with np.errstate(divide="ignore", invalid="ignore"):
            corr = pcov / np.outer(d, d)
    late = (t >= 1800) & (t <= 3600)
    b = np.polyfit(t[late], v[late], 1)[0] if late.sum() >= 10 else None
    return {
        "corr_c2_k": float(corr[3, 5]),
        "tau2_s": float(popt[4]),
        "drift_biexp_mV_h": abs(float(popt[5])) * 3600 * 1000,
        "drift_late_mV_h": abs(float(b)) * 3600 * 1000 if b is not None else None,
        "k_V_per_s": float(popt[5]),
    }


def per_soc_dqdv(raw, cycle: int, soc_pct: float, cfg: DqdvPeakConfig) -> float | None:
    """dQ/dV magnitude at rest voltage ~ from local discharge curve at that SOC."""
    seg, cap = leg_df(raw, cycle, "discharge")
    if seg.empty:
        return None
    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    Q = q_series(seg, cap)
    total = float(Q[-1])
    q_target = total * soc_pct / 100.0
    vx, dqdv, qx, _ = prepare_dqdv_arrays(V, Q, cfg)
    if len(vx) < 5:
        return None
    i = int(np.argmin(np.abs(qx - q_target)))
    return float(abs(dqdv[i])) if np.isfinite(dqdv[i]) else None


def sqrt_t_slopes(cycle_df, i_exp=77.0) -> dict:
    ex = extract_pulse_trace(cycle_df, expected_pulse_current=i_exp)
    if ex is None:
        return {}
    t, v, _, i_med, v0 = ex
    r = np.abs(v0 - v) / max(abs(i_med), 1e-9) * 1000.0

    def slope(t0, t1):
        m = (t >= t0) & (t <= t1)
        if m.sum() < 4:
            return None, None
        x = np.sqrt(t[m])
        y = r[m]
        c = np.polyfit(x, y, 1)
        yh = np.polyval(c, x)
        r2 = 1 - np.sum((y - yh) ** 2) / max(np.sum((y - np.mean(y)) ** 2), 1e-12)
        return float(c[0]), float(r2)

    a1, r1 = slope(1, 10)
    a2, r2 = slope(10, 30)
    fit = decompose_pulse_cycle(cycle_df, expected_pulse_current=i_exp)
    return {
        "A_1_10": a1,
        "R2_1_10": r1,
        "A_10_30": a2,
        "R2_10_30": a2 and r2,
        "A_split_ratio": (a1 / a2) if a1 and a2 and a2 != 0 else None,
        "R_ohmic": fit.R_ohmic,
        "R_ct": fit.R_ct,
        "tau_ct": fit.tau_ct,
        "A_diff": fit.A_diff,
        "R_30s_total": fit.R_30s_total,
        "fit_cond": getattr(fit, "fit_condition_number", None),
    }


def param_sweep(seg, cap_col) -> list[dict]:
    rows = []
    for n in [500, 1500, 3000]:
        for sw in [7, 11, 21, 31]:
            for mdv in [0.012, 0.006, 0.003]:
                for mdf in [0.04, 0.015]:
                    cfg = DqdvPeakConfig(n_interp=n, sg_window=sw, merge_v_sep_v=mdv, min_distance_frac=mdf)
                    V = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
                    Q = q_series(seg, cap_col)
                    np_r = len(find_dqdv_peaks(V, Q, config=cfg))
                    sm = effective_smooth_mV(seg, cap_col, sw)
                    rows.append({
                        "n_interp": n, "sg_window": sw, "merge_dv": mdv, "min_dist_frac": mdf,
                        "n_peaks": np_r,
                        "eff_smooth_mV": sm.get("effective_smooth_mV"),
                    })
    return rows


def main():
    raw = load_cycler_csv(str(RAW22), column_map=studio_column_map())
    step = load_stepemd_csv(STEP22)
    feat = extract_stepemd_features_table(step_df=step, path=STEP22)
    subset = pd.read_csv(SUBSET22)
    protocol = build_protocol_exclusion(step)
    cfg = DqdvPeakConfig(n_interp=500, sg_window=21, sg_poly=3, merge_v_sep_v=0.012)

    out: dict = {"raw": str(RAW22), "date": "2026-08-05"}

    # §1 correction: capa_full C/3 is cycles 2-3 BOL, not RPT block 4-6
    out["background_corrections"] = [
        "§1.3 'RPT C/3' for dQ/dV: BOL capa_full cycles are 2-3 (i≈25.78A), NOT block 4-6 (DC-IR+rpt+capacheck)",
        "Design graphite % for Ch22/Ch25: not in repo → UNKNOWN",
        "raw_meta source_sch: null → CV cutoff UNKNOWN",
    ]

    # Q1 — BOL capa_full cycle 3 discharge + charge
    seg3, cap3 = leg_df(raw, 3, "discharge")
    seg3c, cap3c = leg_df(raw, 3, "charge")
    wiggle = wiggle_width_v(seg3)
    pk_dis = peak_table_dqdv_dvdq(seg3, cap3, cfg)
    pk_chg = peak_table_dqdv_dvdq(seg3c, cap3c, cfg)
    out["Q1"] = {
        "cycle": 3,
        "protocol": "capa_full C/3",
        "wiggle_raw_mV": wiggle,
        "discharge": pk_dis,
        "charge_highV_dqdv": [p for p in pk_chg["dqdv_highV_peaks"]],
        "charge_n_dqdv_total": pk_chg["n_dqdv_total"],
    }

    # Q2
    total3 = float(q_series(seg3, cap3)[-1])
    cgr3 = c_gr_from_features(pk_dis, total3)
    out["Q2"] = {
        "total_Ah": total3,
        "measurement": cgr3,
        "design_graphite_pct": "UNKNOWN",
        "Q_gaps_Ah": None,
    }
    valleys = pk_dis.get("dvdq_highV_valleys_neg", [])
    if len(valleys) >= 2:
        qs = [v["Q"] for v in valleys]
        gaps = [qs[i + 1] - qs[i] for i in range(len(qs) - 1)]
        out["Q2"]["Q_gaps_Ah"] = gaps
        out["Q2"]["Q_gaps_pct"] = [100 * g / total3 for g in gaps]

    # Q3 — all capa_full cycles
    q3_rows = []
    for bi, cyc in enumerate(CAPA_FULL):
        seg, cap = leg_df(raw, cyc, "discharge")
        if seg.empty:
            continue
        pk = peak_table_dqdv_dvdq(seg, cap, cfg)
        tot = float(q_series(seg, cap)[-1])
        cgr = c_gr_from_features(pk, tot)
        # RPT pair reproducibility
        cyc2 = cyc + 1
        seg2, cap2 = leg_df(raw, cyc2, "discharge")
        cgr2 = c_gr_from_features(peak_table_dqdv_dvdq(seg2, cap2, cfg), float(q_series(seg2, cap2)[-1])) if not seg2.empty else {}
        q3_rows.append({
            "block": bi + 1,
            "cycle": cyc,
            "cycle_pair": cyc2,
            "total_Ah": tot,
            **cgr,
            "C_Si_Ah": (tot - cgr["C_Gr_Ah"]) if cgr.get("C_Gr_Ah") else None,
            "C_Gr_pair_delta_Ah": abs((cgr.get("C_Gr_Ah") or 0) - (cgr2.get("C_Gr_Ah") or 0)) if cgr.get("C_Gr_Ah") and cgr2.get("C_Gr_Ah") else None,
        })
    out["Q3"] = q3_rows

    # Q4 — hyst_area regions BOL/mid/late routine
    rout_cycles = [50, 320, 530]
    q4 = []
    for c in rout_cycles:
        row = subset[subset["cycle"] == c]
        if row.empty:
            continue
        r = row.iloc[0]
        q4.append({
            "cycle": c,
            "hyst_area": r.get("hyst_area"),
            "hyst_area_low": r.get("hyst_area_low"),
            "hyst_area_mid": r.get("hyst_area_mid"),
            "hyst_area_high": r.get("hyst_area_high"),
            "hyst_frac_high": r.get("hyst_frac_high"),
            "dchg_dVdQ_SOC0": r.get("dchg_dVdQ_SOC0"),
            "dchg_dVdQ_SOCmid": r.get("dchg_dVdQ_SOCmid"),
            "self_discharge_soc80": r.get("self_discharge_rate_soc80"),
            "R_ohmic_soc50": r.get("R_ohmic_soc50"),
        })
    out["Q4"] = q4

    # Q5
    out["Q5"] = {
        "Ch22_in_repo": True,
        "Ch25_in_repo": RAW25.exists(),
        "graphite_group_Ch22": "UNKNOWN",
        "graphite_group_Ch25": "UNKNOWN",
        "set4_cells_in_repo": ["M01Ch022", "M01Ch025"],
        "design_diff_beyond_graphite": "UNKNOWN",
    }

    # Q8 — per-SOC dQ/dV and I_leak (block 1 rests from cycles 4,5,6)
    q8 = []
    for soc, cyc in [(80, 4), (50, 5), (20, 6)]:
        g = raw[raw["cycle"] == cyc]
        pair = extract_pre_pulse_rest(g, expected_pulse_current=77.0)
        dqdv = per_soc_dqdv(raw, cyc, soc, cfg)  # approximate from same-cycle partial D
        if pair is None:
            continue
        t, v = pair
        sd = fit_sd_cov(t, v)
        sd_main = fit_self_discharge_rest(t, v)
        k = sd["k_V_per_s"]
        i_leak = abs(k) / dqdv if dqdv and dqdv > 1e-9 else None
        q8.append({
            "SOC": soc,
            "cycle": cyc,
            "dQdV_Ah_per_V": dqdv,
            "drift_mV_h": sd_main.get("self_discharge_rate"),
            "I_leak_uA": i_leak * 1e6 if i_leak else None,
        })
    out["Q8"] = q8

    # Q9 — all blocks × SOC
    q9 = []
    for bi, block in enumerate(DCIR_BLOCKS):
        for soc, idx in [(80, 0), (50, 1), (20, 2)]:
            cyc = block[idx]
            g = raw[raw["cycle"] == cyc]
            pair = extract_pre_pulse_rest(g, expected_pulse_current=77.0)
            if pair is None:
                continue
            t, v = pair
            sd = fit_sd_cov(t, v)
            q9.append({"block": bi + 1, "SOC": soc, "cycle": cyc, **sd, "match": abs(sd["drift_biexp_mV_h"] - sd["drift_late_mV_h"]) / max(sd["drift_late_mV_h"], 1e-9) < 0.3 if sd["drift_late_mV_h"] else None})
    out["Q9"] = q9

    # Q10 — drift SOC profile vs Gr feature SOC
    gr_soc = None
    if valleys:
        q_mid = np.mean([v["Q"] for v in valleys])
        gr_soc = 100.0 * q_mid / total3
    sd_prof = {80: None, 50: None, 20: None}
    for row in q8:
        sd_prof[row["SOC"]] = row["drift_mV_h"]
    out["Q10"] = {"Gr_feature_SOC_pct_est": gr_soc, "drift_mV_h_by_SOC": sd_prof, "max_at_Gr_boundary": None}
    if gr_soc and all(sd_prof.values()):
        # closest SOC to gr_soc among 20/50/80
        keys = [20, 50, 80]
        closest = min(keys, key=lambda s: abs(s - gr_soc))
        out["Q10"]["closest_SOC_to_Gr"] = closest
        out["Q10"]["max_drift_SOC"] = max(sd_prof, key=lambda s: sd_prof[s])

    # Q11 — rest drift vs RPT bump
    rpt_res = analyze_rpt_recovery(feat, step, cell_id="M01Ch022")
    blocks_df = rpt_res.blocks_table()
    ocv = compute_ocv_drift_table(DCIR_BLOCKS, raw, expected_pulse_current=77.0)
    drift_block = []
    for bi, block in enumerate(DCIR_BLOCKS):
        c80 = block[0]
        g = raw[raw["cycle"] == c80]
        pair = extract_pre_pulse_rest(g, expected_pulse_current=77.0)
        d = None
        if pair:
            d = fit_self_discharge_rest(pair[0], pair[1]).get("self_discharge_rate")
        bl = blocks_df[blocks_df["block_id"] == bi + 1]
        amp = float(bl.iloc[0]["rpt_recovery_amplitude"]) if not bl.empty and pd.notna(bl.iloc[0].get("rpt_recovery_amplitude")) else None
        drift_block.append({"block": bi + 1, "sd80_mV_h": d, "rpt_amp_pct": amp})
    df11 = pd.DataFrame(drift_block).dropna(subset=["sd80_mV_h", "rpt_amp_pct"])
    if len(df11) >= 3:
        r11, p11 = pearsonr(df11["sd80_mV_h"], df11["rpt_amp_pct"])
    else:
        r11 = p11 = None
    out["Q11"] = {"table": drift_block, "pearson_r": r11, "p": p11, "n": len(df11)}

    # Q12
    q12 = {}
    for c in [5, 320, 530]:
        q12[c] = sqrt_t_slopes(raw[raw["cycle"] == c])
    out["Q12"] = q12

    # Q13 — parallel_shift vs proxies
    rout = feat[(feat["cycle"] >= 12) & (~feat["cycle"].isin(protocol.excluded))].copy()
    # build block-level proxies from DC-IR SOC50 routine-adjacent
    ocv_tbl = ocv.merge(
        pd.DataFrame([{"block_start_cycle": b[0], "cycle_soc50": b[1]} for b in DCIR_BLOCKS]),
        left_on="block_start_cycle",
        right_on="block_start_cycle",
    )
    proxies = []
    for _, row in ocv_tbl.iterrows():
        c50 = int(row["cycle_soc50"])
        fr = feat[feat["cycle"] == c50]
        if fr.empty:
            # use subset
            fr = subset[subset["cycle"] == c50]
        if fr.empty:
            continue
        fr = fr.iloc[0]
        proxies.append({
            "block": int(row["block_id"]),
            "parallel_shift": row.get("ocv_parallel_shift"),
            "EoC_restV_relax": fr.get("EoC_restV_relax"),
            "chgCVcapa": fr.get("chgCVcapa"),
            "R_30s_soc50": fr.get("R_30s_total_soc50"),
        })
    pdf = pd.DataFrame(proxies).dropna(subset=["parallel_shift"])
    q13 = {"n": len(pdf), "detection_limit_r_n6": 0.81, "correlations": {}}
    for col in ["EoC_restV_relax", "chgCVcapa", "R_30s_soc50"]:
        sub = pdf.dropna(subset=[col, "parallel_shift"])
        if len(sub) >= 3:
            r, p = pearsonr(sub["parallel_shift"], sub[col])
            q13["correlations"][col] = {"r": float(r), "p": float(p), "n": len(sub)}
        else:
            q13["correlations"][col] = {"r": None, "p": None, "n": len(sub)}
    q13["table"] = proxies
    out["Q13"] = q13

    # Q14 — C_PE from cathode charge peaks cycle 3
    cpe_q = []
    for c in CAPA_FULL[:3]:
        seg, cap = leg_df(raw, c, "charge")
        pk = peak_table_dqdv_dvdq(seg, cap, cfg)
        peaks = pk["dqdv_highV_peaks"]
        if len(peaks) >= 2:
            qs = sorted([p["Q"] for p in peaks if p.get("Q")])
            gaps = [qs[i + 1] - qs[i] for i in range(len(qs) - 1)]
            cpe_q.append({"cycle": c, "C_PE_gap_max_Ah": max(gaps), "n_peaks": len(peaks)})
    out["Q14"] = {"C_PE_estimates": cpe_q, "observables": 2, "unknowns": 4, "determined_after_fix": "PARTIAL — fixing C_PE and C_Gr leaves C_Si+offset underdetermined (2 obs, 2 unknowns)"}

    # Q15-Q18 dQ/dV quality
    seg50, cap50 = leg_df(raw, 50, "discharge")
    w50 = wiggle_width_v(seg50, 3.55, 4.05)
    sm_routine = effective_smooth_mV(seg50, cap50, 21)
    sm_rpt, cap_rpt = leg_df(raw, 3, "discharge")
    sm_rpt_m = effective_smooth_mV(sm_rpt, cap_rpt, 21)
    out["Q15"] = {
        "routine_tc50_wiggle_mV": w50.get("width_mV"),
        "routine_eff_smooth_mV": sm_routine.get("effective_smooth_mV"),
        "rpt_tc3_eff_smooth_mV": sm_rpt_m.get("effective_smooth_mV"),
        "filter_erases_feature": (sm_routine.get("effective_smooth_mV") or 0) > (w50.get("width_mV") or 999),
    }

    V50 = pd.to_numeric(seg50["voltage"], errors="coerce").to_numpy(float)
    sig = local_noise(V50) * 1000
    dV = np.abs(np.gradient(V50)) * 1000
    df_n = pd.DataFrame({"V": V50, "sigma_mV": sig, "dV_mV": dV}).dropna()
    df_n["bin"] = pd.cut(df_n["V"], 5)
    q16_tab = df_n.groupby("bin", observed=True).agg(sigma=("sigma_mV", "median"), dV=("dV_mV", "median")).assign(ratio=lambda x: x["sigma"] / x["dV"])
    out["Q16"] = {str(k): v for k, v in q16_tab.to_dict("index").items()}
    out["Q16_ratio_max_min"] = float(q16_tab["ratio"].max() / q16_tab["ratio"].min()) if q16_tab["ratio"].min() > 0 else None

    d = np.abs(np.diff(V50))
    d = d[d > 0]
    out["Q17"] = {
        "routine_min_dV": float(d.min()) if len(d) else None,
        "unique_small": np.unique(np.round(d[d < 0.02], 6))[:15].tolist(),
    }
    pulse = raw[(raw["cycle"] == 5) & (pd.to_numeric(raw["current"], errors="coerce").abs() > 50)]
    Vp = pd.to_numeric(pulse["voltage"], errors="coerce").to_numpy(float)
    dp = np.abs(np.diff(Vp))
    dp = dp[dp > 0]
    out["Q17"]["pulse_min_dV"] = float(dp.min()) if len(dp) else None

    # Q18 subset sweep — routine vs rpt counts at default-ish combos
    sweep = param_sweep(seg50, cap50)
    sweep_rpt = param_sweep(sm_rpt, cap_rpt)
    best_rout = max(sweep, key=lambda r: r["n_peaks"])
    best_rpt = max(sweep_rpt, key=lambda r: r["n_peaks"])
    out["Q18"] = {
        "routine_max_peaks": best_rout,
        "rpt_max_peaks": best_rpt,
        "routine_never_reaches_rpt_peak_count": best_rout["n_peaks"] < best_rpt["n_peaks"],
        "recommended_for_Q1": {"sg_window": 11, "merge_dv": 0.006, "n_interp": 1500},
    }

    # Q19 POST_RPT
    out["Q19"] = {
        "POST_RPT_EXCLUDE": POST_RPT_EXCLUDE,
        "defined_in": "cyclediag/io/cycle_protocol.py:23",
        "applied_in": "build_protocol_exclusion → peak_export protocol_excluded flag; NOT applied in lges_extract SoHQ",
        "sohq_inflection": "detect_sohq_inflections uses full feat SoHQ without protocol filter",
        "rpt_rows_have_sohq": int(feat[feat["cycle"].isin(protocol.rpt_cycles)]["SoHQ"].notna().sum()),
    }

    # Q20 RPT bump
    out["Q20"] = blocks_df[["block_id", "block_start", "rpt_recovery_amplitude", "rpt_recovery_decay_cycles", "fit_r2", "pre_rpt_anchor_sohq", "bump_significant"]].to_dict(orient="records")

    # Q21 bump contamination
    q21 = []
    for bi, block in enumerate(DCIR_BLOCKS):
        start = block[0]
        end = block[-1] + POST_RPT_EXCLUDE + 15
        seg = rout[(rout["cycle"] >= start) & (rout["cycle"] <= min(end, rout["cycle"].max()))]
        if len(seg) < 5:
            continue
        within = np.polyfit(seg["cycle"], seg["SoHQ"], 1)[0]
        q21.append({"block": bi + 1, "fade_within": float(within), "n_pts": len(seg)})
    anchors = rpt_res.anchors.dropna(subset=["anchor_sohq"])
    if len(anchors) >= 2:
        b2b = np.polyfit(anchors["anchor_cycle"], anchors["anchor_sohq"], 1)[0]
    else:
        b2b = None
    for row in q21:
        row["fade_block_to_block"] = b2b
        row["bump_contamination"] = (row["fade_within"] / b2b - 1) if b2b and b2b != 0 else None
    out["Q21"] = q21

    # Q22 chgCVcapa
    g50 = raw[raw["cycle"] == 50]
    chg = g50[pd.to_numeric(g50["current"], errors="coerce") > 1]
    cv_col = None
    for cn in ("ChargeCVCapacity", "charge_capacity"):
        if cn in chg.columns:
            cv_col = float(pd.to_numeric(chg[cn], errors="coerce").max())
            break
    cv_sig = detect_cv_signal(chg, column_cv_ah=cv_col)
    ste = feat[feat["cycle"] == 50].iloc[0]
    out["Q22"] = {
        "feature_chgCVcapa_tc50": float(ste.get("chgCVcapa", 0)),
        "signal_cv_chgCVcapa": cv_sig.chgCVcapa,
        "signal_has_cv": cv_sig.has_cv,
        "cv_detect_method": cv_sig.cv_detect_method,
        "subset_chgCVcapa_tc3": float(subset.loc[subset["cycle"] == 3, "chgCVcapa"].iloc[0]) if (subset["cycle"] == 3).any() else None,
    }

    # Q23
    out["Q23"] = {"export_pcov": "NOT in fit_self_discharge_rest", "proposed_gate": "|corr(c2,k)|>0.9 or tau2>1200s → valid=False", "rename": "rest_voltage_drift_rate"}

    # Q24
    meta = json.loads(RAW22.with_name(RAW22.name.replace("_raw.csv", "_raw_meta.json")).read_text(encoding="utf-8"))
    out["Q24"] = {"source_sch": meta.get("source_sch"), "cv_cutoff": "UNKNOWN", "temp_all_zero": True}

    # Q25 external
    out["Q25"] = {k: "UNKNOWN" for k in ["stack_pressure", "temperature_log", "Si_pct", "design_diff_30_50", "design_capacity_mismatch", "post_mortem", "fast_charge_cells", "decision_use", "protocol_budget"]}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
