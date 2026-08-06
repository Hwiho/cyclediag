"""SoHQ fade-curve inflection / regime-change detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SohqInflection:
    """One regime-change (breakpoint) on the SoHQ curve."""

    cycle: float
    tagged_cycle: float | None
    sohq: float
    fade_rate_before: float  # % / 100 cycles
    fade_rate_after: float
    curvature: float
    method: str


@dataclass
class SohqRegime:
    """One fade regime between consecutive breakpoints (or ends)."""

    seg_id: int
    cycle_start: float
    cycle_end: float
    tagged_start: float | None
    tagged_end: float | None
    sohq_start: float
    sohq_end: float
    n_points: int
    slope_pct_per_100cyc: float
    delta_sohq: float


@dataclass
class SohqInflectionResult:
    """Full SoHQ inflection analysis for one cell."""

    x: np.ndarray
    sohq: np.ndarray
    sohq_smooth: np.ndarray
    fade_rate: np.ndarray  # % / 100 cycles (on smooth)
    curvature: np.ndarray
    inflections: list[SohqInflection] = field(default_factory=list)
    regimes: list[SohqRegime] = field(default_factory=list)
    x_col: str = "cycle"
    cell_id: str | None = None

    def breakpoints_table(self) -> pd.DataFrame:
        rows = []
        for bp in self.inflections:
            rows.append({
                "cycle": bp.cycle,
                "tagged_cycle": bp.tagged_cycle,
                "sohq": bp.sohq,
                "fade_rate_before": bp.fade_rate_before,
                "fade_rate_after": bp.fade_rate_after,
                "delta_fade_rate": bp.fade_rate_after - bp.fade_rate_before,
                "curvature": bp.curvature,
                "method": bp.method,
            })
        return pd.DataFrame(rows)

    def regimes_table(self) -> pd.DataFrame:
        rows = []
        for r in self.regimes:
            rows.append({
                "seg_id": r.seg_id,
                "cycle_start": r.cycle_start,
                "cycle_end": r.cycle_end,
                "tagged_start": r.tagged_start,
                "tagged_end": r.tagged_end,
                "sohq_start": r.sohq_start,
                "sohq_end": r.sohq_end,
                "n_points": r.n_points,
                "slope_pct_per_100cyc": r.slope_pct_per_100cyc,
                "delta_sohq": r.delta_sohq,
            })
        return pd.DataFrame(rows)


def _x_column(df: pd.DataFrame) -> str:
    if "tagged_cycle" in df.columns and pd.to_numeric(df["tagged_cycle"], errors="coerce").notna().any():
        return "tagged_cycle"
    return "cycle"


def _smooth_series(y: np.ndarray, window: int) -> np.ndarray:
    """Centered rolling mean; edges use expanding mean."""
    n = len(y)
    if n < 3:
        return y.copy()
    w = max(3, int(window))
    if w % 2 == 0:
        w += 1
    w = min(w, n if n % 2 == 1 else n - 1)
    if w < 3:
        return y.copy()
    s = pd.Series(y)
    out = s.rolling(window=w, center=True, min_periods=1).mean().to_numpy(dtype=float)
    return out


def _fade_rate_per_100(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Local fade rate (% SoHQ per 100 cycles) via gradient."""
    if len(x) < 2:
        return np.zeros_like(y)
    dy = np.gradient(y, x)
    return dy * 100.0


def _segment_slope(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2:
        return float("nan")
    coef = np.polyfit(x, y, 1)
    return float(coef[0] * 100.0)  # % per 100 cycles


def _piecewise_breakpoints(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_breaks: int,
    min_seg: int,
) -> list[int]:
    """Find n_breaks indices (into x) minimizing piecewise-linear SSE.

    Exhaustive for 1–2 breaks; greedy sequential for more.
    Returns sorted interior break indices (not 0 / n-1).
    """
    n = len(x)
    if n_breaks < 1 or n < (n_breaks + 1) * min_seg:
        return []

    def sse_for_cuts(cuts: list[int]) -> float:
        bounds = [0] + sorted(cuts) + [n]
        total = 0.0
        for a, b in zip(bounds[:-1], bounds[1:]):
            if b - a < 2:
                return float("inf")
            coef = np.polyfit(x[a:b], y[a:b], 1)
            pred = np.polyval(coef, x[a:b])
            total += float(np.sum((y[a:b] - pred) ** 2))
        return total

    if n_breaks == 1:
        best_i, best_sse = None, float("inf")
        step = 1 if n < 250 else max(1, n // 200)
        for i in range(min_seg, n - min_seg, step):
            sse = sse_for_cuts([i])
            if sse < best_sse:
                best_sse, best_i = sse, i
        return [best_i] if best_i is not None else []

    if n_breaks == 2:
        best, best_sse = None, float("inf")
        step = 1 if n < 250 else max(1, n // 150)
        for i in range(min_seg, n - 2 * min_seg, step):
            for j in range(i + min_seg, n - min_seg, step):
                sse = sse_for_cuts([i, j])
                if sse < best_sse:
                    best_sse, best = sse, [i, j]
        return best or []

    # Greedy: add breaks one by one
    cuts: list[int] = []
    for _ in range(n_breaks):
        best_i, best_sse = None, float("inf")
        for i in range(min_seg, n - min_seg):
            if any(abs(i - c) < min_seg for c in cuts):
                continue
            sse = sse_for_cuts(cuts + [i])
            if sse < best_sse:
                best_sse, best_i = sse, i
        if best_i is None:
            break
        cuts.append(best_i)
    return sorted(cuts)


def _curvature_candidates(
    x: np.ndarray,
    curvature: np.ndarray,
    *,
    max_points: int,
    min_sep: int,
    abs_thresh: float,
) -> list[int]:
    """Local extrema of |curvature| above threshold, spaced by min_sep."""
    n = len(curvature)
    if n < 5:
        return []
    mag = np.abs(curvature)
    finite = np.isfinite(mag)
    if not finite.any():
        return []
    thr = abs_thresh
    if not np.isfinite(thr) or thr <= 0:
        thr = float(np.nanpercentile(mag[finite], 75))

    peaks: list[tuple[float, int]] = []
    for i in range(2, n - 2):
        if not finite[i] or mag[i] < thr:
            continue
        if mag[i] >= mag[i - 1] and mag[i] >= mag[i + 1]:
            peaks.append((mag[i], i))
    peaks.sort(reverse=True)

    chosen: list[int] = []
    for _, i in peaks:
        if any(abs(i - j) < min_sep for j in chosen):
            continue
        chosen.append(i)
        if len(chosen) >= max_points:
            break
    return sorted(chosen)


def detect_sohq_inflections(
    features: pd.DataFrame,
    *,
    sohq_col: str = "SoHQ",
    max_breaks: int = 2,
    smooth_window: int | None = None,
    min_seg_points: int = 40,
    method: str = "hybrid",
) -> SohqInflectionResult | None:
    """Detect SoHQ fade regime changes (inflection / breakpoints).

    Parameters
    ----------
    method:
        ``piecewise`` — piecewise-linear SSE breakpoints (best for fade regimes)
        ``curvature`` — peaks of |d²SoHQ/dx²| on smoothed curve
        ``hybrid`` — piecewise first; fall back to curvature if empty
    """
    if features is None or features.empty or sohq_col not in features.columns:
        return None

    work = features.copy()
    x_col = _x_column(work)
    work[x_col] = pd.to_numeric(work[x_col], errors="coerce")
    work[sohq_col] = pd.to_numeric(work[sohq_col], errors="coerce")
    work = work.dropna(subset=[x_col, sohq_col]).sort_values(x_col)
    if len(work) < max(min_seg_points * 2, 40):
        return None

    x = work[x_col].to_numpy(dtype=float)
    y = work[sohq_col].to_numpy(dtype=float)
    raw_cycle = (
        pd.to_numeric(work["cycle"], errors="coerce").to_numpy(dtype=float)
        if "cycle" in work.columns
        else x.copy()
    )

    n = len(x)
    win = smooth_window or max(11, n // 40)
    if win % 2 == 0:
        win += 1
    y_s = _smooth_series(y, win)
    fade = _fade_rate_per_100(x, y_s)
    curv = np.gradient(fade, x)

    cell_id = None
    if "cell_id" in work.columns and work["cell_id"].notna().any():
        cell_id = str(work["cell_id"].iloc[0])

    min_sep = max(min_seg_points, n // 20)
    idxs: list[int] = []

    def _piecewise_with_elbow() -> list[int]:
        best_cuts: list[int] = []
        prev_sse = float(np.sum((y_s - np.polyval(np.polyfit(x, y_s, 1), x)) ** 2))
        for k in range(1, max_breaks + 1):
            cuts = _piecewise_breakpoints(x, y_s, n_breaks=k, min_seg=min_seg_points)
            if not cuts:
                break
            bounds = [0] + cuts + [n]
            sse = 0.0
            for a, b in zip(bounds[:-1], bounds[1:]):
                coef = np.polyfit(x[a:b], y_s[a:b], 1)
                sse += float(np.sum((y_s[a:b] - np.polyval(coef, x[a:b])) ** 2))
            # require meaningful SSE improvement; always accept first break
            if k > 1 and (prev_sse <= 0 or (prev_sse - sse) / prev_sse < 0.08):
                break
            best_cuts = cuts
            prev_sse = sse
        return best_cuts

    if method in ("piecewise", "hybrid"):
        idxs = _piecewise_with_elbow()

    if method == "curvature" or (method == "hybrid" and not idxs):
        idxs = _curvature_candidates(
            x, curv,
            max_points=max_breaks,
            min_sep=min_sep,
            abs_thresh=float(np.nanpercentile(np.abs(curv), 80)),
        )

    # Build inflection objects
    inflections: list[SohqInflection] = []
    for i in idxs:
        before = _segment_slope(x[max(0, i - min_seg_points):i], y_s[max(0, i - min_seg_points):i])
        after = _segment_slope(x[i:min(n, i + min_seg_points)], y_s[i:min(n, i + min_seg_points)])
        tagged = float(x[i]) if x_col == "tagged_cycle" else None
        cycle_val = float(raw_cycle[i]) if np.isfinite(raw_cycle[i]) else float(x[i])
        inflections.append(
            SohqInflection(
                cycle=cycle_val,
                tagged_cycle=tagged,
                sohq=float(y_s[i]),
                fade_rate_before=before,
                fade_rate_after=after,
                curvature=float(curv[i]) if np.isfinite(curv[i]) else float("nan"),
                method=method,
            )
        )

    # Regimes
    cut_pos = [0] + idxs + [n - 1]
    regimes: list[SohqRegime] = []
    for seg_id, (a, b) in enumerate(zip(cut_pos[:-1], cut_pos[1:]), start=1):
        # include endpoint; for interior break, next segment starts at break
        lo, hi = a, b if b == n - 1 else b
        if hi <= lo:
            continue
        xs, ys = x[lo:hi + 1], y_s[lo:hi + 1]
        tagged_s = float(xs[0]) if x_col == "tagged_cycle" else None
        tagged_e = float(xs[-1]) if x_col == "tagged_cycle" else None
        regimes.append(
            SohqRegime(
                seg_id=seg_id,
                cycle_start=float(raw_cycle[lo]),
                cycle_end=float(raw_cycle[hi]),
                tagged_start=tagged_s,
                tagged_end=tagged_e,
                sohq_start=float(ys[0]),
                sohq_end=float(ys[-1]),
                n_points=int(hi - lo + 1),
                slope_pct_per_100cyc=_segment_slope(xs, ys),
                delta_sohq=float(ys[-1] - ys[0]),
            )
        )

    return SohqInflectionResult(
        x=x,
        sohq=y,
        sohq_smooth=y_s,
        fade_rate=fade,
        curvature=curv,
        inflections=inflections,
        regimes=regimes,
        x_col=x_col,
        cell_id=cell_id,
    )


def plot_sohq_inflection_report(
    features: pd.DataFrame,
    out_path: str | Path,
    *,
    title: str | None = None,
    max_breaks: int = 2,
    method: str = "hybrid",
    dpi: int = 140,
) -> tuple[Path, SohqInflectionResult] | tuple[None, None]:
    """PNG: SoHQ with inflection markers + fade-rate panel + regime table."""
    result = detect_sohq_inflections(
        features, max_breaks=max_breaks, method=method,
    )
    if result is None:
        return None, None

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    x = result.x
    x_label = "Tagged cycle #" if result.x_col == "tagged_cycle" else "Cycle"
    cid = result.cell_id or "cell"

    fig = plt.figure(figsize=(13.5, 7.8), facecolor="white")
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.35, 1.0], width_ratios=[1.4, 1.0],
                  hspace=0.35, wspace=0.28, left=0.07, right=0.98, top=0.88, bottom=0.08)

    ax0 = fig.add_subplot(gs[0, 0])
    ax0.plot(x, result.sohq, color="#a0c4e8", linewidth=1.0, alpha=0.7, label="SoHQ raw")
    ax0.plot(x, result.sohq_smooth, color="#1f77b4", linewidth=2.0, label="SoHQ smooth")
    colors = ("#e74c3c", "#e67e22", "#9b59b6", "#16a085")
    for i, bp in enumerate(result.inflections):
        xv = bp.tagged_cycle if bp.tagged_cycle is not None else bp.cycle
        ax0.axvline(xv, color=colors[i % len(colors)], linestyle="--", linewidth=1.4, alpha=0.9)
        ax0.scatter([xv], [bp.sohq], color=colors[i % len(colors)], s=55, zorder=5,
                    label=f"BP{i + 1} @ {xv:.0f} (SoHQ={bp.sohq:.1f}%)")
    # shade regimes lightly
    for r in result.regimes:
        x0 = r.tagged_start if r.tagged_start is not None else r.cycle_start
        x1 = r.tagged_end if r.tagged_end is not None else r.cycle_end
        ax0.axvspan(x0, x1, alpha=0.04 + 0.03 * (r.seg_id % 3), color="#34495e")
        mid = 0.5 * (x0 + x1)
        y_txt = float(np.nanmin(result.sohq_smooth)) + 1.5
        ax0.text(
            mid, y_txt,
            f"S{r.seg_id}\n{r.slope_pct_per_100cyc:.2f}%/100cyc",
            ha="center", va="bottom", fontsize=7.5, color="#333",
        )
    ax0.set_ylabel("SoHQ (%)", fontsize=9)
    ax0.set_xlabel(x_label, fontsize=9)
    ax0.set_title("SoHQ fade with inflection / regime breakpoints", fontsize=10)
    ax0.grid(True, alpha=0.3)
    ax0.legend(fontsize=7.5, loc="best")

    ax1 = fig.add_subplot(gs[1, 0], sharex=ax0)
    ax1.plot(x, result.fade_rate, color="#d62728", linewidth=1.4, label="fade rate (smooth)")
    ax1.axhline(0.0, color="k", linewidth=0.6, alpha=0.4)
    for i, bp in enumerate(result.inflections):
        xv = bp.tagged_cycle if bp.tagged_cycle is not None else bp.cycle
        ax1.axvline(xv, color=colors[i % len(colors)], linestyle="--", linewidth=1.2, alpha=0.85)
    ax1.set_ylabel("dSoHQ / 100 cyc (%)", fontsize=9)
    ax1.set_xlabel(x_label, fontsize=9)
    ax1.set_title("Local fade rate (1st derivative of smooth SoHQ)", fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8, loc="best")

    # Right: regime + breakpoint tables as text
    ax_t = fig.add_subplot(gs[:, 1])
    ax_t.axis("off")
    lines = ["Regime segments", "─" * 42]
    for r in result.regimes:
        xs = r.tagged_start if r.tagged_start is not None else r.cycle_start
        xe = r.tagged_end if r.tagged_end is not None else r.cycle_end
        lines.append(
            f"S{r.seg_id}: cyc {xs:.0f}–{xe:.0f}  "
            f"SoHQ {r.sohq_start:.1f}→{r.sohq_end:.1f}%  "
            f"slope={r.slope_pct_per_100cyc:+.2f}%/100cyc"
        )
    lines.append("")
    lines.append("Breakpoints")
    lines.append("─" * 42)
    if not result.inflections:
        lines.append("(none detected — nearly single-regime fade)")
    for i, bp in enumerate(result.inflections, start=1):
        xv = bp.tagged_cycle if bp.tagged_cycle is not None else bp.cycle
        lines.append(
            f"BP{i}: cyc={xv:.0f}  SoHQ={bp.sohq:.1f}%  "
            f"rate {bp.fade_rate_before:+.2f} → {bp.fade_rate_after:+.2f}%/100cyc"
        )
    lines.append("")
    lines.append(f"method={method}  n={len(x)}  cell={cid}")
    ax_t.text(
        0.02, 0.98, "\n".join(lines),
        transform=ax_t.transAxes, va="top", ha="left",
        fontsize=8.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f7f9fc", edgecolor="#ccd"),
    )

    fig.suptitle(
        title or f"SoHQ inflection / fade regimes — {cid}",
        fontsize=13, fontweight="bold", y=0.97,
    )
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path, result
