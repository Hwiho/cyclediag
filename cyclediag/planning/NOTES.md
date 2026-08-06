# VP Diagnosis — Notes

> 에이전트·개발 시 **최우선** 참고. pne_studio `planning/NOTES.md` 와 동일 패턴.

---

## 지시 사항 (활성)

<!--
# 한 줄 지시
'''
여러 줄 지시
'''
-->

# Full-cell 기반 LLI·LAM 진단 활성 — 하프셀은 Phase 3 검증·교정용 (필수조건 아님)
'''
- 정책 문서: planning/LLI_LAM_DIAGNOSIS.md
- 스펙: specs/degradation-mode-diagnosis.md
- 현재: Level 1 pattern score 우선 (+ 검증된 범위의 Level 2 est)
- 하프셀 부재를 이유로 LLI/LAM_PE/LAM_NE 진단을 끄지 않음
- 확정값처럼 무조건 출력 금지 — confidence / supporting_features / diagnosis_version 동반
- diagnosis_version: fullcell_v1 → 이후 hc_calibrated_v1 (교체가 아니라 병행·교정)
'''

# 설계가 달라도 **동일 활물질(chemistry)** 이면 유사한 열화 거동이 나타날 수 있음
# VP 특정 구간의 **전압 급강하(cliff/kink)** 가 물리적으로 무엇인지 추출·해석하는 것이 핵심 목표
'''
- lot/footprint 설계 차이는 정규화로 흡수, material fingerprint(dQ/dV peak V 등)로 정렬
- cliff = |dV/dQ| 극대 구간 → 위치(V, SOC_norm), 기울기, 폭, cycle 간 drift 추적
- 단일 QC 이상탐지보다 **열화 메커니즘 후보**를 리포트하는 방향
'''

---

## 합의됨

| 날짜 | 내용 |
|------|------|
| 2026-06-26 | pne_studio와 **별개** 프로젝트로 `cyclediag` 생성 |
| 2026-06-26 | PNE CSV 형식 호환, 코드 의존성 없음 |
| 2026-06-26 | 1차 추천: hand-crafted feature + 이상 탐지 → 이후 supervised |
| 2026-06-26 | **물질(chemistry) 중심** reference — 설계 차이는 secondary 정규화 |
| 2026-06-26 | **전압 급강하 구간(cliff)** 탐지·물리 해석 맵핑이 핵심 관심사 |
| 2026-07-09 | dQ/dV peak 단계별 로드맵 → `PEAK_TRACKING_ROADMAP.md` |
| 2026-07-09 | **M01Ch025** 1차 기준 채널; golden TC **10, 15, 12, 58, 149** (Tier 1), TC **14·69** 조건부 → `GOLDEN_CYCLES.md` |
| 2026-07-09 | 사이클 간 추적: **V-anchor assign** + **H_norm** (세기 변화는 정규화·시계열로) |
| 2026-07-27 | **Full-cell LLI·LAM 진단** 채택. 하프셀은 Phase 3 검증·교정. 정책: `LLI_LAM_DIAGNOSIS.md` |
| 2026-08-06 | **BatteryML · PyBaMM 참고**를 로드맵에 반영 — 패키지 내장 없이 CellData/FeatureSet·ΔQ(V)·전극 SOH 스키마. 상세: `IMPROVEMENT_ROADMAP.md` §12 |
| 2026-08-06 | **PyDMA · PyProBE · DiffCapAnalyzer** 추가 — DMA는 PyDMA 과학+PyProBE API; ICA peak descriptor는 DiffCapAnalyzer. §12.3–12.5 |
| 2026-08-06 | **Full-cell 우선 스택 F1–F8** — ICA/DVA·peak·corr·R·change-point. 하프셀 없어도 MVP 완성. 상세: `IMPROVEMENT_ROADMAP.md` §0 |
| 2026-08-06 | **DOE2 비교 CLI** — `compare-doe`: 양극 동일·음극 상이(SJ900 vs SJ1300) early params + mode contrast |

---

## 미확정 / backlog

### 제품 방향
- [x] **A/C 혼합:** 하프셀 없이 full-cell 스택(F1–F8)으로 진단·추적 우선 (2026-08-06)
- [ ] **B.** 라벨 있는 불량 분류 (soft short, Li plating, …)
- [ ] **C.** 수명/용량 fade 예측 (회귀) — BatteryML Severson ΔQ(V) 경로 (§5.7 / §12) — F6과 병행
- [ ] **D.** Half-cell DMA — BOL OCP fixture로 프로토타입 가능; **aged 하프셀은 미확보** (DM-P3)
- [ ] **E.** **DOE1**에서 set1/set4 중 어느 wet·dry인지 확정 후 arm 폴더 rename
### 데이터
- [ ] 보유 라벨 데이터 규모? (대략 N cells × M cycles)
- [ ] 정상 reference: 동일 설계 lot 평균 vs 단일 golden cell
- [ ] `_raw.csv` vs processed CSV 우선

### Feature
- [ ] CC 구간만 vs CC+CV
- [ ] Specific capacity (mass 필요) vs raw mAh
- [ ] dQ/dV peak 몇 개까지? (상위 3 peak?)

### 모델·스택
- [ ] `scikit-learn` only MVP vs `xgboost` 포함
- [ ] `pyod` (Python Outlier Detection) 사용 여부

### UI
- [ ] CLI only 충분한 기간?
- [ ] GUI는 pne_studio 스타일 Tk vs 웹 (Streamlit)

---

## 당신 코멘트 (처리 이력)

| 날짜 | 지시 | 상태 |
|------|------|------|
| 2026-06-26 | ML VP 진단 도구 로드맵·노트 제작 | Done — planning 초안 |
| 2026-07-27 | LLI·LAM / 하프셀 정책 수정 (full-cell 진단 활성) | Done — `LLI_LAM_DIAGNOSIS.md` + spec |

---

## 참고 링크

- pne_studio VP: `Voltage (V)` vs `Capacity (mAh)` / specific
- pne_studio 파이프라인: CC trim → 보간 → dQ/dV (참고만, 코드 재사용 안 함)
