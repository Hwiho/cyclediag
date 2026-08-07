"""Unit tests for DOE2 arm comparison helpers (no large fixture IO)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.analysis.doe_compare import (
    compare_arms_late_spread,
    early_fade_rates,
    early_parameter_summary,
    mechanism_contrast_narrative,
)


def _fake_features() -> pd.DataFrame:
    rows = []
    for arm, anode_shift in (("SJ900_dry", 0.0), ("SJ1300_dry", -2.0)):
        for cell_i, cell in enumerate((f"{arm}_c1", f"{arm}_c2")):
            for cyc in range(1, 41):
                rows.append(
                    {
                        "arm": arm,
                        "cell_id": cell,
                        "cycle": cyc,
                        "SoHQ": 100.0 + anode_shift - 0.05 * cyc - 0.01 * cell_i,
                        "CE": 0.995 + 0.001 * anode_shift / 10,
                        "EoD_chgR_30s": 1.0 + 0.01 * cyc - anode_shift * 0.05,
                        "hyst_mean": 0.02 - anode_shift * 0.002,
                        "dchg_dQdV_peak1_V": 3.6 + anode_shift * 0.01,
                    }
                )
    return pd.DataFrame(rows)


def test_early_parameter_summary_has_delta():
    early = early_parameter_summary(_fake_features(), early_cycles=20)
    assert not early.empty
    assert any(str(a).startswith("delta:") for a in early["arm"])


def test_early_fade_rates_arm_mean():
    fade = early_fade_rates(_fake_features(), early_cycles=20)
    assert "dSoHQ_dN_early" in set(fade["metric"])
    arm_means = fade[fade["cell_id"] == "__arm_mean__"]
    assert len(arm_means) == 2


def test_late_spread_ranks_indicators():
    late = compare_arms_late_spread(_fake_features(), late_frac=0.25)
    assert not late.empty
    assert "SoHQ" in set(late["indicator"]) or "EoD_chgR_30s" in set(late["indicator"])


def test_narrative_mentions_cathode_control():
    early = early_parameter_summary(_fake_features(), early_cycles=20)
    late = compare_arms_late_spread(_fake_features())
    lines = mechanism_contrast_narrative(early, pd.DataFrame(), late)
    assert any("cathode" in x.lower() for x in lines)
