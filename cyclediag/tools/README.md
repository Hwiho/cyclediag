# cyclediag tools

라이브러리 API는 `cyclediag.features` / `cyclediag.models` 를 직접 import 하세요.

## 활성 스크립트

| Script | Purpose |
|--------|---------|
| `export_cycle_indicators.py` | **사이클별 Rest V / 저항 / SoHQ·CE → Excel + overview PNG (GUI 없이 점검)** |
| `export_degradation_diagnosis.py` | **Full-cell LLI/LAM/impedance pattern diagnosis (하프셀 불필요)** |
| `export_peak_feature_table.py` | Peak feature CSV export (기본: band assign, RPT 제외) |
| `export_rpt_anchor_assign.py` | **RPT 0.33C anchor → routine 0.5C assign** (±10 hard zone) |
| `export_rpt_peak_overlap.py` | **ML soft-map: 0.33C peaks overlapping on 0.5C bumps** |
| `summarize_peak_results.py` | `RESULTS.md` 요약 생성 |
| `export_dqdv_peak_review.py` | dQ/dV peak PNG 검수 export |
| `score_cycle_dqdv_quality.py` | 저노이즈 cycle 추천 |
| `train_peak_assign_global.py` | multi-cell peak assign 학습 |
| `compare_sg_window_peaks.py` 등 | SG/neighbor/range peak 비교 유틸 |

```bash
# 사이클 지표 점검 → Excel + Inspect CSV + overview PNG (2×3)
python cyclediag/tools/export_cycle_indicators.py --input cell_raw.csv
python run_export_cycle_indicators.py --input C:/data/folder --out-dir C:/tmp
# PNG만:  --no-csv --no-xlsx
# PNG 끄기: --no-png

# Full-cell LLI·LAM pattern diagnosis (Level 1 scores + confidence)
python cyclediag/tools/export_degradation_diagnosis.py \
  --input example/output/M01Ch022_cycle_indicators_tagged_full.csv \
  --from-features --out-dir example/output --stem M01Ch022
# or from raw (re-extract + diagnose):
python cyclediag/tools/export_degradation_diagnosis.py --input path/to/cell_raw.csv --out-dir example/output

# 빠른 routine-life export (band, plots 생략 가능)
python cyclediag/tools/export_peak_feature_table.py \
  --input raw.csv --cell-id M01Ch022 --out-dir example/docs/features --no-plots

# hybrid assign + 재학습
python cyclediag/tools/export_peak_feature_table.py \
  --input raw.csv --cell-id M01Ch022 --assign-mode hybrid --retrain-assign
```

## 레거시 실험

`archive/experiments/` · 구 CLI launcher는 [`../archive/README.md`](../archive/README.md)
