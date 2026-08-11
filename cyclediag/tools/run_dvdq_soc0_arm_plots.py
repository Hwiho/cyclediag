"""dVdQ@SOC0 arm plots in the same 3×2 format as R60 arm figure.

Top:    signed dV/dQ curves every 50 tagged cycles (SJ900=Ch022, SJ1300=Ch012) with SOC0 mark
Middle: dVdQ_SOC0 vs tagged cycle (all cells; Ch025 excluded)
Bottom: increase % vs tagged cycle 1
Shared y-scale within each row (900 vs 1300).
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

from cyclediag.features.dqdv_peaks import (
    DEFAULT_DQDV_PEAK_CONFIG,
    compute_dvdq,
    dvdq_intensity_at_soc,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

W_IN, H_IN, DPI = 10.0, 9.2, 140
CELL_COLOR = {
    "M01Ch022": "#1565c0",
    "M01Ch024": "#2e7d32",
    "M01Ch010": "#c62828",
    "M01Ch011": "#ef6c00",
    "M01Ch012": "#6a1b9a",
}
DEFAULT_CELLS = {
    "M01Ch022": (Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"), "set4_SJ900"),
    "M01Ch024": (Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"), "set4_SJ900"),
    "M01Ch010": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"), "SJ1300_dry"),
    "M01Ch011": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"), "SJ1300_dry"),
    "M01Ch012": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"), "SJ1300_dry"),
}
BP_DIRS = {
    "set4_SJ900": Path("example/output/set4/inflection_tagged"),
    "SJ1300_dry": Path("example/output/SJ1300_dry/inflection_tagged"),
}
V_PROFILE_CELLS = {
    "set4_SJ900": "M01Ch022",
    "SJ1300_dry": "M01Ch012",
}


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
    return np.convolve(np.pad(y, (pad, pad), mode="edge"), k, mode="valid")[: len(y)]


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


def load_bps(cell_id: str, arm: str):
    path = BP_DIRS[arm] / f"{cell_id}_breakpoints.csv"
    if not path.exists():
        return None, None
    bp = pd.read_csv(path)
    t = pd.to_numeric(bp.get("tagged_cycle"), errors="coerce").dropna().to_numpy(float)
    if len(t) == 0:
        return None, None
    return float(t[0]), (float(t[1]) if len(t) > 1 else None)


def dchg_qv(raw: pd.DataFrame, cycle: int):
    g = raw[raw["cycle"] == cycle]
    d = leg_segment(g, "discharge", charge_text="charge", discharge_text="discharge")
    if d.empty:
        return None, None
    d = prepare_leg_segment_for_dqdv(d, "discharge")
    if d.empty or "voltage" not in d.columns:
        return None, None
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


def dvdq_soc0_profile(q: np.ndarray, v: np.ndarray):
    """Return qx, signed dvdq, and SOC0 sample (Q, signed dVdQ)."""
    qx, dvdq = compute_dvdq(q, v, DEFAULT_DQDV_PEAK_CONFIG)
    if len(qx) < 5:
        return None
    samp = dvdq_intensity_at_soc(
        q, v, soc_target=0.0, soc_window=0.02, discharge=True,
        config=DEFAULT_DQDV_PEAK_CONFIG, use_abs=False,
    )
    return qx, dvdq, samp


def extract_soc0_table(raw: pd.DataFrame, tagged: list[int], cell_id: str, arm: str) -> pd.DataFrame:
    rows = []
    for tidx, rcyc in enumerate(tagged, start=1):
        q, v = dchg_qv(raw, rcyc)
        inten = q_soc = float("nan")
        if q is not None:
            samp = dvdq_intensity_at_soc(
                q, v, soc_target=0.0, soc_window=0.02, discharge=True,
                config=DEFAULT_DQDV_PEAK_CONFIG, use_abs=False,
            )
            if samp.get("intensity") is not None:
                inten = float(samp["intensity"])
            if samp.get("Q") is not None:
                q_soc = float(samp["Q"])
        rows.append(
            dict(
                arm=arm,
                cell_id=cell_id,
                tagged_cycle=tidx,
                raw_cycle=rcyc,
                dchg_dVdQ_SOC0=inten,
                dchg_dVdQ_SOC0_Q=q_soc,
            )
        )
    df = pd.DataFrame(rows)
    bp1, bp2 = load_bps(cell_id, arm)
    df["BP1_tagged"] = bp1
    df["BP2_tagged"] = bp2
    y = pd.to_numeric(df["dchg_dVdQ_SOC0"], errors="coerce")
    y1 = float(y[np.isfinite(y)].iloc[0]) if np.isfinite(y).any() else float("nan")
    df["SOC0_inc_pct_vs_t1"] = (y / y1 - 1.0) * 100.0 if np.isfinite(y1) and y1 != 0 else np.nan
    return df


def plot_arm(
    frames: list[pd.DataFrame],
    raws: dict[str, tuple[pd.DataFrame, list[int], str]],
    out: Path,
    *,
    vq_step: int = 50,
) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(W_IN, H_IN), sharey="row")
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.06, top=0.90, hspace=0.30, wspace=0.16)

    y_lo, y_hi = np.inf, -np.inf

    for col, arm in enumerate(("set4_SJ900", "SJ1300_dry")):
        axp, axa, axi = axes[0, col], axes[1, col], axes[2, col]

        # middle/bottom: all cells
        for df in frames:
            if df["arm"].iloc[0] != arm:
                continue
            cell = df["cell_id"].iloc[0]
            c = CELL_COLOR.get(cell, "k")
            x = df["tagged_cycle"].to_numpy(float)
            y = pd.to_numeric(df["dchg_dVdQ_SOC0"], errors="coerce").to_numpy(float)
            m = np.isfinite(y)
            if not m.any():
                continue
            y1 = float(y[m][0])
            inc = (y / y1 - 1.0) * 100.0
            axa.plot(x, smooth(y, 11), color=c, lw=1.7, label=cell)
            axi.plot(x, smooth(inc, 11), color=c, lw=1.7, label=cell)
            for t, ls in ((df["BP1_tagged"].iloc[0], "--"), (df["BP2_tagged"].iloc[0], "-.")):
                if pd.notna(t):
                    axa.axvline(t, color="0.45", ls=ls, lw=0.9, alpha=0.5)
                    axi.axvline(t, color="0.45", ls=ls, lw=0.9, alpha=0.5)

        # top: representative cell — signed dVdQ + SOC0 marks
        v_cell = V_PROFILE_CELLS[arm]
        if v_cell in raws:
            raw, tagged, _ = raws[v_cell]
            tmax = len(tagged)
            t_list = sorted(set([1] + list(range(vq_step, tmax + 1, vq_step))))
            nseg = max(len(t_list) - 1, 1)
            for k, tidx in enumerate(t_list):
                q, v = dchg_qv(raw, tagged[tidx - 1])
                if q is None:
                    continue
                prof = dvdq_soc0_profile(q, v)
                if prof is None:
                    continue
                qx, ydq, samp = prof
                color = cm.viridis(k / nseg)
                axp.plot(qx, ydq, color=color, lw=1.5 if tidx != 1 else 2.1, label=f"t{tidx}")
                if samp.get("Q") is not None and samp.get("intensity") is not None:
                    axp.scatter(
                        [samp["Q"]],
                        [samp["intensity"]],
                        s=36,
                        color=color,
                        edgecolors="k",
                        linewidths=0.35,
                        zorder=5,
                    )
                y_lo = min(y_lo, float(np.nanpercentile(ydq, 2)))
                y_hi = max(y_hi, float(np.nanpercentile(ydq, 98)))
                if samp.get("intensity") is not None:
                    y_lo = min(y_lo, float(samp["intensity"]))
                    y_hi = max(y_hi, float(samp["intensity"]))
            # Compact legend: keep every other cycle label to avoid covering curves
            handles, labels = axp.get_legend_handles_labels()
            keep = [i for i, lab in enumerate(labels) if i % 2 == 0 or i == len(labels) - 1]
            axp.legend(
                [handles[i] for i in keep],
                [labels[i] for i in keep],
                loc="lower left",
                ncol=2,
                fontsize=6.5,
                framealpha=0.90,
                borderaxespad=0.4,
                labelspacing=0.18,
                columnspacing=0.7,
                handlelength=1.3,
            )
            axp.set_title(
                f"{arm} / {v_cell} — dV/dQ (dots = SOC0)",
                fontweight="bold",
            )
        axp.set_xlabel("Q [Ah]")
        axp.axhline(0, color="k", lw=0.6, alpha=0.35)
        style(axp)

        axa.axhline(0, color="k", lw=0.6, alpha=0.35)
        axa.set_title(f"{arm} — dVdQ @ SOC0", fontweight="bold")
        axa.legend(fontsize=8)
        style(axa)

        axi.axhline(0, color="k", lw=0.6, alpha=0.4)
        axi.set_title(f"{arm} — inc% vs t1", fontweight="bold")
        axi.set_xlabel("Tagged cycle #")
        axi.legend(fontsize=8)
        style(axi)

    if np.isfinite(y_lo) and np.isfinite(y_hi) and y_hi > y_lo:
        pad = 0.06 * (y_hi - y_lo)
        for ax in (axes[0, 0], axes[0, 1]):
            ax.set_ylim(y_lo - pad, y_hi + pad)

    # Force shared y limits for SOC0 trajectory and inc% rows (900 vs 1300)
    for row in (1, 2):
        lims = []
        for ax in (axes[row, 0], axes[row, 1]):
            lo, hi = ax.get_ylim()
            lims.append((lo, hi))
        lo = min(a[0] for a in lims)
        hi = max(a[1] for a in lims)
        for ax in (axes[row, 0], axes[row, 1]):
            ax.set_ylim(lo, hi)

    axes[0, 0].set_ylabel("dV/dQ [V/Ah]")
    axes[1, 0].set_ylabel("dVdQ_SOC0 [V/Ah]")
    axes[2, 0].set_ylabel("inc% vs t1")
    # Shared y-scale, but still show numeric tick labels on both columns
    for r in range(3):
        for c in range(2):
            axes[r, c].tick_params(axis="y", labelleft=True)
    fig.suptitle(
        "dVdQ@SOC0 — profile (900:Ch022 / 1300:Ch012) · SOC0 · inc% vs t1",
        fontweight="bold",
        fontsize=12.5,
    )
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def plot_cell_triple(
    cell_id: str,
    arm: str,
    raw: pd.DataFrame,
    tagged: list[int],
    df: pd.DataFrame,
    out: Path,
    *,
    vq_step: int = 50,
) -> None:
    """Optional per-cell 3-panel (same layout as R60 cell plots)."""
    x = df["tagged_cycle"].to_numpy(float)
    y = pd.to_numeric(df["dchg_dVdQ_SOC0"], errors="coerce").to_numpy(float)
    m = np.isfinite(y)
    if not m.any():
        return
    y1 = float(y[m][0])
    ys = smooth(y, 11)
    inc = (y / y1 - 1.0) * 100.0
    inc_s = smooth(inc, 11)
    bp1, bp2 = df["BP1_tagged"].iloc[0], df["BP2_tagged"].iloc[0]

    fig, axes = plt.subplots(3, 1, figsize=(W_IN, 8.0))
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.07, top=0.90, hspace=0.32)

    ax = axes[0]
    tmax = len(tagged)
    t_list = sorted(set([1] + list(range(vq_step, tmax + 1, vq_step))))
    nseg = max(len(t_list) - 1, 1)
    for k, tidx in enumerate(t_list):
        q, v = dchg_qv(raw, tagged[tidx - 1])
        if q is None:
            continue
        prof = dvdq_soc0_profile(q, v)
        if prof is None:
            continue
        qx, ydq, samp = prof
        color = cm.viridis(k / nseg)
        ax.plot(qx, ydq, color=color, lw=1.5, label=f"t{tidx}")
        if samp.get("Q") is not None and samp.get("intensity") is not None:
            ax.scatter([samp["Q"]], [samp["intensity"]], s=40, color=color, edgecolors="k", linewidths=0.35, zorder=5)
    ax.set_xlabel("Q [Ah]")
    ax.set_ylabel("dV/dQ [V/Ah]")
    ax.set_title("dV/dQ every 50 tagged (dots = SOC0)", fontweight="bold")
    ax.axhline(0, color="k", lw=0.6, alpha=0.35)
    ax.legend(loc="upper left", ncol=3, fontsize=7, framealpha=0.92)
    style(ax)

    ax = axes[1]
    ax.plot(x, y, color="#90caf9", lw=0.9, alpha=0.75, label="raw")
    ax.plot(x, ys, color="#1565c0", lw=2.0, label="smooth")
    ax.axhline(y1, color="0.4", ls=":", lw=1.0, label=f"SOC0(t1)={y1:.4f}")
    ax.axhline(0, color="k", lw=0.6, alpha=0.35)
    for t, lab, col, ls in ((bp1, "BP1", "#1565c0", "--"), (bp2, "BP2", "#6a1b9a", "-.")):
        if t is None or not np.isfinite(t):
            continue
        ax.axvline(t, color=col, ls=ls, lw=1.4)
        ax.text(t + 4, float(np.nanmax(ys)), lab, color=col, fontsize=9, fontweight="bold")
    ax.set_ylabel("dVdQ_SOC0 [V/Ah]")
    ax.set_xlabel("Tagged cycle #")
    ax.legend(fontsize=8)
    ax.set_title("Cycle dV/dQ @ SOC0", fontweight="bold")
    style(ax)

    ax = axes[2]
    ax.plot(x, inc, color="#ffab91", lw=0.9, alpha=0.75)
    ax.plot(x, inc_s, color="#d84315", lw=2.0, label="inc% vs t1")
    ax.axhline(0, color="k", lw=0.7, alpha=0.4)
    for t, col, ls in ((bp1, "#1565c0", "--"), (bp2, "#6a1b9a", "-.")):
        if t is not None and np.isfinite(t):
            ax.axvline(t, color=col, ls=ls, lw=1.3)
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("inc% vs t1")
    ax.legend(fontsize=8)
    ax.set_title("Growth vs tagged cycle 1", fontweight="bold")
    style(ax)

    fig.suptitle(f"{arm} / {cell_id} — dVdQ@SOC0", fontweight="bold", fontsize=13, y=0.98)
    fig.savefig(out / f"{cell_id}_dvdq_SOC0_triple.png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/dvdq_soc0_arm"),
    )
    p.add_argument("--vq-step", type=int, default=50)
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    frames: list[pd.DataFrame] = []
    raws: dict[str, tuple[pd.DataFrame, list[int], str]] = {}

    for cell_id, (path, arm) in DEFAULT_CELLS.items():
        if not path.exists():
            continue
        print(f"[{cell_id}] extract SOC0 …", flush=True)
        raw = load_raw(path)
        tagged = tagged_routine_cycles(raw)
        df = extract_soc0_table(raw, tagged, cell_id, arm)
        df.to_csv(out / f"{cell_id}_dvdq_SOC0.csv", index=False)
        frames.append(df)
        raws[cell_id] = (raw, tagged, arm)
        if cell_id in V_PROFILE_CELLS.values():
            plot_cell_triple(cell_id, arm, raw, tagged, df, out, vq_step=args.vq_step)

    if frames:
        plot_arm(frames, raws, out / "00_arm_dvdq_SOC0_inc_vs_t1.png", vq_step=args.vq_step)
        pd.concat(frames, ignore_index=True).to_csv(out / "all_dvdq_SOC0.csv", index=False)
        # quick summary
        for df in frames:
            y = pd.to_numeric(df["dchg_dVdQ_SOC0"], errors="coerce")
            print(
                f"  {df['cell_id'].iloc[0]}: t1={y.iloc[0]:.4f}  EOL={y.iloc[-1]:.4f}  "
                f"inc%={df['SOC0_inc_pct_vs_t1'].iloc[-1]:+.1f}"
            )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
