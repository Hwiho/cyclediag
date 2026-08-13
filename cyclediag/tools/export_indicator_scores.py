"""Export the indicator scoring track (not causal diagnosis).

Example::

    python -m cyclediag.tools.export_indicator_scores \\
        example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv \\
        --out /tmp/ch22_indicator_scores

Writes:
  - cycle_scores.csv          per-cycle rollup (routine-only by default)
  - cycle_contributions.csv   per-(cycle, family) |z|
  - indicator_summary.csv     per-indicator scores, ranked
  - top_indicators.csv        shortlist
  - meta.json                 scoring metadata (no mode labels)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cyclediag.api import extract_features, score_dataframe
from cyclediag.features.lges_extract import LgesExtractConfig
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", type=Path, help="cycler raw CSV")
    p.add_argument("--out", type=Path, required=True, help="output directory")
    p.add_argument("--cell-id", default=None)
    p.add_argument(
        "--include-non-routine",
        action="store_true",
        help="score all cycles (debug). Default is routine-only.",
    )
    p.add_argument(
        "--with-diagnosis",
        action="store_true",
        help="also run the separate causal diagnosis track on extract "
             "(LLI/LAM pattern scores). Off by default.",
    )
    p.add_argument("--top-n", type=int, default=15)
    args = p.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    cmap = ColumnMap.studio_default()
    cfg = LgesExtractConfig(
        cell_id=args.cell_id or args.csv.stem,
        # Causal track is opt-in; default export is indicator scores only.
        with_diagnosis=bool(args.with_diagnosis),
    )
    # Pass the path (not a preloaded frame) so column normalization stays single-pass.
    feats = extract_features(args.csv, column_map=cmap, config=cfg)
    raw = load_cycler_csv(str(args.csv), column_map=cmap)
    result = score_dataframe(
        feats,
        raw_df=raw,
        routine_only=not args.include_non_routine,
        top_n=args.top_n,
    )

    result["cycle_scores"].to_csv(args.out / "cycle_scores.csv", index=False)
    result["cycle_contributions"].to_csv(args.out / "cycle_contributions.csv", index=False)
    result["indicator_summary"].to_csv(args.out / "indicator_summary.csv", index=False)
    result["top_indicators"].to_csv(args.out / "top_indicators.csv", index=False)
    (args.out / "meta.json").write_text(
        json.dumps(result["meta"], indent=2, default=str), encoding="utf-8",
    )
    print(f"wrote indicator scores -> {args.out}")
    print(f"  score_layer={result['score_layer']}  causal_track={result['causal_track']}")
    print(f"  scored_rows={result['meta'].get('n_scored_rows')}  "
          f"families={result['meta'].get('n_families')}")
    if not result["top_indicators"].empty:
        print("  top indicators:")
        for _, r in result["top_indicators"].head(args.top_n).iterrows():
            print(f"    {r['indicator_score']:.3f}  {r['feature']}  ({r['family']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
