"""Train 0.33C→0.5C peak-overlap RF and export soft-map / collapse tables."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.peak_stepemd_join import discover_stepend_for_raw  # noqa: E402
from cyclediag.features.rpt_anchor import (  # noqa: E402
    RptAnchorConfig,
    build_rpt_anchor_assign_table,
)
from cyclediag.features.rpt_peak_overlap import (  # noqa: E402
    RptOverlapConfig,
    build_rpt_overlap_artifacts,
    plot_overlap_overlay,
)
from cyclediag.io.cycler_csv import load_cycler_csv  # noqa: E402
from cyclediag.io.cycle_protocol import build_protocol_exclusion  # noqa: E402
from cyclediag.io.stepemd_csv import load_stepemd_csv  # noqa: E402
from cyclediag.io.studio_map import studio_column_map  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ML soft-map: which 0.33C peaks overlap on 0.5C bumps",
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--cell-id", type=str, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "example" / "docs" / "features")
    parser.add_argument("--stepemd", type=Path, default=None)
    args = parser.parse_args()

    df = load_cycler_csv(str(args.input), column_map=studio_column_map())
    stepemd = args.stepemd or discover_stepend_for_raw(args.input)
    if stepemd is None or not Path(stepemd).exists():
        raise SystemExit("StepEnd CSV required. Pass --stepemd.")

    protocol = build_protocol_exclusion(load_stepemd_csv(stepemd))
    assign_df, ckpts, shifts, _meta = build_rpt_anchor_assign_table(
        df, protocol, config=RptAnchorConfig(),
    )
    del assign_df

    cfg = RptOverlapConfig()
    bundle, train_df, soft_df, links, collapses = build_rpt_overlap_artifacts(
        df, ckpts, shifts, protocol, config=cfg,
    )

    out = args.out_dir / args.cell_id
    out.mkdir(parents=True, exist_ok=True)
    model_dir = bundle.save(out / f"{args.cell_id}_rpt_overlap_model")
    train_df.to_csv(out / f"{args.cell_id}_rpt_overlap_train.csv", index=False, encoding="utf-8-sig")
    soft_df.to_csv(out / f"{args.cell_id}_rpt_overlap_soft.csv", index=False, encoding="utf-8-sig")
    links.to_csv(out / f"{args.cell_id}_rpt_overlap_links.csv", index=False, encoding="utf-8-sig")
    collapses.to_csv(
        out / f"{args.cell_id}_rpt_overlap_collapses.csv", index=False, encoding="utf-8-sig",
    )

    plot_dir = out / "plots_rpt_overlap"
    plot_dir.mkdir(exist_ok=True)
    for ckpt in ckpts:
        if ckpt.life_cycle < 100:
            continue
        for leg in ("charge", "discharge"):
            if not (ckpt.peaks.get(leg) or []):
                continue
            fig = plot_overlap_overlay(
                df, ckpt, soft_df, collapses, leg=leg, routine_cycle=ckpt.life_cycle, config=cfg,
            )
            p = plot_dir / f"{args.cell_id}_overlap_life{ckpt.life_cycle}_{leg}.png"
            fig.savefig(p, dpi=140, bbox_inches="tight")
            plt.close(fig)

    print(f"Cell: {args.cell_id}")
    print(f"Train rows: {len(train_df)}  soft edges: {len(soft_df)}  collapses: {len(collapses)}")
    print(f"Model: {model_dir}")
    if not collapses.empty:
        print(collapses[["life_cycle", "leg", "cand_V", "rpt_peak_ids", "best_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
