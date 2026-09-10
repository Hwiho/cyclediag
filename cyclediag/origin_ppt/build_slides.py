"""Build dVdQ@SOC0 Origin OLE PowerPoint.

    python -m cyclediag.origin_ppt --out example/output/dvdq_soc0_slides/dVdQ_SOC0_SJ900_SJ1300_ole.pptx

Needs Origin 2025, originpro, pywin32, pandas, python-pptx.
Shell is the AX 16:9 template when present; graphs are Origin OLE (origin95.graph).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path

import win32com.client

from .config import (
    ARM_CELLS,
    AX_TEMPLATE,
    BODY_HEIGHT,
    BODY_LEFT,
    BODY_TOP,
    BODY_WIDTH,
    DEFAULT_OUT,
    GRAPH_GAP,
    MSO_EMBEDDED_OLE_OBJECT,
    MSO_FALSE,
    MSO_TEXT_HORIZONTAL,
    MSO_TRUE,
    ORIGIN_OLE_PROG_ID,
    OVERLAY_CELLS,
    PANEL_ORDER,
    PP_LAYOUT_BLANK,
    PP_PASTE_OLE_OBJECT,
    PP_SAVE_AS_OPENXML,
    SLIDE_H,
    SLIDE_W,
)
from .data import (
    arm_profile_cell,
    load_arm_tables,
    load_tagged,
    nice_inc,
    overlay_metric_series,
    overlay_metrics,
    profile_series,
    series_for_cells,
    xlim_of,
    ylim_of,
)
from .origin_graphs import OriginSession
from .tables import add_summary_table


def _graph_box(n: int, index: int, *, rows: int | None = None) -> tuple[float, float, float, float]:
    if rows is None:
        cols = n
        gw = (BODY_WIDTH - GRAPH_GAP * max(cols - 1, 0)) / cols
        gh = min(BODY_HEIGHT, gw * 0.78)
        left0 = BODY_LEFT + (BODY_WIDTH - (gw * cols + GRAPH_GAP * max(cols - 1, 0))) / 2.0
        top = BODY_TOP + (BODY_HEIGHT - gh) / 2.0
        return left0 + index * (gw + GRAPH_GAP), top, gw, gh
    cols = int(n / rows)
    gw = (BODY_WIDTH - GRAPH_GAP * max(cols - 1, 0)) / cols
    gh = (BODY_HEIGHT - GRAPH_GAP * max(rows - 1, 0)) / rows
    r, c = divmod(index, cols)
    return BODY_LEFT + c * (gw + GRAPH_GAP), BODY_TOP + r * (gh + GRAPH_GAP), gw, gh


def _spec(series, *, x_title, y_title, ole_name, graph_width, graph_height, legend_pt=14.0) -> dict:
    xl = xlim_of(series)
    yl = ylim_of(series)
    return {
        "series": series,
        "x_title": x_title,
        "y_title": y_title,
        "x_limits": xl,
        "y_limits": yl,
        "x_inc": nice_inc(xl[1] - xl[0]),
        "y_inc": nice_inc(yl[1] - yl[0]),
        "ole_name": ole_name,
        "graph_width": graph_width,
        "graph_height": graph_height,
        "legend_pt": legend_pt,
    }


def _share_ylim(graphs: list[dict]) -> None:
    lo = min(g["y_limits"][0] for g in graphs)
    hi = max(g["y_limits"][1] for g in graphs)
    inc = nice_inc(hi - lo)
    for g in graphs:
        g["y_limits"] = (lo, hi)
        g["y_inc"] = inc


def all_slides(arm_tables: dict, tagged: dict, *, refresh_profiles: bool, skip_profiles: bool) -> list[dict]:
    slides: list[dict] = [
        {
            "kind": "cover",
            "title": "dV/dQ @ SOC0 — Si/Gr 열화",
            "subtitle": "SJ900 vs SJ1300 · tagged routine · Origin OLE",
        },
        {
            "kind": "text",
            "title": "지표 정의",
            "subtitle": "방전 끝단(저전압 Si 꼬리). 절대 Ah와 SOC 정규화를 섞지 말 것.",
            "body": (
                "dchg_dVdQ_SOC0  방전 종료점 |dV/dQ|. SOC% 정규화라 H1/H2 단독 판별은 약함.\r"
                "SOC0/mid  끝단 ÷ 중반(SOC 40-60%). 끝단만 뾰족해지면 상승 → H1 방향.\r"
                "Q_cliff_abs  cliff 시작 절대 Ah ≈ Gr 구간 길이. H1이면 거의 고정, H2면 감소.\r"
                "Qmax-5 Ah  끝에서 5 Ah 고정점의 |dV/dQ|. SOC로 다시 나누지 않음."
            ),
        },
    ]

    if not skip_profiles:
        pair = []
        for arm in ("SJ900", "SJ1300"):
            cell = arm_profile_cell(arm)
            series = profile_series(cell, ycol="dVdQ", xcol="Q_dvdq", step=50, refresh=refresh_profiles)
            pair.append(
                _spec(
                    series,
                    x_title="Q (Ah)",
                    y_title="dV/dQ (V/Ah)",
                    ole_name=f"Graph_profile_{arm}",
                    graph_width=420,
                    graph_height=300,
                    legend_pt=10.0,
                )
            )
        _share_ylim(pair)
        slides.append(
            {
                "kind": "graphs",
                "layout": "pair",
                "title": "dV/dQ profile every 50 tagged (dots = SOC0)",
                "subtitle": "left SJ900 Ch022 · right SJ1300 Ch012 · signed dV/dQ · shared y",
                "graphs": pair,
            }
        )

    soc0_pair = []
    inc_pair = []
    for arm in ("SJ900", "SJ1300"):
        cells = ARM_CELLS[arm]
        soc0 = series_for_cells(arm_tables, cells, xcol="tagged_cycle", ycol="dchg_dVdQ_SOC0")
        inc = series_for_cells(arm_tables, cells, xcol="tagged_cycle", ycol="SOC0_inc_pct_vs_t1", do_smooth=True)
        soc0_pair.append(
            _spec(soc0, x_title="Tagged cycle #", y_title="dVdQ_SOC0 (V/Ah)", ole_name=f"Graph_SOC0_{arm}", graph_width=420, graph_height=300)
        )
        inc_pair.append(
            _spec(inc, x_title="Tagged cycle #", y_title="inc% vs t1", ole_name=f"Graph_inc_{arm}", graph_width=420, graph_height=300)
        )
    _share_ylim(soc0_pair)
    _share_ylim(inc_pair)
    slides.append(
        {
            "kind": "graphs",
            "layout": "pair",
            "title": "dVdQ @ SOC0 vs tagged cycle",
            "subtitle": "SJ900 Ch022/024 · SJ1300 Ch010/011/012 · signed · shared y",
            "graphs": soc0_pair,
        }
    )
    slides.append(
        {
            "kind": "graphs",
            "layout": "pair",
            "title": "SOC0 increase % vs tagged cycle 1",
            "subtitle": "same cells · shared y · SoHQ breakpoints are not drawn (edit in Origin if needed)",
            "graphs": inc_pair,
        }
    )

    for arm in ("SJ900", "SJ1300"):
        df = tagged[arm]
        cells = OVERLAY_CELLS[arm]
        graphs = []
        for col, ylab, tag in overlay_metrics():
            series = overlay_metric_series(df, cells, col)
            graphs.append(
                _spec(
                    series,
                    x_title="Tagged cycle #",
                    y_title=ylab,
                    ole_name=f"Graph_{arm}_{tag}",
                    graph_width=330,
                    graph_height=200,
                    legend_pt=12.0,
                )
            )
        slides.append(
            {
                "kind": "graphs",
                "layout": "quad",
                "title": f"{arm} family overlay (tagged routine)",
                "subtitle": "SOC0 · SOC0/mid · Q_cliff_abs · |dV/dQ| at Qmax-5 Ah",
                "graphs": graphs,
            }
        )

    if not skip_profiles:
        for arm, cell in PANEL_ORDER:
            vq = profile_series(cell, ycol="V", xcol="Q_v", step=50, refresh=refresh_profiles)
            dvdq = profile_series(cell, ycol="dVdQ", xcol="Q_dvdq", step=50, refresh=refresh_profiles)
            traj = series_for_cells(
                {cell: arm_tables[cell]} if cell in arm_tables else {},
                (cell,),
                xcol="tagged_cycle",
                ycol="dchg_dVdQ_SOC0",
                abs_y=True,
            )
            if cell not in arm_tables and arm in tagged:
                g = tagged[arm]
                traj = overlay_metric_series(g, (cell,), "dchg_dVdQ_SOC0")
                for row in traj:
                    row["y"] = [abs(v) for v in row["y"]]
            graphs = [
                _spec(vq, x_title="Q (Ah)", y_title="V (V)", ole_name=f"Graph_{cell}_VQ", graph_width=268, graph_height=201, legend_pt=9.0),
                _spec(dvdq, x_title="Q (Ah)", y_title="dV/dQ (V/Ah)", ole_name=f"Graph_{cell}_dVdQ", graph_width=268, graph_height=201, legend_pt=9.0),
                _spec(traj, x_title="Tagged cycle #", y_title="|dV/dQ| @ SOC0 (V/Ah)", ole_name=f"Graph_{cell}_SOC0", graph_width=268, graph_height=201),
            ]
            slides.append(
                {
                    "kind": "graphs",
                    "layout": "triple",
                    "title": f"{arm} {cell} — V-Q / dV/dQ / |dV/dQ|@SOC0",
                    "subtitle": "profiles every 50 tagged · SOC0 trajectory is |dV/dQ| · double-click graph to edit in Origin",
                    "graphs": graphs,
                }
            )

    slides.append(
        {
            "kind": "summary",
            "title": "당시 판정 요약",
            "subtitle": "si_gr_mechanism/mechanism_summary.csv · 말기 RPT · fit_s/o/dR는 null",
        }
    )
    return slides


def _close_target_ppt(powerpoint, out_ppt: Path) -> None:
    for existing in list(powerpoint.Presentations):
        try:
            if Path(str(existing.FullName)).resolve() == out_ppt.resolve():
                existing.Close()
        except Exception:
            pass


def _sorted_textboxes(slide):
    boxes = []
    for shape in slide.Shapes:
        try:
            if shape.HasTextFrame:
                boxes.append(shape)
        except Exception:
            continue
    return sorted(boxes, key=lambda s: float(s.Top))


def _set_text(shape, text: str, *, size: float | None = None, bold: bool | None = None) -> None:
    rng = shape.TextFrame.TextRange
    rng.Text = text
    rng.Font.Name = "Malgun Gothic"
    if size is not None:
        rng.Font.Size = size
    if bold is not None:
        rng.Font.Bold = MSO_TRUE if bold else MSO_FALSE


def _fill_header(slide, title: str, subtitle: str) -> None:
    boxes = _sorted_textboxes(slide)
    if len(boxes) >= 1:
        _set_text(boxes[0], title, size=18, bold=True)
    if len(boxes) >= 2:
        _set_text(boxes[1], subtitle, size=11, bold=False)


def _paste_ole(slide, name: str, left: float, top: float, width: float, height: float) -> None:
    before = {int(shape.Id) for shape in slide.Shapes}
    slide.Shapes.PasteSpecial(DataType=PP_PASTE_OLE_OBJECT)
    new_shapes = [shape for shape in slide.Shapes if int(shape.Id) not in before]
    if len(new_shapes) != 1:
        raise RuntimeError(f"OLE paste 결과가 1개가 아닙니다: {len(new_shapes)}")
    shape = new_shapes[0]
    class_name = str(
        getattr(shape.OLEFormat, "ProgID", "")
        or getattr(shape.OLEFormat, "ClassType", "")
        or ""
    )
    if int(shape.Type) != MSO_EMBEDDED_OLE_OBJECT or class_name.casefold() != ORIGIN_OLE_PROG_ID:
        raise RuntimeError(f"Origin OLE가 아닙니다: type={shape.Type} class={class_name!r}")
    shape.Name = name
    shape.LockAspectRatio = MSO_FALSE
    shape.Left = left
    shape.Top = top
    shape.Width = width
    shape.Height = height


def _open_deck(powerpoint, out_ppt: Path):
    if AX_TEMPLATE.exists():
        shutil.copy2(AX_TEMPLATE, out_ppt)
        return powerpoint.Presentations.Open(str(out_ppt), WithWindow=True)
    presentation = powerpoint.Presentations.Add()
    presentation.PageSetup.SlideWidth = SLIDE_W
    presentation.PageSetup.SlideHeight = SLIDE_H
    while presentation.Slides.Count:
        presentation.Slides(1).Delete()
    return presentation


def _ensure_slides(presentation, n: int) -> None:
    if AX_TEMPLATE.exists() and presentation.Slides.Count >= 2:
        while presentation.Slides.Count < n:
            presentation.Slides(2).Duplicate()
        while presentation.Slides.Count > n:
            presentation.Slides(presentation.Slides.Count).Delete()
        return
    while presentation.Slides.Count < n:
        presentation.Slides.Add(presentation.Slides.Count + 1, PP_LAYOUT_BLANK)


def _blank_header(slide, title: str, subtitle: str) -> None:
    box = slide.Shapes.AddTextbox(MSO_TEXT_HORIZONTAL, 20, 6, 920, 28)
    _set_text(box, title, size=18, bold=True)
    note = slide.Shapes.AddTextbox(MSO_TEXT_HORIZONTAL, 20, 32, 920, 16)
    _set_text(note, subtitle, size=10, bold=False)


def build(out_ppt: Path, *, refresh_profiles: bool = False, skip_profiles: bool = False) -> None:
    started = time.perf_counter()
    arm_tables = load_arm_tables()
    tagged = load_tagged()
    slides = all_slides(arm_tables, tagged, refresh_profiles=refresh_profiles, skip_profiles=skip_profiles)
    print(f"Building {len(slides)} slides -> {out_ppt}", flush=True)
    out_ppt.parent.mkdir(parents=True, exist_ok=True)

    origin = OriginSession()
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = True
    _close_target_ppt(powerpoint, out_ppt)
    presentation = _open_deck(powerpoint, out_ppt)
    _ensure_slides(presentation, len(slides))
    use_ax = AX_TEMPLATE.exists()

    try:
        for index, spec in enumerate(slides, start=1):
            slide = presentation.Slides(index)
            title, subtitle = spec["title"], spec["subtitle"]
            if use_ax:
                _fill_header(slide, title, subtitle)
            else:
                _blank_header(slide, title, subtitle)
            if spec["kind"] == "text":
                box = slide.Shapes.AddTextbox(MSO_TEXT_HORIZONTAL, BODY_LEFT, BODY_TOP, BODY_WIDTH, BODY_HEIGHT)
                _set_text(box, spec["body"], size=16, bold=False)
                continue
            if spec["kind"] != "graphs":
                continue
            graphs = spec["graphs"]
            rows = {"pair": None, "triple": None, "quad": 2}[spec["layout"]]
            for graph_index, graph_spec in enumerate(graphs):
                left, top, width, height = _graph_box(len(graphs), graph_index, rows=rows)
                graph_spec["graph_width"] = width
                graph_spec["graph_height"] = height
                graph_name = origin.render(graph_spec)
                origin.copy(graph_name)
                _paste_ole(slide, graph_spec["ole_name"], left, top, width, height)
                print(f"  pasted {graph_spec['ole_name']}", flush=True)

        if use_ax:
            presentation.Save()
        else:
            if out_ppt.exists():
                try:
                    out_ppt.unlink()
                except PermissionError:
                    _close_target_ppt(powerpoint, out_ppt)
                    time.sleep(0.5)
                    out_ppt.unlink()
            presentation.SaveAs(str(out_ppt), PP_SAVE_AS_OPENXML)
        print(f"Saved OLE slides={presentation.Slides.Count}", flush=True)
    finally:
        try:
            presentation.Close()
        except Exception:
            pass
        try:
            powerpoint.Quit()
        except Exception:
            pass

    time.sleep(0.4)
    subprocess.run(["taskkill", "/IM", "POWERPNT.EXE", "/F"], capture_output=True, check=False)
    time.sleep(0.6)
    add_summary_table(out_ppt)
    print(f"Done in {time.perf_counter() - started:.1f}s", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build dVdQ@SOC0 Origin OLE PowerPoint")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--refresh-profiles", action="store_true")
    parser.add_argument("--skip-profiles", action="store_true", help="Skip V-Q / dV/dQ curve OLE (faster)")
    args = parser.parse_args()
    build(args.out.resolve(), refresh_profiles=args.refresh_profiles, skip_profiles=args.skip_profiles)
    return 0
