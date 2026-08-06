# VP Diagnosis — Feature Catalog

Voltage Profile 한 **leg**(charge 또는 discharge) × **cycle** 에서 추출할 feature 목록.  
Phase 1에서 Tier 1·2 구현, Tier 0·3은 후순위.

**기호:** `Q` capacity, `V` voltage, `t` time, `I` current, leg ∈ {chg, dis}

---

## Tier 0 — Raw sequence (Phase 3)

| ID | Feature | Shape | 비고 |
|----|---------|-------|------|
| F0.1 | `V_norm(Q*)` | N=256 | Q를 [0,Q_max] 정규화 후 리샘플 |
| F0.2 | `V_norm(t*)` | N=256 | 시간 정규화 (rate 의존 제거 어려움) |
| F0.3 | `dQdV(V*)` | N=256 | 보간 grid 고정 |
| F0.4 | `I_norm(Q*)` | N=256 | CC/CV 구분용 |

---

## Tier 1 — Scalar / 구간 통계 (Phase 1, **우선**)

### 용량·에너지

| ID | Feature | 단위 | 설명 |
|----|---------|------|------|
| F1.1 | `Q_max` | mAh | leg 최대 용량 |
| F1.2 | `Q_spec` | mAh/g | active_mass 있을 때 |
| F1.3 | `E_dis` | mWh | ∫V dQ 근사 |
| F1.4 | `V_avg` | V | 용량 가중 평균 전압 |
| F1.5 | `CE` | — | charge Q / discharge Q (쌍 있을 때) |

### 형태·기울기

| ID | Feature | 단위 | 설명 |
|----|---------|------|------|
| F1.6 | `V_start` | V | leg 시작 전압 |
| F1.7 | `V_end` | V | leg 종료 전압 |
| F1.8 | `dV_dQ_mean` | V/mAh | CC 구간 평균 기울기 |
| F1.9 | `dV_dQ_std` | V/mAh | 기울기 변동 (불균일성) |
| F1.10 | `plateau_V` | V | dV/dQ ≈ 0 구간 중앙 V (있으면) |
| F1.11 | `plateau_width` | mAh | plateau Q 폭 |

### CC / CV

| ID | Feature | 단위 | 설명 |
|----|---------|------|------|
| F1.12 | `cc_Q_frac` | — | CC에서 충전/방전된 Q 비율 |
| F1.13 | `cv_time` | s | CV 구간 시간 |
| F1.14 | `cv_I_decay` | — | CV 시작·끝 전류 비 (충전) |
| F1.15 | `ir_drop_proxy` | V | leg 초반 dV/dt × I (옴성 근사) |

### Reference 대비 (라벨 없이 유용)

| ID | Feature | 단위 | 설명 |
|----|---------|------|------|
| F1.16 | `delta_Q_pct` | % | vs golden Q_max |
| F1.17 | `delta_V_avg` | V | vs golden V_avg |
| F1.18 | `dtw_V` | — | VP shape distance to golden |
| F1.19 | `mahal_T2` | — | Tier1+2 vector vs reference cov |

---

## Tier 2 — dQ/dV · hysteresis (Phase 1–2)

| ID | Feature | 단위 | 설명 |
|----|---------|------|------|
| F2.1 | `peak1_V`, `peak1_H`, `peak1_W` | V, —, V | 최대 peak |
| F2.2 | `peak2_*`, `peak3_*` | | 2·3번째 peak |
| F2.3 | `n_peaks` | — | 유의 peak 개수 |
| F2.4 | `peak_area_sum` | — | dQ/dV 적분 |
| F2.5 | `hyst_area` | V·mAh | charge vs discharge V(Q) 루프 면적 |
| F2.6 | `hyst_max_dV` | V | 동일 Q에서 chg-dis V 차 최대 |
| F2.7 | `dVdQ_peak_V` | V | dV/dQ peak 위치 (anode 쪽) |

**전처리 (pne_studio와 동일 개념, 독립 구현):**
- CC 구간 trim (CV 제외 옵션)
- dQ/dV: 보간 500pt, SG smoothing (window=21, poly=3) — 파라미터는 feature spec에 고정

---

## Tier 3 — Learned (Phase 3)

| ID | Feature | 설명 |
|----|---------|------|
| F3.1 | `cnn_emb_32` | 1D-CNN encoder 마지막 hidden |
| F3.2 | `ae_recon_err` | Autoencoder reconstruction MSE |
| F3.3 | `siamese_dist` | Golden pair embedding L2 |

---

## Metadata features (모델 입력 보조)

| ID | Feature | 출처 |
|----|---------|------|
| M1 | `cycle` | CSV |
| M2 | `c_rate` or `current_set` | step metadata |
| M3 | `temperature` | 있으면 |
| M4 | `loading`, `area`, `cathode_id` | sidecar / filename |
| M5 | `cell_id`, `lot_id` | 파일명 파싱 또는 manifest |

→ **GroupKFold** 시 `cell_id` 로 누수 방지.

---

## Feature vector 조합 (추천 MVP)

**`vp_v1_basic`** (약 25차원):

```
F1.1–F1.15, F1.16–F1.18, F2.1–F2.3 (peak1–3), M1
```

**`vp_v1_full`**: 위 + F2.4–F2.7, M2–M5

---

## 구현 우선순위

1. F1.1, F1.4, F1.6–F1.8, F1.12–F1.13, F1.16–F1.18
2. F2.1 (peak1 only)
3. F1.5, F2.5–F2.6 (chg+dis 쌍 필요)
4. 나머지

---

## 저장 형식

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `cell_id` | str | |
| `file` | str | 원본 경로 |
| `cycle` | int | |
| `leg` | str | `charge` / `discharge` |
| `feature_set` | str | e.g. `vp_v1_basic` |
| `f_*` | float | 개별 feature |
| `label` | str? | optional |

Parquet 권장 (대량 배치).

---

## LGES cycle indicators — `vp_lges_cycle_v1`

사이클당 **1행** (leg 분리 없음). 구현: `cyclediag/features/lges_catalog.py`, `lges_extract.py`.

### 시험(패턴) 점검

| Feature | 단위 | 설명 |
|---------|------|------|
| `chg_V_cutoff`, `dchg_V_cutoff` | V | 충·방전 종료 전압 |
| `chg_I_cutoff` | A | 충전 종료 전류 |
| `chg_temp_avg`, `dchg_temp_avg` | °C | 충·방전 평균 온도 |

### 전압 (Rest)

| Feature | 단위 | 설명 |
|---------|------|------|
| `EoC_restV_init`, `EoC_restV_60s`, `EoC_restV_30m`, `EoC_restV_end` | V | 충전 후 Rest 전압 |
| `delta_EoC_restV_*` | V | 1사이클 대비 변화 |
| `EoD_restV_*`, `delta_EoD_restV_*` | V | 방전 후 Rest (동일 구조) |

기록 시각 없으면 `nan`. `delta_*`는 baseline cycle(기본 1) 대비.

### 저항

| Feature | 단위 | 설명 |
|---------|------|------|
| `EoC_dchgR_10s/30s/60s` | mΩ | 충전 Rest 후 방전 시작 직후 저항 |
| `EoC_dchgR_*_inc` | % | 1사이클 대비 증가율 |
| `EoD_chgR_10s/30s/60s`, `EoD_chgR_*_inc` | mΩ, % | 방전 Rest 후 충전 시작 직후 |

### 용량

| Feature | 단위 | 설명 |
|---------|------|------|
| `CE`, `CE_rev` | % | 쿨롱 효율 / 역방향 효율 |
| `dchgCapa`, `chgCapa`, `chgCCcapa`, `chgCVcapa` | Ah | 용량 (입력 mAh면 자동 변환) |
| `SoHQ` | % | 용량 유지율 (cycle 1 대비) |
| `chgCapa_CCratio`, `delta_chgCapa_CCratio` | %, %p | CC 용량 비율 |
| `chgCVtime` | s | CV 충전 시간 |

### 미분 (최대 8 peak)

`chg_dQdV_peak(#)_V`, `chg_dQdV_peak(#)`, `dchg_dQdV_peak(#)_V`, `dchg_dQdV_peak(#)`,  
`chg_dVdQ_peak(#)_Q`, `chg_dVdQ_peak(#)`, `dchg_dVdQ_peak(#)_Q`, `dchg_dVdQ_peak(#)`

CLI: `python -m cyclediag extract --feature-set vp_lges_cycle_v1 --input … --out …`

---

## Degradation-mode outputs — `vp_lges_cycle_v2` (목표)

Full-cell 기반 LLI·LAM 진단. 하프셀은 Phase 3 교정용 — 정책: [LLI_LAM_DIAGNOSIS.md](LLI_LAM_DIAGNOSIS.md).

| 출력 | 수준 | 비고 |
|------|------|------|
| `LLI_pattern_score`, `LAM_PE_pattern_score`, `LAM_NE_pattern_score` | Level 1 | 상대 정합도 (우선 구현) |
| `impedance_pattern_score`, `transport_limitation_score`, `plating_risk_score`, `contact_loss_score` | Level 1 | |
| `LLI_est`, `LAM_PE_est`, `LAM_NE_est`, `electrode_slippage_est` | Level 2 | 정의·검증 후에만 (현재 null) |
| `LAM_curve_proxy`, `LLI_curve_proxy`, `R_curve_proxy` | Level 2 proxy | full-cell 3-param fit (§5.6); not `*_est` |
| `eta_SOC*`, `PER`, `dQV_log_var`, `mech_vs_chem_ratio` | observation/state | ASSB enrich (§5.7/5.9/5.10) |
| `*_confidence`, `diagnosis_quality_score`, `diagnosis_valid` | meta | 불확실성 필수 |
| `*_est_hc_calibrated` | Level 3 | Phase 3 |

스펙: [../specs/degradation-mode-diagnosis.md](../specs/degradation-mode-diagnosis.md)
