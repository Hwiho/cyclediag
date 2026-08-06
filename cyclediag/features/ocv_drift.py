"""Quasi-OCV drift across DC-IR SOC points — thermodynamic composition proxy.

Terminology (neutral until half-cell / C/20 pseudo-OCV validation):
  ocv_parallel_shift      -> LLI + kinetic early-termination proxy
  ocv_spread_compression  -> electrode imbalance proxy (not symmetric LAM)
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cyclediag.features.self_discharge import self_discharge_for_cycle

_SOC_ORDER = (80, 50, 20)
_SOC_PTS = np.array([80.0, 50.0, 20.0], dtype=float)

_BLOCK_COLS = (
    "ocv_V_inf_soc80",
    "ocv_V_inf_soc50",
    "ocv_V_inf_soc20",
    "ocv_spread_20_80",
    "ocv_spread_50_80",
    "ocv_spread_20_50",
    "ocv_parallel_shift",
    "ocv_spread_compression",
    "ocv_spread_slope",
    "ocv_drift_mode",
    "relax_completeness_soc80",
    "relax_completeness_soc50",
    "relax_completeness_soc20",
    "relax_completeness_max",
)


def _v_inf_for_cycle(
    cycle_df: pd.DataFrame,
    *,
    rest_current_max: float,
    expected_pulse_current: float,
) -> dict[str, Any]:
    sd = self_discharge_for_cycle(
        cycle_df,
        rest_current_max=rest_current_max,
        expected_pulse_current=expected_pulse_current,
    )
    v = sd.get("V_inf_rest")
    if v is None or not np.isfinite(v):
        return {"V_inf_rest": None, "relax_completeness": None, "sd_fit_valid": sd.get("sd_fit_valid")}
    return {
        "V_inf_rest": float(v),
        "relax_completeness": sd.get("relax_completeness"),
        "sd_fit_valid": sd.get("sd_fit_valid"),
    }


def compute_block_quasi_ocv(
    block: list[int],
    raw_df: pd.DataFrame,
    *,
    rest_current_max: float = 0.5,
    expected_pulse_current: float = 70.0,
) -> dict[str, Any] | None:
    """One quasi-OCV curve from a 3-cycle DC-IR block."""
    if len(block) < 3:
        return None
    v_by_soc: dict[int, float | None] = {}
    relax_by_soc: dict[int, float | None] = {}
    for i, cyc in enumerate(block[:3]):
        soc = _SOC_ORDER[i]
        g = raw_df[raw_df["cycle"] == int(cyc)]
        if g.empty:
            v_by_soc[soc] = None
            relax_by_soc[soc] = None
            continue
        row = _v_inf_for_cycle(
            g,
            rest_current_max=rest_current_max,
            expected_pulse_current=expected_pulse_current,
        )
        v_by_soc[soc] = row.get("V_inf_rest")
        relax_by_soc[soc] = row.get("relax_completeness")

    v80, v50, v20 = v_by_soc.get(80), v_by_soc.get(50), v_by_soc.get(20)
    if not all(x is not None and np.isfinite(x) for x in (v80, v50, v20)):
        return None

    spread_20_80 = float(v20 - v80)
    spread_50_80 = float(v50 - v80)
    spread_20_50 = float(v20 - v50)
    rc = [relax_by_soc.get(s) for s in _SOC_ORDER]
    rc_fin = [x for x in rc if x is not None and np.isfinite(x)]

    return {
        "block_cycles": [int(c) for c in block[:3]],
        "ocv_V_inf_soc80": float(v80),
        "ocv_V_inf_soc50": float(v50),
        "ocv_V_inf_soc20": float(v20),
        "ocv_spread_20_80": spread_20_80,
        "ocv_spread_50_80": spread_50_80,
        "ocv_spread_20_50": spread_20_50,
        "relax_completeness_soc80": relax_by_soc.get(80),
        "relax_completeness_soc50": relax_by_soc.get(50),
        "relax_completeness_soc20": relax_by_soc.get(20),
        "relax_completeness_max": float(max(rc_fin)) if rc_fin else None,
    }


def _classify_drift(
    *,
    d80: float,
    d50: float,
    d20: float,
    d_spread_20_80: float,
    parallel_thr: float = 0.005,
    spread_thr: float = 0.010,
) -> tuple[str, float, float, float]:
    """Return (mode, parallel_shift@SOC50, spread_compression, spread_slope).

    Parallel and spread are orthogonal: linear fit on (SOC80,50,20) vs deltas.
    """
    deltas = np.array([d80, d50, d20], dtype=float)
    max_abs = float(np.max(np.abs(deltas)))
    if max_abs < parallel_thr and abs(d_spread_20_80) < spread_thr:
        return "stable", 0.0, float(d_spread_20_80), 0.0

    slope, intercept = np.polyfit(_SOC_PTS, deltas, 1)
    parallel_shift = float(intercept + slope * 50.0)
    spread_slope = float(slope)
    spread_compression = float(d_spread_20_80)
    fit_line = intercept + slope * _SOC_PTS
    parallel_std = float(np.std(deltas - fit_line))

    parallel_dom = parallel_std < parallel_thr
    spread_dom = abs(spread_slope) * 60.0 > spread_thr or abs(spread_compression) > spread_thr

    if parallel_dom and not spread_dom:
        mode = "parallel_shift"
    elif spread_dom and parallel_dom:
        mode = "spread_and_shift"
    elif spread_dom:
        mode = "spread_change"
    else:
        dev = np.abs(deltas - fit_line)
        if float(np.max(dev)) > parallel_thr * 2:
            worst = _SOC_ORDER[int(np.argmax(dev))]
            mode = f"local_soc{worst}"
        else:
            mode = "stable"
    return mode, parallel_shift, spread_compression, spread_slope


def compute_ocv_drift_table(
    dcir_blocks: list[list[int]],
    raw_df: pd.DataFrame,
    *,
    rest_current_max: float = 0.5,
    expected_pulse_current: float = 70.0,
) -> pd.DataFrame:
    """Per-block quasi-OCV metrics with drift vs first valid block."""
    rows: list[dict[str, Any]] = []
    baseline: dict[str, Any] | None = None

    for bid, block in enumerate(dcir_blocks, start=1):
        cur = compute_block_quasi_ocv(
            block,
            raw_df,
            rest_current_max=rest_current_max,
            expected_pulse_current=expected_pulse_current,
        )
        if cur is None:
            continue
        row = {"block_id": bid, "block_start_cycle": int(block[0]), **cur}
        if baseline is None:
            baseline = cur
            row["ocv_parallel_shift"] = 0.0
            row["ocv_spread_compression"] = 0.0
            row["ocv_spread_slope"] = 0.0
            row["ocv_drift_mode"] = "baseline"
            row["delta_ocv_V_inf_soc80"] = 0.0
            row["delta_ocv_V_inf_soc50"] = 0.0
            row["delta_ocv_V_inf_soc20"] = 0.0
            row["delta_ocv_spread_20_80"] = 0.0
        else:
            d80 = cur["ocv_V_inf_soc80"] - baseline["ocv_V_inf_soc80"]
            d50 = cur["ocv_V_inf_soc50"] - baseline["ocv_V_inf_soc50"]
            d20 = cur["ocv_V_inf_soc20"] - baseline["ocv_V_inf_soc20"]
            d_sp = cur["ocv_spread_20_80"] - baseline["ocv_spread_20_80"]
            mode, par, comp, slope = _classify_drift(
                d80=d80, d50=d50, d20=d20, d_spread_20_80=d_sp,
            )
            row["delta_ocv_V_inf_soc80"] = d80
            row["delta_ocv_V_inf_soc50"] = d50
            row["delta_ocv_V_inf_soc20"] = d20
            row["delta_ocv_spread_20_80"] = d_sp
            row["ocv_parallel_shift"] = par
            row["ocv_spread_compression"] = comp
            row["ocv_spread_slope"] = slope
            row["ocv_drift_mode"] = mode
        rows.append(row)
    return pd.DataFrame(rows)


def attach_ocv_drift_to_features(
    features: pd.DataFrame,
    dcir_blocks: list[list[int]],
    raw_df: pd.DataFrame,
    *,
    rest_current_max: float = 0.5,
    expected_pulse_current: float = 70.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Broadcast block-level OCV drift columns onto DC-IR cycle rows."""
    out = features.copy()
    for col in _BLOCK_COLS + (
        "delta_ocv_V_inf_soc80",
        "delta_ocv_V_inf_soc50",
        "delta_ocv_V_inf_soc20",
        "delta_ocv_spread_20_80",
        "ocv_block_id",
    ):
        if col not in out.columns:
            out[col] = np.nan if col != "ocv_drift_mode" else None

    block_df = compute_ocv_drift_table(
        dcir_blocks,
        raw_df,
        rest_current_max=rest_current_max,
        expected_pulse_current=expected_pulse_current,
    )
    if block_df.empty:
        return out, block_df

    broadcast_cols = [c for c in block_df.columns if c not in ("block_cycles",)]
    for _, brow in block_df.iterrows():
        cycles = brow.get("block_cycles") or []
        for cyc in cycles:
            mask = out["cycle"] == int(cyc)
            if not mask.any():
                continue
            for col in broadcast_cols:
                out.loc[mask, col] = brow[col]
            out.loc[mask, "ocv_block_id"] = brow["block_id"]

    return out, block_df
