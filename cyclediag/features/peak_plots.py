"""Plot Phase 4 peak V/H trajectories vs cycle."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_PLOT_PEAKS = {
    "charge": ["P2_shoulder", "P3_main"],
    "discharge": ["P2_mid", "P3_high"],
}


def plot_peak_trajectories(
    track_df: pd.DataFrame,
    out_dir: Path,
    *,
    cell_id: str,
    peaks: dict[str, list[str]] | None = None,
    usable_only: bool = True,
) -> list[Path]:
    """Save V, H_norm, dV_vs_golden plots per leg/peak_id."""
    out_dir.mkdir(parents=True, exist_ok=True)
    peaks = peaks or DEFAULT_PLOT_PEAKS
    work = track_df.copy()
    if usable_only and "usable" in work.columns:
        work = work[work["usable"]]

    saved: list[Path] = []
    for leg, peak_ids in peaks.items():
        sub = work[(work["leg"] == leg) & (work["peak_id"].isin(peak_ids))]
        if sub.empty:
            continue

        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        fig.suptitle(f"{cell_id} — {leg} peak tracking (usable)")

        for peak_id in peak_ids:
            g = sub[sub["peak_id"] == peak_id].sort_values("cycle")
            if g.empty:
                continue
            axes[0].plot(g["cycle"], g["V"], marker=".", label=peak_id, linewidth=1)
            if g["H_norm"].notna().any():
                axes[1].plot(g["cycle"], g["H_norm"], marker=".", label=peak_id, linewidth=1)
            if g["dV_vs_golden"].notna().any():
                axes[2].plot(g["cycle"], g["dV_vs_golden"], marker=".", label=peak_id, linewidth=1)

        axes[0].set_ylabel("V (V)")
        axes[0].legend(loc="best", fontsize=8)
        axes[0].grid(True, alpha=0.3)
        axes[1].set_ylabel("H_norm")
        axes[1].legend(loc="best", fontsize=8)
        axes[1].grid(True, alpha=0.3)
        axes[2].set_ylabel("dV vs golden")
        axes[2].set_xlabel("TotalCycle")
        axes[2].legend(loc="best", fontsize=8)
        axes[2].axhline(0, color="gray", linewidth=0.8)
        axes[2].grid(True, alpha=0.3)

        path = out_dir / f"{cell_id}_{leg}_peak_tracking.png"
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        saved.append(path)

    return saved
