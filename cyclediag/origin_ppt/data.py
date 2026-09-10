"""Load tagged / arm CSVs and optional raw profiles for Origin graphs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    ARM_CSV,
    CELL_COLOR,
    PROFILE_CELLS,
    RAW_CELLS,
    TAGGED,
    XY_CACHE,
)


def smooth(y: np.ndarray, win: int = 11) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    if len(y) < win:
        return y.copy()
    k = np.ones(win) / win
    pad = win // 2
    return np.convolve(np.pad(y, (pad, pad), mode="edge"), k, mode="valid")[: len(y)]


def _finite_xy(x, y) -> tuple[list[float], list[float]]:
    xx = np.asarray(x, dtype=float)
    yy = np.asarray(y, dtype=float)
    m = np.isfinite(xx) & np.isfinite(yy)
    return xx[m].tolist(), yy[m].tolist()


def pad_limits(values: list[float], *, frac: float = 0.08, fallback: tuple[float, float] = (0.0, 1.0)) -> tuple[float, float]:
    finite = [v for v in values if np.isfinite(v)]
    if not finite:
        return fallback
    lo, hi = min(finite), max(finite)
    if hi <= lo:
        return lo - 0.05, hi + 0.05
    span = hi - lo
    return lo - frac * span, hi + frac * span


def nice_inc(span: float, *, n: int = 5) -> float:
    if not np.isfinite(span) or span <= 0:
        return 1.0
    raw = span / n
    mag = 10 ** np.floor(np.log10(raw))
    for step in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw <= step * mag:
            return float(step * mag)
    return float(10.0 * mag)


def load_arm_tables() -> dict[str, pd.DataFrame]:
    out = {}
    for path in sorted(ARM_CSV.glob("*_dvdq_SOC0.csv")):
        if path.name.startswith("all_"):
            continue
        df = pd.read_csv(path)
        out[str(df["cell_id"].iloc[0])] = df
    if not out:
        raise FileNotFoundError(f"arm SOC0 CSV가 없습니다: {ARM_CSV}")
    return out


def load_tagged() -> dict[str, pd.DataFrame]:
    return {arm: pd.read_csv(path) for arm, path in TAGGED.items() if path.exists()}


def series_for_cells(
    tables: dict[str, pd.DataFrame],
    cells: tuple[str, ...],
    *,
    xcol: str,
    ycol: str,
    abs_y: bool = False,
    do_smooth: bool = True,
) -> list[dict]:
    rows = []
    for cell in cells:
        df = tables.get(cell)
        if df is None:
            continue
        x = pd.to_numeric(df[xcol], errors="coerce")
        y = pd.to_numeric(df[ycol], errors="coerce")
        if abs_y:
            y = np.abs(y)
        if do_smooth:
            y = pd.Series(smooth(y.to_numpy(float)))
        xx, yy = _finite_xy(x, y)
        if not xx:
            continue
        rows.append(
            {
                "label": cell,
                "x": xx,
                "y": yy,
                "color": CELL_COLOR.get(cell, "#333333"),
                "kind": "l",
            }
        )
    return rows


def overlay_metric_series(tagged: pd.DataFrame, cells: tuple[str, ...], col: str) -> list[dict]:
    by_cell = {cell: tagged[tagged["cell_id"] == cell] for cell in cells}
    return series_for_cells(by_cell, cells, xcol="tagged_cycle", ycol=col, abs_y=False, do_smooth=False)


def ylim_of(series: list[dict]) -> tuple[float, float]:
    vals: list[float] = []
    for row in series:
        vals.extend(row["y"])
    return pad_limits(vals)


def xlim_of(series: list[dict], *, lo: float = 0.0) -> tuple[float, float]:
    vals: list[float] = []
    for row in series:
        vals.extend(row["x"])
    hi = max(vals) if vals else 1.0
    return lo, hi * 1.02 if hi > lo else hi + 1.0


def _downsample(x: np.ndarray, y: np.ndarray, n: int = 300) -> tuple[np.ndarray, np.ndarray]:
    if len(x) <= n:
        return x, y
    idx = np.linspace(0, len(x) - 1, n).astype(int)
    return x[idx], y[idx]


def ensure_profile_cache(cell_id: str, *, step: int = 50, refresh: bool = False) -> Path:
    XY_CACHE.mkdir(parents=True, exist_ok=True)
    path = XY_CACHE / f"{cell_id}_profiles.csv"
    if path.exists() and not refresh:
        return path
    raw_path, arm = RAW_CELLS[cell_id]
    from cyclediag.tools.run_dvdq_soc0_arm_plots import (
        dchg_qv,
        dvdq_soc0_profile,
        load_raw,
        tagged_routine_cycles,
    )

    print(f"[{cell_id}] extract Origin profiles step={step}", flush=True)
    raw = load_raw(raw_path)
    tagged = tagged_routine_cycles(raw)
    t_list = sorted(set([1] + list(range(step, len(tagged) + 1, step)) + [len(tagged)]))
    rows = []
    for tidx in t_list:
        q, v = dchg_qv(raw, tagged[tidx - 1])
        if q is None:
            continue
        prof = dvdq_soc0_profile(q, v)
        if prof is None:
            continue
        qx, ydq, samp = prof
        q, v = _downsample(q, v)
        qx, ydq = _downsample(qx, ydq)
        n = max(len(q), len(qx))
        for i in range(n):
            rows.append(
                {
                    "cell_id": cell_id,
                    "arm": arm,
                    "tagged_cycle": tidx,
                    "raw_cycle": tagged[tidx - 1],
                    "Q_v": float(q[i]) if i < len(q) else np.nan,
                    "V": float(v[i]) if i < len(v) else np.nan,
                    "Q_dvdq": float(qx[i]) if i < len(qx) else np.nan,
                    "dVdQ": float(ydq[i]) if i < len(ydq) else np.nan,
                    "soc0_Q": samp.get("Q"),
                    "soc0_dVdQ": samp.get("intensity"),
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def profile_series(cell_id: str, *, ycol: str, xcol: str, step: int = 50, refresh: bool = False) -> list[dict]:
    from matplotlib import cm
    from matplotlib.colors import to_hex

    path = ensure_profile_cache(cell_id, step=step, refresh=refresh)
    df = pd.read_csv(path)
    cycles = sorted(df["tagged_cycle"].unique().tolist())
    nseg = max(len(cycles) - 1, 1)
    rows = []
    soc0_x: list[float] = []
    soc0_y: list[float] = []
    for k, tidx in enumerate(cycles):
        g = df[df["tagged_cycle"] == tidx]
        xx, yy = _finite_xy(g[xcol], g[ycol])
        if not xx:
            continue
        color = to_hex(cm.viridis(k / nseg))
        rows.append({"label": f"t{int(tidx)}", "x": xx, "y": yy, "color": color, "kind": "l"})
        if ycol == "dVdQ":
            sq = pd.to_numeric(g["soc0_Q"], errors="coerce")
            sy = pd.to_numeric(g["soc0_dVdQ"], errors="coerce")
            mx, my = _finite_xy(sq.iloc[:1], sy.iloc[:1])
            if mx:
                soc0_x.extend(mx)
                soc0_y.extend(my)
    if soc0_x:
        rows.append({"label": "SOC0", "x": soc0_x, "y": soc0_y, "color": "#111111", "kind": "s"})
    return rows


def arm_profile_cell(arm: str) -> str:
    return PROFILE_CELLS[arm]


def overlay_metrics() -> tuple[tuple[str, str, str], ...]:
    return (
        ("dchg_dVdQ_SOC0", "|dV/dQ| @ SOC0 (V/Ah)", "SOC0"),
        ("dchg_dVdQ_SOC0_to_mid_ratio", "SOC0 / mid ratio", "ratio"),
        ("dchg_Q_cliff_abs", "Q_cliff_abs (Ah)", "cliff"),
        ("dchg_dVdQ_at_Qabs_5", "|dV/dQ| at Qmax-5 Ah (V/Ah)", "qabs5"),
    )


def list_metric_columns(tagged: dict) -> list[str]:
    """Numeric tagged columns with registry role, for ``--list-metrics``."""
    from cyclediag.features.indicator_registry import ROLE_INDICATOR, ROLE_TARGET, role_of

    cols: dict[str, str] = {}
    for df in tagged.values():
        for col in df.columns:
            name = str(col)
            if name in cols:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            cols[name] = role_of(name)
    wanted = {ROLE_INDICATOR, ROLE_TARGET}
    lines = []
    for name in sorted(cols):
        if cols[name] not in wanted:
            continue
        lines.append(f"{name:<36} {cols[name]}")
    return lines
