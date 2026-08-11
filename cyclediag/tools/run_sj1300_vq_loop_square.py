"""Charge+discharge V–Q on the SAME square panel, every 50 tagged cycles.

Each panel overlays charge (solid) and discharge (dashed) for t=1,50,100,…
Legend inside axes at lower-left.

Example::

    python -m cyclediag.tools.run_sj1300_vq_loop_square --arm SJ1300
    python -m cyclediag.tools.run_sj1300_vq_loop_square --arm SJ900
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

DPI = 140
PANEL_IN = 5.5
ARMS = {
    "SJ1300": {
        "label": "SJ1300_dry",
        "cells": {
            "M01Ch010": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"),
            "M01Ch011": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"),
            "M01Ch012": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"),
        },
        "default_out": Path("example/output/crossover_vs_sohq/present_1600x1000/sj1300_vq_loop_square"),
    },
    "SJ900": {
        "label": "set4_SJ900",
        # Ch025 excluded (short life / prior request)
        "cells": {
            "M01Ch022": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"),
            "M01Ch024": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"),
        },
        "default_out": Path("example/output/crossover_vs_sohq/present_1600x1000/sj900_vq_loop_square"),
    },
}


def style(ax) -> None:
    ax.grid(True, alpha=0.28)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)


def load_raw(path: Path):
    df = pd.read_csv(path, encoding="cp949", on_bad_lines="skip")
    return normalize_cycler_dataframe(df, ColumnMap.studio_default())


def tagged_routine_cycles(raw) -> list[int]:
    se = raw.groupby(["cycle", "StepNo"], as_index=False).tail(1)
    prot = build_protocol_exclusion(se)
    flags = detect_protocol_flags(se)
    routine = flags[
        (flags["protocol_kind"] == "routine") & (~flags["cycle"].isin(prot.excluded))
    ].sort_values("cycle")
    return [int(c) for c in routine["cycle"]]


def leg_qv(raw, cycle: int, leg: str):
    g = raw[raw["cycle"] == cycle]
    d = leg_segment(g, leg, charge_text="charge", discharge_text="discharge")
    if d.empty or "voltage" not in d.columns:
        return None, None
    v = pd.to_numeric(d["voltage"], errors="coerce").to_numpy(float)
    prefer = "charge_capacity" if leg == "charge" else "discharge_capacity"
    q = None
    for col in (prefer, "capacity"):
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


def collect(raw, tagged: list[int], step: int):
    tmax = len(tagged)
    t_list = sorted(set([1] + list(range(step, tmax + 1, step))))
    rows = []
    for tidx in t_list:
        rcyc = tagged[tidx - 1]
        qc, vc = leg_qv(raw, rcyc, "charge")
        qd, vd = leg_qv(raw, rcyc, "discharge")
        rows.append(dict(t=tidx, qc=qc, vc=vc, qd=qd, vd=vd))
    return rows


def axis_limits(rows) -> tuple[tuple[float, float], tuple[float, float]]:
    qs, vs = [], []
    for r in rows:
        for q, v in ((r["qc"], r["vc"]), (r["qd"], r["vd"])):
            if q is None:
                continue
            qs.append(float(np.nanmax(q)))
            vs.append(float(np.nanmin(v)))
            vs.append(float(np.nanmax(v)))
    qmax = max(qs) if qs else 70.0
    return (-0.5, qmax * 1.02), (min(vs) - 0.05, max(vs) + 0.05)


def plot_loop_on_ax(ax, rows, *, title: str, qlim, vlim, step: int, square: bool = True) -> None:
    nseg = max(len(rows) - 1, 1)
    for k, r in enumerate(rows):
        color = cm.viridis(k / nseg)
        if r["qc"] is not None:
            ax.plot(r["qc"], r["vc"], color=color, lw=1.55, ls="-", solid_capstyle="round")
        if r["qd"] is not None:
            ax.plot(r["qd"], r["vd"], color=color, lw=1.55, ls="--", solid_capstyle="round")
    ax.set_xlim(*qlim)
    ax.set_ylim(*vlim)
    ax.set_xlabel("Q [Ah]")
    ax.set_ylabel("V")
    ax.set_title(title, fontweight="bold", pad=8)
    if square:
        ax.set_box_aspect(1)
    style(ax)
    handles = [
        Line2D([0], [0], color=cm.viridis(k / nseg), lw=2.0, label=f"t{r['t']}")
        for k, r in enumerate(rows)
    ]
    # Inside axes, lower-left; 2-column compact to reduce overlap with dchg end
    ax.legend(
        handles=handles,
        loc="lower left",
        ncol=2,
        fontsize=6.5,
        framealpha=0.90,
        title=f"every {step}  (— chg, -- dchg)",
        borderaxespad=0.5,
        labelspacing=0.2,
        columnspacing=0.8,
        handlelength=1.4,
    )


BP_DIRS = {
    "set4_SJ900": Path("example/output/set4/inflection_tagged"),
    "SJ1300_dry": Path("example/output/SJ1300_dry/inflection_tagged"),
}


def load_bps(cell_id: str, arm_label: str):
    path = BP_DIRS.get(arm_label, Path()) / f"{cell_id}_breakpoints.csv"
    if not path.exists():
        return None, None
    bp = pd.read_csv(path)
    t = pd.to_numeric(bp.get("tagged_cycle"), errors="coerce").dropna().to_numpy(float)
    if len(t) == 0:
        return None, None
    return float(t[0]), (float(t[1]) if len(t) > 1 else None)


def sohq_table(raw, tagged: list[int]) -> pd.DataFrame:
    """SoHQ from discharge Qmax, BOL = median of first 5 tagged cycles."""
    qmaxes = []
    for rcyc in tagged:
        q, _ = leg_qv(raw, rcyc, "discharge")
        qmaxes.append(float(np.nanmax(q)) if q is not None else float("nan"))
    q = np.asarray(qmaxes, dtype=float)
    bol = float(np.nanmedian(q[:5])) if np.isfinite(q[:5]).any() else float("nan")
    sohq = 100.0 * q / bol if bol and np.isfinite(bol) and bol > 0 else np.full_like(q, np.nan)
    return pd.DataFrame(
        {
            "tagged_cycle": np.arange(1, len(tagged) + 1),
            "raw_cycle": tagged,
            "dchgCapa": q,
            "SoHQ": sohq,
        }
    )


def plot_sohq_on_ax(
    ax, sohq: pd.DataFrame, *, bp1=None, bp2=None, title: str = "SoHQ", square: bool = True
) -> None:
    x = sohq["tagged_cycle"].to_numpy(float)
    y = pd.to_numeric(sohq["SoHQ"], errors="coerce").to_numpy(float)
    ax.plot(x, y, color="#90caf9", lw=0.9, alpha=0.75, label="SoHQ raw")
    # light smooth
    if len(y) >= 11:
        k = np.ones(11) / 11
        ys = np.convolve(np.pad(y, (5, 5), mode="edge"), k, mode="valid")[: len(y)]
        ax.plot(x, ys, color="#1565c0", lw=2.0, label="SoHQ smooth")
    for t, lab, col, ls in ((bp1, "BP1", "#1565c0", "--"), (bp2, "BP2", "#6a1b9a", "-.")):
        if t is None or not np.isfinite(t):
            continue
        ax.axvline(t, color=col, ls=ls, lw=1.5)
        j = int(np.argmin(np.abs(x - t)))
        ax.scatter([t], [y[j]], color=col, s=40, zorder=5, edgecolors="k", linewidths=0.4)
        ax.text(t + 4, y[j] + 0.8, lab, color=col, fontsize=9, fontweight="bold")
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("SoHQ [%]")
    ax.set_title(title, fontweight="bold", pad=8)
    if square:
        ax.set_box_aspect(1)
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    style(ax)


def plot_cell(cell_id: str, arm_label: str, rows, out: Path, step: int, *, raw=None, tagged=None) -> None:
    """1×2: charge+discharge V–Q loop | SoHQ. Figure aspect 3:1 (e.g. 1500×500)."""
    qlim, vlim = axis_limits(rows)
    bp1 = bp2 = None
    sohq = None
    if raw is not None and tagged is not None:
        sohq = sohq_table(raw, tagged)
        bp1, bp2 = load_bps(cell_id, arm_label)

    # 1500×500 px @ 100 dpi → figsize (15, 5); panel width ratio ~1:1 within that
    fig_w, fig_h = 15.0, 5.0
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_h))
    fig.subplots_adjust(left=0.05, right=0.98, bottom=0.14, top=0.84, wspace=0.18)
    # don't force square box aspect — stretch to fill 3:1 canvas
    plot_loop_on_ax(
        axes[0],
        rows,
        title=f"{arm_label} / {cell_id}  (— charge, -- discharge)",
        qlim=qlim,
        vlim=vlim,
        step=step,
        square=False,
    )
    if sohq is not None:
        plot_sohq_on_ax(
            axes[1],
            sohq,
            bp1=bp1,
            bp2=bp2,
            title=f"{arm_label} / {cell_id} — SoHQ",
            square=False,
        )
    else:
        axes[1].set_axis_off()
        axes[1].text(0.5, 0.5, "SoHQ unavailable", ha="center", va="center")

    fig.suptitle(
        f"{arm_label} / {cell_id} — V–Q loop every {step}  |  SoHQ",
        fontweight="bold",
        fontsize=13,
    )
    # exact 1500×500
    fig.savefig(out / f"{cell_id}_chg_dchg_loop_every{step}_square.png", dpi=100)
    fig.savefig(out / f"{cell_id}_chg_dchg_loop_every{step}_SoHQ_1x2.png", dpi=100)
    plt.close(fig)


def plot_overview(all_rows: dict[str, list], out: Path, step: int, *, arm_key: str, arm_label: str) -> None:
    cells = [c for c in all_rows]
    if not cells:
        return
    stack = []
    for c in cells:
        stack.extend(all_rows[c])
    qlim, vlim = axis_limits(stack)

    n = len(cells)
    fig, axes = plt.subplots(1, n, figsize=(n * PANEL_IN, PANEL_IN + 0.3))
    if n == 1:
        axes = [axes]
    fig.subplots_adjust(left=0.05, right=0.99, bottom=0.12, top=0.82, wspace=0.22)
    for ax, cell in zip(axes, cells):
        plot_loop_on_ax(
            ax,
            all_rows[cell],
            title=f"{cell}  (— chg, -- dchg)",
            qlim=qlim,
            vlim=vlim,
            step=step,
        )
    fig.suptitle(
        f"{arm_label} — charge+discharge V–Q (every {step} tagged)",
        fontweight="bold",
        fontsize=14,
    )
    fig.savefig(out / f"00_{arm_key}_chg_dchg_loop_every{step}_1x{n}_square.png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", choices=("SJ900", "SJ1300", "both"), default="both")
    p.add_argument("--out", type=Path, default=None, help="Override output dir (single arm only)")
    p.add_argument("--step", type=int, default=50)
    args = p.parse_args()

    arms = list(ARMS) if args.arm == "both" else [args.arm]
    for arm_key in arms:
        cfg = ARMS[arm_key]
        out = args.out if (args.out is not None and args.arm != "both") else cfg["default_out"]
        out.mkdir(parents=True, exist_ok=True)
        arm_label = cfg["label"]
        all_rows: dict[str, list] = {}
        for cell_id, path in cfg["cells"].items():
            if not path.exists():
                print(f"skip missing {path}")
                continue
            print(f"[{arm_key}/{cell_id}] …", flush=True)
            raw = load_raw(path)
            tagged = tagged_routine_cycles(raw)
            rows = collect(raw, tagged, args.step)
            all_rows[cell_id] = rows
            plot_cell(cell_id, arm_label, rows, out, args.step, raw=raw, tagged=tagged)
            print(f"  n_cycles={len(rows)}")
        plot_overview(all_rows, out, args.step, arm_key=arm_key, arm_label=arm_label)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
