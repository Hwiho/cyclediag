"""Product-path set4 degradation brief — indicator scores first, causal second.

Example::

    python -m cyclediag.tools.export_set4_brief \\
        --fixtures example/fixtures/doe/DOE1/set4_SJ900 \\
        --out example/output/set4_brief
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cyclediag.analysis.lli_kinetic_split import classify_ocv_parallel_shift
from cyclediag.analysis.resistance_anchors import landmark_resistance_trend, resistance_anchor_table
from cyclediag.analysis.sohq_interval_compare import interval_feature_deltas, knee_split_summary
from cyclediag.api import extract_features, score_dataframe
from cyclediag.diagnosis.engine import diagnose_feature_table
from cyclediag.features.lges_extract import LgesExtractConfig
from cyclediag.io.cycler_csv import ColumnMap


CELLS = ("M01Ch022", "M01Ch024", "M01Ch025")


def _find_cell_csv(fixtures: Path, cell_id: str) -> Path | None:
    hits = list(fixtures.glob(f"**/{cell_id}_raw.csv")) + list(fixtures.glob(f"**/*{cell_id[-3:]}*raw.csv"))
    return hits[0] if hits else None


def _brief_cell(cell_id: str, csv_path: Path, out_dir: Path, *, with_causal: bool) -> dict:
    cfg = LgesExtractConfig(cell_id=cell_id, with_diagnosis=False)
    feats = extract_features(csv_path, config=cfg, column_map=ColumnMap.studio_default())
    scored = score_dataframe(feats, routine_only=True, top_n=15)

    cell_out = out_dir / cell_id
    cell_out.mkdir(parents=True, exist_ok=True)
    scored["indicator_summary"].to_csv(cell_out / "indicator_summary.csv", index=False)
    scored["top_indicators"].to_csv(cell_out / "top_indicators.csv", index=False)
    for layer, frame in scored.get("by_layer", {}).items():
        if frame is not None and not frame.empty:
            frame.to_csv(cell_out / f"layer_{layer}.csv", index=False)

    knee = knee_split_summary(feats)
    intervals = interval_feature_deltas(feats)
    if not intervals.empty:
        intervals.to_csv(cell_out / "sohq_interval_deltas.csv", index=False)
    r_anchor = resistance_anchor_table(feats)
    if not r_anchor.empty:
        r_anchor.to_csv(cell_out / "resistance_dcir_anchors.csv", index=False)
    r_trend = landmark_resistance_trend(feats, routine_only=True)
    if not r_trend.empty:
        r_trend.to_csv(cell_out / "resistance_landmark_trend.csv", index=False)
    lli_kin = classify_ocv_parallel_shift(feats)

    causal = {}
    if with_causal:
        diag = diagnose_feature_table(feats, routine_only=True)
        # last scored routine row mode snapshot
        scored_rows = diag[diag.get("diagnosis_scored_row", True) == True] if "diagnosis_scored_row" in diag.columns else diag
        if not scored_rows.empty:
            last = scored_rows.sort_values("cycle").iloc[-1]
            for col in diag.columns:
                if col.endswith("_pattern_score") and pd.notna(last.get(col)):
                    causal[col] = float(last[col])
        diag.to_csv(cell_out / "diagnosis_causal.csv", index=False)

    sohq = pd.to_numeric(feats["SoHQ"], errors="coerce") if "SoHQ" in feats.columns else None
    summary = {
        "cell_id": cell_id,
        "n_cycles_extracted": int(len(feats)),
        "n_scored_routine": int(scored["meta"].get("n_scored_rows", 0)),
        "sohq_start": float(sohq.dropna().iloc[0]) if sohq is not None and sohq.notna().any() else None,
        "sohq_end": float(sohq.dropna().iloc[-1]) if sohq is not None and sohq.notna().any() else None,
        "knee": knee,
        "lli_vs_kinetic": lli_kin,
        "top_mechanism_indicators": (
            scored["by_layer"]["mechanism"].head(10)[["feature", "indicator_score", "corr_health"]]
            .to_dict("records")
            if scored.get("by_layer") and not scored["by_layer"]["mechanism"].empty
            else []
        ),
        "causal_end_snapshot": causal,
        "score_layer": "indicator",
        "causal_track": "separate" if with_causal else "not_run",
    }
    (cell_out / "brief.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixtures", type=Path, default=Path("example/fixtures/doe/DOE1/set4_SJ900"))
    p.add_argument("--out", type=Path, default=Path("example/output/set4_brief"))
    p.add_argument("--with-causal", action="store_true", help="also run Track B diagnosis")
    p.add_argument("--cells", default=",".join(CELLS))
    args = p.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    briefs = []
    for cell_id in [c.strip() for c in args.cells.split(",") if c.strip()]:
        path = _find_cell_csv(args.fixtures, cell_id)
        if path is None:
            print(f"skip {cell_id}: raw csv not found under {args.fixtures}")
            continue
        print(f"=== {cell_id} ({path}) ===", flush=True)
        briefs.append(_brief_cell(cell_id, path, args.out, with_causal=args.with_causal))

    (args.out / "set4_brief.json").write_text(
        json.dumps(briefs, indent=2, default=str), encoding="utf-8",
    )
    # markdown index
    lines = ["# set4 degradation brief", "", "Track A = indicator scores (routine only). Track B = causal (opt-in).", ""]
    for b in briefs:
        lines.append(f"## {b['cell_id']}")
        lines.append(f"- SoHQ: {b.get('sohq_start')} → {b.get('sohq_end')}")
        lines.append(f"- scored routine rows: {b.get('n_scored_routine')}")
        lines.append(f"- knee: {b.get('knee')}")
        lines.append(f"- LLI vs kinetic: {b.get('lli_vs_kinetic', {}).get('label')}")
        lines.append("- top mechanism indicators:")
        for row in b.get("top_mechanism_indicators", [])[:8]:
            lines.append(f"  - {row['indicator_score']:.3f} `{row['feature']}` (r_health={row.get('corr_health')})")
        if b.get("causal_end_snapshot"):
            lines.append("- causal end snapshot:")
            for k, v in b["causal_end_snapshot"].items():
                lines.append(f"  - {k}: {v:.3f}")
        lines.append("")
    (args.out / "set4_brief.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out / 'set4_brief.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
