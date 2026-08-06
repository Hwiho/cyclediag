## 트렌드 요약 — M02Ch103

- 유효 지표: 358개 · aging 방향 일치 47 · 반대 10

### 하락 트렌드 (상위)
- 국소 CE(20): early=528.7 → late=273.2 (Δ=-255.4, -85.37%/100cyc) → decreasing · matches_aging
- 방전후 휴지 완화 τ: early=369.3 → late=291 (Δ=-78.3, -37.29s/100cyc) → decreasing · context
- 방전후 완화 τ Δvs기준: early=9.884 → late=-68.41 (Δ=-78.3, -37.29s/100cyc) → decreasing · context
- 충전 에너지: early=243.6 → late=204.5 (Δ=-39.03, -14.6Wh/100cyc) → decreasing · matches_aging
- LAM 곡선 proxy: early=-3.11 → late=-17.48 (Δ=-14.37, -5.717%/100cyc) → decreasing · context

### 상승 트렌드 (상위)
- fit 잔차 max: early=55.92 → late=152.7 (Δ=+96.79, +42.63mV/100cyc) → increasing · matches_aging
- EoC 방전 10s 증가%: early=28.76 → late=49.05 (Δ=+20.29, +13.58%/100cyc) → increasing · matches_aging
- EoC 방전 30s 증가%: early=22.07 → late=43.82 (Δ=+21.75, +12.44%/100cyc) → increasing · matches_aging
- EoC 방전 60s 증가%: early=17.67 → late=38.96 (Δ=+21.29, +11.32%/100cyc) → increasing · matches_aging
- CV 시간: early=0 → late=0 (Δ=+0, +8.492s/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- 쿨롱 비효율: early=-7.902 → late=-17.31 (Δ=-9.409, -3.596%/100cyc) → decreasing · opposite_aging
- CI /시간: early=-1.548 → late=-3.525 (Δ=-1.977, -0.7513%/h/100cyc) → decreasing · opposite_aging
- 에너지 손실: early=8.32 → late=-1.791 (Δ=-10.11, -3.476Wh/100cyc) → decreasing · opposite_aging
- dSoHQ/dN: early=-0.1665 → late=-0.02386 (Δ=+0.1426, +0.1581%/cyc/100cyc) → increasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.