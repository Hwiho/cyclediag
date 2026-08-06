"""Export RPT-anchored peak assign table (0.33C anchor → 0.5C routine)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.rpt_anchor import (  # noqa: E402
    RptAnchorConfig,
    build_rpt_anchor_assign_table,
    save_rpt_anchor_artifacts,
)
from cyclediag.features.peak_stepemd_join import discover_stepend_for_raw  # noqa: E402
from cyclediag.io.cycler_csv import load_cycler_csv  # noqa: E402
from cyclediag.io.cycle_protocol import build_protocol_exclusion  # noqa: E402
from cyclediag.io.stepemd_csv import load_stepemd_csv  # noqa: E402
from cyclediag.io.studio_map import studio_column_map  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RPT/capacheck anchor assign for routine 0.5C cycles",
    )
    parser.add_argument("--input", type=Path, required=True, help="Raw cycler CSV")
    parser.add_argument("--cell-id", type=str, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "example" / "docs" / "features")
    parser.add_argument("--stepemd", type=Path, default=None, help="StepEnd CSV (auto-discover if omitted)")
    parser.add_argument("--hard-radius", type=int, default=10, help="±life cycles for hard assign zone")
    parser.add_argument("--soft-radius", type=int, default=30)
    parser.add_argument("--shift-window", type=int, default=5, help="Routine cycles before RPT for ΔV")
    args = parser.parse_args()

    cfg = RptAnchorConfig(
        hard_radius=args.hard_radius,
        soft_radius=args.soft_radius,
        routine_shift_window=args.shift_window,
    )

    df = load_cycler_csv(str(args.input), column_map=studio_column_map())
    stepemd = args.stepemd or discover_stepend_for_raw(args.input)
    if stepemd is None or not Path(stepemd).exists():
        raise SystemExit("StepEnd CSV required for RPT/capacheck detection. Pass --stepemd.")

    step_df = load_stepemd_csv(stepemd)
    protocol = build_protocol_exclusion(step_df)

    assign_df, ckpts, shifts, meta = build_rpt_anchor_assign_table(
        df, protocol, config=cfg,
    )
    out_dir = args.out_dir / args.cell_id
    paths = save_rpt_anchor_artifacts(out_dir, args.cell_id, assign_df, ckpts, shifts, meta)

    n_hard = int((assign_df["assign_zone"] == "hard").sum()) if not assign_df.empty else 0
    n_missing = int((assign_df["evidence_type"] == "missing").sum()) if not assign_df.empty else 0
    print(f"Cell: {args.cell_id}")
    print(f"Checkpoints: {len(ckpts)}  routine cycles: {meta.get('n_routine_cycles', 0)}")
    print(f"Assign rows: {len(assign_df)}  hard-zone: {n_hard}  missing: {n_missing}")
    for label, path in paths.items():
        print(f"  {label}: {path}")


if __name__ == "__main__":
    main()
