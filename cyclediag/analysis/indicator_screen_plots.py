"""One-page PNG report: indicators ranked by correlation with SoHQ."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.analysis.indicator_screen import _health_column, screen_indicators
from cyclediag.features.indicator_registry import ROLE_INDICATOR, role_of


def _pick_cell_features(features: pd.DataFrame, cell_id: str | None) -> pd.DataFrame:
    if features is None or features.empty:
        return pd.DataFrame()
    work = features.copy()
    if cell_id and "cell_id" in work.columns:
        sub = work[work["cell_id"].astype(str) == str(cell_id)]
        if not sub.empty:
            return sub
    if "cell_id" in work.columns and work["cell_id"].nunique() > 1:
        first = work["cell_id"].iloc[0]
        return work[work["cell_id"] == first]
    return work


def _rank_by_health(
    screened: pd.DataFrame,
    *,
    top_n: int = 15,
    health_col: str = "SoHQ",
) -> pd.DataFrame:
    if screened is None or screened.empty or "corr_health" not in screened.columns:
        return pd.DataFrame()
    rank = screened.copy()
    # Health targets correlate with health by definition; family aliases would
    # otherwise occupy several of the top slots with one physical signal.
    roles = rank["role"] if "role" in rank.columns else rank["feature"].map(role_of)
    rank = rank[roles == ROLE_INDICATOR]
    if "is_family_primary" in rank.columns:
        rank = rank[rank["is_family_primary"].astype(bool)]
    rank["corr_health"] = pd.to_numeric(rank["corr_health"], errors="coerce")
    rank = rank.dropna(subset=["corr_health"])
    if rank.empty:
        return rank
    rank["abs_r"] = rank["corr_health"].abs()
    rank = rank.sort_values("abs_r", ascending=False).head(top_n)
    return rank.reset_index(drop=True)


def _minmax(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce")
    lo, hi = v.min(), v.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return v * 0.0
    return (v - lo) / (hi - lo)


def plot_sohq_correlation_report(
    features: pd.DataFrame,
    out_path: Path | str,
    *,
    cell_id: str | None = None,
    screened: pd.DataFrame | None = None,
    top_n: int = 12,
    trend_n: int = 4,
    title: str | None = None,
    dpi: int = 140,
) -> Path | None:
    """Save a single-page PNG: SoHQ-corr ranking + trends + scatters.

    Layout
    ------
    Left  : horizontal bars of top indicators by |r vs SoHQ|
    Right : SoHQ vs cycle + top-N indicators (minmax) overlaid with SoHQ
    Bottom: scatter of top 3 indicators vs SoHQ
    """
    work = _pick_cell_features(features, cell_id)
    if work.empty or "cycle" not in work.columns:
        return None

    hcol = _health_column(work)
    if hcol is None:
        return None

    if screened is None or screened.empty:
        screened = screen_indicators(work, health_col=hcol)
    elif "cell_id" in screened.columns and "cell_id" in work.columns:
        cid = work["cell_id"].iloc[0]
        sub = screened[screened["cell_id"].astype(str) == str(cid)]
        if not sub.empty:
            screened = sub

    ranked = _rank_by_health(screened, top_n=top_n, health_col=hcol)
    if ranked.empty:
        return None

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cid = str(work["cell_id"].iloc[0]) if "cell_id" in work.columns else "cell"
    n_cyc = int(pd.to_numeric(work["cycle"], errors="coerce").nunique())
    sohq = pd.to_numeric(work[hcol], errors="coerce")
    sohq_end = float(sohq.dropna().iloc[-1]) if sohq.notna().any() else float("nan")

    fig = plt.figure(figsize=(14.5, 8.2), facecolor="white")
    gs = GridSpec(
        2, 2, figure=fig,
        height_ratios=[1.35, 1.0],
        width_ratios=[1.15, 1.0],
        hspace=0.38, wspace=0.32,
        left=0.08, right=0.98, top=0.88, bottom=0.08,
    )

    # --- Left: ranking bars ---
    ax_bar = fig.add_subplot(gs[:, 0])
    plot_df = ranked.iloc[::-1]  # low at bottom → high at top
    colors = ["#c0392b" if r < 0 else "#2980b9" for r in plot_df["corr_health"]]
    ax_bar.barh(
        plot_df["feature"], plot_df["corr_health"],
        color=colors, edgecolor="none", height=0.72,
    )
    ax_bar.axvline(0.0, color="#333", linewidth=0.8)
    ax_bar.set_xlim(-1.05, 1.05)
    ax_bar.set_xlabel(f"Pearson r vs {hcol}", fontsize=9)
    ax_bar.set_title(f"Top {len(ranked)} indicators by |r vs {hcol}|", fontsize=11, pad=8)
    ax_bar.grid(True, axis="x", alpha=0.3)
    ax_bar.tick_params(axis="y", labelsize=8)
    for y, (feat, r) in enumerate(zip(plot_df["feature"], plot_df["corr_health"])):
        ax_bar.text(
            float(r) + (0.03 if r >= 0 else -0.03), y,
            f"{r:.3f}",
            va="center", ha="left" if r >= 0 else "right",
            fontsize=7.5, color="#222",
        )

    # --- Right top: SoHQ + top indicators (normalized) vs cycle ---
    ax_tr = fig.add_subplot(gs[0, 1])
    x_col = "tagged_cycle" if "tagged_cycle" in work.columns and work["tagged_cycle"].notna().any() else "cycle"
    x_label = "Tagged cycle #" if x_col == "tagged_cycle" else "Cycle"
    x = pd.to_numeric(work[x_col], errors="coerce")
    ax_tr.plot(
        x, _minmax(sohq), color="#111111", linewidth=2.0,
        label=f"{hcol} (minmax)", zorder=5,
    )
    trend_feats = ranked["feature"].head(trend_n).tolist()
    palette = ("#e67e22", "#27ae60", "#8e44ad", "#16a085", "#d35400")
    for i, feat in enumerate(trend_feats):
        if feat not in work.columns:
            continue
        r = float(ranked.loc[ranked["feature"] == feat, "corr_health"].iloc[0])
        ax_tr.plot(
            x, _minmax(work[feat]),
            color=palette[i % len(palette)], linewidth=1.3, alpha=0.9,
            label=f"{feat} (r={r:.2f})",
        )
    ax_tr.set_xlabel(x_label, fontsize=9)
    ax_tr.set_ylabel("Min–max scaled", fontsize=9)
    ax_tr.set_title(f"{hcol} vs top indicators (scaled)", fontsize=10)
    ax_tr.set_ylim(-0.05, 1.05)
    ax_tr.grid(True, alpha=0.3)
    ax_tr.legend(fontsize=7, loc="best", framealpha=0.9)

    # --- Bottom right: 3 scatters ---
    scatter_feats = ranked["feature"].head(3).tolist()
    if scatter_feats:
        inner = gs[1, 1].subgridspec(1, len(scatter_feats), wspace=0.35)
        y_sohq = sohq.to_numpy(dtype=float)
        for i, feat in enumerate(scatter_feats):
            ax = fig.add_subplot(inner[0, i])
            xv = pd.to_numeric(work[feat], errors="coerce").to_numpy(dtype=float)
            mask = np.isfinite(xv) & np.isfinite(y_sohq)
            ax.scatter(xv[mask], y_sohq[mask], s=12, alpha=0.55, color=palette[i % len(palette)], edgecolors="none")
            r = float(ranked.loc[ranked["feature"] == feat, "corr_health"].iloc[0])
            ax.set_title(f"{feat}\nr={r:.3f}", fontsize=8)
            ax.set_xlabel(feat, fontsize=7)
            if i == 0:
                ax.set_ylabel(hcol, fontsize=8)
            ax.grid(True, alpha=0.25)
            ax.tick_params(labelsize=7)

    sohq_txt = f"{sohq_end:.1f}%" if np.isfinite(sohq_end) else "—"
    fig.suptitle(
        title or f"SoHQ correlation report — {cid}",
        fontsize=13, fontweight="bold", y=0.97,
    )
    fig.text(
        0.5, 0.915,
        f"n={n_cyc} cycles  |  {hcol}_end={sohq_txt}  |  blue=+corr, red=−corr"
        "  |  one representative per indicator family, targets excluded",
        ha="center", fontsize=8.5, color="#555",
    )

    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path
