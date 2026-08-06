"""Voltage-band discharge capacity — Si vs graphite utilization proxy (ASSB)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BandCapacityConfig:
    """Default thresholds for SJ900 ASSB full-cell (2.5–4.2 V window)."""

    v_high: float = 3.5
    v_low: float = 3.0


def _capacity_array(seg: pd.DataFrame) -> tuple[np.ndarray, np.ndarray] | None:
    if seg is None or seg.empty or "voltage" not in seg.columns:
        return None
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    for col in ("discharge_capacity", "capacity"):
        if col in seg.columns:
            q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
            if np.isfinite(q).sum() >= 2:
                return v, q
    return None


def discharge_band_capacity(
    dchg_seg: pd.DataFrame,
    *,
    config: BandCapacityConfig | None = None,
) -> dict[str, float | None]:
    """Integrate discharge Q in high-V (cathode/graphite) and low-V (Si tail) bands."""
    cfg = config or BandCapacityConfig()
    pair = _capacity_array(dchg_seg)
    empty: dict[str, float | None] = {
        "dchg_Q_high_V": None,
        "dchg_Q_low_V": None,
        "dchg_Q_mid_V": None,
        "dchg_Q_high_frac": None,
        "dchg_Q_low_frac": None,
        "dchg_f_graphite_proxy": None,
    }
    if pair is None:
        return empty
    v, q = pair
    m = np.isfinite(v) & np.isfinite(q)
    v, q = v[m], q[m]
    if len(v) < 3:
        return empty
    dq = np.diff(q)
    v_mid = 0.5 * (v[:-1] + v[1:])
    fin = np.isfinite(dq) & np.isfinite(v_mid)
    if not fin.any():
        return empty
    dq, v_mid = dq[fin], v_mid[fin]
    q_total = float(np.nansum(np.abs(dq)))
    if q_total <= 1e-9:
        return empty
    q_high = float(np.nansum(np.abs(dq[v_mid > cfg.v_high])))
    q_low = float(np.nansum(np.abs(dq[v_mid < cfg.v_low])))
    q_mid = max(0.0, q_total - q_high - q_low)
    q_high_frac = q_high / q_total
    q_low_frac = q_low / q_total
    denom = q_high + q_low
    f_graphite = (q_high / denom) if denom > 1e-9 else None
    return {
        "dchg_Q_high_V": q_high,
        "dchg_Q_low_V": q_low,
        "dchg_Q_mid_V": q_mid,
        "dchg_Q_high_frac": q_high_frac,
        "dchg_Q_low_frac": q_low_frac,
        "dchg_f_graphite_proxy": f_graphite,
    }
