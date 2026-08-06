"""Diagnose PE/NE dominance by degradation-pattern segments.

Example:
  PYTHONPATH=. python3 cyclediag/tools/diagnose_electrode_segments.py \\
    --input example/fixtures/raw/set4_SJ900/M01Ch022_raw.csv \\
    --out-dir example/output/electrode_segments
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.api import extract_features  # noqa: E402
from cyclediag.diagnosis.electrode_side import (  # noqa: E402
    attach_electrode_side_diagnosis,
    segment_electrode_trajectory,
)
from cyclediag.diagnosis.engine import diagnose_feature_table  # noqa: E402
from cyclediag.diagnosis.halfcell.ocp_library import load_ocp_library  # noqa: E402
from cyclediag.features.enrich_assb import _group_consecutive  # noqa: E402
from cyclediag.features.lges_extract import LgesExtractConfig  # noqa: E402
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv  # noqa: E402


def _dcir_triplet_cycles(raw: pd.DataFrame, *, expected_pulse_current: float = 70.0) -> set[int]:
    """Cycles that belong to 3-SOC DCIR pulse blocks (not routine 0.5C).

    Routine 0.5C ≈ 0.5 * 1C pulse, so a loose |I| threshold falsely marks all
    routine cycles as pulses. Require |I| close to 1C and consecutive triplets.
    """
    thr = 0.75 * expected_pulse_current
    hot: list[int] = []
    for cyc, g in raw.groupby("cycle"):
        i = pd.to_numeric(g.get("current"), errors="coerce")
        if i is None or i.isna().all():
            continue
        if float(i.abs().max()) >= thr:
            hot.append(int(cyc))
    blocks = _group_consecutive(sorted(set(hot)), min_len=1)
    out: set[int] = set()
    for b in blocks:
        if len(b) >= 3:
            out.update(int(x) for x in b[:3])
        elif len(b) >= 1 and float(
            pd.to_numeric(raw.loc[raw["cycle"] == b[0], "current"], errors="coerce").abs().max()
        ) >= 0.9 * expected_pulse_current:
            out.update(int(x) for x in b)
    return out


def _capa_sample_cycles(raw: pd.DataFrame, *, step: int = 10) -> list[int]:
    """Prefer routine/capa cycles; skip DCIR SOC-step triplets only."""
    all_c = sorted(int(c) for c in raw["cycle"].dropna().unique())
    dcir = _dcir_triplet_cycles(raw)
    # capa often immediately before each DCIR block
    anchors: set[int] = set()
    for b in _group_consecutive(sorted(dcir), min_len=3):
        start = int(b[0])
        for d in (-2, -1):
            c = start + d
            if c in set(all_c) and c not in dcir:
                anchors.add(c)
    milestones = {2, 3, 20, 50, 80, 100, 150, 200, 250, 280, 300, 350, 400, 450, 500, 550, 560}
    grid = [
        c for c in all_c
        if c not in dcir and (c % step == 0 or c in anchors or c in milestones or c <= 5)
    ]
    non_dcir = [c for c in all_c if c not in dcir]
    grid = sorted(set(grid) | set(non_dcir[:3]) | set(non_dcir[-5:]) | anchors)
    return grid


def _side_ko(dom: str) -> str:
    return {
        "PE": "양극(PE) 지배",
        "NE": "음극(NE) 지배",
        "mixed": "양·음극 혼합(근소)",
        "shared": "셀 공통/공유 모드",
        "unknown": "판정 불가",
    }.get(dom, dom)


def _build_report(cell_id: str, feats: pd.DataFrame, segs: pd.DataFrame, lib_meta: dict) -> str:
    lines = [
        f"# 열화 구간별 양·음극 가설 진단 — {cell_id}",
        "",
        f"- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)",
        f"- OCP library: anode={lib_meta.get('n_anode_curves')} cathode={lib_meta.get('n_cathode_curves')} aged={lib_meta.get('aged_data')}",
        f"- 분석 포인트: {len(feats)} cycles sampled; 세그먼트는 SoHQ≥50 capa-like",
        "",
        "## 구간 요약 (패턴·양음극 지배 전환)",
        "",
    ]
    if segs.empty:
        lines.append("_세그먼트 없음_")
        return "\n".join(lines)

    for _, s in segs.iterrows():
        pe, ne = s["PE_side_score_mean"], s["NE_side_score_mean"]
        sohq0, sohq1 = s.get("SoHQ_start"), s.get("SoHQ_end")
        sohq_txt = (
            f"{sohq0:.1f}% → {sohq1:.1f}%"
            if sohq0 is not None and sohq1 is not None and np.isfinite(sohq0) and np.isfinite(sohq1)
            else "n/a"
        )
        rel = s.get("relative_dominant") or ("PE" if pe >= ne else "NE")
        winner = "양극(PE)" if rel == "PE" else "음극(NE)"
        strength = "명확" if float(s["dominance_margin_mean"]) >= 0.08 else (
            "약함/근소" if float(s["dominance_margin_mean"]) < 0.04 else "중간"
        )
        knee_tag = " · knee 포함" if s.get("crosses_knee") else ""
        lines.append(
            f"### Seg {int(s['segment'])}: cycle {int(s['cycle_start'])}–{int(s['cycle_end'])} · {_side_ko(str(s['dominant_electrode']))}{knee_tag}"
        )
        lines.append(f"- SoHQ: {sohq_txt} ({int(s['n_points'])} points)")
        lines.append(
            f"- 점수: PE={pe:.2f} / NE={ne:.2f} / shared={s['shared_side_score_mean']:.2f} "
            f"(Δ={s['dominance_margin_mean']:.2f}, conf={s['electrode_confidence_mean']:.2f})"
        )
        lines.append(f"- **이 구간 상대 지배: {winner}** (강도: {strength}, 가설)")
        lines.append(
            f"- 모드: PE=`{s.get('PE_top_modes')}` · NE=`{s.get('NE_top_modes')}` · shared=`{s.get('shared_top_modes')}`"
        )
        if s.get("LAM_PE_mean") is not None and np.isfinite(s["LAM_PE_mean"]):
            cl = s.get("contact_loss_mean")
            lli = s.get("LLI_mean")
            lines.append(
                f"- pattern: LAM_PE={s['LAM_PE_mean']:.2f}, "
                f"contact_loss={float(cl):.2f}, LLI={float(lli) if lli is not None else float('nan'):.2f}"
            )
        lines.append("")

    # life-phase rollup for quick read
    lines.append("## 수명 단계 롤업")
    lines.append("")
    show = feats.sort_values("cycle")
    if "SoHQ" in show.columns:
        show = show[pd.to_numeric(show["SoHQ"], errors="coerce") >= 50].copy()
    if not show.empty:
        pe = pd.to_numeric(show["PE_side_score"], errors="coerce")
        ne = pd.to_numeric(show["NE_side_score"], errors="coerce")
        show = show.assign(_d=pe - ne)
        knee = float(show["knee_cycle_bw"].dropna().iloc[0]) if "knee_cycle_bw" in show and show["knee_cycle_bw"].notna().any() else None
        phases = []
        if knee and np.isfinite(knee):
            phases = [
                ("early→pre-knee", show[show["cycle"] < knee]),
                ("post-knee→EOL", show[show["cycle"] >= knee]),
            ]
        else:
            n = len(show)
            phases = [
                ("early (1/3)", show.iloc[: max(1, n // 3)]),
                ("mid (1/3)", show.iloc[max(1, n // 3): max(2, 2 * n // 3)]),
                ("late (1/3)", show.iloc[max(2, 2 * n // 3):]),
            ]
        for name, ph in phases:
            if ph.empty:
                continue
            pe_m = float(np.nanmean(pd.to_numeric(ph["PE_side_score"], errors="coerce")))
            ne_m = float(np.nanmean(pd.to_numeric(ph["NE_side_score"], errors="coerce")))
            rel = "양극(PE)" if pe_m >= ne_m else "음극(NE)"
            c0, c1 = int(ph["cycle"].iloc[0]), int(ph["cycle"].iloc[-1])
            lines.append(
                f"- **{name}** cyc {c0}–{c1}: PE={pe_m:.2f} NE={ne_m:.2f} → **{rel}** "
                f"(SoHQ {float(ph['SoHQ'].iloc[0]):.0f}→{float(ph['SoHQ'].iloc[-1]):.0f}%)"
            )
        lines.append("")

    lines.append("## 사이클 궤적 (용량 사이클)")
    lines.append("")
    lines.append("| cycle | SoHQ | lean | PE | NE | Δ | LAM_PE | contact | note |")
    lines.append("|------:|-----:|:-----|---:|---:|--:|-------:|--------:|:-----|")
    for _, r in show.iterrows():
        pe_v = float(r.get("PE_side_score") or 0)
        ne_v = float(r.get("NE_side_score") or 0)
        dlt = pe_v - ne_v
        lean = "PE" if dlt >= 0.02 else ("NE" if dlt <= -0.02 else "~")
        note = str(r.get("electrode_narrative") or "")[:50].replace("|", "/")
        lines.append(
            f"| {int(r['cycle'])} | {float(r.get('SoHQ') or 0):.1f} | {lean} | "
            f"{pe_v:.2f} | {ne_v:.2f} | {dlt:+.2f} | "
            f"{float(r.get('LAM_PE_pattern_score') or 0):.2f} | {float(r.get('contact_loss_score') or 0):.2f} | {note} |"
        )
    lines.append("")
    if "knee_cycle_bw" in feats.columns and feats["knee_cycle_bw"].notna().any():
        knee = float(feats["knee_cycle_bw"].dropna().iloc[0])
        fade_b = feats["fade_exponent_b"].dropna().iloc[0] if "fade_exponent_b" in feats.columns else None
        lines.append(f"- Cell fade: knee≈{knee:.0f}, fade_exponent_b={fade_b}")
    lines.append("")
    lines.append(
        "> ASSB Si-rich: 관측 피크≈PE; `contact_loss`→NE(기계적 접촉) 가설. "
        "절대 LAM%는 aged 하프셀 전까지 보고하지 않음. lean은 PE−NE 상대 비교."
    )
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Segmented PE/NE electrode-side diagnosis")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, default=Path("example/output/electrode_segments"))
    p.add_argument("--halfcell-dir", type=Path, default=None)
    p.add_argument("--cell-id", type=str, default=None)
    p.add_argument("--step", type=int, default=10, help="Routine cycle sampling step")
    args = p.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    cell_id = args.cell_id or args.input.stem.replace("_raw", "")

    raw = load_cycler_csv(str(args.input), column_map=ColumnMap.studio_default())
    cycles = _capa_sample_cycles(raw, step=args.step)
    lib = load_ocp_library(args.halfcell_dir)

    cfg = LgesExtractConfig(
        cell_id=cell_id,
        with_diagnosis=False,
        enrich_assb=True,
        auto_baseline=True,
    )
    feats = extract_features(
        args.input,
        cycles=cycles,
        column_map=ColumnMap.studio_default(),
        config=cfg,
    )
    feats = diagnose_feature_table(feats, baseline_cycle=None, with_electrode_side=False)
    bl = None
    if "SoHQ" in feats.columns:
        cand = feats.sort_values("cycle")
        cand = cand.loc[pd.to_numeric(cand["SoHQ"], errors="coerce") >= 95]
        if not cand.empty:
            bl = int(cand.iloc[0]["cycle"])
    feats = attach_electrode_side_diagnosis(feats, baseline_cycle=bl, ocp_library=lib)
    segs = segment_electrode_trajectory(feats)

    keep = [c for c in [
        "cycle", "SoHQ", "CE",
        "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
        "interface_R_score", "solid_diffusion_score",
        "PE_side_score", "NE_side_score", "shared_side_score",
        "dominant_electrode", "dominance_margin", "electrode_confidence",
        "PE_top_modes", "NE_top_modes", "shared_top_modes",
        "electrode_narrative", "fade_exponent_b", "knee_cycle_bw",
        "eta_argmax_SOC", "mech_vs_chem_ratio", "PER",
    ] if c in feats.columns]
    traj_path = out_dir / f"{cell_id}_electrode_trajectory.csv"
    feats[keep].sort_values("cycle").to_csv(traj_path, index=False)
    seg_path = out_dir / f"{cell_id}_electrode_segments.csv"
    segs.to_csv(seg_path, index=False)

    report = _build_report(cell_id, feats, segs, lib.meta)
    report_path = out_dir / f"{cell_id}_electrode_segments_report.md"
    report_path.write_text(report, encoding="utf-8")
    (out_dir / f"{cell_id}_segments_meta.json").write_text(
        json.dumps({
            "cell_id": cell_id,
            "n_cycles_sampled": len(cycles),
            "n_feature_rows": len(feats),
            "n_segments": int(len(segs)),
            "baseline_cycle": bl,
            "ocp_meta": {k: v for k, v in lib.meta.items() if k != "manifest"},
        }, indent=2),
        encoding="utf-8",
    )
    print(report)
    print(f"wrote {traj_path}")
    print(f"wrote {seg_path}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
