"""Tests for routine / C/3 RPT / DCIR cycle role tagging."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.cycle_roles import (
    attach_cycle_roles,
    classify_cycle_currents,
    summarize_rpt_anchors,
)
from cyclediag.features.fade_trajectory import attach_fade_trajectory


def _fake_raw(cycles_currents: list[tuple[int, float]]) -> pd.DataFrame:
    rows = []
    for cyc, i_cc in cycles_currents:
        # short synthetic discharge + charge legs
        for i in (i_cc, -i_cc, i_cc * 0.02):
            rows.append({"cycle": cyc, "current": i, "voltage": 3.7})
    return pd.DataFrame(rows)


def test_classify_routine_vs_rpt_vs_pulse():
    raw = _fake_raw([
        (10, 38.7),   # 0.5C routine
        (107, 25.8),  # C/3 RPT
        (108, 25.8),
        (109, 77.0),  # 1C DCIR (max)
    ])
    # bump pulse cycle max via extra samples
    raw = pd.concat([raw, pd.DataFrame({"cycle": [109], "current": [77.0], "voltage": [3.5]})], ignore_index=True)
    roles = classify_cycle_currents(raw, q_nominal_ah=72.0).set_index("cycle")
    assert roles.loc[10, "cycle_role"] == "routine_05c"
    assert roles.loc[107, "cycle_role"] == "rpt_c3"
    assert roles.loc[108, "cycle_role"] == "rpt_c3"
    assert roles.loc[109, "cycle_role"] == "dcir_pulse"


def test_fade_excludes_rpt_bumps():
    # Smooth routine fade + RPT bumps that would bias knee if mixed
    cycles = list(range(1, 201))
    sohq = [100 - 0.05 * c for c in cycles]
    for c in (50, 100, 150):
        sohq[c - 1] = sohq[c - 1] + 8.0  # fake RPT bump
    feats = pd.DataFrame({"cycle": cycles, "SoHQ": sohq, "capa_Ah": [70.0] * len(cycles)})
    raw_rows = []
    for c in cycles:
        i = 25.8 if c in (50, 100, 150) else 38.7
        raw_rows.append({"cycle": c, "current": i})
        raw_rows.append({"cycle": c, "current": -i})
    raw = pd.DataFrame(raw_rows)
    feats, _ = attach_cycle_roles(feats, raw)
    out = attach_fade_trajectory(feats)
    # Without RPT exclusion the bump train looks flatter / noisier; with exclusion
    # fade still recovers a positive exponent on the routine trend.
    assert out["fade_exponent_b"].notna().all()
    assert float(out["fade_exponent_b"].iloc[0]) > 0.2
    assert feats["SoHQ_rpt_c3"].notna().sum() == 3
    assert feats["SoHQ_routine"].notna().sum() == 197


def test_summarize_rpt_anchors_gap():
    feats = pd.DataFrame({
        "cycle": [10, 11, 107, 108],
        "SoHQ": [95.0, 94.5, 102.0, 101.5],
        "cycle_role": ["routine_05c", "routine_05c", "rpt_c3", "rpt_c3"],
        "C_rate_med_est": [0.5, 0.5, 0.33, 0.33],
        "I_abs_med_cc": [38.7, 38.7, 25.8, 25.8],
    })
    anchors = summarize_rpt_anchors(feats)
    assert len(anchors) == 2
    assert anchors.iloc[0]["cycle"] == 107
    assert anchors.iloc[0]["SoHQ_gap_vs_prev_routine"] == 102.0 - 94.5
