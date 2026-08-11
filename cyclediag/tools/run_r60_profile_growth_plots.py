"""EoC_dchgR_60s plots with figure definition (V_ref before load).

Panels per cell:
  1) Voltage (±5 min around discharge start) for selected tagged cycles
  2) R60 vs tagged cycle
  3) Resistance growth vs baseline tagged cycle 1:
       inc% = (R_n - R_1) / R_1 * 100
       and local d(inc%)/100cyc

Example::

    python -m cyclediag.tools.run_r60_profile_growth_plots \\
        --out example/output/crossover_vs_sohq/present_1600x1000/r60_vwin_growth
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

from cyclediag.features.cc_cv import resolve_current_column
from cyclediag.features.lges_extract import _resistance_mohm, _sample_v_i_at_offsets
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

W_IN, H_IN, DPI = 10.0, 8.0, 140
CELL_COLOR = {
    "M01Ch022": "#1565c0",
    "M01Ch024": "#2e7d32",
    "M01Ch025": "#00838f",
    "M01Ch010": "#c62828",
    "M01Ch011": "#ef6c00",
    "M01Ch012": "#6a1b9a",
}
DEFAULT_CELLS = {
    "M01Ch022": (Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"), "set4_SJ900"),
    "M01Ch024": (Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"), "set4_SJ900"),
    "M01Ch025": (Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv"), "set4_SJ900"),
    "M01Ch010": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"), "SJ1300_dry"),
    "M01Ch011": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"), "SJ1300_dry"),
    "M01Ch012": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"), "SJ1300_dry"),
}
BP_DIRS = {
    "set4_SJ900": Path("example/output/set4/inflection_tagged"),
    "SJ1300_dry": Path("example/output/SJ1300_dry/inflection_tagged"),
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
    return np.convolve(np.pad(y, (pad, pad), mode="edge"), k, mode="valid")[: len(y)]


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


def load_bps(cell_id: str, arm: str):
    path = BP_DIRS[arm] / f"{cell_id}_breakpoints.csv"
    if not path.exists():
        return None, None
    bp = pd.read_csv(path)
    t = pd.to_numeric(bp.get("tagged_cycle"), errors="coerce").dropna().to_numpy(float)
    if len(t) == 0:
        return None, None
    return float(t[0]), (float(t[1]) if len(t) > 1 else None)


def eoc_r60_figure_def(cycle_df: pd.DataFrame) -> float:
    dchg = leg_segment(cycle_df, "discharge", charge_text="charge", discharge_text="discharge")
    if dchg.empty:
        return float("nan")
    s = _sample_v_i_at_offsets(dchg, (0.0, 60.0))
    r = _resistance_mohm(s[0.0][0], s[60.0][0], s[60.0][1])
    return float(r) if r is not None else float("nan")


def discharge_window_vi(
    cycle_df: pd.DataFrame,
    *,
    pad_s: float = 300.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float] | None:
    """Return t_rel(s from discharge start), V, I, V_ref, V_60, R60."""
    i_col = resolve_current_column(cycle_df) or "current"
    t = pd.to_numeric(cycle_df["time"], errors="coerce").to_numpy(float)
    v = pd.to_numeric(cycle_df["voltage"], errors="coerce").to_numpy(float)
    i = pd.to_numeric(cycle_df[i_col], errors="coerce").to_numpy(float)
    m = np.isfinite(t) & np.isfinite(v) & np.isfinite(i)
    t, v, i = t[m], v[m], i[m]
    if len(t) < 20:
        return None
    load = np.flatnonzero(i < -1.0)
    if len(load) == 0:
        return None
    j_load = int(load[0])
    j_ref = j_load - 1
    while j_ref > 0 and abs(float(i[j_ref])) > 0.5:
        j_ref -= 1
    t0 = float(t[j_load])
    v_ref = float(v[j_ref])
    v_60 = float(np.interp(t0 + 60.0, t, v))
    i_60 = float(np.interp(t0 + 60.0, t, i))
    r60 = abs(v_ref - v_60) / abs(i_60) * 1000.0 if abs(i_60) > 1e-9 else float("nan")

    sel = (t >= t0 - pad_s) & (t <= t0 + pad_s)
    if sel.sum() < 10:
        return None
    t_rel = t[sel] - t0
    return t_rel, v[sel], i[sel], v_ref, v_60, r60


def extract_r60_table(raw: pd.DataFrame, tagged: list[int], cell_id: str, arm: str) -> pd.DataFrame:
    csv = R60_SRC / f"{cell_id}_r60_ec2.csv"
    use_cache = False
    if csv.exists():
        df = pd.read_csv(csv)
        y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce")
        # figure-def scale is ~few mΩ; old prep scale was ~0.6–1 mΩ
        if float(np.nanmedian(y.to_numpy(float))) >= 1.5:
            use_cache = True
            bp1, bp2 = load_bps(cell_id, arm)
            df["BP1_tagged"] = bp1
            df["BP2_tagged"] = bp2
            r1 = float(y.iloc[0])
            df["R60_inc_pct_vs_t1"] = (y / r1 - 1.0) * 100.0
            return df
    rows = []
    for tidx, rcyc in enumerate(tagged, start=1):
        g = raw[raw["cycle"] == rcyc]
        r = eoc_r60_figure_def(g)
        rows.append(
            dict(
                arm=arm,
                cell_id=cell_id,
                tagged_cycle=tidx,
                raw_cycle=rcyc,
                EoC_dchgR_60s=r,
            )
        )
    df = pd.DataFrame(rows)
    bp1, bp2 = load_bps(cell_id, arm)
    df["BP1_tagged"] = bp1
    df["BP2_tagged"] = bp2
    r1 = float(pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce").iloc[0])
    df["R60_inc_pct_vs_t1"] = (
        pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce") / r1 - 1.0
    ) * 100.0
    _ = use_cache
    return df


def plot_cell(
    cell_id: str,
    arm: str,
    raw: pd.DataFrame,
    tagged: list[int],
    r60: pd.DataFrame,
    *,
    pad_s: float,
    vq_step: int,
    out: Path,
) -> None:
    x = r60["tagged_cycle"].to_numpy(float)
    y = pd.to_numeric(r60["EoC_dchgR_60s"], errors="coerce").to_numpy(float)
    ys = smooth(y, 11)
    r1 = float(y[np.isfinite(y)][0])
    inc = (y / r1 - 1.0) * 100.0
    inc_s = smooth(inc, 11)
    d_inc = local_slope_per_100(x, inc_s, half=15)
    bp1, bp2 = r60["BP1_tagged"].iloc[0], r60["BP2_tagged"].iloc[0]

    tmax = int(x.max())
    t_list = sorted(set([1] + list(range(vq_step, tmax + 1, vq_step))))
    # keep legend readable
    if len(t_list) > 12:
        t_list = sorted(set([1, vq_step] + list(range(2 * vq_step, tmax + 1, 2 * vq_step)) + [tmax]))

    fig, axes = plt.subplots(3, 1, figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.07, top=0.90, hspace=0.32)

    # --- 1) voltage ±5 min ---
    ax = axes[0]
    nseg = max(len(t_list) - 1, 1)
    for k, tidx in enumerate(t_list):
        if tidx < 1 or tidx > len(tagged):
            continue
        win = discharge_window_vi(raw[raw["cycle"] == tagged[tidx - 1]], pad_s=pad_s)
        if win is None:
            continue
        t_rel, vv, _ii, v_ref, v_60, _r = win
        color = cm.viridis(k / nseg)
        ax.plot(t_rel / 60.0, vv, color=color, lw=1.5, label=f"t{tidx}")
        if tidx == 1:
            ax.scatter([0.0], [v_ref], s=45, color="#6a1b9a", zorder=5, edgecolors="k", linewidths=0.4)
            ax.scatter([1.0], [v_60], s=45, color="#c62828", marker="D", zorder=5, edgecolors="k", linewidths=0.4)
    ax.axvline(0.0, color="0.25", ls="--", lw=1.2)
    ax.axvline(1.0, color="#c62828", ls=":", lw=1.1, alpha=0.8)
    ax.set_xlim(-pad_s / 60.0, pad_s / 60.0)
    ax.set_xlabel("Time from discharge start [min]")
    ax.set_ylabel("Voltage [V]")
    ax.set_title(
        f"Voltage ±{pad_s/60:.0f} min around discharge start "
        r"($V_{ref}$@0, $V_{60s}$@+1 min)",
        fontweight="bold",
    )
    ax.legend(loc="lower left", ncol=4, fontsize=7, framealpha=0.92)
    style(ax)

    # --- 2) R60 trend ---
    ax = axes[1]
    ax.plot(x, y, color="#90caf9", lw=0.9, alpha=0.75, label="R60 raw")
    ax.plot(x, ys, color="#1565c0", lw=2.0, label="R60 smooth")
    ax.axhline(r1, color="0.4", ls=":", lw=1.0, label=f"R60(t1)={r1:.3f} mΩ")
    for t, lab, col, ls in ((bp1, "BP1", "#1565c0", "--"), (bp2, "BP2", "#6a1b9a", "-.")):
        if t is None or not np.isfinite(t):
            continue
        ax.axvline(t, color=col, ls=ls, lw=1.4)
        j = int(np.argmin(np.abs(x - t)))
        ax.scatter([t], [ys[j]], color=col, s=40, zorder=5, edgecolors="k", linewidths=0.4)
        ax.text(t + 4, ys[j], lab, color=col, fontsize=9, fontweight="bold")
    ax.set_ylabel(r"EoC_dchgR$_{60s}$ [mΩ]")
    ax.set_xlabel("Tagged cycle #")
    ax.legend(loc="best", fontsize=8)
    ax.set_title("Cycle resistance (figure def: ΔV/|ΔI| from V_ref)", fontweight="bold")
    style(ax)

    # --- 3) growth vs t1 ---
    ax = axes[2]
    ax.plot(x, inc, color="#ffab91", lw=0.9, alpha=0.75, label=r"inc% = (R−R$_1$)/R$_1$")
    ax.plot(x, inc_s, color="#d84315", lw=2.0, label="inc% smooth")
    ax2 = ax.twinx()
    ax2.plot(x, d_inc, color="#6a1b9a", lw=1.4, alpha=0.85, label="d(inc%)/100cyc")
    ax.axhline(0, color="k", lw=0.7, alpha=0.4)
    for t, col, ls in ((bp1, "#1565c0", "--"), (bp2, "#6a1b9a", "-.")):
        if t is None or not np.isfinite(t):
            continue
        ax.axvline(t, color=col, ls=ls, lw=1.3)
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("Resistance increase vs t1 [%]")
    ax2.set_ylabel("d(inc%) / 100 cyc", color="#6a1b9a")
    ax.set_title("Resistance growth rate (baseline = tagged cycle 1)", fontweight="bold")
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [ln.get_label() for ln in lines], loc="best", fontsize=8)
    style(ax)
    style(ax2)

    fig.suptitle(
        f"{arm} / {cell_id} — V window · R60 · growth vs t1",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    fig.savefig(out / f"{cell_id}_Vwin_R60_growth.png", dpi=DPI)
    plt.close(fig)


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


def plot_arm_r_and_inc(
    frames: list[pd.DataFrame],
    raws: dict[str, tuple[pd.DataFrame, list[int], str]],
    out: Path,
    *,
    pad_s: float = 300.0,
    vq_step: int = 50,
    v_profile_cells: dict[str, str] | None = None,
) -> None:
    """3×2: V±pad_s | V ; R60 | R60 ; inc% | inc%  (SJ900 left, SJ1300 right).

    Voltage row uses only ``v_profile_cells`` (default: SJ900→Ch022, SJ1300→Ch012)
    with a shared y-axis. R60 / inc% rows keep all cells in ``frames``.
    """
    v_profile_cells = v_profile_cells or {
        "set4_SJ900": "M01Ch022",
        "SJ1300_dry": "M01Ch012",
    }
    fig, axes = plt.subplots(3, 2, figsize=(W_IN, H_IN * 1.15))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.06, top=0.90, hspace=0.28, wspace=0.16)
    axes[0, 1].sharey(axes[0, 0])

    v_ymin, v_ymax = np.inf, -np.inf

    for col, arm in enumerate(("set4_SJ900", "SJ1300_dry")):
        axv, axr, axi = axes[0, col], axes[1, col], axes[2, col]
        arm_frames = [df for df in frames if df["arm"].iloc[0] == arm]
        for df in arm_frames:
            cell = df["cell_id"].iloc[0]
            c = CELL_COLOR.get(cell, "k")
            x = df["tagged_cycle"].to_numpy(float)
            y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce").to_numpy(float)
            r1 = float(y[np.isfinite(y)][0])
            inc = (y / r1 - 1.0) * 100.0
            axr.plot(x, smooth(y, 11), color=c, lw=1.7, label=cell)
            axi.plot(x, smooth(inc, 11), color=c, lw=1.7, label=cell)
            for t, ls in ((df["BP1_tagged"].iloc[0], "--"), (df["BP2_tagged"].iloc[0], "-.")):
                if pd.notna(t):
                    axr.axvline(t, color="0.45", ls=ls, lw=0.9, alpha=0.5)
                    axi.axvline(t, color="0.45", ls=ls, lw=0.9, alpha=0.5)

        # voltage: one representative cell per arm
        v_cell = v_profile_cells.get(arm)
        if v_cell and v_cell in raws:
            raw, tagged, _ = raws[v_cell]
            c = CELL_COLOR.get(v_cell, "k")
            tmax = len(tagged)
            t_list = sorted(set([1] + list(range(vq_step, tmax + 1, vq_step))))
            nseg = max(len(t_list) - 1, 1)
            for k, tidx in enumerate(t_list):
                win = discharge_window_vi(raw[raw["cycle"] == tagged[tidx - 1]], pad_s=pad_s)
                if win is None:
                    continue
                t_rel, vv, *_rest = win
                color = cm.viridis(k / nseg)
                lw = 2.2 if tidx == 1 else 1.3
                axv.plot(t_rel / 60.0, vv, color=color, lw=lw, label=f"t{tidx}")
                v_ymin = min(v_ymin, float(np.nanmin(vv)))
                v_ymax = max(v_ymax, float(np.nanmax(vv)))
            axv.legend(loc="lower left", ncol=3, fontsize=7, framealpha=0.92)
            axv.set_title(
                f"{arm} / {v_cell} — V ±{pad_s:.0f}s (every {vq_step})",
                fontweight="bold",
            )
        else:
            axv.set_title(f"{arm} — V (missing cell)", fontweight="bold")

        axv.axvline(0.0, color="0.25", ls="--", lw=1.1)
        axv.axvline(1.0, color="#c62828", ls=":", lw=1.0, alpha=0.8)
        axv.set_xlim(-pad_s / 60.0, pad_s / 60.0)
        style(axv)

        axr.set_title(f"{arm} — R60", fontweight="bold")
        axr.legend(fontsize=8)
        style(axr)

        axi.axhline(0, color="k", lw=0.6, alpha=0.4)
        axi.set_title(f"{arm} — inc% vs t1", fontweight="bold")
        axi.set_xlabel("Tagged cycle #")
        axi.legend(fontsize=8)
        style(axi)

    if np.isfinite(v_ymin) and np.isfinite(v_ymax):
        pad = max(0.02, 0.04 * (v_ymax - v_ymin))
        for axv in (axes[0, 0], axes[0, 1]):
            axv.set_ylim(v_ymin - pad, v_ymax + pad)

    axes[0, 0].set_ylabel("Voltage [V]")
    axes[1, 0].set_ylabel("R60 [mΩ]")
    axes[2, 0].set_ylabel("inc% vs t1")
    fig.suptitle(
        "V±300s (900:Ch022 / 1300:Ch012) · R60 · inc% vs t1",
        fontweight="bold",
        fontsize=12.5,
    )
    fig.savefig(out, dpi=DPI)
    plt.close(fig)


def plot_sj1300_dchg_vq_every50(
    raws: dict[str, tuple[pd.DataFrame, list[int], str]],
    out_dir: Path,
    *,
    step: int = 50,
) -> None:
    """Per SJ1300 channel: full discharge V–Q every ``step`` tagged cycles."""
    for cell, (raw, tagged, arm) in raws.items():
        if arm != "SJ1300_dry":
            continue
        tmax = len(tagged)
        t_list = sorted(set([1] + list(range(step, tmax + 1, step))))
        profiles = []
        for tidx in t_list:
            q, v = dchg_qv(raw, tagged[tidx - 1])
            if q is not None:
                profiles.append((tidx, q, v))
        if not profiles:
            continue

        fig, ax = plt.subplots(figsize=(W_IN, 6.0))
        fig.subplots_adjust(left=0.09, right=0.98, bottom=0.11, top=0.90)
        nseg = max(len(profiles) - 1, 1)
        for k, (tidx, q, v) in enumerate(profiles):
            color = cm.viridis(k / nseg)
            ax.plot(q, v, color=color, lw=1.6, label=f"t{tidx}")
        ax.set_xlabel("Q [Ah]")
        ax.set_ylabel("V")
        ax.set_title(
            f"{arm} / {cell} — discharge V–Q every {step} tagged cycles",
            fontweight="bold",
        )
        ax.legend(loc="lower left", ncol=4, fontsize=7.5, framealpha=0.92)
        style(ax)
        fig.savefig(out_dir / f"{cell}_dchg_VQ_every{step}.png", dpi=DPI)
        plt.close(fig)
        print(f"  wrote {cell}_dchg_VQ_every{step}.png ({len(profiles)} curves)")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/r60_vwin_growth"),
    )
    p.add_argument("--pad-s", type=float, default=300.0, help="± seconds around discharge start")
    p.add_argument("--vq-step", type=int, default=50)
    p.add_argument("--cells", type=str, default="")
    p.add_argument(
        "--exclude",
        type=str,
        default="M01Ch025",
        help="Comma-separated cell ids to skip (default: M01Ch025)",
    )
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    want = {c.strip() for c in args.cells.split(",") if c.strip()} or set(DEFAULT_CELLS)
    exclude = {c.strip() for c in args.exclude.split(",") if c.strip()}
    frames: list[pd.DataFrame] = []
    raws: dict[str, tuple[pd.DataFrame, list[int], str]] = {}

    for cell_id, (path, arm) in DEFAULT_CELLS.items():
        if cell_id not in want or cell_id in exclude or not path.exists():
            continue
        print(f"[{cell_id}] …", flush=True)
        raw = load_raw(path)
        tagged = tagged_routine_cycles(raw)
        r60 = extract_r60_table(raw, tagged, cell_id, arm)
        r60.to_csv(out / f"{cell_id}_R60_vs_t1.csv", index=False)
        frames.append(r60)
        raws[cell_id] = (raw, tagged, arm)
        plot_cell(
            cell_id,
            arm,
            raw,
            tagged,
            r60,
            pad_s=args.pad_s,
            vq_step=args.vq_step,
            out=out,
        )

    if frames:
        plot_arm_r_and_inc(
            frames,
            raws,
            out / "00_arm_R60_inc_vs_t1.png",
            pad_s=args.pad_s,
            vq_step=args.vq_step,
        )
        plot_sj1300_dchg_vq_every50(raws, out, step=args.vq_step)
        pd.concat(frames, ignore_index=True).to_csv(out / "all_R60_vs_t1.csv", index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
