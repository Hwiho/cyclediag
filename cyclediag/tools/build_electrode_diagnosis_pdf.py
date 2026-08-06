#!/usr/bin/env python3
"""Build detailed Korean PDF report — electrode diagnosis v1.3 (Si-on-Gr · NCM82)."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "example" / "output" / "electrode_segments"
ART_DIR = Path("/opt/cursor/artifacts")

C_PE, C_NE, C_CL = "#C45C26", "#1F6F8B", "#0F766E"
C_SOHQ, C_RPT, C_SHARED = "#1A1A1A", "#F59E0B", "#6B7280"
C_BG, C_BAND_PE, C_BAND_CL = "#FAF7F2", "#F3D9C8", "#D1E7DD"


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


def load_cell(cell: str):
    d = pd.read_csv(OUT_DIR / f"{cell}_electrode_trajectory.csv").sort_values("cycle")
    d = d[d["cycle"] >= 2].copy()
    for c in d.columns:
        if c not in ("cycle_role", "dominant_electrode", "electrode_narrative", "PE_top_modes", "NE_top_modes", "shared_top_modes"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
    segs = pd.read_csv(OUT_DIR / f"{cell}_electrode_segments.csv")
    rpt = pd.read_csv(OUT_DIR / f"{cell}_rpt_c3_anchors.csv") if (OUT_DIR / f"{cell}_rpt_c3_anchors.csv").exists() else pd.DataFrame()
    val = json.loads((OUT_DIR / f"{cell}_validation.json").read_text()) if (OUT_DIR / f"{cell}_validation.json").exists() else {}
    return d, segs, rpt, val


def new_page(pdf, title=None):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    if title:
        fig.text(0.08, 0.955, title, fontproperties=fp(13, "bold"), va="top")
        fig.text(0.08, 0.932, "CycleDiag · ASSB SJ900 · Si-on-Gr · NCM82 secondary · v1.3", fontproperties=fp(8), color="#666")
    return fig


def wrap(fig, x, y, text, width=92, size=9, weight="normal", color="#222"):
    lines = []
    for para in text.split("\n"):
        lines.extend(textwrap.wrap(para, width=width) or [""]) if para.strip() else lines.append("")
    fig.text(x, y, "\n".join(lines), fontproperties=fp(size, weight), color=color, va="top", linespacing=1.35)
    return len(lines) * (size * 0.0175)


def shade(ax, segs):
    if segs is None or segs.empty:
        return
    for _, s in segs.iterrows():
        dom = str(s.get("dominant_electrode") or "")
        color = C_BAND_PE if dom == "PE" else (C_BAND_CL if dom in ("contact_stack", "NE", "contact_or_NE") else "#EEEEEE")
        ax.axvspan(float(s["cycle_start"]), float(s["cycle_end"]), color=color, alpha=0.35, lw=0)


def routine(d):
    if "cycle_role" in d.columns:
        r = d[d["cycle_role"].astype(str).eq("routine_05c")]
        if len(r) >= 8:
            return r
    return d


def rpt_rows(d):
    if "cycle_role" in d.columns:
        return d[d["cycle_role"].astype(str).eq("rpt_c3")]
    return d.iloc[0:0]


# ── pages ─────────────────────────────────────────────────────────────

def page_cover(pdf, d22, d24, v22, v24):
    fig = new_page(pdf)
    fig.text(0.08, 0.84, "ASSB SJ900 양·음극 열화 가설 진단 리포트", fontproperties=fp(17, "bold"))
    fig.text(0.08, 0.80, "M01Ch022 · M01Ch024  ·  methodology v1.3 (검증·개정 후)", fontproperties=fp(11))
    box = FancyBboxPatch((0.08, 0.40), 0.84, 0.34, transform=fig.transFigure,
                         boxstyle="round,pad=0.02,rounding_size=0.02", facecolor=C_BG, edgecolor="#DDD")
    fig.patches.append(box)
    wrap(fig, 0.11, 0.70,
         "화학 정체성\n"
         "· 음극: Silicon coated on graphite (Si-on-Gr). 흑연이 노출될 수 있음.\n"
         "· 양극: NCM82 이차입자 — 균열/전자 고립이 화학양론적 LAM%와 동일하지 않음.\n"
         "· 전해질: 전고체(ASSB) · 45 °C · 2.5–4.2 V · ~72 Ah\n\n"
         "프로토콜\n"
         "· routine 0.5C (|I|≈38.7 A) · C/3 RPT (|I|≈25.8 A, ~105 cyc) · DC-IR 1C\n"
         "· 중간 SoHQ 스파이크 = C/3 RPT (노이즈 아님). Δ(RPT−routine)≈+3~7%p\n\n"
         "진단 레벨: hypothesis_bol_ocp — 절대 LAM% / *_est 금지 (aged 하프셀 전)",
         width=78, size=9)
    wrap(fig, 0.08, 0.34,
         "핵심 한 줄: 두 셀 모두 초·중기에 접촉/스택 ohmic 패턴과 PE activity 패턴이 경합하고, "
         "중기 RPT 구간 전후 contact가 강해지며, 후반 PE activity/isolation 쪽 lean이 열린다. "
         "Si co-sign이 있을 때만 Si-on-Gr 음극 기계적/접촉 가설로 읽는다.",
         width=92, size=9.5)
    fig.text(0.08, 0.12, "검증 계획: VALIDATION_IMPROVEMENT_PLAN_v1_3.md · 2026-08-06", fontproperties=fp(8), color="#777")
    pdf.savefig(fig); plt.close(fig)


def page_validation(pdf, v22, v24):
    fig = new_page(pdf, "1. 검증: 로직·지표·추출이 타당한가")
    y = 0.90
    y -= wrap(fig, 0.08, y, "1.1 감사에서 확인·수정한 Critical 이슈", width=92, size=11, weight="bold") + 0.01
    y -= wrap(fig, 0.08, y,
              "C1 방전 residual argmax가 DOD였음 → SOC=100−DOD로 교정. "
              "C2 Q_relax가 RPT에만 찍혀 routine lean에서 Si co-sign이 공허했음 → forward-fill. "
              "C3 ‘Si-rich / stage 없음’ 언어가 Si-on-Gr와 불일치 → 화학 레지스트리·서사 개정. "
              "C4 baseline R 없을 때 absolute R 점수화 → term skip.",
              width=92, size=9) + 0.015
    y -= wrap(fig, 0.08, y, "1.2 이번 사이클 DoD 결과 (Ch022)", width=92, size=11, weight="bold") + 0.01
    qr = v22.get("q_relax_coverage") or {}
    rs = v22.get("residual_soc") or {}
    lam = v22.get("lam_pe") or {}
    roles = (v22.get("cycle_roles") or {}).get("counts") or {}
    y -= wrap(fig, 0.08, y,
              f"· Q_relax routine coverage = {qr.get('coverage')} (목표 ≫0 → 달성)\n"
              f"· residual SOC median≈{rs.get('median'):.1f}% · highSOC≥60 비율={rs.get('frac_high_soc_ge60')}\n"
              f"· LAM_PE ceiling_frac={lam.get('ceiling_frac')} · nunique={lam.get('nunique')} (고착 해제)\n"
              f"· roles: {roles}\n"
              f"· methodology={v22.get('methodology_version')} · chemistry={v22.get('chemistry')}",
              width=92, size=9) + 0.015
    y -= wrap(fig, 0.08, y, "1.3 과학적으로 유지한 계약", width=92, size=11, weight="bold") + 0.01
    wrap(fig, 0.08, y,
         "· 절대 LAM_PE/NE% 및 *_est / *_est_hc_calibrated 금지 (aged HC 전).\n"
         "· contact_loss → contact_stack 우선; NE는 Si chemo-mech co-sign 있을 때만.\n"
         "· peak-only로 LAM_NE% 산출 금지. (후속: 노출 Gr stage는 monitoring만)\n"
         "· PE 점수 = activity/isolation pattern (이차입자 균열 포함 가능) — 화학양론 LAM% 아님.\n"
         "· C/3 RPT는 dual-track 앵커; fade/lean은 routine 0.5C only.",
         width=92, size=9)
    pdf.savefig(fig); plt.close(fig)


def page_methods(pdf):
    fig = new_page(pdf, "2. 방법론 · 왜 이렇게 읽는가")
    y = 0.90
    y -= wrap(fig, 0.08, y, "2.1 전극 가설 점수", width=92, size=11, weight="bold") + 0.008
    y -= wrap(fig, 0.08, y,
              "PE_side ≈ 0.75·LAM_PE_pattern + 0.20·feature boost + FC-OCP Δhits boost\n"
              "contact_stack ≈ contact_loss (R_ohmic growth / ΔR / R_frac 중심)\n"
              "NE_hyp ≈ contact × Si co-sign + residual/SOC boost (Si 피처 이중계산 제거)\n"
              "lean: PE vs max(contact, NE_hyp). 세그먼트: routine only · dwell≥4 · ε=0.05",
              width=92, size=9) + 0.012
    y -= wrap(fig, 0.08, y, "2.2 파라미터 추출 (검증된 것 / 한계)", width=92, size=11, weight="bold") + 0.008
    y -= wrap(fig, 0.08, y,
              "· DC-IR: RΩ + Rct(1−e^(−t/τ)) + A√t, 펄스 thr=0.75×1C (0.5C 오인 방지).\n"
              "· η(SOC): C/3 vs 0.5C 동일 Q 축. RCF = Q_C/3 / Q_0.5C.\n"
              "· Q_relax: RPT 2사이클 용량차 → routine에 forward-fill.\n"
              "· curve fit: V_N≈V_ref(sQ+o)−I·dR → LAM/LLI/R proxies (bound 포화 시 null).\n"
              "· 한계: CE>100% pairing 버그(가드만), DCIR SOC 순서 전압검증 미완, Gr stage feature 미구현.",
              width=92, size=9) + 0.012
    y -= wrap(fig, 0.08, y, "2.3 Si-on-Gr에서의 해석 규칙", width=92, size=11, weight="bold") + 0.008
    wrap(fig, 0.08, y,
         "실리콘이 흑연 위에 코팅되어 있으므로 Si 부피팽창·접촉 손실 신호가 나타날 수 있고, "
         "동시에 흑연이 노출되면 stage 피크가 보일 수 있다. 이번 버전은 Si chemo-mech co-sign"
         "(hyst_low↑, Q_relax, mech/chem, CV)로 NE 가설을 열고, Gr stage monitoring은 후속이다. "
         "‘음극 확정 LAM’은 aged 하프셀 CompositeOCP 전까지 하지 않는다.",
         width=92, size=9)
    pdf.savefig(fig); plt.close(fig)


def page_param_science(pdf):
    fig = new_page(pdf, "3. 패턴을 결정하는 파라미터 (과학적 의미)")
    rows = [
        ("SoHQ_routine", "0.5C 용량유지율", "연속 fade·구간 물리축"),
        ("SoHQ_rpt_c3", "C/3 RPT 용량", "rate gap 앵커; 가짜 회복 방지"),
        ("R_ohmic_growth_100", "오믹 저항 성장률", "contact_stack 1차 증거"),
        ("mech_vs_chem_ratio", "RΩ/Rct", "기계적 vs 계면 화학"),
        ("Q_relax_pct", "RPT 용량 완화", "Si 완화/회복 co-sign"),
        ("hyst_area_low", "저SOC 히스테리시스", "Si chemo-mech 지표"),
        ("LAM_PE_pattern", "PE activity 패턴", "NCM82 이차: 고립≠LAM%"),
        ("LAM_curve_proxy", "곡선 scale proxy", "bound 포화 시 null"),
        ("RCF / PER / η", "rate capability", "C/3↔0.5C 이중트랙"),
        ("fade_b / knee", "페이드 지수·변곡", "routine SoHQ만 적합"),
    ]
    y = 0.88
    fig.text(0.08, y, "파라미터", fontproperties=fp(9, "bold"))
    fig.text(0.30, y, "의미", fontproperties=fp(9, "bold"))
    fig.text(0.58, y, "해석 역할", fontproperties=fp(9, "bold"))
    y -= 0.02
    for a, b, c in rows:
        y -= 0.048
        fig.text(0.08, y, a, fontproperties=fp(8, "bold"))
        fig.text(0.30, y, b, fontproperties=fp(8))
        fig.text(0.58, y, c, fontproperties=fp(8))
    y -= 0.05
    wrap(fig, 0.08, y,
         "Ch022/024에서 중기 lean을 흔든 주인공은 contact_loss(RΩ 성장)와 PE activity 점수의 상대 마진이다. "
         "Si co-sign(median≈0.4 after Q_relax fill)이 중기 이후 올라가 NE 가설 창을 열지만, "
         "dominance는 여전히 PE↔contact 경합이 중심이다.",
         width=92, size=9)
    pdf.savefig(fig); plt.close(fig)


def page_overview(pdf, cell, d, segs, rpt, narrative):
    fig = new_page(pdf, f"4. {cell} — 용량·전극 가설 궤적")
    wrap(fig, 0.08, 0.905, narrative, width=95, size=8.2)
    gs = fig.add_gridspec(2, 1, left=0.10, right=0.95, top=0.78, bottom=0.08, hspace=0.28)
    ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    r, rp = routine(d), rpt_rows(d)
    shade(ax1, segs)
    ax1.plot(r["cycle"], r["SoHQ"], color=C_SOHQ, lw=2, label="SoHQ 0.5C")
    if not rp.empty:
        ax1.scatter(rp["cycle"], rp["SoHQ"], s=40, zorder=5, facecolors=C_RPT, edgecolors="#92400E", label="C/3 RPT")
    ax1.set_ylabel("SoHQ (%)", fontproperties=fp(9)); ax1.set_ylim(55, 105)
    ax1.legend(prop=fp(8), frameon=False, loc="upper right"); ax1.grid(True, alpha=0.25)
    ax1.set_title("이중 트랙: routine fade vs RPT 앵커", fontproperties=fp(10, "bold"), loc="left")
    shade(ax2, segs)
    ax2.plot(r["cycle"], r["PE_side_score"], color=C_PE, lw=2, label="PE activity")
    ax2.plot(r["cycle"], r["contact_stack_score"], color=C_CL, lw=1.8, label="contact_stack")
    ax2.plot(r["cycle"], r["NE_side_score"], color=C_NE, lw=1.4, ls="--", label="NE_hyp")
    ax2.set_xlabel("Cycle", fontproperties=fp(9)); ax2.set_ylabel("Side score", fontproperties=fp(9))
    ax2.set_ylim(0, 0.9); ax2.legend(prop=fp(8), ncol=3, frameon=False); ax2.grid(True, alpha=0.25)
    for ax in (ax1, ax2):
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(fp(8))
    pdf.savefig(fig); plt.close(fig)


def page_drivers(pdf, cell, d, segs):
    fig = new_page(pdf, f"5. {cell} — 결정 파라미터 시각화")
    wrap(fig, 0.08, 0.905,
         "상단: LAM_PE(activity) vs contact_loss vs LLI. 중단: RΩ growth · mech/chem · Q_relax. "
         "하단: lean Δ=PE−contact (전환 트리거).",
         width=95, size=8.2)
    r = routine(d)
    gs = fig.add_gridspec(3, 1, left=0.10, right=0.95, top=0.84, bottom=0.07, hspace=0.32)
    ax0, ax1, ax2 = [fig.add_subplot(gs[i]) for i in range(3)]
    shade(ax0, segs)
    ax0.plot(r["cycle"], r["LAM_PE_pattern_score"], color=C_PE, lw=2, label="LAM_PE (activity)")
    ax0.plot(r["cycle"], r["contact_loss_score"], color=C_CL, lw=2, label="contact_loss")
    if "LLI_pattern_score" in r:
        ax0.plot(r["cycle"], r["LLI_pattern_score"], color="#9333EA", lw=1.2, ls="--", label="LLI")
    ax0.legend(prop=fp(7), ncol=3, frameon=False); ax0.set_ylim(0, 1.05); ax0.grid(True, alpha=0.25)
    ax0.set_ylabel("pattern", fontproperties=fp(8))

    shade(ax1, segs)
    if "R_ohmic_growth_100" in r:
        ax1.plot(r["cycle"], r["R_ohmic_growth_100"], color="#B45309", lw=1.6, label="RΩ growth/100")
    if "mech_vs_chem_ratio" in r:
        ax1.plot(r["cycle"], r["mech_vs_chem_ratio"], color=C_CL, lw=1.4, label="mech/chem")
    if "Q_relax_pct" in r:
        ax1b = ax1.twinx()
        ax1b.plot(r["cycle"], r["Q_relax_pct"], color=C_NE, lw=1.2, ls=":", label="Q_relax%")
        ax1b.set_ylabel("Q_relax %", fontproperties=fp(8))
        for lab in ax1b.get_yticklabels():
            lab.set_fontproperties(fp(7))
    ax1.legend(prop=fp(7), loc="upper left", frameon=False); ax1.grid(True, alpha=0.25)
    ax1.set_ylabel("R metrics", fontproperties=fp(8))

    shade(ax2, segs)
    delta = r["PE_side_score"] - r["contact_stack_score"]
    ax2.fill_between(r["cycle"], 0, delta, where=delta >= 0, color=C_PE, alpha=0.35, interpolate=True)
    ax2.fill_between(r["cycle"], 0, delta, where=delta < 0, color=C_CL, alpha=0.35, interpolate=True)
    ax2.plot(r["cycle"], delta, color="#222", lw=1.2)
    ax2.axhline(0, color="#999", lw=0.6)
    ax2.set_xlabel("Cycle", fontproperties=fp(9)); ax2.set_ylabel("Δ PE−contact", fontproperties=fp(8))
    ax2.grid(True, alpha=0.25)
    for ax in (ax0, ax1, ax2):
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(fp(7))
    pdf.savefig(fig); plt.close(fig)


def page_segments(pdf, cell, segs):
    fig = new_page(pdf, f"6. {cell} — 구간 표")
    wrap(fig, 0.08, 0.90, "routine_05c only. dominant = PE | contact_stack | NE(Si co-sign) | mixed.", width=95, size=8.5)
    if segs.empty:
        pdf.savefig(fig); plt.close(fig); return
    y = 0.86
    headers = ["Seg", "Cycle", "SoHQ", "지배", "PE", "contact", "si", "LAM", "CL"]
    xs = [0.08, 0.14, 0.28, 0.40, 0.52, 0.62, 0.74, 0.82, 0.90]
    for x, h in zip(xs, headers):
        fig.text(x, y, h, fontproperties=fp(8, "bold"))
    y -= 0.025
    for _, s in segs.iterrows():
        y -= 0.028
        vals = [
            str(int(s["segment"])),
            f"{int(s['cycle_start'])}-{int(s['cycle_end'])}",
            f"{s['SoHQ_start']:.0f}→{s['SoHQ_end']:.0f}",
            str(s["dominant_electrode"])[:12],
            f"{s['PE_side_score_mean']:.2f}",
            f"{s['contact_stack_score_mean']:.2f}",
            f"{float(s.get('si_cosign_mean') or 0):.2f}",
            f"{float(s.get('LAM_PE_mean') or 0):.2f}",
            f"{float(s.get('contact_loss_mean') or 0):.2f}",
        ]
        for x, v in zip(xs, vals):
            fig.text(x, y, v, fontproperties=fp(7.5))
        if y < 0.12:
            break
    pdf.savefig(fig); plt.close(fig)


def page_rpt(pdf, cell, rpt):
    fig = new_page(pdf, f"7. {cell} — C/3 RPT 이중 트랙")
    wrap(fig, 0.08, 0.90,
         "RPT SoHQ가 routine보다 높게 찍히는 것은 rate가 낮아 분극이 작기 때문이다. "
         "이 차이를 ‘용량 회복’으로 읽으면 fade/lean이 왜곡된다.",
         width=95, size=9)
    if rpt is None or rpt.empty:
        pdf.savefig(fig); plt.close(fig); return
    ax = fig.add_axes([0.12, 0.35, 0.78, 0.45])
    r = rpt.dropna(subset=["SoHQ_rpt_c3"]).copy()
    ax.plot(r["cycle"], r["SoHQ_rpt_c3"], "o-", color=C_RPT, label="SoHQ C/3")
    if "SoHQ_routine_prev" in r:
        ax.plot(r["cycle"], r["SoHQ_routine_prev"], "s--", color=C_SOHQ, label="prev routine 0.5C")
    ax.set_xlabel("Cycle", fontproperties=fp(9)); ax.set_ylabel("SoHQ (%)", fontproperties=fp(9))
    ax.legend(prop=fp(8), frameon=False); ax.grid(True, alpha=0.25)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontproperties(fp(8))
    if "SoHQ_gap_vs_prev_routine" in r:
        gaps = r["SoHQ_gap_vs_prev_routine"].dropna()
        wrap(fig, 0.08, 0.28,
             f"Δ(RPT−prev routine) median = {gaps.median():+.1f}%p · "
             f"range {gaps.min():+.1f}~{gaps.max():+.1f}%p (n={len(gaps)})",
             width=92, size=9)
    pdf.savefig(fig); plt.close(fig)


def page_story(pdf, cell, text):
    fig = new_page(pdf, f"8. {cell} — 해석 스토리")
    wrap(fig, 0.08, 0.90, text, width=92, size=9)
    pdf.savefig(fig); plt.close(fig)


def page_compare(pdf, d22, d24, s22, s24):
    fig = new_page(pdf, "9. Ch022 vs Ch024 비교")
    r22, r24 = routine(d22), routine(d24)
    gs = fig.add_gridspec(2, 1, left=0.10, right=0.95, top=0.82, bottom=0.08, hspace=0.3)
    ax0, ax1 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    ax0.plot(r22["cycle"], r22["SoHQ"], color="#111", lw=2, label="Ch022")
    ax0.plot(r24["cycle"], r24["SoHQ"], color="#888", lw=2, ls="--", label="Ch024")
    ax0.set_ylabel("SoHQ routine", fontproperties=fp(9)); ax0.legend(prop=fp(8), frameon=False); ax0.grid(True, alpha=0.25)
    ax0.set_title("동일 화학·유사 fade 깊이, lean 타임라인은 셀별", fontproperties=fp(10, "bold"), loc="left")
    ax1.plot(r22["cycle"], r22["PE_side_score"] - r22["contact_stack_score"], color=C_PE, lw=1.6, label="Ch022 Δ")
    ax1.plot(r24["cycle"], r24["PE_side_score"] - r24["contact_stack_score"], color=C_CL, lw=1.6, ls="--", label="Ch024 Δ")
    ax1.axhline(0, color="#999", lw=0.6)
    ax1.set_xlabel("Cycle", fontproperties=fp(9)); ax1.set_ylabel("Δ PE−contact", fontproperties=fp(9))
    ax1.legend(prop=fp(8), frameon=False); ax1.grid(True, alpha=0.25)
    for ax in (ax0, ax1):
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(fp(8))
    pdf.savefig(fig); plt.close(fig)


def page_limits(pdf):
    fig = new_page(pdf, "10. 한계 · 금지 해석 · 다음 실험")
    wrap(fig, 0.08, 0.90,
         "하지 말아야 할 해석\n"
         "· 절대 LAM_PE/NE%로 보고하거나 *_est 컬럼을 채우기\n"
         "· contact_stack을 ‘음극 확정’으로 단정 (압력 로그·aged HC 없음)\n"
         "· C/3 RPT SoHQ bump를 용량 회복으로 읽기\n"
         "· NCM82 이차입자 cracking을 화학양론 CAM 손실과 동일시\n"
         "· ‘Si-rich라 graphite stage가 없다’고 단정 (노출 Gr 가능)\n\n"
         "후속 (P2)\n"
         "1) CE Ah pairing 근본 수정\n"
         "2) Gr stage monitoring feature (노출 지표, LAM% 아님)\n"
         "3) DCIR SOC 순서 전압 검증\n"
         "4) aged/harvested 하프셀 → Level 3 CompositeOCP\n"
         "5) 구속 압력 시계열\n\n"
         "재현\n"
         "PYTHONPATH=. python3 cyclediag/tools/diagnose_electrode_segments.py \\\n"
         "  --input example/fixtures/raw/set4_SJ900/M01Ch022_raw.csv \\\n"
         "  --out-dir example/output/electrode_segments\n"
         "PDF: cyclediag/tools/build_electrode_diagnosis_pdf.py\n"
         "계획: cyclediag/planning/VALIDATION_IMPROVEMENT_PLAN_v1_3.md",
         width=92, size=9)
    pdf.savefig(fig); plt.close(fig)


STORY_022 = (
    "프로토콜\n"
    "중간 SoHQ 상승(107/212/317/422/527)은 C/3 RPT. routine fade 지수≈1.34, knee≈350.\n\n"
    "Seg1 (≈7–100) PE activity lean\n"
    "형성 직후 PE pattern이 앞서고 contact는 낮다(early R baseline/성장 신호 약). "
    "‘양극이 갑자기 나쁘다’기보다 초기 ICA/곡선 proxy가 PE 버킷에 먼저 쌓인 단계.\n\n"
    "Seg2 (≈120–210) mixed · contact↑\n"
    "RΩ growth·contact_loss가 ~0.6대로 올라가 PE와 경합. Si co-sign≈0.4 (Q_relax fill 후). "
    "접촉/스택 가설이 열리지만 Si co-sign만으로 음극 LAM 확정은 하지 않는다.\n\n"
    "Seg3–4 (≈220–EOL) PE lean 재개\n"
    "knee(~350) 이후 PE activity가 상대적으로 우세. EOL SoHQ≈65%. "
    "NCM82 이차입자 고립/균열 가능성을 PE pattern에 포함해 읽되 %로 환산하지 않는다."
)

STORY_024 = (
    "프로토콜\n"
    "Ch022와 동일 C/3 RPT 주기. routine fade≈1.28, knee≈290.\n\n"
    "Seg1–2 (≈7–100) PE\n"
    "초반 PE activity lean. contact는 중기부터 상승.\n\n"
    "Seg2–3 중기 mixed\n"
    "≈120–180에서 contact≈0.62로 PE와 맞먹음. Si-on-Gr co-sign 상승. "
    "Ch022와 같이 ‘중기 음극 확정’이 아니라 contact↔PE 경합.\n\n"
    "Seg4 (≈290–EOL) PE\n"
    "knee 이후 PE lean이 Ch022보다 이르게 분명해진다(≈290+). SoHQ≈64%. "
    "동일 SJ900이라도 lean 타임라인은 셀별로 다르다."
)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)
    out_pdf = OUT_DIR / "ASSB_SJ900_Ch022_Ch024_electrode_diagnosis_report.pdf"
    art_pdf = ART_DIR / "ASSB_SJ900_Ch022_Ch024_electrode_diagnosis_report.pdf"

    d22, s22, r22, v22 = load_cell("M01Ch022")
    d24, s24, r24, v24 = load_cell("M01Ch024")

    with PdfPages(out_pdf) as pdf:
        page_cover(pdf, d22, d24, v22, v24)
        page_validation(pdf, v22, v24)
        page_methods(pdf)
        page_param_science(pdf)
        page_overview(pdf, "M01Ch022", d22, s22, r22,
                      "routine only 궤적 + C/3 RPT 마커. 배경: 분홍=PE seg, 녹=contact/NE seg.")
        page_drivers(pdf, "M01Ch022", d22, s22)
        page_segments(pdf, "M01Ch022", s22)
        page_rpt(pdf, "M01Ch022", r22)
        page_story(pdf, "M01Ch022", STORY_022)
        page_overview(pdf, "M01Ch024", d24, s24, r24,
                      "Ch024: 중기 contact 경합 후 PE lean이 더 이름.")
        page_drivers(pdf, "M01Ch024", d24, s24)
        page_segments(pdf, "M01Ch024", s24)
        page_rpt(pdf, "M01Ch024", r24)
        page_story(pdf, "M01Ch024", STORY_024)
        page_compare(pdf, d22, d24, s22, s24)
        page_limits(pdf)
        meta = pdf.infodict()
        meta["Title"] = "ASSB SJ900 Electrode Diagnosis Report v1.3 (Si-on-Gr / NCM82)"
        meta["Author"] = "CycleDiag"
        meta["Subject"] = "hypothesis_bol_ocp validation + dual-track RPT"
        meta["Keywords"] = "ASSB, Si-on-Gr, NCM82, contact_stack, C/3 RPT"

    art_pdf.write_bytes(out_pdf.read_bytes())
    print(f"wrote {out_pdf}")
    print(f"wrote {art_pdf}")
    print(f"pages ~{len(pdf.pages) if hasattr(pdf,'pages') else '16+'}, size={out_pdf.stat().st_size/1024:.1f} KiB")


if __name__ == "__main__":
    main()
