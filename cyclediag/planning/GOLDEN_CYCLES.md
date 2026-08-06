# Golden Cycles — M01Ch025 (SJ900 set4)

**갱신:** 2026-07-09  
**데이터:** `00207966_260304_set4_SJ900_45도 0.5C cycle_no1_2_4` / M01Ch025[025]  
**raw:** `example/docs/peak_review/_tmp_raw/..._[Ch25]__QN_mono_#4_raw.csv`  
**품질 스코어:** `example/docs/peak_review/sj900_set4_ch025_cycle_quality.csv`  
**도구:** `python cyclediag/tools/score_cycle_dqdv_quality.py --input <raw.csv>`

> **TotalCycle** = raw CSV `TotalCycle` (classification 없음).  
> 유효 사이클 약 **153개** (Ch025 Restore 범위).

---

## Golden 선정 기준

| 항목 | 기준 |
|------|------|
| 노이즈 | `noise_ratio` (MAD/ymax) 낮을수록 좋음 |
| peak 개수 | charge **3** + discharge **3** (자동 assign에 유리) |
| 곡선 | dQ/dV SG smooth 후 고주파 잔차(`hf_std`) 작을수록 좋음 |
| 시각 검수 | 알고리즘 점수와 무관하게 **눈으로 깨끗**하면 golden 후보 |

---

## 사용자 지정 + 알고리즘 검증 (TC 10, 14, 69)

| TC | 사용자 평가 | 알고리즘 순위 | ch/dc peaks | noise | 판정 |
|----|-------------|---------------|-------------|-------|------|
| **10** | golden 후보 | 56 / 153 | 3 / 3 | 0.0054 | **채택** — 시각·개수 양호, 초기 BOL anchor |
| **14** | golden 후보 | 137 / 153 | **4** / 3 | 0.0056 | **조건부** — 충전 4 peak (3.74·3.81 근처 이중 peak). assign 시 merge/window 필요 |
| **69** | golden 후보 | 97 / 153 | **2** / 3 | 0.0060 | **조건부** — 충전 P2 누락. 중기 anchor로는 방전 leg 위주 또는 window 완화 |

---

## 추천 Golden 패널 (2026-07-09)

### Tier 1 — Primary (자동 추적·assign 기본)

| 역할 | TC | 이유 |
|------|-----|------|
| **BOL primary** | **15** | 초기 구간 최저 noise+3/3 (quality rank **20**/153) |
| **BOL backup** | **12** | 10·14 인근, 3/3, noise 0.0056 (rank **25**) |
| **BOL user** | **10** | 사용자 선호, 3/3, noise 낮음 |
| **Early-mid** | **23** | 초기 최상위 (rank **16**), 3/3 |
| **Mid-life** | **58** | 중기 3/3 최상위 (rank **3**), peak V 안정 |
| **Late-life** | **149** | 후반 3/3 (rank **2**) |

### Tier 2 — 보조 / 수동 검수용

| TC | 용도 |
|----|------|
| 11, 13, 20 | BOL 대체 (모두 3/3, 초기 top 15) |
| 55, 65, 83 | 중기 저노이즈 |
| 154 | 후반 최저 noise (rank 1) |
| **14** | 사용자 golden — **수동 window** 또는 3.74/3.81 merge 규칙 |
| **69** | 사용자 golden — **중기 discharge anchor** 또는 charge window −0.03 V |

### 비추천 (자동 golden으로 쓰기 어려움)

- TC **2** (Cycle-001): 초기화 구간, noise 상대적으로 높음 (rank 58)
- peak count ≠ 3/3 인 cycle 다수 (특히 후반 charge 2 peak)

---

## Golden peak 좌표 스냅샷 (assign window 초안)

δV = **±0.04 V** (튜닝 가능)

### TC 15 — BOL primary

| leg | peak | V (V) | H | window |
|-----|------|-------|---|--------|
| charge | P1 | 3.579 | 72.9 | 3.54–3.62 |
| charge | P2 | 3.822 | 98.2 | 3.78–3.86 |
| charge | P3 | 4.012 | 84.0 | 3.97–4.05 |
| discharge | P1 | 3.109 | 61.4 | 3.07–3.15 |
| discharge | P2 | 3.659 | 59.9 | 3.62–3.70 |
| discharge | P3 | 3.912 | 71.9 | 3.87–3.95 |

### TC 10 — BOL user golden

| leg | peak | V (V) | H |
|-----|------|-------|---|
| charge | P1 | 3.586 | 79.3 |
| charge | P2 | 3.807 | 100.0 |
| charge | P3 | 4.036 | 86.1 |
| discharge | P1 | 3.120 | 60.8 |
| discharge | P2 | 3.670 | 60.4 |
| discharge | P3 | 3.921 | 73.7 |

### TC 58 — Mid-life

| leg | peak | V (V) | H |
|-----|------|-------|---|
| charge | P1 | 3.573 | — |
| charge | P2 | 3.791 | — |
| charge | P3 | 4.035 | — |
| discharge | P1 | 3.117 | — |
| discharge | P2 | 3.704 | — |
| discharge | P3 | 3.904 | — |

*(H 값은 `sj900_set4_ch025_cycle_quality.csv` 참조)*

---

## Golden 사용 규칙

1. **Assign (identity):** Tier 1 golden의 V window로 Hungarian match → peak_id 고정  
2. **추적 (magnitude):** assign된 peak_id에 대해 매 cycle `V`, `H` 기록  
3. **세기 정규화:** `H_norm = H / H_golden(TC15, same leg, same peak_id)`  
4. **다구간 golden:** BOL=15, Mid=58, Late=149 — 중간 cycle은 **V 기대값 선형 보간**  
5. **TC 14/69:** Tier 2 — 리뷰 PNG 확인 후 window 수동 조정

---

## 다음 액션

- [ ] TC 10, 14, 15, 58, 69 PNG export (`export_dqdv_peak_review.py --cycle <TC>`)
- [ ] 전 cycle trajectory CSV 생성 (Phase 4 Step 15)
- [ ] TC 14 charge 4-peak merge 규칙 확정
