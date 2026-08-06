"""Generate RESULTS.md summary for a cell peak export folder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.peak_results_report import write_results_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize peak analysis outputs → RESULTS.md")
    parser.add_argument("--cell-dir", type=Path, required=True, help="e.g. example/docs/features/M01Ch022")
    args = parser.parse_args()
    out = write_results_report(args.cell_dir)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
