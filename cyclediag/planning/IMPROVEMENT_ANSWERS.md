# IMPROVEMENT_ROADMAP §10 — 확인 질문 답변

> 근거: SJ900 set4 Ch22 raw 실측 · `_vendor/.../dcir_soc_direction_labels.md` · `cycle_protocol.py` · `dqdv_peaks.py` · `peak_assign.py` · `pattern_scoring.py` · `mass-stack.md` · `example/` 산출물  
> 상태: **CONFIRMED** / **PARTIAL** / **UNKNOWN**  
> 갱신: 2026-08-05

---

## 10.1 DC-IR 측정 상세

### 1. 30 s 펄스 내부 샘플링 (특히 첫 1초)
**CONFIRMED — 전 구간 0.1 s (10 Hz)**  
- TC4/5/6/109 방전 펄스: `n=301`, `tmax=30.0 s`, `dt_med=0.1 s`  
- `t ≤ 1 s` 샘플 **11점** (0.0 … 1.0)  
→ **$R_\Omega$ / $R_{ct}$ 3성분 분해에 필요한 첫 1 s ≥ 10 Hz 조건 충족.** 프로토콜 변경 불필요.

### 2. 펄스 전류 크기
**CONFIRMED — ≈ 1C**  
- 펄스 `|I| ≈ 77.34 A`  
- routine 0.5C `|I| ≈ 38.67 A` → 펄스 ≈ 2× = **~1C**  
- RPT/capa `|I| ≈ 25.78 A` ≈ 0.33C

### 3. 펄스 전 rest
**CONFIRMED — 고정 3600 s (1 h)**  
각 SOC 펄스 직전 Rest `tmax=3600`.

### 4. 펄스 직후 회복 rest 기록?
**CONFIRMED — 1800 s (30 min) Rest 기록됨**  
→ `R_recovery_tau` 산출 **가능**.

### 5. SOC 20/50/80 기준
**CONFIRMED — 직전 capacity-check / full 사이클 용량 대비 상대 %**  
- BOL 고정 Ah 아님. local reference 용량으로 누적 방전 Ah → 20/50/80% 제거.  
- 예: ref ~72 Ah → 14.4 / 21.7 / 21.7 Ah 제거 → SOC 80 / 50 / 20.  
→ 열화 시 측정점 이동 혼입 위험 있음 → `soc_basis: relative_current_capacity` 메타 명시 + 절대 Ah 병기 권장.

### 6. SOC 도달 방법
**CONFIRMED — 만충/capa 기준 후 `SOC Completed` 방전(Ah) 단계**  
전압 기준이 아니라 **Ah fraction 방전 → Rest → Pulse**.

### 7. 3점 SOC가 동일 사이클 연속?
**CONFIRMED — 아니오. TotalCycle당 1점, 3사이클 연속 블록**  
예: TC 4=SOC80, 5=SOC50, 6=SOC20 (이후 109–111 …).  
→ 후속 SOC는 앞 펄스 이력을 일부 가짐.

### 8. R 장비 계산 vs raw V–I
**CONFIRMED — raw V–I 저장 + Impedance 컬럼도 존재**  
- Studio/`dcir.py`는 raw `Voltage`/`Current`로 `R(t)=|ΔV|/|ΔI|` (0.1 / 10 / 30 s).  
- `Impedance (ohm)` 컬럼 부분 채움 있음. **3성분 분해는 raw 트레이스로 가능.**

---

## 10.2 RPT / 사이클 프로토콜

### 9. RPT 주기
**CONFIRMED (SJ900 set4) — 약 105 사이클마다**  
DC-IR/RPT 블록: 4–6, 109–111, 214–216, 319–321, 424–426, 529–531.  
논리 라벨은 `(1, 100, 200, …)` 계열.

### 10. RPT C/3 충·방전? CV?
**CONFIRMED — 충·방전 모두 ≈0.33C (`|I|≈25.78 A`)**  
- capa_full pair (예: TC107–108) 양방향 동일 전류.  
- raw에 `ChargeCVCapacity` 존재 → CC–CV 구조.  
**UNKNOWN:** CV 종료 전류(A 또는 C-rate) 스케줄 문구.

### 11. routine 0.5C 양방향? CV 종료?
**CONFIRMED — 충·방전 모두 ≈0.5C (`|I|≈38.67 A`), 충전 CC–CV**  
- `ChargeCCCapacity` / `ChargeCVCapacity` 모두 비어 있지 않음.  
**UNKNOWN:** 공식 CV cutoff (예: C/20). 일부 사이클 EoC 전류가 높게 남는 구간 있음 → 종료 조건 재확인 권장.  
참고: feature 쪽 `chgCVcapa=0` 보고는 **검출 미스 가능**, raw에 CV Ah는 있음.

### 12. 전압 창 / DOD
**CONFIRMED — ≈ 4.2 V ↔ 2.5 V (full DOD)**  
`chg_V_cutoff≈4.2008`, `dchg_V_cutoff≈2.5000`.

### 13. RPT 직후 용량 회복 bump?
**PARTIAL — 프로토콜상 가정 + 코드에서 처리 / 크기 미정량**  
- `POST_RPT_EXCLUDE = 5` (RPT 블록 후 5사이클 제외).  
- 로드맵은 bump를 전제. Ch22 스냅샷에서 큰 bump는 재측정 안 함 → **플래그 유지, 크기 통계는 추후**.

### 14. formation 사이클 수 / 데이터 잔존?
**PARTIAL**  
- life raw: TC1 Rest → TC2–3 0.33C capa → TC4–6 DC-IR.  
- 별도 formation 스크립트 `automatic_FM_D_0.05C.py` 존재.  
**UNKNOWN:** SJ900 SOP상 formation 정식 사이클 수. life 파일에는 early TC 포함.

### 15. RPT 2사이클 용량 차이?
**CONFIRMED (예시) — 작지만 관측됨**  
TC107 vs 108 방전 Ah: **68.948 vs 68.903** (Δ ≈ **0.045 Ah** ≈ 0.06%).  
→ `Q_relax` 노이즈 하한 후보. 전 블록 통계는 미집계.

---

## 10.3 데이터 · 계측 품질

### 16. routine 샘플링
**CONFIRMED (실측 패턴) — 혼합 트리거**  
TC50 charge: `dt` med≈30 s / max≈60 s / min 0.1 s, `dV` med≈5 mV, `dQ` med≈0.3 Ah.  
**UNKNOWN:** `.sch`에 적힌 Δt/ΔV/ΔQ 설정값 원문.

### 17. 전압 ADC 분해능
**UNKNOWN** — 문서·메타에 없음.

### 18. 온도 기록?
**PARTIAL — 컬럼 있으나 샘플에서 미사용**  
`Temp (Celsius)` 존재, Ch22 raw는 **전부 0.0**.  
코드는 `Temperature`/`Temp`/`CellTemp` 지원. 실측 온도 로그는 이 export에 없음.

### 19. 챔버 온도
**CONFIRMED — 45 °C (파일명/폴더)**  
`..._45도 0.5C cycle_...`  
**UNKNOWN:** 제어 밴드·실측 변동폭.

### 20. dQ/dV 계산
**CONFIRMED**
```
n_interp=500, interp_axis="Q", deriv_mode="smooth_then_diff",
sg_window=21 (도구에선 31 자주 사용), sg_poly=3
```
→ `cyclediag/features/dqdv_peaks.py`

### 21. 피크 검출 기준
**CONFIRMED**  
`prominence_frac=0.02`, `min_distance_frac=0.04`, `min_width_points=5`,  
`mad_prominence_factor=4`, `spike_ratio_max=2.5`, merge `|ΔV|<0.012 V`.  
밴드는 `min_band_height_frac=0.12`.

### 22. Hungarian cost
**CONFIRMED**  
`cost = |ΔV| + h_cost_weight·|ΔH|`, RF 보너스로 감쇠.  
`h_cost_weight=0.015`, `rf_cost_weight=0.5`, `max_match_cost=0.12`.

---

## 10.4 셀 · 재료

### 23. 양극/음극 조성
**PARTIAL — ASSB SJ900 설계 코드 (NMC/LFP/Si% 미명시)**  
- 양극: **S83S ~215 mAh/g**, loading 5 mAh/cm²  
- 음극: **SJ-ASG903 1300 blend ~1306 mAh/g**, loading 5.4 (Si-rich 추정)  
- 워크북: `60Ah_SJ900_..._SJ1300_60-40...`  
- 전압창 2.5–4.2 V → LFP 평탄 경로 아님.  
**UNKNOWN:** NMC 조성비, Si 질량%, LFP 여부( practically No).

### 24. 포맷 · 정격 용량
**PARTIAL**  
- 설계: unit ~41.75 Ah, 2-stack ~83.49 Ah, 18M2U ASSB multi-stack.  
- 실측 Ch22 BOL 방전 ~**72 Ah** 급.  
- 포맷명(파우치/각형) **미명시**; 파일 `QN_mono`.

### 25. 파우치 구속 압력
**UNKNOWN**

### 26. N/P · loading · 두께
**PARTIAL**  
- loading cat/ano **5 / 5.4 mAh/cm²**, area 설계 248.56 cm², **NP ≈ 1.08**.  
- 전극 두께 **미확인**.

### 27. 반쪽셀 OCV
**CONFIRMED — 현재 없음**  
`HalfCellCalibrationNotReady` stub. Level-1은 하프셀 없이 동작.  
→ **P3 `*_est`는 하프셀/문헌 템플릿 확보 전까지 보류가 맞음.**

---

## 10.5 검증 · 목적

### 28. 셀 수 · 사이클 · SoH
**PARTIAL (example 기준)**  
- 초점: set4 **Ch22 (M01Ch022)**, **Ch25 (M01Ch025)**  
- Ch22: TotalCycle **564**, usable routine **337**, usable SoHQ 말기 ~**65%**대  
- Ch25: golden ~153 valid cycles  
- 전체 코호트 N은 NOTES에 미기입.

### 29. replicate 수
**UNKNOWN** — 동일 set의 Ch22 `#1` / Ch25 `#4`는 채널 상이; 공식 replicate 선언 없음.

### 30. post-mortem / half-cell / EIS golden
**CONFIRMED — 레포에 없음**  
calibration example `pending`. → 합성 데이터 + 공개셋이 당분간 검증 주력.

### 31. 의도적 열화 셀
**PARTIAL**  
- 보유: **45 °C · 0.5C** life (고온 SEI 쪽 환경).  
- 저온 급속충전 plating 라벨 코호트 **문서화 없음**.

### 32. 진단으로 내리는 의사결정
**UNKNOWN (제품 합의 미정)**  
NOTES backlog: QC 스크리닝 / 고장 분류 / RUL — 미체크.  
현행 정책: **모드 후보 + confidence 보고**, hard QC 게이트 아님.

### 33. 결과 소비자
**PARTIAL**  
런타임: **`pne_studio2` Diagnosis 탭 + CLI**.  
역할(연구/공정/경영) **미지정**.

### 34. 프로토콜 추가 시간 예산
**UNKNOWN**  
로드맵 참고치: 충전 펄스 ~1분, C/20은 고비용.

---

## 10.6 시스템 · 운영

### 35. 장비 벤더
**PARTIAL — 현재 데이터·로더는 PNE 중심**  
멀티벤더(Arbin/Maccor…)는 로드맵 견고화 항목, 현행 혼재 증거 없음.

### 36. 파일 크기 · 셀당 파일 수
**PARTIAL**  
- Ch22 raw ~**80 MB**, stepend ~0.5 MB; Ch25 raw ~22 MB.  
- 원본 폴더: `.cts/.cyc/.sch/.ini` + export raw/stepend (+ 분석 CSV).

### 37. `diagnosis_quality_score` 계산식
**CONFIRMED**
```
mode data_quality = n_available_evidence / n_configured_terms
row diagnosis_quality_score = mean(mode data_quality)

confidence = 0.45*data_quality + 0.40*agree + 0.15*min(1, n/5)
(+ mode collision 감점)
```
→ residual / samples_per_mV 등 **실측 품질 지표 아님** (로드맵 3.4 교체 대상).

### 38. `mode_weights_fullcell_v1.json` 근거
**PARTIAL — rule_pattern / heuristic**  
문헌 인용·피팅 로그 없음. 전문가 규칙 가중치로 보는 것이 타당.  
→ 화학 분기·라벨 루프 전 재보정 필요.

### 39. pne_studio2 사람 확인·수정 루프
**CONFIRMED — 없음**  
Diagnosis UI는 extract → 표시 → export만. “displays only”.

### 40. 가장 자주 틀리는 진단
**UNKNOWN (사용자 피드백 로그 없음)**  
문서상 위험: mode collision, 온톨로지 혼재, peak H↔SoHQ 용량 스케일 교란.

---

## 우선 8문 요약 (로드맵 §10.7)

| # | 답 | 함의 |
|---|---|---|
| **8** raw V–I | **있음** | R 3성분 분해 **가능** |
| **1** 첫 1 s 샘플링 | **10 Hz 전 구간** | 설정 변경 없이 분해 개방 |
| **5** SOC 기준 | **직전 capa 상대 %** | 절대 Ah 병기·메타 명시 필요 |
| **20** dQ/dV | Q-interp 500 + SG smooth_then_diff | 피크 폭은 SG에 민감 |
| **23** 화학 | ASSB SJ900 (S83S / ASG903-1300), Si-rich 추정 | LFP 경로 아님; Si hyst 지표 중요 |
| **27** 하프셀 OCV | **없음** | P3 `*_est` 보류 |
| **30/31** 정답·유도열화 | **golden 없음** / 45°C life만 | 합성+공개셋 + 라벨 루프 필수 |
| **32** 목적 | **미합의** (현행=모드 후보 보고) | 우선순위 확정 전 제품 질문 남음 |

---

## 여전히 UNKNOWN → 실험 담당자 확인 필요

- CV cutoff 전류 (#10/#11)  
- ADC 분해능 (#17)  
- 온도 실측 위치·챔버 밴드 (#18/#19)  
- `.sch` 샘플링 설정 원문 (#16)  
- 구속 압력 (#25), 전극 두께 (#26), Si%/NMC비 (#23 정밀)  
- 코호트 규모·replicate (#28/#29)  
- 의사결정 목적·소비자·시간 예산 (#32–34)  
- 자주 틀리는 출력 체감 (#40)
