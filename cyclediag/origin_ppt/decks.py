"""Named Origin/matplotlib decks for lifetime indicators.

``dvdq_soc0`` keeps the specialized Si/Gr profile slides. Every other deck is
a tagged-cycle overlay of 2–4 columns that already live on the feature tables.
``--metrics a,b,c`` builds an ad-hoc deck from any tagged columns.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import ARM_CELLS, OVERLAY_CELLS, PANEL_ORDER
from .data import (
    arm_profile_cell,
    nice_inc,
    overlay_metric_series,
    overlay_metrics,
    profile_series,
    series_for_cells,
    xlim_of,
    ylim_of,
)


@dataclass(frozen=True)
class Metric:
    column: str
    y_label: str
    tag: str
    abs_y: bool = False


@dataclass(frozen=True)
class Deck:
    id: str
    title: str
    subtitle: str
    definition: str
    metrics: tuple[Metric, ...]
    include_profiles: bool = False
    include_inc: bool = False
    summary: str = "last_values"  # mechanism | last_values | none


Y_LABEL = {
    "SoHQ": "SoHQ (%)",
    "dSoHQ_dN": "dSoHQ / dN (%/cyc)",
    "dchgCapa": "dchg capacity (Ah)",
    "chgCapa": "chg capacity (Ah)",
    "CE": "CE (%)",
    "CE_rev": "CE_rev (%)",
    "EoC_dchgR_10s": "EoC dchgR 10s (Ω)",
    "EoC_dchgR_60s": "EoC dchgR 60s (Ω)",
    "EoD_chgR_10s": "EoD chgR 10s (Ω)",
    "EoD_chgR_60s": "EoD chgR 60s (Ω)",
    "EoC_dchgR_10s_inc": "EoC dchgR 10s inc% vs t1",
    "EoC_dchgR_60s_inc": "EoC dchgR 60s inc% vs t1",
    "EoC_restV_end": "EoC restV end (V)",
    "EoD_restV_end": "EoD restV end (V)",
    "EoC_restV_60s": "EoC restV 60s (V)",
    "EoD_restV_60s": "EoD restV 60s (V)",
    "hyst_area": "hyst area (V·Ah)",
    "hyst_area_low": "hyst area low (V·Ah)",
    "hyst_area_mid": "hyst area mid (V·Ah)",
    "hyst_frac_low": "hyst frac low",
    "chgCapa_CCratio": "CC ratio (%)",
    "chgCVtime": "CV time (s)",
    "dchg_dVdQ_SOC0": "|dV/dQ| @ SOC0 (V/Ah)",
    "dchg_dVdQ_SOC0_to_mid_ratio": "SOC0 / mid ratio",
    "dchg_Q_cliff_abs": "Q_cliff_abs (Ah)",
    "dchg_dVdQ_at_Qabs_5": "|dV/dQ| at Qmax-5 Ah (V/Ah)",
    "dchg_dVdQ_SOC0_cliff_width_abs": "cliff width abs (Ah)",
}


def metric(column: str, *, y_label: str | None = None, tag: str | None = None, abs_y: bool = False) -> Metric:
    label = y_label or Y_LABEL.get(column, column)
    short = tag or "".join(ch for ch in column if ch.isalnum())[:20]
    return Metric(column=column, y_label=label, tag=short or "m", abs_y=abs_y)


DECKS: dict[str, Deck] = {
    "dvdq_soc0": Deck(
        id="dvdq_soc0",
        title="dV/dQ @ SOC0 - Si/Gr 열화",
        subtitle="SJ900 vs SJ1300 · tagged routine · Origin OLE",
        definition=(
            "dchg_dVdQ_SOC0  방전 종료점 |dV/dQ|. SOC% 정규화라 H1/H2 단독 판별은 약함.\r"
            "SOC0/mid  끝단 ÷ 중반(SOC 40-60%). 끝단만 뾰족해지면 상승 → H1 방향.\r"
            "Q_cliff_abs  cliff 시작 절대 Ah ≈ Gr 구간 길이. H1이면 거의 고정, H2면 감소.\r"
            "Qmax-5 Ah  끝에서 5 Ah 고정점의 |dV/dQ|. SOC로 다시 나누지 않음."
        ),
        metrics=tuple(metric(col, y_label=ylab, tag=tag) for col, ylab, tag in overlay_metrics()),
        include_profiles=True,
        include_inc=True,
        summary="mechanism",
    ),
    "sohq": Deck(
        id="sohq",
        title="SoHQ / CE / capacity",
        subtitle="tagged routine · SJ900 vs SJ1300",
        definition=(
            "SoHQ  방전용량 / 기준용량. 수명 타깃.\r"
            "dSoHQ_dN  사이클당 SoHQ 기울기. BP 전후 가속 구간을 본다.\r"
            "CE  쿨롱효율. LLI· pleating 쪽 단서.\r"
            "dchgCapa  방전 Ah. SoHQ와 같은 family — 절대량 확인용."
        ),
        metrics=(
            metric("SoHQ"),
            metric("dSoHQ_dN"),
            metric("CE"),
            metric("dchgCapa"),
        ),
    ),
    "resistance": Deck(
        id="resistance",
        title="Pulse resistance (EoC / EoD)",
        subtitle="10 s · 60 s · tagged routine",
        definition=(
            "EoC_dchgR_10s / 60s  충전 끝에서 방전 펄스. 60 s는 확산·분극까지.\r"
            "EoD_chgR_10s / 60s  방전 끝에서 충전 펄스. SOC0 근처 저항.\r"
            "10 s vs 60 s를 같이 보면 ohmic vs slower 성분을 나눌 수 있다."
        ),
        metrics=(
            metric("EoC_dchgR_10s"),
            metric("EoC_dchgR_60s"),
            metric("EoD_chgR_10s"),
            metric("EoD_chgR_60s"),
        ),
    ),
    "rest_voltage": Deck(
        id="rest_voltage",
        title="Rest voltage (EoC / EoD)",
        subtitle="60 s · end of rest · tagged routine",
        definition=(
            "EoC_restV_end / 60s  충전 후 휴지. 완화된 OCV에 가깝다.\r"
            "EoD_restV_end / 60s  방전 후 휴지. 방전 쪽 완화는 더 느리다.\r"
            "end와 60 s가 갈라지면 완화 시간 부족 또는 tau 변화."
        ),
        metrics=(
            metric("EoC_restV_end"),
            metric("EoC_restV_60s"),
            metric("EoD_restV_end"),
            metric("EoD_restV_60s"),
        ),
    ),
    "hysteresis": Deck(
        id="hysteresis",
        title="Hysteresis bands",
        subtitle="global / low / mid · tagged routine",
        definition=(
            "hyst_area  전 구간 루프 면적.\r"
            "hyst_area_low  저SOC 밴드 — Si 쪽 국소화.\r"
            "hyst_area_mid  중반 밴드.\r"
            "hyst_frac_low  저SOC 면적 비율. Si fade가 커지면 보통 상승."
        ),
        metrics=(
            metric("hyst_area"),
            metric("hyst_area_low"),
            metric("hyst_area_mid"),
            metric("hyst_frac_low"),
        ),
    ),
    "cv": Deck(
        id="cv",
        title="CC/CV split and efficiency",
        subtitle="tagged routine · SJ900 vs SJ1300",
        definition=(
            "chgCapa_CCratio  CC 충전 비율. CV가 늘면 저항·수송 제한 쪽.\r"
            "chgCVtime  CV 유지 시간.\r"
            "CE · SoHQ  같은 장표에서 용량 손실과 같이 본다."
        ),
        metrics=(
            metric("chgCapa_CCratio"),
            metric("chgCVtime"),
            metric("CE"),
            metric("SoHQ"),
        ),
    ),
    "lifetime": Deck(
        id="lifetime",
        title="Lifetime dashboard",
        subtitle="SoHQ · CE · R60 · EoC restV",
        definition=(
            "한 장표에 수명 타깃과 impedance / OCV 단서를 같이 둔다.\r"
            "SoHQ  용량 유지.\r"
            "CE  비가역 손실.\r"
            "EoC_dchgR_60s  충전 끝 60 s 저항.\r"
            "EoC_restV_end  충전 후 완화된 전압."
        ),
        metrics=(
            metric("SoHQ"),
            metric("CE"),
            metric("EoC_dchgR_60s"),
            metric("EoC_restV_end"),
        ),
    ),
}


def get_deck(deck_id: str) -> Deck:
    try:
        return DECKS[deck_id]
    except KeyError as exc:
        known = ", ".join(DECKS)
        raise KeyError(f"unknown deck {deck_id!r}. choose one of: {known}") from exc


def format_deck_list() -> str:
    lines = ["id             title"]
    for deck in DECKS.values():
        extra = "  [profiles]" if deck.include_profiles else ""
        cols = ", ".join(m.column for m in deck.metrics)
        lines.append(f"{deck.id:<14} {deck.title}{extra}")
        lines.append(f"{'':14} {cols}")
    lines.append("")
    lines.append("ad-hoc: python -m cyclediag.origin_ppt --metrics SoHQ,CE,EoC_dchgR_60s")
    return "\n".join(lines)


def custom_deck(columns: tuple[str, ...], *, title: str | None = None) -> Deck:
    if not columns:
        raise ValueError("--metrics needs at least one column")
    metrics = tuple(metric(col) for col in columns)
    shown = ", ".join(columns)
    return Deck(
        id="custom",
        title=title or shown,
        subtitle="tagged routine · custom metrics",
        definition="User-selected tagged-cycle columns.\r" + "\r".join(columns),
        metrics=metrics,
    )


def _graph_spec(series, *, x_title, y_title, ole_name, legend_pt=14.0) -> dict:
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
        "graph_width": 420,
        "graph_height": 300,
        "legend_pt": legend_pt,
    }


def _share_ylim(graphs: list[dict]) -> None:
    if not graphs:
        return
    lo = min(g["y_limits"][0] for g in graphs)
    hi = max(g["y_limits"][1] for g in graphs)
    inc = nice_inc(hi - lo)
    for g in graphs:
        g["y_limits"] = (lo, hi)
        g["y_inc"] = inc


def _layout_for(n: int) -> str:
    if n <= 2:
        return "pair"
    if n == 3:
        return "triple"
    return "quad"


def overlay_slides(deck: Deck, tagged: dict) -> list[dict]:
    slides: list[dict] = [
        {"kind": "cover", "title": deck.title, "subtitle": deck.subtitle},
        {
            "kind": "text",
            "title": "지표 정의",
            "subtitle": "tagged routine columns · SJ900 vs SJ1300",
            "body": deck.definition,
        },
    ]
    for item in deck.metrics:
        pair = []
        for arm in ("SJ900", "SJ1300"):
            df = tagged.get(arm)
            if df is None or item.column not in df.columns:
                continue
            series = overlay_metric_series(df, OVERLAY_CELLS[arm], item.column)
            if item.abs_y:
                for row in series:
                    row["y"] = [abs(v) for v in row["y"]]
            if not series:
                continue
            pair.append(
                _graph_spec(
                    series,
                    x_title="Tagged cycle #",
                    y_title=item.y_label,
                    ole_name=f"Graph_{item.tag}_{arm}",
                )
            )
        if len(pair) >= 2:
            _share_ylim(pair)
        if pair:
            slides.append(
                {
                    "kind": "graphs",
                    "layout": "pair",
                    "title": f"{item.column} vs tagged cycle",
                    "subtitle": f"{item.y_label} · SJ900 vs SJ1300 · shared y",
                    "graphs": pair,
                }
            )

    chunk: list[Metric] = []
    for item in deck.metrics:
        chunk.append(item)
        if len(chunk) == 4:
            slides.extend(_family_overlay_slides(deck, tagged, tuple(chunk)))
            chunk = []
    if 2 <= len(chunk) <= 3:
        slides.extend(_family_overlay_slides(deck, tagged, tuple(chunk)))

    if deck.summary != "none":
        slides.append(
            {
                "kind": "summary",
                "title": "말기 값 요약" if deck.summary == "last_values" else "당시 판정 요약",
                "subtitle": "last tagged cycle per cell" if deck.summary == "last_values" else "si_gr_mechanism/mechanism_summary.csv",
            }
        )
    return slides


def _family_overlay_slides(deck: Deck, tagged: dict, metrics: tuple[Metric, ...]) -> list[dict]:
    slides = []
    for arm in ("SJ900", "SJ1300"):
        df = tagged.get(arm)
        if df is None:
            continue
        graphs = []
        for item in metrics:
            if item.column not in df.columns:
                continue
            series = overlay_metric_series(df, OVERLAY_CELLS[arm], item.column)
            if not series:
                continue
            graphs.append(
                _graph_spec(
                    series,
                    x_title="Tagged cycle #",
                    y_title=item.y_label,
                    ole_name=f"GraphFam_{arm}_{item.tag}",
                    legend_pt=12.0,
                )
            )
        if graphs:
            slides.append(
                {
                    "kind": "graphs",
                    "layout": _layout_for(len(graphs)),
                    "title": f"{arm} overlay ({deck.id})",
                    "subtitle": " · ".join(m.column for m in metrics),
                    "graphs": graphs,
                }
            )
    return slides


def dvdq_soc0_slides(arm_tables: dict, tagged: dict, *, refresh_profiles: bool, skip_profiles: bool) -> list[dict]:
    deck = DECKS["dvdq_soc0"]
    slides: list[dict] = [
        {"kind": "cover", "title": deck.title, "subtitle": deck.subtitle},
        {
            "kind": "text",
            "title": "지표 정의",
            "subtitle": "방전 끝단(저전압 Si 꼬리). 절대 Ah와 SOC 정규화를 섞지 말 것.",
            "body": deck.definition,
        },
    ]

    if not skip_profiles:
        pair = []
        for arm in ("SJ900", "SJ1300"):
            cell = arm_profile_cell(arm)
            series = profile_series(cell, ycol="dVdQ", xcol="Q_dvdq", step=50, refresh=refresh_profiles)
            pair.append(
                _graph_spec(
                    series,
                    x_title="Q (Ah)",
                    y_title="dV/dQ (V/Ah)",
                    ole_name=f"Graph_profile_{arm}",
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
            _graph_spec(soc0, x_title="Tagged cycle #", y_title="dVdQ_SOC0 (V/Ah)", ole_name=f"Graph_SOC0_{arm}")
        )
        inc_pair.append(
            _graph_spec(inc, x_title="Tagged cycle #", y_title="inc% vs t1", ole_name=f"Graph_inc_{arm}")
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
                _graph_spec(
                    series,
                    x_title="Tagged cycle #",
                    y_title=ylab,
                    ole_name=f"Graph_{arm}_{tag}",
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
                traj = overlay_metric_series(tagged[arm], (cell,), "dchg_dVdQ_SOC0")
                for row in traj:
                    row["y"] = [abs(v) for v in row["y"]]
            graphs = [
                _graph_spec(vq, x_title="Q (Ah)", y_title="V (V)", ole_name=f"Graph_{cell}_VQ", legend_pt=9.0),
                _graph_spec(dvdq, x_title="Q (Ah)", y_title="dV/dQ (V/Ah)", ole_name=f"Graph_{cell}_dVdQ", legend_pt=9.0),
                _graph_spec(traj, x_title="Tagged cycle #", y_title="|dV/dQ| @ SOC0 (V/Ah)", ole_name=f"Graph_{cell}_SOC0"),
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


def resolve_deck(deck_id: str, metrics: tuple[str, ...] | None, tagged: dict) -> Deck:
    if metrics:
        available = _tagged_columns(tagged)
        resolved = tuple(_resolve_column(name, available) for name in metrics)
        return custom_deck(resolved)
    return get_deck(deck_id)


def _tagged_columns(tagged: dict) -> set[str]:
    cols: set[str] = set()
    for df in tagged.values():
        cols.update(str(c) for c in df.columns)
    return cols


def _resolve_column(name: str, available: set[str]) -> str:
    from cyclediag.features.indicator_registry import canonical_name

    if name in available:
        return name
    canon = canonical_name(name)
    if canon in available:
        return canon
    sample = ", ".join(sorted(available)[:12])
    raise KeyError(f"column {name!r} not in tagged tables. examples: {sample}")


def slides_for(
    deck_id: str = "dvdq_soc0",
    *,
    arm_tables: dict | None = None,
    tagged: dict | None = None,
    refresh_profiles: bool = False,
    skip_profiles: bool = False,
    metrics: tuple[str, ...] | None = None,
) -> tuple[Deck, list[dict]]:
    from .data import load_arm_tables, load_tagged

    tagged = tagged if tagged is not None else load_tagged()
    deck = resolve_deck(deck_id, metrics, tagged)
    if deck.id == "dvdq_soc0" and not metrics:
        tables = arm_tables if arm_tables is not None else load_arm_tables()
        return deck, dvdq_soc0_slides(
            tables, tagged, refresh_profiles=refresh_profiles, skip_profiles=skip_profiles
        )
    return deck, overlay_slides(deck, tagged)


def all_slides(arm_tables: dict, tagged: dict, *, refresh_profiles: bool, skip_profiles: bool) -> list[dict]:
    """Backward-compatible dVdQ@SOC0 spec builder used by tests."""
    return dvdq_soc0_slides(arm_tables, tagged, refresh_profiles=refresh_profiles, skip_profiles=skip_profiles)
