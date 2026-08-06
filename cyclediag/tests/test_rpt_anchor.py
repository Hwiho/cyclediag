"""Tests for RPT-anchored peak assign."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cyclediag.features.rpt_anchor import (
    RptAnchorConfig,
    RptCheckpoint,
    RptPeakRef,
    RateShift,
    _bracket_checkpoints,
    _zone,
    assign_routine_cycle,
    discover_rpt_checkpoints,
    infer_checkpoint_life,
    interpolate_expected_v,
)
from cyclediag.io.cycle_protocol import ProtocolExclusion, build_protocol_exclusion


def _step_row(cycle: int, dchg_mah: float, n_steps: int = 4, i_abs: float = 1000.0) -> pd.DataFrame:
    rows = []
    for i in range(n_steps):
        st = ["charge", "rest", "discharge", "rest"][i % 4] if n_steps == 4 else "charge"
        dchg = dchg_mah if st == "discharge" else 0.0
        if st == "charge":
            cur = i_abs
        elif st == "discharge":
            cur = -i_abs
        else:
            cur = 0.0
        rows.append({
            "cycle": cycle,
            "step_type": st,
            "discharge_capacity": dchg,
            "current": cur,
        })
    return pd.DataFrame(rows)


def _capacheck_block(start: int) -> pd.DataFrame:
    parts = []
    for cyc, n_steps, dchg in [
        (start, 8, 14000),
        (start + 1, 6, 21000),
        (start + 2, 6, 21000),
    ]:
        parts.append(_step_row(cyc, dchg, n_steps=n_steps, i_abs=25.8))
    return pd.concat(parts, ignore_index=True)


def _synthetic_raw_df(cycles: list[int]) -> pd.DataFrame:
    """Minimal raw rows with charge/discharge legs for peak band assign."""
    rows = []
    for cyc in cycles:
        for leg, v_base in (("charge", 3.6), ("discharge", 3.2)):
            for i in range(120):
                q = i * 0.5
                v = v_base + q * 0.003
                if leg == "charge" and 60 < i < 80:
                    v += 0.05 * np.sin((i - 60) * 0.3)
                rows.append({
                    "cycle": cyc,
                    "step_type": leg,
                    "voltage": v,
                    "capacity": q,
                    "charge_capacity": q if leg == "charge" else 0.0,
                    "discharge_capacity": q if leg == "discharge" else 0.0,
                    "step_time": float(i),
                    "total_time": float(i + cyc * 1000),
                })
    return pd.DataFrame(rows)


def test_infer_checkpoint_life():
    assert infer_checkpoint_life(4) == 1
    assert infer_checkpoint_life(109) == 100
    assert infer_checkpoint_life(214) == 200
    assert infer_checkpoint_life(529) == 500


def test_discover_rpt_checkpoints():
    # 0.5C routine + two 0.33C full capa + DC-IR block (M01Ch022 pattern)
    parts = [_step_row(c, 66000.0, i_abs=38.7) for c in range(90, 107)]
    parts.append(_step_row(107, 68900.0, i_abs=25.8))
    parts.append(_step_row(108, 68900.0, i_abs=25.8))
    step_df = pd.concat(parts + [_capacheck_block(109)], ignore_index=True)
    protocol = build_protocol_exclusion(step_df)
    ckpts = discover_rpt_checkpoints(protocol)
    life_cycles = [c.life_cycle for c in ckpts]
    assert 100 in life_cycles
    ckpt_100 = next(c for c in ckpts if c.life_cycle == 100)
    assert ckpt_100.anchor_raw_cycles == [107, 108]
    assert ckpt_100.anchor_raw_cycle in (107, 108)


def test_zone_hard_within_ten():
    cfg = RptAnchorConfig(hard_radius=10, soft_radius=30)
    assert _zone(95, 100, 200, cfg) == "hard"
    assert _zone(105, 100, 200, cfg) == "hard"
    assert _zone(150, 100, 200, cfg) == "interpolated"


def test_interpolate_expected_v():
    ckpts = [
        RptCheckpoint(
            life_cycle=100,
            anchor_raw_cycle=110,
            anchor_raw_cycles=[110],
            peaks={
                "charge": [RptPeakRef("P2_shoulder", 3.78, 90.0, "charge")],
            },
        ),
        RptCheckpoint(
            life_cycle=200,
            anchor_raw_cycle=215,
            anchor_raw_cycles=[215],
            peaks={
                "charge": [RptPeakRef("P2_shoulder", 3.76, 85.0, "charge")],
            },
        ),
    ]
    shifts = [
        RateShift(life_cycle=100, leg="charge", peak_id="P2_shoulder", delta_v_mV=30.0, n_pairs=3),
        RateShift(life_cycle=200, leg="charge", peak_id="P2_shoulder", delta_v_mV=25.0, n_pairs=3),
    ]
    v_mid, left, right, _ = interpolate_expected_v(ckpts, 150, "charge", "P2_shoulder", shifts)
    assert left == 100 and right == 200
    assert 3.76 < v_mid < 3.81


def test_exclusive_windows_split_adjacent_peaks():
    from cyclediag.features.rpt_anchor import _exclusive_windows_from_expected

    wins = _exclusive_windows_from_expected(
        [("P2_shoulder", 3.78), ("P3_main", 3.86)],
        half_width=0.06,
    )
    assert "P2_shoulder" in wins and "P3_main" in wins
    # Midpoint boundary so windows do not overlap
    assert wins["P2_shoulder"][1] <= wins["P3_main"][0] + 1e-9
    assert abs(wins["P2_shoulder"][1] - 3.82) < 0.01


def test_fill_missing_with_window_split():
    from cyclediag.features.rpt_anchor import (
        RptAnchorConfig,
        fill_missing_with_window_split,
    )

    vx = np.linspace(3.5, 4.1, 200)
    # Merged bump: single broad peak near 3.82 covering P2+P3 region
    y = np.exp(-((vx - 3.82) / 0.04) ** 2) * 80.0
    # Weak shoulder near P2
    y += np.exp(-((vx - 3.76) / 0.02) ** 2) * 25.0
    refs = pd.DataFrame([
        {"leg": "charge", "peak_id": "P2_shoulder", "V": 3.76, "H_abs": 50, "v_lo": 3.72, "v_hi": 3.80},
        {"leg": "charge", "peak_id": "P3_main", "V": 3.88, "H_abs": 50, "v_lo": 3.84, "v_hi": 3.92},
    ])
    filled = fill_missing_with_window_split(
        {}, refs, vx, y, config=RptAnchorConfig(enable_window_split=True),
    )
    assert "P2_shoulder" in filled
    assert "P3_main" in filled
    assert filled["P2_shoulder"]["assign_method"] == "rpt_window_split"
    assert filled["P2_shoulder"]["V"] < filled["P3_main"]["V"]


def test_assign_routine_cycle_returns_rows():
    ckpts = [
        RptCheckpoint(
            life_cycle=100,
            anchor_raw_cycle=110,
            anchor_raw_cycles=[110],
            peaks={
                "charge": [
                    RptPeakRef("P1_low", 3.56, 70.0, "charge"),
                    RptPeakRef("P2_shoulder", 3.78, 90.0, "charge"),
                    RptPeakRef("P3_main", 3.86, 88.0, "charge"),
                    RptPeakRef("P4_high", 4.01, 82.0, "charge"),
                ],
            },
        ),
    ]
    df = _synthetic_raw_df([95, 100, 105])
    rows = assign_routine_cycle(df, 100, ckpts, [], config=RptAnchorConfig())
    assert rows
    assert any(r["cycle"] == 100 and r["leg"] == "charge" for r in rows)
    assert all("assign_zone" in r and "evidence_type" in r for r in rows)


def test_bracket_checkpoints_edges():
    ckpts = [
        RptCheckpoint(100, 110, [110]),
        RptCheckpoint(200, 215, [215]),
    ]
    left, right = _bracket_checkpoints(ckpts, 50)
    assert left.life_cycle == 100
    left2, right2 = _bracket_checkpoints(ckpts, 250)
    assert right2.life_cycle == 200
