"""CLI: extract cycle rest-V / resistance / capacity indicators → Excel (no GUI).

Examples
--------
# single raw CSV
python cyclediag/tools/export_cycle_indicators.py --input path/to/cell_raw.csv

# folder of *_raw.csv
python cyclediag/tools/export_cycle_indicators.py --input C:/data/cells --out-dir C:/tmp

# library
from cyclediag.features.cycle_indicators_export import export_cycle_indicators
export_cycle_indicators(r"C:\\data\\cell_raw.csv")
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.cycle_indicators_export import (  # noqa: E402
    export_cycle_indicators,
    summarize_cycle_indicators,
)
from cyclediag.features.diagnosis_export import export_diagnosis_bundle  # noqa: E402
from cyclediag.features.lges_extract import LgesExtractConfig  # noqa: E402
from cyclediag.io.cycler_csv import ColumnMap  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "Extract per-cycle indicators (EoC/EoD rest V, start resistance, "
            "SoHQ/CE, …) for offline inspection. No GUI."
        ),
    )
    p.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Raw CSV file or folder (*_raw.csv preferred)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: beside input)",
    )
    p.add_argument("--stem", type=str, default=None, help="Output filename stem")
    p.add_argument(
        "--cycles",
        type=str,
        default="",
        help="Optional cycle list, e.g. 1,2,5-10 (default: all)",
    )
    p.add_argument(
        "--column-map",
        choices=("studio", "pne"),
        default="studio",
        help="CSV column naming (studio=TotalCycle/Voltage/…)",
    )
    p.add_argument("--rest-labels", type=str, default="rest", help="Rest StepType labels")
    p.add_argument(
        "--rest-current-max",
        type=float,
        default=0.01,
        help="|I| threshold (A) to treat as rest when StepType ambiguous",
    )
    p.add_argument("--no-csv", action="store_true", help="Skip inspect CSV")
    p.add_argument("--no-xlsx", action="store_true", help="Skip Excel workbook")
    p.add_argument("--no-png", action="store_true", help="Skip overview PNG")
    p.add_argument(
        "--all-cycles",
        action="store_true",
        help="Include all raw cycles (default: tagged cycles only)",
    )
    p.add_argument(
        "--no-per-cell-png",
        action="store_true",
        help="Only write one overview PNG (skip per-cell PNGs when multi-cell)",
    )
    p.add_argument(
        "--full-report",
        action="store_true",
        help="Full diagnosis bundle: indicator screen CSV + SoHQ proxy/corr PNGs",
    )
    args = p.parse_args()

    cycles = _parse_cycles(args.cycles) if args.cycles.strip() else None
    cmap = ColumnMap.studio_default() if args.column_map == "studio" else ColumnMap.pne_default()
    cfg = LgesExtractConfig(
        rest_labels=args.rest_labels,
        rest_current_max=args.rest_current_max,
    )

    result = (
        export_diagnosis_bundle(
            args.input,
            args.out_dir,
            stem=args.stem,
            cycles=cycles,
            tagged_only=not args.all_cycles,
            write_csv=not args.no_csv,
            write_xlsx=not args.no_xlsx,
            write_screen_csv=True,
            write_png=not args.no_png,
            per_cell_png=not args.no_per_cell_png,
            column_map=cmap,
            config=cfg,
        )
        if args.full_report
        else export_cycle_indicators(
            args.input,
            args.out_dir,
            stem=args.stem,
            cycles=cycles,
            tagged_only=not args.all_cycles,
            write_csv=not args.no_csv,
            write_xlsx=not args.no_xlsx,
            write_png=not args.no_png,
            per_cell_png=not args.no_per_cell_png,
            column_map=cmap,
            config=cfg,
        )
    )

    print(summarize_cycle_indicators(result.features))
    if result.out_xlsx:
        print(f"xlsx: {result.out_xlsx}")
    if result.out_csv:
        print(f"csv:  {result.out_csv}")
    if getattr(result, "out_screen_csv", None):
        print(f"screen: {result.out_screen_csv}")
    for png in result.out_pngs:
        print(f"png:  {png}")
    if result.features.empty:
        print(
            "WARNING: empty table — check StepType/time columns and rest labels.",
            file=sys.stderr,
        )
        sys.exit(1)


def _parse_cycles(text: str) -> list[int]:
    """Parse '1,2,5-8' → [1,2,5,6,7,8]."""
    out: list[int] = []
    for part in text.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(token))
    return sorted(set(out))


if __name__ == "__main__":
    main()
