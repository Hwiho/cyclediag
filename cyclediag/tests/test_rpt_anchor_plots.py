"""Smoke tests for RPT anchor plot builders."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.dqdv_segment import (
    exclude_dcir_pulse_rows,
    split_capacity_runs,
    stitch_capacity_runs,
)
from cyclediag.features.rpt_anchor_plots import (
    merge_rpt_block_vq,
    plot_assign_trajectory,
    plot_confidence_strip,
    plot_residual_mv,
    plot_rpt_routine_dqdv_overlay,
)


def _sample_assign() -> pd.DataFrame:
    rows = []
    for cyc in range(90, 111):
        zone = "hard" if abs(cyc - 100) <= 10 else "soft"
        for pid, v0 in (("P2_shoulder", 3.78), ("P3_main", 3.86)):
            rows.append({
                "cycle": cyc,
                "leg": "charge",
                "peak_id": pid,
                "V_expected": v0 + (cyc - 100) * 0.0001,
                "V_observed": v0 + (cyc - 100) * 0.0001 + 0.01,
                "assign_zone": zone,
                "assign_confidence": 0.9 if zone == "hard" else 0.6,
            })
    return pd.DataFrame(rows)


def test_plot_assign_trajectory_figure():
    fig = plot_assign_trajectory(
        _sample_assign(),
        meta={"checkpoints": [{"life_cycle": 100}]},
    )
    assert len(fig.axes) == 1
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_plot_residual_and_confidence():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = _sample_assign()
    fig1 = plot_residual_mv(df)
    fig2 = plot_confidence_strip(df)
    plt.close(fig1)
    plt.close(fig2)


def test_stitch_capacity_runs_recovers_full_discharge_vspan():
    """Fragmented high/mid/low V runs should stitch to ~full discharge span."""
    runs = [
        (np.linspace(4.08, 3.66, 80), np.linspace(0.0, 12.0, 80)),
        (np.linspace(3.85, 3.26, 90), np.linspace(0.0, 18.0, 90)),
        (np.linspace(3.48, 2.50, 100), np.linspace(0.0, 20.0, 100)),
    ]
    stitched = stitch_capacity_runs(runs, leg="discharge")
    assert stitched is not None
    v, q = stitched
    assert float(np.nanmax(v)) > 4.0
    assert float(np.nanmin(v)) < 2.6
    assert float(q[-1]) > float(q[0])


def test_exclude_dcir_pulse_rows_keeps_cc_only():
    # CC ~26A then DC-IR pulse ~77A
    n_cc, n_pulse = 100, 20
    rows = []
    for i in range(n_cc):
        rows.append({"voltage": 4.0 - i * 0.002, "current": -25.8, "discharge_capacity": i * 0.2})
    for i in range(n_pulse):
        rows.append({"voltage": 3.8 - i * 0.001, "current": -77.3, "discharge_capacity": i * 0.03})
    seg = pd.DataFrame(rows)
    out = exclude_dcir_pulse_rows(seg)
    assert len(out) == n_cc
    assert float(out["current"].abs().max()) < 30.0


def test_merge_rpt_block_vq_and_overlay_smoke():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = []
    # TC1: high-V discharge chunk
    for vv, qq in zip(np.linspace(4.05, 3.70, 60), np.linspace(0.1, 10.0, 60)):
        rows.append({
            "cycle": 1, "step_type": "discharge", "voltage": vv,
            "discharge_capacity": qq, "charge_capacity": 0.0,
        })
    # TC2: low-V discharge chunk
    for vv, qq in zip(np.linspace(3.65, 2.55, 80), np.linspace(0.0, 15.0, 80)):
        rows.append({
            "cycle": 2, "step_type": "discharge", "voltage": vv,
            "discharge_capacity": qq, "charge_capacity": 0.0,
        })
    # Routine full discharge
    for vv, qq in zip(np.linspace(4.0, 2.5, 120), np.linspace(0.1, 50.0, 120)):
        rows.append({
            "cycle": 10, "step_type": "discharge", "voltage": vv,
            "discharge_capacity": qq, "charge_capacity": 0.0,
        })
    df = pd.DataFrame(rows)
    vq = merge_rpt_block_vq(df, [1, 2], "discharge")
    assert vq is not None
    assert float(np.nanmax(vq[0])) > 3.9
    assert float(np.nanmin(vq[0])) < 2.7

    fig = plot_rpt_routine_dqdv_overlay(
        df,
        routine_cycle=10,
        rpt_cycle=2,
        rpt_cycles=[1, 2],
        leg="discharge",
    )
    plt.close(fig)
