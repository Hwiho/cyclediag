"""Tests for ML peak assign."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.dqdv_peaks import DqdvPeakConfig
from cyclediag.features.peak_assign import (
    PeakAssignBundle,
    assign_peaks_for_leg,
    train_peak_assign_from_long,
)


def _golden_long() -> pd.DataFrame:
    rows = []
    for tc in (10, 50, 80):
        rows.extend([
            {"cycle": tc, "leg": "charge", "band": "P1_low", "V": 3.55, "H": 90.0, "usable_leg": True},
            {"cycle": tc, "leg": "charge", "band": "P2_shoulder", "V": 3.75, "H": 85.0, "usable_leg": True},
            {"cycle": tc, "leg": "charge", "band": "P3_main", "V": 3.90, "H": 88.0, "usable_leg": True},
            {"cycle": tc, "leg": "discharge", "band": "P1_low", "V": 3.15, "H": -60.0, "usable_leg": True},
            {"cycle": tc, "leg": "discharge", "band": "P2_mid", "V": 3.68, "H": -62.0, "usable_leg": True},
            {"cycle": tc, "leg": "discharge", "band": "P3_high", "V": 3.92, "H": -70.0, "usable_leg": True},
        ])
    return pd.DataFrame(rows)


def test_train_peak_assign_bundle():
    bundle = train_peak_assign_from_long(_golden_long(), good_cycles=[10, 50, 80])
    assert isinstance(bundle, PeakAssignBundle)
    assert bundle.train_rows > 0
    assert "charge" in bundle.rf_models
    assert not bundle.centroids.empty


def test_hungarian_assign_peaks():
    from cyclediag.features.peak_assign import (
        PeakAssignBundle,
        PeakAssignConfig,
        hungarian_assign_peaks,
        train_peak_assign_from_long,
    )

    bundle = train_peak_assign_from_long(_golden_long(), good_cycles=[10, 50, 80])
    candidates = [
        {"V": 3.55, "H": 88.0},
        {"V": 3.75, "H": 84.0},
        {"V": 3.90, "H": 86.0},
    ]
    refs = bundle.centroids[bundle.centroids["leg"] == "charge"]
    out = hungarian_assign_peaks(candidates, refs, bundle=bundle, leg="charge")
    assert len(out) >= 2
    assert all(p["assign_method"] == "hungarian" for p in out)


def test_train_peak_assign_multi():
    from cyclediag.features.peak_assign import PeakAssignSample, train_peak_assign_multi

    s1 = PeakAssignSample("A", _golden_long(), [10, 50, 80])
    s2 = PeakAssignSample("B", _golden_long(), [10, 50, 80])
    bundle = train_peak_assign_multi([s1, s2])
    assert bundle.train_rows > 0
    assert set(bundle.training_cells) == {"A", "B"}


def test_hybrid_assign_on_synthetic_leg():
    bundle = train_peak_assign_from_long(_golden_long(), good_cycles=[10, 50, 80])
    n = 200
    v = np.linspace(3.0, 4.1, n)
    q = 55 * (1 - np.exp(-(v - 3.0) / 0.32))
    for peak_v, h in ((3.55, 80.0), (3.75, 75.0), (3.90, 78.0)):
        q += np.cumsum(h * np.exp(-((v - peak_v) ** 2) / (2 * 0.02**2))) * (v[1] - v[0])

    peaks = assign_peaks_for_leg(
        v,
        q,
        "charge",
        dqcfg=DqdvPeakConfig(sg_window=21, n_interp=300),
        bundle=bundle,
        assign_mode="hybrid",
    )
    assert len(peaks) >= 2
    ids = {p.get("band") for p in peaks}
    assert "P3_main" in ids or "P2_shoulder" in ids
