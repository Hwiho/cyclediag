"""Compare EoC_dchgR_60s and dchg dQ/dV Ec2 peak intensity: SJ900 vs SJ1300.

Ec2 = discharge dQ/dV band P2_mid (3.55–3.78 V); intensity = |dQ/dV| at band max.
Tagged-routine cycles only; SoHQ BP1/BP2 from existing inflection CSVs when present.

Example::

    python -m cyclediag.tools.run_r60_ec2_arm_compare \\
        --out example/output/crossover_vs_sohq/present_1600x1000/r60_ec2
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cyclediag.analysis.sohq_inflection import detect_sohq_inflections
from cyclediag.features.dqdv_peaks import (
    DEFAULT_DISCHARGE_VOLTAGE_BANDS,
    DEFAULT_DQDV_PEAK_CONFIG,
    find_dqdv_peaks_banded,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv
from cyclediag.features.lges_extract import _resistance_mohm, _sample_v_i_at_offsets
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import build_protocol_exclusion, detect_protocol_flags
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe

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

BP_DIRS = {
    "set4_SJ900": Path("example/output/set4/inflection_tagged"),
    "SJ1300_dry": Path("example/output/SJ1300_dry/inflection_tagged"),
}

EC2_BAND = next(b for b in DEFAULT_DISCHARGE_VOLTAGE_BANDS if b[2] == "P2_mid")
W_IN, H_IN, DPI = 10.0, 6.25, 140
COLORS = {
    "M01Ch022": "#1f77b4",
    "M01Ch024": "#2ca02c",
    "M01Ch025": "#17becf",
    "M01Ch010": "#d62728",
    "M01Ch011": "#ff7f0e",
    "M01Ch012": "#9467bd",
}


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


def dchg_raw_leg(raw: pd.DataFrame, cycle: int) -> pd.DataFrame:
    """Raw discharge leg (includes I≈0 onset) for EoC_dchgR_60s = ΔV/|ΔI|."""
    g = raw[raw["cycle"] == cycle]
    return leg_segment(g, "discharge", charge_text="charge", discharge_text="discharge")


def dchg_qv(dchg: pd.DataFrame):
    """V–Q for Ec2 peaks: use dqdv prep on a copy; resistance uses raw separately."""
    if dchg is None or dchg.empty or "voltage" not in dchg.columns:
        return None, None
    d = prepare_leg_segment_for_dqdv(dchg.copy(), "discharge")
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


def eoc_dchg_r_60s(dchg: pd.DataFrame) -> float:
    """V_ref at discharge onset (I≈0), V/I at +60 s — matches definition figure."""
    samples = _sample_v_i_at_offsets(dchg, (0.0, 60.0))
    v0, _ = samples[0.0]
    vt, it = samples[60.0]
    r = _resistance_mohm(v0, vt, it)
    return float(r) if r is not None else float("nan")


def ec2_peak_intensity(v: np.ndarray, q: np.ndarray) -> tuple[float, float]:
    """Return (|H|, V) for discharge Ec2 = P2_mid band."""
    peaks = find_dqdv_peaks_banded(
        v,
        q,
        (EC2_BAND,),
        config=DEFAULT_DQDV_PEAK_CONFIG,
        min_band_height_frac=0.05,
    )
    if not peaks:
        return float("nan"), float("nan")
    pk = peaks[0]
    return abs(float(pk["H"])), float(pk["V"])


def load_bps(cell_id: str, arm: str) -> tuple[float | None, float | None]:
    path = BP_DIRS[arm] / f"{cell_id}_breakpoints.csv"
    if not path.exists():
        return None, None
    bp = pd.read_csv(path)
    if "tagged_cycle" not in bp.columns or bp.empty:
        return None, None
    t = pd.to_numeric(bp["tagged_cycle"], errors="coerce").dropna().to_numpy(float)
    if len(t) == 0:
        return None, None
    bp1 = float(t[0])
    bp2 = float(t[1]) if len(t) > 1 else None
    return bp1, bp2


def extract_cell(cell_id: str, path: Path, arm: str) -> pd.DataFrame:
    raw = load_raw(path)
    tagged = tagged_routine_cycles(raw)
    rows = []
    for tidx, rcyc in enumerate(tagged, start=1):
        dchg = dchg_raw_leg(raw, rcyc)
        r60 = eoc_dchg_r_60s(dchg) if not dchg.empty else float("nan")
        q, v = dchg_qv(dchg)
        inten, vv = (float("nan"), float("nan"))
        qmax = float("nan")
        if q is not None and v is not None:
            inten, vv = ec2_peak_intensity(v, q)
            qmax = float(np.nanmax(q))
        rows.append(
            {
                "arm": arm,
                "cell_id": cell_id,
                "tagged_cycle": tidx,
                "raw_cycle": rcyc,
                "dchgCapa_Ah": qmax,
                "EoC_dchgR_60s": r60,
                "dchg_dqdV_Ec2_peak_intensity": inten,
                "dchg_dqdV_Ec2_peak_V": vv,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # SoHQ from first 5 tagged capacities
    q0 = float(np.nanmedian(df["dchgCapa_Ah"].iloc[:5].to_numpy(float)))
    df["SoHQ"] = 100.0 * df["dchgCapa_Ah"] / q0 if q0 > 0 else np.nan
    bp1, bp2 = load_bps(cell_id, arm)
    df["BP1_tagged"] = bp1
    df["BP2_tagged"] = bp2
    if bp1 is None or bp2 is None:
        # fallback: detect on the fly
        sohq = df.dropna(subset=["SoHQ"])
        if len(sohq) >= 40:
            det = detect_sohq_inflections(
                sohq["tagged_cycle"].to_numpy(float),
                sohq["SoHQ"].to_numpy(float),
                max_breaks=2,
            )
            bps = list(det.get("breakpoints") or [])
            if bps:
                df["BP1_tagged"] = float(bps[0])
            if len(bps) > 1:
                df["BP2_tagged"] = float(bps[1])
    return df


def _mark_bps(ax, bp1, bp2):
    if bp1 is not None and np.isfinite(bp1):
        ax.axvline(bp1, color="0.35", ls="--", lw=1.0, alpha=0.8)
    if bp2 is not None and np.isfinite(bp2):
        ax.axvline(bp2, color="0.55", ls=":", lw=1.0, alpha=0.8)


def plot_metric_overlay(
    frames: list[pd.DataFrame],
    col: str,
    ylabel: str,
    title: str,
    out: Path,
):
    fig, ax = plt.subplots(figsize=(W_IN, H_IN), dpi=DPI)
    for df in frames:
        if df.empty or col not in df.columns:
            continue
        cell = df["cell_id"].iloc[0]
        arm = df["arm"].iloc[0]
        y = pd.to_numeric(df[col], errors="coerce")
        ax.plot(
            df["tagged_cycle"],
            y,
            color=COLORS.get(cell, "k"),
            lw=1.4,
            label=f"{arm}/{cell}",
            alpha=0.9,
        )
        _mark_bps(ax, df["BP1_tagged"].iloc[0], df["BP2_tagged"].iloc[0])
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_arm_panels(
    frames: list[pd.DataFrame],
    col: str,
    ylabel: str,
    title: str,
    out: Path,
):
    fig, axes = plt.subplots(1, 2, figsize=(W_IN, H_IN), dpi=DPI, sharey=True)
    for ax, arm in zip(axes, ("set4_SJ900", "SJ1300_dry")):
        for df in frames:
            if df.empty or df["arm"].iloc[0] != arm:
                continue
            cell = df["cell_id"].iloc[0]
            y = pd.to_numeric(df[col], errors="coerce")
            ax.plot(df["tagged_cycle"], y, color=COLORS.get(cell, "k"), lw=1.5, label=cell)
            _mark_bps(ax, df["BP1_tagged"].iloc[0], df["BP2_tagged"].iloc[0])
        ax.set_title(arm)
        ax.set_xlabel("Tagged cycle #")
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=8)
    axes[0].set_ylabel(ylabel)
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def regime_slopes(df: pd.DataFrame, col: str) -> list[dict]:
    bp1 = df["BP1_tagged"].iloc[0]
    bp2 = df["BP2_tagged"].iloc[0]
    edges = [1.0]
    if bp1 is not None and np.isfinite(bp1):
        edges.append(float(bp1))
    if bp2 is not None and np.isfinite(bp2):
        edges.append(float(bp2))
    edges.append(float(df["tagged_cycle"].max()) + 1e-9)
    edges = sorted(set(edges))
    rows = []
    x = df["tagged_cycle"].to_numpy(float)
    y = pd.to_numeric(df[col], errors="coerce").to_numpy(float)
    for i in range(len(edges) - 1):
        m = (x >= edges[i]) & (x < edges[i + 1]) & np.isfinite(y)
        if m.sum() < 5:
            continue
        xx, yy = x[m], y[m]
        slope = float(np.polyfit(xx, yy, 1)[0])
        rows.append(
            {
                "arm": df["arm"].iloc[0],
                "cell_id": df["cell_id"].iloc[0],
                "metric": col,
                "regime": f"S{i + 1}",
                "tagged_start": float(xx.min()),
                "tagged_end": float(xx.max()),
                "n": int(m.sum()),
                "y_start": float(yy[0]),
                "y_end": float(yy[-1]),
                "delta": float(yy[-1] - yy[0]),
                "slope_per_cyc": slope,
                "slope_per_100cyc": slope * 100.0,
                "BP1_tagged": bp1,
                "BP2_tagged": bp2,
            }
        )
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("example/output/crossover_vs_sohq/present_1600x1000/r60_ec2"),
    )
    p.add_argument("--cells", type=str, default="", help="Comma list, default all")
    args = p.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    want = {c.strip() for c in args.cells.split(",") if c.strip()} or set(DEFAULT_CELLS)
    frames: list[pd.DataFrame] = []
    slope_rows: list[dict] = []

    for cell_id, (path, arm) in DEFAULT_CELLS.items():
        if cell_id not in want:
            continue
        if not path.exists():
            print(f"skip missing {path}")
            continue
        print(f"extract {cell_id} ({arm}) …")
        df = extract_cell(cell_id, path, arm)
        df.to_csv(out / f"{cell_id}_r60_ec2.csv", index=False)
        frames.append(df)
        slope_rows.extend(regime_slopes(df, "EoC_dchgR_60s"))
        slope_rows.extend(regime_slopes(df, "dchg_dqdV_Ec2_peak_intensity"))
        print(
            f"  n={len(df)}  R60 [{df['EoC_dchgR_60s'].min():.2f},{df['EoC_dchgR_60s'].max():.2f}]"
            f"  Ec2I [{df['dchg_dqdV_Ec2_peak_intensity'].min():.2f},"
            f"{df['dchg_dqdV_Ec2_peak_intensity'].max():.2f}]"
            f"  BP1={df['BP1_tagged'].iloc[0]} BP2={df['BP2_tagged'].iloc[0]}"
        )

    if not frames:
        raise SystemExit("no cells extracted")

    all_df = pd.concat(frames, ignore_index=True)
    all_df.to_csv(out / "all_cells_r60_ec2.csv", index=False)
    slopes = pd.DataFrame(slope_rows)
    slopes.to_csv(out / "regime_slopes_r60_ec2.csv", index=False)

    plot_metric_overlay(
        frames,
        "EoC_dchgR_60s",
        "EoC_dchgR_60s (mΩ)",
        "EoC discharge start R @ 60 s — SJ900 vs SJ1300",
        out / "01_EoC_dchgR_60s_overlay.png",
    )
    plot_arm_panels(
        frames,
        "EoC_dchgR_60s",
        "EoC_dchgR_60s (mΩ)",
        "EoC_dchgR_60s by arm (dashed=BP1, dotted=BP2)",
        out / "02_EoC_dchgR_60s_by_arm.png",
    )
    plot_metric_overlay(
        frames,
        "dchg_dqdV_Ec2_peak_intensity",
        "|dQ/dV| Ec2 (P2_mid) intensity",
        "dchg dQ/dV Ec2 peak intensity — SJ900 vs SJ1300",
        out / "03_Ec2_peak_intensity_overlay.png",
    )
    plot_arm_panels(
        frames,
        "dchg_dqdV_Ec2_peak_intensity",
        "|dQ/dV| Ec2 intensity",
        "Ec2 peak intensity by arm (dashed=BP1, dotted=BP2)",
        out / "04_Ec2_peak_intensity_by_arm.png",
    )

    # dual-axis per representative cell each arm
    for cell in ("M01Ch022", "M01Ch011"):
        df = next((f for f in frames if f["cell_id"].iloc[0] == cell), None)
        if df is None:
            continue
        fig, ax1 = plt.subplots(figsize=(W_IN, H_IN), dpi=DPI)
        ax2 = ax1.twinx()
        ax1.plot(df["tagged_cycle"], df["EoC_dchgR_60s"], color="#1f77b4", lw=1.6, label="R60")
        ax2.plot(
            df["tagged_cycle"],
            df["dchg_dqdV_Ec2_peak_intensity"],
            color="#d62728",
            lw=1.6,
            label="Ec2 |H|",
        )
        _mark_bps(ax1, df["BP1_tagged"].iloc[0], df["BP2_tagged"].iloc[0])
        ax1.set_xlabel("Tagged cycle #")
        ax1.set_ylabel("EoC_dchgR_60s (mΩ)", color="#1f77b4")
        ax2.set_ylabel("Ec2 peak intensity", color="#d62728")
        ax1.set_title(f"{df['arm'].iloc[0]} / {cell}: R60 vs Ec2 intensity")
        ax1.grid(True, alpha=0.25)
        lines = ax1.get_lines() + ax2.get_lines()
        ax1.legend(lines, [ln.get_label() for ln in lines], loc="best", fontsize=9)
        fig.tight_layout()
        fig.savefig(out / f"05_{cell}_R60_vs_Ec2.png")
        plt.close(fig)

    # arm-mean summary at BOL / BP1 / BP2 / EOL
    summary_rows = []
    for df in frames:
        cell = df["cell_id"].iloc[0]
        arm = df["arm"].iloc[0]
        bp1 = df["BP1_tagged"].iloc[0]
        bp2 = df["BP2_tagged"].iloc[0]
        for label, sel in (
            ("BOL_t5", df["tagged_cycle"] <= 5),
            ("near_BP1", (df["tagged_cycle"] - bp1).abs() <= 3) if pd.notna(bp1) else None,
            ("near_BP2", (df["tagged_cycle"] - bp2).abs() <= 3) if pd.notna(bp2) else None,
            ("EOL_last5", df["tagged_cycle"] > df["tagged_cycle"].max() - 5),
        ):
            if sel is None:
                continue
            sub = df.loc[sel]
            if sub.empty:
                continue
            summary_rows.append(
                {
                    "arm": arm,
                    "cell_id": cell,
                    "window": label,
                    "tagged_mid": float(sub["tagged_cycle"].median()),
                    "EoC_dchgR_60s_mean": float(sub["EoC_dchgR_60s"].mean()),
                    "Ec2_intensity_mean": float(sub["dchg_dqdV_Ec2_peak_intensity"].mean()),
                    "Ec2_V_mean": float(sub["dchg_dqdV_Ec2_peak_V"].mean()),
                    "SoHQ_mean": float(sub["SoHQ"].mean()),
                }
            )
    pd.DataFrame(summary_rows).to_csv(out / "window_summary_r60_ec2.csv", index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
