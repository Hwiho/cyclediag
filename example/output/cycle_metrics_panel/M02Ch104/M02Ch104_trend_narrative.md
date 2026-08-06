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