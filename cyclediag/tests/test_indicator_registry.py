"""Registry invariants and the consolidations they encode."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cyclediag.features.indicator_registry import (
    EXACT_ALIASES,
    FAMILIES,
    ROLE_COVARIATE,
    ROLE_DIAGNOSIS,
    ROLE_INDICATOR,
    ROLE_META,
    ROLE_QC,
    ROLE_TARGET,
    ROLES,
    annotate_indicators,
    apply_aliases,
    canonical_base,
    canonical_name,
    dedupe_by_family,
    family_of,
    indicator_columns,
    primary_indicator_columns,
    registry_report,
)

_CONFIG_DIR = Path(__file__).resolve().parents[1] / "diagnosis" / "config"


# --------------------------------------------------------------------------
# registry structure
# --------------------------------------------------------------------------
def test_family_members_are_canonical_bases():
    for family, members in FAMILIES.items():
        assert members, f"{family} is empty"
        for m in members:
            assert canonical_base(m) == m, f"{family}: {m} is not a canonical base"
            assert m not in EXACT_ALIASES, f"{family}: {m} is a retired alias"
            assert family_of(m) == family


def test_families_are_disjoint():
    seen: dict[str, str] = {}
    for family, members in FAMILIES.items():
        for m in members:
            assert m not in seen, f"{m} in both {seen.get(m)} and {family}"
            seen[m] = family


def test_aliases_point_at_live_columns():
    for alias, (canonical, identity) in EXACT_ALIASES.items():
        assert canonical != alias
        assert canonical not in EXACT_ALIASES, f"{alias} -> {canonical} is itself retired"
        assert identity, f"{alias} has no recorded identity"


def test_baseline_wrappers_share_role_and_family():
    for base in ("hyst_area", "EoC_restV_end", "EoC_dchgR_10s"):
        for wrapped in (f"delta_{base}", f"{base}_inc"):
            assert canonical_base(wrapped) == base
            assert family_of(wrapped) == family_of(base)


def test_roles_are_known_values():
    cols = [
        "dchgCapa", "SoHQ", "chg_temp_avg", "quality_score", "LLI_pattern_score",
        "cell_id", "hyst_area", "delta_hyst_area", "R_ohmic_soc50",
        "sd_fit_valid_soc80", "flag_soc20", "cycle",
    ]
    for c in cols:
        from cyclediag.features.indicator_registry import role_of

        assert role_of(c) in ROLES


def test_role_assignments():
    from cyclediag.features.indicator_registry import role_of

    assert role_of("SoHQ") == ROLE_TARGET
    assert role_of("dchg_E") == ROLE_TARGET  # tracks dchgCapa at min-|r| >= 0.997
    assert role_of("chg_temp_avg") == ROLE_COVARIATE
    assert role_of("dchg_cliff_thr_used") == ROLE_QC
    assert role_of("relax_completeness_soc50") == ROLE_QC
    assert role_of("microshort_score") == ROLE_DIAGNOSIS
    assert role_of("LLI_evidence_count") == ROLE_DIAGNOSIS
    assert role_of("block_id") == ROLE_META
    assert role_of("hyst_area") == ROLE_INDICATOR
    assert role_of("delta_hyst_area") == ROLE_INDICATOR
    assert role_of("R_ohmic_soc50") == ROLE_INDICATOR
    # dchg_shape_DTW ends in nothing diagnostic despite the naming overlap
    assert role_of("dchg_shape_DTW") == ROLE_INDICATOR


def test_target_derived_columns_are_not_evidence():
    """Differentiating the target does not turn it into an indicator."""
    from cyclediag.features.indicator_registry import role_of

    for col in ("dSoHQ_dN", "d2SoHQ"):
        assert role_of(col) == ROLE_TARGET
    # Q at the SOC0 landmark is min-|r| 1.0000 with dchgCapa: it *is* capacity
    assert role_of("dchg_dVdQ_SOC0_Q") == ROLE_TARGET
    assert family_of("dchg_dVdQ_SOC0_Q") == family_of("dchgCapa")


def test_sg_width_is_provenance_not_capacity():
    """``dchg_cliff_sg_width_ah`` is the smoothing window, not a cell property.

    It is ``q_span * sg_window / (n_interp - 1)``, so it tracks capacity at a
    fixed ratio. That makes it QC provenance rather than a capacity restatement,
    and it must not sit in the capacity family as if it were evidence.
    """
    from cyclediag.features.indicator_registry import role_of

    assert role_of("dchg_cliff_sg_width_ah") == ROLE_QC
    assert family_of("dchg_cliff_sg_width_ah") != family_of("dchgCapa")


def test_rejected_merges_stay_independent():
    """Pairs that were measured and failed the bar keep their own family.

    Recording them is the point: without it the next reader re-proposes the
    same merges. Numbers are pooled/per-cell min(|pearson|,|spearman|) on the
    DOE1/DOE2/DOE3/ASSB fixtures.
    """
    rejected = (
        # 0.9723 / 0.9908 / 0.9070 pooled — long-rest fit vs pulse-recovery
        # extrapolation are two estimators, not two names for one number
        ("V_inf_rest_soc80", "V_inf_est_soc80"),
        ("V_inf_rest_soc50", "V_inf_est_soc50"),
        ("V_inf_rest_soc20", "V_inf_est_soc20"),
        # per-cell 0.976: discharge-side relaxation is slower than charge-side
        ("EoD_restV_end", "EoD_restV_60s"),
        # pooled 0.996 is a between-cell temperature effect; per cell it is 0.75
        ("chg_temp_avg", "dchg_temp_avg"),
        # 0.90 pooled — normalizing by cycle duration makes a new column, which
        # is why retiring CI required CI_per_hour to exist
        ("CE", "CI_per_hour"),
        # three parameters of one CV fit, never jointly populated on any
        # fixture, so there is no evidence they are redundant
        ("tau_CV", "I_inf_norm"),
        ("tau_CV", "Q_CV_at_Tref"),
        # bands of the same curve, |r| = 0.004 between them
        ("hyst_area", "hyst_area_low"),
    )
    for a, b in rejected:
        assert family_of(a) != family_of(b), f"{a} and {b} were merged after all"


def test_resolution_axes_are_never_collapsed():
    """Criterion 3: correlation does not merge two positions on an axis.

    SOC bands, SOC points and pulse durations exist to localize degradation.
    Some of these pairs do clear the empirical bar — ``hyst_area`` and
    ``hyst_max_dV_mid`` reach per-cell 0.995 because the global loop integral
    contains the mid band — and they still must not be merged, since collapsing
    them removes the axis rather than a duplicate.
    """
    for a, b in (
        ("hyst_area", "hyst_area_mid"),
        ("hyst_area", "hyst_max_dV_mid"),
        ("hyst_area_mid", "hyst_area_high"),
        ("hyst_max_dV", "hyst_max_dV_high"),
        ("R_ohmic_soc20", "R_ohmic_soc50"),
        ("EoC_dchgR_10s", "EoC_dchgR_60s"),
        ("V_inf_rest_soc20", "V_inf_rest_soc80"),
    ):
        assert family_of(a) != family_of(b), f"{a} and {b} collapse a resolution axis"


def test_charge_side_60s_rest_does_merge():
    """The EoC counterpart of the rejected EoD 60 s merge passes at 0.998."""
    assert family_of("EoC_restV_60s") == family_of("EoC_restV_end")


# --------------------------------------------------------------------------
# pool construction
# --------------------------------------------------------------------------
def _wide_frame() -> pd.DataFrame:
    n = 12
    rng = np.random.default_rng(0)
    base = np.linspace(0.0, 1.0, n)
    return pd.DataFrame({
        "cell_id": ["A"] * n,
        "cycle": np.arange(1, n + 1),
        # target + its proxies
        "dchgCapa": 70 - base,
        "SoHQ": 100 - base,
        "dchg_E": 250 - base,
        "chgCapa": 71 - base,
        "chgCCcapa": 70 - base,
        # covariate / qc / diagnosis
        "chg_temp_avg": np.full(n, 45.0) + rng.normal(0, 0.1, n),
        "quality_score": np.full(n, 0.9),
        "LLI_pattern_score": base,
        # one family with several members
        "hyst_area": base,
        "hyst_max_dV": base * 2,
        "delta_hyst_area": base - base[0],
        # independent indicators
        "hyst_area_low": rng.normal(0, 1, n),
        "EoC_dchgR_10s": 1.0 + base,
        "EoC_dchgR_60s": 2.0 + base * 0.5,
        "R_ohmic_soc50": 0.5 + base,
    })


def test_pool_excludes_non_indicator_roles():
    df = _wide_frame()
    pool = primary_indicator_columns(df)
    for excluded in (
        "dchgCapa", "SoHQ", "dchg_E", "chgCapa", "chgCCcapa",
        "chg_temp_avg", "quality_score", "LLI_pattern_score", "cycle", "cell_id",
    ):
        assert excluded not in pool


def test_pool_keeps_exactly_one_member_per_family():
    df = _wide_frame()
    pool = primary_indicator_columns(df)
    families = [family_of(c) for c in pool]
    assert len(families) == len(set(families))
    # the hysteresis family collapses to its baseline-referenced representative
    hyst = [c for c in pool if family_of(c) == "hysteresis_global"]
    assert hyst == ["delta_hyst_area"]
    # independent indicators survive
    for kept in ("hyst_area_low", "EoC_dchgR_10s", "EoC_dchgR_60s", "R_ohmic_soc50"):
        assert kept in pool


def test_indicator_columns_is_wider_than_the_primary_pool():
    df = _wide_frame()
    assert set(primary_indicator_columns(df)) < set(indicator_columns(df))


def test_dedupe_never_nominates_a_retired_alias():
    cols = ["CE", "CI", "R_SOC_slope", "R_SOC_diff_20_80"]
    kept = dedupe_by_family(cols)
    assert set(kept) == {"CE", "R_SOC_slope"}


def test_dedupe_picks_representative_even_if_listed_last():
    kept = dedupe_by_family(["hyst_max_dV", "hyst_area"])
    assert kept == ["hyst_area"]


def test_apply_aliases_maps_legacy_tables():
    legacy = pd.DataFrame({"cycle": [1, 2], "CI": [0.5, 0.7], "R_SOC_diff_20_80": [1.0, 2.0]})
    out = apply_aliases(legacy)
    assert "CI" not in out.columns and "CE" in out.columns
    assert "R_SOC_diff_20_80" not in out.columns and "R_SOC_slope" in out.columns
    # a retired alias is dropped rather than shadowing a live column
    both = pd.DataFrame({"CE": [99.0], "CI": [1.0]})
    assert list(apply_aliases(both).columns) == ["CE"]


def test_annotate_and_report_shapes():
    screened = pd.DataFrame({"feature": ["hyst_area", "hyst_max_dV", "SoHQ"]})
    ann = annotate_indicators(screened)
    assert list(ann["role"]) == [ROLE_INDICATOR, ROLE_INDICATOR, ROLE_TARGET]
    assert ann.loc[ann["feature"] == "hyst_area", "is_family_primary"].item() is True
    assert ann.loc[ann["feature"] == "hyst_max_dV", "is_family_primary"].item() is False

    rep = registry_report(["CE", "CI", "hyst_area"])
    assert rep.loc[rep["column"] == "CI", "retired_alias_of"].item() == "CE"
    assert pd.isna(rep.loc[rep["column"] == "CE", "retired_alias_of"].item())


# --------------------------------------------------------------------------
# retired aliases must not come back
# --------------------------------------------------------------------------
def test_extractor_does_not_emit_retired_aliases():
    from cyclediag.features.lges_catalog import all_lges_feature_columns

    emitted = set(all_lges_feature_columns())
    assert not emitted & set(EXACT_ALIASES)


def test_ci_is_not_emitted_but_ci_per_hour_is():
    from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_cycle_row

    n = 40
    t = np.arange(n, dtype=float) * 60.0
    df = pd.DataFrame({
        "cycle": [1] * (2 * n),
        "step_type": ["charge"] * n + ["discharge"] * n,
        "voltage": list(np.linspace(3.0, 4.2, n)) + list(np.linspace(4.2, 3.0, n)),
        "current": [35.0] * n + [-35.0] * n,
        "charge_capacity": list(np.linspace(0, 70, n)) + [70.0] * n,
        "discharge_capacity": [0.0] * n + list(np.linspace(0, 69, n)),
        "time": list(t) + list(t + t[-1]),
        "step_time": list(t) + list(t),
    })
    row = extract_lges_cycle_row(
        df, 1, config=LgesExtractConfig(cell_id="X", enrich_assb=False, with_diagnosis=False),
    )
    assert "CI" not in row
    assert row["CE"] is not None
    assert row["CI_per_hour"] == pytest.approx(
        (100.0 - row["CE"]) / row["cycle_duration_h"], rel=1e-9,
    )


def test_ocv_drift_table_has_no_retired_alias_columns():
    from cyclediag.features.ocv_drift import compute_ocv_drift_table

    table = compute_ocv_drift_table([], pd.DataFrame({"cycle": []}))
    assert table.empty  # no blocks -> nothing to report
    # the alias names must not be reintroduced by the block builder
    import inspect

    from cyclediag.features import ocv_drift

    src = inspect.getsource(ocv_drift)
    for retired in ("ocv_spread_compression", "ocv_spread_slope", "ocv_block_id"):
        assert f'"{retired}"' not in src.split("_BROADCAST_COLS")[-1]


# --------------------------------------------------------------------------
# diagnosis configs must not score one family twice in one mode
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "config_name",
    ["mode_weights_fullcell_v1.json", "mode_weights_assb_si_v1.json"],
)
def test_mode_evidence_has_no_duplicate_family(config_name):
    cfg = json.loads((_CONFIG_DIR / config_name).read_text(encoding="utf-8"))
    for mode, mode_cfg in cfg["modes"].items():
        features = [t["feature"] for t in mode_cfg.get("evidence", [])]
        assert len(features) == len(set(features)), f"{config_name}:{mode} repeats a feature"
        families = [family_of(f) for f in features]
        dupes = {f for f in families if families.count(f) > 1}
        assert not dupes, (
            f"{config_name}:{mode} scores these indicator families twice: {sorted(dupes)}"
        )


@pytest.mark.parametrize(
    "config_name",
    ["mode_weights_fullcell_v1.json", "mode_weights_assb_si_v1.json"],
)
def test_mode_evidence_never_uses_a_retired_alias(config_name):
    cfg = json.loads((_CONFIG_DIR / config_name).read_text(encoding="utf-8"))
    for mode, mode_cfg in cfg["modes"].items():
        for term in mode_cfg.get("evidence", []):
            assert term["feature"] not in EXACT_ALIASES, (
                f"{config_name}:{mode} uses retired {term['feature']}"
            )
            assert canonical_name(term["feature"]) == term["feature"]


def test_assb_lli_ce_merge_is_score_neutral():
    """Folding CI's weight into CE must not move the LLI pattern score.

    CI was ``100 - CE`` at the same scale and the CE term used
    ``decrease_from_100``, so both terms produced identical evidence.
    """
    from cyclediag.diagnosis.pattern_scoring import load_mode_weights, score_mode_for_row

    merged = load_mode_weights(_CONFIG_DIR / "mode_weights_assb_si_v1.json")
    lli_terms = merged["modes"]["LLI"]["evidence"]
    assert [t["feature"] for t in lli_terms].count("CE") == 1
    ce_term = next(t for t in lli_terms if t["feature"] == "CE")
    assert ce_term["weight"] == pytest.approx(1.9)

    # reconstruct the pre-merge config: CE back at 1.0 plus the CI duplicate
    before = json.loads(json.dumps(merged))
    before_terms = []
    for term in before["modes"]["LLI"]["evidence"]:
        if term["feature"] == "CE":
            before_terms.append({**term, "weight": 1.0})
            before_terms.append(
                {"feature": "CI", "direction": "increase", "weight": 0.9, "scale": 2.0}
            )
        else:
            before_terms.append(term)
    before["modes"]["LLI"]["evidence"] = before_terms

    row = {
        "CE": 97.5,
        "delta_EoD_restV_end": 0.04,
        "delta_dchg_V_cutoff_margin": -0.06,
        "V_inf_est_soc50": 0.01,
    }
    after_score = score_mode_for_row(row, "LLI", merged).estimate
    before_score = score_mode_for_row({**row, "CI": 100.0 - row["CE"]}, "LLI", before).estimate
    assert after_score == pytest.approx(before_score, rel=1e-12)


def test_lam_ne_keeps_the_cv_member_that_can_carry_evidence():
    """The cv_amount fold in LAM_NE kept chgCVtime, not chgCapa_CCratio.

    ``chgCapa_CCratio`` is an absolute percent in the 92-100 range and the term
    scored it with ``decrease`` at ``scale`` 5, so ``tanh(-CCratio/5)`` was
    -1.0 on every fixture row: it could never supply positive evidence and it
    permanently reported itself as a conflicting feature.
    """
    from cyclediag.diagnosis.pattern_scoring import load_mode_weights, score_mode_for_row

    cfg = load_mode_weights(_CONFIG_DIR / "mode_weights_fullcell_v1.json")
    lam_ne = [t["feature"] for t in cfg["modes"]["LAM_NE"]["evidence"]]
    assert "chgCVtime" in lam_ne
    assert "chgCapa_CCratio" not in lam_ne
    cv_term = next(
        t for t in cfg["modes"]["LAM_NE"]["evidence"] if t["feature"] == "chgCVtime"
    )
    assert cv_term["weight"] == pytest.approx(1.3)  # 0.6 + 0.7

    # the retained member responds to the CV phase growing; the dropped one
    # would have returned the same score for both rows
    low = {"chgCVtime": 20.0, "chgCapa_CCratio": 99.0}
    high = {"chgCVtime": 300.0, "chgCapa_CCratio": 92.0}
    s_low = score_mode_for_row(low, "LAM_NE", cfg).estimate
    s_high = score_mode_for_row(high, "LAM_NE", cfg).estimate
    assert s_high > s_low


def test_dcir_decomposition_reaches_the_anomaly_pool():
    """The registry admits columns the old prefix filter dropped by name alone.

    ``_numeric_feature_cols`` only kept ``f_``/``EoC_``/``EoD_``/``chg_``/
    ``dchg_``/``delta_`` prefixes, so the whole R(t) decomposition was invisible
    to the anomaly score even though it is the most direct impedance evidence
    the pipeline produces.
    """
    from cyclediag.models.predict import anomaly_feature_cols

    n = 12
    df = pd.DataFrame({
        "cell_id": ["A"] * n,
        "cycle": np.arange(1, n + 1),
        "dchgCapa": np.linspace(70, 69, n),
        "R_ohmic_soc50": np.linspace(0.5, 0.7, n),
        "R_ct_soc50": np.linspace(1.0, 1.4, n),
        "R_diff_frac_soc50": np.linspace(0.2, 0.3, n),
        "R_SOC_slope": np.linspace(-0.01, -0.02, n),
    })
    pool = anomaly_feature_cols(df)
    for col in ("R_ohmic_soc50", "R_ct_soc50", "R_diff_frac_soc50", "R_SOC_slope"):
        assert col in pool
    assert "dchgCapa" not in pool
