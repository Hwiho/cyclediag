# 사이클별 지표 패널 — M02Ch104

## 트렌드 요약 — M02Ch104

- 유효 지표: 358개 · aging 방향 일치 45 · 반대 10

### 하락 트렌드 (상위)
- 충전 dQ/dV 피크1 높이: early=79.77 → late=96.32 (Δ=+16.55, -849.6Ah/V/100cyc) → decreasing · context
- 국소 CE(20): early=531.3 → late=264.9 (Δ=-266.4, -86.27%/100cyc) → decreasing · matches_aging
- CV 시간: early=0 → late=0 (Δ=+0, -57.45s/100cyc) → decreasing · opposite_aging
- 방전후 휴지 완화 τ: early=369.6 → late=292 (Δ=-77.6, -37.24s/100cyc) → decreasing · context
- 방전후 완화 τ Δvs기준: early=10.48 → late=-67.12 (Δ=-77.6, -37.24s/100cyc) → decreasing · context

### 상승 트렌드 (상위)
- 충전 dQ/dV 피크3 높이: early=83.59 → late=83.53 (Δ=-0.05275, +58.68Ah/V/100cyc) → increasing · context
- fit 잔차 max: early=57.75 → late=150.4 (Δ=+92.67, +35.8mV/100cyc) → increasing · matches_aging
- EoC 방전 10s 증가%: early=32.96 → late=82.57 (Δ=+49.61, +20.83%/100cyc) → increasing · matches_aging
- EoC 방전 30s 증가%: early=22.44 → late=61.39 (Δ=+38.94, +16.26%/100cyc) → increasing · matches_aging
- EoC 방전 60s 증가%: early=18.02 → late=51.21 (Δ=+33.19, +13.94%/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- CV 충전용량: early=0 → late=0 (Δ=+0, -0.3821Ah/100cyc) → decreasing · opposite_aging
- CC비 Δ: early=0 → late=0 (Δ=+0, +0.58561/100cyc) → increasing · opposite_aging
- CV 시간: early=0 → late=0 (Δ=+0, -57.45s/100cyc) → decreasing · opposite_aging
- 쿨롱 비효율: early=-5.573 → late=-17.51 (Δ=-11.94, -5.162%/100cyc) → decreasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.

## 지표 카탈로그 + 트렌드

### 프로토콜 · 온도

**충전 전압 컷오프** (`chg_V_cutoff`)
- 의미: 충전 종료 전압.
- 계산: charge V max/cutoff.
- 트렌드: 충전 전압 컷오프: early=4.2 → late=4.2 (Δ=+9.35e-05, +4.943e-05V/100cyc) → flat · context

**방전 전압 컷오프** (`dchg_V_cutoff`)
- 의미: 방전 종료 전압.
- 계산: discharge V min/cutoff.
- 트렌드: 방전 전압 컷오프: early=2.5 → late=2.5 (Δ=+1.3e-06, -8.795e-07V/100cyc) → flat · context

**충전 전류 컷오프** (`chg_I_cutoff`)
- 의미: CV 종료 전류.
- 계산: charge I cutoff.
- 트렌드: 충전 전류 컷오프: early=34.84 → late=34.81 (Δ=-0.037, +2.976A/100cyc) → increasing · context

**충전 평균 온도** (`chg_temp_avg`)
- 의미: 충전 구간 평균 온도.
- 계산: mean Temp on charge.
- 트렌드: 충전 평균 온도: early=0 → late=0 (Δ=+0, +0C/100cyc) → flat · context

**방전 평균 온도** (`dchg_temp_avg`)
- 의미: 방전 구간 평균 온도.
- 계산: mean Temp on discharge.
- 트렌드: 방전 평균 온도: early=0 → late=0 (Δ=+0, +0C/100cyc) → flat · context

**사이클 소요시간** (`cycle_duration_h`)
- 의미: 한 사이클 벽시계 시간.
- 계산: total step time sum.
- 트렌드: 사이클 소요시간: early=5.109 → late=4.916 (Δ=-0.193, -0.0635h/100cyc) → flat · context

### 용량 · 효율 · CV

**용량 유지율** (`SoHQ`)
- 의미: 기준 대비 방전용량.
- 계산: Q_dchg/Q_base*100.
- 트렌드: 용량 유지율: early=97.11 → late=87.69 (Δ=-9.425, -3.446%/100cyc) → flat · stable

**방전 용량** (`dchgCapa`)
- 의미: 사이클 방전용량.
- 계산: max discharge capacity.
- 트렌드: 방전 용량: early=69.58 → late=62.83 (Δ=-6.753, -2.469Ah/100cyc) → flat · stable

**충전 용량** (`chgCapa`)
- 의미: 사이클 충전용량.
- 계산: max charge capacity.
- 트렌드: 충전 용량: early=66.25 → late=53.46 (Δ=-12.78, -4.959Ah/100cyc) → decreasing · matches_aging

**CC 충전용량** (`chgCCcapa`)
- 의미: CC 구간 용량.
- 계산: CC capacity.
- 트렌드: CC 충전용량: early=64.08 → late=53.2 (Δ=-10.88, -4.389Ah/100cyc) → decreasing · matches_aging

**CV 충전용량** (`chgCVcapa`)
- 의미: CV 구간 용량.
- 계산: signal/column CV Ah.
- 트렌드: CV 충전용량: early=0 → late=0 (Δ=+0, -0.3821Ah/100cyc) → decreasing · opposite_aging

**CC 용량비** (`chgCapa_CCratio`)
- 의미: CC/(CC+CV).
- 계산: chgCCcapa/chgCapa.
- 트렌드: CC 용량비: early=100 → late=100 (Δ=+0, +0.58561/100cyc) → flat · stable

**CC비 (정규화)** (`chgCapa_CCratio_norm`)
- 의미: 기준 정규화 CC비.
- 계산: CCratio / baseline.
- 트렌드: CC비 (정규화): early=96.82 → late=96.82 (Δ=+0, -1.0951/100cyc) → flat · stable

**CC비 Δ** (`delta_chgCapa_CCratio`)
- 의미: 기준 대비 CC비 변화.
- 계산: delta abs.
- 트렌드: CC비 Δ: early=0 → late=0 (Δ=+0, +0.58561/100cyc) → increasing · opposite_aging

**CV 시간** (`chgCVtime`)
- 의미: CV 지속시간.
- 계산: CV step duration.
- 트렌드: CV 시간: early=0 → late=0 (Δ=+0, -57.45s/100cyc) → decreasing · opposite_aging

**CV 시정수** (`tau_CV`)
- 의미: CV 전류 감쇠 τ.
- 계산: I(t) exp fit.
- 트렌드: 

**CV Q @Tref** (`Q_CV_at_Tref`)
- 의미: 온도 보정 CV 용량.
- 계산: CV Q at ref T.
- 트렌드: 

**쿨롱 효율** (`CE`)
- 의미: Q_dchg/Q_chg.
- 계산: dchg/chg*100.
- 트렌드: 쿨롱 효율: early=105.6 → late=117.5 (Δ=+11.94, +5.162%/100cyc) → flat · stable

**가역 CE** (`CE_rev`)
- 의미: 가역 쿨롱 효율 proxy.
- 계산: rev CE extract.
- 트렌드: 가역 CE: early=91.87 → late=84.93 (Δ=-6.939, -3.627%/100cyc) → flat · stable

**국소 CE(20)** (`CE_local_20`)
- 의미: 최근 20사이클 국소 CE.
- 계산: rolling CE.
- 트렌드: 국소 CE(20): early=531.3 → late=264.9 (Δ=-266.4, -86.27%/100cyc) → decreasing · matches_aging

**쿨롱 비효율** (`CI`)
- 의미: 100−CE.
- 계산: 100-CE.
- 트렌드: 쿨롱 비효율: early=-5.573 → late=-17.51 (Δ=-11.94, -5.162%/100cyc) → decreasing · opposite_aging

**CI /시간** (`CI_per_hour`)
- 의미: 시간당 쿨롱 손실.
- 계산: CI / cycle_duration_h.
- 트렌드: CI /시간: early=-1.08 → late=-3.564 (Δ=-2.484, -1.062%/h/100cyc) → decreasing · opposite_aging

**전압 효율** (`VE`)
- 의미: 에너지 전압효율.
- 계산: E_dchg/E_chg.
- 트렌드: 전압 효율: early=0.8907 → late=0.8593 (Δ=-0.03135, -0.013621/100cyc) → flat · stable

**에너지 효율** (`EE`)
- 의미: 충방전 에너지비.
- 계산: E_dchg/E_chg.
- 트렌드: 에너지 효율: early=0.9481 → late=1.009 (Δ=+0.06136, +0.029831/100cyc) → flat · stable

**충전 에너지** (`chg_E`)
- 의미: 충전 Wh.
- 계산: ∫VI dt charge.
- 트렌드: 충전 에너지: early=249.9 → late=204.5 (Δ=-45.34, -18.13Wh/100cyc) → decreasing · matches_aging

**방전 에너지** (`dchg_E`)
- 의미: 방전 Wh.
- 계산: ∫VI dt discharge.
- 트렌드: 방전 에너지: early=235.5 → late=206.5 (Δ=-28.98, -10.9Wh/100cyc) → flat · stable

**에너지 손실** (`dE`)
- 의미: 충전−방전 에너지.
- 계산: chg_E-dchg_E.
- 트렌드: 에너지 손실: early=12.96 → late=-1.942 (Δ=-14.9, -7.235Wh/100cyc) → decreasing · opposite_aging

**완화 용량** (`Q_relax`)
- 의미: 휴지 회복 용량.
- 계산: DCIR block ΔQ.
- 트렌드: 완화 용량: early=-0.421 → late=-0.184 (Δ=+0.237, +0.1584Ah/100cyc) → increasing · context

**완화 용량 %** (`Q_relax_pct`)
- 의미: 회복 용량 분율.
- 계산: Q_relax/Q*100.
- 트렌드: 완화 용량 %: early=-0.5876 → late=-0.2802 (Δ=+0.3073, +0.2126%/100cyc) → increasing · matches_aging

**dSoHQ/dN** (`dSoHQ_dN`)
- 의미: 용량 유지율 순간 기울기.
- 계산: diff SoHQ.
- 트렌드: dSoHQ/dN: early=-0.1686 → late=-0.02175 (Δ=+0.1469, +0.1657%/cyc/100cyc) → increasing · opposite_aging

**d2SoHQ** (`d2SoHQ`)
- 의미: SoHQ 2차 미분.
- 계산: diff dSoHQ.
- 트렌드: d2SoHQ: early=-0.0009522 → late=-0.06476 (Δ=-0.06381, -0.0422%/cyc2/100cyc) → decreasing · context

### 휴지 전압 (충전/방전 후)

**충전후 휴지 초기 V** (`EoC_restV_init`)
- 의미: 충전후 rest 시작 전압.
- 계산: rest step 첫 샘플.
- 트렌드: 충전후 휴지 초기 V: early=4.2 → late=4.2 (Δ=+0.0001923, +8.526e-05V/100cyc) → flat · context

**충전후 휴지 60s V** (`EoC_restV_60s`)
- 의미: 충전후 rest 60초 전압.
- 계산: rest ≈ 60 s 보간.
- 트렌드: 충전후 휴지 60s V: early=4.189 → late=4.183 (Δ=-0.005219, -0.001986V/100cyc) → flat · context

**충전후 휴지 30분 V** (`EoC_restV_30m`)
- 의미: 충전후 rest 30분 전압 (OCV에 가까움).
- 계산: rest ≈ 1800 s 보간.
- 트렌드: 충전후 휴지 30분 V: early=4.175 → late=4.165 (Δ=-0.01015, -0.004059V/100cyc) → flat · context

**충전후 휴지 종료 V** (`EoC_restV_end`)
- 의미: 충전후 rest 마지막 전압.
- 계산: rest step 끝 샘플.
- 트렌드: 충전후 휴지 종료 V: early=4.175 → late=4.165 (Δ=-0.01015, -0.004059V/100cyc) → flat · context

**충전후 휴지 완화량** (`EoC_restV_relax`)
- 의미: 충전후 end−init 완화.
- 계산: EoC_restV_end − EoC_restV_init.
- 트렌드: 충전후 휴지 완화량: early=-0.02466 → late=-0.03511 (Δ=-0.01044, -0.004144V/100cyc) → decreasing · context

**충전후 60s 완화량** (`EoC_restV_relax_60s`)
- 의미: 충전후 60s−init.
- 계산: EoC_restV_60s − EoC_restV_init.
- 트렌드: 충전후 60s 완화량: early=-0.01123 → late=-0.01674 (Δ=-0.005506, -0.002071V/100cyc) → decreasing · context

**충전후 휴지 완화 τ** (`EoC_restV_tau`)
- 의미: 충전후 rest 완화 시정수 proxy.
- 계산: rest V(t) 완화 fit τ.
- 트렌드: 충전후 휴지 완화 τ: early=515.6 → late=530.6 (Δ=+15.03, +9.475s/100cyc) → flat · context

**충전후 60s V Δvs기준** (`delta_EoC_restV_60s`)
- 의미: 기준 사이클 대비 EoC_restV_60s 이동.
- 계산: EoC_restV_60s(cycle) − baseline.
- 트렌드: 충전후 60s V Δvs기준: early=-0.0005717 → late=-0.005791 (Δ=-0.005219, -0.001986V/100cyc) → decreasing · context

**충전후 30분 V Δvs기준** (`delta_EoC_restV_30m`)
- 의미: 기준 사이클 대비 EoC_restV_30m 이동.
- 계산: EoC_restV_30m(cycle) − baseline.
- 트렌드: 충전후 30분 V Δvs기준: early=-0.000939 → late=-0.01109 (Δ=-0.01015, -0.004059V/100cyc) → decreasing · context

**충전후 종료 V Δvs기준** (`delta_EoC_restV_end`)
- 의미: 기준 사이클 대비 EoC_restV_end 이동.
- 계산: EoC_restV_end(cycle) − baseline.
- 트렌드: 충전후 종료 V Δvs기준: early=-0.000939 → late=-0.01109 (Δ=-0.01015, -0.004059V/100cyc) → decreasing · context

**충전후 완화 τ Δvs기준** (`delta_EoC_restV_tau`)
- 의미: 기준 사이클 대비 EoC_restV_tau 이동.
- 계산: EoC_restV_tau(cycle) − baseline.
- 트렌드: 충전후 완화 τ Δvs기준: early=-18.11 → late=-3.079 (Δ=+15.03, +9.475s/100cyc) → increasing · context

**방전후 휴지 초기 V** (`EoD_restV_init`)
- 의미: 방전후 rest 시작 전압.
- 계산: rest step 첫 샘플.
- 트렌드: 방전후 휴지 초기 V: early=2.5 → late=2.5 (Δ=+1.3e-06, -8.795e-07V/100cyc) → flat · context

**방전후 휴지 60s V** (`EoD_restV_60s`)
- 의미: 방전후 rest 60초 전압.
- 계산: rest ≈ 60 s 보간.
- 트렌드: 방전후 휴지 60s V: early=2.907 → late=2.98 (Δ=+0.07306, +0.0338V/100cyc) → flat · context

**방전후 휴지 30분 V** (`EoD_restV_30m`)
- 의미: 방전후 rest 30분 전압 (OCV에 가까움).
- 계산: rest ≈ 1800 s 보간.
- 트렌드: 방전후 휴지 30분 V: early=3.035 → late=3.099 (Δ=+0.06435, +0.02702V/100cyc) → flat · context

**방전후 휴지 종료 V** (`EoD_restV_end`)
- 의미: 방전후 rest 마지막 전압.
- 계산: rest step 끝 샘플.
- 트렌드: 방전후 휴지 종료 V: early=3.035 → late=3.099 (Δ=+0.06435, +0.02702V/100cyc) → flat · context

**방전후 휴지 완화량** (`EoD_restV_relax`)
- 의미: 방전후 end−init 완화.
- 계산: EoD_restV_end − EoD_restV_init.
- 트렌드: 방전후 휴지 완화량: early=0.5348 → late=0.5991 (Δ=+0.06435, +0.02702V/100cyc) → flat · context

**방전후 60s 완화량** (`EoD_restV_relax_60s`)
- 의미: 방전후 60s−init.
- 계산: EoD_restV_60s − EoD_restV_init.
- 트렌드: 방전후 60s 완화량: early=0.4073 → late=0.4803 (Δ=+0.07304, +0.0338V/100cyc) → increasing · context

**방전후 휴지 완화 τ** (`EoD_restV_tau`)
- 의미: 방전후 rest 완화 시정수 proxy.
- 계산: rest V(t) 완화 fit τ.
- 트렌드: 방전후 휴지 완화 τ: early=369.6 → late=292 (Δ=-77.6, -37.24s/100cyc) → decreasing · context

**방전후 60s V Δvs기준** (`delta_EoD_restV_60s`)
- 의미: 기준 사이클 대비 EoD_restV_60s 이동.
- 계산: EoD_restV_60s(cycle) − baseline.
- 트렌드: 방전후 60s V Δvs기준: early=0.0577 → late=0.1308 (Δ=+0.07306, +0.0338V/100cyc) → increasing · context

**방전후 30분 V Δvs기준** (`delta_EoD_restV_30m`)
- 의미: 기준 사이클 대비 EoD_restV_30m 이동.
- 계산: EoD_restV_30m(cycle) − baseline.
- 트렌드: 방전후 30분 V Δvs기준: early=0.04123 → late=0.1056 (Δ=+0.06435, +0.02702V/100cyc) → increasing · context

**방전후 종료 V Δvs기준** (`delta_EoD_restV_end`)
- 의미: 기준 사이클 대비 EoD_restV_end 이동.
- 계산: EoD_restV_end(cycle) − baseline.
- 트렌드: 방전후 종료 V Δvs기준: early=0.04123 → late=0.1056 (Δ=+0.06435, +0.02702V/100cyc) → increasing · context

**방전후 완화 τ Δvs기준** (`delta_EoD_restV_tau`)
- 의미: 기준 사이클 대비 EoD_restV_tau 이동.
- 계산: EoD_restV_tau(cycle) − baseline.
- 트렌드: 방전후 완화 τ Δvs기준: early=10.48 → late=-67.12 (Δ=-77.6, -37.24s/100cyc) → decreasing · context

### 시작 저항 (EoC/EoD)

**EoC 방전 10s DCIR** (`EoC_dchgR_10s`)
- 의미: EoC 방전 시작 후 10s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(10s)|/|I|*1000.
- 트렌드: EoC 방전 10s DCIR: early=0.1714 → late=0.2353 (Δ=+0.06394, +0.02685mΩ/100cyc) → increasing · matches_aging

**EoC 방전 10s 증가%** (`EoC_dchgR_10s_inc`)
- 의미: 기준 대비 EoC_dchgR_10s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 10s 증가%: early=32.96 → late=82.57 (Δ=+49.61, +20.83%/100cyc) → increasing · matches_aging

**EoC 방전 30s DCIR** (`EoC_dchgR_30s`)
- 의미: EoC 방전 시작 후 30s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(30s)|/|I|*1000.
- 트렌드: EoC 방전 30s DCIR: early=0.4605 → late=0.607 (Δ=+0.1465, +0.06116mΩ/100cyc) → increasing · matches_aging

**EoC 방전 30s 증가%** (`EoC_dchgR_30s_inc`)
- 의미: 기준 대비 EoC_dchgR_30s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 30s 증가%: early=22.44 → late=61.39 (Δ=+38.94, +16.26%/100cyc) → increasing · matches_aging

**EoC 방전 60s DCIR** (`EoC_dchgR_60s`)
- 의미: EoC 방전 시작 후 60s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(60s)|/|I|*1000.
- 트렌드: EoC 방전 60s DCIR: early=0.8075 → late=1.035 (Δ=+0.2271, +0.09536mΩ/100cyc) → increasing · matches_aging

**EoC 방전 60s 증가%** (`EoC_dchgR_60s_inc`)
- 의미: 기준 대비 EoC_dchgR_60s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 60s 증가%: early=18.02 → late=51.21 (Δ=+33.19, +13.94%/100cyc) → increasing · matches_aging

**EoD 충전 10s DCIR** (`EoD_chgR_10s`)
- 의미: EoD 충전 시작 후 10s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(10s)|/|I|*1000.
- 트렌드: EoD 충전 10s DCIR: early=0.2743 → late=0.3472 (Δ=+0.07291, +0.02702mΩ/100cyc) → increasing · matches_aging

**EoD 충전 10s 증가%** (`EoD_chgR_10s_inc`)
- 의미: 기준 대비 EoD_chgR_10s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 10s 증가%: early=-2.087 → late=23.94 (Δ=+26.02, +9.645%/100cyc) → increasing · matches_aging

**EoD 충전 30s DCIR** (`EoD_chgR_30s`)
- 의미: EoD 충전 시작 후 30s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(30s)|/|I|*1000.
- 트렌드: EoD 충전 30s DCIR: early=0.7437 → late=0.8696 (Δ=+0.1259, +0.04083mΩ/100cyc) → flat · stable

**EoD 충전 30s 증가%** (`EoD_chgR_30s_inc`)
- 의미: 기준 대비 EoD_chgR_30s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 30s 증가%: early=-3.274 → late=13.1 (Δ=+16.38, +5.31%/100cyc) → increasing · matches_aging

**EoD 충전 60s DCIR** (`EoD_chgR_60s`)
- 의미: EoD 충전 시작 후 60s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(60s)|/|I|*1000.
- 트렌드: EoD 충전 60s DCIR: early=1.324 → late=1.401 (Δ=+0.07751, +0.009482mΩ/100cyc) → flat · stable

**EoD 충전 60s 증가%** (`EoD_chgR_60s_inc`)
- 의미: 기준 대비 EoD_chgR_60s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 60s 증가%: early=-6.438 → late=-0.9583 (Δ=+5.479, +0.6703%/100cyc) → increasing · matches_aging

**EoC R10/R60** (`EoC_dchgR_10_60_ratio`)
- 의미: 10s/60s 비. 초기 응답 비중.
- 계산: EoC_dchgR_10s / EoC_dchgR_60s.
- 트렌드: EoC R10/R60: early=0.2105 → late=0.2268 (Δ=+0.01638, +0.0067411/100cyc) → flat · context

**EoD R10/R60** (`EoD_chgR_10_60_ratio`)
- 의미: 10s/60s 비.
- 계산: EoD_chgR_10s / EoD_chgR_60s.
- 트렌드: EoD R10/R60: early=0.2073 → late=0.2487 (Δ=+0.04143, +0.017511/100cyc) → increasing · context

**EoC R10s @25C** (`EoC_dchgR_10s_T25`)
- 의미: 온도 보정 10s DCIR.
- 계산: Arrhenius-ish correct_r_to_25c.
- 트렌드: EoC R10s @25C: early=0.08189 → late=0.1124 (Δ=+0.03055, +0.01283mΩ/100cyc) → increasing · matches_aging

**EoD R10s @25C** (`EoD_chgR_10s_T25`)
- 의미: 온도 보정 10s DCIR.
- 계산: correct_r_to_25c.
- 트렌드: EoD R10s @25C: early=0.1311 → late=0.1659 (Δ=+0.03484, +0.01291mΩ/100cyc) → increasing · matches_aging

**EoC R10s 성장/50cyc** (`EoC_dchgR_10s_growth_50`)
- 의미: 롤링 기울기 (50사이클).
- 계산: rolling slope of EoC_dchgR_10s.
- 트렌드: 

### DCIR 분해 · 성장

**RΩ (SOC80)** (`R_ohmic_soc80`)
- 의미: √t 외삽 t→0 절편 (초기 비옴 포함 proxy).
- 계산: DCIR early √t intercept.
- 트렌드: 

**Rct (SOC80)** (`R_ct_soc80`)
- 의미: 중간 잔차 지수항. Cdl 미분리.
- 계산: resid exp-sat fit.
- 트렌드: 

**τ_ct (SOC80)** (`tau_ct_soc80`)
- 의미: Rct 시정수 (fit seed 2s).
- 계산: curve_fit τ.
- 트렌드: 

**A_diff (SOC80)** (`A_diff_soc80`)
- 의미: 후반 √t 확산 계수.
- 계산: t∈[10,30] R vs √t slope.
- 트렌드: 

**R30s 총 (SOC80)** (`R_30s_total_soc80`)
- 의미: 펄스 30초 총 DCIR.
- 계산: R(t≈30s).
- 트렌드: 

**RΩ분율 (SOC80)** (`R_ohmic_frac_soc80`)
- 의미: RΩ / R30s.
- 계산: R_ohmic / R_30s_total.
- 트렌드: 

**Rct분율 (SOC80)** (`R_ct_frac_soc80`)
- 의미: Rct / R30s.
- 계산: R_ct / R_30s_total.
- 트렌드: 

**Rdiff분율 (SOC80)** (`R_diff_frac_soc80`)
- 의미: A√30 / R30s.
- 계산: A_diff*sqrt(30)/R30s.
- 트렌드: 

**회복 τ1 (SOC80)** (`R_recovery_tau1_soc80`)
- 의미: 펄스 후 빠른 회복 시정수.
- 계산: two-exp recovery fit.
- 트렌드: 

**회복 τ2 (SOC80)** (`R_recovery_tau2_soc80`)
- 의미: 펄스 후 느린 회복 시정수.
- 계산: two-exp recovery fit.
- 트렌드: 

**V∞ est (SOC80)** (`V_inf_est_soc80`)
- 의미: 회복 fit 무한시간 전압.
- 계산: recovery V_inf.
- 트렌드: 

**V∞ rest (SOC80)** (`V_inf_rest_soc80`)
- 의미: rest 기반 V_inf.
- 계산: rest asymptote.
- 트렌드: 

**자기방전 (SOC80)** (`self_discharge_rate_soc80`)
- 의미: 휴지 중 전압 강하율.
- 계산: dV/dt on long rest.
- 트렌드: 

**DCIR fit R2 (SOC80)** (`dcir_fit_r2_soc80`)
- 의미: R(t) 3성분 fit 품질.
- 계산: r2.
- 트렌드: 

**DCIR fit RMSE (SOC80)** (`dcir_fit_rmse_soc80`)
- 의미: 상대 RMSE.
- 계산: rmse/meanR.
- 트렌드: 

**펄스 전류 (SOC80)** (`pulse_current_A_soc80`)
- 의미: DCIR 펄스 |I| 중앙값.
- 계산: median |I| on pulse.
- 트렌드: 

**t≤1s 샘플수 (SOC80)** (`n_t_le_1s_soc80`)
- 의미: early 샘플 수 (RΩ 외삽 품질).
- 계산: count t<=1.
- 트렌드: 

**회복 amp비 (SOC80)** (`relax_amp_ratio_soc80`)
- 의미: 느린/전체 회복 진폭비.
- 계산: |b2|/(|b1|+|b2|).
- 트렌드: 

**완화 완성도 (SOC80)** (`relax_completeness_soc80`)
- 의미: rest 완화 충분성.
- 계산: relax completeness.
- 트렌드: 

**회복 fit R2 (SOC80)** (`recovery_fit_r2_soc80`)
- 의미: two-exp 회복 fit 품질.
- 계산: r2.
- 트렌드: 

**DCIR fit 유효 (SOC80)** (`dcir_fit_valid_soc80`)
- 의미: rmse/r2/cond 게이트 통과.
- 계산: dcir_fit_valid.
- 트렌드: 

**DCIR fit 조건수 (SOC80)** (`dcir_fit_cond_soc80`)
- 의미: 공분산 조건수 (축퇴 지표).
- 계산: cond(pcov).
- 트렌드: 

**자기방전 fit 유효 (SOC80)** (`sd_fit_valid_soc80`)
- 의미: self-discharge fit 게이트.
- 계산: sd_fit_valid.
- 트렌드: 

**펄스 포인트수 (SOC80)** (`n_points_soc80`)
- 의미: DCIR 펄스 샘플 수.
- 계산: n_points.
- 트렌드: 

**RΩ (SOC50)** (`R_ohmic_soc50`)
- 의미: √t 외삽 t→0 절편 (초기 비옴 포함 proxy).
- 계산: DCIR early √t intercept.
- 트렌드: RΩ (SOC50): early=1.394 → late=2.374 (Δ=+0.9802, +0.4981mΩ/100cyc) → increasing · matches_aging

**Rct (SOC50)** (`R_ct_soc50`)
- 의미: 중간 잔차 지수항. Cdl 미분리.
- 계산: resid exp-sat fit.
- 트렌드: Rct (SOC50): early=0.7244 → late=0.9425 (Δ=+0.2181, +0.09305mΩ/100cyc) → increasing · matches_aging

**τ_ct (SOC50)** (`tau_ct_soc50`)
- 의미: Rct 시정수 (fit seed 2s).
- 계산: curve_fit τ.
- 트렌드: 

**A_diff (SOC50)** (`A_diff_soc50`)
- 의미: 후반 √t 확산 계수.
- 계산: t∈[10,30] R vs √t slope.
- 트렌드: 

**R30s 총 (SOC50)** (`R_30s_total_soc50`)
- 의미: 펄스 30초 총 DCIR.
- 계산: R(t≈30s).
- 트렌드: 

**RΩ분율 (SOC50)** (`R_ohmic_frac_soc50`)
- 의미: RΩ / R30s.
- 계산: R_ohmic / R_30s_total.
- 트렌드: 

**Rct분율 (SOC50)** (`R_ct_frac_soc50`)
- 의미: Rct / R30s.
- 계산: R_ct / R_30s_total.
- 트렌드: 

**Rdiff분율 (SOC50)** (`R_diff_frac_soc50`)
- 의미: A√30 / R30s.
- 계산: A_diff*sqrt(30)/R30s.
- 트렌드: 

**회복 τ1 (SOC50)** (`R_recovery_tau1_soc50`)
- 의미: 펄스 후 빠른 회복 시정수.
- 계산: two-exp recovery fit.
- 트렌드: 

**회복 τ2 (SOC50)** (`R_recovery_tau2_soc50`)
- 의미: 펄스 후 느린 회복 시정수.
- 계산: two-exp recovery fit.
- 트렌드: 

**V∞ est (SOC50)** (`V_inf_est_soc50`)
- 의미: 회복 fit 무한시간 전압.
- 계산: recovery V_inf.
- 트렌드: 

**V∞ rest (SOC50)** (`V_inf_rest_soc50`)
- 의미: rest 기반 V_inf.
- 계산: rest asymptote.
- 트렌드: 

**자기방전 (SOC50)** (`self_discharge_rate_soc50`)
- 의미: 휴지 중 전압 강하율.
- 계산: dV/dt on long rest.
- 트렌드: 

**DCIR fit R2 (SOC50)** (`dcir_fit_r2_soc50`)
- 의미: R(t) 3성분 fit 품질.
- 계산: r2.
- 트렌드: 

**DCIR fit RMSE (SOC50)** (`dcir_fit_rmse_soc50`)
- 의미: 상대 RMSE.
- 계산: rmse/meanR.
- 트렌드: 

**펄스 전류 (SOC50)** (`pulse_current_A_soc50`)
- 의미: DCIR 펄스 |I| 중앙값.
- 계산: median |I| on pulse.
- 트렌드: 

**t≤1s 샘플수 (SOC50)** (`n_t_le_1s_soc50`)
- 의미: early 샘플 수 (RΩ 외삽 품질).
- 계산: count t<=1.
- 트렌드: 

**회복 amp비 (SOC50)** (`relax_amp_ratio_soc50`)
- 의미: 느린/전체 회복 진폭비.
- 계산: |b2|/(|b1|+|b2|).
- 트렌드: 

**완화 완성도 (SOC50)** (`relax_completeness_soc50`)
- 의미: rest 완화 충분성.
- 계산: relax completeness.
- 트렌드: 

**회복 fit R2 (SOC50)** (`recovery_fit_r2_soc50`)
- 의미: two-exp 회복 fit 품질.
- 계산: r2.
- 트렌드: 

**DCIR fit 유효 (SOC50)** (`dcir_fit_valid_soc50`)
- 의미: rmse/r2/cond 게이트 통과.
- 계산: dcir_fit_valid.
- 트렌드: 

**DCIR fit 조건수 (SOC50)** (`dcir_fit_cond_soc50`)
- 의미: 공분산 조건수 (축퇴 지표).
- 계산: cond(pcov).
- 트렌드: 

**자기방전 fit 유효 (SOC50)** (`sd_fit_valid_soc50`)
- 의미: self-discharge fit 게이트.
- 계산: sd_fit_valid.
- 트렌드: 

**펄스 포인트수 (SOC50)** (`n_points_soc50`)
- 의미: DCIR 펄스 샘플 수.
- 계산: n_points.
- 트렌드: 

**RΩ (SOC20)** (`R_ohmic_soc20`)
- 의미: √t 외삽 t→0 절편 (초기 비옴 포함 proxy).
- 계산: DCIR early √t intercept.
- 트렌드: 

**Rct (SOC20)** (`R_ct_soc20`)
- 의미: 중간 잔차 지수항. Cdl 미분리.
- 계산: resid exp-sat fit.
- 트렌드: 

**τ_ct (SOC20)** (`tau_ct_soc20`)
- 의미: Rct 시정수 (fit seed 2s).
- 계산: curve_fit τ.
- 트렌드: 

**A_diff (SOC20)** (`A_diff_soc20`)
- 의미: 후반 √t 확산 계수.
- 계산: t∈[10,30] R vs √t slope.
- 트렌드: 

**R30s 총 (SOC20)** (`R_30s_total_soc20`)
- 의미: 펄스 30초 총 DCIR.
- 계산: R(t≈30s).
- 트렌드: 

**RΩ분율 (SOC20)** (`R_ohmic_frac_soc20`)
- 의미: RΩ / R30s.
- 계산: R_ohmic / R_30s_total.
- 트렌드: 

**Rct분율 (SOC20)** (`R_ct_frac_soc20`)
- 의미: Rct / R30s.
- 계산: R_ct / R_30s_total.
- 트렌드: 

**Rdiff분율 (SOC20)** (`R_diff_frac_soc20`)
- 의미: A√30 / R30s.
- 계산: A_diff*sqrt(30)/R30s.
- 트렌드: 

**회복 τ1 (SOC20)** (`R_recovery_tau1_soc20`)
- 의미: 펄스 후 빠른 회복 시정수.
- 계산: two-exp recovery fit.
- 트렌드: 

**회복 τ2 (SOC20)** (`R_recovery_tau2_soc20`)
- 의미: 펄스 후 느린 회복 시정수.
- 계산: two-exp recovery fit.
- 트렌드: 

**V∞ est (SOC20)** (`V_inf_est_soc20`)
- 의미: 회복 fit 무한시간 전압.
- 계산: recovery V_inf.
- 트렌드: 

**V∞ rest (SOC20)** (`V_inf_rest_soc20`)
- 의미: rest 기반 V_inf.
- 계산: rest asymptote.
- 트렌드: 

**자기방전 (SOC20)** (`self_discharge_rate_soc20`)
- 의미: 휴지 중 전압 강하율.
- 계산: dV/dt on long rest.
- 트렌드: 

**DCIR fit R2 (SOC20)** (`dcir_fit_r2_soc20`)
- 의미: R(t) 3성분 fit 품질.
- 계산: r2.
- 트렌드: 

**DCIR fit RMSE (SOC20)** (`dcir_fit_rmse_soc20`)
- 의미: 상대 RMSE.
- 계산: rmse/meanR.
- 트렌드: 

**펄스 전류 (SOC20)** (`pulse_current_A_soc20`)
- 의미: DCIR 펄스 |I| 중앙값.
- 계산: median |I| on pulse.
- 트렌드: 

**t≤1s 샘플수 (SOC20)** (`n_t_le_1s_soc20`)
- 의미: early 샘플 수 (RΩ 외삽 품질).
- 계산: count t<=1.
- 트렌드: 

**회복 amp비 (SOC20)** (`relax_amp_ratio_soc20`)
- 의미: 느린/전체 회복 진폭비.
- 계산: |b2|/(|b1|+|b2|).
- 트렌드: 

**완화 완성도 (SOC20)** (`relax_completeness_soc20`)
- 의미: rest 완화 충분성.
- 계산: relax completeness.
- 트렌드: 

**회복 fit R2 (SOC20)** (`recovery_fit_r2_soc20`)
- 의미: two-exp 회복 fit 품질.
- 계산: r2.
- 트렌드: 

**DCIR fit 유효 (SOC20)** (`dcir_fit_valid_soc20`)
- 의미: rmse/r2/cond 게이트 통과.
- 계산: dcir_fit_valid.
- 트렌드: 

**DCIR fit 조건수 (SOC20)** (`dcir_fit_cond_soc20`)
- 의미: 공분산 조건수 (축퇴 지표).
- 계산: cond(pcov).
- 트렌드: 

**자기방전 fit 유효 (SOC20)** (`sd_fit_valid_soc20`)
- 의미: self-discharge fit 게이트.
- 계산: sd_fit_valid.
- 트렌드: 

**펄스 포인트수 (SOC20)** (`n_points_soc20`)
- 의미: DCIR 펄스 샘플 수.
- 계산: n_points.
- 트렌드: 

**기계/화학 비** (`mech_vs_chem_ratio`)
- 의미: RΩ/Rct 상대 비중.
- 계산: R_ohmic_soc50 / R_ct_soc50.
- 트렌드: 기계/화학 비: early=1.924 → late=2.519 (Δ=+0.5948, +0.35921/100cyc) → increasing · matches_aging

**RΩ 성장/100cyc** (`R_ohmic_growth_100`)
- 의미: 기준 대비 RΩ 성장률 (레벨과 별개).
- 계산: (R-R0)/((N-N0)/100).
- 트렌드: RΩ 성장/100cyc: early=0.7957 → late=0.4668 (Δ=-0.3289, -0.3314mΩ/100cyc/100cyc) → decreasing · context

**Rct 성장/100cyc** (`R_ct_growth_100`)
- 의미: 기준 대비 Rct 성장률.
- 계산: (Rct-Rct0)/((N-N0)/100).
- 트렌드: Rct 성장/100cyc: early=0.0807 → late=0.1039 (Δ=+0.02316, +0.02333mΩ/100cyc/100cyc) → increasing · context

**R30s 20/50** (`R_ratio_20_50`)
- 의미: SOC20 vs 50 총저항 비.
- 계산: R30s_20 / R30s_50.
- 트렌드: 

**R30s 80/50** (`R_ratio_80_50`)
- 의미: SOC80 vs 50 총저항 비.
- 계산: R30s_80 / R30s_50.
- 트렌드: 

**R–SOC 기울기** (`R_SOC_slope`)
- 의미: SOC20/50/80 R30s 선형 기울기.
- 계산: linreg R vs SOC.
- 트렌드: 

**R–SOC 곡률** (`R_SOC_curvature`)
- 의미: 3점 이차 계수.
- 계산: polyfit deg2.
- 트렌드: 

**RΩ SOC50 (ff)** (`R_ohmic_soc50_ff`)
- 의미: DCIR 블록 forward-fill 값.
- 계산: block stamp + ffill.
- 트렌드: RΩ SOC50 (ff): early=1.394 → late=2.374 (Δ=+0.9802, +0.4981mΩ/100cyc) → increasing · matches_aging

**Rct SOC50 (ff)** (`R_ct_soc50_ff`)
- 의미: DCIR 블록 forward-fill 값.
- 계산: block stamp + ffill.
- 트렌드: Rct SOC50 (ff): early=0.7244 → late=0.9425 (Δ=+0.2181, +0.09305mΩ/100cyc) → increasing · matches_aging

### 곡선 형상 · 히스테리시스

**충전 평균 V** (`chg_V_avg`)
- 의미: 충전 평균 전압.
- 계산: mean V charge.
- 트렌드: 충전 평균 V: early=3.808 → late=3.844 (Δ=+0.03626, +0.01304V/100cyc) → flat · context

**방전 평균 V** (`dchg_V_avg`)
- 의미: 방전 평균 전압.
- 계산: mean V discharge.
- 트렌드: 방전 평균 V: early=3.394 → late=3.299 (Δ=-0.09497, -0.04041V/100cyc) → flat · context

**충전 평균V Δ** (`delta_chg_V_avg`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 충전 평균V Δ: early=0.0501 → late=0.08637 (Δ=+0.03626, +0.01304V/100cyc) → increasing · context

**방전 평균V Δ** (`delta_dchg_V_avg`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 방전 평균V Δ: early=-0.03753 → late=-0.1325 (Δ=-0.09497, -0.04041V/100cyc) → decreasing · context

**충전 IR drop proxy** (`chg_ir_drop_proxy`)
- 의미: 충전 초반 IR 강하 proxy.
- 계산: early ΔV.
- 트렌드: 충전 IR drop proxy: early=0.04013 → late=0.04014 (Δ=+1.09e-05, +1.894e-05V/100cyc) → flat · stable

**방전 IR drop proxy** (`dchg_ir_drop_proxy`)
- 의미: 방전 초반 IR 강하 proxy.
- 계산: early ΔV.
- 트렌드: 방전 IR drop proxy: early=0.04006 → late=0.04011 (Δ=+4.5e-05, +9.457e-05V/100cyc) → flat · stable

**히스테리시스 면적** (`hyst_area`)
- 의미: 전체 충방전 히스테리시스.
- 계산: ∮(Vchg-Vdchg)dQ.
- 트렌드: 히스테리시스 면적: early=0.564 → late=0.6143 (Δ=+0.05033, +0.02057V/100cyc) → flat · stable

**저SOC 히스테리시스** (`hyst_area_low`)
- 의미: 저SOC 밴드. Si chemo-mech.
- 계산: band integral.
- 트렌드: 저SOC 히스테리시스: early=0.07466 → late=0.04496 (Δ=-0.0297, -0.01201V/100cyc) → decreasing · opposite_aging

**중SOC 히스테리시스** (`hyst_area_mid`)
- 의미: 중SOC 밴드.
- 계산: band integral.
- 트렌드: 중SOC 히스테리시스: early=0.2719 → late=0.3264 (Δ=+0.05451, +0.02406V/100cyc) → increasing · context

**고SOC 히스테리시스** (`hyst_area_high`)
- 의미: 고SOC 밴드. PE 보조.
- 계산: band integral.
- 트렌드: 고SOC 히스테리시스: early=0.2198 → late=0.2408 (Δ=+0.02105, +0.008549V/100cyc) → flat · stable

**히스테리시스 저SOC분율** (`hyst_frac_low`)
- 의미: low/total.
- 계산: hyst_low/hyst.
- 트렌드: 히스테리시스 저SOC분율: early=0.1296 → late=0.07315 (Δ=-0.05645, -0.023871/100cyc) → decreasing · context

**히스테리시스 고SOC분율** (`hyst_frac_high`)
- 의미: high/total.
- 계산: hyst_high/hyst.
- 트렌드: 히스테리시스 고SOC분율: early=0.3897 → late=0.392 (Δ=+0.002313, +0.00085821/100cyc) → flat · context

**최대 히스테리시스 dV** (`hyst_max_dV`)
- 의미: 최대 충방전 전압차.
- 계산: max|Vchg-Vdchg|.
- 트렌드: 최대 히스테리시스 dV: early=1.557 → late=1.621 (Δ=+0.06402, +0.02847V/100cyc) → flat · stable

**max dV 저SOC** (`hyst_max_dV_low`)
- 의미: 저SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 저SOC: early=0.6462 → late=0.4859 (Δ=-0.1603, -0.06406V/100cyc) → decreasing · opposite_aging

**max dV 중SOC** (`hyst_max_dV_mid`)
- 의미: 중SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 중SOC: early=0.9965 → late=1.12 (Δ=+0.1239, +0.05083V/100cyc) → flat · context

**max dV 고SOC** (`hyst_max_dV_high`)
- 의미: 고SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 고SOC: early=1.557 → late=1.621 (Δ=+0.06402, +0.02847V/100cyc) → flat · context

**히스테리시스 Δ** (`delta_hyst_area`)
- 의미: 기준 대비 면적.
- 계산: delta.
- 트렌드: 히스테리시스 Δ: early=0.01813 → late=0.06846 (Δ=+0.05033, +0.02057V/100cyc) → increasing · matches_aging

**max dV Δ** (`delta_hyst_max_dV`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: max dV Δ: early=0.02201 → late=0.08603 (Δ=+0.06402, +0.02847V/100cyc) → increasing · matches_aging

**충전 플래토 V** (`chg_plateau_V`)
- 의미: 충전 플래토 전압.
- 계산: plateau detect.
- 트렌드: 충전 플래토 V: early=3.732 → late=3.777 (Δ=+0.04519, +0.01604V/100cyc) → flat · context

**충전 플래토 폭** (`chg_plateau_width`)
- 의미: 충전 플래토 Q 폭.
- 계산: plateau width.
- 트렌드: 충전 플래토 폭: early=13.19 → late=13.83 (Δ=+0.6465, +0.8002Q-units/100cyc) → increasing · context

**방전 플래토 V** (`dchg_plateau_V`)
- 의미: 방전 플래토 전압.
- 계산: plateau detect.
- 트렌드: 방전 플래토 V: early=3.163 → late=3.12 (Δ=-0.04305, -0.01868V/100cyc) → flat · context

**방전 플래토 폭** (`dchg_plateau_width`)
- 의미: 방전 플래토 Q 폭.
- 계산: plateau width.
- 트렌드: 방전 플래토 폭: early=16.87 → late=14.8 (Δ=-2.067, -1.075Q-units/100cyc) → decreasing · matches_aging

**방전 플래토 ΔV** (`delta_dchg_plateau_V`)
- 의미: 기준 대비 이동.
- 계산: delta plateau V.
- 트렌드: 방전 플래토 ΔV: early=-0.03799 → late=-0.08104 (Δ=-0.04305, -0.01868V/100cyc) → decreasing · context

**방전 컷오프 마진** (`dchg_V_cutoff_margin`)
- 의미: 컷오프까지 여유.
- 계산: Vmin-margin.
- 트렌드: 방전 컷오프 마진: early=0.4009 → late=0.2644 (Δ=-0.1365, -0.06004V/100cyc) → decreasing · matches_aging

**컷오프 마진 Δ** (`delta_dchg_V_cutoff_margin`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 컷오프 마진 Δ: early=-0.03642 → late=-0.1729 (Δ=-0.1365, -0.06004V/100cyc) → decreasing · matches_aging

**방전 형상 DTW** (`dchg_shape_DTW`)
- 의미: 기준 곡선 DTW 거리.
- 계산: DTW vs baseline.
- 트렌드: 방전 형상 DTW: early=0.003741 → late=0.007897 (Δ=+0.004156, +0.0017571/100cyc) → increasing · matches_aging

**DTW Δ** (`delta_dchg_shape_DTW`)
- 의미: 기준 대비 DTW.
- 계산: delta.
- 트렌드: DTW Δ: early=0.002047 → late=0.006203 (Δ=+0.004156, +0.0017571/100cyc) → increasing · matches_aging

### dQ/dV · dV/dQ 피크

**충전 dQ/dV 피크1 V** (`chg_dQdV_peak1_V`)
- 의미: 충전 IC 1번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크1 V: early=3.741 → late=3.784 (Δ=+0.043, +0.01064V/100cyc) → flat · context

**충전 dQ/dV 피크1 높이** (`chg_dQdV_peak1`)
- 의미: 충전 IC 1번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크1 높이: early=79.77 → late=96.32 (Δ=+16.55, -849.6Ah/V/100cyc) → decreasing · context

**방전 dQ/dV 피크1 V** (`dchg_dQdV_peak1_V`)
- 의미: 방전 IC 1번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크1 V: early=3.159 → late=3.108 (Δ=-0.05122, -0.02129V/100cyc) → flat · context

**방전 dQ/dV 피크1 높이** (`dchg_dQdV_peak1`)
- 의미: 방전 IC 1번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크1 높이: early=-70.11 → late=-53.3 (Δ=+16.81, +7.031Ah/V/100cyc) → increasing · context

**충전 dV/dQ 피크1 Q** (`chg_dVdQ_peak1_Q`)
- 의미: 충전 dV/dQ 1번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 충전 dV/dQ 피크1 Q: early=56.36 → late=49.36 (Δ=-6.996, -2.543Ah/100cyc) → flat · context

**충전 dV/dQ 피크1 높이** (`chg_dVdQ_peak1`)
- 의미: 충전 dV/dQ 1번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 충전 dV/dQ 피크1 높이: early=0.01527 → late=0.01637 (Δ=+0.001103, +0.000459V/Ah/100cyc) → flat · context

**방전 dV/dQ 피크1 Q** (`dchg_dVdQ_peak1_Q`)
- 의미: 방전 dV/dQ 1번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 방전 dV/dQ 피크1 Q: early=11.96 → late=27.96 (Δ=+16.01, +9.68Ah/100cyc) → increasing · context

**방전 dV/dQ 피크1 높이** (`dchg_dVdQ_peak1`)
- 의미: 방전 dV/dQ 1번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 방전 dV/dQ 피크1 높이: early=-0.02275 → late=-0.02132 (Δ=+0.00143, +0.0008813V/Ah/100cyc) → flat · context

**충전 dQ/dV 피크2 V** (`chg_dQdV_peak2_V`)
- 의미: 충전 IC 2번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크2 V: early=3.765 → late=3.991 (Δ=+0.2264, +0.09095V/100cyc) → flat · context

**충전 dQ/dV 피크2 높이** (`chg_dQdV_peak2`)
- 의미: 충전 IC 2번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크2 높이: early=99.65 → late=80.15 (Δ=-19.51, -8.55Ah/V/100cyc) → decreasing · context

**방전 dQ/dV 피크2 V** (`dchg_dQdV_peak2_V`)
- 의미: 방전 IC 2번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크2 V: early=3.642 → late=3.548 (Δ=-0.09472, -0.02928V/100cyc) → flat · context

**방전 dQ/dV 피크2 높이** (`dchg_dQdV_peak2`)
- 의미: 방전 IC 2번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크2 높이: early=-54.69 → late=-48.51 (Δ=+6.184, +2.413Ah/V/100cyc) → flat · context

**충전 dV/dQ 피크2 Q** (`chg_dVdQ_peak2_Q`)
- 의미: 충전 dV/dQ 2번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**충전 dV/dQ 피크2 높이** (`chg_dVdQ_peak2`)
- 의미: 충전 dV/dQ 2번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**방전 dV/dQ 피크2 Q** (`dchg_dVdQ_peak2_Q`)
- 의미: 방전 dV/dQ 2번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**방전 dV/dQ 피크2 높이** (`dchg_dVdQ_peak2`)
- 의미: 방전 dV/dQ 2번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**충전 dQ/dV 피크3 V** (`chg_dQdV_peak3_V`)
- 의미: 충전 IC 3번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크3 V: early=3.966 → late=3.969 (Δ=+0.003044, +0.1034V/100cyc) → flat · context

**충전 dQ/dV 피크3 높이** (`chg_dQdV_peak3`)
- 의미: 충전 IC 3번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크3 높이: early=83.59 → late=83.53 (Δ=-0.05275, +58.68Ah/V/100cyc) → increasing · context

**방전 dQ/dV 피크3 V** (`dchg_dQdV_peak3_V`)
- 의미: 방전 IC 3번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크3 V: early=3.971 → late=3.829 (Δ=-0.1425, -0.05718V/100cyc) → flat · context

**방전 dQ/dV 피크3 높이** (`dchg_dQdV_peak3`)
- 의미: 방전 IC 3번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크3 높이: early=-61.24 → late=-48.94 (Δ=+12.3, +4.688Ah/V/100cyc) → increasing · context

**충전 dV/dQ 피크3 Q** (`chg_dVdQ_peak3_Q`)
- 의미: 충전 dV/dQ 3번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**충전 dV/dQ 피크3 높이** (`chg_dVdQ_peak3`)
- 의미: 충전 dV/dQ 3번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**방전 dV/dQ 피크3 Q** (`dchg_dVdQ_peak3_Q`)
- 의미: 방전 dV/dQ 3번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**방전 dV/dQ 피크3 높이** (`dchg_dVdQ_peak3`)
- 의미: 방전 dV/dQ 3번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**충전 dQ/dV 피크4 V** (`chg_dQdV_peak4_V`)
- 의미: 충전 IC 4번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**충전 dQ/dV 피크4 높이** (`chg_dQdV_peak4`)
- 의미: 충전 IC 4번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 

**방전 dQ/dV 피크4 V** (`dchg_dQdV_peak4_V`)
- 의미: 방전 IC 4번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**방전 dQ/dV 피크4 높이** (`dchg_dQdV_peak4`)
- 의미: 방전 IC 4번 피크 높이.
- 계산: peak height.
- 트렌드: 

**충전 dV/dQ 피크4 Q** (`chg_dVdQ_peak4_Q`)
- 의미: 충전 dV/dQ 4번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**충전 dV/dQ 피크4 높이** (`chg_dVdQ_peak4`)
- 의미: 충전 dV/dQ 4번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**방전 dV/dQ 피크4 Q** (`dchg_dVdQ_peak4_Q`)
- 의미: 방전 dV/dQ 4번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**방전 dV/dQ 피크4 높이** (`dchg_dVdQ_peak4`)
- 의미: 방전 dV/dQ 4번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**충전 dQ/dV 피크5 V** (`chg_dQdV_peak5_V`)
- 의미: 충전 IC 5번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**충전 dQ/dV 피크5 높이** (`chg_dQdV_peak5`)
- 의미: 충전 IC 5번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 

**방전 dQ/dV 피크5 V** (`dchg_dQdV_peak5_V`)
- 의미: 방전 IC 5번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**방전 dQ/dV 피크5 높이** (`dchg_dQdV_peak5`)
- 의미: 방전 IC 5번 피크 높이.
- 계산: peak height.
- 트렌드: 

**충전 dV/dQ 피크5 Q** (`chg_dVdQ_peak5_Q`)
- 의미: 충전 dV/dQ 5번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**충전 dV/dQ 피크5 높이** (`chg_dVdQ_peak5`)
- 의미: 충전 dV/dQ 5번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**방전 dV/dQ 피크5 Q** (`dchg_dVdQ_peak5_Q`)
- 의미: 방전 dV/dQ 5번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**방전 dV/dQ 피크5 높이** (`dchg_dVdQ_peak5`)
- 의미: 방전 dV/dQ 5번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**충전 dQ/dV 피크6 V** (`chg_dQdV_peak6_V`)
- 의미: 충전 IC 6번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**충전 dQ/dV 피크6 높이** (`chg_dQdV_peak6`)
- 의미: 충전 IC 6번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 

**방전 dQ/dV 피크6 V** (`dchg_dQdV_peak6_V`)
- 의미: 방전 IC 6번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**방전 dQ/dV 피크6 높이** (`dchg_dQdV_peak6`)
- 의미: 방전 IC 6번 피크 높이.
- 계산: peak height.
- 트렌드: 

**충전 dV/dQ 피크6 Q** (`chg_dVdQ_peak6_Q`)
- 의미: 충전 dV/dQ 6번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**충전 dV/dQ 피크6 높이** (`chg_dVdQ_peak6`)
- 의미: 충전 dV/dQ 6번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**방전 dV/dQ 피크6 Q** (`dchg_dVdQ_peak6_Q`)
- 의미: 방전 dV/dQ 6번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**방전 dV/dQ 피크6 높이** (`dchg_dVdQ_peak6`)
- 의미: 방전 dV/dQ 6번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**충전 dQ/dV 피크7 V** (`chg_dQdV_peak7_V`)
- 의미: 충전 IC 7번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**충전 dQ/dV 피크7 높이** (`chg_dQdV_peak7`)
- 의미: 충전 IC 7번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 

**방전 dQ/dV 피크7 V** (`dchg_dQdV_peak7_V`)
- 의미: 방전 IC 7번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**방전 dQ/dV 피크7 높이** (`dchg_dQdV_peak7`)
- 의미: 방전 IC 7번 피크 높이.
- 계산: peak height.
- 트렌드: 

**충전 dV/dQ 피크7 Q** (`chg_dVdQ_peak7_Q`)
- 의미: 충전 dV/dQ 7번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**충전 dV/dQ 피크7 높이** (`chg_dVdQ_peak7`)
- 의미: 충전 dV/dQ 7번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**방전 dV/dQ 피크7 Q** (`dchg_dVdQ_peak7_Q`)
- 의미: 방전 dV/dQ 7번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**방전 dV/dQ 피크7 높이** (`dchg_dVdQ_peak7`)
- 의미: 방전 dV/dQ 7번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**충전 dQ/dV 피크8 V** (`chg_dQdV_peak8_V`)
- 의미: 충전 IC 8번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**충전 dQ/dV 피크8 높이** (`chg_dQdV_peak8`)
- 의미: 충전 IC 8번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 

**방전 dQ/dV 피크8 V** (`dchg_dQdV_peak8_V`)
- 의미: 방전 IC 8번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 

**방전 dQ/dV 피크8 높이** (`dchg_dQdV_peak8`)
- 의미: 방전 IC 8번 피크 높이.
- 계산: peak height.
- 트렌드: 

**충전 dV/dQ 피크8 Q** (`chg_dVdQ_peak8_Q`)
- 의미: 충전 dV/dQ 8번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**충전 dV/dQ 피크8 높이** (`chg_dVdQ_peak8`)
- 의미: 충전 dV/dQ 8번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**방전 dV/dQ 피크8 Q** (`dchg_dVdQ_peak8_Q`)
- 의미: 방전 dV/dQ 8번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 

**방전 dV/dQ 피크8 높이** (`dchg_dVdQ_peak8`)
- 의미: 방전 dV/dQ 8번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 

**충전 피크1 ΔV** (`delta_chg_dQdV_peak1_V`)
- 의미: 기준 대비 충전 dQ/dV 피크1 이동.
- 계산: delta_chg_dQdV_peak1_V
- 트렌드: 충전 피크1 ΔV: early=0.3039 → late=0.3469 (Δ=+0.043, +0.01064V/100cyc) → flat · context

**방전 피크1 ΔV** (`delta_dchg_dQdV_peak1_V`)
- 의미: 기준 대비 방전 dQ/dV 피크1 이동.
- 계산: delta_dchg_dQdV_peak1_V
- 트렌드: 방전 피크1 ΔV: early=-0.01869 → late=-0.06991 (Δ=-0.05122, -0.02129V/100cyc) → decreasing · context

**방전 dV/dQ @SOC0** (`dchg_dVdQ_SOC0`)
- 의미: 저SOC cliff dV/dQ.
- 계산: dchg_dVdQ_SOC0
- 트렌드: 방전 dV/dQ @SOC0: early=0.1009 → late=0.05606 (Δ=-0.04487, -0.02074V/Ah/100cyc) → decreasing · context

**방전 dV/dQ @SOC5** (`dchg_dVdQ_SOC5`)
- 의미: SOC≈5% dV/dQ.
- 계산: dchg_dVdQ_SOC5
- 트렌드: 방전 dV/dQ @SOC5: early=0.0449 → late=0.03828 (Δ=-0.00662, -0.003173V/Ah/100cyc) → decreasing · context

**방전 dV/dQ @SOC10** (`dchg_dVdQ_SOC10`)
- 의미: SOC≈10% dV/dQ.
- 계산: dchg_dVdQ_SOC10
- 트렌드: 방전 dV/dQ @SOC10: early=0.02659 → late=0.02928 (Δ=+0.002688, +0.0008974V/Ah/100cyc) → flat · context

**방전 dV/dQ @mid** (`dchg_dVdQ_SOCmid`)
- 의미: 중SOC dV/dQ.
- 계산: dchg_dVdQ_SOCmid
- 트렌드: 방전 dV/dQ @mid: early=0.01907 → late=0.02087 (Δ=+0.0018, +0.0008028V/Ah/100cyc) → flat · context

**방전 cliff Q** (`dchg_dVdQ_SOC0_Q`)
- 의미: SOC0 dV/dQ 위치 Q.
- 계산: dchg_dVdQ_SOC0_Q
- 트렌드: 방전 cliff Q: early=69.39 → late=62.61 (Δ=-6.776, -2.467Ah/100cyc) → flat · context

**방전 cliff 폭** (`dchg_dVdQ_SOC0_cliff_width`)
- 의미: 저SOC cliff 폭.
- 계산: dchg_dVdQ_SOC0_cliff_width
- 트렌드: 방전 cliff 폭: early=4.74 → late=2.635 (Δ=-2.105, -0.9542Ah/100cyc) → decreasing · context

**cliff/mid 비** (`dchg_dVdQ_SOC0_to_mid_ratio`)
- 의미: SOC0/mid dV/dQ 비.
- 계산: dchg_dVdQ_SOC0_to_mid_ratio
- 트렌드: cliff/mid 비: early=5.29 → late=2.683 (Δ=-2.607, -1.1991/100cyc) → decreasing · context

**충전 dV/dQ @100** (`chg_dVdQ_SOC100`)
- 의미: 만충 부근 dV/dQ.
- 계산: chg_dVdQ_SOC100
- 트렌드: 충전 dV/dQ @100: early=0.008067 → late=0.008414 (Δ=+0.0003465, +0.001896V/Ah/100cyc) → increasing · context

**dV/dQ SOC0 Δ** (`delta_dchg_dVdQ_SOC0`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0
- 트렌드: dV/dQ SOC0 Δ: early=-0.003286 → late=-0.04816 (Δ=-0.04487, -0.02074V/Ah/100cyc) → decreasing · context

**dV/dQ SOC5 Δ** (`delta_dchg_dVdQ_SOC5`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC5
- 트렌드: dV/dQ SOC5 Δ: early=-0.00363 → late=-0.01025 (Δ=-0.00662, -0.003173V/Ah/100cyc) → decreasing · context

**dV/dQ SOC10 Δ** (`delta_dchg_dVdQ_SOC10`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC10
- 트렌드: dV/dQ SOC10 Δ: early=-0.001709 → late=0.0009792 (Δ=+0.002688, +0.0008974V/Ah/100cyc) → increasing · context

**dV/dQ mid Δ** (`delta_dchg_dVdQ_SOCmid`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOCmid
- 트렌드: dV/dQ mid Δ: early=0.0004623 → late=0.002263 (Δ=+0.0018, +0.0008028V/Ah/100cyc) → increasing · context

**dV/dQ 100 Δ** (`delta_chg_dVdQ_SOC100`)
- 의미: 기준 대비.
- 계산: delta_chg_dVdQ_SOC100
- 트렌드: dV/dQ 100 Δ: early=-0.005226 → late=-0.004879 (Δ=+0.0003465, +0.001896V/Ah/100cyc) → increasing · context

**cliff 폭 Δ** (`delta_dchg_dVdQ_SOC0_cliff_width`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0_cliff_width
- 트렌드: cliff 폭 Δ: early=-0.8389 → late=-2.944 (Δ=-2.105, -0.9542Ah/100cyc) → decreasing · context

**cliff/mid Δ** (`delta_dchg_dVdQ_SOC0_to_mid_ratio`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0_to_mid_ratio
- 트렌드: cliff/mid Δ: early=-0.3104 → late=-2.918 (Δ=-2.607, -1.1991/100cyc) → decreasing · context

**충전 IC 면적합** (`chg_dQdV_area_sum`)
- 의미: dQ/dV 피크 면적 합.
- 계산: chg_dQdV_area_sum
- 트렌드: 충전 IC 면적합: early=65.97 → late=53.03 (Δ=-12.94, -5.771Ah/100cyc) → decreasing · context

**방전 IC 면적합** (`dchg_dQdV_area_sum`)
- 의미: dQ/dV 피크 면적 합.
- 계산: dchg_dQdV_area_sum
- 트렌드: 방전 IC 면적합: early=69.39 → late=62.61 (Δ=-6.776, -2.467Ah/100cyc) → flat · context

### 수송 · rate · η

**RCF** (`RCF`)
- 의미: Q_0.5C / Q_C/3.
- 계산: routine/RPT Q.
- 트렌드: RCF: early=0.9711 → late=0.9569 (Δ=-0.01422, -1.5e-061/100cyc) → flat · stable

**RCF 기울기/100** (`RCF_slope_100`)
- 의미: RCF 변화율.
- 계산: first-last slope.
- 트렌드: RCF 기울기/100: early=-0.01506 → late=-0.01506 (Δ=+0, +3.975e-181/100cyc/100cyc) → flat · stable

**PER** (`PER`)
- 의미: η/(ΔI·R).
- 계산: eta_SOC50/(dI*R).
- 트렌드: 

**η @SOC20** (`eta_SOC20`)
- 의미: 저SOC 과전위.
- 계산: C/3 vs 0.5C.
- 트렌드: 

**η @SOC50** (`eta_SOC50`)
- 의미: 중SOC 과전위.
- 계산: C/3 vs 0.5C.
- 트렌드: 

**η @SOC80** (`eta_SOC80`)
- 의미: 고SOC 과전위.
- 계산: C/3 vs 0.5C.
- 트렌드: 

**η max** (`eta_max`)
- 의미: 최대 과전위.
- 계산: max η(SOC).
- 트렌드: 

**η mean** (`eta_mean`)
- 의미: 평균 과전위.
- 계산: mean η.
- 트렌드: 

**η argmax SOC** (`eta_argmax_SOC`)
- 의미: η 최대 SOC.
- 계산: argmax.
- 트렌드: 

**η 저SOC 기울기** (`eta_slope_lowSOC`)
- 의미: 저SOC η 기울기.
- 계산: slope low band.
- 트렌드: 

**Reff scale** (`Reff_scale`)
- 의미: 유효 R 스케일.
- 계산: shape fit scale.
- 트렌드: 

**Reff fit R2** (`Reff_shape_fit_r2`)
- 의미: Reff 형상 fit 품질.
- 계산: r2.
- 트렌드: 

**Reff 잔차 SOC20** (`Reff_resid_soc20`)
- 의미: Reff 모델 잔차.
- 계산: resid.
- 트렌드: 

**Reff 잔차 SOC50** (`Reff_resid_soc50`)
- 의미: Reff 모델 잔차.
- 계산: resid.
- 트렌드: 

**Reff 잔차 SOC80** (`Reff_resid_soc80`)
- 의미: Reff 모델 잔차.
- 계산: resid.
- 트렌드: 

**I∞ 정규화** (`I_inf_norm`)
- 의미: CV 잔류전류 정규화.
- 계산: I_inf / I_ref.
- 트렌드: 

**펄스 1s 샘플수** (`pulse_sample_count_1s`)
- 의미: t≤1s 샘플 수.
- 계산: quality.
- 트렌드: 펄스 1s 샘플수: early=5 → late=7 (Δ=+2, +0.9993count/100cyc) → increasing · context

**펄스 전류 안정도** (`pulse_current_stability`)
- 의미: std(I)/|I|.
- 계산: quality.
- 트렌드: 펄스 전류 안정도: early=0.03844 → late=0.04798 (Δ=+0.009536, +0.0039491/100cyc) → increasing · opposite_aging

**rest 충분성** (`rest_sufficiency`)
- 의미: 휴지 길이/품질.
- 계산: quality.
- 트렌드: rest 충분성: early=3 → late=3 (Δ=+0, -1.678e-171/100cyc) → flat · context

**레그 완전성** (`leg_completeness`)
- 의미: 충방전 레그 완전성.
- 계산: quality.
- 트렌드: 레그 완전성: early=1 → late=1 (Δ=+0, -2.526e-161/100cyc) → flat · context

**완화 완성도 max** (`relax_completeness_max`)
- 의미: SOC별 최대 완화 완성도.
- 계산: max.
- 트렌드: 

**샘플/mV** (`samples_per_mV`)
- 의미: 전압 해상도 샘플밀도.
- 계산: dqdv quality.
- 트렌드: 샘플/mV: early=0.3576 → late=0.3476 (Δ=-0.01003, -0.0036561/mV/100cyc) → flat · context

### OCV · 자기방전

**OCV V∞ SOC80** (`ocv_V_inf_soc80`)
- 의미: 고SOC 무한시간 OCV.
- 계산: recovery/rest V_inf.
- 트렌드: 

**OCV V∞ SOC50** (`ocv_V_inf_soc50`)
- 의미: 중SOC OCV.
- 계산: V_inf.
- 트렌드: 

**OCV V∞ SOC20** (`ocv_V_inf_soc20`)
- 의미: 저SOC OCV.
- 계산: V_inf.
- 트렌드: 

**OCV spread 20–80** (`ocv_spread_20_80`)
- 의미: SOC20–80 OCV 폭.
- 계산: V80-V20.
- 트렌드: 

**OCV spread 50–80** (`ocv_spread_50_80`)
- 의미: SOC50–80 폭.
- 계산: V80-V50.
- 트렌드: 

**OCV spread 20–50** (`ocv_spread_20_50`)
- 의미: SOC20–50 폭.
- 계산: V50-V20.
- 트렌드: 

**OCV 평행이동** (`ocv_parallel_shift`)
- 의미: OCV 곡선 평행 시프트.
- 계산: block OCV shift.
- 트렌드: 

**OCV 폭 압축** (`ocv_spread_compression`)
- 의미: spread 축소.
- 계산: Δspread.
- 트렌드: 

**OCV80 Δ** (`delta_ocv_V_inf_soc80`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 

**OCV50 Δ** (`delta_ocv_V_inf_soc50`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 

**OCV20 Δ** (`delta_ocv_V_inf_soc20`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 

**OCV spread Δ** (`delta_ocv_spread_20_80`)
- 의미: 기준 대비 폭 변화.
- 계산: delta.
- 트렌드: 

### 곡선 fit · ΔQ(V)

**LAM 곡선 proxy** (`LAM_curve_proxy`)
- 의미: V–Q scale 축소 proxy (절대 LAM% 아님).
- 계산: (1-s)*100.
- 트렌드: LAM 곡선 proxy: early=-2.983 → late=-16.28 (Δ=-13.3, -5.282%/100cyc) → decreasing · context

**LLI 곡선 proxy** (`LLI_curve_proxy`)
- 의미: Q 오프셋 proxy (절대 LLI% 아님).
- 계산: offset/Qmax*100.
- 트렌드: LLI 곡선 proxy: early=-0.6179 → late=-2.925 (Δ=-2.307, -1.265%/100cyc) → decreasing · context

**R 곡선 proxy** (`R_curve_proxy`)
- 의미: 곡선 fit dR proxy.
- 계산: fit_dR.
- 트렌드: R 곡선 proxy: early=1.316 → late=4.426 (Δ=+3.11, +1.382mΩ/100cyc) → increasing · matches_aging

**방전 fit scale** (`dchg_fit_scale`)
- 의미: 기준 대비 scale s.
- 계산: 3-param fit.
- 트렌드: 방전 fit scale: early=1.03 → late=1.163 (Δ=+0.133, +0.052821/100cyc) → flat · stable

**방전 fit offset** (`dchg_fit_offset`)
- 의미: Q 오프셋.
- 계산: 3-param fit.
- 트렌드: 방전 fit offset: early=-0.4427 → late=-2.096 (Δ=-1.653, -0.9067Ah/100cyc) → decreasing · context

**방전 fit dR** (`dchg_fit_dR`)
- 의미: 저항 항.
- 계산: 3-param fit.
- 트렌드: 방전 fit dR: early=1.316 → late=4.426 (Δ=+3.11, +1.382mΩ/100cyc) → increasing · matches_aging

**fit 잔차 RMS** (`dchg_fit_residual_rms`)
- 의미: 잔차 rms.
- 계산: RMS(resid).
- 트렌드: fit 잔차 RMS: early=6.482 → late=23.62 (Δ=+17.14, +7.851mV/100cyc) → increasing · matches_aging

**fit 잔차 max** (`dchg_fit_residual_max`)
- 의미: 잔차 최대.
- 계산: max|resid|.
- 트렌드: fit 잔차 max: early=57.75 → late=150.4 (Δ=+92.67, +35.8mV/100cyc) → increasing · matches_aging

**잔차 argmax SOC** (`dchg_fit_residual_argmax_SOC`)
- 의미: 잔차 최대 SOC (방전 DOD→SOC 변환).
- 계산: argmax residual.
- 트렌드: 잔차 argmax SOC: early=99.49 → late=100 (Δ=+0.5116, +0.1207%/100cyc) → flat · context

**fit R2** (`dchg_fit_r2`)
- 의미: 곡선 fit 품질.
- 계산: r2.
- 트렌드: fit R2: early=0.9998 → late=0.997 (Δ=-0.002784, -0.0012751/100cyc) → flat · context

**fit corr(s,o)** (`dchg_fit_corr_s_o`)
- 의미: scale-offset 상관 (축퇴 지표).
- 계산: corr.
- 트렌드: fit corr(s,o): early=0.5081 → late=0.6464 (Δ=+0.1383, +0.053191/100cyc) → increasing · context

**잔차 argmax DOD** (`dchg_fit_residual_argmax_DOD`)
- 의미: 잔차 최대 DOD.
- 계산: argmax DOD.
- 트렌드: 잔차 argmax DOD: early=0.5116 → late=0 (Δ=-0.5116, -0.1207%/100cyc) → decreasing · context

**ΔQ(V) min** (`dQV_min`)
- 의미: 전압빈 ΔQ 최소.
- 계산: histogram.
- 트렌드: ΔQ(V) min: early=-4.586 → late=-15.6 (Δ=-11.01, -4.464Ah/100cyc) → decreasing · context

**ΔQ(V) mean** (`dQV_mean`)
- 의미: ΔQ 평균.
- 계산: mean.
- 트렌드: ΔQ(V) mean: early=-3.289 → late=-10.75 (Δ=-7.459, -2.968Ah/100cyc) → decreasing · context

**ΔQ(V) var** (`dQV_var`)
- 의미: ΔQ 분산.
- 계산: var.
- 트렌드: ΔQ(V) var: early=0.5499 → late=5.774 (Δ=+5.224, +2.257Ah2/100cyc) → increasing · matches_aging

**ΔQ(V) log-var** (`dQV_log_var`)
- 의미: log10 분산.
- 계산: log10(var).
- 트렌드: ΔQ(V) log-var: early=-0.2597 → late=0.7615 (Δ=+1.021, +0.4031/100cyc) → increasing · matches_aging

**ΔQ(V) skew** (`dQV_skew`)
- 의미: 왜도.
- 계산: skew.
- 트렌드: ΔQ(V) skew: early=-0.3387 → late=-0.6991 (Δ=-0.3603, -0.14661/100cyc) → decreasing · context

**ΔQ(V) kurtosis** (`dQV_kurtosis`)
- 의미: 첨도.
- 계산: kurtosis.
- 트렌드: ΔQ(V) kurtosis: early=-0.9607 → late=-0.6674 (Δ=+0.2933, +0.099781/100cyc) → increasing · context

**ΔQ argmin V** (`dQV_argmin_V`)
- 의미: ΔQ 최소 전압.
- 계산: argmin.
- 트렌드: ΔQ argmin V: early=3.118 → late=3.042 (Δ=-0.07644, -0.03204V/100cyc) → flat · context

**dQ/dV SNR** (`dqdv_snr`)
- 의미: IC 신호대잡음.
- 계산: snr estimate.
- 트렌드: dQ/dV SNR: early=74.55 → late=71.99 (Δ=-2.557, -0.74771/100cyc) → flat · context

**데이터 품질점수** (`quality_score`)
- 의미: 추출 품질 종합.
- 계산: quality gates.
- 트렌드: 데이터 품질점수: early=1 → late=1 (Δ=+0, -2.526e-160–1/100cyc) → flat · context

**전압 노이즈 σ** (`v_noise_sigma`)
- 의미: 전압 노이즈 추정.
- 계산: noise sigma.
- 트렌드: 전압 노이즈 σ: early=0.0228 → late=0.02362 (Δ=+0.0008128, +0.0002606V/100cyc) → flat · context

**ΔQ(V) 기준 사이클** (`dQV_ref_cycle`)
- 의미: ΔQ 비교 기준 사이클.
- 계산: ref cycle id.
- 트렌드: ΔQ(V) 기준 사이클: early=3 → late=3 (Δ=+0, -1.678e-17cyc/100cyc) → flat · context

**온도 가용** (`temperature_available`)
- 의미: Temp 컬럼 유효 여부.
- 계산: bool→float.
- 트렌드: 온도 가용: early=0 → late=0 (Δ=+0, +00/1/100cyc) → flat · context

**Q_relax 유의** (`Q_relax_significant`)
- 의미: 완화 용량 유의 플래그.
- 계산: threshold flag.
- 트렌드: Q_relax 유의: early=1 → late=1 (Δ=+0, -0.17570/1/100cyc) → decreasing · context

**fit 축퇴 플래그** (`dchg_fit_degenerate_flag`)
- 의미: scale bound 포화 등.
- 계산: degenerate flag.
- 트렌드: fit 축퇴 플래그: early=0 → late=0 (Δ=+0, +00/1/100cyc) → flat · context

**η 유효** (`eta_valid`)
- 의미: 과전위 계산 유효 플래그.
- 계산: eta_valid.
- 트렌드: 

**fade b 표준오차** (`fade_exponent_b_se`)
- 의미: fade 지수 표준오차.
- 계산: fit se.
- 트렌드: fade b 표준오차: early=0.04217 → late=0.04217 (Δ=+0, -9.384e-181/100cyc) → flat · context

**ΔQ 유효 V범위** (`dQV_valid_V_range`)
- 의미: ΔQ 집계 전압폭.
- 계산: Vmax-Vmin used.
- 트렌드: ΔQ 유효 V범위: early=0.7873 → late=0.7873 (Δ=+0, -7.515e-17V/100cyc) → flat · context

### fade · knee

**fade 지수 b** (`fade_exponent_b`)
- 의미: SoHQ power-law 지수.
- 계산: SoHQ fit.
- 트렌드: fade 지수 b: early=0.6066 → late=0.6066 (Δ=+0, -7.647e-171/100cyc) → flat · context

**fade 지수 a** (`fade_exponent_a`)
- 의미: power-law 계수.
- 계산: SoHQ fit.
- 트렌드: fade 지수 a: early=0.00345 → late=0.00345 (Δ=+0, -6.793e-191/100cyc) → flat · context

**fade fit R2** (`fade_fit_r2`)
- 의미: fade 적합도.
- 계산: r2.
- 트렌드: fade fit R2: early=0.9484 → late=0.9484 (Δ=+0, -2.448e-161/100cyc) → flat · context

**fade SoHQ0** (`fade_sohq0`)
- 의미: fit 초기 SoHQ.
- 계산: intercept.
- 트렌드: fade SoHQ0: early=97.37 → late=97.37 (Δ=+0, -2.532e-14%/100cyc) → flat · context

**knee 사이클** (`knee_cycle_bw`)
- 의미: bilinear knee 위치.
- 계산: broken-stick SoHQ.
- 트렌드: knee 사이클: early=30 → late=30 (Δ=+0, -3.132e-15cyc/100cyc) → flat · context

**knee 심각도** (`knee_severity`)
- 의미: 전후 기울기 차이.
- 계산: slope_after-before.
- 트렌드: knee 심각도: early=0 → late=0 (Δ=+0, +01/100cyc) → flat · stable

**knee 전 기울기** (`knee_slope_before`)
- 의미: knee 이전 fade 기울기.
- 계산: bilinear.
- 트렌드: knee 전 기울기: early=-0.1654 → late=-0.1654 (Δ=+0, +5.592e-17%/cyc/100cyc) → flat · stable

**knee 후 기울기** (`knee_slope_after`)
- 의미: knee 이후 fade 기울기.
- 계산: bilinear.
- 트렌드: knee 후 기울기: early=-0.02693 → late=-0.02693 (Δ=+0, +9.397e-18%/cyc/100cyc) → flat · stable

**knee fit R2** (`knee_fit_r2`)
- 의미: knee 적합도.
- 계산: r2.
- 트렌드: knee fit R2: early=0.9858 → late=0.9858 (Δ=+0, -1.171e-161/100cyc) → flat · context

### 열화 패턴 점수

**PE activity 패턴** (`LAM_PE_pattern_score`)
- 의미: NCM activity/isolation (절대 LAM% 아님).
- 계산: mode_weights LAM_PE.
- 트렌드: PE activity 패턴: early=0.6051 → late=0.9263 (Δ=+0.3212, +0.14480–1/100cyc) → increasing · matches_aging

**NE 패턴 점수** (`LAM_NE_pattern_score`)
- 의미: NE 관련 패턴 (Si-on-Gr에선 보조).
- 계산: mode_weights LAM_NE.
- 트렌드: 

**contact_loss** (`contact_loss_score`)
- 의미: 옴/스택/접촉 증거 합.
- 계산: RΩ growth 등 가중합.
- 트렌드: contact_loss: early=0.8664 → late=0.9423 (Δ=+0.0759, +0.04940–1/100cyc) → increasing · matches_aging

**LLI 패턴** (`LLI_pattern_score`)
- 의미: CE·slippage·offset 기반.
- 계산: mode_weights LLI.
- 트렌드: LLI 패턴: early=0.3694 → late=0.6369 (Δ=+0.2675, +0.12010–1/100cyc) → increasing · matches_aging

**계면 R 패턴** (`interface_R_score`)
- 의미: Rct·VE 등 계면저항.
- 계산: mode_weights interface_R.
- 트렌드: 계면 R 패턴: early=0.4752 → late=0.8706 (Δ=+0.3954, +0.14840–1/100cyc) → increasing · matches_aging

**고체확산 패턴** (`solid_diffusion_score`)
- 의미: A_diff·PER·RCF.
- 계산: mode_weights solid_diffusion.
- 트렌드: 고체확산 패턴: early=0.5208 → late=0.6973 (Δ=+0.1764, +0.026140–1/100cyc) → flat · stable

**SE 분해 패턴** (`SE_decomposition_score`)
- 의미: CE↓·Rct↑ 등 SE 분해 가설.
- 계산: mode_weights SE_decomposition.
- 트렌드: SE 분해 패턴: early=0.1836 → late=0.3461 (Δ=+0.1625, +0.069950–1/100cyc) → increasing · matches_aging

**마이크로쇼트 패턴** (`microshort_score`)
- 의미: 자기방전·CE 기반 soft-short 가설.
- 계산: mode_weights microshort.
- 트렌드: 

**임피던스 패턴** (`impedance_pattern_score`)
- 의미: 총 임피던스 성장 패턴.
- 계산: mode score.
- 트렌드: 

**수송제한 패턴** (`transport_limitation_score`)
- 의미: rate/수송 제한 패턴.
- 계산: mode score.
- 트렌드: 

**플레이팅 리스크** (`plating_risk_score`)
- 의미: Li plating 위험 패턴.
- 계산: mode score.
- 트렌드: 

**contact_loss 신뢰도** (`contact_loss_confidence`)
- 의미: 패턴 점수 신뢰도.
- 계산: evidence coverage.
- 트렌드: contact_loss 신뢰도: early=0.52 → late=0.448 (Δ=-0.072, +0.0084290–1/100cyc) → flat · context

**LAM_PE 신뢰도** (`LAM_PE_confidence`)
- 의미: 패턴 신뢰도.
- 계산: confidence.
- 트렌드: LAM_PE 신뢰도: early=0.88 → late=0.616 (Δ=-0.264, -0.10330–1/100cyc) → decreasing · context

**LLI 신뢰도** (`LLI_confidence`)
- 의미: 패턴 신뢰도.
- 계산: confidence.
- 트렌드: LLI 신뢰도: early=0.72 → late=0.72 (Δ=+0, -0.023570–1/100cyc) → flat · context

### 전극 lean 가설

**PE lean** (`PE_side_score`)
- 의미: 0.75·LAM_PE + feature + FC-OCP Δhits.
- 계산: electrode_side v1.3.
- 트렌드: PE lean: early=0.5038 → late=0.7947 (Δ=+0.2909, +0.12810–1/100cyc) → increasing · matches_aging

**contact_stack** (`contact_stack_score`)
- 의미: ≈ contact_loss (R-centric).
- 계산: clip(contact_loss).
- 트렌드: contact_stack: early=0.8664 → late=0.9423 (Δ=+0.0759, +0.04940–1/100cyc) → increasing · matches_aging

**NE 가설** (`NE_side_score`)
- 의미: contact × Si co-sign.
- 계산: electrode_side.
- 트렌드: NE 가설: early=0.1921 → late=0.285 (Δ=+0.09298, +0.039660–1/100cyc) → increasing · matches_aging

**shared 모드** (`shared_side_score`)
- 의미: LLI/interface 등 공유 모드 평균.
- 계산: shared modes mean.
- 트렌드: shared 모드: early=0.3777 → late=0.6388 (Δ=+0.2612, +0.094980–1/100cyc) → increasing · matches_aging

**Si co-sign** (`si_cosign`)
- 의미: 저SOC hyst·Q_relax·mech/chem·CV 동시 신호.
- 계산: SI_NE_COSIGN boost.
- 트렌드: Si co-sign: early=0.2 → late=0.4 (Δ=+0.2, +0.070320–1/100cyc) → increasing · matches_aging

**dominant 마진** (`dominance_margin`)
- 의미: 1위−2위 점수차.
- 계산: top-second.
- 트렌드: dominant 마진: early=0.3462 → late=0.1471 (Δ=-0.199, -0.076450–1/100cyc) → decreasing · context

**FC-OCP 피크 hits** (`pe_peak_hits`)
- 의미: 충전 dQ/dV ↔ 합성 FC-OCP 매칭 수.
- 계산: unique nearest ±60mV.
- 트렌드: FC-OCP 피크 hits: early=0 → late=0 (Δ=+0, -0.2314count/100cyc) → decreasing · context

**FC-OCP hits Δ** (`pe_peak_hits_delta`)
- 의미: 기준 대비 hits 증가.
- 계산: hits-hits0.
- 트렌드: FC-OCP hits Δ: early=0 → late=0 (Δ=+0, +0count/100cyc) → flat · stable

**FC-OCP hits (alias)** (`fc_ocp_hits`)
- 의미: pe_peak_hits 별칭.
- 계산: same as pe_peak_hits.
- 트렌드: FC-OCP hits (alias): early=0 → late=0 (Δ=+0, -0.2314count/100cyc) → decreasing · context

**FC-OCP hits Δ (alias)** (`fc_ocp_hits_delta`)
- 의미: pe_peak_hits_delta 별칭.
- 계산: same as pe_peak_hits_delta.
- 트렌드: FC-OCP hits Δ (alias): early=0 → late=0 (Δ=+0, +0count/100cyc) → flat · stable

**전극진단 신뢰도** (`electrode_confidence`)
- 의미: coverage·분리·OCP 가용성.
- 계산: 0.35cov+0.35sep+0.30ocp.
- 트렌드: 전극진단 신뢰도: early=0.8687 → late=0.82 (Δ=-0.04879, -0.0020910–1/100cyc) → flat · context
