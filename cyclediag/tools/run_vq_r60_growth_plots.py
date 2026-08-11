"""Combined plots: discharge V-Q + EoC_dchgR_60s + dR60 growth rate.

Uses existing r60_ec2 CSVs when present; otherwise extracts R60 from raw.
Voltage profiles sampled every ``--vq-step`` tagged cycles (default 50).

Example::

    python -m cyclediag.tools.run_vq_r60_growth_plots \\
        --out example/output/crossover_vs_sohq/present_1600x1000/vq_r60_growth
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import pandas as pd

from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv
from cyclediag.features.lges_extract import _resistance_mohm, _sample_v_i_at_offsets
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

W_IN, H_IN, DPI = 10.0, 7.5, 140
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

DEFAULT_CELLS = {
    "M01Ch022": (
        Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"),
        "set4_SJ900",
    ),
    "M01Ch024": (
        Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"),
        "set4_SJ900",
    ),
    "M01Ch025": (
        Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv"),
        "set4_SJ900",
    ),
    "M01Ch010": (
        Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"),
        "SJ1300_dry",
    ),
    "M01Ch011": (
        Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"),
        "SJ1300_dry",
    ),
    "M01Ch012": (
        Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"),
        "SJ1300_dry",
    ),
}

R60_SRC = Path("example/output/crossover_vs_sohq/present_1600x1000/r60_ec2")


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
    return np.convolve(yp, k, mode="valid")[: len(y)]


def local_slope_per_100(x: np.ndarray, y: np.ndarray, half: int = 15) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        if hi - lo < 5:
            continue
        xx, yy = x[lo:hi], y[lo:hi]
        m = np.isfinite(xx) & np.isfinite(yy)
        if m.sum() < 5:
            continue
        out[i] = float(np.polyfit(xx[m], yy[m], 1)[0]) * 100.0
    return out


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="cp949", on_bad_lines="skip")
    return normalize_cycler_dataframe(df, ColumnMap.studio_default())


def tagged_routine_cycles(raw: pd.DataFrame) -> list[int]:
    se = raw.groupby(["cycle", "StepNo"], as_index=False).tail(1)
    prot = build_protocol_exclusion(se)
    flags = detect_protocol_flags(se)
    routine = flags[
        (flags["protocol_kind"] == "routine") & (~flags["cycle"].isin(prot.excluded))
    ].sort_values("cycle")
    return [int(c) for c in routine["cycle"]]


def dchg_qv(raw: pd.DataFrame, cycle: int):
    g = raw[raw["cycle"] == cycle]
    d = leg_segment(g, "discharge", charge_text="charge", discharge_text="discharge")
    if d.empty or "voltage" not in d.columns:
        return None, None
    d = prepare_leg_segment_for_dqdv(d, "discharge")
    v = pd.to_numeric(d["voltage"], errors="coerce").to_numpy(float)
    q = None
    for col in ("discharge_capacity", "capacity"):
        if col in d.columns:
            qq = pd.to_numeric(d[col], errors="coerce").to_numpy(float)
            if np.isfinite(qq).sum() >= 10:
                q = qq
                break
    if q is None:
        return None, None
    m = np.isfinite(v) & np.isfinite(q)
    if m.sum() < 30:
        return None, None
    q, v = q[m], v[m]
    q = q - float(np.nanmin(q))
    order = np.argsort(q)
    return q[order], v[order]


def load_or_build_r60(cell_id: str, path: Path, arm: str, raw: pd.DataFrame, tagged: list[int]) -> pd.DataFrame:
    csv = R60_SRC / f"{cell_id}_r60_ec2.csv"
    if csv.exists():
        return pd.read_csv(csv)
    rows = []
    for tidx, rcyc in enumerate(tagged, start=1):
        g = raw[raw["cycle"] == rcyc]
        d = leg_segment(g, "discharge", charge_text="charge", discharge_text="discharge")
        r = float("nan")
        if not d.empty:
            # raw leg: V_ref at I≈0 onset (figure definition), not dqdv-prep trim
            s = _sample_v_i_at_offsets(d, (0.0, 60.0))
            r0 = _resistance_mohm(s[0.0][0], s[60.0][0], s[60.0][1])
            r = float(r0) if r0 is not None else float("nan")
        rows.append(
            dict(
                arm=arm,
                cell_id=cell_id,
                tagged_cycle=tidx,
                raw_cycle=rcyc,
                EoC_dchgR_60s=r,
                BP1_tagged=np.nan,
                BP2_tagged=np.nan,
            )
        )
    return pd.DataFrame(rows)


def regime_slopes(x, y, bp1, bp2):
    edges = [float(np.nanmin(x))]
    if bp1 is not None and np.isfinite(bp1):
        edges.append(float(bp1))
    if bp2 is not None and np.isfinite(bp2):
        edges.append(float(bp2))
    edges.append(float(np.nanmax(x)) + 1e-9)
    edges = sorted(set(edges))
    regs = []
    for i in range(len(edges) - 1):
        m = (x >= edges[i]) & (x < edges[i + 1]) & np.isfinite(y)
        if m.sum() < 5:
            continue
        xx, yy = x[m], y[m]
        slope = float(np.polyfit(xx, yy, 1)[0]) * 100.0
        regs.append(
            dict(
                seg_id=i + 1,
                tagged_start=float(xx.min()),
                tagged_end=float(xx.max()),
                slope_per_100cyc=slope,
            )
        )
    return regs


def plot_cell_triple(
    cell_id: str,
    arm: str,
    raw: pd.DataFrame,
    tagged: list[int],
    r60: pd.DataFrame,
    *,
    vq_step: int,
    out: Path,
) -> None:
    x = r60["tagged_cycle"].to_numpy(float)
    y = pd.to_numeric(r60["EoC_dchgR_60s"], errors="coerce").to_numpy(float)
    ys = smooth(y, 11)
    d_local = local_slope_per_100(x, ys, half=15)
    bp1 = r60["BP1_tagged"].iloc[0] if "BP1_tagged" in r60.columns else np.nan
    bp2 = r60["BP2_tagged"].iloc[0] if "BP2_tagged" in r60.columns else np.nan
    regs = regime_slopes(x, ys, bp1, bp2)

    # voltage profiles every vq_step
    tmax = int(x.max())
    t_list = list(range(1, tmax + 1, vq_step))
    if 1 not in t_list:
        t_list = [1] + t_list
    profiles = []
    for t in t_list:
        if t > len(tagged):
            continue
        q, v = dchg_qv(raw, tagged[t - 1])
        if q is not None:
            profiles.append((t, q, v))

    fig, axes = plt.subplots(3, 1, figsize=(W_IN, H_IN), sharex=False)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.07, top=0.92, hspace=0.28)

    # --- 1) voltage profile ---
    ax = axes[0]
    if profiles:
        nseg = max(len(profiles) - 1, 1)
        for k, (t, q, v) in enumerate(profiles):
            color = cm.viridis(k / nseg)
            ax.plot(q, v, color=color, lw=1.5 if t != 50 else 2.3, label=f"t{t}")
        ax.legend(loc="lower left", ncol=4, fontsize=7, framealpha=0.92)
    ax.set_ylabel("V")
    ax.set_xlabel("Q [Ah]")
    ax.set_title(
        f"{arm} / {cell_id} — discharge V–Q every {vq_step} tagged cycles",
        fontweight="bold",
    )
    style(ax)

    # --- 2) R60 vs cycle ---
    ax = axes[1]
    ax.plot(x, y, color="#90caf9", lw=0.9, alpha=0.7, label="R60 raw")
    ax.plot(x, ys, color="#1565c0", lw=2.0, label="R60 smooth")
    for i, r in enumerate(regs):
        ax.axvspan(r["tagged_start"], r["tagged_end"], color=SPAN[i % 3], alpha=0.18, zorder=0)
    for t, lab, col, ls in ((bp1, "BP1", "#1565c0", "--"), (bp2, "BP2", "#6a1b9a", "-.")):
        if t is None or not np.isfinite(t):
            continue
        ax.axvline(t, color=col, ls=ls, lw=1.5)
        j = int(np.argmin(np.abs(x - t)))
        ax.scatter([t], [ys[j]], color=col, s=45, zorder=5, edgecolors="k", linewidths=0.4)
        ax.text(t + 4, ys[j], lab, color=col, fontsize=9, fontweight="bold")
    ax.set_ylabel("EoC_dchgR_60s [mΩ]")
    ax.set_xlabel("Tagged cycle #")
    ax.legend(loc="best", fontsize=8)
    ax.set_title("Cycle resistance (discharge start, 60 s)", fontweight="bold")
    style(ax)

    # --- 3) growth rate ---
    ax = axes[2]
    ax.plot(x, d_local, color="#d62728", lw=1.6, label="local dR60 / 100 cyc")
    ax.axhline(0, color="k", lw=0.7, alpha=0.4)
    finite = d_local[np.isfinite(d_local)]
    if len(finite):
        fmin, fmax = float(np.nanmin(finite)), float(np.nanmax(finite))
        pad = max(0.04, (fmax - fmin) * 0.2)
        lab_y = fmin - pad
        ax.set_ylim(lab_y - 0.3 * pad, fmax + 0.35 * pad)
    else:
        lab_y = -0.05
    for i, r in enumerate(regs):
        col = EDGE[i % 3]
        ax.hlines(r["slope_per_100cyc"], r["tagged_start"], r["tagged_end"], colors=col, lw=2.3)
        mid = 0.5 * (r["tagged_start"] + r["tagged_end"])
        ax.text(
            mid,
            lab_y,
            f"S{r['seg_id']} {r['slope_per_100cyc']:+.3f}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=col,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor=col, alpha=0.96),
            clip_on=False,
        )
    if bp1 is not None and np.isfinite(bp1):
        ax.axvline(bp1, color="#1565c0", ls="--", lw=1.4)
    if bp2 is not None and np.isfinite(bp2):
        ax.axvline(bp2, color="#6a1b9a", ls="-.", lw=1.4)
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("dR60 / 100 cyc [mΩ]")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title("Resistance growth rate", fontweight="bold")
    style(ax)

    fig.suptitle(
        f"{arm} / {cell_id} — V profile · R60 · dR60",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def plot_arm_summary(frames: list[pd.DataFrame], out: Path) -> None:
    """Side-by-side arm: R60 + dR60 (no VQ — kept clean)."""
    fig, axes = plt.subplots(2, 2, figsize=(W_IN, H_IN), sharex="col")
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.09, top=0.88, hspace=0.18, wspace=0.18)
    for col, arm in enumerate(("set4_SJ900", "SJ1300_dry")):
        axr, axd = axes[0, col], axes[1, col]
        for df in frames:
            if df["arm"].iloc[0] != arm:
                continue
            cell = df["cell_id"].iloc[0]
            x = df["tagged_cycle"].to_numpy(float)
            y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce").to_numpy(float)
            ys = smooth(y, 11)
            d = local_slope_per_100(x, ys, half=15)
            c = CELL_COLOR.get(cell, "k")
            axr.plot(x, ys, color=c, lw=1.7, label=cell)
            axd.plot(x, d, color=c, lw=1.3, label=cell)
            bp1, bp2 = df["BP1_tagged"].iloc[0], df["BP2_tagged"].iloc[0]
            if pd.notna(bp1):
                axr.axvline(bp1, color="0.4", ls="--", lw=0.9, alpha=0.5)
                axd.axvline(bp1, color="0.4", ls="--", lw=0.9, alpha=0.5)
            if pd.notna(bp2):
                axr.axvline(bp2, color="0.55", ls="-.", lw=0.9, alpha=0.5)
                axd.axvline(bp2, color="0.55", ls="-.", lw=0.9, alpha=0.5)
        axr.set_title(arm, fontweight="bold")
        axd.axhline(0, color="k", lw=0.6, alpha=0.4)
        axd.set_xlabel("Tagged cycle #")
        axr.legend(fontsize=8)
        axd.legend(fontsize=7)
        style(axr)
        style(axd)
    axes[0, 0].set_ylabel("R60 [mΩ]")
    axes[1, 0].set_ylabel("dR60 / 100 cyc [mΩ]")
    fig.suptitle(
        "EoC_dchgR_60s & growth rate — SJ900 vs SJ1300",
        fontweight="bold",
        fontsize=13,
    )
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def plot_arm_vq_compare(
    raws: dict[str, tuple[pd.DataFrame, list[int], str]],
    *,
    t: int,
    out: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(W_IN, 5.5), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.12, top=0.86, wspace=0.12)
    for ax, arm in zip(axes, ("set4_SJ900", "SJ1300_dry")):
        for cell, (raw, tagged, a) in raws.items():
            if a != arm or t > len(tagged):
                continue
            q, v = dchg_qv(raw, tagged[t - 1])
            if q is None:
                continue
            ax.plot(q, v, color=CELL_COLOR.get(cell, "k"), lw=1.8, label=cell)
        ax.set_title(f"{arm} @ t={t}", fontweight="bold")
        ax.set_xlabel("Q [Ah]")
        ax.legend(fontsize=8)
        style(ax)
    axes[0].set_ylabel("V")
    fig.suptitle(f"Discharge voltage profile @ tagged t={t}", fontweight="bold")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/vq_r60_growth"),
    )
    p.add_argument("--vq-step", type=int, default=50)
    p.add_argument("--cells", type=str, default="")
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    want = {c.strip() for c in args.cells.split(",") if c.strip()} or set(DEFAULT_CELLS)
    frames: list[pd.DataFrame] = []
    raws: dict[str, tuple[pd.DataFrame, list[int], str]] = {}

    for cell_id, (path, arm) in DEFAULT_CELLS.items():
        if cell_id not in want or not path.exists():
            continue
        print(f"[{cell_id}] …", flush=True)
        raw = load_raw(path)
        tagged = tagged_routine_cycles(raw)
        r60 = load_or_build_r60(cell_id, path, arm, raw, tagged)
        frames.append(r60)
        raws[cell_id] = (raw, tagged, arm)
        plot_cell_triple(
            cell_id,
            arm,
            raw,
            tagged,
            r60,
            vq_step=args.vq_step,
            out=out / f"{cell_id}_VQ_R60_dR.png",
        )

    if frames:
        plot_arm_summary(frames, out / "00_arm_R60_dR.png")
        for t in (1, 50, 100, 200):
            plot_arm_vq_compare(raws, t=t, out=out / f"00_VQ_arm_t{t:03d}.png")
        pd.concat(frames, ignore_index=True).to_csv(out / "all_R60.csv", index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
