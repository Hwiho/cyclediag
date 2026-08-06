## 트렌드 요약 — M02Ch110

- 유효 지표: 32개 · aging 방향 일치 14 · 반대 2

### 하락 트렌드 (상위)
- LAM 곡선 proxy: early=-1.997 → late=-11.94 (Δ=-9.94, -3.998%/100cyc) → decreasing · context
- 방전 플래토 폭: early=17.11 → late=14.08 (Δ=-3.029, -1.019Q-units/100cyc) → decreasing · matches_aging
- RΩ 성장률 /100cyc: early=1.033 → late=0.7356 (Δ=-0.2978, -0.2984mΩ/100cyc/100cyc) → decreasing · context
- 방전 플래토 ΔV: early=-0.03086 → late=-0.101 (Δ=-0.07014, -0.02987V/100cyc) → decreasing · context
- 저SOC 히스테리시스: early=0.08764 → late=0.04561 (Δ=-0.04203, -0.01711V/100cyc) → decreasing · opposite_aging

### 상승 트렌드 (상위)
- 쿨롱 효율: early=102.1 → late=116.9 (Δ=+14.79, +6.128%/100cyc) → increasing · opposite_aging
- 기계/화학 비: early=1.473 → late=2.975 (Δ=+1.501, +0.76211/100cyc) → increasing · matches_aging
- 옴 저항 (SOC50): early=1.07 → late=2.615 (Δ=+1.545, +0.7422mΩ/100cyc) → increasing · matches_aging
- LLI 곡선 proxy: early=-0.04551 → late=1.874 (Δ=+1.919, +0.4965%/100cyc) → increasing · context
- 완화 용량 회복: early=-0.4859 → late=0.0484 (Δ=+0.5343, +0.2864%/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- 쿨롱 효율: early=102.1 → late=116.9 (Δ=+14.79, +6.128%/100cyc) → increasing · opposite_aging
- 저SOC 히스테리시스: early=0.08764 → late=0.04561 (Δ=-0.04203, -0.01711V/100cyc) → decreasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.