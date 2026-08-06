"""Feature family registry — IMPROVEMENT_ROADMAP §4.1.

Used to limit anomaly inputs to 1–2 representatives per family and document
unit / layer / requires metadata. Diagnosis can still use the full feature set.
"""

from __future__ import annotations

from typing import Any

FAMILY: dict[str, list[str]] = {
    "coulombic": ["SoHQ", "dchgCapa", "CE", "CI", "CI_per_hour", "Q_relax_pct"],
    "kinetic": ["R_ct_soc50", "tau_ct_soc50", "R_30s_total_soc50", "tau_CV", "VE", "EE"],
    "geometric": ["R_ohmic_soc50", "R_ohmic_frac_soc50", "mech_vs_chem_ratio", "R_ohmic_growth_100"],
    "transport": ["A_diff_soc50", "PER", "eta_SOC50", "eta_argmax_SOC", "RCF", "RCF_slope_100"],
    "thermodynamic": [
        "LAM_curve_proxy", "LLI_curve_proxy", "R_curve_proxy",
        "dQV_log_var", "dchg_fit_offset", "dchg_fit_scale",
    ],
    "integrity": ["self_discharge_rate_soc80", "self_discharge_rate_soc50", "microshort_score"],
    "si_hysteresis": ["hyst_area_low", "hyst_area_mid", "hyst_area_high", "hyst_area"],
    "thermal": ["dT_max"],  # unavailable while Temp==0
}

# Preferred anomaly representatives (1–2 per family)
ANOMALY_REPRESENTATIVES: dict[str, list[str]] = {
    "coulombic": ["SoHQ", "CE"],
    "kinetic": ["R_ct_soc50", "VE"],
    "geometric": ["R_ohmic_soc50", "mech_vs_chem_ratio"],
    "transport": ["PER", "RCF"],
    "thermodynamic": ["dQV_log_var", "LAM_curve_proxy"],
    "integrity": ["self_discharge_rate_soc80"],
    "si_hysteresis": ["hyst_area_low"],
}

FEATURE_META: dict[str, dict[str, Any]] = {
    "SoHQ": {"unit": "%", "layer": 1, "family": "coulombic"},
    "CE": {"unit": "%", "layer": 1, "family": "coulombic"},
    "R_ohmic_soc50": {"unit": "mOhm", "layer": 2, "family": "geometric"},
    "R_ct_soc50": {"unit": "mOhm", "layer": 2, "family": "kinetic"},
    "PER": {"unit": "1", "layer": 2, "family": "transport"},
    "dQV_log_var": {"unit": "log10(Ah^2)", "layer": 1, "family": "thermodynamic"},
    "LAM_curve_proxy": {"unit": "%", "layer": 2, "family": "thermodynamic", "note": "proxy not *_est"},
    "hyst_area_low": {"unit": "V", "layer": 1, "family": "si_hysteresis"},
    "mech_vs_chem_ratio": {"unit": "1", "layer": 3, "family": "geometric", "note": "hypothesis"},
}


def anomaly_feature_list(available: list[str] | None = None) -> list[str]:
    """Return de-duplicated anomaly input columns present in ``available``."""
    out: list[str] = []
    for reps in ANOMALY_REPRESENTATIVES.values():
        for r in reps:
            if available is None or r in available:
                if r not in out:
                    out.append(r)
    return out


def family_of(feature: str) -> str | None:
    meta = FEATURE_META.get(feature)
    if meta:
        return str(meta.get("family"))
    for fam, members in FAMILY.items():
        if feature in members:
            return fam
    return None
