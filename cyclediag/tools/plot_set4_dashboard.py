"""Generate static dashboard PNGs for SJ900 set4 (Ch22 / Ch25).

Usage:
  python -m cyclediag.tools.plot_set4_dashboard
  python -m cyclediag.tools.plot_set4_dashboard --out example/output/set4_new/plots
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "example" / "output" / "set4_new"
DEFAULT_RPT = ROOT / "example" / "output" / "rpt_recovery_ch22"
DEFAULT_OUT = ROOT / "example" / "output" / "set4_new" / "plots"

CELLS = ("M01Ch022", "M01Ch025")
COLORS = {"M01Ch022": "#2563eb", "M01Ch025": "#dc2626"}


def _load_cell(data_dir: Path, cell_id: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    feat = pd.read_csv(data_dir / f"{cell_id}_new_subset.csv")
    dcir = pd.read_csv(data_dir / f"{cell_id}_dcir_trend.csv")
    summ_path = data_dir / f"{cell_id}_summary.json"
    summary = json.loads(summ_path.read_text(encoding="utf-8")) if summ_path.exists() else {}
    feat["cycle"] = pd.to_numeric(feat["cycle"], errors="coerce")
    dcir["cycle"] = pd.to_numeric(dcir["cycle"], errors="coerce")
    return feat.sort_values("cycle"), dcir.sort_values("cycle"), summary


def _pulse_mask(feat: pd.DataFrame) -> pd.Series:
    cols = [c for c in feat.columns if c.startswith("R_30s_total_soc")]
    if not cols:
        return pd.Series(False, index=feat.index)
    return pd.to_numeric(feat.get("R_30s_total_soc50", feat[cols[0]]), errors="coerce").notna()


def _save(fig: plt.Figure, out_dir: Path, name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_executive_summary(cells: dict, out_dir: Path) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("SJ900 set4 executive summary (45C, 0.5C)", fontsize=14, fontweight="bold")

    for ax, (metric, label, unit) in zip(
        axes.flat,
        [
            ("SoHQ", "SoHQ", "%"),
            ("R_30s_total_soc50", "R total SOC50", "mOhm"),
            ("self_discharge_rate_soc80", "Self-discharge SOC80", "mV/h"),
            ("VE", "Voltage efficiency", ""),
        ],
    ):
        for cid, (feat, dcir, summ) in cells.items():
            src = dcir if metric.startswith("R_") or metric.startswith("self") else feat
            if metric not in src.columns:
                continue
            y = pd.to_numeric(src[metric], errors="coerce")
            x = src["cycle"]
            m = y.notna()
            ax.plot(x[m], y[m], "-o", ms=3, lw=1.2, color=COLORS[cid], label=cid, alpha=0.85)
        ax.set_xlabel("Cycle")
        ax.set_ylabel(f"{label} {unit}".strip())
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    fig.tight_layout()
    return _save(fig, out_dir, "00_executive_summary.png")


def plot_sohq_fade(cells: dict, rpt_dir: Path | None, out_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2 if "M01Ch022" in cells else 1, figsize=(14, 5), squeeze=False)
    fig.suptitle("Capacity fade (SoHQ)", fontsize=13, fontweight="bold")

    corrected = None
    if rpt_dir and (rpt_dir / "sohq_corrected_series.csv").exists():
        corrected = pd.read_csv(rpt_dir / "sohq_corrected_series.csv")

    for j, cid in enumerate(CELLS):
        if cid not in cells:
            continue
        ax = axes[0, j] if len(axes.shape) > 1 and axes.shape[1] > j else axes[0, 0]
        feat, _, summ = cells[cid]
        rout = feat[~_pulse_mask(feat)]
        y = pd.to_numeric(rout.get("SoHQ"), errors="coerce")
        ax.plot(rout["cycle"], y, ".", color=COLORS[cid], ms=4, alpha=0.5, label="SoHQ routine")
        if cid == "M01Ch022" and corrected is not None:
            cyc = pd.to_numeric(corrected["cycle"], errors="coerce")
            corr = pd.to_numeric(corrected.get("SoHQ_corrected"), errors="coerce")
            rout2 = pd.to_numeric(corrected.get("SoHQ_routine"), errors="coerce")
            ax.plot(cyc, rout2, "-", color="#94a3b8", lw=0.8, alpha=0.6)
            ax.plot(cyc, corr, "-", color="#16a34a", lw=1.2, label="SoHQ corrected (Ch22)")
        ax.set_title(f"{cid}  end={summ.get('SoHQ_last', '?'):.1f}%")
        ax.set_xlabel("Cycle")
        ax.set_ylabel("SoHQ (%)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return _save(fig, out_dir, "01_sohq_fade.png")


def plot_dcir_components(cells: dict, out_dir: Path) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("DC-IR decomposition (SOC50)", fontsize=13, fontweight="bold")
    metrics = [
        ("R_ohmic_soc50", "R ohmic"),
        ("R_ct_soc50", "R ct"),
        ("A_diff_soc50", "A diff (sqrt t)"),
        ("R_30s_total_soc50", "R @ 30s total"),
    ]
    for ax, (col, title) in zip(axes.flat, metrics):
        for cid, (_, dcir, _) in cells.items():
            if col not in dcir.columns:
                continue
            y = pd.to_numeric(dcir[col], errors="coerce")
            ax.plot(dcir["cycle"], y, "-o", ms=4, lw=1.3, color=COLORS[cid], label=cid)
        ax.set_title(title)
        ax.set_xlabel("Cycle")
        ax.set_ylabel("mOhm" if "A_diff" not in col else "mOhm/sqrt(s)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, out_dir, "02_dcir_components.png")


def plot_dcir_soc_structure(cells: dict, out_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("DC-IR SOC structure", fontsize=13, fontweight="bold")
    for ax, col, title in zip(
        axes,
        ["R_ratio_20_50", "R_SOC_slope"],
        ["R20/R50 ratio", "R vs SOC slope"],
    ):
        for cid, (_, dcir, _) in cells.items():
            if col not in dcir.columns:
                continue
            y = pd.to_numeric(dcir[col], errors="coerce")
            ax.plot(dcir["cycle"], y, "-o", ms=4, color=COLORS[cid], label=cid)
        ax.set_title(title)
        ax.set_xlabel("Cycle")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, out_dir, "03_dcir_soc_structure.png")


def plot_relaxation_sd(cells: dict, out_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Relaxation & self-discharge", fontsize=13, fontweight="bold")

    ax = axes[0]
    for cid, (feat, dcir, _) in cells.items():
        qr = feat.dropna(subset=["Q_relax_pct"]) if "Q_relax_pct" in feat.columns else pd.DataFrame()
        if qr.empty:
            continue
        q = qr.drop_duplicates("cycle")
        ax.bar(
            q["cycle"].astype(str) if len(q) <= 12 else q["cycle"],
            pd.to_numeric(q["Q_relax_pct"], errors="coerce"),
            width=8 if len(q) > 6 else 0.4,
            alpha=0.7,
            color=COLORS[cid],
            label=cid,
        )
    ax.axhline(0.065, color="gray", ls="--", label="noise floor 0.065%")
    ax.set_title("Q_relax per RPT block (%)")
    ax.set_xlabel("Cycle (block marker)")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)

    ax = axes[1]
    for cid, (_, dcir, _) in cells.items():
        col = "self_discharge_rate_soc80"
        if col not in dcir.columns:
            continue
        y = pd.to_numeric(dcir[col], errors="coerce")
        ax.plot(dcir["cycle"], y, "-o", ms=4, color=COLORS[cid], label=cid)
    ax.set_title("Self-discharge SOC80 (mV/h)")
    ax.set_xlabel("Cycle")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, out_dir, "04_relaxation_selfdischarge.png")


def plot_ocv_drift(data_dir: Path, out_dir: Path) -> Path | None:
    """Build OCV drift from raw if stepemd available."""
    try:
        from cyclediag.features.enrich_assb import enrich_feature_table
        from cyclediag.features.stepemd_extract import extract_stepemd_features_table
        from cyclediag.io.cycler_csv import load_cycler_csv
        from cyclediag.io.stepemd_csv import load_stepemd_csv
        from cyclediag.io.studio_map import studio_column_map
    except ImportError:
        return None

    raw_hits = list((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*raw.csv"))
    step_hits = list((ROOT / "example/docs/features/M01Ch022").glob("*Ch22*stepend.csv"))
    if not raw_hits or not step_hits:
        return None

    raw = load_cycler_csv(str(raw_hits[0]), column_map=studio_column_map())
    step = load_stepemd_csv(step_hits[0])
    feat = extract_stepemd_features_table(step_df=step, path=step_hits[0])
    _, meta = enrich_feature_table(feat, raw, expected_pulse_current=77.0)
    ocv = pd.DataFrame(meta.get("ocv_drift_blocks", []))
    if ocv.empty:
        return None

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Quasi-OCV drift across SOC (Ch22 DC-IR blocks)", fontsize=13, fontweight="bold")
    x = ocv["block_start_cycle"]

    axes[0, 0].plot(x, ocv["ocv_V_inf_soc80"], "o-", label="SOC80")
    axes[0, 0].plot(x, ocv["ocv_V_inf_soc50"], "s-", label="SOC50")
    axes[0, 0].plot(x, ocv["ocv_V_inf_soc20"], "^-", label="SOC20")
    axes[0, 0].set_title("V_inf pre-pulse rest (V)")
    axes[0, 0].set_xlabel("Block start cycle")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(x, ocv["ocv_spread_20_80"], "o-", color="#7c3aed")
    axes[0, 1].set_title("ocv_spread_20_80 (V)")
    axes[0, 1].set_xlabel("Block start cycle")
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(x, ocv["ocv_parallel_shift"], "o-", color="#059669")
    axes[1, 0].set_title("Parallel shift vs BOL (LLI proxy, V)")
    axes[1, 0].set_xlabel("Block start cycle")
    axes[1, 0].grid(True, alpha=0.3)

    modes = ocv["ocv_drift_mode"].astype(str)
    axes[1, 1].bar(range(len(ocv)), [1] * len(ocv), color="#94a3b8")
    axes[1, 1].set_xticks(range(len(ocv)))
    axes[1, 1].set_xticklabels([f"b{i}\n{int(c)}" for i, c in zip(ocv["block_id"], x)], fontsize=8)
    axes[1, 1].set_title("ocv_drift_mode")
    for i, m in enumerate(modes):
        axes[1, 1].text(i, 0.5, m, ha="center", fontsize=7, rotation=90)

    fig.tight_layout()
    path = _save(fig, out_dir, "05_ocv_drift_ch22.png")
    ocv.to_csv(out_dir / "ocv_drift_ch22_blocks.csv", index=False)
    return path


def plot_rpt_recovery(rpt_dir: Path, out_dir: Path) -> Path | None:
    if not rpt_dir.exists():
        return None
    overlay = rpt_dir / "rpt_recovery_overlay.csv"
    blocks = rpt_dir / "rpt_recovery_blocks.csv"
    anchors = rpt_dir / "pre_rpt_anchors.csv"
    if not overlay.exists():
        return None

    ov = pd.read_csv(overlay)
    bl = pd.read_csv(blocks) if blocks.exists() else pd.DataFrame()
    anc = pd.read_csv(anchors) if anchors.exists() else pd.DataFrame()

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("RPT recovery bump (Ch22, 0.5C routine)", fontsize=13, fontweight="bold")

    ax = axes[0, 0]
    for bid, grp in ov.groupby("block_id"):
        phase = grp["life_phase"].iloc[0]
        c = "#2563eb" if phase == "early" else "#dc2626"
        ax.plot(grp["rel_cycle"], grp["SoHQ_routine"], "o-", ms=3, lw=1, color=c, alpha=0.35)
    mean_p = ov.groupby("rel_cycle")["SoHQ_routine"].mean()
    ax.plot(mean_p.index, mean_p.values, "k-", lw=2, label="mean")
    ax.axvline(5, color="gray", ls=":", label="POST_RPT_EXCLUDE=5")
    ax.set_title("Post-RPT recovery overlay")
    ax.set_xlabel("Rel cycle after block end")
    ax.set_ylabel("SoHQ routine (%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    if not bl.empty:
        ax = axes[0, 1]
        ax.bar(bl["block_id"], bl["rpt_recovery_decay_cycles"], color="#6366f1")
        ax.axhline(5, color="gray", ls=":")
        ax.set_title("Recovery lambda (cycles)")
        ax.set_xlabel("RPT block #")
        ax.grid(True, axis="y", alpha=0.3)

        ax = axes[1, 0]
        ax.bar(bl["block_id"], bl["rpt_recovery_amplitude"], color="#059669")
        ax.axhline(0.065, color="red", ls="--", label="Q_relax floor")
        ax.set_title("Recovery amplitude A (% SoHQ)")
        ax.set_xlabel("RPT block #")
        ax.legend(fontsize=8)
        ax.grid(True, axis="y", alpha=0.3)

    if not anc.empty and "anchor_sohq" in anc.columns:
        ax = axes[1, 1]
        ax.plot(anc["block_start"], anc["anchor_sohq"], "s-", color="#dc2626", label="pre-RPT anchor")
        if "delta_first_vs_immediate" in bl.columns:
            ax2 = ax.twinx()
            ax2.bar(bl["block_id"], bl["delta_first_vs_immediate"], alpha=0.3, color="#f97316", label="1st post - immediate")
            ax2.set_ylabel("delta vs immediate pre-RPT (%)")
        ax.set_title("Pre-RPT anchors")
        ax.set_xlabel("Block start cycle")
        ax.set_ylabel("SoHQ anchor (%)")
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return _save(fig, out_dir, "06_rpt_recovery_ch22.png")


def plot_ve_hysteresis(cells: dict, out_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("VE & hysteresis (routine cycles)", fontsize=13, fontweight="bold")
    for ax, col, title in zip(axes, ["VE", "hyst_frac_low"], ["Voltage efficiency", "Hyst frac low SOC"]):
        for cid, (feat, _, _) in cells.items():
            rout = feat[~_pulse_mask(feat)]
            if col not in rout.columns:
                continue
            y = pd.to_numeric(rout[col], errors="coerce")
            ax.plot(rout["cycle"], y, "-", lw=1.2, color=COLORS[cid], label=cid, alpha=0.85)
        ax.set_title(title)
        ax.set_xlabel("Cycle")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, out_dir, "07_ve_hysteresis.png")


def plot_diagnosis_scores(cells: dict, out_dir: Path) -> Path:
    modes = [
        "contact_loss_score",
        "microshort_score",
        "LLI_pattern_score",
        "LAM_PE_pattern_score",
        "solid_diffusion_score",
    ]
    fig, axes = plt.subplots(len(modes), 1, figsize=(14, 12), sharex=True)
    fig.suptitle("ASSB diagnosis mode scores (routine)", fontsize=13, fontweight="bold")
    for ax, mode in zip(axes, modes):
        for cid, (feat, _, _) in cells.items():
            rout = feat[~_pulse_mask(feat)]
            if mode not in rout.columns:
                continue
            y = pd.to_numeric(rout[mode], errors="coerce")
            ax.plot(rout["cycle"], y, "-", lw=1.0, color=COLORS[cid], label=cid, alpha=0.8)
        ax.set_ylabel(mode.replace("_score", ""), fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.05, 1.05)
    axes[-1].set_xlabel("Cycle")
    axes[0].legend(fontsize=8, ncol=2)
    fig.tight_layout()
    return _save(fig, out_dir, "08_diagnosis_scores.png")


def plot_per_cell_dashboard(cells: dict, out_dir: Path) -> list[Path]:
    paths = []
    for cid, (feat, dcir, summ) in cells.items():
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle(f"{cid} multi-metric dashboard", fontsize=14, fontweight="bold")
        gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

        def _ax(r, c):
            return fig.add_subplot(gs[r, c])

        rout = feat[~_pulse_mask(feat)]
        ax = _ax(0, 0)
        ax.plot(rout["cycle"], pd.to_numeric(rout["SoHQ"], errors="coerce"), ".", ms=3, color=COLORS[cid])
        ax.set_title(f"SoHQ (end {summ.get('SoHQ_last', float('nan')):.1f}%)")
        ax.grid(True, alpha=0.3)

        ax = _ax(0, 1)
        if "R_30s_total_soc50" in dcir.columns:
            ax.plot(dcir["cycle"], dcir["R_30s_total_soc50"], "o-", ms=3)
        ax.set_title("R30 SOC50")
        ax.grid(True, alpha=0.3)

        ax = _ax(0, 2)
        if "self_discharge_rate_soc80" in dcir.columns:
            ax.plot(dcir["cycle"], dcir["self_discharge_rate_soc80"], "o-", ms=3, color="#f97316")
        ax.set_title("Self-discharge SOC80")
        ax.grid(True, alpha=0.3)

        ax = _ax(1, 0)
        if "VE" in rout.columns:
            ax.plot(rout["cycle"], pd.to_numeric(rout["VE"], errors="coerce"), "-", lw=1)
        ax.set_title("VE")
        ax.grid(True, alpha=0.3)

        ax = _ax(1, 1)
        if "Q_relax_pct" in feat.columns:
            q = feat.dropna(subset=["Q_relax_pct"]).drop_duplicates("cycle")
            ax.bar(q["cycle"], q["Q_relax_pct"], width=10, alpha=0.7)
            ax.axhline(0.065, color="gray", ls="--")
        ax.set_title("Q_relax %")
        ax.grid(True, axis="y", alpha=0.3)

        ax = _ax(1, 2)
        for col in ("R_ohmic_soc50", "R_ct_soc50"):
            if col in dcir.columns:
                ax.plot(dcir["cycle"], dcir[col], "o-", ms=2, label=col.replace("_soc50", ""))
        ax.legend(fontsize=7)
        ax.set_title("R ohmic / R ct")
        ax.grid(True, alpha=0.3)

        ax = _ax(2, 0)
        if "contact_loss_score" in rout.columns:
            ax.plot(rout["cycle"], rout["contact_loss_score"], "-", color=COLORS[cid])
        ax.set_title("contact_loss")
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

        ax = _ax(2, 1)
        if "LLI_pattern_score" in rout.columns:
            ax.plot(rout["cycle"], rout["LLI_pattern_score"], "-", label="LLI")
        if "LAM_PE_pattern_score" in rout.columns:
            ax.plot(rout["cycle"], rout["LAM_PE_pattern_score"], "-", label="LAM_PE")
        ax.legend(fontsize=7)
        ax.set_title("LLI / LAM pattern")
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

        ax = _ax(2, 2)
        ax.axis("off")
        lines = [
            f"Cycles analyzed: {summ.get('n_cycles_analyzed')}/{summ.get('n_cycles_raw')}",
            f"SoHQ: {summ.get('SoHQ_first', 0):.1f} -> {summ.get('SoHQ_last', 0):.1f}%",
            f"R30: {summ.get('R_30s_total_soc50_first', 0):.2f} -> {summ.get('R_30s_total_soc50_last', 0):.2f} mOhm",
            f"sd80: {summ.get('self_discharge_rate_soc80_first', 0):.1f} -> {summ.get('self_discharge_rate_soc80_last', 0):.1f} mV/h",
            f"VE: {summ.get('VE_first', 0):.3f} -> {summ.get('VE_last', 0):.3f}",
            "CE median unreliable in this run",
        ]
        ax.text(0.05, 0.95, "\n".join(lines), va="top", fontsize=10, family="monospace")

        paths.append(_save(fig, out_dir, f"09_dashboard_{cid}.png"))
    return paths


def write_index(out_dir: Path, paths: list[Path]) -> None:
    lines = ["# SJ900 set4 dashboard plots", "", "Generated PNGs for quick visual review.", ""]
    for p in sorted(paths):
        lines.append(f"- [{p.name}]({p.name})")
    lines.extend([
        "",
        "## Data sources",
        "- `../M01Ch022_new_subset.csv`, `../M01Ch025_new_subset.csv`",
        "- `../M01Ch022_dcir_trend.csv`, `../M01Ch025_dcir_trend.csv`",
        "- `../../rpt_recovery_ch22/` (Ch22 RPT recovery)",
        "",
        "Regenerate: `python -m cyclediag.tools.plot_set4_dashboard`",
    ])
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--rpt", type=Path, default=DEFAULT_RPT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    cells: dict = {}
    for cid in CELLS:
        csv_path = args.data / f"{cid}_new_subset.csv"
        if not csv_path.exists():
            print("skip missing", cid)
            continue
        cells[cid] = _load_cell(args.data, cid)

    if not cells:
        print("No set4 data found at", args.data)
        return 1

    paths: list[Path] = []
    paths.append(plot_executive_summary(cells, args.out))
    paths.append(plot_sohq_fade(cells, args.rpt, args.out))
    paths.append(plot_dcir_components(cells, args.out))
    paths.append(plot_dcir_soc_structure(cells, args.out))
    paths.append(plot_relaxation_sd(cells, args.out))
    p = plot_ocv_drift(args.data, args.out)
    if p:
        paths.append(p)
    p = plot_rpt_recovery(args.rpt, args.out)
    if p:
        paths.append(p)
    paths.append(plot_ve_hysteresis(cells, args.out))
    paths.append(plot_diagnosis_scores(cells, args.out))
    paths.extend(plot_per_cell_dashboard(cells, args.out))
    write_index(args.out, paths)

    print(f"Wrote {len(paths)} plots to {args.out}")
    for p in paths:
        print(" ", p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
