"""Run DOE2 arm compare: SJ900 dry vs SJ1300 dry (same cathode, different anode).

Usage (repo root):
  python -m cyclediag.tools.run_doe2_compare
  python -m cyclediag.tools.run_doe2_compare --out example/output/DOE2_compare --early-cycles 30
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="DOE2 SJ900 vs SJ1300 compare")
    p.add_argument("--fixtures-root", default="")
    p.add_argument("--out", default="example/output/DOE2_compare")
    p.add_argument("--early-cycles", type=int, default=30)
    p.add_argument("--no-diagnosis", action="store_true")
    p.add_argument("--no-plots", action="store_true")
    args = p.parse_args(argv)

    from cyclediag.analysis.doe_compare import DoeCompareConfig, run_doe_compare

    summary = run_doe_compare(
        DoeCompareConfig(
            doe_id="DOE2",
            fixtures_root=Path(args.fixtures_root) if args.fixtures_root else None,
            out_dir=Path(args.out),
            early_cycles=args.early_cycles,
            run_diagnosis=not args.no_diagnosis,
            write_plots=not args.no_plots,
        )
    )
    print(f"Wrote → {summary['out_dir']}")
    for line in summary.get("narrative", []):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
