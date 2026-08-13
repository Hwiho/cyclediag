"""Compare cells on matched SoHQ intervals rather than end-of-life points."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from cyclediag.features.indicator_registry import primary_indicator_columns

DEFAULT_BANDS: tuple[tuple[float, float], ...] = (
    (95.0, 90.0),
    (90.0, 80.0),
    (80.0, 70.0),
    (70.0, 60.0),
)


def _band_mask(sohq: pd.Series, hi: float, lo: float) -> pd.Series:
    s = pd.to_numeric(sohq, errors="coerce")
    return s.notna() & (s <= hi) & (s > lo)


def interval_feature_deltas(
    features: pd.DataFrame,
    *,
    bands: Sequence[tuple[float, float]] = DEFAULT_BANDS,
    columns: Iterable[str] | None = None,
    health_col: str = "SoHQ",
) -> pd.DataFrame:
    """Per-cell, per-band mean change of primary indicators.

    Returns long rows: cell_id, band, feature, early_mean, late_mean, delta.
    Within a band, 'early' is the first third of cycles in that band and
    'late' is the last third — so each band has its own local change rate.
    """
    if features is None or features.empty or health_col not in features.columns:
        return pd.DataFrame()
    cols = list(columns) if columns is not None else primary_indicator_columns(features)
    rows: list[dict] = []
    cell_key = "cell_id" if "cell_id" in features.columns else None
    groups = features.groupby(cell_key, sort=False) if cell_key else [(None, features)]
    for cid, grp in groups:
        grp = grp.sort_values("cycle") if "cycle" in grp.columns else grp
        sohq = grp[health_col]
        for hi, lo in bands:
            sub = grp.loc[_band_mask(sohq, hi, lo)]
            if len(sub) < 6:
                continue
            n = len(sub)
            early = sub.iloc[: max(2, n // 3)]
            late = sub.iloc[-max(2, n // 3):]
            for col in cols:
                if col not in sub.columns:
                    continue
                e = pd.to_numeric(early[col], errors="coerce").mean()
                l = pd.to_numeric(late[col], errors="coerce").mean()
                if not (np.isfinite(e) and np.isfinite(l)):
                    continue
                rows.append({
                    "cell_id": cid,
                    "band": f"{hi:.0f}-{lo:.0f}",
                    "band_hi": hi,
                    "band_lo": lo,
                    "feature": col,
                    "n_cycles": n,
                    "early_mean": float(e),
                    "late_mean": float(l),
                    "delta": float(l - e),
                })
    return pd.DataFrame(rows)


def knee_split_summary(
    features: pd.DataFrame,
    *,
    health_col: str = "SoHQ",
    knee_sohq: float | None = None,
) -> dict:
    """Split a cell trajectory into pre/post knee.

    If ``knee_sohq`` is None, use the SoHQ at the maximum of |d2SoHQ| when
    present, else the SoHQ at 60% of cycle span.
    """
    if features is None or features.empty or health_col not in features.columns:
        return {"knee_cycle": None, "knee_sohq": None}
    df = features.sort_values("cycle") if "cycle" in features.columns else features
    sohq = pd.to_numeric(df[health_col], errors="coerce")
    cyc = pd.to_numeric(df["cycle"], errors="coerce") if "cycle" in df.columns else pd.Series(np.arange(len(df)))
    if knee_sohq is not None:
        # first cycle at or below threshold
        m = sohq.notna() & (sohq <= knee_sohq)
        if not m.any():
            return {"knee_cycle": None, "knee_sohq": knee_sohq}
        idx = m.to_numpy().nonzero()[0][0]
    elif "d2SoHQ" in df.columns and pd.to_numeric(df["d2SoHQ"], errors="coerce").notna().sum() >= 5:
        d2 = pd.to_numeric(df["d2SoHQ"], errors="coerce").abs()
        idx = int(d2.idxmax())
        # idx may be label; convert to position
        idx = list(df.index).index(idx)
    else:
        idx = int(len(df) * 0.6)
    return {
        "knee_cycle": float(cyc.iloc[idx]) if np.isfinite(cyc.iloc[idx]) else None,
        "knee_sohq": float(sohq.iloc[idx]) if np.isfinite(sohq.iloc[idx]) else None,
        "pre_n": int(idx),
        "post_n": int(len(df) - idx),
    }
