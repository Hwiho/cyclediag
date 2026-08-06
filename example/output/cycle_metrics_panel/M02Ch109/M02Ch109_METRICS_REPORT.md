# 사이클별 지표 패널 — M02Ch109

## 트렌드 요약 — M02Ch109

- 유효 지표: 358개 · aging 방향 일치 50 · 반대 7

### 하락 트렌드 (상위)
- 국소 CE(20): early=508.2 → late=307.6 (Δ=-200.6, -64.13%/100cyc) → decreasing · matches_aging
- 충전 에너지: early=245.5 → late=192.6 (Δ=-52.85, -19.1Wh/100cyc) → decreasing · matches_aging
- 방전후 휴지 완화 τ: early=363.6 → late=331 (Δ=-32.59, -18.21s/100cyc) → decreasing · context
- 방전후 완화 τ Δvs기준: early=2.451 → late=-30.14 (Δ=-32.59, -18.21s/100cyc) → decreasing · context
- 방전 에너지: early=229.6 → late=196 (Δ=-33.62, -13.72Wh/100cyc) → decreasing · matches_aging

### 상승 트렌드 (상위)
- 충전 dQ/dV 피크1 높이: early=82.63 → late=79.14 (Δ=-3.494, +2873Ah/V/100cyc) → increasing · context
- 충전 dV/dQ 피크2 Q: early=54.66 → late=54.66 (Δ=+0, +438.5Ah/100cyc) → increasing · context
- 충전 dQ/dV 피크4 높이: early=96.66 → late=96.66 (Δ=+0, +78.37Ah/V/100cyc) → increasing · context
- CV 시간: early=0 → late=0 (Δ=+0, +64.76s/100cyc) → increasing · matches_aging
- fit 잔차 max: early=32.5 → late=206 (Δ=+173.5, +63.06mV/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- 쿨롱 비효율: early=-3.121 → late=-18.04 (Δ=-14.92, -4.96%/100cyc) → decreasing · opposite_aging
- CI /시간: early=-0.6188 → late=-3.64 (Δ=-3.021, -1.001%/h/100cyc) → decreasing · opposite_aging
- 에너지 손실: early=16.35 → late=-3.434 (Δ=-19.78, -5.333Wh/100cyc) → decreasing · opposite_aging
- dSoHQ/dN: early=-0.1803 → late=-0.02412 (Δ=+0.1562, +0.1703%/cyc/100cyc) → increasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.

## 지표 카탈로그 + 트렌드

### 프로토콜 · 온도

**충전 전압 컷오프** (`chg_V_cutoff`)
- 의미: 충전 종료 전압.
- 계산: charge V max/cutoff.
- 트렌드: 충전 전압 컷오프: early=4.2 → late=4.2 (Δ=+6.67e-05, +2.691e-05V/100cyc) → flat · context

**방전 전압 컷오프** (`dchg_V_cutoff`)
- 의미: 방전 종료 전압.
- 계산: discharge V min/cutoff.
- 트렌드: 방전 전압 컷오프: early=2.5 → late=2.5 (Δ=+5e-06, -1.773e-07V/100cyc) → flat · context

**충전 전류 컷오프** (`chg_I_cutoff`)
- 의미: CV 종료 전류.
- 계산: charge I cutoff.
- 트렌드: 충전 전류 컷오프: early=33.45 → late=33.6 (Δ=+0.151, -1.312A/100cyc) → flat · context

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
- 트렌드: 사이클 소요시간: early=5.048 → late=4.957 (Δ=-0.09135, -0.1445h/100cyc) → flat · context

### 용량 · 효율 · CV

**용량 유지율** (`SoHQ`)
- 의미: 기준 대비 방전용량.
- 계산: Q_dchg/Q_base*100.
- 트렌드: 용량 유지율: early=97.56 → late=86.38 (Δ=-11.18, -4.486%/100cyc) → flat · stable

**방전 용량** (`dchgCapa`)
- 의미: 사이클 방전용량.
- 계산: max discharge capacity.
- 트렌드: 방전 용량: early=67.46 → late=59.73 (Δ=-7.733, -3.102Ah/100cyc) → flat · stable

**충전 용량** (`chgCapa`)
- 의미: 사이클 충전용량.
- 계산: max charge capacity.
- 트렌드: 충전 용량: early=65.31 → late=50.6 (Δ=-14.71, -5.416Ah/100cyc) → decreasing · matches_aging

**CC 충전용량** (`chgCCcapa`)
- 의미: CC 구간 용량.
- 계산: CC capacity.
- 트렌드: CC 충전용량: early=65 → late=50.34 (Δ=-14.66, -5.825Ah/100cyc) → decreasing · matches_aging

**CV 충전용량** (`chgCVcapa`)
- 의미: CV 구간 용량.
- 계산: signal/column CV Ah.
- 트렌드: CV 충전용량: early=0 → late=0 (Δ=+0, +0.4007Ah/100cyc) → increasing · matches_aging

**CC 용량비** (`chgCapa_CCratio`)
- 의미: CC/(CC+CV).
- 계산: chgCCcapa/chgCapa.
- 트렌드: CC 용량비: early=100 → late=100 (Δ=+0, -0.70791/100cyc) → flat · stable

**CC비 (정규화)** (`chgCapa_CCratio_norm`)
- 의미: 기준 정규화 CC비.
- 계산: CCratio / baseline.
- 트렌드: CC비 (정규화): early=94.84 → late=94.84 (Δ=+0, -4.6091/100cyc) → flat · stable

**CC비 Δ** (`delta_chgCapa_CCratio`)
- 의미: 기준 대비 CC비 변화.
- 계산: delta abs.
- 트렌드: CC비 Δ: early=0 → late=0 (Δ=+0, -0.70791/100cyc) → decreasing · matches_aging

**CV 시간** (`chgCVtime`)
- 의미: CV 지속시간.
- 계산: CV step duration.
- 트렌드: CV 시간: early=0 → late=0 (Δ=+0, +64.76s/100cyc) → increasing · matches_aging

**CV 시정수** (`tau_CV`)
- 의미: CV 전류 감쇠 τ.
- 계산: I(t) exp fit.
- 트렌드: CV 시정수: early=969.7 → late=969.7 (Δ=+0, n/a) → flat · stable

**CV Q @Tref** (`Q_CV_at_Tref`)
- 의미: 온도 보정 CV 용량.
- 계산: CV Q at ref T.
- 트렌드: CV Q @Tref: early=4.293 → late=4.293 (Δ=+0, n/a) → flat · context

**쿨롱 효율** (`CE`)
- 의미: Q_dchg/Q_chg.
- 계산: dchg/chg*100.
- 트렌드: 쿨롱 효율: early=103.1 → late=118 (Δ=+14.92, +4.96%/100cyc) → flat · stable

**가역 CE** (`CE_rev`)
- 의미: 가역 쿨롱 효율 proxy.
- 계산: rev CE extract.
- 트렌드: 가역 CE: early=96.58 → late=84.72 (Δ=-11.86, -3.769%/100cyc) → flat · stable

**국소 CE(20)** (`CE_local_20`)
- 의미: 최근 20사이클 국소 CE.
- 계산: rolling CE.
- 트렌드: 국소 CE(20): early=508.2 → late=307.6 (Δ=-200.6, -64.13%/100cyc) → decreasing · matches_aging

**쿨롱 비효율** (`CI`)
- 의미: 100−CE.
- 계산: 100-CE.
- 트렌드: 쿨롱 비효율: early=-3.121 → late=-18.04 (Δ=-14.92, -4.96%/100cyc) → decreasing · opposite_aging

**CI /시간** (`CI_per_hour`)
- 의미: 시간당 쿨롱 손실.
- 계산: CI / cycle_duration_h.
- 트렌드: CI /시간: early=-0.6188 → late=-3.64 (Δ=-3.021, -1.001%/h/100cyc) → decreasing · opposite_aging

**전압 효율** (`VE`)
- 의미: 에너지 전압효율.
- 계산: E_dchg/E_chg.
- 트렌드: 전압 효율: early=0.906 → late=0.8618 (Δ=-0.04423, -0.019681/100cyc) → flat · stable

**에너지 효율** (`EE`)
- 의미: 충방전 에너지비.
- 계산: E_dchg/E_chg.
- 트렌드: 에너지 효율: early=0.9334 → late=1.018 (Δ=+0.08444, +0.022261/100cyc) → flat · stable

**충전 에너지** (`chg_E`)
- 의미: 충전 Wh.
- 계산: ∫VI dt charge.
- 트렌드: 충전 에너지: early=245.5 → late=192.6 (Δ=-52.85, -19.1Wh/100cyc) → decreasing · matches_aging

**방전 에너지** (`dchg_E`)
- 의미: 방전 Wh.
- 계산: ∫VI dt discharge.
- 트렌드: 방전 에너지: early=229.6 → late=196 (Δ=-33.62, -13.72Wh/100cyc) → decreasing · matches_aging

**에너지 손실** (`dE`)
- 의미: 충전−방전 에너지.
- 계산: chg_E-dchg_E.
- 트렌드: 에너지 손실: early=16.35 → late=-3.434 (Δ=-19.78, -5.333Wh/100cyc) → decreasing · opposite_aging

**완화 용량** (`Q_relax`)
- 의미: 휴지 회복 용량.
- 계산: DCIR block ΔQ.
- 트렌드: 완화 용량: early=-0.318 → late=0.067 (Δ=+0.385, +0.199Ah/100cyc) → increasing · context

**완화 용량 %** (`Q_relax_pct`)
- 의미: 회복 용량 분율.
- 계산: Q_relax/Q*100.
- 트렌드: 완화 용량 %: early=-0.4599 → late=0.1079 (Δ=+0.5678, +0.2924%/100cyc) → increasing · matches_aging

**dSoHQ/dN** (`dSoHQ_dN`)
- 의미: 용량 유지율 순간 기울기.
- 계산: diff SoHQ.
- 트렌드: dSoHQ/dN: early=-0.1803 → late=-0.02412 (Δ=+0.1562, +0.1703%/cyc/100cyc) → increasing · opposite_aging

**d2SoHQ** (`d2SoHQ`)
- 의미: SoHQ 2차 미분.
- 계산: diff dSoHQ.
- 트렌드: d2SoHQ: early=-0.001093 → late=-0.06812 (Δ=-0.06703, -0.04653%/cyc2/100cyc) → decreasing · context

### 휴지 전압 (충전/방전 후)

**충전후 휴지 초기 V** (`EoC_restV_init`)
- 의미: 충전후 rest 시작 전압.
- 계산: rest step 첫 샘플.
- 트렌드: 충전후 휴지 초기 V: early=4.2 → late=4.2 (Δ=+3.1e-05, +7.909e-06V/100cyc) → flat · context

**충전후 휴지 60s V** (`EoC_restV_60s`)
- 의미: 충전후 rest 60초 전압.
- 계산: rest ≈ 60 s 보간.
- 트렌드: 충전후 휴지 60s V: early=4.192 → late=4.18 (Δ=-0.01169, -0.004764V/100cyc) → flat · context

**충전후 휴지 30분 V** (`EoC_restV_30m`)
- 의미: 충전후 rest 30분 전압 (OCV에 가까움).
- 계산: rest ≈ 1800 s 보간.
- 트렌드: 충전후 휴지 30분 V: early=4.18 → late=4.147 (Δ=-0.03277, -0.01371V/100cyc) → flat · context

**충전후 휴지 종료 V** (`EoC_restV_end`)
- 의미: 충전후 rest 마지막 전압.
- 계산: rest step 끝 샘플.
- 트렌드: 충전후 휴지 종료 V: early=4.18 → late=4.147 (Δ=-0.03277, -0.01371V/100cyc) → flat · context

**충전후 휴지 완화량** (`EoC_restV_relax`)
- 의미: 충전후 end−init 완화.
- 계산: EoC_restV_end − EoC_restV_init.
- 트렌드: 충전후 휴지 완화량: early=-0.01979 → late=-0.05251 (Δ=-0.03272, -0.01372V/100cyc) → decreasing · context

**충전후 60s 완화량** (`EoC_restV_relax_60s`)
- 의미: 충전후 60s−init.
- 계산: EoC_restV_60s − EoC_restV_init.
- 트렌드: 충전후 60s 완화량: early=-0.007971 → late=-0.0196 (Δ=-0.01163, -0.004772V/100cyc) → decreasing · context

**충전후 휴지 완화 τ** (`EoC_restV_tau`)
- 의미: 충전후 rest 완화 시정수 proxy.
- 계산: rest V(t) 완화 fit τ.
- 트렌드: 충전후 휴지 완화 τ: early=536.5 → late=596.2 (Δ=+59.75, +30.27s/100cyc) → increasing · context

**충전후 60s V Δvs기준** (`delta_EoC_restV_60s`)
- 의미: 기준 사이클 대비 EoC_restV_60s 이동.
- 계산: EoC_restV_60s(cycle) − baseline.
- 트렌드: 충전후 60s V Δvs기준: early=-0.000606 → late=-0.01229 (Δ=-0.01169, -0.004764V/100cyc) → decreasing · context

**충전후 30분 V Δvs기준** (`delta_EoC_restV_30m`)
- 의미: 기준 사이클 대비 EoC_restV_30m 이동.
- 계산: EoC_restV_30m(cycle) − baseline.
- 트렌드: 충전후 30분 V Δvs기준: early=-0.001037 → late=-0.03381 (Δ=-0.03277, -0.01371V/100cyc) → decreasing · context

**충전후 종료 V Δvs기준** (`delta_EoC_restV_end`)
- 의미: 기준 사이클 대비 EoC_restV_end 이동.
- 계산: EoC_restV_end(cycle) − baseline.
- 트렌드: 충전후 종료 V Δvs기준: early=-0.001037 → late=-0.03381 (Δ=-0.03277, -0.01371V/100cyc) → decreasing · context

**충전후 완화 τ Δvs기준** (`delta_EoC_restV_tau`)
- 의미: 기준 사이클 대비 EoC_restV_tau 이동.
- 계산: EoC_restV_tau(cycle) − baseline.
- 트렌드: 충전후 완화 τ Δvs기준: early=3.14 → late=62.89 (Δ=+59.75, +30.27s/100cyc) → increasing · context

**방전후 휴지 초기 V** (`EoD_restV_init`)
- 의미: 방전후 rest 시작 전압.
- 계산: rest step 첫 샘플.
- 트렌드: 방전후 휴지 초기 V: early=2.5 → late=2.5 (Δ=+5e-06, -1.773e-07V/100cyc) → flat · context

**방전후 휴지 60s V** (`EoD_restV_60s`)
- 의미: 방전후 rest 60초 전압.
- 계산: rest ≈ 60 s 보간.
- 트렌드: 방전후 휴지 60s V: early=2.88 → late=2.947 (Δ=+0.06707, +0.0321V/100cyc) → flat · context

**방전후 휴지 30분 V** (`EoD_restV_30m`)
- 의미: 방전후 rest 30분 전압 (OCV에 가까움).
- 계산: rest ≈ 1800 s 보간.
- 트렌드: 방전후 휴지 30분 V: early=3.015 → late=3.074 (Δ=+0.05874, +0.02552V/100cyc) → flat · context

**방전후 휴지 종료 V** (`EoD_restV_end`)
- 의미: 방전후 rest 마지막 전압.
- 계산: rest step 끝 샘플.
- 트렌드: 방전후 휴지 종료 V: early=3.015 → late=3.074 (Δ=+0.05874, +0.02552V/100cyc) → flat · context

**방전후 휴지 완화량** (`EoD_restV_relax`)
- 의미: 방전후 end−init 완화.
- 계산: EoD_restV_end − EoD_restV_init.
- 트렌드: 방전후 휴지 완화량: early=0.5149 → late=0.5737 (Δ=+0.05873, +0.02552V/100cyc) → flat · context

**방전후 60s 완화량** (`EoD_restV_relax_60s`)
- 의미: 방전후 60s−init.
- 계산: EoD_restV_60s − EoD_restV_init.
- 트렌드: 방전후 60s 완화량: early=0.3803 → late=0.4474 (Δ=+0.06706, +0.0321V/100cyc) → increasing · context

**방전후 휴지 완화 τ** (`EoD_restV_tau`)
- 의미: 방전후 rest 완화 시정수 proxy.
- 계산: rest V(t) 완화 fit τ.
- 트렌드: 방전후 휴지 완화 τ: early=363.6 → late=331 (Δ=-32.59, -18.21s/100cyc) → decreasing · context

**방전후 60s V Δvs기준** (`delta_EoD_restV_60s`)
- 의미: 기준 사이클 대비 EoD_restV_60s 이동.
- 계산: EoD_restV_60s(cycle) − baseline.
- 트렌드: 방전후 60s V Δvs기준: early=0.05302 → late=0.1201 (Δ=+0.06707, +0.0321V/100cyc) → increasing · context

**방전후 30분 V Δvs기준** (`delta_EoD_restV_30m`)
- 의미: 기준 사이클 대비 EoD_restV_30m 이동.
- 계산: EoD_restV_30m(cycle) − baseline.
- 트렌드: 방전후 30분 V Δvs기준: early=0.0396 → late=0.09834 (Δ=+0.05874, +0.02552V/100cyc) → increasing · context

**방전후 종료 V Δvs기준** (`delta_EoD_restV_end`)
- 의미: 기준 사이클 대비 EoD_restV_end 이동.
- 계산: EoD_restV_end(cycle) − baseline.
- 트렌드: 방전후 종료 V Δvs기준: early=0.0396 → late=0.09834 (Δ=+0.05874, +0.02552V/100cyc) → increasing · context

**방전후 완화 τ Δvs기준** (`delta_EoD_restV_tau`)
- 의미: 기준 사이클 대비 EoD_restV_tau 이동.
- 계산: EoD_restV_tau(cycle) − baseline.
- 트렌드: 방전후 완화 τ Δvs기준: early=2.451 → late=-30.14 (Δ=-32.59, -18.21s/100cyc) → decreasing · context

### 시작 저항 (EoC/EoD)

**EoC 방전 10s DCIR** (`EoC_dchgR_10s`)
- 의미: EoC 방전 시작 후 10s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(10s)|/|I|*1000.
- 트렌드: EoC 방전 10s DCIR: early=0.1673 → late=0.2312 (Δ=+0.06388, +0.02024mΩ/100cyc) → increasing · matches_aging

**EoC 방전 10s 증가%** (`EoC_dchgR_10s_inc`)
- 의미: 기준 대비 EoC_dchgR_10s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 10s 증가%: early=26.35 → late=74.6 (Δ=+48.25, +15.29%/100cyc) → increasing · matches_aging

**EoC 방전 30s DCIR** (`EoC_dchgR_30s`)
- 의미: EoC 방전 시작 후 30s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(30s)|/|I|*1000.
- 트렌드: EoC 방전 30s DCIR: early=0.4659 → late=0.5895 (Δ=+0.1236, +0.03882mΩ/100cyc) → increasing · matches_aging

**EoC 방전 30s 증가%** (`EoC_dchgR_30s_inc`)
- 의미: 기준 대비 EoC_dchgR_30s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 30s 증가%: early=22.42 → late=54.9 (Δ=+32.48, +10.2%/100cyc) → increasing · matches_aging

**EoC 방전 60s DCIR** (`EoC_dchgR_60s`)
- 의미: EoC 방전 시작 후 60s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(60s)|/|I|*1000.
- 트렌드: EoC 방전 60s DCIR: early=0.8369 → late=0.9792 (Δ=+0.1423, +0.0423mΩ/100cyc) → flat · stable

**EoC 방전 60s 증가%** (`EoC_dchgR_60s_inc`)
- 의미: 기준 대비 EoC_dchgR_60s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 60s 증가%: early=17.35 → late=37.3 (Δ=+19.95, +5.931%/100cyc) → increasing · matches_aging

**EoD 충전 10s DCIR** (`EoD_chgR_10s`)
- 의미: EoD 충전 시작 후 10s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(10s)|/|I|*1000.
- 트렌드: EoD 충전 10s DCIR: early=0.2951 → late=0.3938 (Δ=+0.09867, +0.03026mΩ/100cyc) → increasing · matches_aging

**EoD 충전 10s 증가%** (`EoD_chgR_10s_inc`)
- 의미: 기준 대비 EoD_chgR_10s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 10s 증가%: early=-1.82 → late=31.01 (Δ=+32.83, +10.07%/100cyc) → increasing · matches_aging

**EoD 충전 30s DCIR** (`EoD_chgR_30s`)
- 의미: EoD 충전 시작 후 30s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(30s)|/|I|*1000.
- 트렌드: EoD 충전 30s DCIR: early=0.7952 → late=0.9948 (Δ=+0.1997, +0.05961mΩ/100cyc) → increasing · matches_aging

**EoD 충전 30s 증가%** (`EoD_chgR_30s_inc`)
- 의미: 기준 대비 EoD_chgR_30s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 30s 증가%: early=-7.382 → late=15.87 (Δ=+23.26, +6.943%/100cyc) → increasing · matches_aging

**EoD 충전 60s DCIR** (`EoD_chgR_60s`)
- 의미: EoD 충전 시작 후 60s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(60s)|/|I|*1000.
- 트렌드: EoD 충전 60s DCIR: early=1.425 → late=1.675 (Δ=+0.2503, +0.06577mΩ/100cyc) → flat · stable

**EoD 충전 60s 증가%** (`EoD_chgR_60s_inc`)
- 의미: 기준 대비 EoD_chgR_60s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 60s 증가%: early=-9.217 → late=6.729 (Δ=+15.95, +4.19%/100cyc) → increasing · matches_aging

**EoC R10/R60** (`EoC_dchgR_10_60_ratio`)
- 의미: 10s/60s 비. 초기 응답 비중.
- 계산: EoC_dchgR_10s / EoC_dchgR_60s.
- 트렌드: EoC R10/R60: early=0.2004 → late=0.2354 (Δ=+0.03505, +0.012021/100cyc) → increasing · context

**EoD R10/R60** (`EoD_chgR_10_60_ratio`)
- 의미: 10s/60s 비.
- 계산: EoD_chgR_10s / EoD_chgR_60s.
- 트렌드: EoD R10/R60: early=0.2071 → late=0.2315 (Δ=+0.02437, +0.0099431/100cyc) → flat · context

**EoC R10s @25C** (`EoC_dchgR_10s_T25`)
- 의미: 온도 보정 10s DCIR.
- 계산: Arrhenius-ish correct_r_to_25c.
- 트렌드: EoC R10s @25C: early=0.07994 → late=0.1105 (Δ=+0.03052, +0.009672mΩ/100cyc) → increasing · matches_aging

**EoD R10s @25C** (`EoD_chgR_10s_T25`)
- 의미: 온도 보정 10s DCIR.
- 계산: correct_r_to_25c.
- 트렌드: EoD R10s @25C: early=0.141 → late=0.1882 (Δ=+0.04715, +0.01446mΩ/100cyc) → increasing · matches_aging

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
- 트렌드: RΩ (SOC50): early=1.107 → late=2.765 (Δ=+1.658, +0.7947mΩ/100cyc) → increasing · matches_aging

**Rct (SOC50)** (`R_ct_soc50`)
- 의미: 중간 잔차 지수항. Cdl 미분리.
- 계산: resid exp-sat fit.
- 트렌드: Rct (SOC50): early=0.7331 → late=0.9012 (Δ=+0.1681, +0.07175mΩ/100cyc) → increasing · matches_aging

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
- 트렌드: 기계/화학 비: early=1.51 → late=3.068 (Δ=+1.559, +0.78761/100cyc) → increasing · matches_aging

**RΩ 성장/100cyc** (`R_ohmic_growth_100`)
- 의미: 기준 대비 RΩ 성장률 (레벨과 별개).
- 계산: (R-R0)/((N-N0)/100).
- 트렌드: RΩ 성장/100cyc: early=1.097 → late=0.7898 (Δ=-0.3076, -0.3082mΩ/100cyc/100cyc) → decreasing · context

**Rct 성장/100cyc** (`R_ct_growth_100`)
- 의미: 기준 대비 Rct 성장률.
- 계산: (Rct-Rct0)/((N-N0)/100).
- 트렌드: Rct 성장/100cyc: early=0.06301 → late=0.08006 (Δ=+0.01705, +0.01708mΩ/100cyc/100cyc) → increasing · context

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
- 트렌드: RΩ SOC50 (ff): early=1.107 → late=2.765 (Δ=+1.658, +0.7947mΩ/100cyc) → increasing · matches_aging

**Rct SOC50 (ff)** (`R_ct_soc50_ff`)
- 의미: DCIR 블록 forward-fill 값.
- 계산: block stamp + ffill.
- 트렌드: Rct SOC50 (ff): early=0.7331 → late=0.9012 (Δ=+0.1681, +0.07175mΩ/100cyc) → increasing · matches_aging

### 곡선 형상 · 히스테리시스

**충전 평균 V** (`chg_V_avg`)
- 의미: 충전 평균 전압.
- 계산: mean V charge.
- 트렌드: 충전 평균 V: early=3.775 → late=3.826 (Δ=+0.0513, +0.02473V/100cyc) → flat · context

**방전 평균 V** (`dchg_V_avg`)
- 의미: 방전 평균 전압.
- 계산: mean V discharge.
- 트렌드: 방전 평균 V: early=3.414 → late=3.291 (Δ=-0.1227, -0.05344V/100cyc) → flat · context

**충전 평균V Δ** (`delta_chg_V_avg`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 충전 평균V Δ: early=0.03517 → late=0.08647 (Δ=+0.0513, +0.02473V/100cyc) → increasing · context

**방전 평균V Δ** (`delta_dchg_V_avg`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 방전 평균V Δ: early=-0.0255 → late=-0.1482 (Δ=-0.1227, -0.05344V/100cyc) → decreasing · context

**충전 IR drop proxy** (`chg_ir_drop_proxy`)
- 의미: 충전 초반 IR 강하 proxy.
- 계산: early ΔV.
- 트렌드: 충전 IR drop proxy: early=0.0401 → late=0.04022 (Δ=+0.0001202, +4.798e-05V/100cyc) → flat · stable

**방전 IR drop proxy** (`dchg_ir_drop_proxy`)
- 의미: 방전 초반 IR 강하 proxy.
- 계산: early ΔV.
- 트렌드: 방전 IR drop proxy: early=0.04014 → late=0.04006 (Δ=-7.85e-05, +5.587e-05V/100cyc) → flat · stable

**히스테리시스 면적** (`hyst_area`)
- 의미: 전체 충방전 히스테리시스.
- 계산: ∮(Vchg-Vdchg)dQ.
- 트렌드: 히스테리시스 면적: early=0.5534 → late=0.5995 (Δ=+0.04609, +0.02455V/100cyc) → flat · stable

**저SOC 히스테리시스** (`hyst_area_low`)
- 의미: 저SOC 밴드. Si chemo-mech.
- 계산: band integral.
- 트렌드: 저SOC 히스테리시스: early=0.08696 → late=0.0429 (Δ=-0.04406, -0.01859V/100cyc) → decreasing · opposite_aging

**중SOC 히스테리시스** (`hyst_area_mid`)
- 의미: 중SOC 밴드.
- 계산: band integral.
- 트렌드: 중SOC 히스테리시스: early=0.2494 → late=0.3197 (Δ=+0.07029, +0.03311V/100cyc) → increasing · context

**고SOC 히스테리시스** (`hyst_area_high`)
- 의미: 고SOC 밴드. PE 보조.
- 계산: band integral.
- 트렌드: 고SOC 히스테리시스: early=0.2146 → late=0.2348 (Δ=+0.02015, +0.0101V/100cyc) → flat · stable

**히스테리시스 저SOC분율** (`hyst_frac_low`)
- 의미: low/total.
- 계산: hyst_low/hyst.
- 트렌드: 히스테리시스 저SOC분율: early=0.1573 → late=0.07156 (Δ=-0.08575, -0.036781/100cyc) → decreasing · context

**히스테리시스 고SOC분율** (`hyst_frac_high`)
- 의미: high/total.
- 계산: hyst_high/hyst.
- 트렌드: 히스테리시스 고SOC분율: early=0.3876 → late=0.3916 (Δ=+0.004007, +0.00089161/100cyc) → flat · context

**최대 히스테리시스 dV** (`hyst_max_dV`)
- 의미: 최대 충방전 전압차.
- 계산: max|Vchg-Vdchg|.
- 트렌드: 최대 히스테리시스 dV: early=1.544 → late=1.604 (Δ=+0.06049, +0.02819V/100cyc) → flat · stable

**max dV 저SOC** (`hyst_max_dV_low`)
- 의미: 저SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 저SOC: early=0.7218 → late=0.4718 (Δ=-0.2499, -0.1046V/100cyc) → decreasing · opposite_aging

**max dV 중SOC** (`hyst_max_dV_mid`)
- 의미: 중SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 중SOC: early=0.9545 → late=1.087 (Δ=+0.1326, +0.06617V/100cyc) → increasing · context

**max dV 고SOC** (`hyst_max_dV_high`)
- 의미: 고SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 고SOC: early=1.544 → late=1.604 (Δ=+0.06049, +0.02819V/100cyc) → flat · context

**히스테리시스 Δ** (`delta_hyst_area`)
- 의미: 기준 대비 면적.
- 계산: delta.
- 트렌드: 히스테리시스 Δ: early=0.004869 → late=0.05096 (Δ=+0.04609, +0.02455V/100cyc) → increasing · matches_aging

**max dV Δ** (`delta_hyst_max_dV`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: max dV Δ: early=0.01068 → late=0.07117 (Δ=+0.06049, +0.02819V/100cyc) → increasing · matches_aging

**충전 플래토 V** (`chg_plateau_V`)
- 의미: 충전 플래토 전압.
- 계산: plateau detect.
- 트렌드: 충전 플래토 V: early=3.686 → late=3.773 (Δ=+0.08688, +0.007599V/100cyc) → flat · context

**충전 플래토 폭** (`chg_plateau_width`)
- 의미: 충전 플래토 Q 폭.
- 계산: plateau width.
- 트렌드: 충전 플래토 폭: early=9.855 → late=8.971 (Δ=-0.8839, +0.3163Q-units/100cyc) → flat · context

**방전 플래토 V** (`dchg_plateau_V`)
- 의미: 방전 플래토 전압.
- 계산: plateau detect.
- 트렌드: 방전 플래토 V: early=3.191 → late=3.119 (Δ=-0.07246, -0.03168V/100cyc) → flat · context

**방전 플래토 폭** (`dchg_plateau_width`)
- 의미: 방전 플래토 Q 폭.
- 계산: plateau width.
- 트렌드: 방전 플래토 폭: early=17.18 → late=14.39 (Δ=-2.783, -1.057Q-units/100cyc) → decreasing · matches_aging

**방전 플래토 ΔV** (`delta_dchg_plateau_V`)
- 의미: 기준 대비 이동.
- 계산: delta plateau V.
- 트렌드: 방전 플래토 ΔV: early=-0.0316 → late=-0.1041 (Δ=-0.07246, -0.03168V/100cyc) → decreasing · context

**방전 컷오프 마진** (`dchg_V_cutoff_margin`)
- 의미: 컷오프까지 여유.
- 계산: Vmin-margin.
- 트렌드: 방전 컷오프 마진: early=0.424 → late=0.2955 (Δ=-0.1285, -0.05657V/100cyc) → decreasing · matches_aging

**컷오프 마진 Δ** (`delta_dchg_V_cutoff_margin`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 컷오프 마진 Δ: early=-0.01781 → late=-0.1463 (Δ=-0.1285, -0.05657V/100cyc) → decreasing · matches_aging

**방전 형상 DTW** (`dchg_shape_DTW`)
- 의미: 기준 곡선 DTW 거리.
- 계산: DTW vs baseline.
- 트렌드: 방전 형상 DTW: early=0.003479 → late=0.01283 (Δ=+0.009351, +0.0042011/100cyc) → increasing · matches_aging

**DTW Δ** (`delta_dchg_shape_DTW`)
- 의미: 기준 대비 DTW.
- 계산: delta.
- 트렌드: DTW Δ: early=0.0023 → late=0.01165 (Δ=+0.009351, +0.0042011/100cyc) → increasing · matches_aging

### dQ/dV · dV/dQ 피크

**충전 dQ/dV 피크1 V** (`chg_dQdV_peak1_V`)
- 의미: 충전 IC 1번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크1 V: early=3.483 → late=3.759 (Δ=+0.2763, +0.1079V/100cyc) → flat · context

**충전 dQ/dV 피크1 높이** (`chg_dQdV_peak1`)
- 의미: 충전 IC 1번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크1 높이: early=82.63 → late=79.14 (Δ=-3.494, +2873Ah/V/100cyc) → increasing · context

**방전 dQ/dV 피크1 V** (`dchg_dQdV_peak1_V`)
- 의미: 방전 IC 1번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크1 V: early=3.171 → late=3.127 (Δ=-0.04414, -0.02336V/100cyc) → flat · context

**방전 dQ/dV 피크1 높이** (`dchg_dQdV_peak1`)
- 의미: 방전 IC 1번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크1 높이: early=-71.49 → late=-57 (Δ=+14.49, +6.091Ah/V/100cyc) → increasing · context

**충전 dV/dQ 피크1 Q** (`chg_dVdQ_peak1_Q`)
- 의미: 충전 dV/dQ 1번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 충전 dV/dQ 피크1 Q: early=53.86 → late=46.87 (Δ=-6.991, -0.7311Ah/100cyc) → flat · context

**충전 dV/dQ 피크1 높이** (`chg_dVdQ_peak1`)
- 의미: 충전 dV/dQ 1번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 충전 dV/dQ 피크1 높이: early=0.01608 → late=0.01841 (Δ=+0.002333, +0.00117V/Ah/100cyc) → increasing · context

**방전 dV/dQ 피크1 Q** (`dchg_dVdQ_peak1_Q`)
- 의미: 방전 dV/dQ 1번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 방전 dV/dQ 피크1 Q: early=9.551 → late=24.64 (Δ=+15.09, +8.437Ah/100cyc) → increasing · context

**방전 dV/dQ 피크1 높이** (`dchg_dVdQ_peak1`)
- 의미: 방전 dV/dQ 1번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 방전 dV/dQ 피크1 높이: early=-0.02255 → late=-0.02253 (Δ=+2.241e-05, +5.881e-05V/Ah/100cyc) → flat · context

**충전 dQ/dV 피크2 V** (`chg_dQdV_peak2_V`)
- 의미: 충전 IC 2번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크2 V: early=3.709 → late=3.963 (Δ=+0.2535, +0.02521V/100cyc) → flat · context

**충전 dQ/dV 피크2 높이** (`chg_dQdV_peak2`)
- 의미: 충전 IC 2번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크2 높이: early=89.39 → late=79.78 (Δ=-9.61, +5.206Ah/V/100cyc) → increasing · context

**방전 dQ/dV 피크2 V** (`dchg_dQdV_peak2_V`)
- 의미: 방전 IC 2번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크2 V: early=3.647 → late=3.634 (Δ=-0.01286, -0.00825V/100cyc) → flat · context

**방전 dQ/dV 피크2 높이** (`dchg_dQdV_peak2`)
- 의미: 방전 IC 2번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크2 높이: early=-53.72 → late=-50.65 (Δ=+3.076, +1.53Ah/V/100cyc) → flat · context

**충전 dV/dQ 피크2 Q** (`chg_dVdQ_peak2_Q`)
- 의미: 충전 dV/dQ 2번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 충전 dV/dQ 피크2 Q: early=54.66 → late=54.66 (Δ=+0, +438.5Ah/100cyc) → increasing · context

**충전 dV/dQ 피크2 높이** (`chg_dVdQ_peak2`)
- 의미: 충전 dV/dQ 2번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 충전 dV/dQ 피크2 높이: early=0.016 → late=0.016 (Δ=+0, -0.1718V/Ah/100cyc) → decreasing · context

**방전 dV/dQ 피크2 Q** (`dchg_dVdQ_peak2_Q`)
- 의미: 방전 dV/dQ 2번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 방전 dV/dQ 피크2 Q: early=30.31 → late=27.62 (Δ=-2.687, -2.449Ah/100cyc) → decreasing · context

**방전 dV/dQ 피크2 높이** (`dchg_dVdQ_peak2`)
- 의미: 방전 dV/dQ 2번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 방전 dV/dQ 피크2 높이: early=-0.02128 → late=-0.0221 (Δ=-0.0008211, -0.0006283V/Ah/100cyc) → flat · context

**충전 dQ/dV 피크3 V** (`chg_dQdV_peak3_V`)
- 의미: 충전 IC 3번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크3 V: early=3.955 → late=3.968 (Δ=+0.01332, +0.03493V/100cyc) → flat · context

**충전 dQ/dV 피크3 높이** (`chg_dQdV_peak3`)
- 의미: 충전 IC 3번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크3 높이: early=80.43 → late=76.81 (Δ=-3.614, +11.25Ah/V/100cyc) → increasing · context

**방전 dQ/dV 피크3 V** (`dchg_dQdV_peak3_V`)
- 의미: 방전 IC 3번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크3 V: early=3.979 → late=3.85 (Δ=-0.1294, -0.0689V/100cyc) → flat · context

**방전 dQ/dV 피크3 높이** (`dchg_dQdV_peak3`)
- 의미: 방전 IC 3번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크3 높이: early=-60.3 → late=-45.42 (Δ=+14.88, +7.976Ah/V/100cyc) → increasing · context

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
- 트렌드: 충전 dQ/dV 피크4 V: early=4.17 → late=4.17 (Δ=+0, +0.02558V/100cyc) → flat · context

**충전 dQ/dV 피크4 높이** (`chg_dQdV_peak4`)
- 의미: 충전 IC 4번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크4 높이: early=96.66 → late=96.66 (Δ=+0, +78.37Ah/V/100cyc) → increasing · context

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
- 트렌드: 충전 피크1 ΔV: early=0.07889 → late=0.3552 (Δ=+0.2763, +0.1079V/100cyc) → increasing · context

**방전 피크1 ΔV** (`delta_dchg_dQdV_peak1_V`)
- 의미: 기준 대비 방전 dQ/dV 피크1 이동.
- 계산: delta_dchg_dQdV_peak1_V
- 트렌드: 방전 피크1 ΔV: early=-0.03964 → late=-0.08378 (Δ=-0.04414, -0.02336V/100cyc) → decreasing · context

**방전 dV/dQ @SOC0** (`dchg_dVdQ_SOC0`)
- 의미: 저SOC cliff dV/dQ.
- 계산: dchg_dVdQ_SOC0
- 트렌드: 방전 dV/dQ @SOC0: early=0.1088 → late=0.0715 (Δ=-0.0373, -0.01789V/Ah/100cyc) → decreasing · context

**방전 dV/dQ @SOC5** (`dchg_dVdQ_SOC5`)
- 의미: SOC≈5% dV/dQ.
- 계산: dchg_dVdQ_SOC5
- 트렌드: 방전 dV/dQ @SOC5: early=0.04927 → late=0.04319 (Δ=-0.006084, -0.002711V/Ah/100cyc) → decreasing · context

**방전 dV/dQ @SOC10** (`dchg_dVdQ_SOC10`)
- 의미: SOC≈10% dV/dQ.
- 계산: dchg_dVdQ_SOC10
- 트렌드: 방전 dV/dQ @SOC10: early=0.02923 → late=0.03061 (Δ=+0.001384, +0.000375V/Ah/100cyc) → flat · context

**방전 dV/dQ @mid** (`dchg_dVdQ_SOCmid`)
- 의미: 중SOC dV/dQ.
- 계산: dchg_dVdQ_SOCmid
- 트렌드: 방전 dV/dQ @mid: early=0.01969 → late=0.02074 (Δ=+0.001049, +0.0004172V/Ah/100cyc) → flat · context

**방전 cliff Q** (`dchg_dVdQ_SOC0_Q`)
- 의미: SOC0 dV/dQ 위치 Q.
- 계산: dchg_dVdQ_SOC0_Q
- 트렌드: 방전 cliff Q: early=67.25 → late=59.54 (Δ=-7.706, -3.09Ah/100cyc) → flat · context

**방전 cliff 폭** (`dchg_dVdQ_SOC0_cliff_width`)
- 의미: 저SOC cliff 폭.
- 계산: dchg_dVdQ_SOC0_cliff_width
- 트렌드: 방전 cliff 폭: early=4.986 → late=3.58 (Δ=-1.407, -0.5884Ah/100cyc) → decreasing · context

**cliff/mid 비** (`dchg_dVdQ_SOC0_to_mid_ratio`)
- 의미: SOC0/mid dV/dQ 비.
- 계산: dchg_dVdQ_SOC0_to_mid_ratio
- 트렌드: cliff/mid 비: early=5.537 → late=3.448 (Δ=-2.089, -0.97631/100cyc) → decreasing · context

**충전 dV/dQ @100** (`chg_dVdQ_SOC100`)
- 의미: 만충 부근 dV/dQ.
- 계산: chg_dVdQ_SOC100
- 트렌드: 충전 dV/dQ @100: early=0.01031 → late=0.00885 (Δ=-0.001455, +0.0002154V/Ah/100cyc) → flat · context

**dV/dQ SOC0 Δ** (`delta_dchg_dVdQ_SOC0`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0
- 트렌드: dV/dQ SOC0 Δ: early=0.0009219 → late=-0.03638 (Δ=-0.0373, -0.01789V/Ah/100cyc) → decreasing · context

**dV/dQ SOC5 Δ** (`delta_dchg_dVdQ_SOC5`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC5
- 트렌드: dV/dQ SOC5 Δ: early=-0.001912 → late=-0.007996 (Δ=-0.006084, -0.002711V/Ah/100cyc) → decreasing · context

**dV/dQ SOC10 Δ** (`delta_dchg_dVdQ_SOC10`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC10
- 트렌드: dV/dQ SOC10 Δ: early=-0.001814 → late=-0.0004295 (Δ=+0.001384, +0.000375V/Ah/100cyc) → increasing · context

**dV/dQ mid Δ** (`delta_dchg_dVdQ_SOCmid`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOCmid
- 트렌드: dV/dQ mid Δ: early=0.0003679 → late=0.001417 (Δ=+0.001049, +0.0004172V/Ah/100cyc) → increasing · context

**dV/dQ 100 Δ** (`delta_chg_dVdQ_SOC100`)
- 의미: 기준 대비.
- 계산: delta_chg_dVdQ_SOC100
- 트렌드: dV/dQ 100 Δ: early=-0.004458 → late=-0.005913 (Δ=-0.001455, +0.0002154V/Ah/100cyc) → flat · context

**cliff 폭 Δ** (`delta_dchg_dVdQ_SOC0_cliff_width`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0_cliff_width
- 트렌드: cliff 폭 Δ: early=-0.5324 → late=-1.939 (Δ=-1.407, -0.5884Ah/100cyc) → decreasing · context

**cliff/mid Δ** (`delta_dchg_dVdQ_SOC0_to_mid_ratio`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0_to_mid_ratio
- 트렌드: cliff/mid Δ: early=-0.0464 → late=-2.135 (Δ=-2.089, -0.97631/100cyc) → decreasing · context

**충전 IC 면적합** (`chg_dQdV_area_sum`)
- 의미: dQ/dV 피크 면적 합.
- 계산: chg_dQdV_area_sum
- 트렌드: 충전 IC 면적합: early=65 → late=50.34 (Δ=-14.66, -5.373Ah/100cyc) → decreasing · context

**방전 IC 면적합** (`dchg_dQdV_area_sum`)
- 의미: dQ/dV 피크 면적 합.
- 계산: dchg_dQdV_area_sum
- 트렌드: 방전 IC 면적합: early=67.25 → late=59.54 (Δ=-7.706, -3.09Ah/100cyc) → flat · context

### 수송 · rate · η

**RCF** (`RCF`)
- 의미: Q_0.5C / Q_C/3.
- 계산: routine/RPT Q.
- 트렌드: RCF: early=0.9756 → late=0.9618 (Δ=-0.01379, -0.00091791/100cyc) → flat · stable

**RCF 기울기/100** (`RCF_slope_100`)
- 의미: RCF 변화율.
- 계산: first-last slope.
- 트렌드: RCF 기울기/100: early=-0.01381 → late=-0.01381 (Δ=+0, +1.76e-181/100cyc/100cyc) → flat · stable

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
- 트렌드: I∞ 정규화: early=0.1575 → late=0.1575 (Δ=+0, n/a) → flat · context

**펄스 1s 샘플수** (`pulse_sample_count_1s`)
- 의미: t≤1s 샘플 수.
- 계산: quality.
- 트렌드: 펄스 1s 샘플수: early=5 → late=7 (Δ=+2, +0.7642count/100cyc) → increasing · context

**펄스 전류 안정도** (`pulse_current_stability`)
- 의미: std(I)/|I|.
- 계산: quality.
- 트렌드: 펄스 전류 안정도: early=0.02691 → late=0.04374 (Δ=+0.01683, +0.008531/100cyc) → increasing · opposite_aging

**rest 충분성** (`rest_sufficiency`)
- 의미: 휴지 길이/품질.
- 계산: quality.
- 트렌드: rest 충분성: early=3 → late=3 (Δ=+0, +1.547e-151/100cyc) → flat · context

**레그 완전성** (`leg_completeness`)
- 의미: 충방전 레그 완전성.
- 계산: quality.
- 트렌드: 레그 완전성: early=0.9997 → late=0.9998 (Δ=+4.688e-05, -0.018271/100cyc) → flat · context

**완화 완성도 max** (`relax_completeness_max`)
- 의미: SOC별 최대 완화 완성도.
- 계산: max.
- 트렌드: 

**샘플/mV** (`samples_per_mV`)
- 의미: 전압 해상도 샘플밀도.
- 계산: dqdv quality.
- 트렌드: 샘플/mV: early=0.3601 → late=0.3483 (Δ=-0.01178, -0.010411/mV/100cyc) → flat · context

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
- 트렌드: LAM 곡선 proxy: early=-2.01 → late=-12.04 (Δ=-10.03, -4.231%/100cyc) → decreasing · context

**LLI 곡선 proxy** (`LLI_curve_proxy`)
- 의미: Q 오프셋 proxy (절대 LLI% 아님).
- 계산: offset/Qmax*100.
- 트렌드: LLI 곡선 proxy: early=-0.08575 → late=1.893 (Δ=+1.979, +0.601%/100cyc) → increasing · context

**R 곡선 proxy** (`R_curve_proxy`)
- 의미: 곡선 fit dR proxy.
- 계산: fit_dR.
- 트렌드: R 곡선 proxy: early=0.9099 → late=4.215 (Δ=+3.305, +1.485mΩ/100cyc) → increasing · matches_aging

**방전 fit scale** (`dchg_fit_scale`)
- 의미: 기준 대비 scale s.
- 계산: 3-param fit.
- 트렌드: 방전 fit scale: early=1.02 → late=1.12 (Δ=+0.1003, +0.042311/100cyc) → flat · stable

**방전 fit offset** (`dchg_fit_offset`)
- 의미: Q 오프셋.
- 계산: 3-param fit.
- 트렌드: 방전 fit offset: early=-0.0593 → late=1.309 (Δ=+1.368, +0.4156Ah/100cyc) → increasing · context

**방전 fit dR** (`dchg_fit_dR`)
- 의미: 저항 항.
- 계산: 3-param fit.
- 트렌드: 방전 fit dR: early=0.9099 → late=4.215 (Δ=+3.305, +1.485mΩ/100cyc) → increasing · matches_aging

**fit 잔차 RMS** (`dchg_fit_residual_rms`)
- 의미: 잔차 rms.
- 계산: RMS(resid).
- 트렌드: fit 잔차 RMS: early=4.166 → late=19.92 (Δ=+15.76, +6.287mV/100cyc) → increasing · matches_aging

**fit 잔차 max** (`dchg_fit_residual_max`)
- 의미: 잔차 최대.
- 계산: max|resid|.
- 트렌드: fit 잔차 max: early=32.5 → late=206 (Δ=+173.5, +63.06mV/100cyc) → increasing · matches_aging

**잔차 argmax SOC** (`dchg_fit_residual_argmax_SOC`)
- 의미: 잔차 최대 SOC (방전 DOD→SOC 변환).
- 계산: argmax residual.
- 트렌드: 잔차 argmax SOC: early=100 → late=100 (Δ=+0, +0.01772%/100cyc) → flat · context

**fit R2** (`dchg_fit_r2`)
- 의미: 곡선 fit 품질.
- 계산: r2.
- 트렌드: fit R2: early=0.9999 → late=0.9977 (Δ=-0.002216, -0.0009451/100cyc) → flat · context

**fit corr(s,o)** (`dchg_fit_corr_s_o`)
- 의미: scale-offset 상관 (축퇴 지표).
- 계산: corr.
- 트렌드: fit corr(s,o): early=0.5274 → late=0.7694 (Δ=+0.242, +0.086511/100cyc) → increasing · context

**잔차 argmax DOD** (`dchg_fit_residual_argmax_DOD`)
- 의미: 잔차 최대 DOD.
- 계산: argmax DOD.
- 트렌드: 잔차 argmax DOD: early=0 → late=0 (Δ=+0, -0.01772%/100cyc) → decreasing · context

**ΔQ(V) min** (`dQV_min`)
- 의미: 전압빈 ΔQ 최소.
- 계산: histogram.
- 트렌드: ΔQ(V) min: early=-3.291 → late=-15.81 (Δ=-12.52, -5.29Ah/100cyc) → decreasing · context

**ΔQ(V) mean** (`dQV_mean`)
- 의미: ΔQ 평균.
- 계산: mean.
- 트렌드: ΔQ(V) mean: early=-2.444 → late=-12.23 (Δ=-9.785, -4.138Ah/100cyc) → decreasing · context

**ΔQ(V) var** (`dQV_var`)
- 의미: ΔQ 분산.
- 계산: var.
- 트렌드: ΔQ(V) var: early=0.224 → late=3.968 (Δ=+3.744, +1.638Ah2/100cyc) → increasing · matches_aging

**ΔQ(V) log-var** (`dQV_log_var`)
- 의미: log10 분산.
- 계산: log10(var).
- 트렌드: ΔQ(V) log-var: early=-0.6498 → late=0.5986 (Δ=+1.248, +0.48881/100cyc) → increasing · matches_aging

**ΔQ(V) skew** (`dQV_skew`)
- 의미: 왜도.
- 계산: skew.
- 트렌드: ΔQ(V) skew: early=-0.4386 → late=-0.7259 (Δ=-0.2873, -0.088181/100cyc) → decreasing · context

**ΔQ(V) kurtosis** (`dQV_kurtosis`)
- 의미: 첨도.
- 계산: kurtosis.
- 트렌드: ΔQ(V) kurtosis: early=-1.138 → late=-0.9904 (Δ=+0.1475, +0.073191/100cyc) → increasing · context

**ΔQ argmin V** (`dQV_argmin_V`)
- 의미: ΔQ 최소 전압.
- 계산: argmin.
- 트렌드: ΔQ argmin V: early=3.157 → late=3.094 (Δ=-0.06254, -0.02518V/100cyc) → flat · context

**dQ/dV SNR** (`dqdv_snr`)
- 의미: IC 신호대잡음.
- 계산: snr estimate.
- 트렌드: dQ/dV SNR: early=84.45 → late=66.15 (Δ=-18.3, -5.3481/100cyc) → decreasing · context

**데이터 품질점수** (`quality_score`)
- 의미: 추출 품질 종합.
- 계산: quality gates.
- 트렌드: 데이터 품질점수: early=1 → late=1 (Δ=+0, -0.0058960–1/100cyc) → flat · context

**전압 노이즈 σ** (`v_noise_sigma`)
- 의미: 전압 노이즈 추정.
- 계산: noise sigma.
- 트렌드: 전압 노이즈 σ: early=0.02013 → late=0.02569 (Δ=+0.005566, +0.001643V/100cyc) → increasing · context

**ΔQ(V) 기준 사이클** (`dQV_ref_cycle`)
- 의미: ΔQ 비교 기준 사이클.
- 계산: ref cycle id.
- 트렌드: ΔQ(V) 기준 사이클: early=3 → late=3 (Δ=+0, -1.223e-15cyc/100cyc) → flat · context

**온도 가용** (`temperature_available`)
- 의미: Temp 컬럼 유효 여부.
- 계산: bool→float.
- 트렌드: 온도 가용: early=0 → late=0 (Δ=+0, +00/1/100cyc) → flat · context

**Q_relax 유의** (`Q_relax_significant`)
- 의미: 완화 용량 유의 플래그.
- 계산: threshold flag.
- 트렌드: Q_relax 유의: early=1 → late=1 (Δ=+0, -0.1740/1/100cyc) → decreasing · context

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
- 트렌드: fade b 표준오차: early=0.02841 → late=0.02841 (Δ=+0, +1.319e-171/100cyc) → flat · context

**ΔQ 유효 V범위** (`dQV_valid_V_range`)
- 의미: ΔQ 집계 전압폭.
- 계산: Vmax-Vmin used.
- 트렌드: ΔQ 유효 V범위: early=0.7713 → late=0.7713 (Δ=+0, -8.591e-17V/100cyc) → flat · context

### fade · knee

**fade 지수 b** (`fade_exponent_b`)
- 의미: SoHQ power-law 지수.
- 계산: SoHQ fit.
- 트렌드: fade 지수 b: early=0.6819 → late=0.6819 (Δ=+0, +1.845e-161/100cyc) → flat · context

**fade 지수 a** (`fade_exponent_a`)
- 의미: power-law 계수.
- 계산: SoHQ fit.
- 트렌드: fade 지수 a: early=0.00281 → late=0.00281 (Δ=+0, +1.006e-181/100cyc) → flat · context

**fade fit R2** (`fade_fit_r2`)
- 의미: fade 적합도.
- 계산: r2.
- 트렌드: fade fit R2: early=0.9826 → late=0.9826 (Δ=+0, +3.805e-161/100cyc) → flat · context

**fade SoHQ0** (`fade_sohq0`)
- 의미: fit 초기 SoHQ.
- 계산: intercept.
- 트렌드: fade SoHQ0: early=97.8 → late=97.8 (Δ=+0, +3.2e-14%/100cyc) → flat · context

**knee 사이클** (`knee_cycle_bw`)
- 의미: bilinear knee 위치.
- 계산: broken-stick SoHQ.
- 트렌드: knee 사이클: early=40 → late=40 (Δ=+0, +1.837e-14cyc/100cyc) → flat · context

**knee 심각도** (`knee_severity`)
- 의미: 전후 기울기 차이.
- 계산: slope_after-before.
- 트렌드: knee 심각도: early=0 → late=0 (Δ=+0, +01/100cyc) → flat · stable

**knee 전 기울기** (`knee_slope_before`)
- 의미: knee 이전 fade 기울기.
- 계산: bilinear.
- 트렌드: knee 전 기울기: early=-0.1283 → late=-0.1283 (Δ=+0, -4.12e-17%/cyc/100cyc) → flat · stable

**knee 후 기울기** (`knee_slope_after`)
- 의미: knee 이후 fade 기울기.
- 계산: bilinear.
- 트렌드: knee 후 기울기: early=-0.03629 → late=-0.03629 (Δ=+0, -1.572e-17%/cyc/100cyc) → flat · stable

**knee fit R2** (`knee_fit_r2`)
- 의미: knee 적합도.
- 계산: r2.
- 트렌드: knee fit R2: early=0.9986 → late=0.9986 (Δ=+0, +2.221e-161/100cyc) → flat · context

### 열화 패턴 점수

**PE activity 패턴** (`LAM_PE_pattern_score`)
- 의미: NCM activity/isolation (절대 LAM% 아님).
- 계산: mode_weights LAM_PE.
- 트렌드: PE activity 패턴: early=0.5637 → late=0.9611 (Δ=+0.3974, +0.15350–1/100cyc) → increasing · matches_aging

**NE 패턴 점수** (`LAM_NE_pattern_score`)
- 의미: NE 관련 패턴 (Si-on-Gr에선 보조).
- 계산: mode_weights LAM_NE.
- 트렌드: 

**contact_loss** (`contact_loss_score`)
- 의미: 옴/스택/접촉 증거 합.
- 계산: RΩ growth 등 가중합.
- 트렌드: contact_loss: early=0.7834 → late=0.9914 (Δ=+0.208, +0.073020–1/100cyc) → increasing · matches_aging

**LLI 패턴** (`LLI_pattern_score`)
- 의미: CE·slippage·offset 기반.
- 계산: mode_weights LLI.
- 트렌드: LLI 패턴: early=0.2637 → late=0.5959 (Δ=+0.3322, +0.12970–1/100cyc) → increasing · matches_aging

**계면 R 패턴** (`interface_R_score`)
- 의미: Rct·VE 등 계면저항.
- 계산: mode_weights interface_R.
- 트렌드: 계면 R 패턴: early=0.4033 → late=0.8515 (Δ=+0.4483, +0.17430–1/100cyc) → increasing · matches_aging

**고체확산 패턴** (`solid_diffusion_score`)
- 의미: A_diff·PER·RCF.
- 계산: mode_weights solid_diffusion.
- 트렌드: 고체확산 패턴: early=0.4528 → late=0.6434 (Δ=+0.1906, +0.036250–1/100cyc) → increasing · matches_aging

**SE 분해 패턴** (`SE_decomposition_score`)
- 의미: CE↓·Rct↑ 등 SE 분해 가설.
- 계산: mode_weights SE_decomposition.
- 트렌드: SE 분해 패턴: early=0.1068 → late=0.3554 (Δ=+0.2486, +0.10710–1/100cyc) → increasing · matches_aging

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
- 트렌드: contact_loss 신뢰도: early=0.52 → late=0.448 (Δ=-0.072, +0.0038780–1/100cyc) → flat · context

**LAM_PE 신뢰도** (`LAM_PE_confidence`)
- 의미: 패턴 신뢰도.
- 계산: confidence.
- 트렌드: LAM_PE 신뢰도: early=0.751 → late=0.616 (Δ=-0.135, -0.051760–1/100cyc) → decreasing · context

**LLI 신뢰도** (`LLI_confidence`)
- 의미: 패턴 신뢰도.
- 계산: confidence.
- 트렌드: LLI 신뢰도: early=0.72 → late=0.72 (Δ=+0, -0.041280–1/100cyc) → decreasing · context

### 전극 lean 가설

**PE lean** (`PE_side_score`)
- 의미: 0.75·LAM_PE + feature + FC-OCP Δhits.
- 계산: electrode_side v1.3.
- 트렌드: PE lean: early=0.4775 → late=0.8151 (Δ=+0.3375, +0.13050–1/100cyc) → increasing · matches_aging

**contact_stack** (`contact_stack_score`)
- 의미: ≈ contact_loss (R-centric).
- 계산: clip(contact_loss).
- 트렌드: contact_stack: early=0.7834 → late=0.9914 (Δ=+0.208, +0.073020–1/100cyc) → increasing · matches_aging

**NE 가설** (`NE_side_score`)
- 의미: contact × Si co-sign.
- 계산: electrode_side.
- 트렌드: NE 가설: early=0.1724 → late=0.2999 (Δ=+0.1276, +0.066880–1/100cyc) → increasing · matches_aging

**shared 모드** (`shared_side_score`)
- 의미: LLI/interface 등 공유 모드 평균.
- 계산: shared modes mean.
- 트렌드: shared 모드: early=0.3133 → late=0.6092 (Δ=+0.296, +0.081850–1/100cyc) → increasing · matches_aging

**Si co-sign** (`si_cosign`)
- 의미: 저SOC hyst·Q_relax·mech/chem·CV 동시 신호.
- 계산: SI_NE_COSIGN boost.
- 트렌드: Si co-sign: early=0.2 → late=0.4 (Δ=+0.2, +0.12510–1/100cyc) → increasing · matches_aging

**dominant 마진** (`dominance_margin`)
- 의미: 1위−2위 점수차.
- 계산: top-second.
- 트렌드: dominant 마진: early=0.2638 → late=0.1706 (Δ=-0.09322, -0.057480–1/100cyc) → decreasing · context

**FC-OCP 피크 hits** (`pe_peak_hits`)
- 의미: 충전 dQ/dV ↔ 합성 FC-OCP 매칭 수.
- 계산: unique nearest ±60mV.
- 트렌드: FC-OCP 피크 hits: early=1 → late=0 (Δ=-1, -0.2094count/100cyc) → decreasing · context

**FC-OCP hits Δ** (`pe_peak_hits_delta`)
- 의미: 기준 대비 hits 증가.
- 계산: hits-hits0.
- 트렌드: FC-OCP hits Δ: early=0 → late=0 (Δ=+0, +0count/100cyc) → flat · stable

**FC-OCP hits (alias)** (`fc_ocp_hits`)
- 의미: pe_peak_hits 별칭.
- 계산: same as pe_peak_hits.
- 트렌드: FC-OCP hits (alias): early=1 → late=0 (Δ=-1, -0.2094count/100cyc) → decreasing · context

**FC-OCP hits Δ (alias)** (`fc_ocp_hits_delta`)
- 의미: pe_peak_hits_delta 별칭.
- 계산: same as pe_peak_hits_delta.
- 트렌드: FC-OCP hits Δ (alias): early=0 → late=0 (Δ=+0, +0count/100cyc) → flat · stable

**전극진단 신뢰도** (`electrode_confidence`)
- 의미: coverage·분리·OCP 가용성.
- 계산: 0.35cov+0.35sep+0.30ocp.
- 트렌드: 전극진단 신뢰도: early=0.825 → late=0.861 (Δ=+0.03603, +0.01950–1/100cyc) → flat · context
