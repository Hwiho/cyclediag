"""Smoke test for SoHQ BP presentation tool (synthetic, no raw fixtures)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.analysis.sohq_inflection import detect_sohq_inflections
from cyclediag.tools import run_sohq_bp_presentation as mod


def test_plot_sohq_regimes_writes(tmp_path):
    x = np.arange(1, 301, dtype=float)
    y = np.empty_like(x)
    y[:120] = 100 - 0.04 * x[:120]
    y[120:220] = y[119] - 0.12 * (x[120:220] - 120)
    y[220:] = y[219] - 0.05 * (x[220:] - 220)
    y = y + np.random.default_rng(0).normal(0, 0.05, size=len(x))
    df = pd.DataFrame(
        {"cell_id": "synth", "cycle": x, "tagged_cycle": x, "SoHQ": y}
    )
    out = tmp_path / "regimes.png"
    info = mod.plot_sohq_regimes(df, out, title="synth")
    assert out.is_file()
    assert info.get("bp1") is not None
    assert len(info.get("regimes") or []) >= 2
    assert (tmp_path / "regimes_regimes.csv").is_file()


def test_detect_two_breaks_on_piecewise():
    x = np.arange(1, 401, dtype=float)
    y = np.empty_like(x)
    y[:150] = 100 - 0.03 * x[:150]
    y[150:280] = y[149] - 0.11 * (x[150:280] - 150)
    y[280:] = y[279] - 0.04 * (x[280:] - 280)
    df = pd.DataFrame(
        {"cell_id": "t", "cycle": x, "tagged_cycle": x, "SoHQ": y}
    )
    res = detect_sohq_inflections(df, max_breaks=2, method="piecewise", min_seg_points=40)
    assert res is not None
    assert len(res.inflections) == 2
    assert len(res.regimes) == 3
