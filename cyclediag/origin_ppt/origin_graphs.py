"""One Origin graph page: swap XY, restyle, copy to clipboard.

Creates Book1/Graph from scratch when no OPJU template is present
(same COM paste contract as data_analysis/hppc_analysis).
"""

from __future__ import annotations

import time

import originpro as op

from .config import CACHE_DIR


def _first_graph():
    graphs = op.graph_list("p") or []
    if graphs:
        return graphs[0]
    graph = op.new_graph(lname="Graph1")
    if graph is None:
        raise RuntimeError("Origin graph 페이지를 만들지 못했습니다.")
    return graph


def _sheet():
    sheet = op.find_sheet("w", "[Book1]Sheet1")
    if sheet is not None:
        return sheet
    sheet = op.new_sheet("w")
    if sheet is None:
        raise RuntimeError("Origin worksheet를 만들지 못했습니다.")
    return sheet


def _write_series(series: list[dict], x_title: str, y_title: str) -> None:
    sheet = _sheet()
    n = max(len(series) * 2, 2)
    sheet.cols = n
    for index, row in enumerate(series):
        sheet.from_list(index * 2, row["x"], lname=x_title, comments=row["label"] or f"s{index}", axis="X")
        sheet.from_list(index * 2 + 1, row["y"], lname=y_title, comments=row["label"] or f"s{index}", axis="Y")


class OriginSession:
    def __init__(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        op.set_show(True)
        try:
            op.new()
        except Exception:
            pass
        time.sleep(0.25)
        _sheet()
        _first_graph()
        self._style_key: tuple | None = None
        self._plot_key: tuple | None = None

    def render(self, spec: dict) -> str:
        series = spec["series"]
        if not series:
            raise RuntimeError(f"빈 시리즈: {spec.get('ole_name')}")
        y_title = str(spec["y_title"])
        x_title = str(spec["x_title"])
        plot_key = (spec["ole_name"], len(series), tuple(s["kind"] for s in series[:8]))
        style_key = (
            float(spec["graph_width"]),
            float(spec["graph_height"]),
            tuple(spec["x_limits"]),
            tuple(spec["y_limits"]),
            float(spec["x_inc"]),
            float(spec["y_inc"]),
        )
        _write_series(series, x_title, y_title)
        if plot_key != self._plot_key:
            self._rebuild_plots(spec)
            self._plot_key = plot_key
        else:
            op.lt_exec("legendupdate; doc -uw;")
        self._restyle(spec, x_title, y_title, full=style_key != self._style_key)
        self._style_key = style_key
        return str(_first_graph().name)

    def copy(self, graph_name: str) -> None:
        copied = op.lt_exec(f"win -a {graph_name}; clipboard {graph_name};")
        if not copied:
            raise RuntimeError(f"Origin clipboard 복사 실패: {graph_name}")
        time.sleep(0.12)

    def _rebuild_plots(self, spec: dict) -> None:
        graph = _first_graph()
        graph.activate()
        layer = graph[0]
        layer.activate()
        sheet = _sheet()
        for plot in reversed(list(layer.plot_list())):
            plot.remove()
        for index, row in enumerate(spec["series"]):
            kind = row.get("kind") or "l"
            plot = layer.add_plot(sheet, coly=index * 2 + 1, colx=index * 2, type=kind)
            if plot is None:
                raise RuntimeError(f"Origin curve {index + 1}을 만들지 못했습니다.")
            plot.color = row["color"]
            size = "5" if kind == "s" else "7"
            plot.set_cmd(
                "-k 1",
                "-kf 0",
                f"-z {size}",
                "-l 1",
                "-d 0",
                "-wp 3",
            )
        op.lt_exec("legendupdate; doc -uw;")

    def _restyle(self, spec: dict, x_title: str, y_title: str, *, full: bool) -> None:
        graph = _first_graph()
        graph.activate()
        layer = graph[0]
        layer.activate()
        layer.axis("x").title = rf"\b({x_title})"
        layer.axis("y").title = rf"\b({y_title})"
        x0, x1 = spec["x_limits"]
        y0, y1 = spec["y_limits"]
        x_inc = float(spec["x_inc"])
        y_inc = float(spec["y_inc"])
        layer.set_int("sauto", 0)
        layer.set_int("x.rescale", 1)
        layer.set_int("y.rescale", 1)
        layer.set_xlim(float(x0), float(x1))
        layer.set_ylim(float(y0), float(y1))
        op.lt_exec(
            f"layer.x.from={x0:g}; layer.x.to={x1:g}; layer.x.inc={x_inc:g};"
            f"layer.y.from={y0:g}; layer.y.to={y1:g}; layer.y.inc={y_inc:g};"
        )
        if not full:
            op.lt_exec("doc -uw;")
            return

        graph_width = float(spec["graph_width"])
        graph_height = float(spec["graph_height"])
        legend_pt = float(spec.get("legend_pt", 14.0))
        tick_pt = float(spec.get("tick_pt", 18.0))
        title_pt = float(spec.get("title_pt", 22.0))
        graph.set_int("kar", 0)
        page_width = float(graph.get_float("width"))
        graph.set_float("height", page_width * graph_height / graph_width)
        graph.set_int("autoSize", 0)
        page_width = float(graph.get_float("width"))
        page_height = float(graph.get_float("height"))
        left_pct, top_pct, width_pct, height_pct = 16.0, 12.0, 70.0, 70.0
        layer.set_int("unit", 1)
        layer.set_float("left", left_pct)
        layer.set_float("top", top_pct)
        layer.set_float("width", width_pct)
        layer.set_float("height", height_pct)
        op.lt_exec(
            f"layer.x.label.pt={tick_pt:g}; layer.y.label.pt={tick_pt:g};"
            "layer.x.label.bold=1; layer.y.label.bold=1;"
            "layer.x.ticks=10; layer.y.ticks=10;"
            "layer.x.showGrids=1; layer.y.showGrids=1;"
            "layer.x.grid.majorType=2; layer.y.grid.majorType=2;"
            "layer.x.minorTicks=1; layer.y.minorTicks=1;"
        )
        for name in ("xb", "yl"):
            label = layer.label(name)
            if label is None:
                continue
            label.set_float("fsize", title_pt)
            try:
                label.set_float("pt", title_pt)
            except Exception:
                pass
        op.lt_exec(
            f"xb.fsize={title_pt:g}; yl.fsize={title_pt:g}; "
            f"xb.pt={title_pt:g}; yl.pt={title_pt:g}; doc -uw;"
        )
        legend = layer.label("legend")
        if legend is not None:
            legend.set_int("background", 0)
            legend.set_int("attach", 1)
            legend.set_int("anchor", 1)
            legend.set_float("fsize", legend_pt)
            try:
                legend.set_float("pt", legend_pt)
            except Exception:
                pass
            op.lt_exec(
                f"legend.background=0; legend.fsize={legend_pt:g}; legend.pt={legend_pt:g}; doc -uw;"
            )
            plot_top = top_pct / 100.0 * page_height
            plot_right = (left_pct + width_pct) / 100.0 * page_width
            raw = str(legend.get_str("pageRect")).strip()
            values = tuple(float(v) for v in raw.split()) if raw else ()
            if len(values) == 4:
                legend_w = max(values[2] - values[0], 1.0)
                pad = page_width * 0.012
                legend.set_float("left", plot_right - legend_w - pad)
                legend.set_float("top", plot_top + pad)
        op.lt_exec("doc -uw;")
        print(
            f"  restyle page={page_width:.0f}x{page_height:.0f} {y_title}",
            flush=True,
        )
