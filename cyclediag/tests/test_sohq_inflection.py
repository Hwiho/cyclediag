"""Tests for SoHQ inflection / regime detection."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.analysis.sohq_inflection import (
    detect_sohq_inflections,
    plot_sohq_inflection_report,
)


def _piecewise_fade(n: int = 200) -> pd.DataFrame:
    """Three-regime fade: slow → fast → slower."""
    x = np.arange(1, n + 1, dtype=float)
    y = np.empty(n)
    # regime 1: -0.02%/cyc → -2%/100cyc
    y[:60] = 100 - 0.02 * x[:60]
    # regime 2: -0.12%/cyc
    y[60:140] = y[59] - 0.12 * (x[60:140] - x[59])
    # regime 3: -0.04%/cyc
    y[140:] = y[139] - 0.04 * (x[140:] - x[139])
    y = y + np.random.default_rng(0).normal(0, 0.05, size=n)
    return pd.DataFrame({
        "cell_id": "synth",
        "cycle": x,
        "tagged_cycle": x,
        "SoHQ": y,
    })


def test_detect_piecewise_inflections():
    df = _piecewise_fade()
    result = detect_sohq_inflections(df, max_breaks=2, method="piecewise", min_seg_points=20)
    assert result is not None
    assert len(result.inflections) >= 1
    assert len(result.regimes) >= 2
    # breakpoints near 60 and 140
    bps = sorted(
        (bp.tagged_cycle if bp.tagged_cycle is not None else bp.cycle)
        for bp in result.inflections
    )
    assert any(abs(b - 60) < 15 for b in bps)


def test_hybrid_prefers_major_fade_regimes():
    """Hybrid should recover steep-mid / gentle-late regimes (not early noise)."""
    x = np.arange(1, 501, dtype=float)
    y = np.empty_like(x)
    y[:260] = 100 - 0.045 * x[:260]
    y[260:410] = y[259] - 0.10 * (x[260:410] - x[259])
    y[410:] = y[409] - 0.05 * (x[410:] - x[409])
    y = y + np.random.default_rng(1).normal(0, 0.08, size=len(x))
    df = pd.DataFrame({"cell_id": "t", "cycle": x, "tagged_cycle": x, "SoHQ": y})
    result = detect_sohq_inflections(df, max_breaks=2, method="hybrid", min_seg_points=40)
    assert result is not None
    bps = sorted(bp.tagged_cycle or bp.cycle for bp in result.inflections)
    assert len(bps) == 2
    assert abs(bps[0] - 260) < 25
    assert abs(bps[1] - 410) < 25
    slopes = [r.slope_pct_per_100cyc for r in result.regimes]
    assert slopes[1] < slopes[0]  # mid steeper (more negative)
    assert slopes[2] > slopes[1]  # late gentler than mid


def test_rank_sohq_drivers_by_regime():
    from cyclediag.analysis.regime_singularity import rank_sohq_drivers_by_regime

    x = np.arange(1, 301, dtype=float)
    # three regimes with different drivers
    eoc = 4.2 - 0.0001 * x
    eod = 3.0 + 0.0002 * x
    r10 = 10 + 0.01 * x
    # SoHQ piecewise
    sohq = np.empty_like(x)
    sohq[:100] = 100 - 0.05 * x[:100]
    sohq[100:200] = sohq[99] - 0.12 * (x[100:200] - 100)
    sohq[200:] = sohq[199] - 0.04 * (x[200:] - 200)
    df = pd.DataFrame({
        "cell_id": "t",
        "cycle": x,
        "tagged_cycle": x,
        "SoHQ": sohq,
        "EoC_restV_end": eoc,
        "EoD_restV_end": eod,
        "EoC_dchgR_10s": r10,
    })
    out = rank_sohq_drivers_by_regime(df, breakpoints=[100.0, 200.0], top_n=3)
    assert not out.empty
    assert set(out["regime"]) == {"S1", "S2", "S3"}
    assert out.groupby("regime").size().min() >= 1
