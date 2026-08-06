"""Find indicators that change behavior across SoHQ fade regimes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.analysis.sohq_inflection import detect_sohq_inflections

_EXCLUDE = frozenset({
    "cell_id", "tagged_cycle", "pair_label", "cycle", "tagged_source", "file",
    "SoHQ", "dchgCapa", "chgCapa", "capacity", "f_Q_max",
    "chgCCcapa", "chgCVcapa",
    # capacity / energy proxies (track SoHQ almost 1:1)
    "dchg_E", "chg_E",
    "dchg_dQdV_area_sum", "chg_dQdV_area_sum",
    # Q at SOC0 ≈ discharge Qmax — capacity proxy, not dV/dQ intensity
    "dchg_dVdQ_SOC0_Q",
    "dchg_dVdQ_peak1_Q", "dchg_dVdQ_peak2_Q", "dchg_dVdQ_peak3_Q",
    "chg_dVdQ_peak1_Q", "chg_dVdQ_peak2_Q", "chg_dVdQ_peak3_Q",
})


def _x_col(df: pd.DataFrame) -> str:
    if "tagged_cycle" in df.columns and pd.to_numeric(df["tagged_cycle"], errors="coerce").notna().any():
        return "tagged_cycle"
    return "cycle"


def _numeric_cols(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        base = c[6:] if c.startswith("delta_") else c
        if c in _EXCLUDE or base in _EXCLUDE:
            continue
        if c.endswith("_inc") and c[:-4] in _EXCLUDE:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().sum() < 40:
            continue
        if float(s.std(skipna=True) or 0) < 1e-12:
            continue
        cols.append(c)
    return cols


def screen_regime_singularities(
    features: pd.DataFrame,
    *,
    breakpoints: list[float] | None = None,
    window: int = 15,
) -> pd.DataFrame:
    """Rank indicators by slope/jump/correlation change across SoHQ regimes.

    If ``breakpoints`` is None, uses ``detect_sohq_inflections`` (hybrid).
    """
    if features is None or features.empty:
        return pd.DataFrame()

    work = features.copy()
    x_col = _x_col(work)
    work[x_col] = pd.to_numeric(work[x_col], errors="coerce")
    work = work.dropna(subset=[x_col]).sort_values(x_col)

    if breakpoints is None:
        infl = detect_sohq_inflections(work, max_breaks=2, method="hybrid")
        if infl is None or not infl.inflections:
            return pd.DataFrame()
        breakpoints = [
            float(bp.tagged_cycle if bp.tagged_cycle is not None else bp.cycle)
            for bp in infl.inflections
        ]
    breakpoints = sorted(float(b) for b in breakpoints)
    if len(breakpoints) < 1:
        return pd.DataFrame()

    x = work[x_col]
    sohq = pd.to_numeric(work["SoHQ"], errors="coerce") if "SoHQ" in work.columns else None

    # Build regime masks from ordered breakpoints
    edges = [float("-inf")] + breakpoints + [float("inf")]
    masks = [(x > edges[i]) & (x <= edges[i + 1]) for i in range(len(edges) - 1)]
    # first regime includes left edge
    masks[0] = x <= breakpoints[0]

    rows: list[dict] = []
    for col in _numeric_cols(work):
        s = pd.to_numeric(work[col], errors="coerce")
        std = float(s.std(skipna=True))
        if std <= 0:
            continue

        slopes, corrs, means = [], [], []
        for m in masks:
            xx = x[m & s.notna()].to_numpy(dtype=float)
            yy = s[m & s.notna()].to_numpy(dtype=float)
            if len(xx) < 10:
                slopes.append(np.nan)
                means.append(np.nan)
                corrs.append(np.nan)
                continue
            slopes.append(float(np.polyfit(xx, yy, 1)[0]))
            means.append(float(yy.mean()))
            if sohq is not None:
                a = s[m]
                b = sohq[m]
                ok = a.notna() & b.notna()
                corrs.append(float(a[ok].corr(b[ok])) if ok.sum() >= 10 else np.nan)
            else:
                corrs.append(np.nan)

        jumps = []
        for b in breakpoints:
            pre = s[(x >= b - window) & (x < b)].mean()
            post = s[(x > b) & (x <= b + window)].mean()
            jumps.append(float(post - pre) if np.isfinite(pre) and np.isfinite(post) else np.nan)

        d_slopes = [
            abs(slopes[i + 1] - slopes[i])
            if np.isfinite(slopes[i]) and np.isfinite(slopes[i + 1]) else np.nan
            for i in range(len(slopes) - 1)
        ]
        # correlation sign flip between adjacent regimes
        sign_flips = 0
        for i in range(len(corrs) - 1):
            if np.isfinite(corrs[i]) and np.isfinite(corrs[i + 1]):
                if abs(corrs[i]) >= 0.4 and abs(corrs[i + 1]) >= 0.4 and corrs[i] * corrs[i + 1] < 0:
                    sign_flips += 1

        score = sum((d or 0) / std for d in d_slopes)
        score += sum(abs(j or 0) / std for j in jumps)
        score += 1.5 * sign_flips  # prioritize sign flips

        row: dict = {
            "feature": col,
            "score": round(score, 4),
            "sign_flips": sign_flips,
            "std": std,
        }
        for i, sl in enumerate(slopes, start=1):
            row[f"slope_S{i}"] = sl
        for i, d in enumerate(d_slopes, start=1):
            row[f"d_slope_{i}{i+1}"] = d
        for i, jv in enumerate(jumps):
            row[f"jump_bp{i+1}"] = jv
            row[f"bp{i+1}"] = breakpoints[i]
        for i, r in enumerate(corrs, start=1):
            row[f"r_S{i}"] = r
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["sign_flips", "score"], ascending=[False, False]).reset_index(drop=True)


def plot_regime_singularity_report(
    features: pd.DataFrame,
    out_path: Path | str,
    *,
    breakpoints: list[float] | None = None,
    top_n: int = 6,
    title: str | None = None,
    dpi: int = 140,
) -> tuple[Path, pd.DataFrame] | tuple[None, None]:
    """PNG: SoHQ regimes + top singularity indicators (minmax trends)."""
    screened = screen_regime_singularities(features, breakpoints=breakpoints)
    if screened.empty:
        return None, None

    from cyclediag.analysis.sohq_inflection import detect_sohq_inflections

    infl = detect_sohq_inflections(features, max_breaks=2, method="hybrid")
    if breakpoints is None and infl is not None:
        breakpoints = [
            float(bp.tagged_cycle if bp.tagged_cycle is not None else bp.cycle)
            for bp in infl.inflections
        ]
    breakpoints = breakpoints or []

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    work = features.copy()
    x_col = _x_col(work)
    work[x_col] = pd.to_numeric(work[x_col], errors="coerce")
    work["SoHQ"] = pd.to_numeric(work["SoHQ"], errors="coerce")
    work = work.dropna(subset=[x_col, "SoHQ"]).sort_values(x_col)
    x = work[x_col].to_numpy(dtype=float)
    sohq = work["SoHQ"].to_numpy(dtype=float)

    # Prefer sign-flip features, then high score
    top = screened.head(top_n)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_feat = len(top)
    fig = plt.figure(figsize=(14, 3.2 + 1.7 * n_feat), facecolor="white")
    gs = GridSpec(n_feat + 1, 1, figure=fig, hspace=0.35, left=0.08, right=0.78, top=0.92, bottom=0.05)

    ax0 = fig.add_subplot(gs[0, 0])
    ax0.plot(x, sohq, color="#1f77b4", linewidth=1.6, label="SoHQ")
    colors_bp = ("#e74c3c", "#e67e22", "#9b59b6")
    for i, b in enumerate(breakpoints):
        ax0.axvline(b, color=colors_bp[i % len(colors_bp)], linestyle="--", linewidth=1.4,
                    label=f"BP{i+1}={b:.0f}")
    ax0.set_ylabel("SoHQ %", fontsize=8)
    ax0.set_title("SoHQ regimes (reference)", fontsize=9)
    ax0.grid(True, alpha=0.3)
    ax0.legend(fontsize=7, loc="best")

    palette = ("#e67e22", "#27ae60", "#8e44ad", "#16a085", "#c0392b", "#2980b9")
    x_label = "Tagged cycle #" if x_col == "tagged_cycle" else "Cycle"

    for i, (_, row) in enumerate(top.iterrows()):
        ax = fig.add_subplot(gs[i + 1, 0], sharex=ax0)
        feat = str(row["feature"])
        if feat not in work.columns:
            continue
        y = pd.to_numeric(work[feat], errors="coerce")
        y_mm = (y - y.min()) / (y.max() - y.min()) if y.max() > y.min() else y * 0
        ax.plot(x, y_mm, color=palette[i % len(palette)], linewidth=1.3)
        for j, b in enumerate(breakpoints):
            ax.axvline(b, color=colors_bp[j % len(colors_bp)], linestyle="--", linewidth=1.1, alpha=0.8)
        # annotate regime correlations
        rs = [row.get(f"r_S{k}") for k in (1, 2, 3)]
        rtxt = "  ".join(
            f"S{k}:r={rs[k-1]:+.2f}" if rs[k - 1] == rs[k - 1] else f"S{k}:r=—"
            for k in (1, 2, 3)
        )
        flip = "  ★sign-flip" if int(row.get("sign_flips", 0) or 0) > 0 else ""
        ax.set_ylabel("minmax", fontsize=7)
        ax.set_title(f"{feat}{flip}   {rtxt}", fontsize=8, loc="left")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.25)
        if i == n_feat - 1:
            ax.set_xlabel(x_label, fontsize=8)

    # side note
    fig.text(
        0.80, 0.5,
        "Singularity = slope jump\nand/or SoHQ-corr\nsign flip across\nS1|S2|S3\n\n"
        + "\n".join(
            f"{i+1}. {r.feature}" + (" ★" if int(r.sign_flips or 0) else "")
            for i, r in top.iterrows()
        ),
        fontsize=8, va="center", family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f7f9fc", edgecolor="#ccd"),
    )

    cid = str(work["cell_id"].iloc[0]) if "cell_id" in work.columns else "cell"
    fig.suptitle(
        title or f"Regime singularity indicators — {cid}",
        fontsize=12, fontweight="bold",
    )
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path, screened


def _resolve_breakpoints(
    features: pd.DataFrame,
    breakpoints: list[float] | None,
) -> list[float]:
    if breakpoints is not None:
        return sorted(float(b) for b in breakpoints)
    infl = detect_sohq_inflections(features, max_breaks=2, method="hybrid")
    if infl is None or not infl.inflections:
        return []
    return [
        float(bp.tagged_cycle if bp.tagged_cycle is not None else bp.cycle)
        for bp in infl.inflections
    ]


def _regime_masks(x: pd.Series, breakpoints: list[float]) -> list[pd.Series]:
    """Boolean masks for regimes split by breakpoints (inclusive left of each BP)."""
    bps = sorted(breakpoints)
    masks: list[pd.Series] = []
    for i, b in enumerate(bps):
        if i == 0:
            masks.append(x <= b)
        else:
            masks.append((x > bps[i - 1]) & (x <= b))
    masks.append(x > bps[-1])
    return masks


def rank_sohq_drivers_by_regime(
    features: pd.DataFrame,
    *,
    breakpoints: list[float] | None = None,
    top_n: int = 8,
    min_points: int = 15,
) -> pd.DataFrame:
    """Per-regime SoHQ correlation ranking (degradation drivers).

    Returns long table with columns:
    regime, cycle_start, cycle_end, n, feature, pearson_r, abs_r, slope, rank
    """
    if features is None or features.empty or "SoHQ" not in features.columns:
        return pd.DataFrame()

    work = features.copy()
    x_col = _x_col(work)
    work[x_col] = pd.to_numeric(work[x_col], errors="coerce")
    work["SoHQ"] = pd.to_numeric(work["SoHQ"], errors="coerce")
    work = work.dropna(subset=[x_col, "SoHQ"]).sort_values(x_col)
    bps = _resolve_breakpoints(work, breakpoints)
    if not bps:
        return pd.DataFrame()

    x = work[x_col]
    sohq = work["SoHQ"]
    masks = _regime_masks(x, bps)
    cols = _numeric_cols(work)
    rows: list[dict] = []

    for seg_id, m in enumerate(masks, start=1):
        xx = x[m]
        if xx.empty:
            continue
        cyc_lo, cyc_hi = float(xx.min()), float(xx.max())
        n_pts = int(m.sum())
        y_sohq = sohq[m]
        for col in cols:
            s = pd.to_numeric(work.loc[m, col], errors="coerce")
            ok = s.notna() & y_sohq.notna()
            if int(ok.sum()) < min_points:
                continue
            r = float(s[ok].corr(y_sohq[ok]))
            if not np.isfinite(r):
                continue
            xv = xx[ok].to_numpy(dtype=float)
            yv = s[ok].to_numpy(dtype=float)
            slope = float(np.polyfit(xv, yv, 1)[0]) if len(xv) >= 2 else float("nan")
            rows.append({
                "regime": f"S{seg_id}",
                "cycle_start": cyc_lo,
                "cycle_end": cyc_hi,
                "n": n_pts,
                "feature": col,
                "pearson_r": r,
                "abs_r": abs(r),
                "slope": slope,
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    parts = []
    for reg, grp in out.groupby("regime", sort=True):
        g = grp.sort_values("abs_r", ascending=False).head(top_n).copy()
        g["rank"] = range(1, len(g) + 1)
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def plot_regime_driver_report(
    features: pd.DataFrame,
    out_path: Path | str,
    *,
    breakpoints: list[float] | None = None,
    top_n: int = 8,
    title: str | None = None,
    dpi: int = 140,
) -> tuple[Path, pd.DataFrame] | tuple[None, None]:
    """PNG: per-regime |r vs SoHQ| bar charts + summary text."""
    drivers = rank_sohq_drivers_by_regime(
        features, breakpoints=breakpoints, top_n=top_n,
    )
    if drivers.empty:
        return None, None

    bps = _resolve_breakpoints(features, breakpoints)
    work = features.copy()
    x_col = _x_col(work)
    work[x_col] = pd.to_numeric(work[x_col], errors="coerce")
    work["SoHQ"] = pd.to_numeric(work["SoHQ"], errors="coerce")
    work = work.dropna(subset=[x_col, "SoHQ"]).sort_values(x_col)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    regimes = sorted(drivers["regime"].unique())
    n_reg = len(regimes)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14.5, 8.5), facecolor="white")
    gs = GridSpec(
        2, n_reg, figure=fig,
        height_ratios=[1.0, 1.35],
        hspace=0.38, wspace=0.28,
        left=0.07, right=0.98, top=0.88, bottom=0.06,
    )

    # Top: SoHQ with regimes
    ax_sohq = fig.add_subplot(gs[0, :])
    x = work[x_col].to_numpy(dtype=float)
    sohq = work["SoHQ"].to_numpy(dtype=float)
    ax_sohq.plot(x, sohq, color="#1f77b4", linewidth=1.8, label="SoHQ")
    bp_colors = ("#e74c3c", "#e67e22", "#9b59b6")
    for i, b in enumerate(bps):
        ax_sohq.axvline(b, color=bp_colors[i % len(bp_colors)], linestyle="--",
                        linewidth=1.4, label=f"BP{i+1}={b:.0f}")
    # shade regimes
    edges = [float(x.min())] + bps + [float(x.max())]
    shade = ("#d6eaf8", "#fdebd0", "#e8daef", "#d5f5e3")
    for i in range(len(edges) - 1):
        ax_sohq.axvspan(edges[i], edges[i + 1], color=shade[i % len(shade)], alpha=0.35)
        mid = 0.5 * (edges[i] + edges[i + 1])
        sub = drivers[drivers["regime"] == f"S{i+1}"]
        if not sub.empty:
            lo, hi = sub["cycle_start"].iloc[0], sub["cycle_end"].iloc[0]
            ax_sohq.text(
                mid, float(np.nanmax(sohq)) - 1.5,
                f"S{i+1}\n{lo:.0f}–{hi:.0f}",
                ha="center", va="top", fontsize=8, color="#333",
            )
    x_label = "Tagged cycle #" if x_col == "tagged_cycle" else "Cycle"
    ax_sohq.set_xlabel(x_label, fontsize=9)
    ax_sohq.set_ylabel("SoHQ (%)", fontsize=9)
    ax_sohq.set_title("Fade regimes (SoHQ)", fontsize=10)
    ax_sohq.grid(True, alpha=0.3)
    ax_sohq.legend(fontsize=8, loc="best")

    # Bottom: one bar chart per regime
    for i, reg in enumerate(regimes):
        ax = fig.add_subplot(gs[1, i])
        sub = drivers[drivers["regime"] == reg].sort_values("abs_r", ascending=True)
        colors = ["#c0392b" if r < 0 else "#2980b9" for r in sub["pearson_r"]]
        ax.barh(sub["feature"], sub["pearson_r"], color=colors, edgecolor="none", height=0.72)
        ax.axvline(0.0, color="#333", linewidth=0.8)
        ax.set_xlim(-1.05, 1.05)
        lo = sub["cycle_start"].iloc[0]
        hi = sub["cycle_end"].iloc[0]
        n = int(sub["n"].iloc[0])
        ax.set_title(f"{reg}: cyc {lo:.0f}–{hi:.0f} (n={n})\nTop |r vs SoHQ|", fontsize=9)
        ax.set_xlabel("Pearson r vs SoHQ", fontsize=8)
        ax.tick_params(axis="y", labelsize=7.5)
        ax.grid(True, axis="x", alpha=0.3)
        for y_pos, r in enumerate(sub["pearson_r"]):
            ax.text(
                float(r) + (0.03 if r >= 0 else -0.03), y_pos,
                f"{r:.2f}",
                va="center", ha="left" if r >= 0 else "right",
                fontsize=7, color="#222",
            )

    cid = str(work["cell_id"].iloc[0]) if "cell_id" in work.columns else "cell"
    fig.suptitle(
        title or f"Per-regime SoHQ drivers — {cid}",
        fontsize=13, fontweight="bold", y=0.97,
    )
    fig.text(
        0.5, 0.915,
        "blue = +corr with SoHQ   |   red = −corr with SoHQ   |   capacity columns excluded",
        ha="center", fontsize=8.5, color="#555",
    )
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path, drivers
