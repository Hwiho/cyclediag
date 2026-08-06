"""Simple per-metric trend analysis on cycle series."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .metric_catalog import MetricSpec, available_metrics, get_metric


def _finite_xy(df: pd.DataFrame, key: str) -> tuple[np.ndarray, np.ndarray]:
    cyc = pd.to_numeric(df.get("cycle"), errors="coerce")
    y = pd.to_numeric(df.get(key), errors="coerce")
    m = cyc.notna() & y.notna() & np.isfinite(cyc) & np.isfinite(y)
    return cyc[m].to_numpy(dtype=float), y[m].to_numpy(dtype=float)


def lin_slope_per_100(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 3:
        return None
    # y ~ a + b * cycle → per 100 cycles
    A = np.vstack([x, np.ones(len(x))]).T
    try:
        b, _ = np.linalg.lstsq(A, y, rcond=None)[0]
    except Exception:
        return None
    if not np.isfinite(b):
        return None
    return float(b * 100.0)


def analyze_series(
    df: pd.DataFrame,
    key: str,
    *,
    early_n: int = 5,
    late_n: int = 5,
    routine_only: bool = True,
) -> dict[str, Any]:
    """Return trend summary for one metric column."""
    d = df.sort_values("cycle")
    if routine_only and "cycle_role" in d.columns:
        d = d.loc[d["cycle_role"].astype(str).eq("routine_05c")]
    x, y = _finite_xy(d, key)
    spec = get_metric(key)
    out: dict[str, Any] = {
        "metric": key,
        "title_ko": spec.title_ko if spec else key,
        "unit": spec.unit if spec else "",
        "family": spec.family if spec else "",
        "aging_hint": spec.aging_hint if spec else "either",
        "n": int(len(y)),
        "cycle_start": int(x[0]) if len(x) else None,
        "cycle_end": int(x[-1]) if len(x) else None,
        "early_median": None,
        "late_median": None,
        "delta_late_early": None,
        "pct_change": None,
        "slope_per_100": None,
        "trend_label": "insufficient_data",
        "vs_expectation": "n/a",
        "note": "",
    }
    if len(y) < 2:
        return out

    n_e = min(early_n, len(y))
    n_l = min(late_n, len(y))
    early = float(np.median(y[:n_e]))
    late = float(np.median(y[-n_l:]))
    delta = late - early
    slope = lin_slope_per_100(x, y)
    out["early_median"] = early
    out["late_median"] = late
    out["delta_late_early"] = float(delta)
    out["slope_per_100"] = slope
    if abs(early) > 1e-12:
        out["pct_change"] = float(100.0 * delta / abs(early))

    # classify trend using slope if available else delta
    signal = slope if slope is not None else delta
    # scale-free relative threshold
    scale = max(abs(early), abs(late), np.std(y), 1e-9)
    thr = 0.05 * scale  # 5% of scale per comparison unit
    if slope is not None:
        # slope is per 100 cycles — compare to 5% of scale
        if abs(slope) < thr:
            label = "flat"
        elif slope > 0:
            label = "increasing"
        else:
            label = "decreasing"
    else:
        if abs(delta) < thr:
            label = "flat"
        elif delta > 0:
            label = "increasing"
        else:
            label = "decreasing"
    out["trend_label"] = label

    hint = out["aging_hint"]
    if hint in ("increase", "decrease") and label in ("increasing", "decreasing", "flat"):
        if label == "flat":
            out["vs_expectation"] = "stable"
        elif (hint == "increase" and label == "increasing") or (
            hint == "decrease" and label == "decreasing"
        ):
            out["vs_expectation"] = "matches_aging"
        else:
            out["vs_expectation"] = "opposite_aging"
    else:
        out["vs_expectation"] = "context"

    # short Korean note
    unit = out["unit"] or ""
    sl = f"{slope:+.4g}{unit}/100cyc" if slope is not None else "n/a"
    out["note"] = (
        f"{out['title_ko']}: early={early:.4g} → late={late:.4g} "
        f"(Δ={delta:+.4g}, {sl}) → {label}"
        + (f" · {out['vs_expectation']}" if out["vs_expectation"] != "n/a" else "")
    )
    return out


def analyze_all_metrics(
    df: pd.DataFrame,
    *,
    keys: list[str] | None = None,
    routine_only: bool = True,
) -> pd.DataFrame:
    specs = available_metrics(df.columns) if keys is None else [
        s for k in keys if (s := get_metric(k)) is not None
    ]
    # also allow raw keys not in catalog
    if keys is not None:
        want = keys
    else:
        want = [s.key for s in specs]
    rows = [analyze_series(df, k, routine_only=routine_only) for k in want if k in df.columns]
    return pd.DataFrame(rows)


def extract_cycle_metric_table(
    df: pd.DataFrame,
    *,
    keys: list[str] | None = None,
    routine_only: bool = True,
) -> pd.DataFrame:
    """Slim cycle×metric table for export."""
    d = df.sort_values("cycle").copy()
    if routine_only and "cycle_role" in d.columns:
        d = d.loc[d["cycle_role"].astype(str).eq("routine_05c")]
    base = ["cycle"]
    if "cycle_role" in d.columns:
        base.append("cycle_role")
    if "SoHQ" in d.columns and (keys is None or "SoHQ" not in (keys or [])):
        # always keep SoHQ as context when present
        pass
    if keys is None:
        keys = [m.key for m in available_metrics(d.columns)]
    cols = base + [k for k in keys if k in d.columns and k not in base]
    return d[cols].reset_index(drop=True)


def narrative_from_trends(trends: pd.DataFrame, *, cell_id: str = "") -> str:
    lines = [
        f"## 트렌드 요약{f' — {cell_id}' if cell_id else ''}",
        "",
    ]
    if trends.empty:
        lines.append("분석 가능한 지표가 없습니다.")
        return "\n".join(lines)

    aging = trends.loc[trends["vs_expectation"] == "matches_aging"]
    opposite = trends.loc[trends["vs_expectation"] == "opposite_aging"]
    def _by_abs_slope(frame: pd.DataFrame) -> pd.DataFrame:
        f = frame.copy()
        f["_abs"] = pd.to_numeric(f["slope_per_100"], errors="coerce").abs().fillna(0.0)
        return f.sort_values("_abs", ascending=False)

    rising = _by_abs_slope(trends.loc[trends["trend_label"] == "increasing"])
    falling = _by_abs_slope(trends.loc[trends["trend_label"] == "decreasing"])

    lines.append(f"- 유효 지표: {len(trends)}개 · aging 방향 일치 {len(aging)} · 반대 {len(opposite)}")
    lines.append("")
    if not falling.empty:
        lines.append("### 하락 트렌드 (상위)")
        for _, r in falling.head(5).iterrows():
            lines.append(f"- {r['note']}")
        lines.append("")
    if not rising.empty:
        lines.append("### 상승 트렌드 (상위)")
        for _, r in rising.head(5).iterrows():
            lines.append(f"- {r['note']}")
        lines.append("")
    if not opposite.empty:
        lines.append("### 기대 aging과 반대")
        for _, r in opposite.head(4).iterrows():
            lines.append(f"- {r['note']}")
        lines.append("")
    lines.append(
        "> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). "
        "패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다."
    )
    return "\n".join(lines)
