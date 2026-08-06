"""Local CC/CV region detection (standalone; no pne_studio dependency)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CvRegionInfo:
    has_cv: bool
    cv_start_index: int | None
    n_cc: int
    n_cv: int
    cc_q_frac: float | None
    cv_time_s: float | None
    v_cc_end: float | None
    q_cc_end: float | None
    v_cv_start: float | None
    q_cv_start: float | None
    current_col: str | None
    method: str


def resolve_current_column(df: pd.DataFrame) -> str | None:
    """Pick a current column (AvgCurrent preferred)."""
    priority: list[str] = []
    fallback: list[str] = []
    for col in df.columns:
        clean = str(col).lower().replace(" ", "").replace("_", "")
        if clean in ("avgcurrent", "avgcurrentma", "avgcurrenta"):
            priority.append(col)
        elif clean in ("current", "curr", "i", "currenta", "currentma"):
            fallback.append(col)
    for col in priority + fallback:
        series = pd.to_numeric(df[col], errors="coerce").abs()
        valid = series[np.isfinite(series) & (series > 0)]
        if len(valid) >= 4:
            return col
    for col in priority + fallback:
        return col
    return None


def _empty(method: str = "no_cv", current_col: str | None = None, n: int = 0) -> CvRegionInfo:
    return CvRegionInfo(
        has_cv=False,
        cv_start_index=None,
        n_cc=n,
        n_cv=0,
        cc_q_frac=1.0 if n > 0 else None,
        cv_time_s=0.0,
        v_cc_end=None,
        q_cc_end=None,
        v_cv_start=None,
        q_cv_start=None,
        current_col=current_col,
        method=method,
    )


def detect_cv_region(
    seg: pd.DataFrame,
    *,
    v_col: str = "voltage",
    q_col: str | None = None,
    t_col: str | None = None,
    i_col: str | None = None,
    v_cutoff_margin_v: float = 0.015,
    dvdt_max_v_per_min: float = 0.0002,
) -> CvRegionInfo:
    """Detect CC→CV boundary on one charge/discharge leg."""
    if seg is None or seg.empty or v_col not in seg.columns:
        return _empty("empty")

    n = len(seg)
    if i_col is None:
        i_col = resolve_current_column(seg)
    if t_col is None:
        for c in ("step_time", "time", "StepTime_sec"):
            if c in seg.columns:
                t_col = c
                break
    if q_col is None:
        for c in ("charge_capacity", "capacity", "discharge_capacity"):
            if c in seg.columns:
                q_col = c
                break

    v = pd.to_numeric(seg[v_col], errors="coerce").to_numpy(dtype=float)
    i = (
        pd.to_numeric(seg[i_col], errors="coerce").to_numpy(dtype=float)
        if i_col is not None
        else np.full(n, np.nan)
    )
    t = (
        pd.to_numeric(seg[t_col], errors="coerce").to_numpy(dtype=float)
        if t_col is not None
        else np.arange(n, dtype=float)
    )
    q = (
        pd.to_numeric(seg[q_col], errors="coerce").to_numpy(dtype=float)
        if q_col is not None
        else np.full(n, np.nan)
    )

    finite_v = v[np.isfinite(v)]
    if len(finite_v) < 4:
        return _empty("too_short", i_col, n)

    v_cut = float(np.nanpercentile(finite_v, 99))
    near_cut = np.isfinite(v) & (v >= v_cut - v_cutoff_margin_v)

    # Prefer signal: near cutoff, flat dV/dt, decaying |I|
    dt = np.diff(t)
    dv = np.diff(v)
    with np.errstate(divide="ignore", invalid="ignore"):
        dvdt = np.where(np.abs(dt) > 1e-12, dv / dt, np.nan)
    dvdt_per_min = np.concatenate([[dvdt[0] if len(dvdt) else np.nan], dvdt]) * 60.0
    di = np.diff(np.abs(i))
    didt = np.concatenate([[di[0] if len(di) else np.nan], di])

    mask = near_cut & np.isfinite(dvdt_per_min) & (np.abs(dvdt_per_min) < dvdt_max_v_per_min)
    if np.isfinite(i).sum() >= 4:
        mask = mask & np.isfinite(didt) & (didt < 0)

    best_a = best_b = -1
    a = None
    for idx, flag in enumerate(mask):
        if flag and a is None:
            a = idx
        elif not flag and a is not None:
            if best_a < 0 or (idx - a) > (best_b - best_a):
                best_a, best_b = a, idx
            a = None
    if a is not None and (best_a < 0 or (n - a) > (best_b - best_a)):
        best_a, best_b = a, n

    method = "signal"
    if best_a < 0 or best_b - best_a < 3:
        # Fallback: voltage plateau at cutoff (constant V run)
        plateau = near_cut & np.isfinite(v)
        best_a = best_b = -1
        a = None
        for idx, flag in enumerate(plateau):
            if flag and a is None:
                a = idx
            elif not flag and a is not None:
                if best_a < 0 or (idx - a) > (best_b - best_a):
                    best_a, best_b = a, idx
                a = None
        if a is not None and (best_a < 0 or (n - a) > (best_b - best_a)):
            best_a, best_b = a, n
        method = "voltage_plateau"
        if best_a < 0 or best_b - best_a < 3:
            return _empty("no_cv", i_col, n)

    # Prefer the start of the plateau near the end of the leg (CC→CV)
    # If earliest plateau is mid-leg noise, take the last long run.
    # Recompute last long run for plateau near end:
    if best_b < n * 0.5 and method == "voltage_plateau":
        # search from end: first index of trailing near-cut run
        j = n - 1
        while j >= 0 and near_cut[j]:
            j -= 1
        start = j + 1
        if n - start >= 3:
            best_a, best_b = start, n
            method = "trailing_plateau"

    cv_start = int(best_a)
    n_cc = cv_start
    n_cv = n - cv_start
    t0 = float(t[cv_start]) if np.isfinite(t[cv_start]) else 0.0
    t1 = float(t[n - 1]) if np.isfinite(t[n - 1]) else t0
    cv_time = max(0.0, t1 - t0)

    q_start = float(q[0]) if np.isfinite(q[0]) else (float(np.nanmin(q)) if np.isfinite(q).any() else np.nan)
    q_cc = float(q[cv_start]) if np.isfinite(q[cv_start]) else np.nan
    q_end = float(q[n - 1]) if np.isfinite(q[n - 1]) else (float(np.nanmax(q)) if np.isfinite(q).any() else np.nan)
    if np.isfinite(q_start) and np.isfinite(q_end) and abs(q_end - q_start) > 1e-12:
        cc_q_frac = abs(q_cc - q_start) / abs(q_end - q_start) if np.isfinite(q_cc) else None
    else:
        cc_q_frac = float(n_cc) / float(n) if n else None

    v_cc_end = float(v[cv_start - 1]) if cv_start > 0 and np.isfinite(v[cv_start - 1]) else (
        float(v[cv_start]) if np.isfinite(v[cv_start]) else None
    )
    v_cv_start = float(v[cv_start]) if np.isfinite(v[cv_start]) else None

    return CvRegionInfo(
        has_cv=True,
        cv_start_index=cv_start,
        n_cc=n_cc,
        n_cv=n_cv,
        cc_q_frac=float(cc_q_frac) if cc_q_frac is not None else None,
        cv_time_s=float(cv_time),
        v_cc_end=v_cc_end,
        q_cc_end=float(q_cc) if np.isfinite(q_cc) else None,
        v_cv_start=v_cv_start,
        q_cv_start=float(q_cc) if np.isfinite(q_cc) else None,
        current_col=i_col,
        method=method,
    )


def trim_to_cc_end(
    seg: pd.DataFrame,
    info: CvRegionInfo,
    *,
    include_boundary: bool = True,
) -> pd.DataFrame:
    """Keep CC portion up to (optionally including) the CC→CV boundary."""
    if seg is None or seg.empty or not info.has_cv or info.cv_start_index is None:
        return seg
    end = int(info.cv_start_index)
    if include_boundary:
        end = min(len(seg), end + 1)
    return seg.iloc[:end].copy()
