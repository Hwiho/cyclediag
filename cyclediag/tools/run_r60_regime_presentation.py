"""EoC_dchgR_60s regime presentation: SJ900 set4 vs SJ1300 dry.

Uses precomputed r60 CSVs (or regenerates) and SoHQ BP1/BP2 windows.
SoHQ-style panels: R60 trajectory + local dR/100cyc with S1–S3 slopes.

Example::

    python -m cyclediag.tools.run_r60_regime_presentation \\
        --src example/output/crossover_vs_sohq/present_1600x1000/r60_ec2 \\
        --out example/output/crossover_vs_sohq/present_1600x1000/r60_regimes
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

W_IN, H_IN, DPI = 10.0, 6.25, 140
EDGE = ["#1565c0", "#c62828", "#6a1b9a"]
SPAN = ["#bbdefb", "#ffcdd2", "#e1bee7"]
CELL_COLOR = {
    "M01Ch022": "#1565c0",
    "M01Ch024": "#2e7d32",
    "M01Ch025": "#00838f",
    "M01Ch010": "#c62828",
    "M01Ch011": "#ef6c00",
    "M01Ch012": "#6a1b9a",
}
ARMS = ("set4_SJ900", "SJ1300_dry")


def style(ax) -> None:
    ax.grid(True, alpha=0.28)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)


def smooth(y: np.ndarray, win: int = 11) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    if len(y) < win:
        return y.copy()
    k = np.ones(win) / win
    pad = win // 2
    yp = np.pad(y, (pad, pad), mode="edge")
    out = np.convolve(yp, k, mode="valid")
    return out[: len(y)]


def local_slope_per_100(x: np.ndarray, y: np.ndarray, half: int = 15) -> np.ndarray:
    """Rolling linear slope * 100 (units of y per 100 tagged cycles)."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        if hi - lo < 5:
            continue
        xx, yy = x[lo:hi], y[lo:hi]
        m = np.isfinite(xx) & np.isfinite(yy)
        if m.sum() < 5:
            continue
        out[i] = float(np.polyfit(xx[m], yy[m], 1)[0]) * 100.0
    return out


def regimes_from_bps(x: np.ndarray, y: np.ndarray, bp1, bp2) -> list[dict]:
    edges = [float(np.nanmin(x))]
    if bp1 is not None and np.isfinite(bp1):
        edges.append(float(bp1))
    if bp2 is not None and np.isfinite(bp2):
        edges.append(float(bp2))
    edges.append(float(np.nanmax(x)) + 1e-9)
    edges = sorted(set(edges))
    rows = []
    for i in range(len(edges) - 1):
        m = (x >= edges[i]) & (x < edges[i + 1]) & np.isfinite(y)
        if m.sum() < 5:
            continue
        xx, yy = x[m], y[m]
        slope = float(np.polyfit(xx, yy, 1)[0])
        rows.append(
            {
                "seg_id": i + 1,
                "tagged_start": float(xx.min()),
                "tagged_end": float(xx.max()),
                "y_start": float(yy[0]),
                "y_end": float(yy[-1]),
                "delta": float(yy[-1] - yy[0]),
                "slope_per_100cyc": slope * 100.0,
                "n": int(m.sum()),
            }
        )
    return rows


def plot_cell_regime(df: pd.DataFrame, out: Path) -> list[dict]:
    cell = str(df["cell_id"].iloc[0])
    arm = str(df["arm"].iloc[0])
    x = df["tagged_cycle"].to_numpy(float)
    y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce").to_numpy(float)
    ys = smooth(y, 11)
    d_local = local_slope_per_100(x, ys, half=15)
    bp1 = df["BP1_tagged"].iloc[0]
    bp2 = df["BP2_tagged"].iloc[0]
    regs = regimes_from_bps(x, ys, bp1, bp2)

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.10, top=0.88, hspace=0.16)

    ax = axes[0]
    ax.plot(x, y, color="#a0c4e8", lw=1.0, alpha=0.65, label="R60 raw")
    ax.plot(x, ys, color="#1565c0", lw=2.1, label="R60 smooth")
    for i, r in enumerate(regs):
        ax.axvspan(r["tagged_start"], r["tagged_end"], color=SPAN[i % 3], alpha=0.20, zorder=0)
    ymin = float(np.nanmin(ys[np.isfinite(ys)])) - 0.02
    ymax = float(np.nanmax(ys[np.isfinite(ys)])) + 0.02
    head = (ymax - ymin) * 0.32
    ax.set_ylim(ymin, ymax + head)
    for i, r in enumerate(regs):
        mid = 0.5 * (r["tagged_start"] + r["tagged_end"])
        ax.text(
            mid,
            ymax + head * 0.55,
            f"S{r['seg_id']}: {r['slope_per_100cyc']:+.3f} mΩ/100cyc",
            ha="center",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=EDGE[i % 3],
            bbox=dict(
                boxstyle="round,pad=0.28",
                facecolor="white",
                edgecolor=EDGE[i % 3],
                lw=1.2,
                alpha=0.98,
            ),
            zorder=10,
            clip_on=False,
        )
    for t, lab, col, ls in ((bp1, "BP1", "#1565c0", "--"), (bp2, "BP2", "#6a1b9a", "-.")):
        if t is None or not np.isfinite(t):
            continue
        j = int(np.argmin(np.abs(x - t)))
        ax.axvline(t, color=col, ls=ls, lw=1.7)
        ax.scatter([t], [ys[j]], color=col, s=55, zorder=5, edgecolors="k", linewidths=0.4)
        ax.text(t + 6, ys[j] + (ymax - ymin) * 0.08, lab, color=col, fontsize=10, fontweight="bold")
    ax.set_ylabel("EoC_dchgR_60s [mΩ]")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title(f"{arm} / {cell} — EoC_dchgR_60s regimes (SoHQ BP windows)", fontweight="bold")
    style(ax)

    ax = axes[1]
    ax.plot(x, d_local, color="#d62728", lw=1.7, label="local dR60/100cyc")
    ax.axhline(0, color="k", lw=0.7, alpha=0.4)
    finite = d_local[np.isfinite(d_local)]
    fmin = float(np.nanmin(finite)) if len(finite) else -0.1
    fmax = float(np.nanmax(finite)) if len(finite) else 0.1
    pad = max(0.05, (fmax - fmin) * 0.25)
    lab_y = fmin - pad
    ax.set_ylim(lab_y - pad * 0.4, fmax + pad * 0.35)
    for i, r in enumerate(regs):
        col = EDGE[i % 3]
        ax.hlines(r["slope_per_100cyc"], r["tagged_start"], r["tagged_end"], colors=col, lw=2.4)
        mid = 0.5 * (r["tagged_start"] + r["tagged_end"])
        ax.text(
            mid,
            lab_y,
            f"S{r['seg_id']} {r['slope_per_100cyc']:+.3f}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=col,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=col, alpha=0.98),
            clip_on=False,
        )
    if bp1 is not None and np.isfinite(bp1):
        ax.axvline(bp1, color="#1565c0", ls="--", lw=1.5)
    if bp2 is not None and np.isfinite(bp2):
        ax.axvline(bp2, color="#6a1b9a", ls="-.", lw=1.5)
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("dR60 / 100 cyc [mΩ]")
    ax.legend(loc="upper right", fontsize=9)
    style(ax)
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return regs


def plot_arm_overlay(frames: list[pd.DataFrame], out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(W_IN, H_IN), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.12, top=0.88, wspace=0.12)
    for ax, arm in zip(axes, ARMS):
        for df in frames:
            if df["arm"].iloc[0] != arm:
                continue
            cell = df["cell_id"].iloc[0]
            x = df["tagged_cycle"].to_numpy(float)
            y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce").to_numpy(float)
            ax.plot(x, smooth(y, 11), color=CELL_COLOR.get(cell, "k"), lw=1.8, label=cell)
            bp1, bp2 = df["BP1_tagged"].iloc[0], df["BP2_tagged"].iloc[0]
            if pd.notna(bp1):
                ax.axvline(bp1, color="0.35", ls="--", lw=1.0, alpha=0.55)
            if pd.notna(bp2):
                ax.axvline(bp2, color="0.55", ls="-.", lw=1.0, alpha=0.55)
        ax.set_title(arm, fontweight="bold")
        ax.set_xlabel("Tagged cycle #")
        ax.legend(fontsize=8)
        style(ax)
    axes[0].set_ylabel("EoC_dchgR_60s [mΩ] (smooth)")
    fig.suptitle("EoC_dchgR_60s — SJ900 vs SJ1300 (dashed=BP1, dashdot=BP2)", fontweight="bold")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def plot_slope_bars(slopes: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(W_IN, H_IN), sharey=True)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.14, top=0.86, wspace=0.15)
    for ax, arm in zip(axes, ARMS):
        sub = slopes[slopes["arm"] == arm]
        cells = list(dict.fromkeys(sub["cell_id"]))
        x = np.arange(len(cells))
        w = 0.25
        for i, seg in enumerate((1, 2, 3)):
            vals = []
            for c in cells:
                row = sub[(sub["cell_id"] == c) & (sub["seg_id"] == seg)]
                vals.append(float(row["slope_per_100cyc"].iloc[0]) if len(row) else np.nan)
            ax.bar(x + (i - 1) * w, vals, width=w, color=EDGE[i], label=f"S{seg}", alpha=0.9)
        ax.axhline(0, color="k", lw=0.7, alpha=0.4)
        ax.set_xticks(x)
        ax.set_xticklabels(cells, rotation=15)
        ax.set_title(arm, fontweight="bold")
        ax.legend(fontsize=8)
        style(ax)
    axes[0].set_ylabel("dR60 / 100 cyc [mΩ]")
    fig.suptitle("Regime R60 growth rate (SoHQ BP windows)", fontweight="bold")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def plot_norm_growth(frames: list[pd.DataFrame], out: Path) -> None:
    """R60 / R60(BOL) so arms compare growth shape."""
    fig, ax = plt.subplots(figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.12, top=0.90)
    for df in frames:
        cell = df["cell_id"].iloc[0]
        arm = df["arm"].iloc[0]
        y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce").to_numpy(float)
        bol = float(np.nanmedian(y[:5]))
        if not np.isfinite(bol) or bol <= 0:
            continue
        yn = smooth(y / bol, 11)
        ls = "-" if arm == "set4_SJ900" else "--"
        ax.plot(
            df["tagged_cycle"],
            yn,
            color=CELL_COLOR.get(cell, "k"),
            lw=1.7,
            ls=ls,
            label=f"{arm[-8:] if len(arm)>12 else arm}/{cell}",
        )
    ax.axhline(1.0, color="k", lw=0.7, alpha=0.4)
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("R60 / R60_BOL")
    ax.set_title("Normalized EoC_dchgR_60s growth (solid=SJ900, dashed=SJ1300)", fontweight="bold")
    ax.legend(fontsize=7.5, ncol=2, loc="upper left")
    style(ax)
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--src",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/r60_ec2"),
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/r60_regimes"),
    )
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    cells = ["M01Ch022", "M01Ch024", "M01Ch025", "M01Ch010", "M01Ch011", "M01Ch012"]
    frames: list[pd.DataFrame] = []
    slope_rows: list[dict] = []

    for cell in cells:
        path = args.src / f"{cell}_r60_ec2.csv"
        if not path.exists():
            print(f"missing {path}")
            continue
        df = pd.read_csv(path)
        frames.append(df)
        regs = plot_cell_regime(df, out / f"{cell}_R60_dR_regimes.png")
        for r in regs:
            slope_rows.append({"arm": df["arm"].iloc[0], "cell_id": cell, **r})
        print(f"{cell}: wrote regime panel, n_reg={len(regs)}")

    slopes = pd.DataFrame(slope_rows)
    slopes.to_csv(out / "regime_R60_slopes.csv", index=False)

    plot_arm_overlay(frames, out / "00_R60_by_arm.png")
    plot_slope_bars(slopes, out / "00_R60_regime_slope_bars.png")
    plot_norm_growth(frames, out / "00_R60_normalized_growth.png")

    # arm-level summary table
    rows = []
    for df in frames:
        y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce")
        bp1, bp2 = df["BP1_tagged"].iloc[0], df["BP2_tagged"].iloc[0]
        rows.append(
            {
                "arm": df["arm"].iloc[0],
                "cell_id": df["cell_id"].iloc[0],
                "n_tagged": len(df),
                "R60_BOL": float(y.iloc[:5].mean()),
                "R60_BP1": float(y[(df["tagged_cycle"] - bp1).abs() <= 3].mean())
                if pd.notna(bp1)
                else np.nan,
                "R60_BP2": float(y[(df["tagged_cycle"] - bp2).abs() <= 3].mean())
                if pd.notna(bp2)
                else np.nan,
                "R60_EOL": float(y.iloc[-5:].mean()),
                "growth_BOL_EOL_pct": float(y.iloc[-5:].mean() / y.iloc[:5].mean() - 1.0) * 100.0,
                "BP1_tagged": bp1,
                "BP2_tagged": bp2,
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(out / "R60_arm_summary.csv", index=False)

    # markdown-lite text summary for quick read
    lines = ["# EoC_dchgR_60s — SJ900 vs SJ1300", ""]
    for arm in ARMS:
        sub = summary[summary["arm"] == arm]
        lines.append(f"## {arm}")
        lines.append(
            f"- BOL→EOL growth (mean): {sub['growth_BOL_EOL_pct'].mean():+.1f}% "
            f"(BOL {sub['R60_BOL'].mean():.3f} → EOL {sub['R60_EOL'].mean():.3f} mΩ)"
        )
        arm_sl = slopes[slopes["arm"] == arm]
        for seg in (1, 2, 3):
            ss = arm_sl[arm_sl["seg_id"] == seg]["slope_per_100cyc"]
            if len(ss):
                lines.append(f"- S{seg} dR60/100cyc (mean): {ss.mean():+.4f} mΩ")
        lines.append("")
    (out / "README_R60_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
