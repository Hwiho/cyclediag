## 트렌드 요약 — M02Ch109

- 유효 지표: 32개 · aging 방향 일치 15 · 반대 1

### 하락 트렌드 (상위)
- LAM 곡선 proxy: early=-2.01 → late=-12.04 (Δ=-10.03, -4.231%/100cyc) → decreasing · context
- 방전 플래토 폭: early=17.18 → late=14.39 (Δ=-2.783, -1.057Q-units/100cyc) → decreasing · matches_aging
- RΩ 성장률 /100cyc: early=1.097 → late=0.7898 (Δ=-0.3076, -0.3082mΩ/100cyc/100cyc) → decreasing · context
- 방전 플래토 ΔV: early=-0.0316 → late=-0.1041 (Δ=-0.07246, -0.03168V/100cyc) → decreasing · context
- 저SOC 히스테리시스: early=0.08696 → late=0.0429 (Δ=-0.04406, -0.01859V/100cyc) → decreasing · opposite_aging

### 상승 트렌드 (상위)
- 옴 저항 (SOC50): early=1.107 → late=2.765 (Δ=+1.658, +0.7947mΩ/100cyc) → increasing · matches_aging
- 기계/화학 비: early=1.51 → late=3.068 (Δ=+1.559, +0.78761/100cyc) → increasing · matches_aging
- LLI 곡선 proxy: early=-0.08575 → late=1.893 (Δ=+1.979, +0.601%/100cyc) → increasing · context
- 완화 용량 회복: early=-0.4599 → late=0.1079 (Δ=+0.5678, +0.2924%/100cyc) → increasing · matches_aging
- 계면 R 패턴: early=0.4033 → late=0.8515 (Δ=+0.4483, +0.17430–1/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- 저SOC 히스테리시스: early=0.08696 → late=0.0429 (Δ=-0.04406, -0.01859V/100cyc) → decreasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.