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