"""SoHQ regime BPs + BP1/BP2 voltage / dQ/dV presentation figures.

Tagged-routine only. Default: SJ900 set4 + SJ1300 dry cells.

Example (local or Cursor Cloud / CI)::

    python -m cyclediag.tools.run_sohq_bp_presentation \\
        --out example/output/sohq_bp_presentation

    # single cell quick smoke
    python -m cyclediag.tools.run_sohq_bp_presentation \\
        --cells M01Ch022 --out /tmp/bp_pres --step 40
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

from cyclediag.analysis.sohq_inflection import detect_sohq_inflections
from cyclediag.features.dqdv_peaks import (
    DEFAULT_DQDV_PEAK_CONFIG,
    compute_dqdv,
    compute_dvdq,
)
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

DEFAULT_CELLS = {
    "M01Ch022": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"),
    "M01Ch024": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"),
    "M01Ch025": Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv"),
    "M01Ch010": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"),
    "M01Ch011": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"),
    "M01Ch012": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"),
}

W_IN, H_IN, DPI = 10.0, 6.25, 140


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


def build_sohq_table(raw: pd.DataFrame, tagged: list[int], cell_id: str) -> pd.DataFrame:
    q0s = []
    for rcyc in tagged[:5]:
        q, _ = dchg_qv(raw, rcyc)
        if q is not None:
            q0s.append(float(np.nanmax(q)))
    q_bol = float(np.nanmedian(q0s)) if q0s else float("nan")
    rows = []
    for tidx, rcyc in enumerate(tagged, start=1):
        q, _ = dchg_qv(raw, rcyc)
        if q is None:
            continue
        qmax = float(np.nanmax(q))
        sohq = 100.0 * qmax / q_bol if q_bol and np.isfinite(q_bol) else float("nan")
        rows.append(
            {
                "cell_id": cell_id,
                "tagged_cycle": tidx,
                "cycle": rcyc,
                "SoHQ": sohq,
                "Qmax": qmax,
            }
        )
    return pd.DataFrame(rows)


def style(ax) -> None:
    ax.grid(True, alpha=0.28)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)


def sample_around(bp: float, n_tagged: int, before: int = 40, after: int = 80, step: int = 20):
    lo = max(1, int(bp) - before)
    hi = min(n_tagged, int(bp) + after)
    ts = list(range(lo, hi + 1, step))
    if int(bp) not in ts:
        ts.append(int(bp))
        ts.sort()
    return ts


def plot_sohq_regimes(df: pd.DataFrame, out: Path, *, title: str) -> dict:
    res = detect_sohq_inflections(df, max_breaks=2, method="piecewise", min_seg_points=40)
    if res is None:
        return {}
    bp1 = res.inflections[0].tagged_cycle if res.inflections else None
    bp2 = res.inflections[1].tagged_cycle if len(res.inflections) > 1 else None

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.10, top=0.88, hspace=0.16)
    edge = ["#1565c0", "#c62828", "#6a1b9a"]
    span = ["#bbdefb", "#ffcdd2", "#e1bee7"]

    ax = axes[0]
    ax.plot(res.x, res.sohq, color="#a0c4e8", lw=1.0, alpha=0.65, label="SoHQ raw")
    ax.plot(res.x, res.sohq_smooth, color="#1565c0", lw=2.1, label="SoHQ smooth")
    for i, r in enumerate(res.regimes):
        ax.axvspan(r.tagged_start, r.tagged_end, color=span[i % 3], alpha=0.20, zorder=0)
    ymin = float(np.nanmin(res.sohq_smooth)) - 1.5
    ymax = float(np.nanmax(res.sohq_smooth)) + 0.5
    head = (ymax - ymin) * 0.26
    ax.set_ylim(ymin, ymax + head)
    for i, r in enumerate(res.regimes):
        mid = 0.5 * (r.tagged_start + r.tagged_end)
        ax.text(
            mid,
            ymax + head * 0.55,
            f"S{r.seg_id}: {r.slope_pct_per_100cyc:+.2f}%/100cyc",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=edge[i % 3],
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="white",
                edgecolor=edge[i % 3],
                lw=1.2,
                alpha=0.98,
            ),
            zorder=10,
            clip_on=False,
        )
    for t, lab, col, ls in (
        (bp1, "BP1", "#1565c0", "--"),
        (bp2, "BP2", "#6a1b9a", "-."),
    ):
        if t is None:
            continue
        j = int(np.argmin(np.abs(res.x - t)))
        ax.axvline(t, color=col, ls=ls, lw=1.7)
        ax.scatter([t], [res.sohq_smooth[j]], color=col, s=55, zorder=5, edgecolors="k", linewidths=0.4)
        ax.text(t + 6, res.sohq_smooth[j] + 1.2, lab, color=col, fontsize=10, fontweight="bold")
    ax.set_ylabel("SoHQ [%]")
    ax.legend(loc="lower left", fontsize=9)
    ax.set_title(title, fontweight="bold")
    style(ax)

    ax = axes[1]
    ax.plot(res.x, res.fade_rate, color="#d62728", lw=1.9, label="local dSoHQ/100cyc")
    ax.axhline(0, color="k", lw=0.7, alpha=0.4)
    fmin = float(np.nanmin(res.fade_rate[np.isfinite(res.fade_rate)]))
    fmax = float(np.nanmax(res.fade_rate[np.isfinite(res.fade_rate)]))
    lab_y = fmin - (fmax - fmin) * 0.22
    ax.set_ylim(lab_y - (fmax - fmin) * 0.12, fmax + (fmax - fmin) * 0.08)
    for i, r in enumerate(res.regimes):
        col = edge[i % 3]
        ax.hlines(r.slope_pct_per_100cyc, r.tagged_start, r.tagged_end, colors=col, lw=2.4)
        mid = 0.5 * (r.tagged_start + r.tagged_end)
        ax.text(
            mid,
            lab_y,
            f"S{r.seg_id} {r.slope_pct_per_100cyc:+.2f}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=col,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=col, alpha=0.98),
            clip_on=False,
        )
    if bp1 is not None:
        ax.axvline(bp1, color="#1565c0", ls="--", lw=1.5)
    if bp2 is not None:
        ax.axvline(bp2, color="#6a1b9a", ls="-.", lw=1.5)
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("dSoHQ / 100 cyc [%]")
    ax.legend(loc="upper right", fontsize=9)
    style(ax)
    fig.savefig(out, dpi=DPI, bbox_inches=None, pad_inches=0)
    plt.close(fig)

    res.breakpoints_table().to_csv(out.with_name(out.stem + "_breakpoints.csv"), index=False)
    res.regimes_table().to_csv(out.with_name(out.stem + "_regimes.csv"), index=False)
    return {
        "bp1": bp1,
        "bp2": bp2,
        "regimes": [
            {
                "seg_id": r.seg_id,
                "tagged_start": r.tagged_start,
                "tagged_end": r.tagged_end,
                "dSoHQ_pct_per_100cyc": r.slope_pct_per_100cyc,
                "delta_SoHQ": r.delta_sohq,
            }
            for r in res.regimes
        ],
    }


def plot_bp_profiles(
    raw: pd.DataFrame,
    tagged: list[int],
    *,
    cell_id: str,
    bp1: float,
    bp2: float,
    out: Path,
    step: int = 20,
) -> pd.DataFrame:
    n = len(tagged)
    windows = {
        "BP1": (bp1, sample_around(bp1, n, step=step)),
        "BP2": (bp2, sample_around(bp2, n, after=min(80, max(0, n - int(bp2))), step=step)),
    }
    data: dict[str, list[dict]] = {}
    for win, (bp, ts) in windows.items():
        profiles = []
        for t in ts:
            q, v = dchg_qv(raw, tagged[t - 1])
            if q is None:
                continue
            v_dq, dqdv = compute_dqdv(v, q, DEFAULT_DQDV_PEAK_CONFIG)
            qx, dvdq = compute_dvdq(q, v, DEFAULT_DQDV_PEAK_CONFIG)
            profiles.append(
                dict(t=t, c=tagged[t - 1], q=q, v=v, v_dq=v_dq, dqdv=dqdv, qx=qx, dvdq=dvdq, bp=int(bp))
            )
        data[win] = profiles

    all_p = data["BP1"] + data["BP2"]
    if not all_p:
        return pd.DataFrame()

    qmax = max(float(np.nanmax(p["q"])) for p in all_p)
    vmin = min(float(np.nanmin(p["v"])) for p in all_p)
    vmax = max(float(np.nanmax(p["v"])) for p in all_p)
    dq_stack = np.concatenate([p["dqdv"][np.isfinite(p["dqdv"])] for p in all_p])
    dq_lo, dq_hi = np.nanpercentile(dq_stack, [2, 98])
    lim_q = (-0.5, qmax * 1.02)
    lim_v = (vmin - 0.05, vmax + 0.05)
    span = dq_hi - dq_lo
    lim_dq = (dq_lo - 0.08 * span, dq_hi + 0.08 * span)

    fig, axes = plt.subplots(2, 2, figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.07, right=0.99, bottom=0.09, top=0.88, wspace=0.22, hspace=0.28)
    for col_i, win in enumerate(["BP1", "BP2"]):
        bp, profs = windows[win][0], data[win]
        nseg = max(len(profs) - 1, 1)
        axv, axd = axes[0, col_i], axes[1, col_i]
        for k, p in enumerate(profs):
            color = cm.viridis(k / nseg)
            lw = 2.4 if p["t"] == int(bp) else 1.4
            lab = f"t{p['t']}" + (" *BP" if p["t"] == int(bp) else "")
            axv.plot(p["q"], p["v"], color=color, lw=lw, label=lab)
            axd.plot(p["v_dq"], p["dqdv"], color=color, lw=lw, label=lab)
        axv.set_xlim(*lim_q)
        axv.set_ylim(*lim_v)
        axd.set_xlim(lim_v[0], lim_v[1])
        axd.set_ylim(*lim_dq)
        axv.set_title(f"{win} (BP={int(bp)}) — V-Q", fontweight="bold")
        axd.set_title(f"{win} — dQ/dV", fontweight="bold")
        axv.set_xlabel("Q [Ah]")
        axv.set_ylabel("V")
        axd.set_xlabel("V")
        axd.set_ylabel("dQ/dV [Ah/V]")
        axv.legend(loc="lower left", ncol=2, fontsize=7, framealpha=0.92)
        axd.legend(loc="upper right", ncol=2, fontsize=7, framealpha=0.92)
        style(axv)
        style(axd)
    fig.suptitle(
        f"{cell_id} — V-Q & dQ/dV every {step} tagged cycles around BP1 / BP2",
        fontsize=13,
        fontweight="bold",
        y=0.97,
    )
    fig.savefig(out, dpi=DPI, bbox_inches=None, pad_inches=0)
    plt.close(fig)

    # metrics
    rows = []
    for win, profs in data.items():
        for p in profs:
            qmax_i = float(np.nanmax(p["q"]))

            def v_at(qa, q=p["q"], v=p["v"], qmax_i=qmax_i):
                if qmax_i < qa:
                    return float("nan")
                return float(np.interp(qa, q, v))

            dq, vv = p["dqdv"], p["v_dq"]
            fin = np.isfinite(dq) & np.isfinite(vv)
            peak_v = peak_dq = float("nan")
            if fin.sum() > 5:
                band = fin & (vv >= 3.4) & (vv <= 4.0)
                if band.sum() >= 3:
                    ipeak = np.flatnonzero(band)[int(np.nanargmax(dq[band]))]
                    peak_v, peak_dq = float(vv[ipeak]), float(dq[ipeak])
            rows.append(
                dict(
                    cell=cell_id,
                    window=win,
                    tagged=p["t"],
                    cycle=p["c"],
                    at_BP=int(p["t"] == p["bp"]),
                    Qmax=qmax_i,
                    V_at_Q5=v_at(5),
                    V_at_Q15=v_at(15),
                    V_at_Q30=v_at(30),
                    dQdV_peak_V=peak_v,
                    dQdV_peak=peak_dq,
                )
            )
    mdf = pd.DataFrame(rows)
    mdf.to_csv(out.with_name(out.stem + "_metrics.csv"), index=False)
    return mdf


def run_cell(cell_id: str, raw_path: Path, out_dir: Path, step: int) -> dict:
    print(f"[{cell_id}] load {raw_path}", flush=True)
    raw = load_raw(raw_path)
    tagged = tagged_routine_cycles(raw)
    sohq = build_sohq_table(raw, tagged, cell_id)
    cell_out = out_dir / cell_id
    cell_out.mkdir(parents=True, exist_ok=True)
    sohq.to_csv(cell_out / "sohq_tagged.csv", index=False)

    info = plot_sohq_regimes(
        sohq,
        cell_out / f"{cell_id}_sohq_dsohq_regimes.png",
        title=f"{cell_id} — SoHQ & dSoHQ/100cyc (tagged)",
    )
    if not info or info.get("bp1") is None or info.get("bp2") is None:
        print(f"[{cell_id}] skip BP profiles (need 2 BPs)", flush=True)
        return {"cell": cell_id, **info, "n_tagged": len(tagged)}

    plot_bp_profiles(
        raw,
        tagged,
        cell_id=cell_id,
        bp1=float(info["bp1"]),
        bp2=float(info["bp2"]),
        out=cell_out / f"{cell_id}_BP1_BP2_VQ_dQdV.png",
        step=step,
    )
    print(
        f"[{cell_id}] BP1={info['bp1']:.0f} BP2={info['bp2']:.0f} "
        f"regimes={[r['dSoHQ_pct_per_100cyc'] for r in info['regimes']]}",
        flush=True,
    )
    return {"cell": cell_id, "n_tagged": len(tagged), **info}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("example/output/sohq_bp_presentation"))
    p.add_argument(
        "--cells",
        nargs="+",
        default=list(DEFAULT_CELLS.keys()),
        help="Cell IDs to process",
    )
    p.add_argument("--step", type=int, default=20, help="Tagged-cycle stride around BPs")
    p.add_argument("--repo-root", type=Path, default=Path("."))
    args = p.parse_args(argv)

    root = args.repo_root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    out.mkdir(parents=True, exist_ok=True)

    summaries = []
    for cid in args.cells:
        if cid not in DEFAULT_CELLS:
            print(f"skip unknown cell {cid}", flush=True)
            continue
        raw_path = root / DEFAULT_CELLS[cid]
        if not raw_path.exists():
            print(f"skip missing fixture {raw_path}", flush=True)
            continue
        summaries.append(run_cell(cid, raw_path, out, args.step))

    # summary table of regime slopes
    rows = []
    for s in summaries:
        for r in s.get("regimes") or []:
            rows.append(
                {
                    "cell": s["cell"],
                    "n_tagged": s.get("n_tagged"),
                    "BP1": s.get("bp1"),
                    "BP2": s.get("bp2"),
                    "regime": f"S{r['seg_id']}",
                    "tagged_start": r["tagged_start"],
                    "tagged_end": r["tagged_end"],
                    "dSoHQ_pct_per_100cyc": r["dSoHQ_pct_per_100cyc"],
                    "delta_SoHQ": r["delta_SoHQ"],
                }
            )
    if rows:
        pd.DataFrame(rows).to_csv(out / "regime_dsohq_summary.csv", index=False)
    print(f"DONE → {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
