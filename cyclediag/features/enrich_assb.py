"""Post-extract enrichment for ASSB / roadmap §9.1–§9.2 full-cell metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cyclediag.features.curve_fit import attach_curve_fit
from cyclediag.features.fade_trajectory import attach_fade_trajectory
from cyclediag.features.dcir_decompose import (
    decompose_pulse_cycle,
    result_to_dict,
    soc_ratio_features,
)
from cyclediag.features.dqv_stats import attach_dqv_stats
from cyclediag.features.ocv_drift import attach_ocv_drift_to_features
from cyclediag.features.overpotential import (
    compute_eta_for_pair,
    nearest_routine_after_rpt,
)
from cyclediag.features.quality import cycle_quality_metrics
from cyclediag.features.rpt_metrics import (
    Q_RELAX_NOISE_FLOOR_PCT,
    attach_per,
    attach_rcf,
)
from cyclediag.features.self_discharge import self_discharge_for_cycle

_SOC_ORDER = (80, 50, 20)
POST_RPT_EXCLUDE = 5


def _find_pulse_cycles(
    raw_df: pd.DataFrame,
    *,
    expected_pulse_current: float,
) -> list[int]:
    out: list[int] = []
    for cyc, g in raw_df.groupby("cycle"):
        i = pd.to_numeric(g.get("current"), errors="coerce")
        if i is None or i.isna().all():
            continue
        if float(i.abs().max()) >= 0.5 * expected_pulse_current:
            out.append(int(cyc))
    return sorted(set(out))


def _group_consecutive(cycles: list[int], *, min_len: int = 1) -> list[list[int]]:
    if not cycles:
        return []
    blocks: list[list[int]] = []
    cur = [cycles[0]]
    for c in cycles[1:]:
        if c == cur[-1] + 1:
            cur.append(c)
        else:
            if len(cur) >= min_len:
                blocks.append(cur)
            cur = [c]
    if len(cur) >= min_len:
        blocks.append(cur)
    return blocks


def _q(row: pd.Series) -> float | None:
    for col in ("dchgCapa", "dchg_capa"):
        if col in row.index and pd.notna(row[col]):
            try:
                v = float(row[col])
            except (TypeError, ValueError):
                continue
            if np.isfinite(v):
                return v
    return None


def attach_q_relax_from_dcir_blocks(
    features: pd.DataFrame,
    dcir_blocks: list[list[int]],
    *,
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT,
) -> pd.DataFrame:
    """Q_relax from the two high-Q cycles immediately before each DC-IR block."""
    out = features.copy()
    for col in ("Q_relax", "Q_relax_pct", "Q_relax_significant"):
        if col not in out.columns:
            out[col] = np.nan if col != "Q_relax_significant" else None
    by = {int(r.cycle): r for r in out.itertuples()}
    for block in dcir_blocks:
        if not block:
            continue
        start = int(block[0])
        c1, c2 = start - 2, start - 1
        if c1 not in by or c2 not in by:
            continue
        q1, q2 = _q(pd.Series(by[c1]._asdict())), _q(pd.Series(by[c2]._asdict()))
        if q1 is None or q2 is None or q2 == 0:
            continue
        if min(q1, q2) < 10:
            continue
        q_relax = q2 - q1
        q_relax_pct = q_relax / q2 * 100.0
        for c in (c1, c2):
            mask = out["cycle"] == c
            out.loc[mask, "Q_relax"] = q_relax
            out.loc[mask, "Q_relax_pct"] = q_relax_pct
            out.loc[mask, "Q_relax_significant"] = abs(q_relax_pct) > noise_floor_pct
    return out


def first_capa_baseline(features: pd.DataFrame, dcir_blocks: list[list[int]]) -> int | None:
    """First post-formation capa cycle2 (before first DC-IR)."""
    if not dcir_blocks:
        return None
    start = int(dcir_blocks[0][0])
    c2 = start - 1
    if (features["cycle"] == c2).any():
        return c2
    return None


def _set_cell(out: pd.DataFrame, mask, col: str, val) -> None:
    if col not in out.columns:
        out[col] = pd.Series([None] * len(out), dtype=object)
    if out[col].dtype != object and not (
        isinstance(val, (int, float, np.floating, np.integer)) and not isinstance(val, (bool, np.bool_))
    ):
        out[col] = out[col].astype(object)
    if isinstance(val, (bool, np.bool_)):
        out[col] = out[col].astype(object)
        out.loc[mask, col] = bool(val)
    elif val is None or (isinstance(val, float) and not np.isfinite(val)):
        out.loc[mask, col] = np.nan if out[col].dtype != object else None
    elif isinstance(val, str):
        out[col] = out[col].astype(object)
        out.loc[mask, col] = val
    else:
        try:
            out.loc[mask, col] = val
        except (TypeError, ValueError):
            out[col] = out[col].astype(object)
            out.loc[mask, col] = val


def _attach_r_growth_and_mech_chem(
    out: pd.DataFrame,
    dcir_blocks: list[list[int]],
) -> pd.DataFrame:
    """R_ohmic/R_ct growth per 100 cycles + mech_vs_chem_ratio; forward-fill to later cycles."""
    for col in (
        "R_ohmic_growth_100", "R_ct_growth_100", "mech_vs_chem_ratio",
        "R_ohmic_soc50_ff", "R_ct_soc50_ff",
    ):
        if col not in out.columns:
            out[col] = np.nan

    series: list[tuple[int, float | None, float | None]] = []
    for block in dcir_blocks:
        if len(block) < 2:
            continue
        # SOC50 is typically middle of 80/50/20 block
        c50 = int(block[1]) if len(block) >= 2 else int(block[0])
        rows = out.loc[out["cycle"] == c50]
        if rows.empty:
            # try any cycle in block that has R_ohmic_soc50
            for c in block:
                rows = out.loc[out["cycle"] == int(c)]
                if not rows.empty and pd.notna(rows.iloc[0].get("R_ohmic_soc50")):
                    c50 = int(c)
                    break
        if rows.empty:
            continue
        r = rows.iloc[0]
        ro = r.get("R_ohmic_soc50")
        rc = r.get("R_ct_soc50")
        try:
            ro_f = float(ro) if ro is not None and pd.notna(ro) else None
        except (TypeError, ValueError):
            ro_f = None
        try:
            rc_f = float(rc) if rc is not None and pd.notna(rc) else None
        except (TypeError, ValueError):
            rc_f = None
        series.append((c50, ro_f, rc_f))

    if not series:
        return out

    c0, ro0, rc0 = series[0]
    # forward-fill block metrics onto subsequent feature cycles
    sorted_cycles = sorted(int(c) for c in out["cycle"].dropna().unique())
    for i, (c_blk, ro, rc) in enumerate(series):
        c_next = series[i + 1][0] if i + 1 < len(series) else (sorted_cycles[-1] + 1)
        growth_o = growth_c = mech = None
        if ro0 is not None and ro is not None and c_blk != c0:
            dn = (c_blk - c0) / 100.0
            if abs(dn) > 1e-9:
                growth_o = (ro - ro0) / dn
        if rc0 is not None and rc is not None and c_blk != c0:
            dn = (c_blk - c0) / 100.0
            if abs(dn) > 1e-9:
                growth_c = (rc - rc0) / dn
        if ro is not None and rc is not None and abs(rc) > 1e-12:
            mech = ro / rc

        for cyc in sorted_cycles:
            if cyc < c_blk or cyc >= c_next:
                continue
            mask = out["cycle"] == cyc
            if ro is not None:
                out.loc[mask, "R_ohmic_soc50_ff"] = ro
                # also expose as R_ohmic_soc50 for diagnosis if missing
                if "R_ohmic_soc50" in out.columns:
                    miss = mask & out["R_ohmic_soc50"].isna()
                    out.loc[miss, "R_ohmic_soc50"] = ro
            if rc is not None:
                out.loc[mask, "R_ct_soc50_ff"] = rc
                if "R_ct_soc50" in out.columns:
                    miss = mask & out["R_ct_soc50"].isna()
                    out.loc[miss, "R_ct_soc50"] = rc
            if growth_o is not None:
                out.loc[mask, "R_ohmic_growth_100"] = growth_o
            if growth_c is not None:
                out.loc[mask, "R_ct_growth_100"] = growth_c
            if mech is not None:
                out.loc[mask, "mech_vs_chem_ratio"] = mech
    return out


def _attach_eta_and_per(
    out: pd.DataFrame,
    raw_df: pd.DataFrame,
    dcir_blocks: list[list[int]],
    capa_anchors: set[int],
    pulse_set: set[int],
    *,
    rest_current_max: float,
) -> pd.DataFrame:
    eta_cols = [
        "eta_SOC20", "eta_SOC50", "eta_SOC80", "eta_max", "eta_argmax_SOC",
        "eta_mean", "eta_slope_lowSOC", "eta_valid",
        "Reff_scale", "Reff_shape_fit_r2",
        "Reff_resid_soc20", "Reff_resid_soc50", "Reff_resid_soc80",
    ]
    for c in eta_cols:
        if c not in out.columns:
            out[c] = np.nan if c != "eta_valid" else None

    all_cycles = sorted(int(c) for c in raw_df["cycle"].dropna().unique())
    for block in dcir_blocks:
        if len(block) < 1:
            continue
        # capa pair before block ≈ C/3; use cycle2 (start-1)
        rpt_c = int(block[0]) - 1
        if rpt_c not in capa_anchors and (out["cycle"] == rpt_c).any() is False:
            rpt_c = int(block[0]) - 2
        routine_c = nearest_routine_after_rpt(
            all_cycles, int(block[-1]), exclude=POST_RPT_EXCLUDE, pulse_set=pulse_set,
        )
        if routine_c is None:
            continue
        rpt_df = raw_df[raw_df["cycle"] == rpt_c]
        rou_df = raw_df[raw_df["cycle"] == routine_c]
        r_by_soc: dict[float, float] = {}
        for i, cyc in enumerate(block[:3]):
            soc = float(_SOC_ORDER[i]) if i < 3 else None
            if soc is None:
                continue
            rows = out.loc[out["cycle"] == int(cyc)]
            if rows.empty:
                continue
            r = rows.iloc[0].get(f"R_30s_total_soc{int(soc)}")
            try:
                rf = float(r)
            except (TypeError, ValueError):
                continue
            if np.isfinite(rf):
                r_by_soc[soc] = rf
        eta = compute_eta_for_pair(
            rpt_df, rou_df,
            rest_current_max=rest_current_max,
            r_dcir_by_soc=r_by_soc or None,
        )
        # stamp on routine cycle and RPT cycle
        for cyc in (rpt_c, routine_c, *block[:3]):
            mask = out["cycle"] == int(cyc)
            if not mask.any():
                continue
            for k, val in eta.items():
                _set_cell(out, mask, k, val)

    out = attach_per(out)
    # RCF slope per 100 cycles (simple first→last on finite RCF)
    if "RCF" in out.columns and "RCF_slope_100" not in out.columns:
        out["RCF_slope_100"] = np.nan
    rcf = pd.to_numeric(out.get("RCF"), errors="coerce")
    cyc = pd.to_numeric(out.get("cycle"), errors="coerce")
    m = rcf.notna() & cyc.notna()
    if m.sum() >= 4:
        x = cyc[m].to_numpy(dtype=float)
        y = rcf[m].to_numpy(dtype=float)
        # robust: first/last decile means
        order = np.argsort(x)
        n = len(order)
        k = max(1, n // 10)
        x0, y0 = float(np.mean(x[order[:k]])), float(np.mean(y[order[:k]]))
        x1, y1 = float(np.mean(x[order[-k:]])), float(np.mean(y[order[-k:]]))
        if abs(x1 - x0) > 1e-9:
            slope100 = (y1 - y0) / ((x1 - x0) / 100.0)
            out.loc[m, "RCF_slope_100"] = slope100
    return out


def enrich_feature_table(
    features: pd.DataFrame,
    raw_df: pd.DataFrame | None,
    *,
    rest_current_max: float = 0.5,
    expected_pulse_current: float = 70.0,
    with_curve_fit: bool = True,
    with_dqv_stats: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Attach Q_relax, DCIR, self-discharge, quality, RCF, η/PER, ΔQ(V), curve proxies."""
    meta: dict[str, Any] = {
        "baseline_cycle_auto": None,
        "dcir_blocks": [],
        "capa_anchor_cycles": [],
        "ocv_drift_blocks": [],
    }
    if features is None or features.empty:
        return features, meta

    out = features.copy()
    if raw_df is None or "cycle" not in raw_df.columns:
        return out, meta

    pulse = _find_pulse_cycles(raw_df, expected_pulse_current=expected_pulse_current)
    blocks = _group_consecutive(pulse, min_len=1)
    dcir_blocks = [b[:3] for b in blocks if len(b) >= 3] or blocks
    meta["dcir_blocks"] = dcir_blocks
    meta["baseline_cycle_auto"] = first_capa_baseline(out, dcir_blocks)

    out = attach_q_relax_from_dcir_blocks(out, dcir_blocks)

    capa_anchors: set[int] = set()
    for block in dcir_blocks:
        start = int(block[0])
        for c in (start - 2, start - 1):
            if (out["cycle"] == c).any():
                capa_anchors.add(c)
    meta["capa_anchor_cycles"] = sorted(capa_anchors)
    pulse_set = set(pulse)
    routine_mask = ~out["cycle"].isin(pulse_set)
    out = attach_rcf(out, routine_mask=routine_mask, rpt_cycles=capa_anchors)

    for soc in _SOC_ORDER:
        for k in (
            "R_ohmic", "R_ct", "tau_ct", "A_diff", "R_30s_total",
            "R_ohmic_frac", "dcir_fit_valid",
            "self_discharge_rate", "sd_fit_valid",
            "R_recovery_tau1", "R_recovery_tau2", "V_inf_est",
        ):
            col = f"{k}_soc{soc}"
            if col not in out.columns:
                out[col] = np.nan

    for block in dcir_blocks:
        soc_rows: list[dict[str, Any]] = []
        for i, cyc in enumerate(block[:3]):
            soc = _SOC_ORDER[i] if len(block) >= 3 and i < 3 else None
            g = raw_df[raw_df["cycle"] == int(cyc)]
            fit = decompose_pulse_cycle(
                g,
                rest_current_max=rest_current_max,
                expected_pulse_current=expected_pulse_current,
            )
            sd = self_discharge_for_cycle(
                g,
                rest_current_max=rest_current_max,
                expected_pulse_current=expected_pulse_current,
            )
            payload = result_to_dict(fit)
            mask = out["cycle"] == int(cyc)
            if soc is None:
                for k, val in payload.items():
                    _set_cell(out, mask, k, val)
                _set_cell(out, mask, "self_discharge_rate", sd.get("self_discharge_rate"))
                continue
            suf = f"_soc{soc}"
            for k, val in payload.items():
                _set_cell(out, mask, f"{k}{suf}", val)
            _set_cell(out, mask, f"self_discharge_rate_soc{soc}", sd.get("self_discharge_rate"))
            _set_cell(out, mask, f"sd_fit_valid_soc{soc}", sd.get("sd_fit_valid"))
            _set_cell(out, mask, f"V_inf_rest_soc{soc}", sd.get("V_inf_rest"))
            _set_cell(out, mask, f"relax_completeness_soc{soc}", sd.get("relax_completeness"))
            soc_rows.append({"soc": soc, "R_30s_total": fit.R_30s_total})
        ratios = soc_ratio_features(soc_rows)
        for cyc in block[:3]:
            mask = out["cycle"] == int(cyc)
            for k, val in ratios.items():
                _set_cell(out, mask, k, val)

    out = _attach_r_growth_and_mech_chem(out, dcir_blocks)
    out = _attach_eta_and_per(
        out, raw_df, dcir_blocks, capa_anchors, pulse_set,
        rest_current_max=rest_current_max,
    )

    out, ocv_blocks = attach_ocv_drift_to_features(
        out,
        dcir_blocks,
        raw_df,
        rest_current_max=rest_current_max,
        expected_pulse_current=expected_pulse_current,
    )
    meta["ocv_drift_blocks"] = ocv_blocks.to_dict(orient="records") if not ocv_blocks.empty else []

    for col in (
        "samples_per_mV", "v_noise_sigma", "quant_step_est", "dqdv_snr",
        "rest_sufficiency", "pulse_sample_count_1s", "pulse_current_stability",
        "leg_completeness", "temperature_available", "quality_score",
        "quality_gate_failed_groups",
    ):
        if col not in out.columns:
            out[col] = pd.Series([None] * len(out), dtype=object)

    for cyc in out["cycle"].astype(int).unique():
        g = raw_df[raw_df["cycle"] == int(cyc)]
        qm = cycle_quality_metrics(g, rest_current_max=rest_current_max)
        mask = out["cycle"] == int(cyc)
        for k, val in qm.items():
            _set_cell(out, mask, k, val)

    ref = meta["baseline_cycle_auto"]
    feat_cycles = sorted(int(c) for c in out["cycle"].dropna().unique())
    if with_dqv_stats and ref is not None:
        out = attach_dqv_stats(
            out, raw_df, ref_cycle=int(ref),
            rest_current_max=rest_current_max, cycle_list=feat_cycles,
        )
    if with_curve_fit and ref is not None:
        out = attach_curve_fit(
            out, raw_df, ref_cycle=int(ref),
            rest_current_max=rest_current_max, cycle_list=feat_cycles,
        )

    # §5.12 fade exponent + bilinear knee (cell-level, broadcast to rows)
    out = attach_fade_trajectory(out)

    return out, meta
