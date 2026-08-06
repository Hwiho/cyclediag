"""Cross-checks for A_diff, self-discharge, OCV drift — Ch22 set4.

Usage:
  python -m cyclediag.tools.validate_assb_metrics
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cyclediag.features.dcir_decompose import decompose_pulse_cycle, extract_pulse_trace
from cyclediag.features.ocv_drift import compute_ocv_drift_table
from cyclediag.features.self_discharge import extract_pre_pulse_rest, fit_self_discharge_rest
from cyclediag.io.cycler_csv import load_cycler_csv
from cyclediag.io.stepemd_csv import load_stepemd_csv
from cyclediag.io.studio_map import studio_column_map

RAW = sorted((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*raw.csv"))[0]
STEP = sorted((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*stepend.csv"))[0]
OUT = ROOT / "example/output/set4_new/metrics_validation_ch22.json"

DCIR_BLOCKS = [[4, 5, 6], [109, 110, 111], [214, 215, 216], [319, 320, 321], [424, 425, 426], [529, 530, 531]]
SOC_CYCLES = {80: 4, 50: 5, 20: 6}  # first block mapping


def fit_sd_with_cov(t, v):
    def _f(x, vinf, c1, tau1, c2, tau2, k):
        return vinf - c1 * np.exp(-x / max(tau1, 1.0)) - c2 * np.exp(-x / max(tau2, 10.0)) - k * x

    vinf0 = float(v[-1])
    p0 = (vinf0, 0.01, 100.0, 0.01, 800.0, 1e-8)
    popt, pcov = curve_fit(
        _f, t, v, p0=p0, maxfev=12000,
        bounds=([vinf0 - 0.5, 0.0, 1.0, 0.0, 10.0, -1e-5], [vinf0 + 0.5, 1.0, 2000.0, 1.0, 5000.0, 1e-5]),
    )
    names = ["vinf", "c1", "tau1", "c2", "tau2", "k"]
    corr = np.zeros((6, 6))
    if pcov is not None and np.all(np.isfinite(pcov)):
        d = np.sqrt(np.diag(pcov))
        with np.errstate(divide="ignore", invalid="ignore"):
            corr = pcov / np.outer(d, d)
    late = (t >= 1800) & (t <= 3600)
    b_late = np.polyfit(t[late], v[late], 1)[0] if late.sum() >= 10 else None
    return {
        "params": dict(zip(names, map(float, popt))),
        "corr_c2_k": float(corr[3, 5]) if np.isfinite(corr[3, 5]) else None,
        "tau2_s": float(popt[4]),
        "k_V_per_s": float(popt[5]),
        "sd_rate_mV_h": abs(float(popt[5])) * 3600 * 1000,
        "late_linear_mV_h": abs(float(b_late)) * 3600 * 1000 if b_late is not None else None,
        "identifiable": abs(corr[3, 5]) < 0.9 if np.isfinite(corr[3, 5]) else False,
        "tau2_ok": float(popt[4]) < 1200.0,
    }


def sqrt_t_linearity(cycle_df) -> dict:
    ex = extract_pulse_trace(cycle_df, expected_pulse_current=77.0)
    if ex is None:
        return {"ok": False}
    t, v, _, i_med, v0 = ex
    r = np.abs(v0 - v) / max(abs(i_med), 1e-9) * 1000.0
    late = (t >= 10) & (t <= 30)
    if late.sum() < 5:
        return {"ok": False}
    x = np.sqrt(t[late])
    y = r[late]
    coef = np.polyfit(x, y, 1)
    yhat = np.polyval(coef, x)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    return {
        "A_diff_mohm_per_sqrt_s": float(coef[0]),
        "R2_10_30s": r2,
        "sqrt_t_valid": r2 is not None and r2 > 0.95,
    }


def main():
    raw = load_cycler_csv(str(RAW), column_map=studio_column_map())
    step = load_stepemd_csv(STEP)

    # 1) self-discharge identifiability per SOC (block 1)
    sd_rows = []
    for soc, cyc in SOC_CYCLES.items():
        g = raw[raw["cycle"] == cyc]
        pair = extract_pre_pulse_rest(g, expected_pulse_current=77.0)
        if pair is None:
            continue
        t, v = pair
        fit = fit_sd_with_cov(t, v)
        fit["soc"] = soc
        fit["cycle"] = cyc
        # rough I_leak: k * C_eff; use ~50 Ah cell, dV/dOCV ~0.05 V per 1% SOC rough at mid -> 2.5V span/100
        k = fit["k_V_per_s"]
        dqdv_v_per_ah = 0.035  # placeholder; replace with measured dV/dQ
        i_leak_a = abs(k) / dqdv_v_per_ah if dqdv_v_per_ah > 0 else None
        fit["I_leak_A_rough"] = i_leak_a
        sd_rows.append(fit)

    # 2) OCV parallel shift vs R30
    ocv = compute_ocv_drift_table(DCIR_BLOCKS, raw, expected_pulse_current=77.0)
    dcir = []
    for block in DCIR_BLOCKS:
        c50 = block[1]
        fit = decompose_pulse_cycle(raw[raw["cycle"] == c50], expected_pulse_current=77.0)
        dcir.append({"block_start_cycle": block[0], "R_30s_soc50": fit.R_30s_total})
    ddf = ocv.merge(pd.DataFrame(dcir), on="block_start_cycle", how="left")
    if len(ddf) > 3:
        r_par, p_par = pearsonr(ddf["ocv_parallel_shift"], ddf["R_30s_soc50"])
        r_sp, p_sp = pearsonr(ddf["delta_ocv_spread_20_80"], ddf["R_30s_soc50"])
    else:
        r_par = p_par = r_sp = p_sp = None

    # 3) sqrt-t for SOC50 cycles across life
    sqrt_rows = []
    for block in DCIR_BLOCKS:
        c50 = block[1]
        row = sqrt_t_linearity(raw[raw["cycle"] == c50])
        row["cycle"] = c50
        sqrt_rows.append(row)

    out = {
        "self_discharge_identifiability": sd_rows,
        "ocv_shift_vs_R30": {
            "pearson_parallel_shift_vs_R30": r_par,
            "p_parallel": p_par,
            "pearson_delta_spread_vs_R30": r_sp,
            "p_spread": p_sp,
            "table": ddf[["block_id", "block_start_cycle", "ocv_parallel_shift", "delta_ocv_spread_20_80", "R_30s_soc50"]].to_dict(orient="records"),
        },
        "sqrt_t_linearity_soc50": sqrt_rows,
        "notes": [
            "corr(c2,k)|>0.9 => biexp-linear k not identifiable",
            "tau2>1200s => downgrade self_discharge_rate",
            "parallel_shift correlated with R30 => kinetic early-termination confound",
            "I_leak uses rough dV/dQ placeholder until per-SOC slope wired",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
