"""Zoom voltage profiles around early-life analysis start, every 50 tagged cycles.

Focus: tagged 1 → ~200 (R60 step / S1 start region), curves at t=1,50,100,150,200
plus 50-cycle chunk panels (1–50, 50–100, 100–150, 150–200).

Example::

    python -m cyclediag.tools.run_vq_early50_zoom \\
        --out example/output/crossover_vs_sohq/present_1600x1000/vq_early50
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

from cyclediag.features.dqdv_peaks import DEFAULT_DQDV_PEAK_CONFIG, compute_dqdv
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

W_IN, H_IN, DPI = 10.0, 6.25, 140

DEFAULT_CELLS = {
    "M01Ch022": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"),
    "M01Ch024": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"),
    "M01Ch025": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv"),
    "M01Ch010": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"),
    "M01Ch011": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"),
    "M01Ch012": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"),
}

ARM = {
    "M01Ch022": "set4_SJ900",
    "M01Ch024": "set4_SJ900",
    "M01Ch025": "set4_SJ900",
    "M01Ch010": "SJ1300_dry",
    "M01Ch011": "SJ1300_dry",
    "M01Ch012": "SJ1300_dry",
}


def style(ax) -> None:
    ax.grid(True, alpha=0.28)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)


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


def collect_profiles(raw: pd.DataFrame, tagged: list[int], t_list: list[int]) -> list[dict]:
    out = []
    for t in t_list:
        if t < 1 or t > len(tagged):
            continue
        q, v = dchg_qv(raw, tagged[t - 1])
        if q is None:
            continue
        vv, dq = compute_dqdv(v, q, DEFAULT_DQDV_PEAK_CONFIG)
        out.append(dict(t=t, c=tagged[t - 1], q=q, v=v, v_dq=vv, dqdv=dq))
    return out


def plot_overlay_and_chunks(
    cell_id: str,
    arm: str,
    profiles_by_t: dict[int, dict],
    *,
    anchors: list[int],
    chunks: list[tuple[int, int]],
    out: Path,
) -> None:
    """Top: overlay at 50-cyc anchors. Bottom: 4 chunk panels (start+end of each 50)."""
    fig = plt.figure(figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.07, right=0.99, bottom=0.08, top=0.88, hspace=0.38, wspace=0.22)
    gs = fig.add_gridspec(2, 4, height_ratios=[1.15, 1.0])

    # shared limits from all shown profiles
    shown = [profiles_by_t[t] for t in anchors if t in profiles_by_t]
    for a, b in chunks:
        for t in (a, b):
            if t in profiles_by_t:
                shown.append(profiles_by_t[t])
    if not shown:
        plt.close(fig)
        return

    qmax = max(float(np.nanmax(p["q"])) for p in shown)
    # zoom: high-V / early discharge where R60 step often shows IR + shape
    # full Q on top; chunk panels also full Q but tighter V zoom around start of discharge
    vmin = min(float(np.nanmin(p["v"])) for p in shown)
    vmax = max(float(np.nanmax(p["v"])) for p in shown)
    # start-of-discharge zoom band (first ~15 Ah + high V)
    v_hi = vmax
    v_lo_zoom = max(vmin, vmax - 0.55)  # top ~0.55 V of discharge

    ax0 = fig.add_subplot(gs[0, :2])
    ax1 = fig.add_subplot(gs[0, 2:])
    nseg = max(len(anchors) - 1, 1)
    for k, t in enumerate(anchors):
        p = profiles_by_t.get(t)
        if p is None:
            continue
        color = cm.viridis(k / nseg)
        lw = 2.3 if t == 50 else 1.5
        lab = f"t{t}" + (" *start~50" if t == 50 else "")
        ax0.plot(p["q"], p["v"], color=color, lw=lw, label=lab)
        ax1.plot(p["v_dq"], p["dqdv"], color=color, lw=lw, label=lab)
    ax0.set_xlim(-0.3, qmax * 1.02)
    ax0.set_ylim(vmin - 0.03, vmax + 0.03)
    ax0.set_xlabel("Q [Ah]")
    ax0.set_ylabel("V")
    ax0.set_title("V–Q every 50 tagged cyc (early window)", fontweight="bold")
    ax0.legend(loc="lower left", fontsize=8, ncol=2, framealpha=0.92)
    style(ax0)

    # dQ/dV limits
    dq_stack = np.concatenate([p["dqdv"][np.isfinite(p["dqdv"])] for p in shown])
    dq_lo, dq_hi = np.nanpercentile(dq_stack, [2, 98])
    span = max(dq_hi - dq_lo, 1e-6)
    ax1.set_xlim(vmin - 0.03, vmax + 0.03)
    ax1.set_ylim(dq_lo - 0.08 * span, dq_hi + 0.08 * span)
    ax1.set_xlabel("V")
    ax1.set_ylabel("dQ/dV [Ah/V]")
    ax1.set_title("dQ/dV every 50 tagged cyc", fontweight="bold")
    ax1.legend(loc="upper right", fontsize=8, ncol=2, framealpha=0.92)
    style(ax1)

    # chunk panels: zoom high-V start of discharge
    for i, (a, b) in enumerate(chunks):
        ax = fig.add_subplot(gs[1, i])
        pa, pb = profiles_by_t.get(a), profiles_by_t.get(b)
        if pa is not None:
            ax.plot(pa["q"], pa["v"], color="#1565c0", lw=2.0, label=f"t{a}")
        if pb is not None:
            ax.plot(pb["q"], pb["v"], color="#c62828", lw=2.0, label=f"t{b}")
        ax.set_xlim(-0.2, min(18.0, qmax * 0.55))  # expand start-of-dchg
        ax.set_ylim(v_lo_zoom, v_hi + 0.02)
        ax.set_title(f"chunk t{a}–t{b} (start-V zoom)", fontsize=9, fontweight="bold")
        ax.set_xlabel("Q [Ah]", fontsize=8)
        if i == 0:
            ax.set_ylabel("V", fontsize=8)
        ax.legend(fontsize=7, loc="lower left")
        style(ax)

    fig.suptitle(
        f"{arm} / {cell_id} — early analysis window, 50-cycle cuts (R60 step ~t50)",
        fontsize=12.5,
        fontweight="bold",
        y=0.97,
    )
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def plot_arm_compare_at_t(
    cell_profiles: dict[str, dict[int, dict]],
    t: int,
    out: Path,
) -> None:
    """Single tagged-cycle V-Q overlay: all cells at the same tagged t."""
    fig, axes = plt.subplots(1, 2, figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.12, top=0.88, wspace=0.2)
    for ax, arm in zip(axes, ("set4_SJ900", "SJ1300_dry")):
        for cell, by_t in cell_profiles.items():
            if ARM[cell] != arm:
                continue
            p = by_t.get(t)
            if p is None:
                continue
            ax.plot(p["q"], p["v"], lw=1.8, label=cell)
        ax.set_title(f"{arm} @ tagged t={t}", fontweight="bold")
        ax.set_xlabel("Q [Ah]")
        ax.set_ylabel("V")
        ax.legend(fontsize=8)
        style(ax)
    fig.suptitle(f"Discharge V–Q at analysis anchors (t={t})", fontweight="bold")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/vq_early50"),
    )
    p.add_argument("--step", type=int, default=50)
    p.add_argument("--tmax", type=int, default=200)
    p.add_argument("--cells", type=str, default="")
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    anchors = list(range(1, args.tmax + 1, args.step))
    if anchors[0] != 1:
        anchors = [1] + anchors
    # ensure t=50 present when step=50
    if 50 not in anchors and args.tmax >= 50:
        anchors = sorted(set(anchors + [50]))
    chunks = [(a, a + args.step) for a in range(1, args.tmax, args.step)]
    # (1,50), (50,100), ...
    chunks = []
    edges = list(range(1, args.tmax + 1, args.step))
    if edges[-1] != args.tmax and args.tmax in anchors:
        pass
    for i in range(len(edges) - 1):
        chunks.append((edges[i], edges[i + 1]))
    # if started at 1 with step 50: (1,51) bad — use (1,50),(50,100)...
    chunks = []
    seq = [1] + list(range(args.step, args.tmax + 1, args.step))
    seq = sorted(set(seq))
    anchors = seq
    for i in range(len(seq) - 1):
        chunks.append((seq[i], seq[i + 1]))

    want = {c.strip() for c in args.cells.split(",") if c.strip()} or set(DEFAULT_CELLS)
    cell_profiles: dict[str, dict[int, dict]] = {}
    metric_rows = []

    for cell_id, path in DEFAULT_CELLS.items():
        if cell_id not in want or not path.exists():
            continue
        print(f"[{cell_id}] load …", flush=True)
        raw = load_raw(path)
        tagged = tagged_routine_cycles(raw)
        need = sorted(set(anchors + [t for ab in chunks for t in ab]))
        need = [t for t in need if t <= len(tagged)]
        profs = collect_profiles(raw, tagged, need)
        by_t = {p["t"]: p for p in profs}
        cell_profiles[cell_id] = by_t
        plot_overlay_and_chunks(
            cell_id,
            ARM[cell_id],
            by_t,
            anchors=anchors,
            chunks=chunks[:4],
            out=out / f"{cell_id}_VQ_early50.png",
        )
        for t, p in by_t.items():
            qmax = float(np.nanmax(p["q"]))

            def v_at(qa, q=p["q"], v=p["v"], qmax=qmax):
                if qmax < qa:
                    return float("nan")
                return float(np.interp(qa, q, v))

            metric_rows.append(
                dict(
                    arm=ARM[cell_id],
                    cell_id=cell_id,
                    tagged=t,
                    raw_cycle=p["c"],
                    Qmax=qmax,
                    V_start=float(p["v"][0]),
                    V_at_Q1=v_at(1),
                    V_at_Q5=v_at(5),
                    V_at_Q10=v_at(10),
                    dV_0_to_5Ah=v_at(0.1) - v_at(5) if np.isfinite(v_at(5)) else np.nan,
                )
            )
        print(f"  n_tagged={len(tagged)} anchors={anchors}")

    mdf = pd.DataFrame(metric_rows)
    mdf.to_csv(out / "early50_VQ_metrics.csv", index=False)

    for t in (1, 50, 100, 150, 200):
        if any(t in cp for cp in cell_profiles.values()):
            plot_arm_compare_at_t(cell_profiles, t, out / f"00_arm_compare_t{t:03d}.png")

    # delta V-Q: t50 - t1 and t100 - t50 (shape change around analysis start)
    fig, axes = plt.subplots(1, 2, figsize=(W_IN, H_IN), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.12, top=0.86, wspace=0.15)
    for ax, (t0, t1), title in zip(
        axes,
        ((1, 50), (50, 100)),
        ("ΔV = V(t50)−V(t1) @ Q", "ΔV = V(t100)−V(t50) @ Q"),
    ):
        q_grid = np.linspace(0.5, 40, 200)
        for cell, by_t in cell_profiles.items():
            if t0 not in by_t or t1 not in by_t:
                continue
            p0, p1 = by_t[t0], by_t[t1]
            qmax = min(float(np.nanmax(p0["q"])), float(np.nanmax(p1["q"])))
            g = q_grid[q_grid <= qmax]
            v0 = np.interp(g, p0["q"], p0["v"])
            v1 = np.interp(g, p1["q"], p1["v"])
            ls = "-" if ARM[cell] == "set4_SJ900" else "--"
            ax.plot(g, v1 - v0, lw=1.6, ls=ls, label=f"{ARM[cell]}/{cell}")
        ax.axhline(0, color="k", lw=0.7, alpha=0.4)
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Q [Ah]")
        ax.legend(fontsize=6.5, ncol=1)
        style(ax)
    axes[0].set_ylabel("ΔV [V]")
    fig.suptitle(
        "Early window voltage shift (solid=SJ900, dashed=SJ1300)",
        fontweight="bold",
    )
    fig.savefig(out / "00_deltaV_t1_t50_t100.png", dpi=DPI)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
