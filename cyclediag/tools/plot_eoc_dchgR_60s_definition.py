"""Explain EoC_dchgR_60s with marked V_ref / V_60s points (figure definition).

Matches: ΔV = V_ref(방전 직전) − V_60s(방전+60s),  R = ΔV / |ΔI|

Example::

    python -m cyclediag.tools.plot_eoc_dchgR_60s_definition \\
        --raw example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv \\
        --cycle 12 \\
        --out example/output/crossover_vs_sohq/present_1600x1000/r60_definition
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cyclediag.features.cc_cv import resolve_current_column
from cyclediag.features.lges_extract import _resistance_mohm, _sample_v_i_at_offsets
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv

W_IN, H_IN, DPI = 10.0, 6.5, 140


def _style(ax) -> None:
    ax.grid(True, alpha=0.28)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--raw",
        type=Path,
        default=Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"),
    )
    p.add_argument("--cycle", type=int, default=12)
    p.add_argument(
        "--out",
        type=Path,
        default=Path(
            "example/output/crossover_vs_sohq/present_1600x1000/r60_definition"
        ),
    )
    p.add_argument("--pad-before-s", type=float, default=120.0)
    p.add_argument("--pad-after-s", type=float, default=120.0)
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    raw = load_cycler_csv(args.raw, column_map=ColumnMap.studio_default())
    g = raw[raw["cycle"] == int(args.cycle)].copy()
    if g.empty:
        raise SystemExit(f"no cycle {args.cycle}")

    i_col = resolve_current_column(g) or "current"
    t = pd.to_numeric(g["time"], errors="coerce").to_numpy(float)
    v = pd.to_numeric(g["voltage"], errors="coerce").to_numpy(float)
    i = pd.to_numeric(g[i_col], errors="coerce").to_numpy(float)

    # Discharge start: first sample with strong discharge current
    dchg_mask = i < -1.0
    if not dchg_mask.any():
        raise SystemExit("no discharge current found")
    j_load = int(np.flatnonzero(dchg_mask)[0])
    # V_ref = last point with |I|~0 immediately before load (방전 직전)
    j_ref = j_load - 1
    while j_ref > 0 and abs(float(i[j_ref])) > 0.5:
        j_ref -= 1
    t0 = float(t[j_load])  # 방전 시작 (current onset)
    t_ref = float(t[j_ref])
    v_ref = float(v[j_ref])
    t_60 = t0 + 60.0
    # interpolate V,I at t0+60
    v_60 = float(np.interp(t_60, t, v))
    i_60 = float(np.interp(t_60, t, i))
    i_rest = float(i[j_ref])
    dI = abs(i_60 - i_rest)
    dV = v_ref - v_60
    r_ohm = dV / dI if dI > 1e-12 else float("nan")
    r_mohm = r_ohm * 1000.0

    # catalog path on raw discharge leg (should match)
    dchg = leg_segment(g, "discharge", charge_text="charge", discharge_text="discharge")
    samples = _sample_v_i_at_offsets(dchg, (0.0, 60.0))
    r_cat = _resistance_mohm(samples[0.0][0], samples[60.0][0], samples[60.0][1])

    # window for plot
    t_lo = t0 - float(args.pad_before_s)
    t_hi = t0 + float(args.pad_after_s)
    m = (t >= t_lo) & (t <= t_hi) & np.isfinite(t) & np.isfinite(v)
    tw, vw, iw = t[m], v[m], i[m]

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.10, right=0.97, bottom=0.10, top=0.86, hspace=0.08)

    ax = axes[0]
    ax.plot(tw, vw, color="#1e88e5", lw=2.0, label="Voltage")
    ax.axvline(t0, color="0.25", ls="--", lw=1.4)
    ax.axvline(t_60, color="#c62828", ls="--", lw=1.3, alpha=0.85)
    ax.scatter(
        [t_ref],
        [v_ref],
        s=90,
        color="#6a1b9a",
        zorder=5,
        edgecolors="k",
        linewidths=0.6,
        label=r"$V_{ref}$ (방전 직전)",
    )
    ax.scatter(
        [t_60],
        [v_60],
        s=90,
        color="#c62828",
        marker="D",
        zorder=5,
        edgecolors="k",
        linewidths=0.6,
        label=r"$V_{60s}$ (방전 + 60s)",
    )
    # ΔV arrow
    x_arrow = t0 + 75
    ax.annotate(
        "",
        xy=(x_arrow, v_60),
        xytext=(x_arrow, v_ref),
        arrowprops=dict(arrowstyle="<->", color="#c62828", lw=1.8),
    )
    ax.text(
        x_arrow + 4,
        0.5 * (v_ref + v_60),
        rf"$\Delta V = V_{{ref}} - V_{{60s}}$"
        f"\n= {dV:.4f} V",
        color="#c62828",
        fontsize=10,
        fontweight="bold",
        va="center",
    )
    ax.text(
        t0 + 2,
        v_ref + 0.012,
        "방전 시작",
        fontsize=9,
        color="0.2",
        fontweight="bold",
    )
    ax.text(
        t_60 + 2,
        v_60 - 0.025,
        "+60 s",
        fontsize=9,
        color="#c62828",
        fontweight="bold",
    )
    ax.set_ylabel("전압 (V)")
    ax.set_ylim(min(vw.min(), v_60) - 0.04, max(vw.max(), v_ref) + 0.04)
    ax.legend(loc="upper right", fontsize=9)
    _style(ax)

    ax = axes[1]
    ax.plot(tw, iw, color="#e53935", lw=2.0, label="Current")
    ax.axvline(t0, color="0.25", ls="--", lw=1.4)
    ax.axvline(t_60, color="#c62828", ls="--", lw=1.3, alpha=0.85)
    ax.axhline(0, color="k", lw=0.6, alpha=0.35)
    ax.scatter([t_ref], [i_rest], s=70, color="#6a1b9a", zorder=5, edgecolors="k", linewidths=0.5)
    ax.scatter(
        [t_60],
        [i_60],
        s=70,
        color="#c62828",
        marker="D",
        zorder=5,
        edgecolors="k",
        linewidths=0.5,
    )
    ax.text(
        t0 + 2,
        min(iw.min() * 0.15, -1),
        "방전 시작",
        fontsize=9,
        color="0.2",
        fontweight="bold",
    )
    ax.set_ylabel("전류 (A)")
    ax.set_xlabel("시간 (초)")
    ax.legend(loc="lower right", fontsize=9)
    _style(ax)

    cell = args.raw.stem.replace("_raw", "")
    fig.suptitle(
        f"{cell} cycle {args.cycle} — EoC_dchgR_60s 정의\n"
        rf"$EoC\_dchgR_{{60s}} = \Delta V / |\Delta I| = "
        rf"{dV:.4f}\,V\ /\ {dI:.3f}\,A = {r_mohm:.3f}\,m\Omega$"
        + (f"  (catalog match {r_cat:.3f} mΩ)" if r_cat is not None else ""),
        fontsize=12,
        fontweight="bold",
        y=0.98,
    )
    fig.savefig(out / f"{cell}_cyc{args.cycle}_EoC_dchgR_60s_definition.png", dpi=DPI)
    plt.close(fig)

    # also save a compact formula card
    summary = pd.DataFrame(
        [
            {
                "cell": cell,
                "cycle": args.cycle,
                "t_ref_s": t_ref,
                "t0_discharge_start_s": t0,
                "t_60s": t_60,
                "V_ref_V": v_ref,
                "V_60s_V": v_60,
                "I_rest_A": i_rest,
                "I_60s_A": i_60,
                "dV_V": dV,
                "dI_A": dI,
                "EoC_dchgR_60s_mOhm": r_mohm,
                "catalog_raw_leg_mOhm": r_cat,
            }
        ]
    )
    summary.to_csv(out / f"{cell}_cyc{args.cycle}_EoC_dchgR_60s_points.csv", index=False)
    print(summary.to_string(index=False))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
