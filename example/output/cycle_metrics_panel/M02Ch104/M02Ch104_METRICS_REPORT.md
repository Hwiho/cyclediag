# 사이클별 지표 패널 — M02Ch104

## 트렌드 요약 — M02Ch104

- 유효 지표: 32개 · aging 방향 일치 14 · 반대 1

### 하락 트렌드 (상위)
- LAM 곡선 proxy: early=-2.983 → late=-16.28 (Δ=-13.3, -5.282%/100cyc) → decreasing · context
- LLI 곡선 proxy: early=-0.6179 → late=-2.925 (Δ=-2.307, -1.265%/100cyc) → decreasing · context
- 방전 플래토 폭: early=16.87 → late=14.8 (Δ=-2.067, -1.075Q-units/100cyc) → decreasing · matches_aging
- RΩ 성장률 /100cyc: early=0.7957 → late=0.4668 (Δ=-0.3289, -0.3314mΩ/100cyc/100cyc) → decreasing · context
- 방전 플래토 ΔV: early=-0.03799 → late=-0.08104 (Δ=-0.04305, -0.01868V/100cyc) → decreasing · context

### 상승 트렌드 (상위)
- 옴 저항 (SOC50): early=1.394 → late=2.374 (Δ=+0.9802, +0.4981mΩ/100cyc) → increasing · matches_aging
- 기계/화학 비: early=1.924 → late=2.519 (Δ=+0.5948, +0.35921/100cyc) → increasing · matches_aging
- 완화 용량 회복: early=-0.5876 → late=-0.2802 (Δ=+0.3073, +0.2126%/100cyc) → increasing · matches_aging
- 계면 R 패턴: early=0.4752 → late=0.8706 (Δ=+0.3954, +0.14840–1/100cyc) → increasing · matches_aging
- PE activity 패턴: early=0.6051 → late=0.9263 (Δ=+0.3212, +0.14480–1/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- 저SOC 히스테리시스: early=0.07466 → late=0.04496 (Δ=-0.0297, -0.01201V/100cyc) → decreasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.

## 지표 카탈로그 + 트렌드

### 용량 · 효율

**용량 유지율** (`SoHQ`)
- 의미: 기준 대비 방전용량 유지율. fade/knee의 1차 관측량.
- 계산: Q_dchg(cycle) / Q_baseline × 100 (routine 0.5C).
- 트렌드: 용량 유지율: early=97.11 → late=87.69 (Δ=-9.425, -3.446%/100cyc) → flat · stable

**쿨롱 효율** (`CE`)
- 의미: 충전 대비 방전용량 비. LLI·부반응 힌트.
- 계산: Q_dchg / Q_chg × 100 (이상치 >102% 또는 <85%는 진단에서 제외).
- 트렌드: 쿨롱 효율: early=105.6 → late=117.5 (Δ=+11.94, +5.162%/100cyc) → flat · stable

**전압 효율** (`VE`)
- 의미: 에너지 효율의 전압 측. 저항·분극 증가 시 하락.
- 계산: E_dchg / E_chg (Wh).
- 트렌드: 전압 효율: early=0.8907 → late=0.8593 (Δ=-0.03135, -0.013621/100cyc) → flat · stable

**에너지 효율** (`EE`)
- 의미: 충·방전 에너지 비.
- 계산: E_dchg / E_chg.
- 트렌드: 에너지 효율: early=0.9481 → late=1.009 (Δ=+0.06136, +0.029831/100cyc) → flat · stable

**완화 용량 회복** (`Q_relax_pct`)
- 의미: DCIR/RPT 전후 휴지로 회복되는 용량 분율. Si chemo-mech co-sign.
- 계산: DCIR 블록 전후 Q 차이 / Q × 100, routine에 forward-fill.
- 트렌드: 완화 용량 회복: early=-0.5876 → late=-0.2802 (Δ=+0.3073, +0.2126%/100cyc) → increasing · matches_aging

### 저항 · 분해

**옴 저항 (SOC50)** (`R_ohmic_soc50`)
- 의미: DCIR 펄스 early √t 외삽 t→0 절편. 순수 옴이 아니라 초기 비옴 성분 proxy.
- 계산: R(t)=|ΔV|/|I|; t∈[0,0.3]s 에서 R vs √t 회귀 절편. SOC50 블록 → forward-fill.
- 트렌드: 옴 저항 (SOC50): early=1.394 → late=2.374 (Δ=+0.9802, +0.4981mΩ/100cyc) → increasing · matches_aging

**전하전달 저항 (SOC50)** (`R_ct_soc50`)
- 의미: 중간 시간대 잔차의 지수 포화항. 계면/화학 저항 proxy (Cdl 직접 추정 아님).
- 계산: resid = R−RΩ−A√t; t∈[0.3,10]s 에서 Rct(1−e^(−t/τ)) fit.
- 트렌드: 전하전달 저항 (SOC50): early=0.7244 → late=0.9425 (Δ=+0.2181, +0.09305mΩ/100cyc) → increasing · matches_aging

**Rct 시정수 τ** (`tau_ct_soc50`)
- 의미: R(t) 잔차 fit의 유효 시정수. τ≈Rct·Cdl 가설이지만 Cdl은 분리하지 않음.
- 계산: curve_fit 초기값 2s, bounds [0.05, 20]; 데이터로 추정.
- 트렌드: 

**기계/화학 비** (`mech_vs_chem_ratio`)
- 의미: 옴(스택·접촉) vs 전하전달(계면) 상대 비중.
- 계산: R_ohmic_soc50 / R_ct_soc50.
- 트렌드: 기계/화학 비: early=1.924 → late=2.519 (Δ=+0.5948, +0.35921/100cyc) → increasing · matches_aging

**RΩ 성장률 /100cyc** (`R_ohmic_growth_100`)
- 의미: 기준 DCIR 대비 100사이클당 옴 저항 증가율. 레벨(RΩ)과 별개 — 감속해도 RΩ는 계속 상승 가능.
- 계산: (RΩ - RΩ0) / ((cyc - cyc0)/100).
- 트렌드: RΩ 성장률 /100cyc: early=0.7957 → late=0.4668 (Δ=-0.3289, -0.3314mΩ/100cyc/100cyc) → decreasing · context

**RΩ / R30s 분율** (`R_ohmic_frac_soc50`)
- 의미: 30s 총저항 중 옴 성분 비중.
- 계산: R_ohmic / R_30s_total @ SOC50.
- 트렌드: 

**EoC 방전 10s DCIR** (`EoC_dchgR_10s`)
- 의미: 충전 종료 후 방전 시작 10초 시점 ΔV/I. Rct·확산 포함 총 DCIR.
- 계산: |V0−V(10s)|/|I|×1000. 순수 RΩ 아님.
- 트렌드: EoC 방전 10s DCIR: early=0.1714 → late=0.2353 (Δ=+0.06394, +0.02685mΩ/100cyc) → increasing · matches_aging

### 곡선 형상 · dQ/dV

**저SOC 히스테리시스** (`hyst_area_low`)
- 의미: 저SOC 충·방전 전압 면적. Si-on-Gr chemo-mech 지표.
- 계산: V–Q 히스테리시스를 SOC 밴드별로 적분 (low band).
- 트렌드: 저SOC 히스테리시스: early=0.07466 → late=0.04496 (Δ=-0.0297, -0.01201V/100cyc) → decreasing · opposite_aging

**고SOC 히스테리시스** (`hyst_area_high`)
- 의미: 고SOC 히스테리시스. PE activity 보조 증거.
- 계산: 히스테리시스 high-SOC band 면적.
- 트렌드: 고SOC 히스테리시스: early=0.2198 → late=0.2408 (Δ=+0.02105, +0.008549V/100cyc) → flat · stable

**방전 플래토 폭** (`dchg_plateau_width`)
- 의미: 방전 플래토 구간 폭. 좁아지면 PE isolation/activity 패턴.
- 계산: 방전 V 플래토 검출 후 Q 폭.
- 트렌드: 방전 플래토 폭: early=16.87 → late=14.8 (Δ=-2.067, -1.075Q-units/100cyc) → decreasing · matches_aging

**방전 플래토 ΔV** (`delta_dchg_plateau_V`)
- 의미: 기준 대비 방전 플래토 전압 이동.
- 계산: plateau_V(cycle) − plateau_V(baseline).
- 트렌드: 방전 플래토 ΔV: early=-0.03799 → late=-0.08104 (Δ=-0.04305, -0.01868V/100cyc) → decreasing · context

**충전 dQ/dV 피크1 V** (`chg_dQdV_peak1_V`)
- 의미: 충전 IC 1번 피크 위치. FC-OCP 매칭·위상 이동 추적.
- 계산: Q 보간 → SG → find_peaks.
- 트렌드: 충전 dQ/dV 피크1 V: early=3.741 → late=3.784 (Δ=+0.043, +0.01064V/100cyc) → flat · context

**LAM 곡선 proxy** (`LAM_curve_proxy`)
- 의미: 기준 V–Q 대비 scale 축소 proxy. 절대 LAM% 아님; 부호·bound 포화에 주의.
- 계산: (1 - fit_scale) * 100 (discharge 3-param fit). scale>1 이면 음수.
- 트렌드: LAM 곡선 proxy: early=-2.983 → late=-16.28 (Δ=-13.3, -5.282%/100cyc) → decreasing · context

**LLI 곡선 proxy** (`LLI_curve_proxy`)
- 의미: 기준 대비 Q축 offset. 절대 LLI% 아님.
- 계산: fit_offset / Q_max × 100.
- 트렌드: LLI 곡선 proxy: early=-0.6179 → late=-2.925 (Δ=-2.307, -1.265%/100cyc) → decreasing · context

### 수송 · rate

**Rate capability factor** (`RCF`)
- 의미: 0.5C 용량 / 가까운 C/3 RPT 용량. rate 손실 시 하락.
- 계산: Q_0.5C(N) / Q_C/3(nearest RPT).
- 트렌드: Rate capability factor: early=0.9711 → late=0.9569 (Δ=-0.01422, -1.5e-061/100cyc) → flat · stable

**분극 효율 비** (`PER`)
- 의미: 과전위 대비 DCIR 스케일. 수송 제한 시 변화.
- 계산: η(SOC50) / (ΔI · R_DCIR_50).
- 트렌드: 

**최대 과전위 η** (`eta_max`)
- 의미: C/3 vs 0.5C 동일 Q축 최대 전압차.
- 계산: 동일 Q에서 |V_C3 − V_0.5C| 최댓값.
- 트렌드: 

**η 최댓값 SOC** (`eta_argmax_SOC`)
- 의미: η가 최대인 SOC. 고SOC면 PE, 저SOC면 NE 쪽 힌트.
- 계산: argmax_SOC of η(SOC).
- 트렌드: 

### 열화 패턴 점수

**PE activity 패턴** (`LAM_PE_pattern_score`)
- 의미: NCM 이차 고립/activity 패턴. 절대 LAM% 금지.
- 계산: plateau·dQdV·LAM_curve_proxy·dQV_log_var 가중합 (mode_weights).
- 트렌드: PE activity 패턴: early=0.6051 → late=0.9263 (Δ=+0.3212, +0.14480–1/100cyc) → increasing · matches_aging

**접촉/스택 손실** (`contact_loss_score`)
- 의미: 옴 성장·분율·mech/chem 증가 증거 합. 전극 미분해.
- 계산: R_ohmic_growth, ΔRΩ, RΩ_frac, EoC_10s, mech/chem 가중합.
- 트렌드: 접촉/스택 손실: early=0.8664 → late=0.9423 (Δ=+0.0759, +0.04940–1/100cyc) → increasing · matches_aging

**LLI 패턴** (`LLI_pattern_score`)
- 의미: CE·slippage·곡선 offset 기반 LLI 가설 점수.
- 계산: CE↓, CI↑, restV/cutoff margin, LLI_curve_proxy 등.
- 트렌드: LLI 패턴: early=0.3694 → late=0.6369 (Δ=+0.2675, +0.12010–1/100cyc) → increasing · matches_aging

**계면 R 패턴** (`interface_R_score`)
- 의미: Rct·τ·VE 하락 등 계면저항 성장 가설.
- 계산: R_ct↑, tau_ct↑, VE↓, EoC_60s 등.
- 트렌드: 계면 R 패턴: early=0.4752 → late=0.8706 (Δ=+0.3954, +0.14840–1/100cyc) → increasing · matches_aging

**고체확산 제한** (`solid_diffusion_score`)
- 의미: A_diff·PER·RCF 기반 확산/수송 제한.
- 계산: A_diff↑, PER↑, RCF↓ 등.
- 트렌드: 고체확산 제한: early=0.5208 → late=0.6973 (Δ=+0.1764, +0.026140–1/100cyc) → flat · stable

### 전극 lean 가설

**PE lean 점수** (`PE_side_score`)
- 의미: LAM_PE_pattern + feature boost + FC-OCP Δhits.
- 계산: 0.75·LAM_PE + 0.20·PE_boost + peak_boost.
- 트렌드: PE lean 점수: early=0.5038 → late=0.7947 (Δ=+0.2909, +0.12810–1/100cyc) → increasing · matches_aging

**contact_stack lean** (`contact_stack_score`)
- 의미: contact_loss를 dominant 경쟁에 넣는 이름. ≈ contact_loss_score.
- 계산: clip(contact_loss_score, 0, 1).
- 트렌드: contact_stack lean: early=0.8664 → late=0.9423 (Δ=+0.0759, +0.04940–1/100cyc) → increasing · matches_aging

**NE 가설 점수** (`NE_side_score`)
- 의미: contact × Si chemo-mech co-sign. Si 없으면 NE 확정 금지.
- 계산: 0.55·contact·(0.25+0.75·si) + 0.30·NE_boost·si.
- 트렌드: NE 가설 점수: early=0.1921 → late=0.285 (Δ=+0.09298, +0.039660–1/100cyc) → increasing · matches_aging

**Si co-sign** (`si_cosign`)
- 의미: 저SOC hyst·Q_relax·mech/chem·CV 등 Si chemo-mech 동시 신호.
- 계산: SI_NE_COSIGN feature boost (baseline 대비 ↑ 비율).
- 트렌드: Si co-sign: early=0.2 → late=0.4 (Δ=+0.2, +0.070320–1/100cyc) → increasing · matches_aging
