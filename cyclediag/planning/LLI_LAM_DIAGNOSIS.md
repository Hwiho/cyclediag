# LLI·LAM 진단 및 하프셀 로드맵

**상태:** 활성 정책 (2026-07-27)  
**Feature set 목표:** `vp_lges_cycle_v2`  
**현재 구현 feature set:** `vp_lges_cycle_v1` (지표 추출) → v2에서 진단 컬럼·불확실성 스키마 추가

관련: [FEATURES.md](FEATURES.md) · [LABELS.md](LABELS.md) · [../specs/degradation-mode-diagnosis.md](../specs/degradation-mode-diagnosis.md)

---

## 정책 요약 (필수)

현재 버전에서는 **full-cell voltage/current profile**을 기반으로 LLI, LAM_PE, LAM_NE를 **추정·진단**한다.  
진단 결과에는 사용한 방법, 근거 feature, 신뢰도 및 불확실성을 함께 제공한다.

추후 하프셀 데이터가 확보되면 full-cell 기반 진단을 **검증·교정**하고, 전극별 열화 기여도 및 정량 추정 정확도를 **고도화**한다.

### Full-cell 우선 스택 (하프셀 없이 — 현재 메인)

상세 DoD·순서: [IMPROVEMENT_ROADMAP.md §0](IMPROVEMENT_ROADMAP.md#0-full-cell-우선-스택-하프셀-없이)

| ID | 기능 | 역할 |
|----|------|------|
| F1 | ICA/DVA 곡선 생성 | dQ/dV · dV/dQ |
| F2 | 피크 자동 검출 | V/H/area/W/sign |
| F3 | 피크 matching | cycle 간 identity |
| F4 | 피크 위치 이동 | LLI / slippage pattern |
| F5 | 피크 면적 감소 | LAM_PE pattern (Si: LAM_NE 피크 단독 금지) |
| F6 | 곡선 correlation | ΔQ(V) · baseline 유사도 |
| F7 | 저항·polarization 증가 | 접촉/계면/확산 |
| F8 | change-point 탐지 | knee · 급변 시점 |

하프셀 DMA는 Phase 3 **교정**이며, 위 8가지의 **전제 조건이 아니다**.

**데이터 (2026-08-06):** BOL 양·음극 하프셀(C/20)이 [`example/fixtures/halfcell/`](../../example/fixtures/halfcell/README.md)에 있음.  
음극 cycle 1–3. **열화 후 하프셀은 아직 없음.**

### 삭제된 제한 (적용 금지)

다음 취지의 문장·구현은 **사용하지 않는다**.

- 하프셀 데이터가 없으므로 LLI, LAM_NE, LAM_PE 진단 기능을 구현하지 않는다.
- 현재 버전에서는 LLI, LAM_NE, LAM_PE를 출력하지 않는다.
- 하프셀 없이 LLI·LAM을 확정적으로 진단해서는 안 된다.  
  → **확정값처럼 무조건 출력하지 않는다**는 불확실성 원칙은 유지하되, **진단 기능 자체를 끄지 않는다**.

---

## 1. 현재 버전의 열화 원인진단 목표

`vp_lges_cycle_v2`에서는 하프셀 데이터가 없더라도 full-cell profile에서 추출한 지표로 다음 모드를 진단한다.

| 모드 | 의미 |
|------|------|
| LLI | Loss of Lithium Inventory |
| LAM_PE | Loss of Active Material (Positive) |
| LAM_NE | Loss of Active Material (Negative) |
| impedance growth | 저항 성장 |
| polarization / transport limitation | 분극·수송 제한 |
| electrode slippage / operating-window shift | 전극 미끄러짐·동작창 이동 |
| lithium plating (suspect) | 도금 의심 패턴 |
| contact / cell-level R (suspect) | 접촉·셀 수준 저항 증가 의심 |

하프셀이 없다는 이유로 LLI·LAM 진단을 **제외하지 않는다**.

### Full-cell에서 LLI·LAM 추정에 쓰는 정보

- full-cell dQ/dV · dV/dQ peak 위치·간격·면적·폭
- peak 이동, 소멸, merge, split
- 고정 전압 기준 용량 landmark (`Q_at_V`)
- voltage-band별 용량
- SOC / baseline-Q 좌표의 말단 cliff
- cutoff margin
- plateau 위치·폭
- rest voltage · relaxation (τ 포함)
- 충·방전 시작 저항 및 저항 분해
- CV current decay
- hysteresis · voltage efficiency
- Delta-Q · 전체 곡선 형상 (DTW 등)
- degradation trajectory · knee transition

---

## 2. 진단 결과 표현 원칙 — 3 Levels

하프셀이 없어도 아래를 출력할 수 있다. 단 **근거에 따라 수준을 구분**한다.

| Level | 이름 | 예시 컬럼 | 의미 |
|-------|------|-----------|------|
| **1** | Pattern score | `LLI_pattern_score`, `LAM_PE_pattern_score`, `LAM_NE_pattern_score`, `impedance_pattern_score` | 물리 패턴·rule 기반 **상대 정합도** (절대 열화량 아님) |
| **2** | Model-based estimate | `LLI_est`, `LAM_PE_est`, `LAM_NE_est`, `electrode_slippage_est` | fitting / synthetic / (weakly) supervised. `%` 또는 capacity fraction이면 **정의·baseline을 명시** |
| **3** | Half-cell-calibrated | `LLI_est_hc_calibrated`, `LAM_PE_est_hc_calibrated`, `LAM_NE_est_hc_calibrated` | 하프셀 연동 보정·검증 (**Phase 3**) |

**현재 버전:** Level 1 + 가능한 범위의 Level 2.  
검증이 부족한 `*_est`는 억지로 만들지 말고 **`*_pattern_score`를 우선**한다.

---

## 3. Full-cell 기반 degradation-mode estimation

가능하면 pristine full-cell 또는 초기 정상 cycle reference를 사용한다.

### 3.1 LLI 후보 패턴

- 양·음극 반응 window의 상대 이동
- peak spacing / alignment 변화
- 고정 전압 `Q_at_V`의 일관된 이동
- charge/discharge endpoint 조기 도달
- cutoff margin 감소
- active capacity loss 없이도 가능한 profile shift
- CE 장기 추세·비가역 손실
- rest voltage endpoint shift
- baseline 대비 Delta-Q의 특정 방향 변화

### 3.2 LAM_PE 후보 패턴

- 양극 관련 peak area / voltage-band capacity 감소
- 양극 plateau width 축소
- discharge 평균 전압·energy profile 변화
- **위치 이동보다 면적 감소** 중심 변화
- 고SOC / 양극 endpoint 형상 변화

### 3.3 LAM_NE 후보 패턴

- 음극 staging peak area·spacing 변화
- 저SOC / 방전 말단 cliff 변화
- charge acceptance · CV decay 변화
- 음극 endpoint 관련 cutoff margin
- 저SOC 충전 시작 저항 증가
- 음극 voltage-band capacity 축소

### 3.4 Impedance growth 후보 패턴

- `R_fast`, `R_10s`, `R_60s` 증가
- polarization / diffusion component 증가
- CV 시간·tail ratio·current-decay τ 증가
- hysteresis · cycle energy loss 증가
- voltage efficiency 감소
- rest relaxation slow component 증가

**가중치:** mode별 score 식은 **config 또는 model artifact**로 관리한다.  
코드에 해석 불가한 **고정 weight를 하드코딩하지 않는다**.

---

## 4. 불확실성 처리

진단은 수행하되 **확정값처럼 무조건 출력하지 않는다**. 각 결과에 다음을 동반한다.

| 필드 | 의미 |
|------|------|
| `estimate` | 점수 또는 추정값 |
| `confidence` | 0–1 |
| `evidence_count` | 지지 근거 수 |
| `supporting_features` | 지지 feature 목록 |
| `conflicting_features` | 상충 feature 목록 |
| `data_quality_score` | 입력/프로토콜 품질 |
| `diagnosis_valid` | 출력 유효 여부 |
| `diagnosis_version` | 예: `fullcell_v1` vs 향후 `hc_calibrated_v1` |

### Confidence를 낮추거나 보류하는 경우

- profile coverage 부족
- peak matching confidence 부족
- protocol / C-rate / cutoff / rest 시간 변경
- 여러 모드가 유사 pattern을 만듦 (식별 가능성↓)
- baseline profile 품질 부족

JSON 예시:

```json
{
  "degradation_mode": "LLI",
  "estimate": 0.12,
  "unit": "relative_fraction",
  "confidence": 0.71,
  "supporting_features": [
    "peak_spacing_shift",
    "dchg_Q_at_V3.6_delta",
    "dchg_V_cutoff_margin",
    "EoD_restV_end_delta"
  ],
  "conflicting_features": ["dchg_peak_area_loss"],
  "diagnosis_valid": true,
  "diagnosis_version": "fullcell_v1"
}
```

---

## 5. 방법 우선순위

| 순서 | Method | 용도 |
|------|--------|------|
| **A** | Rule-based pattern diagnosis | 빠른 구현, 방향성 검증, 전문가 cross-check, 설명 |
| **B** | Full-cell curve fitting | empirical deformation, OCV library, synthetic LLI/LAM, parametric shift/scale |
| **C** | Data-driven mode model | post-mortem / 전문가 label 있을 때; **cell·batch·protocol 분리 검증** |

Method B parameter 예: Li inventory shift, PE/NE capacity scale, electrode offset/slippage, R·polarization scale.  
reference 품질이 낮으면 **절대값보다 cycle 간 상대 변화**를 우선한다.

---

## 6. 현재 버전 권장 출력 컬럼

### Pattern / risk scores (우선)

- `LLI_pattern_score`
- `LAM_PE_pattern_score`
- `LAM_NE_pattern_score`
- `impedance_pattern_score`
- `transport_limitation_score`
- `plating_risk_score`
- `contact_loss_score`

### Quantitative estimates (검증 가능할 때만)

- `LLI_est`, `LAM_PE_est`, `LAM_NE_est`
- `electrode_slippage_est`

### Confidence / meta

- `LLI_confidence`, `LAM_PE_confidence`, `LAM_NE_confidence`
- `diagnosis_quality_score`
- `diagnosis_valid`
- `diagnosis_method`
- `diagnosis_model_version`

---

## 7. 하프셀의 추후 역할 (필수조건이 아님)

하프셀은 LLI·LAM을 **처음 가능하게 하는 조건이 아니라**, full-cell 진단을 **고도화**하는 후속 기능이다.

1. **검증:** full-cell `LAM_PE/NE` vs 수확 전극 잔존 가역용량; peak attribution; 전극별 R/kinetics 기여  
2. **교정:** pattern↔state 관계, `*_est` scale, chemistry·조건별 threshold, FP/FN, confidence calibration  
3. **원인분해:** intrinsic capacity loss 분리, electrode peak library, OCV reconstruction, balancing/stoichiometry, label 정밀화  

Half-cell 추가 시 full-cell 결과를 **교체하지 않고** 검증·교정·고도화할 수 있는 인터페이스를 유지한다.  
비교용 **calibration schema**는 Phase 1에서 사전 정의한다 → [degradation-mode-diagnosis.md](../specs/degradation-mode-diagnosis.md).

---

## 8. 로드맵 Phases

### Phase 1 — Full-cell 기반 진단 (**현재 작업 범위**)

- `vp_lges_cycle_v2` feature
- Delta-Q · fixed-voltage landmark
- peak matching · peak-shape 확장
- rest · resistance decomposition
- CV kinetics
- hysteresis · voltage efficiency
- stress history
- causal knee detection
- full-cell LLI/LAM **pattern diagnosis**
- 가능한 범위의 full-cell **quantitative estimation**
- confidence · uncertainty 출력
- half-cell calibration **schema** 사전 정의 (구현은 스텁/인터페이스)

### Phase 2 — 온도

- 온도 동특성 · exposure
- R temperature normalization
- 열화지표×온도 interaction
- 조건별 진단 안정성

### Phase 3 — Half-cell-assisted

- pristine electrode OCV library
- aged harvested half-cell 연동
- full-cell ↔ electrode peak mapping
- OCV reconstruction
- `*_est_hc_calibrated`
- slippage / stoichiometric endpoint 정밀화
- 전극별 impedance attribution
- validation · retraining
- **외부 참고 (내장 금지):** [PyDMA](https://github.com/tum-ees/PyDMA) 과학 기능(LLI/LAM/stoich/blend, OCV+ICA+DVA 가중 fit) + [PyProBE](https://github.com/ImperialCollegeLondon/PyProBE) API(`OCP`/`CompositeOCP`, batch DMA, warm-start, `quantify_degradation_modes`) — 상세 [IMPROVEMENT_ROADMAP.md §12.3–12.4](IMPROVEMENT_ROADMAP.md#123-pydma에서-가져올-것-dma-과학--목표에-가장-근접)

### Phase 4 — 통합 원인진단

full-cell + 온도 + half-cell reference + post-mortem + stress history → 통합 degradation-mode 모델.

---

## 9. 완료 조건 (DoD)

- [x] full-cell 기반 LLI·LAM 진단 기능 포함 (`cyclediag/diagnosis/`)
- [x] pattern score 형태로 출력 (`*_pattern_score`; `*_est`는 검증 전 null)
- [x] confidence + supporting feature 동반
- [x] 하프셀 부재를 이유로 진단을 **비활성화하지 않음**
- [x] `fullcell_v1` vs `hc_calibrated_v1` **버전 구분**
- [x] 하프셀은 Phase 3 roadmap에 명시
- [x] half-cell 추가 시 교체가 아닌 검증·교정 인터페이스 (`calibrate` stub)
- [x] full-cell 추정 vs half-cell 실측 비교용 **calibration schema** 사전 정의

---

*2026-07-27: 하프셀 필수조건 제거 · full-cell LLI/LAM 진단 정책으로 개정*  
*2026-08-06: Phase 3에 PyDMA·PyProBE 참고 링크 추가*  
*2026-08-06: Full-cell 우선 스택 F1–F8 (하프셀 없이)를 메인 트랙으로 명시*
