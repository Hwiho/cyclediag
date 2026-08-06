#!/usr/bin/env python3
"""Compare DOE cathode arms (same anode): early params + degradation mechanisms.

Example (DOE3 S83S vs Bimodal):
  PYTHONPATH=. python3 cyclediag/tools/compare_doe_cathodes.py \\
    --arm A=S83S:example/fixtures/doe/DOE3/S83S \\
    --arm B=Bimodal:example/fixtures/doe/DOE3/Bimodal \\
    --out-dir example/output/doe3_cathode_compare
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.analysis.doe_cathode_compare import (  # noqa: E402
    arm_aggregate,
    compare_arms,
    early_window_summary,
    estimate_pulse_current_a,
    estimate_q_nominal_ah,
    late_window_summary,
    mechanism_delta,
    summarize_mechanism_contrast,
    top_differences,
)
from cyclediag.api import extract_features  # noqa: E402
from cyclediag.diagnosis.electrode_side import (  # noqa: E402
    attach_electrode_side_diagnosis,
    segment_electrode_trajectory,
)
from cyclediag.diagnosis.engine import diagnose_feature_table  # noqa: E402
from cyclediag.diagnosis.halfcell.ocp_library import load_ocp_library  # noqa: E402
from cyclediag.features.cycle_roles import attach_cycle_roles, routine_mask  # noqa: E402
from cyclediag.features.lges_extract import LgesExtractConfig  # noqa: E402
from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv  # noqa: E402
from cyclediag.tools.diagnose_electrode_segments import _capa_sample_cycles  # noqa: E402

C_A, C_B = "#C45C26", "#1F6F8B"
C_BG = "#FAF7F2"


def _setup_font() -> str:
    for path in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ):
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            name = font_manager.FontProperties(fname=path).get_name()
            mpl.rcParams["font.family"] = name
            mpl.rcParams["axes.unicode_minus"] = False
            return path
    return ""


FONT = _setup_font()


def fp(size=10, weight="normal"):
    if FONT:
        return font_manager.FontProperties(fname=FONT, size=size, weight=weight)
    return font_manager.FontProperties(size=size, weight=weight)


def parse_arm(spec: str) -> tuple[str, Path]:
    # Name:path
    if ":" not in spec:
        raise SystemExit(f"--arm needs Name:path, got {spec}")
    name, path = spec.split(":", 1)
    return name.strip(), Path(path.strip())


def list_raw_csvs(folder: Path) -> list[Path]:
    return sorted(folder.glob("*_raw.csv"))


def diagnose_one(
    path: Path,
    *,
    halfcell_dir: Path | None,
    step: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    raw = load_cycler_csv(str(path), column_map=ColumnMap.studio_default())
    q_nom = estimate_q_nominal_ah(raw)
    i_pulse = estimate_pulse_current_a(raw)
    cell_id = path.stem.replace("_raw", "")

    cycles = _capa_sample_cycles(
        raw, step=step, q_nominal_ah=q_nom, expected_pulse_current=float(i_pulse),
    )

    lib = load_ocp_library(halfcell_dir)
    cfg = LgesExtractConfig(
        cell_id=cell_id,
        with_diagnosis=False,
        enrich_assb=True,
        auto_baseline=True,
        expected_pulse_current=float(i_pulse),
    )
    feats = extract_features(
        path, cycles=cycles, column_map=ColumnMap.studio_default(), config=cfg,
    )
    feats, _ = attach_cycle_roles(feats, raw, q_nominal_ah=q_nom)
    feats = diagnose_feature_table(feats, baseline_cycle=None, with_electrode_side=False)
    bl = None
    if "SoHQ" in feats.columns:
        cand = feats.sort_values("cycle")
        cand = cand.loc[routine_mask(cand)]
        cand = cand.loc[pd.to_numeric(cand["SoHQ"], errors="coerce") >= 95]
        if not cand.empty:
            bl = int(cand.iloc[0]["cycle"])
    feats = attach_electrode_side_diagnosis(feats, baseline_cycle=bl, ocp_library=lib)
    segs = segment_electrode_trajectory(feats, routine_only=True)
    meta = {
        "cell_id": cell_id,
        "q_nominal_ah": q_nom,
        "expected_pulse_current": i_pulse,
        "baseline_cycle": bl,
        "n_cycles_raw": int(raw["cycle"].nunique()),
        "n_sampled": int(len(feats)),
        "role_counts": feats["cycle_role"].astype(str).value_counts().to_dict() if "cycle_role" in feats else {},
    }
    return feats, segs, meta


def cell_summary_row(arm: str, path: Path, feats: pd.DataFrame, meta: dict) -> dict:
    early = early_window_summary(feats)
    late = late_window_summary(feats)
    delta = mechanism_delta(early, late)
    row = {"arm": arm, "cell_id": meta["cell_id"], "path": str(path), **meta, **early, **late, **delta}
    # fade/knee from feats
    for k in ("fade_exponent_b", "knee_cycle_bw"):
        if k in feats.columns and feats[k].notna().any():
            row[k] = float(feats[k].dropna().iloc[0])
    return row


def wrap(fig, x, y, text, width=92, size=9, weight="normal"):
    lines = []
    for para in text.split("\n"):
        lines.extend(textwrap.wrap(para, width=width) or [""]) if para.strip() else lines.append("")
    fig.text(x, y, "\n".join(lines), fontproperties=fp(size, weight), va="top", linespacing=1.35)
    return len(lines) * (size * 0.017)


def build_pdf(
    out_pdf: Path,
    *,
    name_a: str,
    name_b: str,
    traj: dict[str, pd.DataFrame],
    cell_table: pd.DataFrame,
    cmp: pd.DataFrame,
    narrative: str,
):
    ART = Path("/opt/cursor/artifacts")
    ART.mkdir(parents=True, exist_ok=True)
    with PdfPages(out_pdf) as pdf:
        # cover
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.84, "DOE3 양극(cathode) 비교 진단", fontproperties=fp(18, "bold"))
        fig.text(0.08, 0.80, f"{name_a} vs {name_b}  ·  음극 동일 (Si-on-Gr)", fontproperties=fp(12))
        fig.text(0.08, 0.74, "모노셀 · 45 °C · bimodal-30 µm 전해질 계열", fontproperties=fp(10), color="#555")
        wrap(fig, 0.08, 0.66,
             "목적: 초반(BOL/early) 파라미터 fingerprint와 수명 중 열화기작 "
             "(PE activity / contact_stack / LLI / Si co-sign)이 양극 타입에 따라 "
             "어떻게 갈라지는지 비교한다.\n\n"
             f"Arm A = {name_a} (M02Ch103–105)\n"
             f"Arm B = {name_b} (M02Ch109–111)\n\n"
             "방법: routine 0.5C 궤적 + C/3 RPT 앵커 + DCIR R forward-fill · "
             "electrode_side_v1.3 hypothesis_bol_ocp (절대 LAM% 금지).",
             width=88, size=9.5)
        fig.text(0.08, 0.12, "CycleDiag · compare_doe_cathodes.py · 2026-08-06", fontproperties=fp(8), color="#777")
        pdf.savefig(fig); plt.close(fig)

        # early contrast
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "1. 초반부터 다른 파라미터", fontproperties=fp(13, "bold"))
        early = top_differences(cmp, family="early", n=10)
        y = 0.90
        wrap(fig, 0.08, y, "early = routine SoHQ≥90%, cycle≤50 구간의 median (셀 평균).", width=92, size=8.5)
        y = 0.86
        if not early.empty:
            for _, r in early.iterrows():
                y -= 0.035
                fig.text(0.08, y, str(r["metric"])[:42], fontproperties=fp(8, "bold"))
                fig.text(0.48, y,
                         f"{name_a} {r[f'{name_a}_mean']:.4g} ± {r[f'{name_a}_std']:.3g}   |   "
                         f"{name_b} {r[f'{name_b}_mean']:.4g} ± {r[f'{name_b}_std']:.3g}",
                         fontproperties=fp(7.5))
                y -= 0.02
                eff = r.get("effect_size")
                fig.text(0.48, y,
                         f"Δ({name_b}−{name_a})={r[f'diff_{name_b}_minus_{name_a}']:+.4g}   "
                         f"effect={eff:+.2f}σ" if eff is not None and np.isfinite(eff) else "",
                         fontproperties=fp(7), color="#555")
        pdf.savefig(fig); plt.close(fig)

        # SoHQ overlay
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "2. 용량 유지율 · 전극 lean 궤적", fontproperties=fp(13, "bold"))
        ax1 = fig.add_axes([0.10, 0.55, 0.82, 0.32])
        ax2 = fig.add_axes([0.10, 0.12, 0.82, 0.32])
        for arm, color, ls in ((name_a, C_A, "-"), (name_b, C_B, "--")):
            cells = [c for c, df in traj.items() if cell_table.loc[cell_table.cell_id == c, "arm"].iloc[0] == arm]
            for i, cid in enumerate(cells):
                d = traj[cid]
                r = d[d["cycle_role"].astype(str).eq("routine_05c")] if "cycle_role" in d.columns else d
                ax1.plot(r["cycle"], r["SoHQ"], color=color, lw=1.5 if i == 0 else 1.0,
                         alpha=0.95 if i == 0 else 0.45, ls=ls, label=arm if i == 0 else None)
                if "PE_side_score" in r and "contact_stack_score" in r:
                    ax2.plot(r["cycle"], r["PE_side_score"] - r["contact_stack_score"],
                             color=color, lw=1.4 if i == 0 else 0.9, alpha=0.9 if i == 0 else 0.4, ls=ls,
                             label=arm if i == 0 else None)
        ax1.set_ylabel("SoHQ % (routine)", fontproperties=fp(9))
        ax1.set_title("Retention", fontproperties=fp(10, "bold"), loc="left")
        ax1.legend(prop=fp(8), frameon=False); ax1.grid(True, alpha=0.25)
        ax2.axhline(0, color="#999", lw=0.6)
        ax2.set_xlabel("Cycle", fontproperties=fp(9))
        ax2.set_ylabel("Δ PE − contact", fontproperties=fp(9))
        ax2.set_title("상대 lean (양수=PE activity)", fontproperties=fp(10, "bold"), loc="left")
        ax2.legend(prop=fp(8), frameon=False); ax2.grid(True, alpha=0.25)
        for ax in (ax1, ax2):
            for lab in ax.get_xticklabels() + ax.get_yticklabels():
                lab.set_fontproperties(fp(8))
        pdf.savefig(fig); plt.close(fig)

        # mechanism deltas
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "3. 열화기작 Δ (late − early)", fontproperties=fp(13, "bold"))
        aging = top_differences(cmp, family="delta_aging", n=8)
        if not aging.empty:
            ax = fig.add_axes([0.18, 0.35, 0.70, 0.50])
            labels = [str(x).replace("delta_", "") for x in aging["metric"]]
            x = np.arange(len(labels))
            w = 0.35
            ax.barh(x - w / 2, aging[f"{name_a}_mean"], height=w, color=C_A, label=name_a)
            ax.barh(x + w / 2, aging[f"{name_b}_mean"], height=w, color=C_B, label=name_b)
            ax.set_yticks(x); ax.set_yticklabels(labels, fontproperties=fp(8))
            ax.axvline(0, color="#999", lw=0.6)
            ax.legend(prop=fp(8), frameon=False); ax.grid(True, axis="x", alpha=0.25)
            ax.set_xlabel("Δ score (late−early)", fontproperties=fp(9))
            for lab in ax.get_xticklabels():
                lab.set_fontproperties(fp(8))
        wrap(fig, 0.08, 0.28, narrative, width=92, size=8.5)
        pdf.savefig(fig); plt.close(fig)

        # PE vs contact drivers
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "4. 드라이버: PE activity vs contact_loss", fontproperties=fp(13, "bold"))
        ax = fig.add_axes([0.12, 0.20, 0.78, 0.65])
        for arm, color, marker in ((name_a, C_A, "o"), (name_b, C_B, "s")):
            cells = cell_table.loc[cell_table.arm == arm, "cell_id"]
            first = True
            for cid in cells:
                d = traj[cid]
                r = d[d["cycle_role"].astype(str).eq("routine_05c")] if "cycle_role" in d.columns else d
                ax.plot(r["contact_loss_score"], r["LAM_PE_pattern_score"], marker, color=color,
                        ms=4, alpha=0.7, label=arm if first else None)
                first = False
        ax.set_xlabel("contact_loss", fontproperties=fp(9))
        ax.set_ylabel("LAM_PE activity pattern", fontproperties=fp(9))
        ax.legend(prop=fp(8), frameon=False); ax.grid(True, alpha=0.25)
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(fp(8))
        wrap(fig, 0.08, 0.12,
             "점이 우측=접촉/스택 증거↑, 위=양극 activity/isolation↑. "
             "두 팔이 다른 궤적을 그리면 양극 타입에 따른 기작 분기를 시사한다.",
             width=92, size=8.5)
        pdf.savefig(fig); plt.close(fig)

        # limits
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "5. 한계 · 다음", fontproperties=fp(13, "bold"))
        wrap(fig, 0.08, 0.88,
             "· n=3/arm — effect size는 탐색용. 통계 검정은 후속.\n"
             "· 절대 LAM% 금지. PE pattern은 NCM 이차 고립/균열을 포함할 수 있음.\n"
             "· 음극 동일 가정은 DOE 설계에 따름 — 로트/코팅 변동은 미측정.\n"
             "· DOE3 펄스 ≈109 A (set4 77 A와 다름) — 자동 감지 적용.\n"
             "· aged 하프셀·압력 로그 오면 Level-3 검증 가능.",
             width=92, size=9.5)
        pdf.savefig(fig); plt.close(fig)

        meta = pdf.infodict()
        meta["Title"] = f"DOE3 Cathode Compare {name_a} vs {name_b}"
        meta["Author"] = "CycleDiag"

    (ART / out_pdf.name).write_bytes(out_pdf.read_bytes())


def main() -> None:
    p = argparse.ArgumentParser(description="Compare DOE cathode arms")
    p.add_argument("--arm", action="append", required=True, help="Name:folder (repeat twice)")
    p.add_argument("--out-dir", type=Path, default=Path("example/output/doe3_cathode_compare"))
    p.add_argument("--halfcell-dir", type=Path, default=None)
    p.add_argument("--step", type=int, default=10)
    args = p.parse_args()
    if len(args.arm) != 2:
        raise SystemExit("Provide exactly two --arm Name:path")

    (name_a, dir_a), (name_b, dir_b) = parse_arm(args.arm[0]), parse_arm(args.arm[1])
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    traj: dict[str, pd.DataFrame] = {}
    rows: list[dict] = []
    for arm, folder in ((name_a, dir_a), (name_b, dir_b)):
        for path in list_raw_csvs(folder):
            print(f"diagnose {arm} {path.name} ...", flush=True)
            feats, segs, meta = diagnose_one(path, halfcell_dir=args.halfcell_dir, step=args.step)
            cid = meta["cell_id"]
            traj[cid] = feats
            feats.to_csv(out / f"{cid}_trajectory.csv", index=False)
            segs.to_csv(out / f"{cid}_segments.csv", index=False)
            rows.append(cell_summary_row(arm, path, feats, meta))

    cell_table = pd.DataFrame(rows)
    cell_table.to_csv(out / "cell_summaries.csv", index=False)

    arm_a = arm_aggregate(cell_table.loc[cell_table.arm == name_a].to_dict("records"))
    arm_b = arm_aggregate(cell_table.loc[cell_table.arm == name_b].to_dict("records"))
    (out / "arm_A_aggregate.json").write_text(json.dumps(arm_a, indent=2), encoding="utf-8")
    (out / "arm_B_aggregate.json").write_text(json.dumps(arm_b, indent=2), encoding="utf-8")

    cmp = compare_arms(arm_a, arm_b, name_a=name_a, name_b=name_b)
    cmp.to_csv(out / "arm_contrast.csv", index=False)
    narrative = summarize_mechanism_contrast(cmp, name_a=name_a, name_b=name_b)
    (out / "mechanism_contrast.md").write_text(narrative, encoding="utf-8")

    # markdown report
    summary_cols = [
        c for c in (
            "arm", "cell_id", "SoHQ_end", "fade_exponent_b", "knee_cycle_bw",
            "early_SoHQ", "early_LAM_PE_pattern_score", "early_contact_loss_score",
            "late_LAM_PE_pattern_score", "late_contact_loss_score",
            "delta_LAM_PE_pattern_score", "delta_contact_loss_score",
            "delta_PE_side_score", "delta_contact_stack_score",
        ) if c in cell_table.columns
    ]
    try:
        table_md = cell_table[summary_cols].to_markdown(index=False)
    except ImportError:
        table_md = "```\n" + cell_table[summary_cols].to_string(index=False) + "\n```"
    lines = [
        f"# DOE3 양극 비교: {name_a} vs {name_b}",
        "",
        "- 음극: Si-on-Gr (동일) · 양극만 다름",
        f"- cells A: {', '.join(cell_table.loc[cell_table.arm==name_a,'cell_id'])}",
        f"- cells B: {', '.join(cell_table.loc[cell_table.arm==name_b,'cell_id'])}",
        "",
        narrative,
        "",
        "## 셀별 요약",
        "",
        table_md,
    ]
    (out / "COMPARE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    pdf_path = out / f"DOE3_{name_a}_vs_{name_b}_cathode_compare.pdf"
    build_pdf(pdf_path, name_a=name_a, name_b=name_b, traj=traj, cell_table=cell_table, cmp=cmp, narrative=narrative)
    print(narrative)
    print(f"wrote {out}")
    print(f"wrote {pdf_path}")


if __name__ == "__main__":
    main()
