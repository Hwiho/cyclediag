"""Indicator scoring track — separate from causal diagnosis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cyclediag.models.indicator_scoring import (
    attach_protocol_flags,
    filter_scoring_rows,
    score_indicators,
    top_scored_indicators,
)
from cyclediag.models.predict import predict_features


def _cell_frame(n: int = 40) -> pd.DataFrame:
    cyc = np.arange(1, n + 1)
    # slow drift on two independent indicators; capacity is a target
    return pd.DataFrame({
        "cell_id": ["X"] * n,
        "cycle": cyc,
        "SoHQ": 100 - 0.2 * cyc,
        "dchgCapa": 70 - 0.1 * cyc,
        "hyst_area": 0.5 + 0.01 * cyc,
        "hyst_max_dV": 0.1 + 0.002 * cyc,  # same family as hyst_area
        "EoC_dchgR_10s": 0.1 + 0.001 * cyc,
        "VE": 0.90 - 0.001 * cyc,
        "protocol_kind": ["routine"] * n,
        "protocol_excluded": [False] * n,
    })


def test_score_indicators_one_per_family_and_no_mode_labels():
    df = _cell_frame()
    res = score_indicators(df, routine_only=True)
    assert not res.indicator_summary.empty
    assert res.meta["score_layer"] == "indicator"
    assert "diagnosis" in res.meta["causal_track"] or "separate" in res.meta["causal_track"]

    fams = list(res.indicator_summary["family"])
    assert len(fams) == len(set(fams))
    # hysteresis collapses to one representative
    hyst = res.indicator_summary[
        res.indicator_summary["family"] == "hysteresis_global"
    ]
    assert len(hyst) == 1
    # no causal mode columns
    for bad in ("LLI", "LAM_PE", "LAM_NE", "degradation_mode", "pattern_score"):
        assert bad not in res.indicator_summary.columns
        assert bad not in res.cycle_scores.columns


def test_routine_only_drops_rpt_spikes():
    df = _cell_frame(30)
    # inject an RPT spike on resistance
    df.loc[10, "protocol_kind"] = "rpt"
    df.loc[10, "EoC_dchgR_10s"] = 50.0
    df.loc[11:15, "protocol_kind"] = "post_rpt"
    df.loc[11:15, "protocol_excluded"] = True
    df.loc[11:15, "EoC_dchgR_10s"] = 40.0

    res = score_indicators(df, routine_only=True)
    scored = res.cycle_scores[res.cycle_scores["scoring_row"]]
    assert set(scored["protocol_kind"].astype(str)) == {"routine"}
    assert int(res.meta["n_scored_rows"]) == 24  # 30 - 1 rpt - 5 post_rpt

    # the spike cycle must not receive an indicator_score
    spike = res.cycle_scores.loc[10]
    assert bool(spike["scoring_row"]) is False
    assert pd.isna(spike["indicator_score"])


def test_filter_keeps_unknown_when_no_protocol_detected():
    df = _cell_frame(10).drop(columns=["protocol_kind", "protocol_excluded"])
    tagged = attach_protocol_flags(df, raw_df=None)
    kept = filter_scoring_rows(tagged, routine_only=True)
    assert len(kept) == 10


def test_predict_features_uses_indicator_track():
    df = _cell_frame()
    out = predict_features(df, routine_only=True)
    assert "anomaly_score" in out.columns
    assert "indicator_score" in out.columns
    # historical aliases mirror the indicator track
    m = out["scoring_row"]
    assert np.allclose(
        out.loc[m, "anomaly_score"].astype(float),
        out.loc[m, "indicator_score"].astype(float),
        equal_nan=True,
    )


def test_top_scored_indicators_respects_family():
    summary = pd.DataFrame({
        "feature": ["hyst_area", "hyst_max_dV", "VE"],
        "family": ["hysteresis_global", "hysteresis_global", "VE"],
        "indicator_score": [0.9, 0.8, 0.7],
    })
    top = top_scored_indicators(summary, n=5, min_score=0.0)
    assert list(top["feature"]) == ["hyst_area", "VE"]


def test_targets_do_not_enter_the_score_pool():
    df = _cell_frame()
    res = score_indicators(df)
    features = set(res.indicator_summary["feature"])
    assert "SoHQ" not in features
    assert "dchgCapa" not in features
    # contributions also skip targets
    if not res.cycle_contributions.empty:
        assert "SoHQ" not in set(res.cycle_contributions["feature"])
