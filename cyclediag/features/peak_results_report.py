"""Build human-readable markdown summary from peak export outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _df_to_md(df: pd.DataFrame, float_fmt: str = ".4f") -> str:
    if df.empty:
        return ""
    rows = []
    headers = list(df.columns)
    rows.append("| " + " | ".join(str(h) for h in headers) + " |")
    rows.append("| " + " | ".join("---" for _ in headers) + " |")
    for _, row in df.iterrows():
        cells = []
        for v in row:
            if isinstance(v, float):
                cells.append(format(v, float_fmt))
            else:
                cells.append(str(v))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _top_fade_correlations(path: Path, n: int = 8) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty or "pearson_r" not in df.columns:
        return df
    return df.reindex(df["pearson_r"].abs().sort_values(ascending=False).index).head(n)


def _assign_method_counts(long_path: Path) -> dict[str, int]:
    if not long_path.exists():
        return {}
    df = pd.read_csv(long_path)
    if "assign_method" not in df.columns:
        return {}
    return df["assign_method"].value_counts().to_dict()


def build_results_markdown(cell_dir: Path) -> str:
    """Generate RESULTS.md content for one cell export folder."""
    cell_dir = Path(cell_dir)
    meta_files = sorted(cell_dir.glob("*_peak_features_meta.json"))
    if not meta_files:
        raise FileNotFoundError(f"no meta json in {cell_dir}")
    meta = _read_json(meta_files[0])
    cell_id = meta.get("cell_id", cell_dir.name)
    outputs = meta.get("outputs", {})
    cfg = meta.get("config", {})

    fade_path = Path(outputs.get("fade_correlation", ""))
    if not fade_path.is_absolute():
        fade_path = cell_dir / fade_path.name if fade_path.name else cell_dir / f"{cell_id}_peak_fade_correlation.csv"
    fade_top = _top_fade_correlations(fade_path)

    summary_path = cell_dir / f"{cell_id}_peak_tracking_summary.csv"
    summary_tbl = ""
    if summary_path.exists():
        s = pd.read_csv(summary_path)
        cols = [
            c for c in (
                "leg", "peak_id", "V_mean", "H_norm_mean", "dV_dcycle_mean", "dH_abs_dcycle_mean",
            )
            if c in s.columns
        ]
        summary_tbl = _df_to_md(s[cols])

    assign_counts = _assign_method_counts(cell_dir / f"{cell_id}_peak_trajectory_long.csv")

    lines = [
        f"# {cell_id} — Peak 분석 결과 요약",
        "",
        "> 자동 생성 (`cyclediag/tools/summarize_peak_results.py`). 수동 메모는 하단에 추가.",
        "",
        "## 한눈에 보기",
        "",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| 총 사이클 | {meta.get('n_cycles_total', '—')} |",
        f"| usable (양쪽 leg) | {meta.get('n_cycles_usable', '—')} |",
        f"| 제외 | {meta.get('n_cycles_excluded', '—')} |",
        f"| golden cycles | {meta.get('good_cycles', [])} |",
        f"| assign 모드 | {meta.get('assign_mode', '—')} |",
        f"| SG window | {cfg.get('sg_window', '—')} |",
        f"| 프로토콜 제외 | {'RPT+capacheck' if meta.get('exclude_protocol') else '없음'} |",
        "",
    ]

    proto = meta.get("protocol_exclusion") or {}
    if proto:
        lines.extend([
            "## Routine-life 제외 (RPT / capacheck)",
            "",
            f"| 항목 | 값 |",
            f"|------|-----|",
            f"| RPT 사이클 | {proto.get('n_rpt', '—')} |",
            f"| capacheck (저용량) | {proto.get('n_capacheck', '—')} |",
            f"| RPT 직후 버퍼 | {proto.get('n_post_rpt', '—')} (각 블록 +{proto.get('post_rpt_exclude', 5)}cyc) |",
            f"| 제외 합계 | {proto.get('n_excluded_total', '—')} |",
            "",
            "※ RPT 전용 분석은 별도 프로토콜 예정. 현재 peak/fade 파이프라인은 **0.5C routine life** 만 대상.",
            "",
        ])
        req = meta.get("good_cycles_requested") or []
        used = meta.get("good_cycles") or []
        dropped = sorted(set(req) - set(used))
        if dropped:
            lines.extend([
                f"Golden에서 제외된 사이클 (프로토콜): `{dropped}`",
                "",
            ])

    lines.extend([
        "## 파일 맵 (무엇을 보면 되나)",
        "",
        "| 용도 | 파일 |",
        "|------|------|",
        "| **메인 테이블** (사이클×peak + SoHQ) | `*_peak_cycle_merged.csv` |",
        "| peak 추적 long (V, H, H_norm, drift) | `*_peak_tracking.csv` |",
        "| 사이클당 wide feature | `*_peak_features.csv` |",
        "| usable만 필터 | `*_peak_features_usable.csv` |",
        "| golden 기준 V/H | `*_peak_golden_ref.csv` |",
        "| peak별 drift 요약 | `*_peak_tracking_summary.csv` |",
        "| peak vs fade 상관 | `*_peak_fade_correlation.csv` |",
        "| assign 학습 규칙 | `*_peak_assign_model/learned_criteria.json` |",
        "| ML 이상탐지 (부가) | `*_peak_ml_predictions.csv` |",
        "| RPT/capacheck 플래그 | `*_protocol_flags.csv` |",
        "| 프로토콜 제외 목록 | `*_protocol_exclude.json` |",
        "| 궤적 그래프 | `plots/*_peak_tracking.png` |",
        "| **머신 인덱스** | `*_peak_features_meta.json` |",
        "",
    ])

    if assign_counts:
        lines.extend([
            "## Peak assign 방법 분포",
            "",
            "| assign_method | 개수 |",
            "|---------------|------|",
        ])
        for k, v in sorted(assign_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {k} | {v} |")
        lines.append("")

    if not fade_top.empty:
        lines.extend([
            "## Fade와 상관 큰 peak feature (usable)",
            "",
            _df_to_md(fade_top, float_fmt=".3f"),
            "",
            "※ 용량 기반 지표(SoHQ, dchgCapa)와 H가 같이 움직이면 peak **세기**보다 **용량 스케일** 영향일 수 있음 — `*_V` drift도 함께 확인.",
            "",
        ])

    if summary_tbl:
        lines.extend([
            "## Peak별 궤적 요약 (usable)",
            "",
            summary_tbl,
            "",
        ])

    lines.extend([
        "## 해석 체크리스트",
        "",
        "1. `plots/` — P2_shoulder / P3_main V·H_norm이 매끄러운가?",
        "2. `*_peak_features_excluded.csv` — 제외 사유(노이즈, band_gap) 확인",
        "3. `*_peak_fade_correlation.csv` — SoHQ와 같이 가는 **위치(V)** 컬럼 찾기",
        "4. golden cycle (TC10 등) — `good_cycle_ref=True` 행이 기대와 맞는가?",
        "",
        "## 수동 메모",
        "",
        "<!-- 여기에 검수 노트, 이상 TC, 다음 실험 계획 -->",
        "",
    ])
    return "\n".join(lines)


def write_results_report(cell_dir: Path) -> Path:
    cell_dir = Path(cell_dir)
    out = cell_dir / "RESULTS.md"
    out.write_text(build_results_markdown(cell_dir), encoding="utf-8")
    return out
