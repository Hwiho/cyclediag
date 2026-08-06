# 열화 구간별 전극 가설 진단 v1.3 — M01Ch022

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- Chemistry: **Si-on-Gr** (Si coating on graphite, exposed Gr 가능) · **NCM82 secondary**
- Methodology: electrode_side_v1_3 · FC-OCP charge unique Δhits · R-centric contact_stack · Si co-sign NE
- Protocol dual-track: routine 0.5C 궤적 + C/3 RPT 앵커 (중간 SoHQ bump = RPT)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 90 cycles (routine=60, rpt_c3=12); 세그먼트는 routine only · SoHQ≥50

## 구간 요약 (routine 0.5C)

### Seg 1: cycle 7–100 · 양극(PE) 가설 우위
- SoHQ(routine): 96.3% → 92.2% (13 points)
- 점수: PE=0.59 / contact_stack=0.12 / NE_hyp=0.03 / shared=0.39 (conf=0.75)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.22
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.70, contact_loss=0.12, LLI=0.42

### Seg 2: cycle 120–210 · 혼합/근소
- SoHQ(routine): 91.6% → 88.0% (10 points)
- 점수: PE=0.61 / contact_stack=0.62 / NE_hyp=0.19 / shared=0.46 (conf=0.57)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.40
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.69, contact_loss=0.62, LLI=0.53

### Seg 3: cycle 220–340 · 양극(PE) 가설 우위
- SoHQ(routine): 87.5% → 81.1% (12 points)
- 점수: PE=0.60 / contact_stack=0.46 / NE_hyp=0.14 / shared=0.52 (conf=0.70)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.40
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.68, contact_loss=0.46, LLI=0.58

### Seg 4: cycle 350–564 · 양극(PE) 가설 우위
- SoHQ(routine): 80.3% → 65.4% (25 points)
- 점수: PE=0.58 / contact_stack=0.25 / NE_hyp=0.08 / shared=0.49 (conf=0.66)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.41
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.75, contact_loss=0.25, LLI=0.54

## C/3 RPT 앵커 (이중 트랙)

중간 궤적의 SoHQ 상승 스파이크는 **C/3(~0.33C) RPT 용량**입니다. rate가 낮아 분극이 작아 보이므로 0.5C routine보다 높게 찍히는 것이 정상입니다. fade/lean/세그먼트에는 넣지 않고 RCF·η·열역학 용량 트랙으로만 씁니다.

| cycle | SoHQ_C/3 | prev routine | SoHQ_0.5C | Δ(RPT−routine) |
|------:|---------:|-------------:|----------:|---------------:|
| 2 | 100.6 | — | n/a | n/a |
| 3 | 100.0 | — | n/a | n/a |
| 107 | 95.5 | 100 | 92.2 | +3.2 |
| 108 | 95.4 | 100 | 92.2 | +3.2 |
| 212 | 92.7 | 210 | 88.0 | +4.8 |
| 213 | 92.7 | 210 | 88.0 | +4.7 |
| 317 | 88.8 | 310 | 83.0 | +5.9 |
| 318 | 89.0 | 310 | 83.0 | +6.1 |
| 422 | 79.5 | 420 | 73.2 | +6.3 |
| 423 | 80.3 | 420 | 73.2 | +7.1 |
| 527 | 72.2 | 520 | 67.1 | +5.1 |
| 528 | 72.7 | 520 | 67.1 | +5.6 |

## 수명 단계 롤업 (routine only)

- **early (1/3)** cyc 7–180: PE=0.60 contact=0.29 NE_hyp=0.08 → majority **양극(PE) 가설 우위** (SoHQ 96→89%)
- **mid (1/3)** cyc 190–390: PE=0.59 contact=0.45 NE_hyp=0.14 → majority **혼합/근소** (SoHQ 89→76%)
- **late (1/3)** cyc 400–564: PE=0.59 contact=0.23 NE_hyp=0.07 → majority **양극(PE) 가설 우위** (SoHQ 75→65%)

## 사이클 궤적

| cycle | role | SoHQ | dominant | PE | contact | NE_hyp | LAM_PE | contact_loss | note |
|------:|:-----|-----:|:---------|---:|--------:|-------:|-------:|-------------:|:-----|
| 2 | rpt_c3 | 100.6 | PE | 0.20 | 0.00 | 0.00 | 0.05 | 0.00 | C/3 RPT anchor (not fade spike) |
| 3 | rpt_c3 | 100.0 | unknown | 0.16 | 0.00 | 0.00 | 0.00 | 0.00 | C/3 RPT anchor (not fade spike) |
| 7 | routine_05c | 96.3 | PE | 0.64 | 0.00 | 0.00 | 0.72 | 0.00 | PE activity/isolation pattern leads (PE= |
| 8 | routine_05c | 96.1 | PE | 0.55 | 0.00 | 0.00 | 0.63 | 0.00 | PE activity/isolation pattern leads (PE= |
| 9 | routine_05c | 95.9 | PE | 0.62 | 0.00 | 0.00 | 0.73 | 0.00 | PE activity/isolation pattern leads (PE= |
| 10 | routine_05c | 95.8 | PE | 0.71 | 0.00 | 0.00 | 0.83 | 0.00 | PE activity/isolation pattern leads (PE= |
| 20 | routine_05c | 95.0 | PE | 0.51 | 0.00 | 0.00 | 0.57 | 0.00 | PE activity/isolation pattern leads (PE= |
| 30 | routine_05c | 94.6 | mixed | 0.39 | 0.00 | 0.00 | 0.45 | 0.00 | Mixed signals (PE=0.39, contact=0.00, NE |
| 40 | routine_05c | 94.3 | mixed | 0.48 | 0.00 | 0.00 | 0.58 | 0.00 | Mixed signals (PE=0.48, contact=0.00, NE |
| 50 | routine_05c | 94.0 | mixed | 0.48 | 0.00 | 0.00 | 0.57 | 0.00 | Mixed signals (PE=0.48, contact=0.00, NE |
| 60 | routine_05c | 93.7 | PE | 0.51 | 0.00 | 0.00 | 0.61 | 0.00 | PE activity/isolation pattern leads (PE= |
| 70 | routine_05c | 93.4 | PE | 0.61 | 0.00 | 0.00 | 0.75 | 0.00 | PE activity/isolation pattern leads (PE= |
| 80 | routine_05c | 93.0 | PE | 0.75 | 0.54 | 0.16 | 0.87 | 0.54 | PE activity/isolation pattern leads (PE= |
| 90 | routine_05c | 92.6 | PE | 0.70 | 0.51 | 0.11 | 0.87 | 0.51 | PE activity/isolation pattern leads (PE= |
| 100 | routine_05c | 92.2 | PE | 0.78 | 0.48 | 0.10 | 0.97 | 0.48 | PE activity/isolation pattern leads (PE= |
| 107 | rpt_c3 | 95.5 | PE | 0.49 | 0.00 | 0.00 | 0.54 | 0.00 | C/3 RPT anchor (not fade spike) |
| 108 | rpt_c3 | 95.4 | PE | 0.41 | 0.00 | 0.00 | 0.44 | 0.00 | C/3 RPT anchor (not fade spike) |
| 120 | routine_05c | 91.6 | mixed | 0.65 | 0.61 | 0.18 | 0.76 | 0.61 | Mixed signals (PE=0.65, contact=0.61, NE |
| 130 | routine_05c | 91.2 | mixed | 0.60 | 0.62 | 0.19 | 0.74 | 0.62 | Mixed signals (PE=0.60, contact=0.62, NE |
| 140 | routine_05c | 90.8 | mixed | 0.58 | 0.61 | 0.18 | 0.67 | 0.61 | Mixed signals (PE=0.58, contact=0.61, NE |
| 150 | routine_05c | 90.4 | mixed | 0.58 | 0.62 | 0.19 | 0.67 | 0.62 | Mixed signals (PE=0.58, contact=0.62, NE |
| 160 | routine_05c | 90.2 | mixed | 0.61 | 0.61 | 0.18 | 0.68 | 0.61 | Mixed signals (PE=0.61, contact=0.61, NE |
| 170 | routine_05c | 89.8 | mixed | 0.61 | 0.62 | 0.19 | 0.68 | 0.62 | Mixed signals (PE=0.61, contact=0.62, NE |
| 180 | routine_05c | 89.3 | mixed | 0.61 | 0.62 | 0.19 | 0.68 | 0.62 | Mixed signals (PE=0.61, contact=0.62, NE |
| 190 | routine_05c | 88.9 | mixed | 0.64 | 0.63 | 0.19 | 0.67 | 0.63 | Mixed signals (PE=0.64, contact=0.63, NE |
| 200 | routine_05c | 88.4 | mixed | 0.61 | 0.62 | 0.19 | 0.68 | 0.62 | Mixed signals (PE=0.61, contact=0.62, NE |
| 210 | routine_05c | 88.0 | mixed | 0.63 | 0.61 | 0.19 | 0.67 | 0.61 | Mixed signals (PE=0.63, contact=0.61, NE |
| 212 | rpt_c3 | 92.7 | PE | 0.63 | 0.47 | 0.14 | 0.73 | 0.47 | C/3 RPT anchor (not fade spike) |
| 213 | rpt_c3 | 92.7 | PE | 0.62 | 0.47 | 0.18 | 0.72 | 0.47 | C/3 RPT anchor (not fade spike) |
| 220 | routine_05c | 87.5 | PE | 0.61 | 0.46 | 0.14 | 0.68 | 0.46 | PE activity/isolation pattern leads (PE= |
| 230 | routine_05c | 87.1 | PE | 0.61 | 0.47 | 0.14 | 0.68 | 0.47 | PE activity/isolation pattern leads (PE= |
| 240 | routine_05c | 86.6 | mixed | 0.56 | 0.47 | 0.20 | 0.68 | 0.47 | Mixed signals (PE=0.56, contact=0.47, NE |
| 250 | routine_05c | 86.1 | PE | 0.61 | 0.47 | 0.14 | 0.68 | 0.47 | PE activity/isolation pattern leads (PE= |
| 260 | routine_05c | 85.6 | PE | 0.61 | 0.48 | 0.14 | 0.68 | 0.48 | PE activity/isolation pattern leads (PE= |
| 270 | routine_05c | 85.2 | PE | 0.61 | 0.48 | 0.14 | 0.68 | 0.48 | PE activity/isolation pattern leads (PE= |
| 280 | routine_05c | 84.6 | PE | 0.61 | 0.48 | 0.14 | 0.68 | 0.48 | PE activity/isolation pattern leads (PE= |
| 290 | routine_05c | 84.1 | PE | 0.61 | 0.49 | 0.15 | 0.68 | 0.49 | PE activity/isolation pattern leads (PE= |
| 300 | routine_05c | 83.6 | PE | 0.61 | 0.47 | 0.14 | 0.68 | 0.47 | PE activity/isolation pattern leads (PE= |
| 310 | routine_05c | 83.0 | mixed | 0.61 | 0.48 | 0.14 | 0.68 | 0.48 | Mixed signals (PE=0.61, contact=0.48, NE |
| 317 | rpt_c3 | 88.8 | PE | 0.58 | 0.32 | 0.10 | 0.67 | 0.32 | C/3 RPT anchor (not fade spike) |
| 318 | rpt_c3 | 89.0 | PE | 0.56 | 0.34 | 0.10 | 0.68 | 0.34 | C/3 RPT anchor (not fade spike) |
| 330 | routine_05c | 82.0 | mixed | 0.61 | 0.40 | 0.12 | 0.68 | 0.40 | Mixed signals (PE=0.61, contact=0.40, NE |
| 340 | routine_05c | 81.1 | mixed | 0.61 | 0.38 | 0.12 | 0.68 | 0.38 | Mixed signals (PE=0.61, contact=0.38, NE |
| 350 | routine_05c | 80.3 | mixed | 0.61 | 0.37 | 0.11 | 0.68 | 0.37 | Mixed signals (PE=0.61, contact=0.37, NE |
| 360 | routine_05c | 79.3 | shared | 0.54 | 0.35 | 0.13 | 0.58 | 0.35 | Shared modes lead (shared=0.64): solid_d |
| 370 | routine_05c | 78.3 | mixed | 0.56 | 0.33 | 0.10 | 0.68 | 0.33 | Mixed signals (PE=0.56, contact=0.33, NE |
| 380 | routine_05c | 77.3 | mixed | 0.49 | 0.31 | 0.09 | 0.58 | 0.31 | Mixed signals (PE=0.49, contact=0.31, NE |
| 390 | routine_05c | 76.1 | mixed | 0.56 | 0.31 | 0.09 | 0.68 | 0.31 | Mixed signals (PE=0.56, contact=0.31, NE |
| 400 | routine_05c | 75.1 | mixed | 0.51 | 0.30 | 0.09 | 0.68 | 0.30 | Mixed signals (PE=0.51, contact=0.30, NE |
| 410 | routine_05c | 74.1 | mixed | 0.51 | 0.27 | 0.08 | 0.68 | 0.27 | Mixed signals (PE=0.51, contact=0.27, NE |
| 420 | routine_05c | 73.2 | mixed | 0.51 | 0.28 | 0.09 | 0.68 | 0.28 | Mixed signals (PE=0.51, contact=0.28, NE |
| 422 | rpt_c3 | 79.5 | PE | 0.74 | 0.25 | 0.07 | 0.99 | 0.25 | C/3 RPT anchor (not fade spike) |
| 423 | rpt_c3 | 80.3 | PE | 0.56 | 0.26 | 0.08 | 0.67 | 0.26 | C/3 RPT anchor (not fade spike) |
| 430 | routine_05c | 73.7 | mixed | 0.51 | 0.25 | 0.07 | 0.68 | 0.25 | Mixed signals (PE=0.51, contact=0.25, NE |
| 440 | routine_05c | 72.3 | mixed | 0.51 | 0.23 | 0.07 | 0.68 | 0.23 | Mixed signals (PE=0.51, contact=0.23, NE |
| 450 | routine_05c | 71.4 | mixed | 0.51 | 0.22 | 0.07 | 0.68 | 0.22 | Mixed signals (PE=0.51, contact=0.22, NE |
| 460 | routine_05c | 70.6 | mixed | 0.51 | 0.23 | 0.07 | 0.68 | 0.23 | Mixed signals (PE=0.51, contact=0.23, NE |
| 470 | routine_05c | 69.9 | mixed | 0.51 | 0.23 | 0.07 | 0.68 | 0.23 | Mixed signals (PE=0.51, contact=0.23, NE |
| 480 | routine_05c | 69.3 | PE | 0.51 | 0.23 | 0.07 | 0.68 | 0.23 | PE activity/isolation pattern leads (PE= |
| 490 | routine_05c | 68.6 | PE | 0.51 | 0.23 | 0.07 | 0.69 | 0.23 | PE activity/isolation pattern leads (PE= |
| 500 | routine_05c | 68.1 | PE | 0.59 | 0.23 | 0.07 | 0.79 | 0.23 | PE activity/isolation pattern leads (PE= |
| 510 | routine_05c | 67.6 | PE | 0.64 | 0.23 | 0.07 | 0.85 | 0.23 | PE activity/isolation pattern leads (PE= |
| 520 | routine_05c | 67.1 | PE | 0.66 | 0.26 | 0.08 | 0.88 | 0.26 | PE activity/isolation pattern leads (PE= |
| 527 | rpt_c3 | 72.2 | PE | 0.74 | 0.21 | 0.06 | 0.98 | 0.21 | C/3 RPT anchor (not fade spike) |
| 528 | rpt_c3 | 72.7 | PE | 0.63 | 0.22 | 0.07 | 0.84 | 0.22 | C/3 RPT anchor (not fade spike) |
| 540 | routine_05c | 66.7 | PE | 0.64 | 0.19 | 0.06 | 0.85 | 0.19 | PE activity/isolation pattern leads (PE= |
| 550 | routine_05c | 66.1 | PE | 0.67 | 0.18 | 0.05 | 0.90 | 0.18 | PE activity/isolation pattern leads (PE= |
| 560 | routine_05c | 65.6 | PE | 0.69 | 0.22 | 0.07 | 0.92 | 0.22 | PE activity/isolation pattern leads (PE= |
| 561 | routine_05c | 65.6 | PE | 0.69 | 0.21 | 0.06 | 0.92 | 0.21 | PE activity/isolation pattern leads (PE= |
| 562 | routine_05c | 65.5 | PE | 0.69 | 0.22 | 0.07 | 0.92 | 0.22 | PE activity/isolation pattern leads (PE= |
| 563 | routine_05c | 65.5 | PE | 0.69 | 0.21 | 0.06 | 0.92 | 0.21 | PE activity/isolation pattern leads (PE= |
| 564 | routine_05c | 65.4 | PE | 0.70 | 0.21 | 0.06 | 0.93 | 0.21 | PE activity/isolation pattern leads (PE= |

> v1.3 Si-on-Gr · NCM82 secondary: mid-life SoHQ bumps = **C/3 RPT**. `contact_stack` = R-centric stack/contact. `NE` = Si chemo-mech co-sign only. PE = activity/isolation pattern (not LAM%). 절대 LAM% 금지. Gr stage monitoring은 후속.