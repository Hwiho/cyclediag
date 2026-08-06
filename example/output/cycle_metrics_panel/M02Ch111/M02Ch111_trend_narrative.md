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