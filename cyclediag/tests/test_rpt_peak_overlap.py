"""Tests for 0.33C→0.5C peak overlap / collapse soft-map."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.rpt_anchor import RptCheckpoint, RptPeakRef, RateShift
from cyclediag.features.rpt_peak_overlap import (
    RptOverlapConfig,
    best_rpt_links,
    detect_collapses,
    train_rpt_overlap_model,
)
from cyclediag.io.cycle_protocol import ProtocolExclusion


def test_detect_collapses_two_rpt_share_one_cand():
    soft = pd.DataFrame([
        {
            "life_cycle": 100, "routine_cycle": 100, "leg": "discharge",
            "cand_idx": 0, "cand_V": 3.75, "cand_H": -60,
            "rpt_peak_id": "P2_mid", "rpt_V": 3.72, "rpt_H": -50,
            "V_expected_0p5": 3.74, "delta_v": 0.01,
            "geom_score": 0.9, "rf_proba": 0.6, "score": 0.7,
        },
        {
            "life_cycle": 100, "routine_cycle": 100, "leg": "discharge",
            "cand_idx": 0, "cand_V": 3.75, "cand_H": -60,
            "rpt_peak_id": "P3_high", "rpt_V": 3.88, "rpt_H": -55,
            "V_expected_0p5": 3.90, "delta_v": -0.15,
            "geom_score": 0.4, "rf_proba": 0.5, "score": 0.45,
        },
        {
            "life_cycle": 100, "routine_cycle": 100, "leg": "discharge",
            "cand_idx": 1, "cand_V": 3.15, "cand_H": -40,
            "rpt_peak_id": "P1_low", "rpt_V": 3.13, "rpt_H": -40,
            "V_expected_0p5": 3.14, "delta_v": 0.01,
            "geom_score": 0.95, "rf_proba": 0.8, "score": 0.85,
        },
    ])
    col = detect_collapses(soft, config=RptOverlapConfig(collapse_score_min=0.2, share_frac_of_best=0.5))
    assert len(col) == 1
    assert set(col.iloc[0]["rpt_peak_ids"].split(",")) == {"P2_mid", "P3_high"}


def test_best_rpt_links_picks_max_score():
    soft = pd.DataFrame([
        {
            "life_cycle": 100, "routine_cycle": 100, "leg": "charge",
            "cand_idx": 0, "cand_V": 3.8, "cand_H": 80,
            "rpt_peak_id": "P2_shoulder", "rpt_V": 3.78, "rpt_H": 90,
            "V_expected_0p5": 3.8, "delta_v": 0.0,
            "geom_score": 1.0, "rf_proba": 0.9, "score": 0.9,
        },
        {
            "life_cycle": 100, "routine_cycle": 100, "leg": "charge",
            "cand_idx": 1, "cand_V": 3.9, "cand_H": 70,
            "rpt_peak_id": "P2_shoulder", "rpt_V": 3.78, "rpt_H": 90,
            "V_expected_0p5": 3.8, "delta_v": 0.1,
            "geom_score": 0.4, "rf_proba": 0.2, "score": 0.3,
        },
    ])
    links = best_rpt_links(soft)
    assert len(links) == 1
    assert int(links.iloc[0]["cand_idx"]) == 0


def test_train_overlap_rf_two_classes():
    rows = []
    for i in range(20):
        rows.append({
            "source": "rpt_0p33", "life_cycle": 100, "cycle": 108, "leg": "discharge",
            "peak_id": "P1_low", "V": 3.13 + 0.01 * np.random.randn(),
            "H": -50 + np.random.randn(), "rate_c": 0.33, "V_expected": 3.13,
        })
        rows.append({
            "source": "rpt_0p33", "life_cycle": 100, "cycle": 108, "leg": "discharge",
            "peak_id": "P2_mid", "V": 3.72 + 0.01 * np.random.randn(),
            "H": -55 + np.random.randn(), "rate_c": 0.33, "V_expected": 3.72,
        })
    train = pd.DataFrame(rows)
    shifts = [RateShift(100, "discharge", "P1_low", 5.0), RateShift(100, "discharge", "P2_mid", 8.0)]
    bundle = train_rpt_overlap_model(train, shifts, config=RptOverlapConfig(n_estimators=20))
    assert "discharge" in bundle.rf_models
    assert set(bundle.peak_ids["discharge"]) == {"P1_low", "P2_mid"}
