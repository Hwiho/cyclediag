# Validation · Improvement Plan v1.3 (Si-on-Gr · NCM82 secondary)

**날짜:** 2026-08-06  
**대상:** electrode-side lean · mode scores · enrich 추출 · RPT dual-track  
**화학:** ASSB pouch · **Si coating on graphite** (노출 Gr 가능) · **NCM82 이차입자**  
**프로세스:** 감사 → 1차 계획 → **검토 개정(이 문서)** → 구현 → PDF

---

## 1. 감사 요약 (v1.2 이후 잔여 이슈)

### 유지 (타당)
- hypothesis_bol_ocp · absolute LAM% 금지
- pulse thr 0.75×I · FC-OCP Δhits · contact_stack ≠ NE 자동
- C/3 RPT dual-track (routine fade/lean, RPT 앵커)
- CE out-of-range skip · negative LAM_curve_proxy skip

### Critical (이번에 고침)
| ID | 문제 | 영향 |
|---|---|---|
| C1 | `dchg_fit_residual_argmax_SOC`가 실제로는 **DOD%** | PE/NE residual boost 반전 |
| C2 | `Q_relax`가 RPT 행에만 찍힘 → routine lean에 미전달 | Si co-sign 공허 |
| C3 | 화학 언어가 **Si-rich (stage 없음)** | Si-on-Gr·노출 Gr와 불일치 |
| C4 | baseline R 없을 때 absolute R 점수화 | contact_loss 과대 (V6 잔여) |

### High (이번에 포함)
| ID | 문제 | 조치 |
|---|---|---|
| H1 | Si co-sign 피처가 contact_loss evidence와 중복 | contact는 R-계열 중심; Si는 co-sign 버킷 분리 |
| H2 | FC 피크 hit을 PE로 호칭 · chg+dchg 혼매칭 | charge-leg only · unique nearest · `fc_peak_hits` 명명 |
| H3 | LAM_PE를 AM 손실로 읽기 | **PE activity/isolation pattern** (이차입자 균열/고립 포함) |
| H6 | RPT 앵커를 진단 서사에 미통합 | RPT co-sign 표 + PDF 이중 트랙 그림 |

### Medium → 후속 (명시)
- CE Ah pairing 근본 수정
- Gr stage monitoring feature (노출 지표, LAM% 아님)
- DCIR SOC order 전압 검증
- PER dI from measured currents
- aged HC → Level 3

---

## 2. 1차 계획 → 검토 → 개정

### 1차 초안
모든 Critical+High+Gr-stage feature를 한 사이클에 넣기.

### 검토에서 줄인 것
1. **Gr-stage peak 신규는 이번 사이클 보류** — 피처 설계·게이트가 크고, false NE% 위험. 정책/서사만 Si-on-Gr로 교정하고 monitoring은 P2.
2. **Peak attribution “고도화” 대신 보수화** — unique + charge-only + 이름 정정. NP 보정 synth는 aged/검증 후.
3. **세그먼트 ε 추가 완화보다 dwell↑** — 과분할은 min_segment_cycles=4 + knee 경계 유지.
4. **검증 메트릭을 PDF에 강제** — residual SOC 부호, Q_relax coverage, baseline-R skip rate, role counts.

### 개정 구현 범위 (이번 사이클) = P0+P1

**P0**
1. curve_fit: DOD→SOC 변환 (`SOC = 100 − DOD`) 또는 컬럼 rename + electrode 규칙 정합
2. Q_relax forward-fill to routine between RPT blocks
3. chemistry: `Si_on_Gr` + NCM82_secondary 표기 (registry/weights/PDF)
4. pattern_scoring: `use_baseline`인데 baseline 결측 → **term skip** (absolute 금지)

**P1**
5. mode_weights contact_loss: R_ohmic_growth / baseline ΔR / R_frac 중심; hyst/Q_relax/mech는 가중↓ 또는 제거(Si 버킷으로)
6. electrode_side: peak hits → `fc_ocp_hits` (PE-only claim 완화); charge peaks only; unique assign
7. Si co-sign: hyst_low + mech + Q_relax (fill 후); NE_FEATURE에서 Si 중복 제거
8. LAM_PE narrative/description → PE activity/isolation pattern
9. segment min_dwell=4; validation_metrics 확장
10. PDF v1.3: 화학 정체성 · 검증 섹션 · 드라이버 그래프 · dual-track · 과학 서사

---

## 3. 화학 정책 (개정)

**Anode:** Si coating on graphite — Gr may be exposed.  
**Cathode:** NCM82 secondary particles — cracking/isolation ≠ stoichiometric LAM%.  
**Allowed:** PE activity pattern; contact_stack; Si chemo-mech co-sign; (later) Gr-stage *monitoring*.  
**Forbidden:** LAM_NE% from peaks only; “no graphite stages exist”; contact→confirmed NE without co-sign; absolute `*_est` without aged HC.

**Lean language:**  
> 중기 **접촉/스택 ohmic 패턴** 우위. Si chemo-mech co-sign이 있으면 **Si-on-Gr 음극 기계적/접촉 가설**.  
> 전극 분해 LAM%는 aged 하프셀 전까지 보고하지 않는다.

---

## 4. 성공 기준 (DoD)

- [ ] residual argmax가 true SOC 도메인 (또는 규칙이 DOD에 맞게 수정됨) — 테스트
- [ ] routine 행의 Q_relax non-null 비율 ≫ 0 (RPT 이후 구간)
- [ ] baseline R 결측 시 contact_loss가 absolute R로 포화되지 않음
- [ ] PDF/서사에 Si-on-Gr · NCM82 secondary 명시
- [ ] Ch022/Ch024 재진단 + 상세 PDF (검증·파라미터·그래프)
- [ ] 단위 테스트 통과

---

## 5. 명시적 비범위 (P2)
CE pairing · Gr-stage feature 추출 · DCIR SOC voltage gate · aged HC Level 3 · NP-window OCP synth
