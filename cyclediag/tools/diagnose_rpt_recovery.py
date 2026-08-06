"""RPT post-block recovery diagnostic — overlay, λ fit, permanent-step test.

Usage:
  python -m cyclediag.tools.diagnose_rpt_recovery \\
    --stepemd example/docs/features/M01Ch022/*Ch22*stepend.csv \\
    --out example/output/rpt_recovery_ch22
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.analysis.rpt_recovery import analyze_rpt_recovery, apply_recovery_correction  # noqa: E402
from cyclediag.features.stepemd_extract import extract_stepemd_features_table  # noqa: E402
from cyclediag.io.cycle_protocol import POST_RPT_EXCLUDE  # noqa: E402
from cyclediag.io.stepemd_csv import cell_id_from_path, load_stepemd_csv  # noqa: E402


def _resolve_input(path: str) -> Path:
    p = Path(path)
    if p.exists():
        return p
    matches = sorted(ROOT.glob(path))
    if not matches:
        raise FileNotFoundError(f"No file matching: {path}")
    return matches[0]


def _plot_overlay(result, out_dir: Path) -> None:
    overlay = result.overlay_table()
    if overlay.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    colors_early = "#2563eb"
    colors_late = "#dc2626"

    for block_id, grp in overlay.groupby("block_id"):
        phase = grp["life_phase"].iloc[0]
        color = colors_early if phase == "early" else colors_late
        ax.plot(
            grp["rel_cycle"],
            grp["SoHQ_routine"],
            "o-",
            color=color,
            alpha=0.35,
            markersize=4,
            linewidth=1,
            label=f"block {block_id} ({phase})" if block_id <= 2 or block_id == result.n_blocks else None,
        )

    # Mean profile across blocks
    mean_prof = overlay.groupby("rel_cycle")["SoHQ_routine"].mean()
    ax.plot(mean_prof.index, mean_prof.values, "k-", linewidth=2.5, label="mean SoHQ_routine")

    # Mean recovery component
    blocks = result.blocks_table()
    lam_median = blocks["rpt_recovery_decay_cycles"].median()
    a_median = blocks["rpt_recovery_amplitude"].median()
    if np.isfinite(lam_median) and np.isfinite(a_median):
        k = np.arange(1, int(result.post_window) + 1)
        ax.plot(k, a_median * np.exp(-k / lam_median), "g--", linewidth=2, label=f"median fit A*exp(-k/lam), lam={lam_median:.1f}")

    ax.axvline(POST_RPT_EXCLUDE, color="gray", linestyle=":", label=f"POST_RPT_EXCLUDE={POST_RPT_EXCLUDE}")
    ax.set_xlabel("Relative cycle after RPT block end (n - n_block_end)")
    ax.set_ylabel("SoHQ_routine (%)")
    ax.set_title(f"RPT recovery overlay — {result.cell_id or 'cell'} ({result.n_blocks} blocks)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "overlay_sohq_routine.png", dpi=150)
    plt.close(fig)


def _plot_lambda_vs_block(result, out_dir: Path) -> None:
    blocks = result.blocks_table()
    if blocks.empty:
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    x = blocks["block_end_cycle"]
    axes[0].bar(blocks["block_id"], blocks["rpt_recovery_decay_cycles"], color="#6366f1")
    axes[0].axhline(POST_RPT_EXCLUDE, color="gray", linestyle=":", label=f"fixed exclude={POST_RPT_EXCLUDE}")
    axes[0].set_xlabel("RPT block #")
    axes[0].set_ylabel("lambda (cycles)")
    axes[0].set_title("Recovery time constant λ per block")
    axes[0].legend()

    axes[1].bar(blocks["block_id"], blocks["rpt_recovery_amplitude"], color="#059669")
    axes[1].set_xlabel("RPT block #")
    axes[1].set_ylabel("A (% SoHQ)")
    axes[1].set_title("Recovery amplitude A per block")

    fig.suptitle(f"Block-end cycles: {', '.join(str(int(v)) for v in x)}")
    fig.tight_layout()
    fig.savefig(out_dir / "lambda_amplitude_by_block.png", dpi=150)
    plt.close(fig)


def _plot_contamination(result, out_dir: Path) -> None:
    series = result.series
    fig, ax = plt.subplots(figsize=(12, 5))
    cyc = series["cycle"]
    mixed = pd.to_numeric(series.get("SoHQ_mixed"), errors="coerce")
    rout = pd.to_numeric(series.get("SoHQ_routine"), errors="coerce")
    corr = apply_recovery_correction(result)
    corrected = pd.to_numeric(corr.get("SoHQ_corrected"), errors="coerce")

    ax.plot(cyc, mixed, ".", color="#94a3b8", markersize=2, alpha=0.5, label="SoHQ_mixed (all cycles)")
    ax.plot(cyc, rout, "-", color="#2563eb", linewidth=1.2, label="SoHQ_routine (0.5C only)")
    ax.plot(cyc, corrected, "-", color="#16a34a", linewidth=1.0, alpha=0.8, label="SoHQ_corrected")
    for b in result.blocks:
        ax.axvspan(b.block_start, b.block_end, color="#fde68a", alpha=0.25)
    ax.set_xlabel("Cycle")
    ax.set_ylabel("SoHQ (%)")
    ax.set_title("Series separation: mixed vs routine vs recovery-corrected")
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "series_separation.png", dpi=150)
    plt.close(fig)


def _plot_anchors(result, corrected_df, out_dir: Path) -> None:
    """Pre-RPT anchor series (clean) vs routine vs corrected."""
    anchors = result.anchors.dropna(subset=["anchor_sohq"])
    if anchors.empty:
        return
    series = result.series
    fig, ax = plt.subplots(figsize=(12, 5))
    cyc = series["cycle"]
    rout = pd.to_numeric(series.get("SoHQ_routine"), errors="coerce")
    corr = pd.to_numeric(corrected_df.get("SoHQ_corrected"), errors="coerce")
    ax.plot(cyc, rout, "-", color="#2563eb", linewidth=1.0, alpha=0.7, label="SoHQ_routine (0.5C)")
    ax.plot(cyc, corr, "-", color="#16a34a", linewidth=1.0, label="SoHQ_corrected")
    ax.plot(
        anchors["anchor_cycle"],
        anchors["anchor_sohq"],
        "s",
        color="#dc2626",
        markersize=8,
        zorder=5,
        label="pre-RPT anchor (mean last 5 routine cyc)",
    )
    for _, row in anchors.iterrows():
        ax.axvline(row["block_start"], color="#fde68a", alpha=0.4, linewidth=0.8)
    ax.set_xlabel("Cycle")
    ax.set_ylabel("SoHQ (%)")
    ax.set_title("Pre-RPT anchors vs routine (0.5C-only comparison)")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "pre_rpt_anchors.png", dpi=150)
    plt.close(fig)


def _plot_bump_contamination(result, out_dir: Path) -> None:
    seg = result.bump_segments
    if seg.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 4))
    x = (seg["anchor_cycle_start"] + seg["anchor_cycle_end"]) / 2.0
    ax.bar(range(len(seg)), seg["bump_contamination"], color="#7c3aed")
    ax.axhline(0, color="k", linewidth=0.8)
    ax.set_xticks(range(len(seg)))
    ax.set_xticklabels([f"seg {int(i)}" for i in seg["segment_id"]], fontsize=8)
    ax.set_ylabel("bump_contamination")
    ax.set_title("fade_rate_intra / fade_rate_inter - 1  (anchor-to-anchor baseline)")
    for i, (_, row) in enumerate(seg.iterrows()):
        ax.text(i, row["bump_contamination"], f"cyc~{int(x.iloc[i])}", ha="center", va="bottom", fontsize=7)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "bump_contamination.png", dpi=150)
    plt.close(fig)


def _plot_amplitude_onset(result, out_dir: Path) -> None:
    blocks = result.blocks_table()
    if blocks.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(blocks["block_id"], blocks["rpt_recovery_amplitude"], color="#059669", label="A (fit)")
    ax.axhline(result.noise_floor_pct, color="#dc2626", linestyle="--", label=f"Q_relax floor {result.noise_floor_pct}%")
    if result.onset and result.onset.bump_onset_block_id:
        ax.axvline(
            result.onset.bump_onset_block_id,
            color="#f97316",
            linestyle=":",
            linewidth=2,
            label=f"bump_onset block {int(result.onset.bump_onset_block_id)}",
        )
    ax.set_xlabel("RPT block #")
    ax.set_ylabel("A (% SoHQ)")
    ax.set_title("Recovery amplitude vs noise floor (reversible loss at rest)")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "amplitude_bump_onset.png", dpi=150)
    plt.close(fig)


def _plot_onset_timeline(result, out_dir: Path) -> None:
    if result.onset is None:
        return
    o = result.onset
    if o.bump_onset_cycle is None and o.knee_onset_cycle is None:
        return
    fig, ax = plt.subplots(figsize=(10, 2.5))
    xmax = max(v for v in (o.bump_onset_cycle, o.knee_onset_cycle, 500) if v is not None)
    ax.set_xlim(0, xmax * 1.05)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    if o.bump_onset_cycle is not None:
        ax.axvline(o.bump_onset_cycle, color="#f97316", linewidth=2, label=f"bump_onset @ cyc {o.bump_onset_cycle:.0f}")
        ax.text(o.bump_onset_cycle, 0.5, " bump_onset", va="center", color="#f97316", fontsize=9)
    if o.knee_onset_cycle is not None:
        ax.axvline(o.knee_onset_cycle, color="#dc2626", linewidth=2, label=f"knee_onset @ cyc {o.knee_onset_cycle:.0f}")
        ax.text(o.knee_onset_cycle, 0.5, " knee_onset", va="center", color="#dc2626", fontsize=9)
    ax.set_xlabel("Cycle")
    title = "Onset ordering"
    if o.bump_precedes_knee is True:
        title += " — bump precedes knee (hypothesis supported)"
    elif o.bump_precedes_knee is False:
        title += " — knee precedes bump"
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "bump_vs_knee_onset.png", dpi=150)
    plt.close(fig)


def _plot_permanent_steps(result, out_dir: Path) -> None:
    blocks = result.blocks_table()
    if blocks.empty or blocks["permanent_step_pct"].isna().all():
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(blocks["block_id"], blocks["permanent_step_pct"], color="#f97316")
    ax.axhline(0, color="k", linewidth=0.8)
    ax.set_xlabel("RPT block #")
    ax.set_ylabel("Permanent step after recovery (% SoHQ)")
    ax.set_title("(c) Residual baseline shift — positive = step up persists")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "permanent_step_by_block.png", dpi=150)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="RPT recovery bump diagnostic")
    ap.add_argument("--stepemd", required=True, help="StepEnd CSV path or glob under repo root")
    ap.add_argument("--out", default="example/output/rpt_recovery", help="Output directory")
    ap.add_argument("--post-window", type=int, default=20, help="Post-block routine cycles to fit")
    ap.add_argument("--pre-lookback", type=int, default=20, help="Pre-block routine cycles for trend")
    ap.add_argument("--anchor-width", type=int, default=5, help="Pre-RPT anchor window (routine 0.5C cycles)")
    ap.add_argument("--noise-floor", type=float, default=0.065, help="Q_relax noise floor (pct SoHQ) for bump_onset")
    args = ap.parse_args()

    stepemd_path = _resolve_input(args.stepemd)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    step_df = load_stepemd_csv(stepemd_path)
    table = extract_stepemd_features_table(step_df=step_df, path=stepemd_path)
    cell_id = cell_id_from_path(stepemd_path)

    result = analyze_rpt_recovery(
        table,
        step_df,
        cell_id=cell_id,
        post_window=args.post_window,
        pre_lookback=args.pre_lookback,
        anchor_width=args.anchor_width,
        noise_floor_pct=args.noise_floor,
    )

    blocks_df = result.blocks_table()
    overlay_df = result.overlay_table()
    corrected_df = apply_recovery_correction(result)

    blocks_df.to_csv(out_dir / "rpt_recovery_blocks.csv", index=False)
    overlay_df.to_csv(out_dir / "rpt_recovery_overlay.csv", index=False)
    result.anchors.to_csv(out_dir / "pre_rpt_anchors.csv", index=False)
    result.bump_segments.to_csv(out_dir / "bump_contamination.csv", index=False)
    result.contamination.to_csv(out_dir / "sohq_contamination.csv", index=False)
    corrected_df.to_csv(out_dir / "sohq_corrected_series.csv", index=False)

    summary = {
        "cell_id": cell_id,
        "stepemd": str(stepemd_path),
        "n_blocks": result.n_blocks,
        "post_rpt_exclude_current": POST_RPT_EXCLUDE,
        "post_window_fit": args.post_window,
        "lambda_median": float(blocks_df["rpt_recovery_decay_cycles"].median()) if not blocks_df.empty else None,
        "lambda_max": float(blocks_df["rpt_recovery_decay_cycles"].max()) if not blocks_df.empty else None,
        "amplitude_median_pct": float(blocks_df["rpt_recovery_amplitude"].median()) if not blocks_df.empty else None,
        "permanent_step_median_pct": float(blocks_df["permanent_step_pct"].median()) if not blocks_df.empty else None,
        "noise_floor_pct": args.noise_floor,
        "blocks": blocks_df.to_dict(orient="records"),
        "bump_segments": result.bump_segments.to_dict(orient="records"),
        "onset": {
            "bump_onset_block_id": result.onset.bump_onset_block_id if result.onset else None,
            "bump_onset_cycle": result.onset.bump_onset_cycle if result.onset else None,
            "bump_onset_amplitude": result.onset.bump_onset_amplitude if result.onset else None,
            "knee_onset_cycle": result.onset.knee_onset_cycle if result.onset else None,
            "knee_onset_method": result.onset.knee_onset_method if result.onset else None,
            "bump_precedes_knee": result.onset.bump_precedes_knee if result.onset else None,
            "cycle_gap": result.onset.cycle_gap if result.onset else None,
        },
        "diagnosis": [],
    }

    lam_max = summary["lambda_max"]
    if lam_max is not None and lam_max > POST_RPT_EXCLUDE + 2:
        summary["diagnosis"].append(
            f"lambda_max={lam_max:.1f} > POST_RPT_EXCLUDE={POST_RPT_EXCLUDE}: fixed exclude under-corrects late blocks"
        )
    post_contam = result.contamination[result.contamination["in_post_rpt_buffer"]]
    if not post_contam.empty:
        d = post_contam["delta_mixed_minus_routine"].dropna()
        if not d.empty and d.abs().max() > 0.3:
            summary["diagnosis"].append(
                "Post-RPT buffer cycles differ from routine interpolation in mixed SoHQ - use SoHQ_routine for knee"
            )
    if result.onset and result.onset.bump_precedes_knee:
        summary["diagnosis"].append(
            f"bump_onset (cyc {result.onset.bump_onset_cycle:.0f}) precedes knee_onset (cyc {result.onset.knee_onset_cycle:.0f}) by {result.onset.cycle_gap:.0f} cyc"
        )
    seg = result.bump_segments
    if not seg.empty:
        rising = seg[seg["bump_contamination"] > 0.05]
        if not rising.empty:
            first = rising.iloc[0]
            summary["diagnosis"].append(
                f"bump_contamination > 0 from segment {int(first['segment_id'])} (cyc~{int(first['anchor_cycle_start'])})"
            )
    perm = blocks_df["permanent_step_pct"].dropna()
    if not perm.empty and perm.median() > 0.15:
        summary["diagnosis"].append(
            f"Median permanent step {perm.median():.2f}% - partial (c) component; record, do not subtract"
        )

    def _json_safe(obj):
        if isinstance(obj, dict):
            return {k: _json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_json_safe(v) for v in obj]
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return obj

    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(_json_safe(summary), f, indent=2, ensure_ascii=False)

    _plot_overlay(result, out_dir)
    _plot_lambda_vs_block(result, out_dir)
    _plot_contamination(result, out_dir)
    _plot_anchors(result, corrected_df, out_dir)
    _plot_bump_contamination(result, out_dir)
    _plot_amplitude_onset(result, out_dir)
    _plot_onset_timeline(result, out_dir)
    _plot_permanent_steps(result, out_dir)

    print(f"Cell: {cell_id}")
    print(f"RPT blocks: {result.n_blocks}")
    print(blocks_df.to_string(index=False))
    if result.onset:
        o = result.onset
        print(f"\nOnset: bump@{o.bump_onset_cycle}  knee@{o.knee_onset_cycle}  precedes={o.bump_precedes_knee}")
    if summary["diagnosis"]:
        print("\nDiagnosis:")
        for line in summary["diagnosis"]:
            print(f"  - {line}")
    print(f"\nWrote outputs to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
