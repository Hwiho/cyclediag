"""Tests for absolute-Ah cliff metrics (H1/H2 synthetic discrimination)."""

from __future__ import annotations

import numpy as np
import pytest

from cyclediag.features.cliff_metrics import compute_cliff_metrics


def _synth_curve(c_gr: float, c_si: float) -> tuple[np.ndarray, np.ndarray]:
    q = np.linspace(0, c_gr + c_si, 1200)
    v = np.where(
        q < c_gr,
        4.10 - 0.35 * (q / c_gr),
        3.75 - 0.60 * ((q - c_gr) / max(c_si, 1e-9)),
    )
    tail = q >= c_gr + c_si - 2.0
    v = np.asarray(v, dtype=float)
    v[tail] -= 1.2 * ((q[tail] - (c_gr + c_si - 2.0)) / 2.0) ** 2
    return q, v


def test_h1_q_cliff_abs_stable_when_si_fades():
    cliffs = []
    for csi in (32, 24, 16, 8):
        m = compute_cliff_metrics(*_synth_curve(40.0, float(csi)))
        assert m["cliff_valid"], f"csi={csi}"
        cliffs.append(m["Q_cliff_abs"])
    cv = float(np.std(cliffs) / (np.mean(cliffs) + 1e-9))
    assert cv < 0.10, f"H1 CV={cv:.3f}, cliffs={cliffs}"


def test_h2_q_cliff_abs_scales_with_f():
    qs = []
    fs = [1.0, 0.75, 0.5, 0.25]
    for f in fs:
        m = compute_cliff_metrics(*_synth_curve(40.0 * f, 32.0 * f))
        assert m["cliff_valid"]
        qs.append(m["Q_cliff_abs"])
    coef = np.polyfit(fs, qs, 1)
    pred = np.polyval(coef, fs)
    ss_res = float(np.sum((np.array(qs) - pred) ** 2))
    ss_tot = float(np.sum((np.array(qs) - np.mean(qs)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    assert r2 > 0.95, f"H2 R²={r2:.3f}, qs={qs}"


def test_q_tail_decreases_when_si_fades_h1():
    m32 = compute_cliff_metrics(*_synth_curve(40.0, 32.0))
    m8 = compute_cliff_metrics(*_synth_curve(40.0, 8.0))
    assert m32["Q_tail_abs"] > m8["Q_tail_abs"]
