# 사이클별 지표 패널 — M02Ch111

## 트렌드 요약 — M02Ch111

- 유효 지표: 358개 · aging 방향 일치 48 · 반대 13

### 하락 트렌드 (상위)
- 충전 dQ/dV 피크1 높이: early=80.48 → late=81.33 (Δ=+0.8509, -3433Ah/V/100cyc) → decreasing · context
- 국소 CE(20): early=498.2 → late=301.7 (Δ=-196.5, -63.24%/100cyc) → decreasing · matches_aging
- 충전 에너지: early=249.7 → late=194.6 (Δ=-55.06, -21.6Wh/100cyc) → decreasing · matches_aging
- 방전후 휴지 완화 τ: early=361.7 → late=324.2 (Δ=-37.57, -20.28s/100cyc) → decreasing · context
- 방전후 완화 τ Δvs기준: early=3.59 → late=-33.98 (Δ=-37.57, -20.28s/100cyc) → decreasing · context

### 상승 트렌드 (상위)
- CV 시정수: early=843 → late=843 (Δ=+0, +80.05s/100cyc) → increasing · matches_aging
- fit 잔차 max: early=34.04 → late=203.3 (Δ=+169.3, +62.24mV/100cyc) → increasing · matches_aging
- 충전 dQ/dV 피크4 높이: early=96.7 → late=96.7 (Δ=+0, +40.62Ah/V/100cyc) → increasing · context
- EoC 방전 10s 증가%: early=24.02 → late=69.66 (Δ=+45.64, +21.57%/100cyc) → increasing · matches_aging
- EoC 방전 30s 증가%: early=18.59 → late=50.31 (Δ=+31.72, +15.2%/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- CV 충전용량: early=0 → late=0 (Δ=+0, -0.06824Ah/100cyc) → decreasing · opposite_aging
- CV 시간: early=0 → late=0 (Δ=+0, -14.51s/100cyc) → decreasing · opposite_aging
- 쿨롱 효율: early=101.9 → late=116.9 (Δ=+14.98, +6.03%/100cyc) → increasing · opposite_aging
- 쿨롱 비효율: early=-1.924 → late=-16.9 (Δ=-14.98, -6.03%/100cyc) → decreasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.

## 지표 카탈로그 + 트렌드

### 프로토콜 · 온도

**충전 전압 컷오프** (`chg_V_cutoff`)
- 의미: 충전 종료 전압.
- 계산: charge V max/cutoff.
- 트렌드: 충전 전압 컷오프: early=4.2 → late=4.2 (Δ=+5.18e-05, +3.568e-05V/100cyc) → flat · context

**방전 전압 컷오프** (`dchg_V_cutoff`)
- 의미: 방전 종료 전압.
- 계산: discharge V min/cutoff.
- 트렌드: 방전 전압 컷오프: early=2.5 → late=2.5 (Δ=-1.5e-05, +7.158e-06V/100cyc) → flat · context

**충전 전류 컷오프** (`chg_I_cutoff`)
- 의미: CV 종료 전류.
- 계산: charge I cutoff.
- 트렌드: 충전 전류 컷오프: early=33.21 → late=34.45 (Δ=+1.242, +1.183A/100cyc) → flat · context

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
- 트렌드: 사이클 소요시간: early=5.086 → late=5.014 (Δ=-0.07194, -0.1598h/100cyc) → flat · context

### 용량 · 효율 · CV

**용량 유지율** (`SoHQ`)
- 의미: 기준 대비 방전용량.
- 계산: Q_dchg/Q_base*100.
- 트렌드: 용량 유지율: early=97.72 → late=86.75 (Δ=-10.97, -4.347%/100cyc) → flat · stable

**방전 용량** (`dchgCapa`)
- 의미: 사이클 방전용량.
- 계산: max discharge capacity.
- 트렌드: 방전 용량: early=67.59 → late=60 (Δ=-7.588, -3.007Ah/100cyc) → flat · stable

**충전 용량** (`chgCapa`)
- 의미: 사이클 충전용량.
- 계산: max charge capacity.
- 트렌드: 충전 용량: early=66.47 → late=51.19 (Δ=-15.29, -6.005Ah/100cyc) → decreasing · matches_aging

**CC 충전용량** (`chgCCcapa`)
- 의미: CC 구간 용량.
- 계산: CC capacity.
- 트렌드: CC 충전용량: early=65.57 → late=50.88 (Δ=-14.69, -5.938Ah/100cyc) → decreasing · matches_aging

**CV 충전용량** (`chgCVcapa`)
- 의미: CV 구간 용량.
- 계산: signal/column CV Ah.
- 트렌드: CV 충전용량: early=0 → late=0 (Δ=+0, -0.06824Ah/100cyc) → decreasing · opposite_aging

**CC 용량비** (`chgCapa_CCratio`)
- 의미: CC/(CC+CV).
- 계산: chgCCcapa/chgCapa.
- 트렌드: CC 용량비: early=100 → late=100 (Δ=+0, +0.048311/100cyc) → flat · stable

**CC비 (정규화)** (`chgCapa_CCratio_norm`)
- 의미: 기준 정규화 CC비.
- 계산: CCratio / baseline.
- 트렌드: CC비 (정규화): early=95.23 → late=95.23 (Δ=+0, +0.31261/100cyc) → flat · stable

**CC비 Δ** (`delta_chgCapa_CCratio`)
- 의미: 기준 대비 CC비 변화.
- 계산: delta abs.
- 트렌드: CC비 Δ: early=0 → late=0 (Δ=+0, +0.048311/100cyc) → flat · stable

**CV 시간** (`chgCVtime`)
- 의미: CV 지속시간.
- 계산: CV step duration.
- 트렌드: CV 시간: early=0 → late=0 (Δ=+0, -14.51s/100cyc) → decreasing · opposite_aging

**CV 시정수** (`tau_CV`)
- 의미: CV 전류 감쇠 τ.
- 계산: I(t) exp fit.
- 트렌드: CV 시정수: early=843 → late=843 (Δ=+0, +80.05s/100cyc) → increasing · matches_aging

**CV Q @Tref** (`Q_CV_at_Tref`)
- 의미: 온도 보정 CV 용량.
- 계산: CV Q at ref T.
- 트렌드: CV Q @Tref: early=3.231 → late=3.231 (Δ=+0, +0.5513Ah/100cyc) → increasing · context

**쿨롱 효율** (`CE`)
- 의미: Q_dchg/Q_chg.
- 계산: dchg/chg*100.
- 트렌드: 쿨롱 효율: early=101.9 → late=116.9 (Δ=+14.98, +6.03%/100cyc) → increasing · opposite_aging

**가역 CE** (`CE_rev`)
- 의미: 가역 쿨롱 효율 proxy.
- 계산: rev CE extract.
- 트렌드: 가역 CE: early=97.48 → late=85.31 (Δ=-12.17, -4.382%/100cyc) → flat · stable

**국소 CE(20)** (`CE_local_20`)
- 의미: 최근 20사이클 국소 CE.
- 계산: rolling CE.
- 트렌드: 국소 CE(20): early=498.2 → late=301.7 (Δ=-196.5, -63.24%/100cyc) → decreasing · matches_aging

**쿨롱 비효율** (`CI`)
- 의미: 100−CE.
- 계산: 100-CE.
- 트렌드: 쿨롱 비효율: early=-1.924 → late=-16.9 (Δ=-14.98, -6.03%/100cyc) → decreasing · opposite_aging

**CI /시간** (`CI_per_hour`)
- 의미: 시간당 쿨롱 손실.
- 계산: CI / cycle_duration_h.
- 트렌드: CI /시간: early=-0.3778 → late=-3.372 (Δ=-2.994, -1.201%/h/100cyc) → decreasing · opposite_aging

**전압 효율** (`VE`)
- 의미: 에너지 전압효율.
- 계산: E_dchg/E_chg.
- 트렌드: 전압 효율: early=0.9062 → late=0.8627 (Δ=-0.04354, -0.018351/100cyc) → flat · stable

**에너지 효율** (`EE`)
- 의미: 충방전 에너지비.
- 계산: E_dchg/E_chg.
- 트렌드: 에너지 효율: early=0.9239 → late=1.009 (Δ=+0.08505, +0.033241/100cyc) → flat · stable

**충전 에너지** (`chg_E`)
- 의미: 충전 Wh.
- 계산: ∫VI dt charge.
- 트렌드: 충전 에너지: early=249.7 → late=194.6 (Δ=-55.06, -21.6Wh/100cyc) → decreasing · matches_aging

**방전 에너지** (`dchg_E`)
- 의미: 방전 Wh.
- 계산: ∫VI dt discharge.
- 트렌드: 방전 에너지: early=230 → late=196.9 (Δ=-33.12, -13.35Wh/100cyc) → decreasing · matches_aging

**에너지 손실** (`dE`)
- 의미: 충전−방전 에너지.
- 계산: chg_E-dchg_E.
- 트렌드: 에너지 손실: early=18.99 → late=-1.746 (Δ=-20.74, -8.288Wh/100cyc) → decreasing · opposite_aging

**완화 용량** (`Q_relax`)
- 의미: 휴지 회복 용량.
- 계산: DCIR block ΔQ.
- 트렌드: 완화 용량: early=-0.308 → late=0.012 (Δ=+0.32, +0.175Ah/100cyc) → increasing · context

**완화 용량 %** (`Q_relax_pct`)
- 의미: 회복 용량 분율.
- 계산: Q_relax/Q*100.
- 트렌드: 완화 용량 %: early=-0.4453 → late=0.01934 (Δ=+0.4647, +0.2544%/100cyc) → increasing · matches_aging

**dSoHQ/dN** (`dSoHQ_dN`)
- 의미: 용량 유지율 순간 기울기.
- 계산: diff SoHQ.
- 트렌드: dSoHQ/dN: early=-0.1786 → late=-0.02735 (Δ=+0.1513, +0.1691%/cyc/100cyc) → increasing · opposite_aging

**d2SoHQ** (`d2SoHQ`)
- 의미: SoHQ 2차 미분.
- 계산: diff dSoHQ.
- 트렌드: d2SoHQ: early=-0.001083 → late=-0.071 (Δ=-0.06992, -0.0469%/cyc2/100cyc) → decreasing · context

### 휴지 전압 (충전/방전 후)

**충전후 휴지 초기 V** (`EoC_restV_init`)
- 의미: 충전후 rest 시작 전압.
- 계산: rest step 첫 샘플.
- 트렌드: 충전후 휴지 초기 V: early=4.2 → late=4.2 (Δ=+0.0001093, +3.172e-05V/100cyc) → flat · context

**충전후 휴지 60s V** (`EoC_restV_60s`)
- 의미: 충전후 rest 60초 전압.
- 계산: rest ≈ 60 s 보간.
- 트렌드: 충전후 휴지 60s V: early=4.192 → late=4.181 (Δ=-0.01071, -0.004539V/100cyc) → flat · context

**충전후 휴지 30분 V** (`EoC_restV_30m`)
- 의미: 충전후 rest 30분 전압 (OCV에 가까움).
- 계산: rest ≈ 1800 s 보간.
- 트렌드: 충전후 휴지 30분 V: early=4.179 → late=4.153 (Δ=-0.02615, -0.01123V/100cyc) → flat · context

**충전후 휴지 종료 V** (`EoC_restV_end`)
- 의미: 충전후 rest 마지막 전압.
- 계산: rest step 끝 샘플.
- 트렌드: 충전후 휴지 종료 V: early=4.179 → late=4.153 (Δ=-0.02615, -0.01123V/100cyc) → flat · context

**충전후 휴지 완화량** (`EoC_restV_relax`)
- 의미: 충전후 end−init 완화.
- 계산: EoC_restV_end − EoC_restV_init.
- 트렌드: 충전후 휴지 완화량: early=-0.02061 → late=-0.04693 (Δ=-0.02632, -0.01126V/100cyc) → decreasing · context

**충전후 60s 완화량** (`EoC_restV_relax_60s`)
- 의미: 충전후 60s−init.
- 계산: EoC_restV_60s − EoC_restV_init.
- 트렌드: 충전후 60s 완화량: early=-0.007592 → late=-0.01846 (Δ=-0.01086, -0.004571V/100cyc) → decreasing · context

**충전후 휴지 완화 τ** (`EoC_restV_tau`)
- 의미: 충전후 rest 완화 시정수 proxy.
- 계산: rest V(t) 완화 fit τ.
- 트렌드: 충전후 휴지 완화 τ: early=534.7 → late=560.4 (Δ=+25.64, +14.47s/100cyc) → flat · context

**충전후 60s V Δvs기준** (`delta_EoC_restV_60s`)
- 의미: 기준 사이클 대비 EoC_restV_60s 이동.
- 계산: EoC_restV_60s(cycle) − baseline.
- 트렌드: 충전후 60s V Δvs기준: early=-0.0004723 → late=-0.01118 (Δ=-0.01071, -0.004539V/100cyc) → decreasing · context

**충전후 30분 V Δvs기준** (`delta_EoC_restV_30m`)
- 의미: 기준 사이클 대비 EoC_restV_30m 이동.
- 계산: EoC_restV_30m(cycle) − baseline.
- 트렌드: 충전후 30분 V Δvs기준: early=-0.000821 → late=-0.02698 (Δ=-0.02615, -0.01123V/100cyc) → decreasing · context

**충전후 종료 V Δvs기준** (`delta_EoC_restV_end`)
- 의미: 기준 사이클 대비 EoC_restV_end 이동.
- 계산: EoC_restV_end(cycle) − baseline.
- 트렌드: 충전후 종료 V Δvs기준: early=-0.000821 → late=-0.02698 (Δ=-0.02615, -0.01123V/100cyc) → decreasing · context

**충전후 완화 τ Δvs기준** (`delta_EoC_restV_tau`)
- 의미: 기준 사이클 대비 EoC_restV_tau 이동.
- 계산: EoC_restV_tau(cycle) − baseline.
- 트렌드: 충전후 완화 τ Δvs기준: early=-21.76 → late=3.882 (Δ=+25.64, +14.47s/100cyc) → increasing · context

**방전후 휴지 초기 V** (`EoD_restV_init`)
- 의미: 방전후 rest 시작 전압.
- 계산: rest step 첫 샘플.
- 트렌드: 방전후 휴지 초기 V: early=2.5 → late=2.5 (Δ=-1.5e-05, +7.158e-06V/100cyc) → flat · context

**방전후 휴지 60s V** (`EoD_restV_60s`)
- 의미: 방전후 rest 60초 전압.
- 계산: rest ≈ 60 s 보간.
- 트렌드: 방전후 휴지 60s V: early=2.883 → late=2.951 (Δ=+0.06807, +0.0323V/100cyc) → flat · context

**방전후 휴지 30분 V** (`EoD_restV_30m`)
- 의미: 방전후 rest 30분 전압 (OCV에 가까움).
- 계산: rest ≈ 1800 s 보간.
- 트렌드: 방전후 휴지 30분 V: early=3.016 → late=3.074 (Δ=+0.05746, +0.02446V/100cyc) → flat · context

**방전후 휴지 종료 V** (`EoD_restV_end`)
- 의미: 방전후 rest 마지막 전압.
- 계산: rest step 끝 샘플.
- 트렌드: 방전후 휴지 종료 V: early=3.016 → late=3.074 (Δ=+0.05746, +0.02446V/100cyc) → flat · context

**방전후 휴지 완화량** (`EoD_restV_relax`)
- 의미: 방전후 end−init 완화.
- 계산: EoD_restV_end − EoD_restV_init.
- 트렌드: 방전후 휴지 완화량: early=0.5163 → late=0.5736 (Δ=+0.05739, +0.02446V/100cyc) → flat · context

**방전후 60s 완화량** (`EoD_restV_relax_60s`)
- 의미: 방전후 60s−init.
- 계산: EoD_restV_60s − EoD_restV_init.
- 트렌드: 방전후 60s 완화량: early=0.3826 → late=0.4507 (Δ=+0.06806, +0.0323V/100cyc) → increasing · context

**방전후 휴지 완화 τ** (`EoD_restV_tau`)
- 의미: 방전후 rest 완화 시정수 proxy.
- 계산: rest V(t) 완화 fit τ.
- 트렌드: 방전후 휴지 완화 τ: early=361.7 → late=324.2 (Δ=-37.57, -20.28s/100cyc) → decreasing · context

**방전후 60s V Δvs기준** (`delta_EoD_restV_60s`)
- 의미: 기준 사이클 대비 EoD_restV_60s 이동.
- 계산: EoD_restV_60s(cycle) − baseline.
- 트렌드: 방전후 60s V Δvs기준: early=0.05328 → late=0.1214 (Δ=+0.06807, +0.0323V/100cyc) → increasing · context

**방전후 30분 V Δvs기준** (`delta_EoD_restV_30m`)
- 의미: 기준 사이클 대비 EoD_restV_30m 이동.
- 계산: EoD_restV_30m(cycle) − baseline.
- 트렌드: 방전후 30분 V Δvs기준: early=0.03952 → late=0.09698 (Δ=+0.05746, +0.02446V/100cyc) → increasing · context

**방전후 종료 V Δvs기준** (`delta_EoD_restV_end`)
- 의미: 기준 사이클 대비 EoD_restV_end 이동.
- 계산: EoD_restV_end(cycle) − baseline.
- 트렌드: 방전후 종료 V Δvs기준: early=0.03952 → late=0.09698 (Δ=+0.05746, +0.02446V/100cyc) → increasing · context

**방전후 완화 τ Δvs기준** (`delta_EoD_restV_tau`)
- 의미: 기준 사이클 대비 EoD_restV_tau 이동.
- 계산: EoD_restV_tau(cycle) − baseline.
- 트렌드: 방전후 완화 τ Δvs기준: early=3.59 → late=-33.98 (Δ=-37.57, -20.28s/100cyc) → decreasing · context

### 시작 저항 (EoC/EoD)

**EoC 방전 10s DCIR** (`EoC_dchgR_10s`)
- 의미: EoC 방전 시작 후 10s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(10s)|/|I|*1000.
- 트렌드: EoC 방전 10s DCIR: early=0.1733 → late=0.2371 (Δ=+0.06378, +0.03014mΩ/100cyc) → increasing · matches_aging

**EoC 방전 10s 증가%** (`EoC_dchgR_10s_inc`)
- 의미: 기준 대비 EoC_dchgR_10s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 10s 증가%: early=24.02 → late=69.66 (Δ=+45.64, +21.57%/100cyc) → increasing · matches_aging

**EoC 방전 30s DCIR** (`EoC_dchgR_30s`)
- 의미: EoC 방전 시작 후 30s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(30s)|/|I|*1000.
- 트렌드: EoC 방전 30s DCIR: early=0.4759 → late=0.6032 (Δ=+0.1273, +0.06098mΩ/100cyc) → increasing · matches_aging

**EoC 방전 30s 증가%** (`EoC_dchgR_30s_inc`)
- 의미: 기준 대비 EoC_dchgR_30s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 30s 증가%: early=18.59 → late=50.31 (Δ=+31.72, +15.2%/100cyc) → increasing · matches_aging

**EoC 방전 60s DCIR** (`EoC_dchgR_60s`)
- 의미: EoC 방전 시작 후 60s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(60s)|/|I|*1000.
- 트렌드: EoC 방전 60s DCIR: early=0.8405 → late=1.012 (Δ=+0.172, +0.08047mΩ/100cyc) → increasing · matches_aging

**EoC 방전 60s 증가%** (`EoC_dchgR_60s_inc`)
- 의미: 기준 대비 EoC_dchgR_60s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoC 방전 60s 증가%: early=13.96 → late=37.28 (Δ=+23.32, +10.91%/100cyc) → increasing · matches_aging

**EoD 충전 10s DCIR** (`EoD_chgR_10s`)
- 의미: EoD 충전 시작 후 10s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(10s)|/|I|*1000.
- 트렌드: EoD 충전 10s DCIR: early=0.2826 → late=0.3457 (Δ=+0.06308, +0.02728mΩ/100cyc) → increasing · matches_aging

**EoD 충전 10s 증가%** (`EoD_chgR_10s_inc`)
- 의미: 기준 대비 EoD_chgR_10s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 10s 증가%: early=-4.719 → late=16.55 (Δ=+21.26, +9.197%/100cyc) → increasing · matches_aging

**EoD 충전 30s DCIR** (`EoD_chgR_30s`)
- 의미: EoD 충전 시작 후 30s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(30s)|/|I|*1000.
- 트렌드: EoD 충전 30s DCIR: early=0.7679 → late=0.9127 (Δ=+0.1448, +0.05638mΩ/100cyc) → increasing · matches_aging

**EoD 충전 30s 증가%** (`EoD_chgR_30s_inc`)
- 의미: 기준 대비 EoD_chgR_30s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 30s 증가%: early=-8.423 → late=8.849 (Δ=+17.27, +6.724%/100cyc) → increasing · matches_aging

**EoD 충전 60s DCIR** (`EoD_chgR_60s`)
- 의미: EoD 충전 시작 후 60s 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).
- 계산: |V0-V(60s)|/|I|*1000.
- 트렌드: EoD 충전 60s DCIR: early=1.374 → late=1.548 (Δ=+0.1747, +0.06353mΩ/100cyc) → flat · stable

**EoD 충전 60s 증가%** (`EoD_chgR_60s_inc`)
- 의미: 기준 대비 EoD_chgR_60s 상대 증가율.
- 계산: 100*(R/R0 - 1).
- 트렌드: EoD 충전 60s 증가%: early=-10.29 → late=1.118 (Δ=+11.41, +4.149%/100cyc) → increasing · matches_aging

**EoC R10/R60** (`EoC_dchgR_10_60_ratio`)
- 의미: 10s/60s 비. 초기 응답 비중.
- 계산: EoC_dchgR_10s / EoC_dchgR_60s.
- 트렌드: EoC R10/R60: early=0.2062 → late=0.2345 (Δ=+0.02834, +0.013781/100cyc) → increasing · context

**EoD R10/R60** (`EoD_chgR_10_60_ratio`)
- 의미: 10s/60s 비.
- 계산: EoD_chgR_10s / EoD_chgR_60s.
- 트렌드: EoD R10/R60: early=0.2065 → late=0.2233 (Δ=+0.01683, +0.0086811/100cyc) → flat · context

**EoC R10s @25C** (`EoC_dchgR_10s_T25`)
- 의미: 온도 보정 10s DCIR.
- 계산: Arrhenius-ish correct_r_to_25c.
- 트렌드: EoC R10s @25C: early=0.08282 → late=0.1133 (Δ=+0.03048, +0.0144mΩ/100cyc) → increasing · matches_aging

**EoD R10s @25C** (`EoD_chgR_10s_T25`)
- 의미: 온도 보정 10s DCIR.
- 계산: correct_r_to_25c.
- 트렌드: EoD R10s @25C: early=0.1351 → late=0.1652 (Δ=+0.03014, +0.01304mΩ/100cyc) → increasing · matches_aging

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
- 트렌드: RΩ (SOC50): early=1.092 → late=2.744 (Δ=+1.651, +0.7975mΩ/100cyc) → increasing · matches_aging

**Rct (SOC50)** (`R_ct_soc50`)
- 의미: 중간 잔차 지수항. Cdl 미분리.
- 계산: resid exp-sat fit.
- 트렌드: Rct (SOC50): early=0.7379 → late=0.9016 (Δ=+0.1637, +0.06968mΩ/100cyc) → increasing · matches_aging

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
- 트렌드: 기계/화학 비: early=1.48 → late=3.043 (Δ=+1.563, +0.79681/100cyc) → increasing · matches_aging

**RΩ 성장/100cyc** (`R_ohmic_growth_100`)
- 의미: 기준 대비 RΩ 성장률 (레벨과 별개).
- 계산: (R-R0)/((N-N0)/100).
- 트렌드: RΩ 성장/100cyc: early=1.104 → late=0.7864 (Δ=-0.3172, -0.3213mΩ/100cyc/100cyc) → decreasing · context

**Rct 성장/100cyc** (`R_ct_growth_100`)
- 의미: 기준 대비 Rct 성장률.
- 계산: (Rct-Rct0)/((N-N0)/100).
- 트렌드: Rct 성장/100cyc: early=0.05901 → late=0.07797 (Δ=+0.01896, +0.01921mΩ/100cyc/100cyc) → increasing · context

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
- 트렌드: RΩ SOC50 (ff): early=1.092 → late=2.744 (Δ=+1.651, +0.7975mΩ/100cyc) → increasing · matches_aging

**Rct SOC50 (ff)** (`R_ct_soc50_ff`)
- 의미: DCIR 블록 forward-fill 값.
- 계산: block stamp + ffill.
- 트렌드: Rct SOC50 (ff): early=0.7379 → late=0.9016 (Δ=+0.1637, +0.06968mΩ/100cyc) → increasing · matches_aging

### 곡선 형상 · 히스테리시스

**충전 평균 V** (`chg_V_avg`)
- 의미: 충전 평균 전압.
- 계산: mean V charge.
- 트렌드: 충전 평균 V: early=3.774 → late=3.824 (Δ=+0.05024, +0.02046V/100cyc) → flat · context

**방전 평균 V** (`dchg_V_avg`)
- 의미: 방전 평균 전압.
- 계산: mean V discharge.
- 트렌드: 방전 평균 V: early=3.413 → late=3.291 (Δ=-0.1219, -0.05321V/100cyc) → flat · context

**충전 평균V Δ** (`delta_chg_V_avg`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 충전 평균V Δ: early=0.03413 → late=0.08437 (Δ=+0.05024, +0.02046V/100cyc) → increasing · context

**방전 평균V Δ** (`delta_dchg_V_avg`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 방전 평균V Δ: early=-0.02634 → late=-0.1482 (Δ=-0.1219, -0.05321V/100cyc) → decreasing · context

**충전 IR drop proxy** (`chg_ir_drop_proxy`)
- 의미: 충전 초반 IR 강하 proxy.
- 계산: early ΔV.
- 트렌드: 충전 IR drop proxy: early=0.04014 → late=0.04014 (Δ=-6.9e-06, +2.066e-05V/100cyc) → flat · stable

**방전 IR drop proxy** (`dchg_ir_drop_proxy`)
- 의미: 방전 초반 IR 강하 proxy.
- 계산: early ΔV.
- 트렌드: 방전 IR drop proxy: early=0.04009 → late=0.04015 (Δ=+5.57e-05, +0.0004129V/100cyc) → flat · stable

**히스테리시스 면적** (`hyst_area`)
- 의미: 전체 충방전 히스테리시스.
- 계산: ∮(Vchg-Vdchg)dQ.
- 트렌드: 히스테리시스 면적: early=0.5537 → late=0.5996 (Δ=+0.04594, +0.02149V/100cyc) → flat · stable

**저SOC 히스테리시스** (`hyst_area_low`)
- 의미: 저SOC 밴드. Si chemo-mech.
- 계산: band integral.
- 트렌드: 저SOC 히스테리시스: early=0.08677 → late=0.0439 (Δ=-0.04287, -0.01806V/100cyc) → decreasing · opposite_aging

**중SOC 히스테리시스** (`hyst_area_mid`)
- 의미: 중SOC 밴드.
- 계산: band integral.
- 트렌드: 중SOC 히스테리시스: early=0.2494 → late=0.319 (Δ=+0.06957, +0.03057V/100cyc) → increasing · context

**고SOC 히스테리시스** (`hyst_area_high`)
- 의미: 고SOC 밴드. PE 보조.
- 계산: band integral.
- 트렌드: 고SOC 히스테리시스: early=0.2143 → late=0.2348 (Δ=+0.02048, +0.009044V/100cyc) → flat · stable

**히스테리시스 저SOC분율** (`hyst_frac_low`)
- 의미: low/total.
- 계산: hyst_low/hyst.
- 트렌드: 히스테리시스 저SOC분율: early=0.157 → late=0.07325 (Δ=-0.08377, -0.035291/100cyc) → decreasing · context

**히스테리시스 고SOC분율** (`hyst_frac_high`)
- 의미: high/total.
- 계산: hyst_high/hyst.
- 트렌드: 히스테리시스 고SOC분율: early=0.3874 → late=0.3919 (Δ=+0.004497, +0.0011271/100cyc) → flat · context

**최대 히스테리시스 dV** (`hyst_max_dV`)
- 의미: 최대 충방전 전압차.
- 계산: max|Vchg-Vdchg|.
- 트렌드: 최대 히스테리시스 dV: early=1.543 → late=1.602 (Δ=+0.05813, +0.02742V/100cyc) → flat · stable

**max dV 저SOC** (`hyst_max_dV_low`)
- 의미: 저SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 저SOC: early=0.7193 → late=0.4784 (Δ=-0.2409, -0.1008V/100cyc) → decreasing · opposite_aging

**max dV 중SOC** (`hyst_max_dV_mid`)
- 의미: 중SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 중SOC: early=0.9535 → late=1.088 (Δ=+0.1344, +0.05858V/100cyc) → increasing · context

**max dV 고SOC** (`hyst_max_dV_high`)
- 의미: 고SOC 최대 dV.
- 계산: band max.
- 트렌드: max dV 고SOC: early=1.543 → late=1.602 (Δ=+0.05813, +0.02742V/100cyc) → flat · context

**히스테리시스 Δ** (`delta_hyst_area`)
- 의미: 기준 대비 면적.
- 계산: delta.
- 트렌드: 히스테리시스 Δ: early=0.004923 → late=0.05087 (Δ=+0.04594, +0.02149V/100cyc) → increasing · matches_aging

**max dV Δ** (`delta_hyst_max_dV`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: max dV Δ: early=0.008159 → late=0.06629 (Δ=+0.05813, +0.02742V/100cyc) → increasing · matches_aging

**충전 플래토 V** (`chg_plateau_V`)
- 의미: 충전 플래토 전압.
- 계산: plateau detect.
- 트렌드: 충전 플래토 V: early=3.686 → late=3.774 (Δ=+0.08743, +0.01714V/100cyc) → flat · context

**충전 플래토 폭** (`chg_plateau_width`)
- 의미: 충전 플래토 Q 폭.
- 계산: plateau width.
- 트렌드: 충전 플래토 폭: early=10.34 → late=9.889 (Δ=-0.4511, +0.4667Q-units/100cyc) → flat · context

**방전 플래토 V** (`dchg_plateau_V`)
- 의미: 방전 플래토 전압.
- 계산: plateau detect.
- 트렌드: 방전 플래토 V: early=3.19 → late=3.116 (Δ=-0.07325, -0.03213V/100cyc) → flat · context

**방전 플래토 폭** (`dchg_plateau_width`)
- 의미: 방전 플래토 Q 폭.
- 계산: plateau width.
- 트렌드: 방전 플래토 폭: early=17.42 → late=14.33 (Δ=-3.09, -1.201Q-units/100cyc) → decreasing · matches_aging

**방전 플래토 ΔV** (`delta_dchg_plateau_V`)
- 의미: 기준 대비 이동.
- 계산: delta plateau V.
- 트렌드: 방전 플래토 ΔV: early=-0.03324 → late=-0.1065 (Δ=-0.07325, -0.03213V/100cyc) → decreasing · context

**방전 컷오프 마진** (`dchg_V_cutoff_margin`)
- 의미: 컷오프까지 여유.
- 계산: Vmin-margin.
- 트렌드: 방전 컷오프 마진: early=0.4223 → late=0.2915 (Δ=-0.1308, -0.05775V/100cyc) → decreasing · matches_aging

**컷오프 마진 Δ** (`delta_dchg_V_cutoff_margin`)
- 의미: 기준 대비.
- 계산: delta.
- 트렌드: 컷오프 마진 Δ: early=-0.01926 → late=-0.1501 (Δ=-0.1308, -0.05775V/100cyc) → decreasing · matches_aging

**방전 형상 DTW** (`dchg_shape_DTW`)
- 의미: 기준 곡선 DTW 거리.
- 계산: DTW vs baseline.
- 트렌드: 방전 형상 DTW: early=0.003666 → late=0.01155 (Δ=+0.007883, +0.0036571/100cyc) → increasing · matches_aging

**DTW Δ** (`delta_dchg_shape_DTW`)
- 의미: 기준 대비 DTW.
- 계산: delta.
- 트렌드: DTW Δ: early=0.002511 → late=0.01039 (Δ=+0.007883, +0.0036571/100cyc) → increasing · matches_aging

### dQ/dV · dV/dQ 피크

**충전 dQ/dV 피크1 V** (`chg_dQdV_peak1_V`)
- 의미: 충전 IC 1번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크1 V: early=3.464 → late=3.761 (Δ=+0.2962, +0.05425V/100cyc) → flat · context

**충전 dQ/dV 피크1 높이** (`chg_dQdV_peak1`)
- 의미: 충전 IC 1번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크1 높이: early=80.48 → late=81.33 (Δ=+0.8509, -3433Ah/V/100cyc) → decreasing · context

**방전 dQ/dV 피크1 V** (`dchg_dQdV_peak1_V`)
- 의미: 방전 IC 1번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크1 V: early=3.169 → late=3.116 (Δ=-0.05271, -0.02131V/100cyc) → flat · context

**방전 dQ/dV 피크1 높이** (`dchg_dQdV_peak1`)
- 의미: 방전 IC 1번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크1 높이: early=-71.29 → late=-56.51 (Δ=+14.78, +6.118Ah/V/100cyc) → increasing · context

**충전 dV/dQ 피크1 Q** (`chg_dVdQ_peak1_Q`)
- 의미: 충전 dV/dQ 1번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 충전 dV/dQ 피크1 Q: early=55.15 → late=47.41 (Δ=-7.742, -3.048Ah/100cyc) → decreasing · context

**충전 dV/dQ 피크1 높이** (`chg_dVdQ_peak1`)
- 의미: 충전 dV/dQ 1번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 충전 dV/dQ 피크1 높이: early=0.01582 → late=0.01802 (Δ=+0.002205, +0.0009162V/Ah/100cyc) → increasing · context

**방전 dV/dQ 피크1 Q** (`dchg_dVdQ_peak1_Q`)
- 의미: 방전 dV/dQ 1번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 방전 dV/dQ 피크1 Q: early=11.59 → late=25.05 (Δ=+13.46, +8.147Ah/100cyc) → increasing · context

**방전 dV/dQ 피크1 높이** (`dchg_dVdQ_peak1`)
- 의미: 방전 dV/dQ 1번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 방전 dV/dQ 피크1 높이: early=-0.02213 → late=-0.0227 (Δ=-0.0005672, -0.0002853V/Ah/100cyc) → flat · context

**충전 dQ/dV 피크2 V** (`chg_dQdV_peak2_V`)
- 의미: 충전 IC 2번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크2 V: early=3.698 → late=3.981 (Δ=+0.2825, +0.08312V/100cyc) → flat · context

**충전 dQ/dV 피크2 높이** (`chg_dQdV_peak2`)
- 의미: 충전 IC 2번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크2 높이: early=89.44 → late=75.44 (Δ=-14, -4.197Ah/V/100cyc) → flat · context

**방전 dQ/dV 피크2 V** (`dchg_dQdV_peak2_V`)
- 의미: 방전 IC 2번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크2 V: early=3.645 → late=3.629 (Δ=-0.01606, -0.01394V/100cyc) → flat · context

**방전 dQ/dV 피크2 높이** (`dchg_dQdV_peak2`)
- 의미: 방전 IC 2번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크2 높이: early=-53.28 → late=-50.82 (Δ=+2.457, +1.283Ah/V/100cyc) → flat · context

**충전 dV/dQ 피크2 Q** (`chg_dVdQ_peak2_Q`)
- 의미: 충전 dV/dQ 2번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 충전 dV/dQ 피크2 Q: early=65.54 → late=65.54 (Δ=+0, n/a) → flat · context

**충전 dV/dQ 피크2 높이** (`chg_dVdQ_peak2`)
- 의미: 충전 dV/dQ 2번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 충전 dV/dQ 피크2 높이: early=0.01257 → late=0.01257 (Δ=+0, n/a) → flat · context

**방전 dV/dQ 피크2 Q** (`dchg_dVdQ_peak2_Q`)
- 의미: 방전 dV/dQ 2번 피크 용량 위치.
- 계산: dV/dQ peak Q.
- 트렌드: 방전 dV/dQ 피크2 Q: early=30.03 → late=29.09 (Δ=-0.9408, -1.651Ah/100cyc) → decreasing · context

**방전 dV/dQ 피크2 높이** (`dchg_dVdQ_peak2`)
- 의미: 방전 dV/dQ 2번 피크 높이.
- 계산: dV/dQ peak height.
- 트렌드: 방전 dV/dQ 피크2 높이: early=-0.02153 → late=-0.02176 (Δ=-0.0002347, -0.0005918V/Ah/100cyc) → flat · context

**충전 dQ/dV 피크3 V** (`chg_dQdV_peak3_V`)
- 의미: 충전 IC 3번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 충전 dQ/dV 피크3 V: early=3.953 → late=3.997 (Δ=+0.04471, -0.01215V/100cyc) → flat · context

**충전 dQ/dV 피크3 높이** (`chg_dQdV_peak3`)
- 의미: 충전 IC 3번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크3 높이: early=82.18 → late=78.36 (Δ=-3.826, +7.334Ah/V/100cyc) → increasing · context

**방전 dQ/dV 피크3 V** (`dchg_dQdV_peak3_V`)
- 의미: 방전 IC 3번 피크 전압.
- 계산: SG + find_peaks.
- 트렌드: 방전 dQ/dV 피크3 V: early=3.981 → late=3.855 (Δ=-0.1263, -0.09386V/100cyc) → flat · context

**방전 dQ/dV 피크3 높이** (`dchg_dQdV_peak3`)
- 의미: 방전 IC 3번 피크 높이.
- 계산: peak height.
- 트렌드: 방전 dQ/dV 피크3 높이: early=-59.57 → late=-45.25 (Δ=+14.32, +6.625Ah/V/100cyc) → increasing · context

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
- 트렌드: 충전 dQ/dV 피크4 V: early=4.161 → late=4.161 (Δ=+0, -0.05226V/100cyc) → flat · context

**충전 dQ/dV 피크4 높이** (`chg_dQdV_peak4`)
- 의미: 충전 IC 4번 피크 높이.
- 계산: peak prominence/height.
- 트렌드: 충전 dQ/dV 피크4 높이: early=96.7 → late=96.7 (Δ=+0, +40.62Ah/V/100cyc) → increasing · context

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
- 트렌드: 충전 피크1 ΔV: early=0.04817 → late=0.3443 (Δ=+0.2962, +0.05425V/100cyc) → increasing · context

**방전 피크1 ΔV** (`delta_dchg_dQdV_peak1_V`)
- 의미: 기준 대비 방전 dQ/dV 피크1 이동.
- 계산: delta_dchg_dQdV_peak1_V
- 트렌드: 방전 피크1 ΔV: early=-0.03239 → late=-0.0851 (Δ=-0.05271, -0.02131V/100cyc) → decreasing · context

**방전 dV/dQ @SOC0** (`dchg_dVdQ_SOC0`)
- 의미: 저SOC cliff dV/dQ.
- 계산: dchg_dVdQ_SOC0
- 트렌드: 방전 dV/dQ @SOC0: early=0.1078 → late=0.06981 (Δ=-0.03795, -0.01832V/Ah/100cyc) → decreasing · context

**방전 dV/dQ @SOC5** (`dchg_dVdQ_SOC5`)
- 의미: SOC≈5% dV/dQ.
- 계산: dchg_dVdQ_SOC5
- 트렌드: 방전 dV/dQ @SOC5: early=0.04914 → late=0.04273 (Δ=-0.00641, -0.002951V/Ah/100cyc) → decreasing · context

**방전 dV/dQ @SOC10** (`dchg_dVdQ_SOC10`)
- 의미: SOC≈10% dV/dQ.
- 계산: dchg_dVdQ_SOC10
- 트렌드: 방전 dV/dQ @SOC10: early=0.02913 → late=0.03017 (Δ=+0.001044, +0.0002802V/Ah/100cyc) → flat · context

**방전 dV/dQ @mid** (`dchg_dVdQ_SOCmid`)
- 의미: 중SOC dV/dQ.
- 계산: dchg_dVdQ_SOCmid
- 트렌드: 방전 dV/dQ @mid: early=0.0196 → late=0.02076 (Δ=+0.001167, +0.0004514V/Ah/100cyc) → flat · context

**방전 cliff Q** (`dchg_dVdQ_SOC0_Q`)
- 의미: SOC0 dV/dQ 위치 Q.
- 계산: dchg_dVdQ_SOC0_Q
- 트렌드: 방전 cliff Q: early=67.39 → late=59.8 (Δ=-7.583, -2.982Ah/100cyc) → flat · context

**방전 cliff 폭** (`dchg_dVdQ_SOC0_cliff_width`)
- 의미: 저SOC cliff 폭.
- 계산: dchg_dVdQ_SOC0_cliff_width
- 트렌드: 방전 cliff 폭: early=4.997 → late=3.478 (Δ=-1.519, -0.6294Ah/100cyc) → decreasing · context

**cliff/mid 비** (`dchg_dVdQ_SOC0_to_mid_ratio`)
- 의미: SOC0/mid dV/dQ 비.
- 계산: dchg_dVdQ_SOC0_to_mid_ratio
- 트렌드: cliff/mid 비: early=5.499 → late=3.369 (Δ=-2.13, -1.0051/100cyc) → decreasing · context

**충전 dV/dQ @100** (`chg_dVdQ_SOC100`)
- 의미: 만충 부근 dV/dQ.
- 계산: chg_dVdQ_SOC100
- 트렌드: 충전 dV/dQ @100: early=0.009986 → late=0.01344 (Δ=+0.003457, +0.001421V/Ah/100cyc) → increasing · context

**dV/dQ SOC0 Δ** (`delta_dchg_dVdQ_SOC0`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0
- 트렌드: dV/dQ SOC0 Δ: early=0.001093 → late=-0.03686 (Δ=-0.03795, -0.01832V/Ah/100cyc) → decreasing · context

**dV/dQ SOC5 Δ** (`delta_dchg_dVdQ_SOC5`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC5
- 트렌드: dV/dQ SOC5 Δ: early=-0.002466 → late=-0.008876 (Δ=-0.00641, -0.002951V/Ah/100cyc) → decreasing · context

**dV/dQ SOC10 Δ** (`delta_dchg_dVdQ_SOC10`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC10
- 트렌드: dV/dQ SOC10 Δ: early=-0.001896 → late=-0.0008519 (Δ=+0.001044, +0.0002802V/Ah/100cyc) → increasing · context

**dV/dQ mid Δ** (`delta_dchg_dVdQ_SOCmid`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOCmid
- 트렌드: dV/dQ mid Δ: early=0.0002808 → late=0.001447 (Δ=+0.001167, +0.0004514V/Ah/100cyc) → increasing · context

**dV/dQ 100 Δ** (`delta_chg_dVdQ_SOC100`)
- 의미: 기준 대비.
- 계산: delta_chg_dVdQ_SOC100
- 트렌드: dV/dQ 100 Δ: early=-0.004091 → late=-0.0006338 (Δ=+0.003457, +0.001421V/Ah/100cyc) → increasing · context

**cliff 폭 Δ** (`delta_dchg_dVdQ_SOC0_cliff_width`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0_cliff_width
- 트렌드: cliff 폭 Δ: early=-0.5255 → late=-2.044 (Δ=-1.519, -0.6294Ah/100cyc) → decreasing · context

**cliff/mid Δ** (`delta_dchg_dVdQ_SOC0_to_mid_ratio`)
- 의미: 기준 대비.
- 계산: delta_dchg_dVdQ_SOC0_to_mid_ratio
- 트렌드: cliff/mid Δ: early=-0.02339 → late=-2.154 (Δ=-2.13, -1.0051/100cyc) → decreasing · context

**충전 IC 면적합** (`chg_dQdV_area_sum`)
- 의미: dQ/dV 피크 면적 합.
- 계산: chg_dQdV_area_sum
- 트렌드: 충전 IC 면적합: early=66.15 → late=50.88 (Δ=-15.27, -5.683Ah/100cyc) → decreasing · context

**방전 IC 면적합** (`dchg_dQdV_area_sum`)
- 의미: dQ/dV 피크 면적 합.
- 계산: dchg_dQdV_area_sum
- 트렌드: 방전 IC 면적합: early=67.39 → late=59.8 (Δ=-7.583, -2.982Ah/100cyc) → flat · context

### 수송 · rate · η

**RCF** (`RCF`)
- 의미: Q_0.5C / Q_C/3.
- 계산: routine/RPT Q.
- 트렌드: RCF: early=0.9772 → late=0.9672 (Δ=-0.009985, +0.0016941/100cyc) → flat · stable

**RCF 기울기/100** (`RCF_slope_100`)
- 의미: RCF 변화율.
- 계산: first-last slope.
- 트렌드: RCF 기울기/100: early=-0.01156 → late=-0.01156 (Δ=+0, +3.54e-181/100cyc/100cyc) → flat · stable

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
- 트렌드: I∞ 정규화: early=5.405e-17 → late=5.405e-17 (Δ=+0, +0.12631/100cyc) → increasing · context

**펄스 1s 샘플수** (`pulse_sample_count_1s`)
- 의미: t≤1s 샘플 수.
- 계산: quality.
- 트렌드: 펄스 1s 샘플수: early=5 → late=7 (Δ=+2, +0.8611count/100cyc) → increasing · context

**펄스 전류 안정도** (`pulse_current_stability`)
- 의미: std(I)/|I|.
- 계산: quality.
- 트렌드: 펄스 전류 안정도: early=0.02607 → late=0.04566 (Δ=+0.01959, +0.0083421/100cyc) → increasing · opposite_aging

**rest 충분성** (`rest_sufficiency`)
- 의미: 휴지 길이/품질.
- 계산: quality.
- 트렌드: rest 충분성: early=3 → late=3 (Δ=+0, -0.16151/100cyc) → decreasing · context

**레그 완전성** (`leg_completeness`)
- 의미: 충방전 레그 완전성.
- 계산: quality.
- 트렌드: 레그 완전성: early=0.9998 → late=0.9999 (Δ=+8.035e-05, -0.018141/100cyc) → flat · context

**완화 완성도 max** (`relax_completeness_max`)
- 의미: SOC별 최대 완화 완성도.
- 계산: max.
- 트렌드: 

**샘플/mV** (`samples_per_mV`)
- 의미: 전압 해상도 샘플밀도.
- 계산: dqdv quality.
- 트렌드: 샘플/mV: early=0.3618 → late=0.3506 (Δ=-0.01121, -0.011761/mV/100cyc) → flat · context

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
- 트렌드: LAM 곡선 proxy: early=-1.959 → late=-12.31 (Δ=-10.36, -4.262%/100cyc) → decreasing · context

**LLI 곡선 proxy** (`LLI_curve_proxy`)
- 의미: Q 오프셋 proxy (절대 LLI% 아님).
- 계산: offset/Qmax*100.
- 트렌드: LLI 곡선 proxy: early=-0.2132 → late=1.26 (Δ=+1.473, +0.4021%/100cyc) → increasing · context

**R 곡선 proxy** (`R_curve_proxy`)
- 의미: 곡선 fit dR proxy.
- 계산: fit_dR.
- 트렌드: R 곡선 proxy: early=0.9586 → late=4.291 (Δ=+3.333, +1.524mΩ/100cyc) → increasing · matches_aging

**방전 fit scale** (`dchg_fit_scale`)
- 의미: 기준 대비 scale s.
- 계산: 3-param fit.
- 트렌드: 방전 fit scale: early=1.02 → late=1.123 (Δ=+0.1036, +0.042621/100cyc) → flat · stable

**방전 fit offset** (`dchg_fit_offset`)
- 의미: Q 오프셋.
- 계산: 3-param fit.
- 트렌드: 방전 fit offset: early=-0.1474 → late=0.8715 (Δ=+1.019, +0.2781Ah/100cyc) → increasing · context

**방전 fit dR** (`dchg_fit_dR`)
- 의미: 저항 항.
- 계산: 3-param fit.
- 트렌드: 방전 fit dR: early=0.9586 → late=4.291 (Δ=+3.333, +1.524mΩ/100cyc) → increasing · matches_aging

**fit 잔차 RMS** (`dchg_fit_residual_rms`)
- 의미: 잔차 rms.
- 계산: RMS(resid).
- 트렌드: fit 잔차 RMS: early=4.072 → late=20.02 (Δ=+15.95, +6.417mV/100cyc) → increasing · matches_aging

**fit 잔차 max** (`dchg_fit_residual_max`)
- 의미: 잔차 최대.
- 계산: max|resid|.
- 트렌드: fit 잔차 max: early=34.04 → late=203.3 (Δ=+169.3, +62.24mV/100cyc) → increasing · matches_aging

**잔차 argmax SOC** (`dchg_fit_residual_argmax_SOC`)
- 의미: 잔차 최대 SOC (방전 DOD→SOC 변환).
- 계산: argmax residual.
- 트렌드: 잔차 argmax SOC: early=100 → late=100 (Δ=+0, +0.01526%/100cyc) → flat · context

**fit R2** (`dchg_fit_r2`)
- 의미: 곡선 fit 품질.
- 계산: r2.
- 트렌드: fit R2: early=0.9999 → late=0.9977 (Δ=-0.002247, -0.00096861/100cyc) → flat · context

**fit corr(s,o)** (`dchg_fit_corr_s_o`)
- 의미: scale-offset 상관 (축퇴 지표).
- 계산: corr.
- 트렌드: fit corr(s,o): early=0.5388 → late=0.7869 (Δ=+0.2481, +0.087661/100cyc) → increasing · context

**잔차 argmax DOD** (`dchg_fit_residual_argmax_DOD`)
- 의미: 잔차 최대 DOD.
- 계산: argmax DOD.
- 트렌드: 잔차 argmax DOD: early=0 → late=0 (Δ=+0, -0.01526%/100cyc) → decreasing · context

**ΔQ(V) min** (`dQV_min`)
- 의미: 전압빈 ΔQ 최소.
- 계산: histogram.
- 트렌드: ΔQ(V) min: early=-3.286 → late=-15.66 (Δ=-12.38, -5.241Ah/100cyc) → decreasing · context

**ΔQ(V) mean** (`dQV_mean`)
- 의미: ΔQ 평균.
- 계산: mean.
- 트렌드: ΔQ(V) mean: early=-2.433 → late=-12.03 (Δ=-9.599, -4.07Ah/100cyc) → decreasing · context

**ΔQ(V) var** (`dQV_var`)
- 의미: ΔQ 분산.
- 계산: var.
- 트렌드: ΔQ(V) var: early=0.2287 → late=4.005 (Δ=+3.776, +1.662Ah2/100cyc) → increasing · matches_aging

**ΔQ(V) log-var** (`dQV_log_var`)
- 의미: log10 분산.
- 계산: log10(var).
- 트렌드: ΔQ(V) log-var: early=-0.6408 → late=0.6026 (Δ=+1.243, +0.48451/100cyc) → increasing · matches_aging

**ΔQ(V) skew** (`dQV_skew`)
- 의미: 왜도.
- 계산: skew.
- 트렌드: ΔQ(V) skew: early=-0.3955 → late=-0.762 (Δ=-0.3665, -0.11451/100cyc) → decreasing · context

**ΔQ(V) kurtosis** (`dQV_kurtosis`)
- 의미: 첨도.
- 계산: kurtosis.
- 트렌드: ΔQ(V) kurtosis: early=-1.093 → late=-0.9439 (Δ=+0.149, +0.073451/100cyc) → increasing · context

**ΔQ argmin V** (`dQV_argmin_V`)
- 의미: ΔQ 최소 전압.
- 계산: argmin.
- 트렌드: ΔQ argmin V: early=3.158 → late=3.09 (Δ=-0.06796, -0.02668V/100cyc) → flat · context

**dQ/dV SNR** (`dqdv_snr`)
- 의미: IC 신호대잡음.
- 계산: snr estimate.
- 트렌드: dQ/dV SNR: early=76.79 → late=62 (Δ=-14.79, -5.3481/100cyc) → decreasing · context

**데이터 품질점수** (`quality_score`)
- 의미: 추출 품질 종합.
- 계산: quality gates.
- 트렌드: 데이터 품질점수: early=1 → late=1 (Δ=+0, -0.053850–1/100cyc) → decreasing · context

**전압 노이즈 σ** (`v_noise_sigma`)
- 의미: 전압 노이즈 추정.
- 계산: noise sigma.
- 트렌드: 전압 노이즈 σ: early=0.02213 → late=0.02742 (Δ=+0.005281, +0.00179V/100cyc) → increasing · context

**ΔQ(V) 기준 사이클** (`dQV_ref_cycle`)
- 의미: ΔQ 비교 기준 사이클.
- 계산: ref cycle id.
- 트렌드: ΔQ(V) 기준 사이클: early=3 → late=3 (Δ=+0, -4.883e-16cyc/100cyc) → flat · context

**온도 가용** (`temperature_available`)
- 의미: Temp 컬럼 유효 여부.
- 계산: bool→float.
- 트렌드: 온도 가용: early=0 → late=0 (Δ=+0, +00/1/100cyc) → flat · context

**Q_relax 유의** (`Q_relax_significant`)
- 의미: 완화 용량 유의 플래그.
- 계산: threshold flag.
- 트렌드: Q_relax 유의: early=1 → late=0 (Δ=-1, -0.53580/1/100cyc) → decreasing · context

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
- 트렌드: fade b 표준오차: early=0.03028 → late=0.03028 (Δ=+0, +1.126e-171/100cyc) → flat · context

**ΔQ 유효 V범위** (`dQV_valid_V_range`)
- 의미: ΔQ 집계 전압폭.
- 계산: Vmax-Vmin used.
- 트렌드: ΔQ 유효 V범위: early=0.7715 → late=0.7715 (Δ=+0, +1.747e-17V/100cyc) → flat · context

### fade · knee

**fade 지수 b** (`fade_exponent_b`)
- 의미: SoHQ power-law 지수.
- 계산: SoHQ fit.
- 트렌드: fade 지수 b: early=0.6732 → late=0.6732 (Δ=+0, +7.504e-171/100cyc) → flat · context

**fade 지수 a** (`fade_exponent_a`)
- 의미: power-law 계수.
- 계산: SoHQ fit.
- 트렌드: fade 지수 a: early=0.002867 → late=0.002867 (Δ=+0, +4.396e-191/100cyc) → flat · context

**fade fit R2** (`fade_fit_r2`)
- 의미: fade 적합도.
- 계산: r2.
- 트렌드: fade fit R2: early=0.9796 → late=0.9796 (Δ=+0, +2.735e-161/100cyc) → flat · context

**fade SoHQ0** (`fade_sohq0`)
- 의미: fit 초기 SoHQ.
- 계산: intercept.
- 트렌드: fade SoHQ0: early=97.96 → late=97.96 (Δ=+0, +5.437e-14%/100cyc) → flat · context

**knee 사이클** (`knee_cycle_bw`)
- 의미: bilinear knee 위치.
- 계산: broken-stick SoHQ.
- 트렌드: knee 사이클: early=30 → late=30 (Δ=+0, +8.192e-15cyc/100cyc) → flat · context

**knee 심각도** (`knee_severity`)
- 의미: 전후 기울기 차이.
- 계산: slope_after-before.
- 트렌드: knee 심각도: early=0 → late=0 (Δ=+0, +01/100cyc) → flat · stable

**knee 전 기울기** (`knee_slope_before`)
- 의미: knee 이전 fade 기울기.
- 계산: bilinear.
- 트렌드: knee 전 기울기: early=-0.1479 → late=-0.1479 (Δ=+0, -3.32e-17%/cyc/100cyc) → flat · stable

**knee 후 기울기** (`knee_slope_after`)
- 의미: knee 이후 fade 기울기.
- 계산: bilinear.
- 트렌드: knee 후 기울기: early=-0.03581 → late=-0.03581 (Δ=+0, -1.356e-17%/cyc/100cyc) → flat · stable

**knee fit R2** (`knee_fit_r2`)
- 의미: knee 적합도.
- 계산: r2.
- 트렌드: knee fit R2: early=0.9979 → late=0.9979 (Δ=+0, +3.735e-161/100cyc) → flat · context

### 열화 패턴 점수

**PE activity 패턴** (`LAM_PE_pattern_score`)
- 의미: NCM activity/isolation (절대 LAM% 아님).
- 계산: mode_weights LAM_PE.
- 트렌드: PE activity 패턴: early=0.5224 → late=0.9484 (Δ=+0.426, +0.17170–1/100cyc) → increasing · matches_aging

**NE 패턴 점수** (`LAM_NE_pattern_score`)
- 의미: NE 관련 패턴 (Si-on-Gr에선 보조).
- 계산: mode_weights LAM_NE.
- 트렌드: 

**contact_loss** (`contact_loss_score`)
- 의미: 옴/스택/접촉 증거 합.
- 계산: RΩ growth 등 가중합.
- 트렌드: contact_loss: early=0.7447 → late=0.9905 (Δ=+0.2458, +0.15760–1/100cyc) → increasing · matches_aging

**LLI 패턴** (`LLI_pattern_score`)
- 의미: CE·slippage·offset 기반.
- 계산: mode_weights LLI.
- 트렌드: LLI 패턴: early=0.2804 → late=0.5708 (Δ=+0.2904, +0.10470–1/100cyc) → increasing · matches_aging

**계면 R 패턴** (`interface_R_score`)
- 의미: Rct·VE 등 계면저항.
- 계산: mode_weights interface_R.
- 트렌드: 계면 R 패턴: early=0.3832 → late=0.8502 (Δ=+0.467, +0.20280–1/100cyc) → increasing · matches_aging

**고체확산 패턴** (`solid_diffusion_score`)
- 의미: A_diff·PER·RCF.
- 계산: mode_weights solid_diffusion.
- 트렌드: 고체확산 패턴: early=0.4264 → late=0.5751 (Δ=+0.1488, -0.0010570–1/100cyc) → flat · stable

**SE 분해 패턴** (`SE_decomposition_score`)
- 의미: CE↓·Rct↑ 등 SE 분해 가설.
- 계산: mode_weights SE_decomposition.
- 트렌드: SE 분해 패턴: early=0.1159 → late=0.3538 (Δ=+0.238, +0.073470–1/100cyc) → increasing · matches_aging

**마이크로쇼트 패턴** (`microshort_score`)
- 의미: 자기방전·CE 기반 soft-short 가설.
- 계산: mode_weights microshort.
- 트렌드: 마이크로쇼트 패턴: early=0.09603 → late=0.09603 (Δ=+0, -0.28020–1/100cyc) → decreasing · opposite_aging

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
- 트렌드: contact_loss 신뢰도: early=0.52 → late=0.448 (Δ=-0.072, -0.0043570–1/100cyc) → flat · context

**LAM_PE 신뢰도** (`LAM_PE_confidence`)
- 의미: 패턴 신뢰도.
- 계산: confidence.
- 트렌드: LAM_PE 신뢰도: early=0.751 → late=0.616 (Δ=-0.135, -0.069180–1/100cyc) → decreasing · context

**LLI 신뢰도** (`LLI_confidence`)
- 의미: 패턴 신뢰도.
- 계산: confidence.
- 트렌드: LLI 신뢰도: early=0.7598 → late=0.72 (Δ=-0.03978, -0.065670–1/100cyc) → decreasing · context

### 전극 lean 가설

**PE lean** (`PE_side_score`)
- 의미: 0.75·LAM_PE + feature + FC-OCP Δhits.
- 계산: electrode_side v1.3.
- 트렌드: PE lean: early=0.4806 → late=0.8109 (Δ=+0.3302, +0.13490–1/100cyc) → increasing · matches_aging

**contact_stack** (`contact_stack_score`)
- 의미: ≈ contact_loss (R-centric).
- 계산: clip(contact_loss).
- 트렌드: contact_stack: early=0.7447 → late=0.9905 (Δ=+0.2458, +0.15760–1/100cyc) → increasing · matches_aging

**NE 가설** (`NE_side_score`)
- 의미: contact × Si co-sign.
- 계산: electrode_side.
- 트렌드: NE 가설: early=0.1638 → late=0.2996 (Δ=+0.1358, +0.08160–1/100cyc) → increasing · matches_aging

**shared 모드** (`shared_side_score`)
- 의미: LLI/interface 등 공유 모드 평균.
- 계산: shared modes mean.
- 트렌드: shared 모드: early=0.2985 → late=0.5887 (Δ=+0.2902, +0.072660–1/100cyc) → increasing · matches_aging

**Si co-sign** (`si_cosign`)
- 의미: 저SOC hyst·Q_relax·mech/chem·CV 동시 신호.
- 계산: SI_NE_COSIGN boost.
- 트렌드: Si co-sign: early=0.2 → late=0.4 (Δ=+0.2, +0.10750–1/100cyc) → increasing · matches_aging

**dominant 마진** (`dominance_margin`)
- 의미: 1위−2위 점수차.
- 계산: top-second.
- 트렌드: dominant 마진: early=0.2599 → late=0.1796 (Δ=-0.0803, -0.026560–1/100cyc) → decreasing · context

**FC-OCP 피크 hits** (`pe_peak_hits`)
- 의미: 충전 dQ/dV ↔ 합성 FC-OCP 매칭 수.
- 계산: unique nearest ±60mV.
- 트렌드: FC-OCP 피크 hits: early=1 → late=0 (Δ=-1, -0.2485count/100cyc) → decreasing · context

**FC-OCP hits Δ** (`pe_peak_hits_delta`)
- 의미: 기준 대비 hits 증가.
- 계산: hits-hits0.
- 트렌드: FC-OCP hits Δ: early=1 → late=0 (Δ=-1, -0.2485count/100cyc) → decreasing · opposite_aging

**FC-OCP hits (alias)** (`fc_ocp_hits`)
- 의미: pe_peak_hits 별칭.
- 계산: same as pe_peak_hits.
- 트렌드: FC-OCP hits (alias): early=1 → late=0 (Δ=-1, -0.2485count/100cyc) → decreasing · context

**FC-OCP hits Δ (alias)** (`fc_ocp_hits_delta`)
- 의미: pe_peak_hits_delta 별칭.
- 계산: same as pe_peak_hits_delta.
- 트렌드: FC-OCP hits Δ (alias): early=1 → late=0 (Δ=-1, -0.2485count/100cyc) → decreasing · opposite_aging

**전극진단 신뢰도** (`electrode_confidence`)
- 의미: coverage·분리·OCP 가용성.
- 계산: 0.35cov+0.35sep+0.30ocp.
- 트렌드: 전극진단 신뢰도: early=0.825 → late=0.8766 (Δ=+0.05161, +0.042380–1/100cyc) → flat · context
