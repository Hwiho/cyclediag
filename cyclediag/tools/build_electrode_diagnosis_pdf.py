#!/usr/bin/env python3
"""Build a detailed Korean PDF report for Ch022/Ch024 electrode-side diagnosis."""

from __future__ import annotations

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
DATA = {
    "M01Ch022": OUT_DIR / "M01Ch022_electrode_trajectory.csv",
    "M01Ch024": OUT_DIR / "M01Ch024_electrode_trajectory.csv",
}
SEGS = {
    "M01Ch022": OUT_DIR / "M01Ch022_electrode_segments.csv",
    "M01Ch024": OUT_DIR / "M01Ch024_electrode_segments.csv",
}

# Colors (avoid purple AI-default cluster)
C_PE = "#C45C26"      # terracotta / cathode
C_NE = "#1F6F8B"      # teal / anode
C_SHARED = "#6B7280"
C_SOHQ = "#1A1A1A"
C_CL = "#0F766E"
C_LAM = "#B45309"
C_LLI = "#7C3AED"
C_BG = "#FAF7F2"
C_BAND_PE = "#F3D9C8"
C_BAND_NE = "#CDE5EC"


def _setup_font() -> str:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            prop = font_manager.FontProperties(fname=path)
            name = prop.get_name()
            mpl.rcParams["font.family"] = name
            mpl.rcParams["axes.unicode_minus"] = False
            return path
    return ""


FONT_PATH = _setup_font()


def fp(size: float = 10, weight: str = "normal") -> font_manager.FontProperties:
    if FONT_PATH:
        return font_manager.FontProperties(fname=FONT_PATH, size=size, weight=weight)
    return font_manager.FontProperties(size=size, weight=weight)


def load_cell(cell: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_csv(DATA[cell]).sort_values("cycle")
    d = d[d["cycle"] >= 2].copy()
    for c in (
        "SoHQ", "PE_side_score", "NE_side_score", "shared_side_score",
        "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
        "dominance_margin", "electrode_confidence", "mech_vs_chem_ratio", "PER",
    ):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d["delta_PE_NE"] = d["PE_side_score"] - d["NE_side_score"]
    segs = pd.read_csv(SEGS[cell]) if SEGS[cell].exists() else pd.DataFrame()
    return d, segs


def new_page(pdf: PdfPages, title: str | None = None):
    fig = plt.figure(figsize=(8.27, 11.69))  # A4
    fig.patch.set_facecolor("white")
    if title:
        fig.text(0.08, 0.955, title, fontproperties=fp(14, "bold"), va="top")
        fig.text(0.08, 0.935, "CycleDiag · ASSB SJ900 · hypothesis_bol_ocp", fontproperties=fp(8), color="#666")
    return fig


def draw_wrapped(fig, x, y, text, width=92, size=9, color="#222", weight="normal", va="top"):
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=width) or [""])
    block = "\n".join(lines)
    fig.text(x, y, block, fontproperties=fp(size, weight), color=color, va=va, ha="left", linespacing=1.35)
    # estimate height consumed (~ size points)
    return len(lines) * (size * 0.018)


def shade_segments(ax, segs: pd.DataFrame, y0=0, y1=1):
    if segs is None or segs.empty:
        return
    for _, s in segs.iterrows():
        dom = str(s.get("relative_dominant") or s.get("dominant_electrode") or "")
        color = C_BAND_PE if dom == "PE" else (C_BAND_NE if dom == "NE" else "#EEEEEE")
        ax.axvspan(float(s["cycle_start"]), float(s["cycle_end"]), color=color, alpha=0.35, lw=0)


def page_cover(pdf: PdfPages):
    fig = new_page(pdf)
    fig.text(0.08, 0.82, "ASSB SJ900 양·음극 열화 가설 진단 리포트", fontproperties=fp(18, "bold"))
    fig.text(0.08, 0.78, "M01Ch022 · M01Ch024 구간별 PE/NE dominance 분석", fontproperties=fp(12))
    box = FancyBboxPatch((0.08, 0.42), 0.84, 0.28, transform=fig.transFigure,
                         boxstyle="round,pad=0.02,rounding_size=0.02",
                         facecolor=C_BG, edgecolor="#DDD", linewidth=1)
    fig.patches.append(box)
    summary = (
        "진단 레벨: hypothesis_bol_ocp (aged 하프셀 교정 아님)\n"
        "셀: set4 SJ900 full-cell · 45 °C · 2.5–4.2 V · 0.5C routine / C/3 RPT\n"
        "Ch022: SoHQ ≈ 100% → 65% (564 cyc) · 중기 음극(contact_loss) → 후기 양극(PE)\n"
        "Ch024: SoHQ ≈ 100% → 64% (≈533 cyc) · 초·후기 양극 경향 · 중기 음극 포켓\n"
        "근거: full-cell pattern score + BOL OCP peak attribution + fade trajectory"
    )
    draw_wrapped(fig, 0.11, 0.66, summary, width=78, size=9.5)
    fig.text(0.08, 0.34, "핵심 결론 (한 줄)", fontproperties=fp(11, "bold"))
    draw_wrapped(
        fig, 0.08, 0.30,
        "두 셀 모두 수명 후반에 양극(PE) 쪽 신호가 상대적으로 강해지지만, "
        "Ch022는 중기(~80–380 사이클)에 음극(NE) 접촉 손실(contact_loss) 가설이 "
        "더 길고 명확하게 지속된 뒤 ~390 사이클 부근에서 양극 지배로 전환된다. "
        "이 결과는 절대 LAM%가 아니라 full-cell 패턴 점수와 BOL OCP에 기반한 상대 가설이다.",
        width=92, size=9.5,
    )
    fig.text(0.08, 0.12, "작성: CycleDiag automated report · 2026-08-06", fontproperties=fp(8), color="#777")
    fig.text(0.08, 0.09, "정책: IMPROVEMENT_ROADMAP §9.5 · LLI_LAM_DIAGNOSIS (ASSB Si-rich)", fontproperties=fp(8), color="#777")
    pdf.savefig(fig)
    plt.close(fig)


def page_methods(pdf: PdfPages):
    fig = new_page(pdf, "1. 진단이 무엇을 말하는지 (과학적 프레임)")
    y = 0.90
    y -= draw_wrapped(fig, 0.08, y, "1.1 왜 ‘가설’인가", width=92, size=11, weight="bold") + 0.01
    y -= draw_wrapped(
        fig, 0.08, y,
        "전고체(ASSB) 파우치 full-cell만으로는 양극·음극 각각의 활성물질 손실(LAM_PE/LAM_NE)을 "
        "절대 %로 분리하기 어렵다. 관측되는 것은 V(Q), I(t), DC-IR, dQ/dV 피크 등 셀 수준 신호다. "
        "본 리포트의 PE/NE 점수는 ‘어느 전극 쪽 증거가 상대적으로 더 큰가’를 나타내는 "
        "hypothesis_bol_ocp 레벨이며, aged/harvested 하프셀이 없는 한 *_est_hc_calibrated 는 채우지 않는다.",
        width=92, size=9,
    ) + 0.02
    y -= draw_wrapped(fig, 0.08, y, "1.2 ASSB Si-rich에서의 전극 매핑 규칙", width=92, size=11, weight="bold") + 0.01
    y -= draw_wrapped(
        fig, 0.08, y,
        "• 양극(PE): LAM_PE pattern score + 고SOC 분극/히스테리시스 + 양극 BOL OCP 피크와 "
        "full-cell dQ/dV 피크의 전압 근접(attribution).\n"
        "• 음극(NE): contact_loss score를 Si 음극 기계적 접촉 손실의 1차 경로로 취급 "
        "(ASSB에서 R_ohmic 성장·mech/chem 비). 흑연 stage 기반 LAM_NE 피크 단독 판정은 금지.\n"
        "• 공유(shared): LLI, interface_R, SE_decomposition, microshort, solid_diffusion — "
        "전극 한쪽에만 귀속하기 어려운 셀 수준 모드.",
        width=92, size=9,
    ) + 0.02
    y -= draw_wrapped(fig, 0.08, y, "1.3 점수 산식 (개념)", width=92, size=11, weight="bold") + 0.01
    y -= draw_wrapped(
        fig, 0.08, y,
        "PE_side ≈ 0.70·mean(PE 모드 점수) + 0.25·feature boost + peak attribution boost\n"
        "NE_side ≈ 0.70·mean(NE 모드 점수) + 0.30·feature boost\n"
        "lean Δ = PE_side − NE_side  (≥ +0.02 → PE lean, ≤ −0.02 → NE lean)\n"
        "구간 분할: lean 부호 전환 · LAM_PE vs contact_loss 우위 전환 · (가능 시) knee 통과",
        width=92, size=9,
    ) + 0.02
    y -= draw_wrapped(fig, 0.08, y, "1.4 데이터·전처리", width=92, size=11, weight="bold") + 0.01
    draw_wrapped(
        fig, 0.08, y,
        "용량(capa) 사이클만 사용. DC-IR 3-SOC 펄스 트리플릿(|I|≈1C)은 SoHQ가 부분 SOC로 "
        "왜곡되므로 제외. 루틴 0.5C와 혼동되지 않도록 펄스 임계를 0.75·1C로 엄격화. "
        "샘플: ~10 사이클 간격 + RPT 직전 capa + 수명 마일스톤. "
        "baseline: SoHQ≥95% 첫 용량 사이클. BOL 하프셀: C/20, 음극 cycle 1–3, 양극 단사이클.",
        width=92, size=9,
    )
    pdf.savefig(fig)
    plt.close(fig)


def page_param_catalog(pdf: PdfPages):
    fig = new_page(pdf, "2. 패턴을 결정하는 핵심 파라미터")
    rows = [
        ("SoHQ", "용량 유지율(%)", "열화 단계·구간 경계의 물리 축"),
        ("LAM_PE_pattern_score", "양극 활성물질 손실 패턴", "PE 측 핵심 모드 (피크 면적·곡선 proxy 등)"),
        ("contact_loss_score", "접촉 손실 패턴", "NE 측 핵심 (R_ohmic·mech/chem)"),
        ("LLI_pattern_score", "리튬 재고 손실 패턴", "공유 모드 — 전극 단정 금지"),
        ("PE_side_score / NE_side_score", "전극 가설 점수", "모드+부가증거 가중합"),
        ("Δ (PE−NE)", "상대 지배 lean", "구간 전환의 직접 트리거"),
        ("BOL OCP peaks", "하프셀 개방회로 피크", "full-cell 피크→PE attribution"),
        ("fade_exponent / knee", "페이드 지수·변곡", "수명 단계(조기/가속) 맥락"),
    ]
    fig.text(0.08, 0.90, "아래 파라미터가 세그먼트 라벨(PE/NE/mixed)을 실질적으로 결정한다.", fontproperties=fp(9))
    y = 0.86
    fig.text(0.08, y, "파라미터", fontproperties=fp(9, "bold"))
    fig.text(0.32, y, "의미", fontproperties=fp(9, "bold"))
    fig.text(0.58, y, "해석에서의 역할", fontproperties=fp(9, "bold"))
    y -= 0.025
    fig.lines.append(plt.Line2D([0.08, 0.92], [y + 0.01, y + 0.01], transform=fig.transFigure, color="#CCC"))
    for name, meaning, role in rows:
        y -= 0.055
        fig.text(0.08, y, name, fontproperties=fp(8, "bold"), color="#333")
        fig.text(0.32, y, meaning, fontproperties=fp(8), color="#444")
        fig.text(0.58, y, role, fontproperties=fp(8), color="#444")
    y -= 0.06
    draw_wrapped(
        fig, 0.08, y,
        "특히 Ch022에서 중기→후기 전환을 만든 것은 (1) contact_loss_score가 중기 0.6 전후로 "
        "고원(plateau)을 이룬 뒤, (2) 후기에 PE_side가 NE_side를 지속적으로 상회(Δ>0)한 조합이다. "
        "LAM_PE_pattern_score 단독 급증보다는, NE 측 점수가 상대적으로 완화되며 PE lean이 "
        "열리는 양상이다. Ch024는 초부터 PE lean이 있고 중기 NE 포켓이 짧다.",
        width=92, size=9,
    )
    pdf.savefig(fig)
    plt.close(fig)


def fig_sohq_and_sides(ax1, ax2, d: pd.DataFrame, segs: pd.DataFrame, cell: str):
    shade_segments(ax1, segs)
    ax1.plot(d["cycle"], d["SoHQ"], color=C_SOHQ, lw=2.0, label="SoHQ")
    ax1.set_ylabel("SoHQ (%)", fontproperties=fp(9))
    ax1.set_title(f"{cell} — 용량 유지율과 전극 가설 점수", fontproperties=fp(10, "bold"), loc="left")
    ax1.legend(prop=fp(8), loc="upper right", frameon=False)
    ax1.set_ylim(55, 105)
    ax1.grid(True, alpha=0.25)

    shade_segments(ax2, segs)
    ax2.plot(d["cycle"], d["PE_side_score"], color=C_PE, lw=2.0, label="PE_side")
    ax2.plot(d["cycle"], d["NE_side_score"], color=C_NE, lw=2.0, label="NE_side")
    ax2.plot(d["cycle"], d["shared_side_score"], color=C_SHARED, lw=1.2, ls="--", label="shared")
    ax2.axhline(0, color="#999", lw=0.5)
    ax2.set_xlabel("Cycle", fontproperties=fp(9))
    ax2.set_ylabel("Side score (0–1)", fontproperties=fp(9))
    ax2.legend(prop=fp(8), loc="upper left", ncol=3, frameon=False)
    ax2.set_ylim(0, 0.85)
    ax2.grid(True, alpha=0.25)
    for ax in (ax1, ax2):
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(fp(8))


def fig_modes_and_delta(ax1, ax2, d: pd.DataFrame, segs: pd.DataFrame, cell: str):
    shade_segments(ax1, segs)
    ax1.plot(d["cycle"], d["LAM_PE_pattern_score"], color=C_LAM, lw=2, label="LAM_PE")
    ax1.plot(d["cycle"], d["contact_loss_score"], color=C_CL, lw=2, label="contact_loss")
    ax1.plot(d["cycle"], d["LLI_pattern_score"], color="#9333EA", lw=1.3, ls="--", label="LLI")
    ax1.set_ylabel("Pattern score", fontproperties=fp(9))
    ax1.set_title(f"{cell} — 모드 점수 (패턴을 만든 파라미터)", fontproperties=fp(10, "bold"), loc="left")
    ax1.legend(prop=fp(8), loc="upper left", ncol=3, frameon=False)
    ax1.set_ylim(0, 0.9)
    ax1.grid(True, alpha=0.25)

    shade_segments(ax2, segs)
    ax2.fill_between(
        d["cycle"], 0, d["delta_PE_NE"],
        where=d["delta_PE_NE"] >= 0, color=C_PE, alpha=0.35, interpolate=True, label="PE lean (Δ>0)",
    )
    ax2.fill_between(
        d["cycle"], 0, d["delta_PE_NE"],
        where=d["delta_PE_NE"] < 0, color=C_NE, alpha=0.35, interpolate=True, label="NE lean (Δ<0)",
    )
    ax2.plot(d["cycle"], d["delta_PE_NE"], color="#222", lw=1.2)
    ax2.axhline(0.02, color=C_PE, ls=":", lw=1)
    ax2.axhline(-0.02, color=C_NE, ls=":", lw=1)
    ax2.set_xlabel("Cycle", fontproperties=fp(9))
    ax2.set_ylabel("Δ = PE − NE", fontproperties=fp(9))
    ax2.set_title("상대 지배 lean (구간 전환 트리거)", fontproperties=fp(10, "bold"), loc="left")
    ax2.legend(prop=fp(8), loc="lower right", frameon=False)
    ax2.grid(True, alpha=0.25)
    for ax in (ax1, ax2):
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(fp(8))


def page_cell_overview(pdf: PdfPages, cell: str, d: pd.DataFrame, segs: pd.DataFrame, narrative: str):
    fig = new_page(pdf, f"3. {cell} 개요 궤적")
    draw_wrapped(fig, 0.08, 0.91, narrative, width=95, size=8.5)
    gs = fig.add_gridspec(2, 1, left=0.10, right=0.95, top=0.78, bottom=0.08, hspace=0.28)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    fig_sohq_and_sides(ax1, ax2, d, segs, cell)
    # legend note for bands
    fig.text(0.10, 0.01, "배경 밴드: 분홍=상대 PE 지배 구간, 청록=상대 NE 지배 구간 (segment relative_dominant)", fontproperties=fp(7), color="#666")
    pdf.savefig(fig)
    plt.close(fig)


def page_cell_drivers(pdf: PdfPages, cell: str, d: pd.DataFrame, segs: pd.DataFrame, narrative: str):
    fig = new_page(pdf, f"4. {cell} — 결정 파라미터 시각화")
    draw_wrapped(fig, 0.08, 0.91, narrative, width=95, size=8.5)
    gs = fig.add_gridspec(2, 1, left=0.10, right=0.95, top=0.78, bottom=0.08, hspace=0.30)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    fig_modes_and_delta(ax1, ax2, d, segs, cell)
    pdf.savefig(fig)
    plt.close(fig)


def page_segment_table(pdf: PdfPages, cell: str, segs: pd.DataFrame, extra: str):
    fig = new_page(pdf, f"5. {cell} 구간별 해석표")
    draw_wrapped(fig, 0.08, 0.91, extra, width=95, size=8.5)
    y = 0.84
    headers = ["Seg", "Cycle", "SoHQ", "지배", "PE", "NE", "Δ", "LAM_PE", "contact", "LLI"]
    xs = [0.08, 0.14, 0.28, 0.40, 0.50, 0.58, 0.66, 0.74, 0.82, 0.90]
    for x, h in zip(xs, headers):
        fig.text(x, y, h, fontproperties=fp(7.5, "bold"))
    y -= 0.02
    for _, s in segs.iterrows():
        y -= 0.028
        if y < 0.08:
            break
        dom = str(s.get("relative_dominant") or "")
        color = C_PE if dom == "PE" else (C_NE if dom == "NE" else "#444")
        vals = [
            f"{int(s['segment'])}",
            f"{int(s['cycle_start'])}-{int(s['cycle_end'])}",
            f"{s['SoHQ_start']:.0f}→{s['SoHQ_end']:.0f}",
            dom,
            f"{s['PE_side_score_mean']:.2f}",
            f"{s['NE_side_score_mean']:.2f}",
            f"{s['PE_side_score_mean']-s['NE_side_score_mean']:+.2f}",
            f"{s['LAM_PE_mean']:.2f}",
            f"{s['contact_loss_mean']:.2f}",
            f"{s['LLI_mean']:.2f}" if pd.notna(s.get('LLI_mean')) else "-",
        ]
        for x, v in zip(xs, vals):
            fig.text(x, y, v, fontproperties=fp(7), color=color if x == xs[3] else "#222")
    pdf.savefig(fig)
    plt.close(fig)


def page_comparison(pdf: PdfPages, d22: pd.DataFrame, d24: pd.DataFrame):
    fig = new_page(pdf, "6. Ch022 vs Ch024 비교")
    gs = fig.add_gridspec(3, 1, left=0.10, right=0.95, top=0.88, bottom=0.08, hspace=0.35)
    ax0 = fig.add_subplot(gs[0])
    ax0.plot(d22["cycle"], d22["SoHQ"], color="#111", lw=2, label="Ch022 SoHQ")
    ax0.plot(d24["cycle"], d24["SoHQ"], color="#888", lw=2, ls="--", label="Ch024 SoHQ")
    ax0.set_ylabel("SoHQ (%)", fontproperties=fp(9))
    ax0.set_title("용량 fade 비교", fontproperties=fp(10, "bold"), loc="left")
    ax0.legend(prop=fp(8), frameon=False)
    ax0.grid(True, alpha=0.25)
    ax0.set_ylim(55, 105)

    ax1 = fig.add_subplot(gs[1])
    ax1.plot(d22["cycle"], d22["delta_PE_NE"], color=C_PE, lw=1.8, label="Ch022 Δ")
    ax1.plot(d24["cycle"], d24["delta_PE_NE"], color=C_NE, lw=1.8, label="Ch024 Δ")
    ax1.axhline(0, color="#999", lw=0.8)
    ax1.set_ylabel("Δ PE−NE", fontproperties=fp(9))
    ax1.set_title("전극 lean 비교 (양수=양극 우위)", fontproperties=fp(10, "bold"), loc="left")
    ax1.legend(prop=fp(8), frameon=False)
    ax1.grid(True, alpha=0.25)

    ax2 = fig.add_subplot(gs[2])
    ax2.plot(d22["cycle"], d22["contact_loss_score"], color=C_CL, lw=1.8, label="Ch022 contact")
    ax2.plot(d24["cycle"], d24["contact_loss_score"], color="#99C2C2", lw=1.8, ls="--", label="Ch024 contact")
    ax2.plot(d22["cycle"], d22["LAM_PE_pattern_score"], color=C_LAM, lw=1.5, label="Ch022 LAM_PE")
    ax2.plot(d24["cycle"], d24["LAM_PE_pattern_score"], color="#E8B989", lw=1.5, ls="--", label="Ch024 LAM_PE")
    ax2.set_xlabel("Cycle", fontproperties=fp(9))
    ax2.set_ylabel("Score", fontproperties=fp(9))
    ax2.set_title("결정 모드: contact_loss vs LAM_PE", fontproperties=fp(10, "bold"), loc="left")
    ax2.legend(prop=fp(7.5), ncol=2, frameon=False)
    ax2.grid(True, alpha=0.25)
    for ax in (ax0, ax1, ax2):
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(fp(8))
    pdf.savefig(fig)
    plt.close(fig)


def page_scatter_phase(pdf: PdfPages, d22: pd.DataFrame, d24: pd.DataFrame):
    fig = new_page(pdf, "7. 모드 공간에서의 궤적 (왜 그렇게 읽었는가)")
    draw_wrapped(
        fig, 0.08, 0.91,
        "가로축=contact_loss(NE 가설), 세로축=LAM_PE(PE 가설). 점이 우측으로 가면 음극 접촉 증거가 강하고, "
        "위로 가면 양극 LAM 패턴이 강하다. 색은 사이클(밝을수록 후기). Ch022는 중기에 우측(고 contact)으로 "
        "머문 뒤 후기에 상대적으로 위로/좌측으로 이동하며 PE lean이 열린다.",
        width=95, size=8.5,
    )
    gs = fig.add_gridspec(1, 2, left=0.08, right=0.95, top=0.78, bottom=0.18, wspace=0.28)
    for ax, d, title in (
        (fig.add_subplot(gs[0]), d22, "Ch022"),
        (fig.add_subplot(gs[1]), d24, "Ch024"),
    ):
        sc = ax.scatter(
            d["contact_loss_score"], d["LAM_PE_pattern_score"],
            c=d["cycle"], cmap="YlOrBr", s=28, alpha=0.85, edgecolors="none",
        )
        ax.set_xlabel("contact_loss (NE)", fontproperties=fp(9))
        ax.set_ylabel("LAM_PE (PE)", fontproperties=fp(9))
        ax.set_title(title, fontproperties=fp(10, "bold"))
        ax.set_xlim(0.2, 0.75)
        ax.set_ylim(0.0, 0.45)
        ax.grid(True, alpha=0.25)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(fp(8))
        cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label("cycle", fontproperties=fp(8))
        for t in cb.ax.get_yticklabels():
            t.set_fontproperties(fp(7))
    pdf.savefig(fig)
    plt.close(fig)


def page_interpretation_ch022(pdf: PdfPages):
    fig = new_page(pdf, "8. Ch022 — 해석 스토리 (상황 설명)")
    text = (
        "단계 A · 형성~조기 (≈2–70)\n"
        "SoHQ는 100%→93%로 완만. PE/NE 점수가 모두 낮고 Δ가 ±0.05 안에서 흔들린다. "
        "이 구간은 ‘어느 전극이 지배적’이라기보다 기준선 확립과 약한 초기 신호 단계다. "
        "40–70에서 일시적 PE lean이 보이지만 contact_loss는 아직 0.4 미만이다.\n\n"
        "단계 B · 중기 음극 지배 (≈80–380) — 가장 중요한 구간\n"
        "cycle 80 부근에서 contact_loss가 ~0.67로 점프하고, 이후 중기 대부분 0.6대를 유지한다. "
        "동시에 NE_side가 PE_side를 지속 상회(Δ≈−0.08~−0.20). ASSB Si-rich 정책상 "
        "이 패턴을 ‘음극 기계적 접촉 손실 가설이 우세’로 읽는다. "
        "구속 압력 로그가 없어 절대 원인 단정은 불가하나, R_ohmic/mech 계열 증거가 "
        "NE 버킷에 매핑되어 점수가 올라간 상황이다. LLI도 중기 후반 상승해 공유 모드가 "
        "병행되지만, lean의 부호를 바꾼 주인공은 contact_loss다.\n\n"
        "단계 C · 전환 (~390)\n"
        "cycle 390 전후 Δ가 음→양으로 바뀐다. contact_loss가 소폭 완화(0.6→0.5대)되고 "
        "PE_side가 0.48–0.53으로 올라가 PE lean이 열린다. ‘양극이 갑자기 나빠졌다’기보다 "
        "음극 측 상대 증거가 한 풀 꺾이며 양극 패턴이 전면에 드러난 전환으로 해석한다.\n\n"
        "단계 D · 후기 양극 우위 (≈390–550) & EOL\n"
        "SoHQ 76%→66%. PE lean이 유지되며 LAM_PE pattern은 ~0.31로 고원. "
        "EOL(560+)에서는 Δ가 다시 소폭 음으로 돌아가 마진이 작아진다 — 후기에도 "
        "양·음극 신호가 공존함을 보여 주며, 단정 대신 ‘후기 PE 우세 후 EOL 근소 혼합’으로 기술한다."
    )
    draw_wrapped(fig, 0.08, 0.90, text, width=92, size=9)
    pdf.savefig(fig)
    plt.close(fig)


def page_interpretation_ch024(pdf: PdfPages):
    fig = new_page(pdf, "9. Ch024 — 해석 스토리 (상황 설명)")
    text = (
        "단계 A · 초반 양극 경향 (≈2–90)\n"
        "Ch022와 달리 초반부터 PE_side가 NE_side보다 높은 구간이 많다(Δ>0). "
        "SoHQ 100%→92%. LAM_PE와 contact가 동시에 완만히 오르지만 lean은 PE 쪽이다.\n\n"
        "단계 B · 중기 혼재 + 짧은 NE 포켓 (≈100–350)\n"
        "100–230은 PE↔NE가 교차하는 mixed. 240–260과 340–350에서 contact_loss가 "
        "올라가 NE 지배가 명확해지는 ‘포켓’이 생긴다. Ch022의 긴 NE 고원(~300 cyc)과 "
        "비교하면 Ch024의 음극 우위는 짧고 단속적이다.\n\n"
        "단계 C · 후기 양극 (~360–EOL)\n"
        "≈360 이후 Δ가 다시 양수로 기울고 PE 상대 지배가 이어진다. SoHQ 74%→64%. "
        "수명 롤업도 early PE · mid NE 근소 · late PE로, Ch022와 ‘후기 PE’는 공유하되 "
        "중기 NE의 길이·강도가 다르다.\n\n"
        "셀 간 함의\n"
        "동일 화학(SJ900)·유사 fade 깊이(~65% SoHQ)에서도 전극 lean 타임라인이 다르다. "
        "이는 full-cell 패턴 진단이 셀별 기구 서사를 구분할 수 있음을 시사하나, "
        "압력·온도·로트 공변량이 비어 있어 원인 단정은 보류한다. aged 하프셀이 오면 "
        "이 lean을 절대 LAM_PE/NE%로 검증하는 것이 다음 단계다."
    )
    draw_wrapped(fig, 0.08, 0.90, text, width=92, size=9)
    pdf.savefig(fig)
    plt.close(fig)


def page_limits(pdf: PdfPages):
    fig = new_page(pdf, "10. 한계 · 금지 해석 · 다음 실험")
    text = (
        "하지 말아야 할 해석\n"
        "• 본 리포트의 PE/NE 점수를 LAM_PE=xx%, LAM_NE=yy% 같은 절대량으로 인용하지 말 것.\n"
        "• Si-rich에서 full-cell 피크만으로 LAM_NE를 확정하지 말 것 (정책 금지).\n"
        "• Temp 컬럼이 0이므로 Arrhenius/DTV 보정 결과를 끼워 넣지 말 것.\n"
        "• contact_loss를 ‘구속 압력 부족’으로 단정하지 말 것 — 압력 로그 없음.\n\n"
        "신뢰도를 올리는 다음 데이터\n"
        "1) Aged/harvested 하프셀 OCP → *_est_hc_calibrated / DMA quantify\n"
        "2) 구속 압력 시계열 → contact_loss 해석의 인과 고리\n"
        "3) 온도 로그 export 복구 → 셀 간 비교·정규화\n"
        "4) §5.1 dQ/dV 필터 스윕 verdict → 피크 경로 확정 후 deconv\n\n"
        "재현 방법\n"
        "PYTHONPATH=. python3 cyclediag/tools/diagnose_electrode_segments.py \\\n"
        "  --input example/fixtures/raw/set4_SJ900/M01Ch022_raw.csv \\\n"
        "  --out-dir example/output/electrode_segments\n"
        "본 PDF: cyclediag/tools/build_electrode_diagnosis_pdf.py"
    )
    draw_wrapped(fig, 0.08, 0.90, text, width=92, size=9)
    pdf.savefig(fig)
    plt.close(fig)


def phase_means(d: pd.DataFrame) -> str:
    d = d.dropna(subset=["SoHQ"])
    n = len(d)
    parts = []
    for name, sl in (
        ("early", d.iloc[: n // 3]),
        ("mid", d.iloc[n // 3 : 2 * n // 3]),
        ("late", d.iloc[2 * n // 3 :]),
    ):
        pe, ne = sl["PE_side_score"].mean(), sl["NE_side_score"].mean()
        winner = "PE" if pe >= ne else "NE"
        parts.append(
            f"{name}: PE={pe:.2f}/NE={ne:.2f}→{winner} "
            f"(SoHQ {sl['SoHQ'].iloc[0]:.0f}→{sl['SoHQ'].iloc[-1]:.0f}%)"
        )
    return " · ".join(parts)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)
    out_pdf = OUT_DIR / "ASSB_SJ900_Ch022_Ch024_electrode_diagnosis_report.pdf"
    art_pdf = ART_DIR / "ASSB_SJ900_Ch022_Ch024_electrode_diagnosis_report.pdf"

    d22, s22 = load_cell("M01Ch022")
    d24, s24 = load_cell("M01Ch024")

    with PdfPages(out_pdf) as pdf:
        page_cover(pdf)
        page_methods(pdf)
        page_param_catalog(pdf)
        page_cell_overview(
            pdf, "M01Ch022", d22, s22,
            f"샘플 {len(d22)} capa-like cycles. {phase_means(d22)}. "
            "중기 NE(contact_loss) 고원 후 ~390에서 PE lean 전환이 핵심 서사.",
        )
        page_cell_drivers(
            pdf, "M01Ch022", d22, s22,
            "상단: LAM_PE vs contact_loss vs LLI. 하단: Δ=PE−NE (구간 전환 트리거). "
            "중기 Δ<0이 길고, 후기 Δ>0으로 바뀌는 것이 ‘음극→양극’ 해석의 직접 근거.",
        )
        page_segment_table(
            pdf, "M01Ch022", s22,
            "relative_dominant 기준. 강도는 |Δ|≈dominance_margin_mean 참고 (표의 Δ열).",
        )
        page_cell_overview(
            pdf, "M01Ch024", d24, s24,
            f"샘플 {len(d24)} capa-like cycles. {phase_means(d24)}. "
            "초·후기 PE 경향, 중기 NE 포켓이 Ch022보다 짧다.",
        )
        page_cell_drivers(
            pdf, "M01Ch024", d24, s24,
            "Ch024는 contact_loss 고원이 Ch022만큼 길지 않고, Δ 부호 반전이 더 빈번(혼재)하다.",
        )
        page_segment_table(
            pdf, "M01Ch024", s24,
            "Seg5·8이 짧은 NE 명확 구간, Seg9–11이 후기 PE 구간.",
        )
        page_comparison(pdf, d22, d24)
        page_scatter_phase(pdf, d22, d24)
        page_interpretation_ch022(pdf)
        page_interpretation_ch024(pdf)
        page_limits(pdf)

        meta = pdf.infodict()
        meta["Title"] = "ASSB SJ900 Ch022/Ch024 Electrode-side Diagnosis Report"
        meta["Author"] = "CycleDiag"
        meta["Subject"] = "hypothesis_bol_ocp PE/NE segment diagnosis"
        meta["Keywords"] = "ASSB, SJ900, LAM_PE, contact_loss, electrode diagnosis"

    # also copy to artifacts
    art_pdf.write_bytes(out_pdf.read_bytes())
    print(f"wrote {out_pdf}")
    print(f"wrote {art_pdf}")
    print(f"pages ~14, size={out_pdf.stat().st_size/1024:.1f} KiB")


if __name__ == "__main__":
    main()
