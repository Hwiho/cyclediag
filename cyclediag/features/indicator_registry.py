"""Canonical indicator registry — one place that says what each column *is*.

Why this exists
---------------
The extract pipeline emits ~390 columns per cycle. Many of them are the same
measurement under a different name, unit, or normalization. Left unmanaged that
duplication is not cosmetic: every consumer that builds its feature pool by
"take all numeric columns" silently weights a physical signal by how many
aliases it happens to have. Two concrete symptoms:

* ``predict_features`` averages |z| over the pool, so charge-capacity was
  counted four times (``chgCapa``, ``chgCCcapa``, ``chg_E``,
  ``chg_dQdV_area_sum``) and every landmark voltage twice (raw + ``delta_``).
* ``mode_weights_assb_si_v1`` scored LLI from both ``CE`` and ``CI``, and
  ``CI`` is exactly ``100 - CE``, so one measurement carried 44 % of the mode.

Two orthogonal axes are recorded here.

``role``
    What kind of quantity it is. Only ``ROLE_INDICATOR`` columns are
    degradation evidence; targets, covariates, QC provenance, diagnosis
    outputs and metadata must never be fed to a generic indicator pool.

``family``
    Which physical measurement it belongs to. A family holds columns that were
    shown to be redundant, and exactly one member is the representative that
    enters an automatically built pool. Every member stays emitted and stays
    available to explicit configs, plots and exports — a family says
    "do not count these as independent", not "throw these away".

Membership criteria — a merge needs (1) or (2), *and* always (3)
    1. Structural — one column is an exact algebraic function of another: a
       unit change (``f_Q_spec`` = ``f_Q_max`` / active mass), a normalization
       of the same quantity by a slowly varying reference (``Q_relax_pct`` =
       ``Q_relax`` / block capacity), or a fallback that returns the partner
       (``chgCapa_CCratio_norm``). ``delta_<x>`` and ``<x>_inc`` are affine in
       ``<x>`` with a per-cell constant, so within a cell they are exactly
       redundant; this is handled by ``canonical_base`` rather than listed.
    2. Empirical — the *per-cell* median of ``min(|pearson|, |spearman|)`` is
       ``>= 0.98`` over at least three DOE1 / DOE2 / DOE3 / ASSB fixture cells.
       Pooled correlation is recorded as a cross-check but is never the sole
       justification: pooling mixes between-cell spread into the coefficient.
       ``chg_temp_avg`` / ``dchg_temp_avg`` reach pooled 0.996 only because
       cells sit at different temperatures, and the one cell with enough paired
       samples gives 0.75. Conversely a low pooled number does not block a
       merge — ``EoD_chgR_10s`` and its ``_T25`` partner sit at pooled 0.54 for
       the same reason, yet inside a cell the temperature correction is monotone
       in the raw value and the per-cell median is exactly 1.0000.
    3. Same measurement, same segment — correlation alone is not enough. Where
       a resolution axis exists on purpose, members from different positions on
       that axis are never merged even when they correlate: SOC bands
       (``hyst_area`` vs ``hyst_area_mid``, per-cell 0.995), SOC points
       (``R_ohmic_soc20`` vs ``_soc50``) and pulse durations
       (``EoC_dchgR_10s`` vs ``_60s``) all exist to localize degradation, and
       collapsing them would delete the axis rather than a duplicate. Merges
       run *within* one position: the loop area and the peak ``|dV|`` of the
       same band, or the raw and temperature-corrected form of the same pulse.

Candidates that were measured and *rejected* are recorded in
``planning/IMPROVEMENT_ROADMAP.md``; the short list is ``V_inf_rest_soc*`` vs
``V_inf_est_soc*`` (two different estimators, pooled-only support),
``EoD_restV_60s`` vs ``EoD_restV_end`` (per-cell 0.976, discharge-side
relaxation is slower than the charge side, whose 60 s sample does merge at
0.998), ``CE`` vs ``CI_per_hour`` (0.90 — normalizing the inefficiency by cycle
duration makes it a genuinely new column, which is why the retired ``CI`` was
replaced by ``CI_per_hour`` rather than simply deleted), and the cross-band
hysteresis pairs held out by criterion 3.

``EXACT_ALIASES`` is the stronger verdict: an exact algebraic duplicate that no
longer has its own column. ``apply_aliases`` maps the retired names when
reading tables written before the consolidation.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping

import pandas as pd

ROLE_INDICATOR = "indicator"
ROLE_TARGET = "target"
ROLE_COVARIATE = "covariate"
ROLE_QC = "qc"
ROLE_DIAGNOSIS = "diagnosis"
ROLE_META = "meta"

ROLES = (
    ROLE_INDICATOR,
    ROLE_TARGET,
    ROLE_COVARIATE,
    ROLE_QC,
    ROLE_DIAGNOSIS,
    ROLE_META,
)

DELTA_PREFIX = "delta_"
INC_SUFFIX = "_inc"


# --------------------------------------------------------------------------
# Retired exact duplicates: name -> (canonical column, identity)
# --------------------------------------------------------------------------
EXACT_ALIASES: dict[str, tuple[str, str]] = {
    "CI": ("CE", "CI == 100 - CE"),
    "ocv_spread_compression": (
        "delta_ocv_spread_20_80",
        "both were assigned the same d(ocv_spread_20_80) value",
    ),
    "ocv_spread_slope": (
        "delta_ocv_spread_20_80",
        "slope of a 3-point fit on evenly spaced SOC == -delta_spread/60",
    ),
    "ocv_block_id": ("block_id", "broadcast copy of block_id"),
    "ocv_V_inf_soc80": (
        "V_inf_rest_soc80",
        "same self_discharge_for_cycle V_inf_rest, fitted twice",
    ),
    "ocv_V_inf_soc50": (
        "V_inf_rest_soc50",
        "same self_discharge_for_cycle V_inf_rest, fitted twice",
    ),
    "ocv_V_inf_soc20": (
        "V_inf_rest_soc20",
        "same self_discharge_for_cycle V_inf_rest, fitted twice",
    ),
    "R_SOC_diff_20_80": (
        "R_SOC_slope",
        "slope of a 3-point fit on evenly spaced SOC == -(R20 - R80)/60",
    ),
}


# --------------------------------------------------------------------------
# Families: family name -> ordered members, earliest listed member wins.
#
# Members are canonical bases: never a retired alias, never a ``delta_*`` /
# ``*_inc`` wrapper. Wrappers are folded onto their base by ``canonical_base``,
# so listing ``hyst_area`` also covers ``delta_hyst_area``.
# --------------------------------------------------------------------------
FAMILIES: dict[str, tuple[str, ...]] = {
    # Capacity / energy. dchgCapa and SoHQ are the health target; dchg_E
    # followed at 0.997 and dchg_dVdQ_SOC0_Q — the Q coordinate of the SOC0
    # landmark, i.e. the end of the discharge — at 1.0000 pooled and per cell.
    # None of them can serve as independent evidence for a change in health.
    "capacity_discharge": ("dchgCapa", "SoHQ", "dchg_E", "dchg_dVdQ_SOC0_Q"),
    "capacity_charge": ("chgCapa", "chgCCcapa", "chg_E", "chg_dQdV_area_sum"),
    # f_Q_spec is f_Q_max / active_mass_g — a unit change with a constant
    # divisor. Not on the LGES path, so this one rests on the code, not on a
    # correlation.
    "capacity_legacy": ("f_Q_max", "f_Q_spec"),
    # CC/CV split: the CC share, the amount of CV charge and its duration are
    # one measurement (0.997-0.998 pooled and per cell). chgCapa_CCratio_norm
    # is the same share against a reference cycle and falls back to the raw
    # share when that reference is missing, which is every fixture row that
    # has it.
    "cv_amount": (
        "chgCapa_CCratio",
        "chgCVcapa",
        "chgCVtime",
        "chgCapa_CCratio_norm",
    ),
    # Relaxed end-of-charge rest voltage. The 30 min sample equals the last
    # rest sample on every fixture cycle (rest is exactly 30 min), and the
    # 60 s sample followed at per-cell min-|r| 0.998. The discharge side is
    # *not* symmetric: EoD_restV_60s only reaches 0.976 per cell, so it stays
    # an independent column and only the 30 min / end pair is folded.
    "rest_v_eoc_relaxed": ("EoC_restV_end", "EoC_restV_30m", "EoC_restV_60s"),
    "rest_v_eod_relaxed": ("EoD_restV_end", "EoD_restV_30m"),
    # Voltage at the moment the discharge load is released: the cycler logs the
    # discharge cutoff and the first rest sample as the same point (0.992).
    "v_eod_terminal": ("EoD_restV_init", "dchg_V_cutoff"),
    # Landmark resistance: only the temperature-corrected variant merges with
    # its raw column. The four pulse durations stayed independent
    # (min-|r| 0.94-0.95), which is the R(t) decomposition we want to keep.
    "r_eoc_dchg_10s": ("EoC_dchgR_10s", "EoC_dchgR_10s_T25"),
    "r_eod_chg_10s": (
        "EoD_chgR_10s",
        "EoD_chgR_10s_T25",
        "EoD_chgR_R10_minus_R0p1",
    ),
    "r_eod_chg_30s": ("EoD_chgR_30s", "EoD_chgR_R30_minus_R0p1"),
    # Hysteresis: within a band, loop area and peak |dV| are two summaries of
    # the same dV(Q) segment, at per-cell 0.988-0.992.
    #
    # Bands stay separate under criterion 3, and the measurements say to be
    # careful here rather than aggressive. The low band is plainly independent
    # (hyst_area vs hyst_area_low: |r| = 0.004), but the global, mid and high
    # bands do track each other on these cells — hyst_area vs hyst_max_dV_mid
    # reaches per-cell 0.995. That is partly by construction, since the global
    # loop integral contains the mid band, and the cross-band pairs are not
    # mutually consistent: merging global with mid and high with mid would
    # collapse all bands into one column and delete the SOC-resolved
    # hysteresis that exists to localize Si degradation. So the bands are left
    # as four families and the residual overlap is accepted.
    "hysteresis_global": ("hyst_area", "hyst_max_dV"),
    "hysteresis_mid": ("hyst_area_mid", "hyst_max_dV_mid"),
    "hysteresis_high": ("hyst_area_high", "hyst_max_dV_high"),
    # Cliff width at SOC0 in absolute Ah and in normalized SOC (per-cell 0.999).
    # The absolute-Ah form leads: it is the Si/Gr mechanism discriminator.
    "cliff_width_soc0": (
        "dchg_dVdQ_SOC0_cliff_width_abs",
        "dchg_dVdQ_SOC0_cliff_width",
    ),
    "q_relax": ("Q_relax_pct", "Q_relax"),
}

_FAMILY_OF: dict[str, str] = {}
for _fam, _members in FAMILIES.items():
    for _m in _members:
        if _m in _FAMILY_OF:
            raise RuntimeError(f"{_m} listed in two families: {_FAMILY_OF[_m]}, {_fam}")
        _FAMILY_OF[_m] = _fam


# --------------------------------------------------------------------------
# Roles
# --------------------------------------------------------------------------
_META_EXACT = frozenset({
    "cell_id", "file", "leg", "feature_set", "cycle", "tagged_cycle",
    "tagged_source", "pair_label", "block_id", "block_start_cycle",
    "cv_method", "cv_detect_method", "has_cv", "ocv_drift_mode",
    "diagnosis_method", "diagnosis_model_version", "diagnosis_version",
    "anomaly_score", "flag", "top_features", "quality_gate_failed_groups",
    "protocol_kind", "protocol_excluded",
})

# Health targets, the columns that tracked them at min-|r| >= 0.997, and the
# columns computed *from* them. All are useless — or circular — as evidence
# for a change in health.
_TARGET_EXACT = frozenset({
    "SoHQ", "dchgCapa", "chgCapa", "capacity",
    "chgCCcapa", "chg_E", "dchg_E", "chg_dQdV_area_sum",
    # Q coordinate of the SOC0 landmark: min-|r| 1.0000 with dchgCapa
    "dchg_dVdQ_SOC0_Q",
    # derivatives of SoHQ. Their correlation with capacity is low (0.34, 0.10)
    # but they are differentiated from the target, so scoring a cell as
    # anomalous on them restates the target rather than predicting it.
    "dSoHQ_dN", "d2SoHQ",
    # legacy f_* extractor: f_Q_spec is f_Q_max divided by the active mass
    "f_Q_max", "f_Q_spec",
})

# Protocol / environment conditions: useful for gating and sanity checks,
# never degradation evidence. chg_temp_avg and dchg_temp_avg are kept as two
# columns — they are not a family, because their pooled 0.996 is a between-cell
# effect and the only cell with enough paired samples gives 0.75.
_COVARIATE_EXACT = frozenset({
    "chg_V_cutoff", "dchg_V_cutoff", "chg_I_cutoff",
    "chg_temp_avg", "dchg_temp_avg", "temperature_available",
    "cycle_duration_h",
})

# Provenance: thresholds actually used, fit validity, sample counts, landmark
# locators, signal-quality metrics.
_QC_EXACT = frozenset({
    "samples_per_mV", "v_noise_sigma", "quant_step_est", "dqdv_snr",
    "rest_sufficiency", "pulse_sample_count_1s", "pulse_current_stability",
    "leg_completeness", "quality_score", "cv_detect_mismatch_pct",
    "relax_completeness_max", "diagnosis_quality_score", "diagnosis_valid",
    "Q_relax_significant", "dchg_cliff_valid", "dchg_cliff_thr_used",
    # the Savitzky-Golay smoothing width actually used, reported in Ah. It is
    # q_span * sg_window / (n_interp - 1), so it scales with capacity at a
    # fixed 4.19 % on every fixture cell — a processing parameter, not a width
    # the cell produced, which is why it is not in the capacity family either.
    "dchg_cliff_sg_width_ah",
    "dchg_fit_r2", "dchg_fit_corr_s_o", "dchg_fit_degenerate_flag",
    "dchg_fit_residual_rms", "dchg_fit_residual_max",
    "dchg_fit_residual_argmax_SOC",
})

_QC_PATTERNS = (
    re.compile(r"^dcir_fit_"),
    re.compile(r"^sd_fit_valid"),
    re.compile(r"^recovery_fit_r2"),
    re.compile(r"^tau_consistency_flag"),
    re.compile(r"^relax_completeness_soc\d+$"),
    re.compile(r"^relax_amp_ratio"),
    re.compile(r"^n_points_soc\d+$"),
    re.compile(r"^n_t_le_1s_soc\d+$"),
    re.compile(r"^flag_soc\d+$"),
    re.compile(r"^pulse_current_A_soc\d+$"),
)

_DIAGNOSIS_PATTERNS = (
    re.compile(r"_pattern_score$"),
    re.compile(r"_score$"),
    re.compile(r"_confidence$"),
    re.compile(r"_evidence_count$"),
    re.compile(r"_supporting_features$"),
    re.compile(r"_conflicting_features$"),
    re.compile(r"_est$"),
    re.compile(r"_est_hc_calibrated$"),
)

# Kept as indicators even though they end in a pattern that usually means
# something else.
_DIAGNOSIS_EXEMPT = frozenset({
    "dchg_shape_DTW", "quality_score", "diagnosis_quality_score",
    "dqdv_snr", "dchg_fit_r2",
})


def canonical_name(col: str) -> str:
    """Retired alias -> the column that replaced it."""
    hit = EXACT_ALIASES.get(col)
    return hit[0] if hit else col


def canonical_base(col: str) -> str:
    """Strip the baseline-referenced wrapper: ``delta_x`` / ``x_inc`` -> ``x``.

    ``delta_x = x - x_baseline`` and ``x_inc = (x - x_baseline)/|x_baseline|``
    are affine in ``x`` with a per-cell constant, so they carry no information
    beyond ``x`` within a cell. They share ``x``'s family and role.
    """
    name = canonical_name(col)
    if name.startswith(DELTA_PREFIX):
        return canonical_base(name[len(DELTA_PREFIX):])
    if name.endswith(INC_SUFFIX) and len(name) > len(INC_SUFFIX):
        return canonical_base(name[: -len(INC_SUFFIX)])
    return name


def is_baseline_referenced(col: str) -> bool:
    """True for ``delta_*`` / ``*_inc`` wrappers."""
    return canonical_base(col) != canonical_name(col)


def role_of(col: str) -> str:
    """Classify a column. Unknown columns default to ``ROLE_INDICATOR``."""
    name = canonical_name(col)
    if name in _META_EXACT:
        return ROLE_META
    base = canonical_base(name)
    if base in _META_EXACT:
        return ROLE_META
    for candidate in (name, base):
        if candidate in _TARGET_EXACT:
            return ROLE_TARGET
        if candidate in _COVARIATE_EXACT:
            return ROLE_COVARIATE
        if candidate in _QC_EXACT:
            return ROLE_QC
        if any(p.search(candidate) for p in _QC_PATTERNS):
            return ROLE_QC
        if candidate not in _DIAGNOSIS_EXEMPT and any(
            p.search(candidate) for p in _DIAGNOSIS_PATTERNS
        ):
            return ROLE_DIAGNOSIS
    return ROLE_INDICATOR


def family_of(col: str) -> str:
    """Family key for ``col``. Columns with no listed partner form their own."""
    base = canonical_base(col)
    return _FAMILY_OF.get(base, base)


def family_primary(family: str) -> str:
    """Declared representative of a family (first listed member)."""
    members = FAMILIES.get(family)
    return members[0] if members else family


def _rank_within_family(col: str) -> tuple[int, int, int, int, str]:
    """Sort key picking one column per family (lowest wins).

    Order of preference: a live column over a retired alias, the declared
    representative, then the baseline-referenced form (comparable across cells
    and what the diagnosis configs consume), then a stable name order.
    """
    base = canonical_base(col)
    members = FAMILIES.get(family_of(col))
    order = members.index(base) if members and base in members else len(members or ())
    return (
        1 if col in EXACT_ALIASES else 0,
        order,
        0 if is_baseline_referenced(col) else 1,
        len(col),
        col,
    )


def dedupe_by_family(cols: Iterable[str]) -> list[str]:
    """Keep one column per family, preserving input order of the survivors."""
    best: dict[str, str] = {}
    for c in cols:
        fam = family_of(c)
        cur = best.get(fam)
        if cur is None or _rank_within_family(c) < _rank_within_family(cur):
            best[fam] = c
    chosen = set(best.values())
    return [c for c in dict.fromkeys(cols) if c in chosen]


def indicator_columns(
    df: pd.DataFrame,
    *,
    roles: Iterable[str] = (ROLE_INDICATOR,),
    require_numeric: bool = True,
) -> list[str]:
    """Columns of ``df`` whose role is in ``roles`` (no family dedupe)."""
    wanted = set(roles)
    out: list[str] = []
    for c in df.columns:
        if role_of(str(c)) not in wanted:
            continue
        if require_numeric and not pd.api.types.is_numeric_dtype(df[c]):
            continue
        out.append(str(c))
    return out


def primary_indicator_columns(
    df: pd.DataFrame,
    *,
    roles: Iterable[str] = (ROLE_INDICATOR,),
    require_numeric: bool = True,
) -> list[str]:
    """One representative per family — the pool for any averaged/ranked score."""
    return dedupe_by_family(
        indicator_columns(df, roles=roles, require_numeric=require_numeric)
    )


def annotate_indicators(
    frame: pd.DataFrame,
    *,
    column: str = "feature",
) -> pd.DataFrame:
    """Add ``role`` / ``family`` / ``is_family_primary`` to a per-indicator table."""
    if frame is None or frame.empty or column not in frame.columns:
        return frame
    out = frame.copy()
    names = out[column].astype(str)
    out["role"] = [role_of(n) for n in names]
    out["family"] = [family_of(n) for n in names]
    primaries = set(dedupe_by_family(list(names)))
    out["is_family_primary"] = [n in primaries for n in names]
    return out


def apply_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Rename retired alias columns so pre-consolidation tables still load."""
    if df is None or df.empty:
        return df
    rename = {
        c: canonical_name(c)
        for c in df.columns
        if c in EXACT_ALIASES and canonical_name(c) not in df.columns
    }
    drop = [c for c in df.columns if c in EXACT_ALIASES and c not in rename]
    out = df.drop(columns=drop) if drop else df
    return out.rename(columns=rename) if rename else out


def registry_report(columns: Iterable[str]) -> pd.DataFrame:
    """Role / family / primary verdict per column — used by tests and docs."""
    names = [str(c) for c in columns]
    primaries = set(dedupe_by_family(names))
    rows: list[Mapping[str, object]] = [
        {
            "column": n,
            "role": role_of(n),
            "family": family_of(n),
            "is_family_primary": n in primaries,
            "baseline_referenced": is_baseline_referenced(n),
            "retired_alias_of": canonical_name(n) if n in EXACT_ALIASES else None,
        }
        for n in names
    ]
    return pd.DataFrame(rows)
