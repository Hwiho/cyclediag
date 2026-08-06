"""CLI: electrode-side (PE/NE) hypothesis diagnosis for selected cycles.

Example:
  PYTHONPATH=. python cyclediag/tools/diagnose_electrode_sides.py \\
    --input example/fixtures/raw/set4_SJ900/M01Ch022_raw.csv \\
    --cycles 50,280,560 --out-dir example/output/electrode_side
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.api import extract_features  # noqa: E402
from cyclediag.diagnosis.electrode_side import (  # noqa: E402
    attach_electrode_side_diagnosis,
    diagnose_electrode_side,
)
from cyclediag.diagnosis.engine import diagnose_feature_table  # noqa: E402
from cyclediag.diagnosis.halfcell.ocp_library import (  # noqa: E402
    load_ocp_library,
    synthesize_fullcell_ocp,
)
from cyclediag.features.lges_extract import LgesExtractConfig  # noqa: E402
from cyclediag.io.cycler_csv import ColumnMap  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="PE/NE electrode-side hypothesis diagnosis")
    p.add_argument("--input", type=Path, required=True, help="Full-cell raw CSV")
    p.add_argument("--cycles", type=str, default="", help="Comma-separated cycles (default: auto sample)")
    p.add_argument("--out-dir", type=Path, default=Path("example/output/electrode_side"))
    p.add_argument("--halfcell-dir", type=Path, default=None)
    p.add_argument("--cell-id", type=str, default=None)
    args = p.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    cell_id = args.cell_id or args.input.stem.replace("_raw", "")

    lib = load_ocp_library(args.halfcell_dir)
    synth = synthesize_fullcell_ocp(lib)
    (out_dir / f"{cell_id}_ocp_library_meta.json").write_text(
        json.dumps({
            "meta": lib.meta,
            "cathode_peaks_charge": lib.cathode_peak_voltages(leg="charge"),
            "cathode_peaks_discharge": lib.cathode_peak_voltages(leg="discharge"),
            "anode_peaks_discharge": lib.anode_peak_voltages(leg="discharge"),
            "synth_fullcell_ocp": (
                None if synth is None else {
                    "v_min": synth["v_min"], "v_max": synth["v_max"],
                    "anode_cycle": synth["anode_cycle"],
                    "note": synth["note"],
                }
            ),
        }, indent=2),
        encoding="utf-8",
    )

    raw_cycles = None
    if args.cycles.strip():
        raw_cycles = [int(x) for x in args.cycles.split(",") if x.strip()]
    else:
        # light default sample — prefer capa-like cycles (skip DCIR SOC steps)
        from cyclediag.io.cycler_csv import load_cycler_csv
        raw = load_cycler_csv(str(args.input), column_map=ColumnMap.studio_default())
        all_c = sorted(int(c) for c in raw["cycle"].dropna().unique())
        # early / mid / late + near RPT anchors (capa often N-1 / N-2 before DCIR block)
        picks = set(all_c[:3] + all_c[len(all_c)//2:len(all_c)//2+2] + all_c[-3:])
        for b in (4, 109, 214, 319, 424, 529):
            for d in (-2, -1):
                if b + d in set(all_c):
                    picks.add(b + d)
        raw_cycles = sorted(picks)

    cfg = LgesExtractConfig(
        cell_id=cell_id,
        with_diagnosis=False,
        enrich_assb=True,
        auto_baseline=True,
    )
    feats = extract_features(
        args.input,
        cycles=raw_cycles,
        column_map=ColumnMap.studio_default(),
        config=cfg,
    )
    # diagnose without double electrode attach first, then attach with library
    feats = diagnose_feature_table(
        feats, baseline_cycle=None, with_electrode_side=False,
    )
    # use enrich auto baseline if present via first capa-like SoHQ~100
    bl = None
    if "SoHQ" in feats.columns:
        early = feats.sort_values("cycle")
        cand = early.loc[pd.to_numeric(early["SoHQ"], errors="coerce") >= 95]
        if not cand.empty:
            bl = int(cand.iloc[0]["cycle"])
    feats = attach_electrode_side_diagnosis(
        feats, baseline_cycle=bl, ocp_library=lib,
    )

    out_csv = out_dir / f"{cell_id}_electrode_side.csv"
    keep = [c for c in [
        "cycle", "SoHQ", "CE",
        "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
        "interface_R_score", "solid_diffusion_score", "SE_decomposition_score",
        "PE_side_score", "NE_side_score", "shared_side_score",
        "dominant_electrode", "dominance_margin", "electrode_confidence",
        "PE_top_modes", "NE_top_modes", "shared_top_modes",
        "PE_supporting", "NE_supporting", "pe_peak_hits",
        "electrode_diagnosis_level", "electrode_narrative",
        "eta_argmax_SOC", "eta_SOC50", "PER", "mech_vs_chem_ratio",
        "LAM_curve_proxy", "hyst_area_low", "hyst_area_high",
    ] if c in feats.columns]
    feats[keep].sort_values("cycle").to_csv(out_csv, index=False)

    # print concise report for key cycles
    report_cycles = raw_cycles
    if len(report_cycles) > 12:
        # highlight early / mid / late
        report_cycles = sorted({
            report_cycles[0], report_cycles[len(report_cycles)//4],
            report_cycles[len(report_cycles)//2], report_cycles[3*len(report_cycles)//4],
            report_cycles[-1],
        } | set(c for c in (50, 280, 400, 530, 560) if c in set(raw_cycles)))

    lines = [f"# Electrode-side hypothesis — {cell_id}", ""]
    lines.append(f"- OCP library: anode_curves={lib.meta.get('n_anode_curves')} "
                 f"cathode_curves={lib.meta.get('n_cathode_curves')} aged={lib.meta.get('aged_data')}")
    lines.append(f"- Level: **hypothesis_bol_ocp** (not aged-HC calibrated)")
    lines.append("")
    for cyc in sorted(report_cycles):
        row = feats.loc[feats["cycle"] == cyc]
        if row.empty:
            continue
        r = row.iloc[0]
        lines.append(f"## Cycle {cyc}")
        sohq = r.get("SoHQ")
        lines.append(f"- SoHQ: {float(sohq):.1f}%" if pd.notna(sohq) else "- SoHQ: n/a")
        lines.append(
            f"- Dominant: **{r.get('dominant_electrode')}** "
            f"(PE={float(r.get('PE_side_score') or 0):.2f}, "
            f"NE={float(r.get('NE_side_score') or 0):.2f}, "
            f"shared={float(r.get('shared_side_score') or 0):.2f}, "
            f"conf={float(r.get('electrode_confidence') or 0):.2f})"
        )
        lines.append(f"- PE modes: {r.get('PE_top_modes')}")
        lines.append(f"- NE modes: {r.get('NE_top_modes')}")
        lines.append(f"- Shared: {r.get('shared_top_modes')}")
        lines.append(f"- Note: {r.get('electrode_narrative')}")
        lines.append("")

    report_path = out_dir / f"{cell_id}_electrode_side_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {out_csv}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
