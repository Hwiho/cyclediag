"""SJ1300: charge + discharge V–Q every 50 tagged cycles, square panels.

Per channel (Ch010/011/012): 1×2 square figure (charge | discharge).
Also a combined 3×2 square-panel overview.

Example::

    python -m cyclediag.tools.run_sj1300_vq_charge_discharge_square \\
        --out example/output/crossover_vs_sohq/present_1600x1000/sj1300_vq_square
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

from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

DPI = 140
# square canvas: each panel roughly square
PANEL_IN = 5.0
CELLS = {
    "M01Ch010": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"),
    "M01Ch011": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"),
    "M01Ch012": Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"),
}


def style(ax) -> None:
    ax.grid(True, alpha=0.28)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)
    ax.set_box_aspect(1)  # square panel


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


def leg_qv(raw: pd.DataFrame, cycle: int, leg: str):
    g = raw[raw["cycle"] == cycle]
    d = leg_segment(g, leg, charge_text="charge", discharge_text="discharge")
    if d.empty or "voltage" not in d.columns:
        return None, None
    v = pd.to_numeric(d["voltage"], errors="coerce").to_numpy(float)
    q = None
    prefer = "charge_capacity" if leg == "charge" else "discharge_capacity"
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


def collect_profiles(raw: pd.DataFrame, tagged: list[int], step: int):
    tmax = len(tagged)
    t_list = sorted(set([1] + list(range(step, tmax + 1, step))))
    out = {"charge": [], "discharge": []}
    for tidx in t_list:
        rcyc = tagged[tidx - 1]
        for leg in ("charge", "discharge"):
            q, v = leg_qv(raw, rcyc, leg)
            if q is not None:
                out[leg].append((tidx, q, v))
    return out


def _lims(profiles: list[tuple]) -> tuple[tuple[float, float], tuple[float, float]]:
    qmax = max(float(np.nanmax(q)) for _, q, _ in profiles)
    vmin = min(float(np.nanmin(v)) for _, _, v in profiles)
    vmax = max(float(np.nanmax(v)) for _, _, v in profiles)
    return (-0.5, qmax * 1.02), (vmin - 0.05, vmax + 0.05)


def plot_on_ax(ax, profiles: list[tuple], *, title: str, qlim, vlim) -> None:
    if not profiles:
        ax.set_title(title)
        return
    nseg = max(len(profiles) - 1, 1)
    for k, (tidx, q, v) in enumerate(profiles):
        color = cm.viridis(k / nseg)
        ax.plot(q, v, color=color, lw=1.5, label=f"t{tidx}")
    ax.set_xlim(*qlim)
    ax.set_ylim(*vlim)
    ax.set_xlabel("Q [Ah]")
    ax.set_ylabel("V")
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="best", ncol=2, fontsize=7, framealpha=0.92)
    style(ax)


def plot_cell_square(cell_id: str, profiles: dict, out: Path, step: int) -> None:
    # shared axis limits across charge/discharge for fair compare
    all_p = profiles["charge"] + profiles["discharge"]
    if not all_p:
        return
    qlim, vlim = _lims(all_p)
    # also unify Q max / V for both panels of this cell
    if profiles["charge"] and profiles["discharge"]:
        qlim_c, vlim_c = _lims(profiles["charge"])
        qlim_d, vlim_d = _lims(profiles["discharge"])
        qlim = (min(qlim_c[0], qlim_d[0]), max(qlim_c[1], qlim_d[1]))
        vlim = (min(vlim_c[0], vlim_d[0]), max(vlim_c[1], vlim_d[1]))

    fig, axes = plt.subplots(1, 2, figsize=(2 * PANEL_IN, PANEL_IN))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.12, top=0.86, wspace=0.22)
    plot_on_ax(
        axes[0],
        profiles["charge"],
        title=f"Charge  (every {step})",
        qlim=qlim,
        vlim=vlim,
    )
    plot_on_ax(
        axes[1],
        profiles["discharge"],
        title=f"Discharge  (every {step})",
        qlim=qlim,
        vlim=vlim,
    )
    fig.suptitle(
        f"SJ1300_dry / {cell_id} — V–Q every {step} tagged cycles",
        fontweight="bold",
        fontsize=13,
    )
    fig.savefig(out / f"{cell_id}_chg_dchg_VQ_every{step}_square.png", dpi=DPI)
    plt.close(fig)


def plot_overview_square(
    all_profiles: dict[str, dict],
    out: Path,
    step: int,
) -> None:
    """3×2 square panels: rows=cells, cols=charge|discharge. Shared V/Q limits."""
    cells = [c for c in ("M01Ch010", "M01Ch011", "M01Ch012") if c in all_profiles]
    if not cells:
        return
    # global limits
    stack = []
    for c in cells:
        stack.extend(all_profiles[c]["charge"])
        stack.extend(all_profiles[c]["discharge"])
    qlim, vlim = _lims(stack)

    fig, axes = plt.subplots(3, 2, figsize=(2 * PANEL_IN, 3 * PANEL_IN))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.04, top=0.93, hspace=0.22, wspace=0.18)
    for r, cell in enumerate(cells):
        plot_on_ax(
            axes[r, 0],
            all_profiles[cell]["charge"],
            title=f"{cell} charge",
            qlim=qlim,
            vlim=vlim,
        )
        plot_on_ax(
            axes[r, 1],
            all_profiles[cell]["discharge"],
            title=f"{cell} discharge",
            qlim=qlim,
            vlim=vlim,
        )
        # only bottom row keeps x labels dense; reduce legend size
        for ax in (axes[r, 0], axes[r, 1]):
            ax.legend(loc="best", ncol=2, fontsize=6.5, framealpha=0.9)
    fig.suptitle(
        f"SJ1300_dry — charge & discharge V–Q every {step} tagged (square panels)",
        fontweight="bold",
        fontsize=14,
    )
    fig.savefig(out / f"00_SJ1300_chg_dchg_VQ_every{step}_square.png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/sj1300_vq_square"),
    )
    p.add_argument("--step", type=int, default=50)
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    all_profiles: dict[str, dict] = {}
    for cell_id, path in CELLS.items():
        if not path.exists():
            print(f"skip missing {path}")
            continue
        print(f"[{cell_id}] …", flush=True)
        raw = load_raw(path)
        tagged = tagged_routine_cycles(raw)
        profiles = collect_profiles(raw, tagged, args.step)
        all_profiles[cell_id] = profiles
        plot_cell_square(cell_id, profiles, out, args.step)
        print(
            f"  charge={len(profiles['charge'])}  discharge={len(profiles['discharge'])}"
        )

    plot_overview_square(all_profiles, out, args.step)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
