## 트렌드 요약 — M02Ch105

- 유효 지표: 358개 · aging 방향 일치 44 · 반대 13

### 하락 트렌드 (상위)
- 충전 dQ/dV 피크1 높이: early=74.98 → late=96.02 (Δ=+21.04, -1188Ah/V/100cyc) → decreasing · context
- CV 시정수: early=1048 → late=1048 (Δ=+0, -251s/100cyc) → decreasing · opposite_aging
- 국소 CE(20): early=544.7 → late=269 (Δ=-275.7, -89.99%/100cyc) → decreasing · matches_aging
- 방전후 휴지 완화 τ: early=370 → late=297.6 (Δ=-72.35, -35.23s/100cyc) → decreasing · context
- 방전후 완화 τ Δvs기준: early=6.491 → late=-65.86 (Δ=-72.35, -35.23s/100cyc) → decreasing · context

### 상승 트렌드 (상위)
- 충전 dQ/dV 피크2 높이: early=91.75 → late=198.4 (Δ=+106.7, +108.1Ah/V/100cyc) → increasing · context
- 충전 dQ/dV 피크3 높이: early=83.38 → late=82.31 (Δ=-1.073, +66.37Ah/V/100cyc) → increasing · context
- fit 잔차 max: early=56.47 → late=145.3 (Δ=+88.82, +28.71mV/100cyc) → increasing · matches_aging
- 충전후 완화 τ Δvs기준: early=-6.131 → late=27.12 (Δ=+33.25, +15.24s/100cyc) → increasing · context
- EoC 방전 10s 증가%: early=27.84 → late=51.35 (Δ=+23.51, +13.84%/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- CV 충전용량: early=0 → late=0 (Δ=+0, -0.1916Ah/100cyc) → decreasing · opposite_aging
- CC비 Δ: early=0 → late=0 (Δ=+0, +0.25931/100cyc) → increasing · opposite_aging
- CV 시간: early=0 → late=0 (Δ=+0, -31.81s/100cyc) → decreasing · opposite_aging
- CV 시정수: early=1048 → late=1048 (Δ=+0, -251s/100cyc) → decreasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.