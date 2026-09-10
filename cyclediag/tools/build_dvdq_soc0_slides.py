"""Rebuild dVdQ@SOC0 figures and pack them into a widescreen PowerPoint.

Regenerates the Aug 2026 figure set (PNG files were not kept) from tagged
feature tables plus raw cycler CSVs, then writes one compilation deck.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": True,
})
import numpy as np
import pandas as pd

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from cyclediag.tools.run_dvdq_soc0_arm_plots import (
    CELL_COLOR as ARM_CELL_COLOR,
    dchg_qv,
    dvdq_soc0_profile,
    load_bps,
    load_raw,
    plot_arm,
    plot_cell_triple,
    style,
    tagged_routine_cycles,
)

ROOT = Path(__file__).resolve().parents[2]
FIG_DPI = 160
STEP = 20

OVERLAY_COLOR = {
    "M01Ch022": "#1f77b4",
    "M01Ch024": "#d62728",
    "M01Ch025": "#2ca02c",
    "M01Ch010": "#1f77b4",
    "M01Ch011": "#d62728",
    "M01Ch012": "#2ca02c",
}
PANEL_CELLS = {
    "SJ900": [
        ("M01Ch022", ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv"),
        ("M01Ch024", ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv"),
        ("M01Ch025", ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv"),
    ],
    "SJ1300": [
        ("M01Ch010", ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv"),
        ("M01Ch011", ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv"),
        ("M01Ch012", ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv"),
    ],
}
NAVY = RGBColor(0x15, 0x32, 0x5B)
TEAL = RGBColor(0x0D, 0x73, 0x73)
INK = RGBColor(0x1F, 0x29, 0x37)
MUTED = RGBColor(0x4B, 0x55, 0x63)
LINE = RGBColor(0xD0, 0xD7, 0xDE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _font(run, *, size: float, bold: bool = False, color=INK, name: str = "Malgun Gothic") -> None:
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    rpr = run._r.get_or_add_rPr()
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = rpr.makeelement(qn("a:ea"), {})
        rpr.append(ea)
    ea.set("typeface", name)


def add_text(slide, l, t, w, h, text, *, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    _font(run, size=size, bold=bold, color=color)
    return box


def add_bar(slide, l, t, w, h, color) -> None:
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, l, t, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def add_picture_fit(slide, path: Path, l, t, w, h) -> None:
    pic = slide.shapes.add_picture(str(path), l, t, w, h)
    # Keep aspect: shrink to fit inside the box.
    pw, ph = pic.width, pic.height
    # python-pptx already stretched to w×h; reset by native aspect if needed.
    from PIL import Image

    with Image.open(path) as im:
        iw, ih = im.size
    target_aspect = float(w) / float(h)
    img_aspect = iw / ih
    if img_aspect > target_aspect:
        new_h = int(w / img_aspect)
        pic.width = w
        pic.height = new_h
        pic.top = t + (h - new_h) // 2
        pic.left = l
    else:
        new_w = int(h * img_aspect)
        pic.height = h
        pic.width = new_w
        pic.left = l + (w - new_w) // 2
        pic.top = t


def header_slide(prs, title: str, subtitle: str) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bar(slide, 0, 0, SLIDE_W, Inches(0.12), TEAL)
    add_bar(slide, 0, Inches(0.12), SLIDE_W, Inches(2.15), NAVY)
    add_text(slide, Inches(0.7), Inches(0.45), Inches(12), Inches(0.4),
             "cyclediag  ·  Si/Gr 열화 메커니즘", size=14, bold=True, color=RGBColor(0x9E, 0xD8, 0xD8))
    add_text(slide, Inches(0.7), Inches(0.90), Inches(12), Inches(0.9),
             title, size=32, bold=True, color=WHITE)
    add_text(slide, Inches(0.7), Inches(1.80), Inches(12), Inches(0.35),
             subtitle, size=14, color=RGBColor(0xC5, 0xD4, 0xE8))
    return slide


def content_slide(prs, title: str, note: str = ""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bar(slide, 0, 0, SLIDE_W, Inches(0.08), TEAL)
    add_bar(slide, 0, Inches(0.08), SLIDE_W, Inches(0.62), NAVY)
    add_text(slide, Inches(0.35), Inches(0.14), Inches(12.6), Inches(0.48),
             title, size=20, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    if note:
        add_text(slide, Inches(0.35), Inches(7.18), Inches(12.6), Inches(0.26),
                 note, size=10, color=MUTED)
    return slide


def downsample(x: np.ndarray, y: np.ndarray, n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    if len(x) <= n:
        return x, y
    idx = np.linspace(0, len(x) - 1, n).astype(int)
    return x[idx], y[idx]


def plot_overlays(tagged: pd.DataFrame, arm_label: str, out: Path, cells: list[str]) -> Path:
    metrics = [
        ("dchg_dVdQ_SOC0", "|dV/dQ| @ SOC0  [V/Ah]", "dVdQ_SOC0"),
        ("dchg_dVdQ_SOC0_to_mid_ratio", "SOC0 / mid  ratio", "SOC0_to_mid"),
        ("dchg_Q_cliff_abs", "Q_cliff_abs  [Ah]", "Q_cliff_abs"),
        ("dchg_dVdQ_at_Qabs_5", "|dV/dQ| at Qmax−5 Ah  [V/Ah]", "dVdQ_Qabs5"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.4))
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.08, top=0.90, hspace=0.32, wspace=0.22)
    for ax, (col, ylab, _) in zip(axes.ravel(), metrics):
        for cell in cells:
            g = tagged[tagged["cell_id"] == cell].sort_values("tagged_cycle")
            if g.empty or col not in g.columns:
                continue
            x = pd.to_numeric(g["tagged_cycle"], errors="coerce")
            y = pd.to_numeric(g[col], errors="coerce")
            m = np.isfinite(x) & np.isfinite(y)
            ax.plot(x[m], y[m], color=OVERLAY_COLOR[cell], lw=1.7, label=cell)
        ax.set_xlabel("Tagged cycle #")
        ax.set_ylabel(ylab)
        ax.set_title(ylab.split("  [")[0], fontweight="bold", fontsize=11)
        ax.legend(fontsize=8)
        style(ax)
    fig.suptitle(f"{arm_label} — dVdQ@SOC0 family (tagged / routine)", fontweight="bold", fontsize=13)
    path = out / f"{arm_label}_dvdq_soc0_family_overlay_tagged.png"
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)
    return path


def collect_panel_profiles(raw: pd.DataFrame, tagged: list[int]) -> list[dict]:
    profiles = []
    t_list = sorted(set([1] + list(range(STEP, len(tagged) + 1, STEP)) + [len(tagged)]))
    for tidx in t_list:
        rcyc = tagged[tidx - 1]
        q, v = dchg_qv(raw, rcyc)
        if q is None:
            continue
        prof = dvdq_soc0_profile(q, v)
        if prof is None:
            continue
        qx, ydq, samp = prof
        q, v = downsample(q, v)
        qx, ydq = downsample(qx, ydq)
        profiles.append(dict(tidx=tidx, rcyc=rcyc, q=q, v=v, qx=qx, ydq=ydq, samp=samp))
    return profiles


def plot_cell_vq_panels(
    cell_id: str,
    arm: str,
    profiles: list[dict],
    traj: pd.DataFrame,
    lims: dict,
    out: Path,
) -> Path:
    fig, axes = plt.subplots(3, 1, figsize=(11.6, 8.6))
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.06, top=0.90, hspace=0.34)
    nseg = max(len(profiles) - 1, 1)
    ax = axes[0]
    for k, p in enumerate(profiles):
        color = cm.viridis(k / nseg)
        ax.plot(p["q"], p["v"], color=color, lw=1.35, label=f"t{p['tidx']}/c{p['rcyc']}")
    ax.set_xlabel("Q [Ah]")
    ax.set_ylabel("V [V]")
    ax.set_title("Discharge V–Q  (every 20 tagged)", fontweight="bold")
    ax.set_xlim(*lims["q"])
    ax.set_ylim(*lims["v"])
    ax.legend(loc="lower left", ncol=4, fontsize=6.4, framealpha=0.90)
    style(ax)

    ax = axes[1]
    for k, p in enumerate(profiles):
        color = cm.viridis(k / nseg)
        ax.plot(p["qx"], p["ydq"], color=color, lw=1.35)
        samp = p["samp"]
        if samp.get("Q") is not None and samp.get("intensity") is not None:
            ax.scatter([samp["Q"]], [samp["intensity"]], s=36, color=color,
                       edgecolors="k", linewidths=0.35, zorder=5)
    ax.axhline(0, color="k", lw=0.6, alpha=0.35)
    ax.set_xlabel("Q [Ah]")
    ax.set_ylabel("signed dV/dQ [V/Ah]")
    ax.set_title("signed dV/dQ  ·  dots = SOC0", fontweight="bold")
    ax.set_xlim(*lims["q"])
    ax.set_ylim(*lims["dvdq"])
    style(ax)

    ax = axes[2]
    x = pd.to_numeric(traj["tagged_cycle"], errors="coerce")
    y = np.abs(pd.to_numeric(traj["dchg_dVdQ_SOC0"], errors="coerce"))
    m = np.isfinite(x) & np.isfinite(y)
    ax.plot(x[m], y[m], color="#1565c0", lw=1.8)
    ax.set_xlabel("Tagged cycle #")
    ax.set_ylabel("|dV/dQ| @ SOC0 [V/Ah]")
    ax.set_title("|dV/dQ| @ SOC0 vs tagged cycle", fontweight="bold")
    ax.set_xlim(*lims["t"])
    ax.set_ylim(*lims["soc0"])
    style(ax)

    fig.suptitle(f"{arm} / {cell_id} — V–Q · dV/dQ · SOC0", fontweight="bold", fontsize=13)
    path = out / f"{cell_id}_VQ_dvdq_SOC0_panels.png"
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)
    return path


def set_limits(bundle: list[tuple[str, list[dict], pd.DataFrame]]) -> dict:
    qs, vs, dqs, ts, s0 = [], [], [], [], []
    for _, profiles, traj in bundle:
        for p in profiles:
            qs.extend([float(np.nanmin(p["q"])), float(np.nanmax(p["q"]))])
            vs.extend([float(np.nanpercentile(p["v"], 1)), float(np.nanpercentile(p["v"], 99))])
            dqs.extend([float(np.nanpercentile(p["ydq"], 2)), float(np.nanpercentile(p["ydq"], 98))])
            if p["samp"].get("intensity") is not None:
                dqs.append(float(p["samp"]["intensity"]))
        x = pd.to_numeric(traj["tagged_cycle"], errors="coerce")
        y = np.abs(pd.to_numeric(traj["dchg_dVdQ_SOC0"], errors="coerce"))
        m = np.isfinite(x) & np.isfinite(y)
        if m.any():
            ts.extend([float(x[m].min()), float(x[m].max())])
            s0.extend([float(y[m].min()), float(y[m].max())])
    def pad(lo, hi, frac=0.06):
        span = hi - lo if hi > lo else 1.0
        return lo - frac * span, hi + frac * span
    return {
        "q": pad(min(qs), max(qs), 0.03),
        "v": pad(min(vs), max(vs), 0.04),
        "dvdq": pad(min(dqs), max(dqs), 0.08),
        "t": pad(min(ts), max(ts), 0.02),
        "soc0": pad(min(s0), max(s0), 0.08),
    }


def existing_paths(fig_dir: Path) -> dict[str, Path]:
    arm_dir = fig_dir / "arm"
    paths = {
        "overlay_sj900": fig_dir / "SJ900_dvdq_soc0_family_overlay_tagged.png",
        "overlay_sj1300": fig_dir / "SJ1300_dvdq_soc0_family_overlay_tagged.png",
        "arm": arm_dir / "00_arm_dvdq_SOC0_inc_vs_t1.png",
        "triple_022": arm_dir / "M01Ch022_dvdq_SOC0_triple.png",
        "triple_012": arm_dir / "M01Ch012_dvdq_SOC0_triple.png",
    }
    for cell in ("M01Ch022", "M01Ch024", "M01Ch025", "M01Ch010", "M01Ch011", "M01Ch012"):
        paths[f"panel_{cell}"] = fig_dir / f"{cell}_VQ_dvdq_SOC0_panels.png"
    return paths


def rebuild_figures(fig_dir: Path, *, skip_raw: bool = False) -> dict[str, Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    sj900 = pd.read_csv(ROOT / "example/output/set4/dvdq_soc0/SJ900_dvdq_soc0_tagged.csv")
    sj1300 = pd.read_csv(ROOT / "example/output/SJ1300_dry/dvdq_soc0/SJ1300_dvdq_soc0_tagged.csv")
    paths["overlay_sj900"] = plot_overlays(sj900, "SJ900", fig_dir, ["M01Ch022", "M01Ch024", "M01Ch025"])
    paths["overlay_sj1300"] = plot_overlays(sj1300, "SJ1300", fig_dir, ["M01Ch010", "M01Ch011", "M01Ch012"])
    print("overlays done", flush=True)
    if skip_raw:
        reused = existing_paths(fig_dir)
        reused.update(paths)
        missing = [k for k, v in reused.items() if not v.exists()]
        if missing:
            raise FileNotFoundError(f"skip-raw missing figures: {missing}")
        return reused

    arm_dir = fig_dir / "arm"
    arm_dir.mkdir(exist_ok=True)
    src_arm = ROOT / "example/output/crossover_vs_sohq/present_1600x1000/dvdq_soc0_arm"
    frames = []
    raws = {}
    for cell_id, raw_path, arm in (
        ("M01Ch022", ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch022_raw.csv", "set4_SJ900"),
        ("M01Ch024", ROOT / "example/fixtures/doe/DOE1/set4_SJ900/M01Ch024_raw.csv", "set4_SJ900"),
        ("M01Ch010", ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch010_raw.csv", "SJ1300_dry"),
        ("M01Ch011", ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch011_raw.csv", "SJ1300_dry"),
        ("M01Ch012", ROOT / "example/fixtures/doe/DOE2/SJ1300_dry/M01Ch012_raw.csv", "SJ1300_dry"),
    ):
        print(f"[{cell_id}] load raw for arm/panels …", flush=True)
        csv = src_arm / f"{cell_id}_dvdq_SOC0.csv"
        df = pd.read_csv(csv)
        frames.append(df)
        raw = load_raw(raw_path)
        tagged = tagged_routine_cycles(raw)
        raws[cell_id] = (raw, tagged, arm)
        if cell_id in ("M01Ch022", "M01Ch012"):
            plot_cell_triple(cell_id, arm, raw, tagged, df, arm_dir, vq_step=50)
    arm_png = arm_dir / "00_arm_dvdq_SOC0_inc_vs_t1.png"
    plot_arm(frames, raws, arm_png, vq_step=50)
    paths["arm"] = arm_png
    paths["triple_022"] = arm_dir / "M01Ch022_dvdq_SOC0_triple.png"
    paths["triple_012"] = arm_dir / "M01Ch012_dvdq_SOC0_triple.png"
    print("arm plots done", flush=True)

    tagged_by_cell = {
        "M01Ch022": sj900,
        "M01Ch024": sj900,
        "M01Ch025": sj900,
        "M01Ch010": sj1300,
        "M01Ch011": sj1300,
        "M01Ch012": sj1300,
    }
    for set_name, cells in PANEL_CELLS.items():
        bundle = []
        for cell_id, raw_path in cells:
            print(f"[{cell_id}] 3-panel profiles …", flush=True)
            if cell_id in raws:
                raw, tagged, _ = raws[cell_id]
            else:
                raw = load_raw(raw_path)
                tagged = tagged_routine_cycles(raw)
            profiles = collect_panel_profiles(raw, tagged)
            traj = tagged_by_cell[cell_id]
            traj = traj[traj["cell_id"] == cell_id].copy()
            bundle.append((cell_id, profiles, traj))
        lims = set_limits(bundle)
        for cell_id, profiles, traj in bundle:
            key = f"panel_{cell_id}"
            paths[key] = plot_cell_vq_panels(cell_id, set_name, profiles, traj, lims, fig_dir)
    print("3-panels done", flush=True)
    return paths


def _set_slide_size(prs: Presentation) -> None:
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H


def figure_slide(prs, title: str, image: Path, note: str = "", *, left=0.35, top=0.82, width=12.6, height=6.25) -> None:
    slide = content_slide(prs, title, note)
    add_picture_fit(slide, image, Inches(left), Inches(top), Inches(width), Inches(height))


def two_figure_slide(prs, title: str, left_img: Path, right_img: Path, left_cap: str, right_cap: str, note: str = "") -> None:
    slide = content_slide(prs, title, note)
    add_text(slide, Inches(0.35), Inches(0.78), Inches(6.2), Inches(0.28), left_cap, size=12, bold=True, color=TEAL)
    add_text(slide, Inches(6.8), Inches(0.78), Inches(6.2), Inches(0.28), right_cap, size=12, bold=True, color=TEAL)
    add_picture_fit(slide, left_img, Inches(0.30), Inches(1.08), Inches(6.35), Inches(5.95))
    add_picture_fit(slide, right_img, Inches(6.70), Inches(1.08), Inches(6.35), Inches(5.95))


def build_pptx(paths: dict[str, Path], out: Path) -> Path:
    prs = Presentation()
    _set_slide_size(prs)

    cover = header_slide(
        prs,
        "dV/dQ @ SOC0로 본 Si/Gr 열화",
        "SJ900 (Si 적음)  vs  SJ1300 (Si 많음)   ·   tagged routine only   ·   2026-08 작업 복원",
    )
    bullets = [
        "방전 끝단(SOC≈0, 저전압 Si 꼬리)의 dV/dQ를 뽑아 H1(Si만 소실) / H2(Si+Gr 동반)를 가르려 한 세트입니다.",
        "dchg_dVdQ_SOC0 단독은 SOC 정규화 때문에 판별력이 약하고, SOC0/mid 비와 Q_cliff_abs가 더 쓸모 있었습니다.",
        "그림은 당시 PNG가 없어서 tagged CSV + raw에서 같은 계약으로 다시 그렸습니다.",
    ]
    y = 2.55
    for b in bullets:
        add_text(cover, Inches(0.75), Inches(y), Inches(11.8), Inches(0.55), "•  " + b, size=15, color=INK)
        y += 0.62
    add_text(cover, Inches(0.75), Inches(4.70), Inches(11.8), Inches(0.35),
             "셀 구성", size=13, bold=True, color=NAVY)
    add_text(cover, Inches(0.75), Inches(5.05), Inches(11.8), Inches(1.4),
             "SJ900 set4   Ch022 · Ch024 · Ch025 (Ch025는 수명 짧음, arm 비교에서는 제외)\n"
             "SJ1300 dry   Ch010 · Ch011 · Ch012\n"
             "대표 프로파일   900 = Ch022    1300 = Ch012",
             size=14, color=INK)

    def_slide = content_slide(prs, "지표 정의", "방전 곡선 저전압(Si 꼬리·고갈) 쪽을 보는 양. 절대 Ah와 SOC 정규화를 섞지 말 것.")
    cards = [
        ("dchg_dVdQ_SOC0", "방전 종료점 |dV/dQ|",
         "SOC≈0 창(끝 2%)의 기울기. 끝단이 가팔라지면 커짐. SOC%로 정규화되어 H1/H2 단독 판별은 약함."),
        ("SOC0_to_mid_ratio", "끝단 ÷ 중반 기울기",
         "|dV/dQ|@SOC0  /  |dV/dQ|@SOC 40–60%. 끝단만 뾰족해지면 상승 → H1 방향."),
        ("Q_cliff_abs", "cliff 시작 절대 Ah",
         "중반 대비 |dV/dQ|가 확 커지는 첫 Q. 대략 Gr 구간 길이(C_Gr) 프록시. H1이면 거의 고정, H2면 감소."),
        ("|dV/dQ| at Qmax−5 Ah", "끝에서 5 Ah 고정점",
         "사이클마다 SOC%로 다시 나누지 않음. 고갈 cliff가 그 지점에 가까워지면 값이 커짐."),
    ]
    for i, (name, one, body) in enumerate(cards):
        col, row = i % 2, i // 2
        l = Inches(0.35 + col * 6.5)
        t = Inches(0.95 + row * 2.95)
        box = def_slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, l, t, Inches(6.25), Inches(2.70))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(0xF4, 0xF7, 0xFA)
        box.line.color.rgb = LINE
        add_text(def_slide, l + Inches(0.22), t + Inches(0.18), Inches(5.8), Inches(0.32),
                 name, size=12, bold=True, color=TEAL)
        add_text(def_slide, l + Inches(0.22), t + Inches(0.52), Inches(5.8), Inches(0.40),
                 one, size=16, bold=True, color=NAVY)
        add_text(def_slide, l + Inches(0.22), t + Inches(1.05), Inches(5.8), Inches(1.40),
                 body, size=13, color=INK)

    figure_slide(
        prs,
        "Arm 비교  3×2  —  signed dV/dQ · SOC0 · inc% vs t1",
        paths["arm"],
        "상단: 50 tagged마다 곡선 + SOC0 점 (900=Ch022, 1300=Ch012).  중단: 셀별 SOC0.  하단: t1 대비 증감%.  행마다 y축 공유.",
        top=0.78, height=6.35,
    )
    two_figure_slide(
        prs,
        "대표 셀 3단  —  dV/dQ 프로파일 · SOC0 궤적 · inc%",
        paths["triple_022"],
        paths["triple_012"],
        "SJ900  Ch022",
        "SJ1300  Ch012",
        "R60 arm과 같은 3단. 점선/파선은 SoHQ breakpoint.",
    )
    two_figure_slide(
        prs,
        "Family overlay  —  tagged routine",
        paths["overlay_sj900"],
        paths["overlay_sj1300"],
        "SJ900  Ch022 / 024 / 025",
        "SJ1300  Ch010 / 011 / 012",
        "같은 네 지표. SOC0 단독보다 SOC0/mid · Q_cliff_abs가 H1/H2 방향에 유리.",
    )

    for cell, arm in (
        ("M01Ch022", "SJ900"),
        ("M01Ch024", "SJ900"),
        ("M01Ch025", "SJ900"),
        ("M01Ch010", "SJ1300"),
        ("M01Ch011", "SJ1300"),
        ("M01Ch012", "SJ1300"),
    ):
        figure_slide(
            prs,
            f"{arm}  {cell}  —  V–Q / signed dV/dQ+SOC0 / |dV/dQ|@SOC0",
            paths[f"panel_{cell}"],
            "패널 1·2: tagged 20사이클 간격.  패널 2: 부호 유지.  패널 3: 절댓값.  축은 세트(SJ900 / SJ1300) 안에서 통일.",
            top=0.78, height=6.35,
        )

    summary = content_slide(prs, "당시 판정 요약", "출처: example/output/si_gr_mechanism/mechanism_summary.csv  (말기 RPT)")
    rows = [
        ("Arm", "Cell", "mechanism", "Q_cliff_abs", "메모"),
        ("SJ900", "Ch022", "H1_dominant", "26.3 Ah", "Si만 빠지는 쪽에 가장 가까움"),
        ("SJ900", "Ch024", "H2_dominant", "27.6 Ah", "Gr 구간도 같이 줄어듦"),
        ("SJ900", "Ch025", "H2_dominant", "43.8 Ah", "tagged ~134, 짧은 수명"),
        ("SJ1300", "Ch010", "H2_dominant", "11.8 Ah", "cliff가 SJ900보다 짧음"),
        ("SJ1300", "Ch011", "H2_dominant", "13.1 Ah", ""),
        ("SJ1300", "Ch012", "H2_dominant", "—", "cliff null"),
    ]
    table = summary.shapes.add_table(len(rows), 5, Inches(0.45), Inches(0.95), Inches(12.4), Inches(3.55)).table
    widths = [1.6, 1.5, 2.4, 2.2, 4.7]
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 4 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = val
            _font(run, size=12, bold=(r == 0), color=WHITE if r == 0 else INK)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = NAVY
            elif r % 2:
                cell.fill.fore_color.rgb = RGBColor(0xF4, 0xF7, 0xFA)
            else:
                cell.fill.fore_color.rgb = WHITE
    add_text(summary, Inches(0.45), Inches(4.70), Inches(12.4), Inches(2.2),
             "읽는 법\n"
             "• H1: Q_cliff_abs가 거의 안 줄고, SOC0/mid가 커짐 (끝단 Si 꼬리만 사라짐).\n"
             "• H2: Q_cliff_abs가 줄고 Gr 구간도 같이 짧아짐. SJ1300 세 셀이 이쪽.\n"
             "• 곡선 정합(fit_s/o/dR, fade_ratio_Si_Gr)은 당시 RPT 방전에서 돌지 않아 null. 판정은 cliff·SOC0/mid 중심.\n"
             "• Arm 그림에서 SJ900 SOC0 크기는 EOL까지 대체로 커지고(+), SJ1300은 작아지거나 약해짐.",
             size=13, color=INK)

    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=ROOT / "example/output/dvdq_soc0_slides")
    p.add_argument("--skip-raw", action="store_true", help="Reuse existing arm/3-panel PNGs")
    p.add_argument(
        "--origin-ole",
        action="store_true",
        help="Also build Origin OLE PPT (requires Origin 2025 + PowerPoint)",
    )
    p.add_argument("--skip-profiles", action="store_true", help="Origin OLE: skip V-Q/dV/dQ curve graphs")
    args = p.parse_args()
    out_dir = args.out_dir
    fig_dir = out_dir / "figures"
    paths = rebuild_figures(fig_dir, skip_raw=args.skip_raw)
    ppt = build_pptx(paths, out_dir / "dVdQ_SOC0_SJ900_SJ1300.pptx")
    print(f"wrote {ppt}")
    if args.origin_ole:
        from cyclediag.origin_ppt.build_slides import build as build_ole

        ole = out_dir / "dVdQ_SOC0_SJ900_SJ1300_ole.pptx"
        build_ole(ole, skip_profiles=args.skip_profiles)
        print(f"wrote {ole}")


if __name__ == "__main__":
    main()
