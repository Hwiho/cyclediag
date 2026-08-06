## 트렌드 요약 — M02Ch110

- 유효 지표: 358개 · aging 방향 일치 47 · 반대 13

### 하락 트렌드 (상위)
- 충전 dV/dQ 피크2 Q: early=59.46 → late=59.46 (Δ=+0, -68.81Ah/100cyc) → decreasing · context
- 국소 CE(20): early=495.5 → late=293.3 (Δ=-202.2, -62.24%/100cyc) → decreasing · matches_aging
- 충전 dQ/dV 피크4 높이: early=94.9 → late=94.9 (Δ=+0, -33.67Ah/V/100cyc) → decreasing · context
- 충전 에너지: early=247.6 → late=194.5 (Δ=-53.1, -21.2Wh/100cyc) → decreasing · matches_aging
- 방전후 완화 τ Δvs기준: early=-15.09 → late=-38.71 (Δ=-23.62, -16.3s/100cyc) → decreasing · context

### 상승 트렌드 (상위)
- 충전 dQ/dV 피크1 높이: early=81.12 → late=78.59 (Δ=-2.528, +80.17Ah/V/100cyc) → increasing · context
- fit 잔차 max: early=29.09 → late=199.9 (Δ=+170.8, +59.84mV/100cyc) → increasing · matches_aging
- 충전후 휴지 완화 τ: early=535.2 → late=607.8 (Δ=+72.58, +36.39s/100cyc) → increasing · context
- 충전후 완화 τ Δvs기준: early=9.997 → late=82.58 (Δ=+72.58, +36.39s/100cyc) → increasing · context
- EoC 방전 10s 증가%: early=21.24 → late=36.42 (Δ=+15.18, +15.76%/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- CV 충전용량: early=0 → late=0 (Δ=+0, -0.01405Ah/100cyc) → decreasing · opposite_aging
- CC비 Δ: early=0 → late=0 (Δ=+0, +0.024081/100cyc) → increasing · opposite_aging
- CV 시간: early=0 → late=0 (Δ=+0, -1.678s/100cyc) → decreasing · opposite_aging
- 쿨롱 효율: early=102.1 → late=116.9 (Δ=+14.79, +6.128%/100cyc) → increasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.