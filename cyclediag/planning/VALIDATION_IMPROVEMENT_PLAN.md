# Electrode-side 진단 검증 · 개선 계획

**날짜:** 2026-08-06  
**대상:** Ch022/Ch024 PE/NE lean · mode pattern scores · enrich 추출  
**상태:** 감사 완료 → 계획 1차 → **검토 후 개정(이 문서)** → 구현

---

## 1. 감사 요약 (무엇이 틀렸는가)

| ID | 문제 | 심각도 | 영향 |
|---|---|---|---|
| V1 | full-cell 피크 V를 **음극/양극 하프셀 V**에 직접 매칭 (V_PE−V_NE 미사용) | **Critical** | pe_peak_boost가 열화와 무관한 상수 bias |
| V2 | enrich `_find_pulse_cycles` thr=**0.5×I** → 0.5C 루틴을 펄스로 오인 | **Critical** | RCF/routine mask·DCIR 블록 오염 |
| V3 | `LAM_PE`가 **≈0.3095(=1.3/4.2)** 천장에 고착 | **Critical** | lean이 사실상 contact_loss 단변수 |
| V4 | `contact_loss→NE`가 정의상 매핑 (원형 추론) | **High** | “중기 음극 지배” 서사가 과신됨 |
| V5 | `eta_argmax_SOC=0`을 low-SOC로 해석 | **High** | 허위 NE boost |
| V6 | `R_ohmic` **절대값** 점수화 (BOL부터 포화) | **High** | contact_loss 과대 |
| V7 | CE>100% 추출 → CE 기반 모드 무효 | **Medium** | LLI/SE_decomp 왜곡 |
| V8 | 세그먼트 ε=0.02로 lean 부호 잡음 | **Medium** | 구간 과분할 |
| V9 | fade/knee가 세그먼트 경로에 미반영 | **Medium** | 수명 단계 분할 약함 |

**유지할 것:** hypothesis_bol_ocp 계약 · absolute `*_est` 금지 · 세그먼트 도구의 0.75×I DCIR 필터 · Δ lean을 *상대 타임라인*으로만 쓰는 철학 · synth FC OCP 아이디어(배선만 필요).

---

## 2. 1차 계획 → 검토 의견 → **개정 계획**

### 1차 계획 (초안)
P0: pulse thr, peak attribution, LAM_PE weights, CE, curve_fit  
P1: contact→NE 완화, R growth, feature boost, fade  
P2: hysteresis, peak area traj

### 검토에서 바뀐 점
1. **Peak attribution을 “고도화”하지 말고 먼저 끄거나 Δhits-only로 축소** — 잘못된 domain 매칭을 유지한 채 boost하면 검증이 더 어려움.  
2. **contact_loss를 NE로 단정하지 말고 `contact_or_stack` 버킷 + Si co-sign** — 서사 언어를 “NE”에서 “접촉/스택 (Si co-sign 시 NE 가설)”로 바꿈.  
3. **검증 산출물을 코드에 내장** — ceiling-lock rate, pulse contamination, lean leave-one-out sensitivity를 CSV/PDF에 명시.  
4. CE 전면 수정은 범위가 큼 → **CE>102 또는 <85면 증거에서 제외**로 가드 후, 추출 버그는 follow-up.

### 개정 구현 범위 (이번 사이클)

#### P0 (반드시)
1. `enrich_assb._find_pulse_cycles`: thr≥0.75×I + optional short-pulse duration gate  
2. `electrode_side` peak attribution: **synth FC OCP peaks**만 사용; boost=`max(0, hits−hits_baseline)`; 매칭 실패 시 boost=0  
3. `mode_weights_assb_si_v1.json` LAM_PE: `delta_chg_V_avg` 제거; peak/plateau는 baseline-relative; `LAM_curve_proxy`는 양수일 때만  
4. `pattern_scoring`: `increase`/`either`에서 baseline이 있으면 Δ 사용 옵션; negative proxy skip; CE out-of-range skip  
5. `curve_fit`: s at bound → `LAM_curve_proxy=NaN` + flag  
6. `_feature_boost`: SOC argmax ∈(5,95)만; 0 무시  
7. electrode lean: `contact_loss` → **contact_stack** 점수; NE lean은 Si co-sign(hyst_low↑, Q_relax↑, mech_vs_chem↑) 있을 때만 NE로 라벨

#### P1 (이번 사이클에 포함)
8. contact_loss evidence: prefer `R_ohmic_growth_100` / baseline Δ; downweight absolute R_ohmic if no baseline  
9. segment: min dwell ≥3 points, lean ε=0.05, hysteresis  
10. `diagnosis/validation_metrics.py`: ceiling lock, pulse flag rate, lean sensitivity  
11. PDF v2: 검증 섹션 + 개정 방법론 + 재진단 결과

#### P2 (명시적 후속)
- CE Ah pairing 버그 근본 수정  
- peak area trajectory for PE aging  
- aged HC → Level 3

---

## 3. 성공 기준 (검증 DoD)

- [ ] Ch022에서 routine cycle이 pulse로 잡히는 비율 ≪ 10% (enrich meta)  
- [ ] LAM_PE nunique 증가 · exact 1.3/4.2 고착 비율 감소  
- [ ] pe_peak_boost가 BOL에서 0에 가깝고, 열화와 함께만 증가(또는 0 유지)  
- [ ] lean 라벨에 `contact_stack` vs `NE_hypothesis` 구분  
- [ ] PDF에 검증 한계·파라미터 정의·그래프 포함  
- [ ] 단위 테스트: pulse thr, attribution domain, LAM ceiling, SOC boost guard  

---

## 4. 해석 언어 (개정)

> “중기 음극 지배” →  
> “중기 **접촉/스택 저항 패턴**이 우세하며, Si co-sign이 있으면 **음극 기계적 접촉 가설**로 읽는다.  
> aged 하프셀·압력 로그 없이 전극 확정은 하지 않는다.”
