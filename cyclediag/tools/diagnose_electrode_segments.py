"""Diagnose PE/NE dominance by degradation-pattern segments.

Dual-track protocol awareness:
- Routine 0.5C → continuous fade / lean / segment trajectory
- C/3 (~0.33C) RPT → capacity anchors (mid-life SoHQ bumps are RPT, not noise)
- DCIR 1C pulse → resistance / η features only

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
from cyclediag.diagnosis.validation_metrics import summarize_validation  # noqa: E402
from cyclediag.features.cycle_roles import (  # noqa: E402
    attach_cycle_roles,
    classify_cycle_currents,
    routine_mask,
    summarize_rpt_anchors,
)
from cyclediag.features.enrich_assb import _group_consecutive  # noqa: E402
from cyclediag.features.lges_extract import LgesExtractConfig  # noqa: E402
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv  # noqa: E402


def _dcir_triplet_cycles(raw: pd.DataFrame, *, expected_pulse_current: float = 70.0) -> set[int]:
    """Cycles that belong to 3-SOC DCIR pulse blocks (not routine 0.5C)."""
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
    """Sample routine 0.5C densely; keep C/3 RPT anchors; include DCIR pulses for R features.

    Fade/lean/segments later filter to routine_05c only. DCIR must still be extracted
    so ohmic/ct growth can forward-fill onto routine cycles.
    """
    all_c = sorted(int(c) for c in raw["cycle"].dropna().unique())
    roles = classify_cycle_currents(raw).set_index("cycle")
    dcir = _dcir_triplet_cycles(raw)
    rpt = set(
        int(c) for c in roles.index
        if str(roles.loc[c, "cycle_role"]) == "rpt_c3"
    )
    routine = set(
        int(c) for c in roles.index
        if str(roles.loc[c, "cycle_role"]) == "routine_05c"
    )

    anchors: set[int] = set(rpt)
    for b in _group_consecutive(sorted(dcir), min_len=3):
        start = int(b[0])
        for d in (-2, -1):
            c = start + d
            if c in set(all_c) and c not in dcir:
                anchors.add(c)
    milestones = {2, 3, 20, 50, 80, 100, 150, 200, 250, 280, 300, 350, 400, 450, 500, 550, 560}
    grid = [
        c for c in all_c
        if c not in dcir and c in routine and (
            c % step == 0 or c in anchors or c in milestones or c <= 5
        )
    ]
    rout_sorted = [c for c in all_c if c in routine]
    # Include DCIR pulse triplets so enrich can stamp R_* and forward-fill
    grid = sorted(
        set(grid) | set(rpt) | set(dcir) | set(rout_sorted[:3]) | set(rout_sorted[-5:]) | anchors
    )
    return grid


def _side_ko(dom: str) -> str:
    return {
        "PE": "양극(PE) 가설 우위",
        "NE": "음극(NE) 가설 우위 (Si co-sign)",
        "contact_stack": "접촉/스택 저항 패턴 우위",
        "contact_or_NE": "접촉·NE 쪽 lean",
        "mixed": "혼합/근소",
        "shared": "셀 공통/공유 모드",
        "unknown": "판정 불가",
    }.get(dom, dom)


def _build_report(
    cell_id: str,
    feats: pd.DataFrame,
    segs: pd.DataFrame,
    lib_meta: dict,
    rpt_anchors: pd.DataFrame,
) -> str:
    n_rout = int(routine_mask(feats).sum()) if "cycle_role" in feats.columns else len(feats)
    n_rpt = int((feats.get("cycle_role") == "rpt_c3").sum()) if "cycle_role" in feats.columns else 0
    lines = [
        f"# 열화 구간별 전극 가설 진단 v1.2 — {cell_id}",
        "",
        f"- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)",
        f"- Methodology: electrode_side_v1_2 · FC-OCP peak Δhits · contact_stack vs NE(Si co-sign)",
        f"- Protocol dual-track: routine 0.5C 궤적 + C/3 RPT 앵커 (중간 SoHQ bump = RPT, 노이즈 아님)",
        f"- OCP library: anode={lib_meta.get('n_anode_curves')} cathode={lib_meta.get('n_cathode_curves')} aged={lib_meta.get('aged_data')}",
        f"- 분석 포인트: {len(feats)} cycles (routine={n_rout}, rpt_c3={n_rpt}); 세그먼트는 routine only · SoHQ≥50",
        "",
        "## 구간 요약 (routine 0.5C)",
        "",
    ]
    if segs.empty:
        lines.append("_세그먼트 없음_")
    else:
        for _, s in segs.iterrows():
            pe = s["PE_side_score_mean"]
            ne = s.get("NE_side_score_mean", 0) or 0
            cl = s.get("contact_stack_score_mean", s.get("contact_loss_mean", 0)) or 0
            sohq0, sohq1 = s.get("SoHQ_start"), s.get("SoHQ_end")
            sohq_txt = (
                f"{sohq0:.1f}% → {sohq1:.1f}%"
                if sohq0 is not None and sohq1 is not None and np.isfinite(sohq0) and np.isfinite(sohq1)
                else "n/a"
            )
            rel = str(s.get("relative_dominant") or s.get("dominant_electrode"))
            lines.append(
                f"### Seg {int(s['segment'])}: cycle {int(s['cycle_start'])}–{int(s['cycle_end'])} · {_side_ko(str(s['dominant_electrode']))}"
            )
            lines.append(f"- SoHQ(routine): {sohq_txt} ({int(s['n_points'])} points)")
            lines.append(
                f"- 점수: PE={pe:.2f} / contact_stack={float(cl):.2f} / NE_hyp={float(ne):.2f} / "
                f"shared={s['shared_side_score_mean']:.2f} (conf={s['electrode_confidence_mean']:.2f})"
            )
            lines.append(f"- **상대 lean 라벨: {_side_ko(rel)}** · si_cosign≈{float(s.get('si_cosign_mean') or 0):.2f}")
            lines.append(
                f"- 모드: PE=`{s.get('PE_top_modes')}` · contact=`{s.get('NE_top_modes')}` · shared=`{s.get('shared_top_modes')}`"
            )
            if s.get("LAM_PE_mean") is not None and np.isfinite(s["LAM_PE_mean"]):
                lines.append(
                    f"- pattern: LAM_PE={s['LAM_PE_mean']:.2f}, "
                    f"contact_loss={float(s.get('contact_loss_mean') or 0):.2f}, "
                    f"LLI={float(s.get('LLI_mean') or 0):.2f}"
                )
            lines.append("")

    lines.append("## C/3 RPT 앵커 (이중 트랙)")
    lines.append("")
    lines.append(
        "중간 궤적의 SoHQ 상승 스파이크는 **C/3(~0.33C) RPT 용량**입니다. "
        "rate가 낮아 분극이 작아 보이므로 0.5C routine보다 높게 찍히는 것이 정상입니다. "
        "fade/lean/세그먼트에는 넣지 않고 RCF·η·열역학 용량 트랙으로만 씁니다."
    )
    lines.append("")
    if rpt_anchors is None or rpt_anchors.empty:
        lines.append("_RPT 앵커 없음_")
    else:
        lines.append("| cycle | SoHQ_C/3 | prev routine | SoHQ_0.5C | Δ(RPT−routine) |")
        lines.append("|------:|---------:|-------------:|----------:|---------------:|")
        for _, r in rpt_anchors.iterrows():
            gap = r.get("SoHQ_gap_vs_prev_routine")
            gap_s = f"{float(gap):+.1f}" if gap is not None and np.isfinite(gap) else "n/a"
            prev_c = r.get("cycle_routine_prev")
            prev_s = str(int(prev_c)) if prev_c is not None and np.isfinite(prev_c) else "—"
            sohq_p = r.get("SoHQ_routine_prev")
            sohq_ps = f"{float(sohq_p):.1f}" if sohq_p is not None and np.isfinite(sohq_p) else "n/a"
            sohq_r = r.get("SoHQ_rpt_c3")
            sohq_rs = f"{float(sohq_r):.1f}" if sohq_r is not None and np.isfinite(sohq_r) else "n/a"
            lines.append(
                f"| {int(r['cycle'])} | {sohq_rs} | {prev_s} | {sohq_ps} | {gap_s} |"
            )
    lines.append("")

    lines.append("## 수명 단계 롤업 (routine only)")
    lines.append("")
    show = feats.sort_values("cycle")
    if "cycle_role" in show.columns:
        show = show.loc[routine_mask(show)].copy()
    if "SoHQ" in show.columns:
        show = show[pd.to_numeric(show["SoHQ"], errors="coerce") >= 50].copy()
    if not show.empty:
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
            cl_m = float(np.nanmean(pd.to_numeric(ph.get("contact_stack_score"), errors="coerce")))
            ne_m = float(np.nanmean(pd.to_numeric(ph["NE_side_score"], errors="coerce")))
            vote = ph["dominant_electrode"].value_counts()
            top = str(vote.index[0]) if len(vote) else "mixed"
            c0, c1 = int(ph["cycle"].iloc[0]), int(ph["cycle"].iloc[-1])
            lines.append(
                f"- **{name}** cyc {c0}–{c1}: PE={pe_m:.2f} contact={cl_m:.2f} NE_hyp={ne_m:.2f} "
                f"→ majority **{_side_ko(top)}** (SoHQ {float(ph['SoHQ'].iloc[0]):.0f}→{float(ph['SoHQ'].iloc[-1]):.0f}%)"
            )
        lines.append("")

    lines.append("## 사이클 궤적")
    lines.append("")
    lines.append("| cycle | role | SoHQ | dominant | PE | contact | NE_hyp | LAM_PE | contact_loss | note |")
    lines.append("|------:|:-----|-----:|:---------|---:|--------:|-------:|-------:|-------------:|:-----|")
    # Show routine + RPT for dual-track visibility
    show_all = feats.sort_values("cycle")
    if "SoHQ" in show_all.columns:
        show_all = show_all[pd.to_numeric(show_all["SoHQ"], errors="coerce") >= 50].copy()
    for _, r in show_all.iterrows():
        role = str(r.get("cycle_role") or "")
        if role not in ("routine_05c", "rpt_c3", ""):
            continue
        note = str(r.get("electrode_narrative") or "")[:40].replace("|", "/")
        if role == "rpt_c3":
            note = "C/3 RPT anchor (not fade spike)"
        cl = r.get("contact_stack_score")
        if cl is None or (isinstance(cl, float) and np.isnan(cl)):
            cl = r.get("contact_loss_score") or 0
        lines.append(
            f"| {int(r['cycle'])} | {role or '—'} | {float(r.get('SoHQ') or 0):.1f} | "
            f"{r.get('dominant_electrode')} | "
            f"{float(r.get('PE_side_score') or 0):.2f} | {float(cl):.2f} | "
            f"{float(r.get('NE_side_score') or 0):.2f} | "
            f"{float(r.get('LAM_PE_pattern_score') or 0):.2f} | {float(r.get('contact_loss_score') or 0):.2f} | {note} |"
        )
    lines.append("")
    lines.append(
        "> v1.2: mid-life SoHQ bumps = **C/3 RPT**. "
        "`contact_stack` = 전극 미분해 접촉/스택 저항. "
        "`NE`는 Si co-sign이 있을 때만. 절대 LAM% 금지."
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
    # Ensure roles even if enrich already attached (idempotent merge)
    if "cycle_role" not in feats.columns:
        feats, _ = attach_cycle_roles(feats, raw)
    else:
        feats, _ = attach_cycle_roles(feats, raw)

    feats = diagnose_feature_table(feats, baseline_cycle=None, with_electrode_side=False)
    bl = None
    if "SoHQ" in feats.columns:
        cand = feats.sort_values("cycle")
        if "cycle_role" in cand.columns:
            cand = cand.loc[routine_mask(cand)]
        cand = cand.loc[pd.to_numeric(cand["SoHQ"], errors="coerce") >= 95]
        if not cand.empty:
            bl = int(cand.iloc[0]["cycle"])
    feats = attach_electrode_side_diagnosis(feats, baseline_cycle=bl, ocp_library=lib)
    segs = segment_electrode_trajectory(feats, routine_only=True)
    rpt_anchors = summarize_rpt_anchors(feats)

    keep = [c for c in [
        "cycle", "cycle_role", "C_rate_med_est", "I_abs_med_cc",
        "SoHQ", "SoHQ_routine", "SoHQ_rpt_c3", "CE",
        "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
        "interface_R_score", "solid_diffusion_score",
        "PE_side_score", "NE_side_score", "contact_stack_score", "shared_side_score",
        "dominant_electrode", "dominance_margin", "electrode_confidence",
        "PE_top_modes", "NE_top_modes", "shared_top_modes",
        "pe_peak_hits", "pe_peak_hits_delta", "si_cosign",
        "electrode_narrative", "fade_exponent_b", "knee_cycle_bw",
        "eta_argmax_SOC", "mech_vs_chem_ratio", "PER", "LAM_curve_proxy", "RCF",
    ] if c in feats.columns]
    traj_path = out_dir / f"{cell_id}_electrode_trajectory.csv"
    feats[keep].sort_values("cycle").to_csv(traj_path, index=False)
    seg_path = out_dir / f"{cell_id}_electrode_segments.csv"
    segs.to_csv(seg_path, index=False)
    rpt_path = out_dir / f"{cell_id}_rpt_c3_anchors.csv"
    rpt_anchors.to_csv(rpt_path, index=False)

    val = summarize_validation(feats)
    val["protocol"] = {
        "routine_n": int(routine_mask(feats).sum()) if "cycle_role" in feats.columns else None,
        "rpt_c3_n": int((feats["cycle_role"] == "rpt_c3").sum()) if "cycle_role" in feats.columns else None,
        "rpt_c3_cycles": rpt_anchors["cycle"].astype(int).tolist() if not rpt_anchors.empty else [],
    }
    (out_dir / f"{cell_id}_validation.json").write_text(
        json.dumps(val, indent=2), encoding="utf-8",
    )

    report = _build_report(cell_id, feats, segs, lib.meta, rpt_anchors)
    report_path = out_dir / f"{cell_id}_electrode_segments_report.md"
    report_path.write_text(report, encoding="utf-8")
    (out_dir / f"{cell_id}_segments_meta.json").write_text(
        json.dumps({
            "cell_id": cell_id,
            "version": "electrode_side_v1_2",
            "n_cycles_sampled": len(cycles),
            "n_feature_rows": len(feats),
            "n_segments": int(len(segs)),
            "baseline_cycle": bl,
            "baseline_note": "early routine_05c with SoHQ>=95",
            "rpt_c3_cycles": rpt_anchors["cycle"].astype(int).tolist() if not rpt_anchors.empty else [],
            "ocp_meta": {k: v for k, v in lib.meta.items() if k != "manifest"},
        }, indent=2),
        encoding="utf-8",
    )
    print(report)
    print(f"wrote {traj_path}")
    print(f"wrote {seg_path}")
    print(f"wrote {rpt_path}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
