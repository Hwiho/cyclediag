"""LGES cycle-analysis feature catalog (from lab indicator spec)."""

from __future__ import annotations

FEATURE_SET_LGES = "vp_lges_cycle_v2"
MAX_DQDV_PEAKS = 8
# Landmark DC-IR style offsets (0.1 s + 10/30/60 s); 60 s kept for legacy columns
RESISTANCE_OFFSETS_S = (0.1, 10.0, 30.0, 60.0)


def resistance_offset_label(offset_s: float) -> str:
    """Column suffix for a resistance sample time (0.1 → ``0p1s``)."""
    if abs(offset_s - 0.1) < 1e-9:
        return "0p1s"
    return f"{int(round(offset_s))}s"

# Rest sample times (seconds from rest start). ``end`` = last point in rest block.
EOC_REST_OFFSETS: dict[str, float | None] = {
    "init": 0.0,
    "60s": 60.0,
    "30m": 1800.0,
    "end": None,
}
EOD_REST_OFFSETS = dict(EOC_REST_OFFSETS)

# Columns that get delta_* (absolute vs cycle 1) after extraction
DELTA_ABS_COLS = [
    "EoC_restV_60s", "EoC_restV_30m", "EoC_restV_end",
    "EoD_restV_60s", "EoD_restV_30m", "EoD_restV_end",
    "chgCapa_CCratio",
    "dchg_dQdV_peak1_V", "chg_dQdV_peak1_V",
    "dchg_dVdQ_SOC0", "dchg_dVdQ_SOC5", "dchg_dVdQ_SOC10", "dchg_dVdQ_SOCmid",
    "chg_dVdQ_SOC100",
    "dchg_V_avg", "chg_V_avg",
    "hyst_area", "hyst_max_dV",
    "dchg_plateau_V",
    "dchg_dVdQ_SOC0_cliff_width", "dchg_dVdQ_SOC0_to_mid_ratio",
    "dchg_V_cutoff_margin", "dchg_shape_DTW",
    "EoC_restV_tau", "EoD_restV_tau",
]

# Columns that get *_inc (% vs cycle 1)
DELTA_PCT_COLS = [
    "EoC_dchgR_0p1s", "EoC_dchgR_10s", "EoC_dchgR_30s", "EoC_dchgR_60s",
    "EoD_chgR_0p1s", "EoD_chgR_10s", "EoD_chgR_30s", "EoD_chgR_60s",
]

BAND_CAPACITY_COLS = [
    "dchg_Q_high_V", "dchg_Q_low_V", "dchg_Q_mid_V",
    "dchg_Q_high_frac", "dchg_Q_low_frac", "dchg_f_graphite_proxy",
]

PATTERN_CHECK_COLS = [
    "chg_V_cutoff", "dchg_V_cutoff", "chg_I_cutoff",
    "chg_temp_avg", "dchg_temp_avg",
]

REST_EOC_COLS = [
    "EoC_restV_init", "EoC_restV_60s", "EoC_restV_30m", "EoC_restV_end",
]
REST_EOD_COLS = [
    "EoD_restV_init", "EoD_restV_60s", "EoD_restV_30m", "EoD_restV_end",
]

REST_DERIVED_COLS = [
    "EoC_restV_relax",  # end - init
    "EoD_restV_relax",
    "EoC_restV_relax_60s",  # 60s - init
    "EoD_restV_relax_60s",
    "EoC_restV_tau",
    "EoD_restV_tau",
]

RESISTANCE_DERIVED_COLS = [
    "EoC_dchgR_10_60_ratio",
    "EoD_chgR_10_60_ratio",
    "EoC_dchgR_R10_minus_R0p1",
    "EoC_dchgR_R30_minus_R0p1",
    "EoD_chgR_R10_minus_R0p1",
    "EoD_chgR_R30_minus_R0p1",
    "EoC_dchgR_10s_T25",
    "EoD_chgR_10s_T25",
]

CAPACITY_COLS = [
    "CE", "CE_rev", "dchgCapa", "SoHQ", "chgCapa",
    "chgCCcapa", "chgCVcapa", "chgCapa_CCratio", "chgCVtime",
]

SHAPE_COLS = [
    "chg_V_avg", "dchg_V_avg",
    "chg_E", "dchg_E",
    "chg_ir_drop_proxy", "dchg_ir_drop_proxy",
    "hyst_area", "hyst_max_dV",
    "chg_plateau_V", "chg_plateau_width",
    "dchg_plateau_V", "dchg_plateau_width",
    "chg_dQdV_area_sum", "dchg_dQdV_area_sum",
    "dchg_V_cutoff_margin",
    "dchg_shape_DTW",
]

DVDQ_SOC_COLS = [
    "dchg_dVdQ_SOC0", "dchg_dVdQ_SOC0_Q",
    "dchg_dVdQ_SOC5", "dchg_dVdQ_SOC10", "dchg_dVdQ_SOCmid",
    "dchg_dVdQ_SOC0_cliff_width", "dchg_dVdQ_SOC0_to_mid_ratio",
    "chg_dVdQ_SOC100",
]

TRAJECTORY_COLS = [
    "dSoHQ_dN", "d2SoHQ",
    "EoC_dchgR_10s_growth_50",
    "CE_local_20",
]

DIAGNOSIS_COLS = [
    "LLI_pattern_score", "LAM_PE_pattern_score", "LAM_NE_pattern_score",
    "impedance_pattern_score",
    "transport_limitation_score", "plating_risk_score", "contact_loss_score",
    "LLI_confidence", "LAM_PE_confidence", "LAM_NE_confidence",
    "impedance_confidence",
    "transport_limitation_confidence", "plating_risk_confidence", "contact_loss_confidence",
    "diagnosis_quality_score", "diagnosis_valid",
    "diagnosis_method", "diagnosis_model_version", "diagnosis_version",
    "LLI_est", "LAM_PE_est", "LAM_NE_est", "electrode_slippage_est",
    "LLI_est_hc_calibrated", "LAM_PE_est_hc_calibrated", "LAM_NE_est_hc_calibrated",
]


def dqdv_peak_column_names() -> list[str]:
    cols: list[str] = []
    for i in range(1, MAX_DQDV_PEAKS + 1):
        cols.extend([
            f"chg_dQdV_peak{i}_V", f"chg_dQdV_peak{i}",
            f"dchg_dQdV_peak{i}_V", f"dchg_dQdV_peak{i}",
            f"chg_dVdQ_peak{i}_Q", f"chg_dVdQ_peak{i}",
            f"dchg_dVdQ_peak{i}_Q", f"dchg_dVdQ_peak{i}",
        ])
    cols.extend(DVDQ_SOC_COLS)
    return cols


def all_lges_feature_columns() -> list[str]:
    res_cols = []
    for prefix in ("EoC_dchgR", "EoD_chgR"):
        for off in RESISTANCE_OFFSETS_S:
            res_cols.append(f"{prefix}_{resistance_offset_label(off)}")
    inc_cols = [f"{c}_inc" for c in DELTA_PCT_COLS]
    delta_cols = [f"delta_{c}" for c in DELTA_ABS_COLS]
    return (
        PATTERN_CHECK_COLS
        + REST_EOC_COLS + REST_EOD_COLS + REST_DERIVED_COLS
        + res_cols + RESISTANCE_DERIVED_COLS + inc_cols
        + CAPACITY_COLS + BAND_CAPACITY_COLS + ["delta_chgCapa_CCratio"]
        + SHAPE_COLS
        + dqdv_peak_column_names()
        + TRAJECTORY_COLS
        + DIAGNOSIS_COLS
        + delta_cols
    )
