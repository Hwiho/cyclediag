#!/usr/bin/env python3
"""Cycle-by-cycle metrics: CSV extract + multi-panel PDF + trend notes.

Examples
--------
# from already-diagnosed trajectory
PYTHONPATH=. python3 cyclediag/tools/plot_cycle_metrics_panel.py \\
  --trajectory example/output/doe3_cathode_compare/M02Ch103_trajectory.csv \\
  --out-dir example/output/cycle_metrics_panel/M02Ch103

# from raw CSV (runs electrode diagnosis)
PYTHONPATH=. python3 cyclediag/tools/plot_cycle_metrics_panel.py \\
  --raw example/fixtures/doe/DOE3/S83S/M02Ch103_raw.csv \\
  --out-dir example/output/cycle_metrics_panel/M02Ch103

# folder of trajectories
PYTHONPATH=. python3 cyclediag/tools/plot_cycle_metrics_panel.py \\
  --trajectory-dir example/output/doe3_cathode_compare \\
  --out-dir example/output/cycle_metrics_panel
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

from cyclediag.analysis.cycle_trend import (  # noqa: E402
    analyze_all_metrics,
    extract_cycle_metric_table,
    narrative_from_trends,
)
from cyclediag.analysis.metric_catalog import (  # noqa: E402
    PANEL_GROUPS,
    available_metrics,
    catalog_as_records,
    get_metric,
    metrics_for_family,
)

C_LINE = "#1F4E5F"
C_EARLY = "#C45C26"
C_LATE = "#1F6F8B"
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


def load_trajectory(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "cycle" not in df.columns:
        raise SystemExit(f"no cycle column in {path}")
    df["cycle"] = pd.to_numeric(df["cycle"], errors="coerce")
    return df.sort_values("cycle")


def diagnose_raw(path: Path, *, step: int = 10, halfcell_dir: Path | None = None) -> pd.DataFrame:
    from cyclediag.tools.compare_doe_cathodes import diagnose_one

    feats, _segs, _meta = diagnose_one(path, halfcell_dir=halfcell_dir, step=step)
    return feats


def wrap_text(fig, x, y, text, width=95, size=8.5, weight="normal", color="#222"):
    lines: list[str] = []
    for para in text.split("\n"):
        if para.strip():
            lines.extend(textwrap.wrap(para, width=width) or [""])
        else:
            lines.append("")
    fig.text(
        x, y, "\n".join(lines),
        fontproperties=fp(size, weight), va="top", color=color, linespacing=1.3,
    )
    return len(lines) * (size * 0.016)


def _routine_xy(df: pd.DataFrame, key: str) -> tuple[np.ndarray, np.ndarray]:
    d = df
    if "cycle_role" in d.columns:
        d = d.loc[d["cycle_role"].astype(str).eq("routine_05c")]
    x = pd.to_numeric(d["cycle"], errors="coerce")
    y = pd.to_numeric(d.get(key), errors="coerce")
    m = x.notna() & y.notna()
    return x[m].to_numpy(dtype=float), y[m].to_numpy(dtype=float)


def build_pdf(
    out_pdf: Path,
    *,
    cell_id: str,
    feats: pd.DataFrame,
    trends: pd.DataFrame,
    narrative: str,
) -> None:
    arts = Path("/opt/cursor/artifacts")
    arts.mkdir(parents=True, exist_ok=True)

    trend_map = {
        str(r["metric"]): r for _, r in trends.iterrows()
    } if not trends.empty else {}

    with PdfPages(out_pdf) as pdf:
        # cover
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.patch.set_facecolor(C_BG)
        fig.text(0.06, 0.90, "사이클별 지표 패널", fontproperties=fp(18, "bold"))
        fig.text(0.06, 0.84, cell_id, fontproperties=fp(14))
        wrap_text(
            fig, 0.06, 0.76,
            "각 패널 = 한 지표의 cycle 궤적 (routine 0.5C).\n"
            "early/late 점선 = 앞·뒤 5포인트 median.\n"
            "트렌드 = 선형 slope/100cyc + aging 기대방향 대조.\n\n"
            "주의: LAM_PE / *_proxy / pattern_score는 가설·proxy이며 "
            "절대 LAM%/LLI%가 아닙니다. R_ohmic은 √t 외삽 proxy "
            "(0.1s 단일값 ≠ 순수 옴).",
            width=100, size=9.5,
        )
        wrap_text(fig, 0.06, 0.42, narrative, width=100, size=8.5)
        fig.text(0.06, 0.08, "CycleDiag · plot_cycle_metrics_panel.py", fontproperties=fp(8), color="#666")
        pdf.savefig(fig)
        plt.close(fig)

        # panel pages by family
        for fam_key, fam_title in PANEL_GROUPS:
            specs = [m for m in metrics_for_family(fam_key) if m.key in feats.columns]
            if not specs:
                continue
            # 3x3 max per page
            for page_i in range(0, len(specs), 9):
                chunk = specs[page_i: page_i + 9]
                nrows = int(np.ceil(len(chunk) / 3))
                fig, axes = plt.subplots(nrows, 3, figsize=(11.69, 8.27), squeeze=False)
                fig.patch.set_facecolor("white")
                fig.suptitle(
                    f"{cell_id} · {fam_title}",
                    fontproperties=fp(13, "bold"), y=0.98,
                )
                for ax in axes.ravel():
                    ax.set_visible(False)
                for i, spec in enumerate(chunk):
                    ax = axes[i // 3, i % 3]
                    ax.set_visible(True)
                    x, y = _routine_xy(feats, spec.key)
                    if len(y) == 0:
                        ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
                        ax.set_title(spec.title_ko, fontproperties=fp(9, "bold"))
                        continue
                    ax.plot(x, y, "-", color=C_LINE, lw=1.4, alpha=0.9)
                    ax.plot(x, y, ".", color=C_LINE, ms=3, alpha=0.55)
                    tr = trend_map.get(spec.key)
                    if tr is not None and tr.get("early_median") is not None:
                        ax.axhline(float(tr["early_median"]), color=C_EARLY, ls="--", lw=0.9, alpha=0.8)
                        ax.axhline(float(tr["late_median"]), color=C_LATE, ls="--", lw=0.9, alpha=0.8)
                    label = ""
                    if tr is not None:
                        sl = tr.get("slope_per_100")
                        sl_s = f"{sl:+.3g}/100" if sl is not None and np.isfinite(sl) else "—"
                        label = f"{tr.get('trend_label')} · {sl_s}"
                    ax.set_title(f"{spec.title_ko}\n{label}", fontproperties=fp(8, "bold"), loc="left")
                    ax.set_xlabel("Cycle", fontproperties=fp(7))
                    ax.set_ylabel(spec.unit, fontproperties=fp(7))
                    ax.grid(True, alpha=0.25)
                    for lab in ax.get_xticklabels() + ax.get_yticklabels():
                        lab.set_fontproperties(fp(7))
                # hide unused
                for j in range(len(chunk), nrows * 3):
                    axes[j // 3, j % 3].set_visible(False)
                fig.tight_layout(rect=[0.02, 0.04, 0.98, 0.95])
                fig.text(
                    0.02, 0.015,
                    "점선: orange=early median · blue=late median  |  routine_05c only",
                    fontproperties=fp(7), color="#666",
                )
                pdf.savefig(fig)
                plt.close(fig)

        # description pages
        specs_all = available_metrics(feats.columns)
        for page_i in range(0, len(specs_all), 6):
            chunk = specs_all[page_i: page_i + 6]
            fig = plt.figure(figsize=(11.69, 8.27))
            fig.patch.set_facecolor(C_BG)
            fig.text(0.06, 0.94, f"지표 설명 · 트렌드 ({cell_id})", fontproperties=fp(13, "bold"))
            y = 0.88
            for spec in chunk:
                tr = trend_map.get(spec.key, {})
                fig.text(0.06, y, f"{spec.title_ko}  ({spec.key})", fontproperties=fp(10, "bold"), color=C_LINE)
                y -= 0.028
                wrap_text(fig, 0.06, y, f"{spec.description}  |  계산: {spec.how}", width=110, size=7.5)
                y -= 0.055
                note = tr.get("note") or "데이터 부족"
                wrap_text(
                    fig, 0.06, y,
                    f"트렌드: {note}  |  aging 기대={spec.aging_hint}  |  vs={tr.get('vs_expectation', 'n/a')}",
                    width=110, size=7.5, color="#444",
                )
                y -= 0.055
                if y < 0.08:
                    break
            pdf.savefig(fig)
            plt.close(fig)

        meta = pdf.infodict()
        meta["Title"] = f"Cycle metrics panel — {cell_id}"
        meta["Author"] = "CycleDiag"

    # also copy to artifacts
    dest = arts / out_pdf.name
    dest.write_bytes(out_pdf.read_bytes())


def write_markdown(
    out_md: Path,
    *,
    cell_id: str,
    trends: pd.DataFrame,
    narrative: str,
) -> None:
    lines = [
        f"# 사이클별 지표 패널 — {cell_id}",
        "",
        narrative,
        "",
        "## 지표 카탈로그 + 트렌드",
        "",
    ]
    for fam_key, fam_title in PANEL_GROUPS:
        sub = trends.loc[trends["family"] == fam_key] if "family" in trends.columns else pd.DataFrame()
        if sub.empty:
            continue
        lines.append(f"### {fam_title}")
        lines.append("")
        for _, r in sub.iterrows():
            spec = get_metric(str(r["metric"]))
            desc = spec.description if spec else ""
            how = spec.how if spec else ""
            lines.append(f"**{r['title_ko']}** (`{r['metric']}`)")
            lines.append(f"- 의미: {desc}")
            lines.append(f"- 계산: {how}")
            lines.append(f"- 트렌드: {r.get('note', '')}")
            lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")


def process_one(
    feats: pd.DataFrame,
    *,
    cell_id: str,
    out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    keys = [m.key for m in available_metrics(feats.columns)]
    table = extract_cycle_metric_table(feats, keys=keys, routine_only=True)
    table.to_csv(out_dir / f"{cell_id}_cycle_metrics.csv", index=False)

    # also keep full trajectory snapshot
    feats.to_csv(out_dir / f"{cell_id}_trajectory.csv", index=False)

    trends = analyze_all_metrics(feats, keys=keys, routine_only=True)
    trends.to_csv(out_dir / f"{cell_id}_trend_summary.csv", index=False)

    narrative = narrative_from_trends(trends, cell_id=cell_id)
    (out_dir / f"{cell_id}_trend_narrative.md").write_text(narrative, encoding="utf-8")
    write_markdown(out_dir / f"{cell_id}_METRICS_REPORT.md", cell_id=cell_id, trends=trends, narrative=narrative)

    (out_dir / "metric_catalog.json").write_text(
        json.dumps(catalog_as_records(), indent=2, ensure_ascii=False), encoding="utf-8",
    )

    pdf_path = out_dir / f"{cell_id}_metrics_panel.pdf"
    build_pdf(pdf_path, cell_id=cell_id, feats=feats, trends=trends, narrative=narrative)
    print(narrative)
    print(f"wrote {pdf_path}")
    return {"cell_id": cell_id, "n_metrics": len(keys), "pdf": str(pdf_path)}


def main() -> None:
    p = argparse.ArgumentParser(description="Cycle metrics multi-panel + trend analysis")
    p.add_argument("--trajectory", type=Path, action="append", default=None, help="trajectory CSV")
    p.add_argument("--trajectory-dir", type=Path, default=None, help="dir of *_trajectory.csv")
    p.add_argument("--raw", type=Path, action="append", default=None, help="raw cycler CSV")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--halfcell-dir", type=Path, default=None)
    p.add_argument("--step", type=int, default=10)
    args = p.parse_args()

    jobs: list[tuple[str, pd.DataFrame]] = []

    if args.trajectory:
        for path in args.trajectory:
            df = load_trajectory(path)
            cid = str(df["cell_id"].iloc[0]) if "cell_id" in df.columns else path.stem.replace("_trajectory", "")
            jobs.append((cid, df))
    if args.trajectory_dir:
        for path in sorted(args.trajectory_dir.glob("*_trajectory.csv")):
            df = load_trajectory(path)
            cid = str(df["cell_id"].iloc[0]) if "cell_id" in df.columns else path.stem.replace("_trajectory", "")
            jobs.append((cid, df))
    if args.raw:
        for path in args.raw:
            print(f"diagnose {path.name} ...", flush=True)
            df = diagnose_raw(path, step=args.step, halfcell_dir=args.halfcell_dir)
            cid = path.stem.replace("_raw", "")
            jobs.append((cid, df))

    if not jobs:
        raise SystemExit("Provide --trajectory, --trajectory-dir, and/or --raw")

    # de-dupe by cell_id (last wins)
    by_id = {cid: df for cid, df in jobs}
    results = []
    for cid, df in by_id.items():
        cell_out = args.out_dir / cid if len(by_id) > 1 else args.out_dir
        print(f"panel {cid} → {cell_out}", flush=True)
        results.append(process_one(df, cell_id=cid, out_dir=cell_out))

    (args.out_dir / "index.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"done {len(results)} cell(s) → {args.out_dir}")


if __name__ == "__main__":
    main()
