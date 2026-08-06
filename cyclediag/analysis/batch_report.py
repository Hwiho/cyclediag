"""Batch diagnosis report for multiple StepEnd / cycler files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd

from cyclediag.analysis.dqdv_screen import compare_cells_dqdv, screen_dqdv_by_file, top_dqdv_problems
from cyclediag.analysis.indicator_screen import (
    compare_cells,
    screen_indicators_by_file,
    top_problem_indicators,
)
from cyclediag.features.diagnosis_export import save_diagnosis_pngs
from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_features_table
from cyclediag.features.stepemd_extract import extract_stepemd_features_table
from cyclediag.io.cycler_csv import ColumnMap, normalize_cycler_dataframe
from cyclediag.io.stepemd_csv import discover_stepemd_files, load_stepemd_csv
from cyclediag.models.predict import predict_features


def _is_stepemd(path: Path) -> bool:
    return "StepEnd" in path.name or path.name.endswith("StepEnd.csv")


def extract_features_from_file(path: Path, *, encoding: str = "cp949") -> pd.DataFrame:
    if _is_stepemd(path):
        return extract_stepemd_features_table(path, encoding=encoding)
    from cyclediag.io.cycler_csv import load_cycler_csv

    cmap = ColumnMap.studio_default()
    df = load_cycler_csv(str(path), column_map=cmap)
    cfg = LgesExtractConfig(cell_id=path.parent.name)
    return extract_lges_features_table(df, filepath=str(path), config=cfg)


def run_batch_report(
    input_dir: str | Path,
    *,
    output_dir: str | Path | None = None,
    files: list[str | Path] | None = None,
    encoding: str = "cp949",
    top_n: int = 12,
    write_pngs: bool = True,
) -> dict:
    """Analyze files, write CSV + HTML report. Returns summary dict."""
    input_dir = Path(input_dir)
    out_dir = Path(output_dir) if output_dir else input_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    feat_dir = out_dir / "diagnosis_features"
    feat_dir.mkdir(exist_ok=True)

    if files:
        paths = [Path(f) for f in files]
    else:
        paths = discover_stepemd_files(input_dir)
        if not paths:
            paths = sorted(input_dir.rglob("*.csv"))[:20]

    if not paths:
        raise FileNotFoundError(f"No CSV files found under {input_dir}")

    all_features: list[pd.DataFrame] = []
    per_cell: dict[str, dict] = []

    for path in paths:
        table = extract_features_from_file(path, encoding=encoding)
        if table.empty:
            per_cell.append({
                "cell_id": path.parent.name,
                "file": str(path),
                "status": "empty",
                "n_cycles": 0,
            })
            continue
        cid = str(table["cell_id"].iloc[0]) if "cell_id" in table.columns else path.parent.name
        safe = cid.replace("[", "_").replace("]", "")
        table.to_csv(feat_dir / f"{safe}_features.csv", index=False)
        all_features.append(table)

        cyc = pd.to_numeric(table["cycle"], errors="coerce")
        sohq_end = None
        if "SoHQ" in table.columns:
            s = pd.to_numeric(table["SoHQ"], errors="coerce").dropna()
            if not s.empty:
                sohq_end = round(float(s.iloc[-1]), 2)
        per_cell.append({
            "cell_id": cid,
            "file": str(path),
            "status": "ok",
            "n_cycles": int(cyc.nunique()),
            "cycle_range": [int(cyc.min()), int(cyc.max())],
            "SoHQ_end": sohq_end,
        })

    if not all_features:
        raise RuntimeError("No features extracted from any file")

    combined = pd.concat(all_features, ignore_index=True)
    combined.to_csv(out_dir / "all_features.csv", index=False)

    screened = screen_indicators_by_file(combined)
    screened.to_csv(out_dir / "indicator_screen_all.csv", index=False)

    dqdv_screen = screen_dqdv_by_file(combined)
    if not dqdv_screen.empty:
        dqdv_screen.to_csv(out_dir / "dqdv_screen_all.csv", index=False)

    compare = compare_cells(combined) if combined["cell_id"].nunique() >= 2 else pd.DataFrame()
    if not compare.empty:
        compare.to_csv(out_dir / "compare_cells.csv", index=False)

    dqdv_cmp = compare_cells_dqdv(combined) if combined["cell_id"].nunique() >= 2 else pd.DataFrame()
    if not dqdv_cmp.empty:
        dqdv_cmp.to_csv(out_dir / "compare_dqdv.csv", index=False)

    diag = predict_features(combined)
    diag.to_csv(out_dir / "diagnosis_scores.csv", index=False)

    png_paths: list[Path] = []
    if write_pngs:
        png_dir = out_dir / "png_reports"
        if "cell_id" in combined.columns:
            for cid, grp in combined.groupby("cell_id", sort=False):
                safe = str(cid).replace("[", "_").replace("]", "")
                sub = screened[screened["cell_id"] == cid] if "cell_id" in screened.columns else screened
                png_paths.extend(
                    save_diagnosis_pngs(
                        grp, png_dir, stem=safe, screened=sub, per_cell=False,
                    )
                )
        else:
            png_paths.extend(
                save_diagnosis_pngs(
                    combined, png_dir, stem="all", screened=screened, per_cell=False,
                )
            )

    # Per-cell top problems
    cell_summaries = []
    for info in per_cell:
        if info.get("status") != "ok":
            cell_summaries.append({**info, "top_indicators": []})
            continue
        cid = info["cell_id"]
        sub = screened[screened["cell_id"] == cid] if "cell_id" in screened.columns else screened
        tops = top_problem_indicators(sub, n=top_n)
        dq_sub = dqdv_screen[dqdv_screen["cell_id"] == cid] if not dqdv_screen.empty and "cell_id" in dqdv_screen.columns else pd.DataFrame()
        dq_tops = top_dqdv_problems(dq_sub, n=6) if not dq_sub.empty else pd.DataFrame()
        info["top_indicators"] = tops.to_dict(orient="records") if not tops.empty else []
        info["top_dqdv"] = dq_tops.to_dict(orient="records") if not dq_tops.empty else []
        cell_summaries.append(info)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(out_dir),
        "n_files": len(paths),
        "n_cells_ok": sum(1 for c in cell_summaries if c.get("status") == "ok"),
        "cells": cell_summaries,
        "compare_top": compare.head(top_n).to_dict(orient="records") if not compare.empty else [],
        "compare_dqdv_top": dqdv_cmp.head(top_n).to_dict(orient="records") if not dqdv_cmp.empty else [],
        "png_reports": [str(p) for p in png_paths],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    html = _render_html_report(summary, screened, compare, dqdv_cmp)
    (out_dir / "diagnosis_report.html").write_text(html, encoding="utf-8")

    return summary


def _df_to_html_table(df: pd.DataFrame, max_rows: int = 15) -> str:
    if df is None or df.empty:
        return "<p><em>데이터 없음</em></p>"
    sub = df.head(max_rows)
    cols = list(sub.columns)
    head = "".join(f"<th>{escape(str(c))}</th>" for c in cols)
    body_rows = []
    for _, row in sub.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float) and pd.notna(v):
                cells.append(f"<td>{v:.4g}</td>")
            else:
                cells.append(f"<td>{escape('' if pd.isna(v) else str(v))}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def _render_html_report(
    summary: dict,
    screened: pd.DataFrame,
    compare: pd.DataFrame,
    dqdv_cmp: pd.DataFrame,
) -> str:
    ts = summary.get("generated_at", "")
    parts = [
        "<!DOCTYPE html><html lang='ko'><head><meta charset='utf-8'>",
        "<title>Cycle Diagnosis Report</title>",
        "<style>",
        "body{font-family:Malgun Gothic,Segoe UI,sans-serif;margin:24px;line-height:1.45;color:#222}",
        "h1,h2{color:#1565C0} table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px}",
        "th,td{border:1px solid #ccc;padding:6px 8px;text-align:left}",
        "th{background:#E3F2FD}.card{border:1px solid #ddd;border-radius:8px;padding:16px;margin:16px 0}",
        ".meta{color:#666;font-size:13px}",
        "</style></head><body>",
        "<h1>500사이클 지표 진단 보고서</h1>",
        f"<p class='meta'>생성: {escape(ts)} · 파일 {summary.get('n_files', 0)}개 · "
        f"성공 {summary.get('n_cells_ok', 0)}셀</p>",
    ]

    for cell in summary.get("cells", []):
        cid = cell.get("cell_id", "?")
        parts.append(f"<div class='card'><h2>{escape(cid)}</h2>")
        if cell.get("status") != "ok":
            parts.append(f"<p>추출 실패: {escape(cell.get('file', ''))}</p></div>")
            continue
        cr = cell.get("cycle_range", [])
        parts.append(
            f"<p>사이클 {cr[0]}–{cr[1]} ({cell.get('n_cycles')} cycles) · "
            f"SoHQ(마지막) {cell.get('SoHQ_end', '—')}%</p>"
        )
        tops = pd.DataFrame(cell.get("top_indicators", []))
        if not tops.empty:
            show = tops[["feature", "severity", "signal", "corr_health", "corr_cycle"]].head(12)
            parts.append("<h3>주요 문제 지표</h3>")
            parts.append(_df_to_html_table(show))
        dq = pd.DataFrame(cell.get("top_dqdv", []))
        if not dq.empty:
            cols = [c for c in ("feature", "severity", "delta_V_mV", "height_fade_pct", "signal") if c in dq.columns]
            parts.append("<h3>dQ/dV peak (해당 시)</h3>")
            parts.append(_df_to_html_table(dq[cols]))
        parts.append("</div>")

    if not compare.empty:
        parts.append("<div class='card'><h2>셀 간 차이 (후반 사이클)</h2>")
        show = compare[["feature", "divergence_score", "max_cell_gap_late", "mean_spread_late"]].head(15)
        parts.append(_df_to_html_table(show))
        parts.append("</div>")

    if dqdv_cmp is not None and not dqdv_cmp.empty:
        parts.append("<div class='card'><h2>dQ/dV peak 셀 간 차이</h2>")
        cols = [c for c in ("feature", "divergence_score", "max_cell_gap_late", "leg", "peak_num") if c in dqdv_cmp.columns]
        parts.append(_df_to_html_table(dqdv_cmp[cols].head(15)))
        parts.append("</div>")

    parts.append(
        "<p class='meta'>CSV: all_features.csv, indicator_screen_all.csv, compare_cells.csv, "
        "summary.json · PNG: png_reports/</p>"
    )
    parts.append("</body></html>")
    return "".join(parts)
