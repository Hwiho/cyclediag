"""Build Origin OLE PowerPoint from a named indicator deck.

    python -m cyclediag.origin_ppt --deck sohq
    python -m cyclediag.origin_ppt --metrics SoHQ,CE,EoC_dchgR_60s

Needs Origin 2025, originpro, pywin32, pandas, python-pptx.
Shell is the AX 16:9 template when present; graphs are Origin OLE (origin95.graph).
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .config import (
    AX_TEMPLATE,
    BODY_HEIGHT,
    BODY_LEFT,
    BODY_TOP,
    BODY_WIDTH,
    GRAPH_GAP,
    MSO_EMBEDDED_OLE_OBJECT,
    MSO_FALSE,
    MSO_TEXT_HORIZONTAL,
    MSO_TRUE,
    ORIGIN_OLE_PROG_ID,
    PP_LAYOUT_BLANK,
    PP_PASTE_OLE_OBJECT,
    PP_SAVE_AS_OPENXML,
    SLIDE_H,
    SLIDE_W,
)
from .decks import all_slides, slides_for
from .origin_graphs import OriginSession
from .tables import add_last_value_table, add_summary_table


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


def build(
    out_ppt: Path,
    *,
    deck: str = "dvdq_soc0",
    metrics: tuple[str, ...] | None = None,
    refresh_profiles: bool = False,
    skip_profiles: bool = False,
) -> None:
    import win32com.client

    from .data import load_tagged

    started = time.perf_counter()
    tagged = load_tagged()
    deck_spec, slides = slides_for(
        deck,
        tagged=tagged,
        refresh_profiles=refresh_profiles,
        skip_profiles=skip_profiles,
        metrics=metrics,
    )
    print(f"Building {len(slides)} slides [{deck_spec.id}] -> {out_ppt}", flush=True)
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
    if deck_spec.summary == "mechanism":
        add_summary_table(out_ppt)
    elif deck_spec.summary == "last_values":
        add_last_value_table(out_ppt, tagged, deck_spec.metrics)
    print(f"Done in {time.perf_counter() - started:.1f}s", flush=True)
