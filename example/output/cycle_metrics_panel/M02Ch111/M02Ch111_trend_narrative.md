## 트렌드 요약 — M02Ch111

- 유효 지표: 32개 · aging 방향 일치 14 · 반대 2

### 하락 트렌드 (상위)
- LAM 곡선 proxy: early=-1.959 → late=-12.31 (Δ=-10.36, -4.262%/100cyc) → decreasing · context
- 방전 플래토 폭: early=17.42 → late=14.33 (Δ=-3.09, -1.201Q-units/100cyc) → decreasing · matches_aging
- RΩ 성장률 /100cyc: early=1.104 → late=0.7864 (Δ=-0.3172, -0.3213mΩ/100cyc/100cyc) → decreasing · context
- 방전 플래토 ΔV: early=-0.03324 → late=-0.1065 (Δ=-0.07325, -0.03213V/100cyc) → decreasing · context
- 저SOC 히스테리시스: early=0.08677 → late=0.0439 (Δ=-0.04287, -0.01806V/100cyc) → decreasing · opposite_aging

### 상승 트렌드 (상위)
- 쿨롱 효율: early=101.9 → late=116.9 (Δ=+14.98, +6.03%/100cyc) → increasing · opposite_aging
- 옴 저항 (SOC50): early=1.092 → late=2.744 (Δ=+1.651, +0.7975mΩ/100cyc) → increasing · matches_aging
- 기계/화학 비: early=1.48 → late=3.043 (Δ=+1.563, +0.79681/100cyc) → increasing · matches_aging
- LLI 곡선 proxy: early=-0.2132 → late=1.26 (Δ=+1.473, +0.4021%/100cyc) → increasing · context
- 완화 용량 회복: early=-0.4453 → late=0.01934 (Δ=+0.4647, +0.2544%/100cyc) → increasing · matches_aging

### 기대 aging과 반대
- 쿨롱 효율: early=101.9 → late=116.9 (Δ=+14.98, +6.03%/100cyc) → increasing · opposite_aging
- 저SOC 히스테리시스: early=0.08677 → late=0.0439 (Δ=-0.04287, -0.01806V/100cyc) → decreasing · opposite_aging

> slope = 선형회귀 ×100사이클. early/late = 앞·뒤 5포인트 median (routine_05c). 패턴 점수는 0–1 가설이며 절대 LAM%가 아닙니다.