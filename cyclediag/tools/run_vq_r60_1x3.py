"""1x3 panel: full dchg V-Q (every 20) | V±5min | R60 inc% vs t1.

Default cells: SJ900 Ch022, SJ1300 Ch012 (arm representatives).

Example::

    python -m cyclediag.tools.run_vq_r60_1x3 \\
        --out example/output/crossover_vs_sohq/present_1600x1000/vq_r60_1x3
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

W_IN, H_IN, DPI = 12.0, 4.2, 140
PAD_S = 300.0  # ±5 min
R60_SRC = Path("example/output/crossover_vs_sohq/present_1600x1000/r60_ec2")
BP_DIRS = {
    "set4_SJ900": Path("example/output/set4/inflection_tagged"),
    "SJ1300_dry": Path("example/output/SJ1300_dry/inflection_tagged"),
}
DEFAULT_CELLS = {
    "M01Ch022": (Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"), "set4_SJ900"),
    "M01Ch012": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"), "SJ1300_dry"),
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


def discharge_window_v(cycle_df: pd.DataFrame, *, pad_s: float = PAD_S):
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
    t0 = float(t[j_load])
    sel = (t >= t0 - pad_s) & (t <= t0 + pad_s)
    if sel.sum() < 10:
        return None
    return t[sel] - t0, v[sel]


def load_r60(cell_id: str, arm: str, raw: pd.DataFrame, tagged: list[int]) -> pd.DataFrame:
    csv = R60_SRC / f"{cell_id}_r60_ec2.csv"
    if csv.exists():
        df = pd.read_csv(csv)
        y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce")
        if float(np.nanmedian(y.to_numpy(float))) >= 1.5:
            bp1, bp2 = load_bps(cell_id, arm)
            df["BP1_tagged"] = bp1
            df["BP2_tagged"] = bp2
            r1 = float(y.iloc[0])
            df["R60_inc_pct_vs_t1"] = (y / r1 - 1.0) * 100.0
            return df
    rows = []
    for tidx, rcyc in enumerate(tagged, start=1):
        g = raw[raw["cycle"] == rcyc]
        d = leg_segment(g, "discharge", charge_text="charge", discharge_text="discharge")
        r = float("nan")
        if not d.empty:
            s = _sample_v_i_at_offsets(d, (0.0, 60.0))
            rr = _resistance_mohm(s[0.0][0], s[60.0][0], s[60.0][1])
            r = float(rr) if rr is not None else float("nan")
        rows.append(dict(tagged_cycle=tidx, raw_cycle=rcyc, EoC_dchgR_60s=r))
    df = pd.DataFrame(rows)
    bp1, bp2 = load_bps(cell_id, arm)
    df["BP1_tagged"] = bp1
    df["BP2_tagged"] = bp2
    y = pd.to_numeric(df["EoC_dchgR_60s"], errors="coerce")
    r1 = float(y.iloc[0])
    df["R60_inc_pct_vs_t1"] = (y / r1 - 1.0) * 100.0
    return df


def plot_1x3(
    cell_id: str,
    arm: str,
    raw: pd.DataFrame,
    tagged: list[int],
    r60: pd.DataFrame,
    out: Path,
    *,
    vq_step: int = 20,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(W_IN, H_IN))
    fig.subplots_adjust(left=0.06, right=0.98, bottom=0.14, top=0.84, wspace=0.28)

    tmax = len(tagged)
    t_list = sorted(set([1] + list(range(vq_step, tmax + 1, vq_step))))
    nseg = max(len(t_list) - 1, 1)

    # --- 1) full discharge V-Q every 20 ---
    ax = axes[0]
    for k, tidx in enumerate(t_list):
        q, v = dchg_qv(raw, tagged[tidx - 1])
        if q is None:
            continue
        ax.plot(q, v, color=cm.viridis(k / nseg), lw=1.35, label=f"t{tidx}")
    ax.set_xlabel("Q [Ah]")
    ax.set_ylabel("V")
    ax.set_title(f"Discharge V–Q every {vq_step}", fontweight="bold")
    ax.legend(loc="lower left", ncol=2, fontsize=6.5, framealpha=0.9)
    style(ax)

    # --- 2) ±5 min around discharge start ---
    ax = axes[1]
    for k, tidx in enumerate(t_list):
        win = discharge_window_v(raw[raw["cycle"] == tagged[tidx - 1]], pad_s=PAD_S)
        if win is None:
            continue
        t_rel, vv = win
        ax.plot(t_rel / 60.0, vv, color=cm.viridis(k / nseg), lw=1.35, label=f"t{tidx}")
    ax.axvline(0.0, color="0.25", ls="--", lw=1.2)
    ax.axvline(1.0, color="#c62828", ls=":", lw=1.1, alpha=0.85)
    ax.set_xlim(-PAD_S / 60.0, PAD_S / 60.0)
    ax.set_xlabel("Time from discharge start [min]")
    ax.set_ylabel("V")
    ax.set_title(r"V $\pm$5 min ($V_{ref}@0$, $+60s$)", fontweight="bold")
    ax.legend(loc="lower left", ncol=2, fontsize=6.5, framealpha=0.9)
    style(ax)

    # --- 3) R60 increase vs t1 ---
    ax = axes[2]
    x = r60["tagged_cycle"].to_numpy(float)
    inc = pd.to_numeric(r60["R60_inc_pct_vs_t1"], errors="coerce").to_numpy(float)
    ax.plot(x, inc, color="#ffab91", lw=0.85, alpha=0.75, label="raw")
    ax.plot(x, smooth(inc, 11), color="#d84315", lw=2.0, label="smooth")
    ax.axhline(0, color="k", lw=0.7, alpha=0.4)
    bp1, bp2 = r60["BP1_tagged"].iloc[0], r60["BP2_tagged"].iloc[0]
    for t, lab, col, ls in ((bp1, "BP1", "#1565c0", "--"), (bp2, "BP2", "#6a1b9a", "-.")):
        if t is None or not np.isfinite(t):
            continue
        ax.axvline(t, color=col, ls=ls, lw=1.4)
        ax.text(t + 3, float(np.nanmax(inc[np.isfinite(inc)])) * 0.92, lab, color=col, fontsize=8, fontweight="bold")
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel(r"R60 inc% vs t1  ($(R-R_1)/R_1$)")
    ax.set_title("EoC_dchgR_60s growth vs t1", fontweight="bold")
    ax.legend(fontsize=8)
    style(ax)

    fig.suptitle(
        f"{arm} / {cell_id} — discharge V–Q · ±5 min · R60 inc%",
        fontweight="bold",
        fontsize=13,
        y=0.98,
    )
    fig.savefig(out / f"{cell_id}_1x3_VQ_pm5min_R60inc.png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/vq_r60_1x3"),
    )
    p.add_argument("--vq-step", type=int, default=20)
    p.add_argument(
        "--cells",
        type=str,
        default="M01Ch022,M01Ch012",
        help="Comma-separated cells (default: Ch022, Ch012)",
    )
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    # allow extra known cells via default map extension
    extra = {
        "M01Ch024": (Path("example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"), "set4_SJ900"),
        "M01Ch010": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"), "SJ1300_dry"),
        "M01Ch011": (Path("example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"), "SJ1300_dry"),
    }
    catalog = {**DEFAULT_CELLS, **extra}

    want = [c.strip() for c in args.cells.split(",") if c.strip()]
    for cell_id in want:
        if cell_id not in catalog:
            print(f"unknown cell {cell_id}")
            continue
        path, arm = catalog[cell_id]
        if not path.exists():
            print(f"missing {path}")
            continue
        print(f"[{cell_id}] …", flush=True)
        raw = load_raw(path)
        tagged = tagged_routine_cycles(raw)
        r60 = load_r60(cell_id, arm, raw, tagged)
        plot_1x3(cell_id, arm, raw, tagged, r60, out, vq_step=args.vq_step)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
