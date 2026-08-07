## DOE2 핵심 2지표: knee × dV/dQ SOC0

양극 동일 · 음극 상이. **사이클 변곡점(knee)** 과 **방전 dV/dQ @SOC0(저SOC cliff)** 가 anode arm을 가르는 1차 관측량.

- SJ900 (excl Ch025): M01Ch022, M01Ch024
- SJ1300: M01Ch010, M01Ch011, M01Ch012

### 1) Knee (bilinear on routine SoHQ)
- **SJ900**: knee ≈ 320 cyc (M01Ch022=350, M01Ch024=290); severity=0.022; SoHQ@knee≈80.8%; end≈64.9%
- **SJ1300**: knee ≈ 253 cyc (M01Ch010=250, M01Ch011=260, M01Ch012=250); severity=0.0422; SoHQ@knee≈88.8%; end≈74.0%

### 2) dV/dQ @ SOC0 (저SOC cliff intensity)
- **SJ900**: SOC0 0.093 → 0.17 (Δ=+0.0774); cliff_width 4.50 → 6.25; ΔSOC0 half-cycle ≈ 480
- **SJ1300**: SOC0 0.113 → 0.075 (Δ=-0.0378); cliff_width 4.56 → 3.45; ΔSOC0 half-cycle ≈ 47

### 교차 해석
- **SJ900**: knee 늦음(~320) · SOC0 **후반에 커짐**(cliff 넓어짐) · ΔSOC0 절반은 knee **이후**(~480).
- **SJ1300**: knee 이름(~253)·더 급함 · SOC0는 **초반부터 줄고** cliff 좁아짐 · ΔSOC0 절반은 knee **이전**(~50).
- 같은 양극인데도 SOC0 궤적 부호가 반대 → **음극 쪽 저SOC 형상**이 knee 타이밍과 함께 arm을 구분.

### 보조 패턴 (Δ late−early, excl Ch025)
- `LLI`: SJ900 +0.0522 vs SJ1300 +0.381
- `LAM_PE activity`: SJ900 +0.371 vs SJ1300 +0.321
- `contact_loss`: SJ900 +0.211 vs SJ1300 +0.183
- `si_cosign`: SJ900 +0.2 vs SJ1300 +0.0667
- `PE_side`: SJ900 +0.214 vs SJ1300 +0.279

> dchg_dVdQ_SOC0 = 방전 말단(SOC≈0) |dV/dQ|. cliff_width = mid 대비 2× 넘는 Q폭. Ch025는 knee 평균에서 제외.