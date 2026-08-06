# VP Diagnosis — Versions

## Policy note (2026-08-06)

- **Full-cell-first stack (no half-cell required):** ICA/DVA → peak detect/match → ΔV/Δarea → curve corr → R/polarization → change-point → `*_pattern_score`. See [IMPROVEMENT_ROADMAP.md §0](IMPROVEMENT_ROADMAP.md#0-full-cell-우선-스택-하프셀-없이).
- **Half-cell BOL fixtures available** at `example/fixtures/halfcell/` (C/20; anode cycles 1–3). **Aged half-cell OCP not available yet.**
- External refs (§12): BatteryML, PyBaMM, PyDMA, PyProBE, DiffCapAnalyzer — concepts/API only, no runtime vendoring. Half-cell DMA is DM-P3 calibration, not a blocker.

## Policy note (2026-07-27)

- Full-cell **LLI / LAM_PE / LAM_NE** diagnosis is in scope for `vp_lges_cycle_v2` (Level 1 pattern scores first).
- Half-cell is **Phase 3 calibration**, not a prerequisite. See [LLI_LAM_DIAGNOSIS.md](LLI_LAM_DIAGNOSIS.md).

---

## v0.1 — Planning (2026-06-26)

**상태:** Current

- `planning/` 로드맵·feature catalog·데이터 스키마·라벨 taxonomy
- `specs/` feature extraction / model pipeline / evaluation 초안
- 패키지 골격: `io`, `features`, `models`, `pipeline`
- 실행: `python run_cyclediag.py --help` (placeholder CLI)

**다음 (v0.2 목표):** Phase 1 — CSV 로드 + Tier 1 feature 10개 + parquet export

---

## v0.2 — Feature MVP (planned)

- PNE CSV loader
- CC/CV split
- F1.1–F1.8, F1.12–F1.13, F1.16–F1.17
- `extract` CLI

---

## v0.3 — Reference distance (planned)

- Golden reference JSON
- DTW / Mahalanobis
- 이상 점수 리포트 (CSV)

---

## v0.4 — ML train/predict (planned)

- Isolation Forest + optional XGBoost
- `train` / `predict` / `evaluate`

---

## v1.0 — Batch + report (planned)

- manifest 배치
- HTML 리포트
- 모델 버전 고정
