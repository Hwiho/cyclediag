"""Tests for Q-axis dQ/dV peak detection (500-pt grid)."""

from __future__ import annotations

import numpy as np
import pytest

from cyclediag.features.dqdv_peaks import (
    DEFAULT_DQDV_PEAK_CONFIG,
    DqdvPeakConfig,
    dvdq_intensity_at_soc,
    find_dqdv_peaks,
    prepare_dqdv_arrays,
)


def _synthetic_charge_leg(n: int = 200, peak_v: float = 3.55, peak_h: float = 80.0):
    v = np.linspace(3.0, 4.15, n)
    q = 55 * (1 - np.exp(-(v - 3.0) / 0.32))
    dqdv = 80 * np.exp(-((v - peak_v) ** 2) / (2 * 0.018**2))
    q = q + np.cumsum(dqdv) * (v[1] - v[0])
    return v, q


def test_prepare_dqdv_uses_q_interp_500_points():
    v, q = _synthetic_charge_leg()
    cfg = DqdvPeakConfig(n_interp=500, interp_axis="Q")
    vx, dqdv, qx, _ = prepare_dqdv_arrays(v, q, cfg)
    assert 100 <= len(vx) <= 500
    assert np.isfinite(dqdv).sum() > 100


def test_find_main_peak_near_expected_voltage():
    v, q = _synthetic_charge_leg(peak_v=3.55)
    peaks = find_dqdv_peaks(v, q, config=DEFAULT_DQDV_PEAK_CONFIG)
    assert len(peaks) >= 1
    assert peaks[0]["V"] == pytest.approx(3.55, abs=0.04)


def test_noise_spikes_suppressed():
    v, q = _synthetic_charge_leg()
    rng = np.random.default_rng(0)
    for _ in range(40):
        i = int(rng.integers(20, len(v) - 20))
        if abs(v[i] - 3.55) < 0.08:
            continue
        q[i] += rng.uniform(0.02, 0.08)

    peaks = find_dqdv_peaks(v, q, max_peaks=3, config=DEFAULT_DQDV_PEAK_CONFIG)
    assert len(peaks) >= 1
    best = max(peaks, key=lambda p: abs(p["H"]))
    assert best["V"] == pytest.approx(3.55, abs=0.06)


def test_discharge_capacity_reset_falls_back_to_v_axis():
    """Mid-leg Q counter reset must not collapse discharge dQ/dV voltage span."""
    v_hi = np.linspace(3.49, 3.05, 94)
    q_hi = np.linspace(0.1, 20.67, 94)
    v_lo = np.linspace(3.24, 2.50, 100)
    q_lo = np.linspace(0.0, 13.13, 100)
    v = np.concatenate([v_hi, v_lo])
    q = np.concatenate([q_hi, q_lo])
    cfg = DqdvPeakConfig(n_interp=500, interp_axis="Q")
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, cfg)
    assert len(vx) > 200
    assert float(np.nanmin(vx)) < 2.8
    assert float(np.nanmax(vx)) > 3.3
    assert np.isfinite(dqdv).sum() > 200


def test_close_peaks_are_merged():
    v = np.linspace(3.0, 4.0, 300)
    q = 50 * (1 - np.exp(-(v - 3.0) / 0.25))
    bump = 40 * np.exp(-((v - 3.52) ** 2) / (2 * 0.01**2))
    bump += 35 * np.exp(-((v - 3.525) ** 2) / (2 * 0.008**2))
    q = q + np.cumsum(bump) * (v[1] - v[0])
    peaks = find_dqdv_peaks(v, q, max_peaks=4, config=DEFAULT_DQDV_PEAK_CONFIG)
    vs = [p["V"] for p in peaks]
    for i in range(len(vs) - 1):
        assert abs(vs[i + 1] - vs[i]) >= 0.01 or len(peaks) <= 2


def test_dvdq_soc0_intensity_on_discharge():
    # discharge: V decreases as Q increases; steep cliff near end (SOC0)
    n = 250
    q = np.linspace(0.0, 100.0, n)
    v = 4.1 - 0.8 * (q / 100.0) - 0.6 * np.exp(-((q - 98.0) ** 2) / (2 * 1.2**2))
    sample = dvdq_intensity_at_soc(q, v, soc_target=0.0, soc_window=0.03, discharge=True)
    assert sample["intensity"] is not None
    assert sample["intensity"] > 0
    assert sample["SOC"] is not None and sample["SOC"] <= 0.03
    mid = dvdq_intensity_at_soc(q, v, soc_target=0.5, soc_window=0.03, discharge=True)
    assert sample["intensity"] > mid["intensity"]
