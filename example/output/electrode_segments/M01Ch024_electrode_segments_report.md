# 열화 구간별 전극 가설 진단 v1.3 — M01Ch024

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- Chemistry: **Si-on-Gr** (Si coating on graphite, exposed Gr 가능) · **NCM82 secondary**
- Methodology: electrode_side_v1_3 · FC-OCP charge unique Δhits · R-centric contact_stack · Si co-sign NE
- Protocol dual-track: routine 0.5C 궤적 + C/3 RPT 앵커 (중간 SoHQ bump = RPT)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 88 cycles (routine=58, rpt_c3=12); 세그먼트는 routine only · SoHQ≥50

## 구간 요약 (routine 0.5C)

### Seg 1: cycle 7–100 · 양극(PE) 가설 우위
- SoHQ(routine): 96.2% → 91.8% (13 points)
- 점수: PE=0.52 / contact_stack=0.13 / NE_hyp=0.03 / shared=0.40 (conf=0.67)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.20
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.62, contact_loss=0.13, LLI=0.44

### Seg 2: cycle 120–180 · 혼합/근소
- SoHQ(routine): 91.1% → 88.3% (7 points)
- 점수: PE=0.58 / contact_stack=0.62 / NE_hyp=0.19 / shared=0.48 (conf=0.62)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.40
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.65, contact_loss=0.62, LLI=0.57

### Seg 3: cycle 190–280 · 양극(PE) 가설 우위
- SoHQ(routine): 87.7% → 82.2% (10 points)
- 점수: PE=0.60 / contact_stack=0.50 / NE_hyp=0.16 / shared=0.51 (conf=0.69)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.42
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.68, contact_loss=0.50, LLI=0.57

### Seg 4: cycle 290–533 · 양극(PE) 가설 우위
- SoHQ(routine): 81.3% → 64.3% (28 points)
- 점수: PE=0.63 / contact_stack=0.24 / NE_hyp=0.07 / shared=0.47 (conf=0.73)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.42
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.81, contact_loss=0.24, LLI=0.51

## C/3 RPT 앵커 (이중 트랙)

중간 궤적의 SoHQ 상승 스파이크는 **C/3(~0.33C) RPT 용량**입니다. rate가 낮아 분극이 작아 보이므로 0.5C routine보다 높게 찍히는 것이 정상입니다. fade/lean/세그먼트에는 넣지 않고 RCF·η·열역학 용량 트랙으로만 씁니다.

| cycle | SoHQ_C/3 | prev routine | SoHQ_0.5C | Δ(RPT−routine) |
|------:|---------:|-------------:|----------:|---------------:|
| 2 | 100.6 | — | n/a | n/a |
| 3 | 100.0 | — | n/a | n/a |
| 107 | 95.3 | 100 | 91.8 | +3.5 |
| 108 | 95.3 | 100 | 91.8 | +3.4 |
| 212 | 92.1 | 210 | 86.7 | +5.3 |
| 213 | 92.0 | 210 | 86.7 | +5.3 |
| 317 | 85.2 | 310 | 79.1 | +6.0 |
| 318 | 85.7 | 310 | 79.1 | +6.6 |
| 422 | 74.5 | 420 | 69.0 | +5.5 |
| 423 | 74.9 | 420 | 69.0 | +6.0 |
| 527 | 68.5 | 526 | 63.9 | +4.6 |
| 528 | 68.9 | 526 | 63.9 | +5.0 |

## 수명 단계 롤업 (routine only)

- **early (1/3)** cyc 7–170: PE=0.54 contact=0.28 NE_hyp=0.08 → majority **혼합/근소** (SoHQ 96→89%)
- **mid (1/3)** cyc 180–370: PE=0.58 contact=0.43 NE_hyp=0.14 → majority **혼합/근소** (SoHQ 88→73%)
- **late (1/3)** cyc 380–533: PE=0.66 contact=0.21 NE_hyp=0.06 → majority **양극(PE) 가설 우위** (SoHQ 72→64%)

## 사이클 궤적

| cycle | role | SoHQ | dominant | PE | contact | NE_hyp | LAM_PE | contact_loss | note |
|------:|:-----|-----:|:---------|---:|--------:|-------:|-------:|-------------:|:-----|
| 2 | rpt_c3 | 100.6 | PE | 0.29 | 0.00 | 0.00 | 0.21 | 0.00 | C/3 RPT anchor (not fade spike) |
| 3 | rpt_c3 | 100.0 | PE | 0.20 | 0.00 | 0.00 | 0.13 | 0.00 | C/3 RPT anchor (not fade spike) |
| 7 | routine_05c | 96.2 | PE | 0.59 | 0.00 | 0.00 | 0.66 | 0.00 | PE activity/isolation pattern leads (PE= |
| 8 | routine_05c | 96.0 | mixed | 0.42 | 0.00 | 0.00 | 0.50 | 0.00 | Mixed signals (PE=0.42, contact=0.00, NE |
| 9 | routine_05c | 95.8 | PE | 0.46 | 0.00 | 0.00 | 0.55 | 0.00 | PE activity/isolation pattern leads (PE= |
| 10 | routine_05c | 95.7 | PE | 0.47 | 0.00 | 0.00 | 0.56 | 0.00 | PE activity/isolation pattern leads (PE= |
| 20 | routine_05c | 94.9 | mixed | 0.39 | 0.00 | 0.00 | 0.45 | 0.00 | Mixed signals (PE=0.39, contact=0.00, NE |
| 30 | routine_05c | 94.5 | mixed | 0.40 | 0.00 | 0.00 | 0.47 | 0.00 | Mixed signals (PE=0.40, contact=0.00, NE |
| 40 | routine_05c | 94.1 | mixed | 0.47 | 0.00 | 0.00 | 0.56 | 0.00 | Mixed signals (PE=0.47, contact=0.00, NE |
| 50 | routine_05c | 93.8 | shared | 0.39 | 0.00 | 0.00 | 0.46 | 0.00 | Shared modes lead (shared=0.46): solid_d |
| 60 | routine_05c | 93.4 | PE | 0.58 | 0.00 | 0.00 | 0.71 | 0.00 | PE activity/isolation pattern leads (PE= |
| 70 | routine_05c | 93.1 | PE | 0.53 | 0.45 | 0.10 | 0.63 | 0.45 | PE activity/isolation pattern leads (PE= |
| 80 | routine_05c | 92.7 | PE | 0.59 | 0.42 | 0.09 | 0.72 | 0.42 | PE activity/isolation pattern leads (PE= |
| 90 | routine_05c | 92.3 | PE | 0.77 | 0.38 | 0.08 | 0.96 | 0.38 | PE activity/isolation pattern leads (PE= |
| 100 | routine_05c | 91.8 | PE | 0.65 | 0.40 | 0.09 | 0.80 | 0.40 | PE activity/isolation pattern leads (PE= |
| 107 | rpt_c3 | 95.3 | PE | 0.22 | 0.00 | 0.00 | 0.23 | 0.00 | C/3 RPT anchor (not fade spike) |
| 108 | rpt_c3 | 95.3 | PE | 0.28 | 0.00 | 0.00 | 0.31 | 0.00 | C/3 RPT anchor (not fade spike) |
| 120 | routine_05c | 91.1 | contact_stack | 0.51 | 0.62 | 0.19 | 0.61 | 0.62 | Contact/stack ohmic pattern leads (conta |
| 130 | routine_05c | 90.6 | mixed | 0.57 | 0.61 | 0.19 | 0.62 | 0.61 | Mixed signals (PE=0.57, contact=0.61, NE |
| 140 | routine_05c | 90.2 | mixed | 0.61 | 0.61 | 0.18 | 0.68 | 0.61 | Mixed signals (PE=0.61, contact=0.61, NE |
| 150 | routine_05c | 89.7 | mixed | 0.55 | 0.60 | 0.18 | 0.60 | 0.60 | Mixed signals (PE=0.55, contact=0.60, NE |
| 160 | routine_05c | 89.3 | mixed | 0.61 | 0.63 | 0.19 | 0.68 | 0.63 | Mixed signals (PE=0.61, contact=0.63, NE |
| 170 | routine_05c | 88.8 | mixed | 0.61 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.61, contact=0.61, NE |
| 180 | routine_05c | 88.3 | mixed | 0.61 | 0.63 | 0.19 | 0.68 | 0.63 | Mixed signals (PE=0.61, contact=0.63, NE |
| 190 | routine_05c | 87.7 | contact_stack | 0.56 | 0.62 | 0.25 | 0.68 | 0.62 | Contact/stack ohmic pattern leads (conta |
| 200 | routine_05c | 87.3 | mixed | 0.61 | 0.62 | 0.19 | 0.68 | 0.62 | Mixed signals (PE=0.61, contact=0.62, NE |
| 210 | routine_05c | 86.7 | mixed | 0.61 | 0.63 | 0.19 | 0.68 | 0.63 | Mixed signals (PE=0.61, contact=0.63, NE |
| 212 | rpt_c3 | 92.1 | PE | 0.65 | 0.50 | 0.15 | 0.80 | 0.50 | C/3 RPT anchor (not fade spike) |
| 213 | rpt_c3 | 92.0 | PE | 0.77 | 0.50 | 0.23 | 0.96 | 0.50 | C/3 RPT anchor (not fade spike) |
| 220 | routine_05c | 86.2 | PE | 0.61 | 0.44 | 0.13 | 0.68 | 0.44 | PE activity/isolation pattern leads (PE= |
| 230 | routine_05c | 85.7 | PE | 0.61 | 0.45 | 0.14 | 0.68 | 0.45 | PE activity/isolation pattern leads (PE= |
| 240 | routine_05c | 85.0 | mixed | 0.61 | 0.47 | 0.18 | 0.68 | 0.47 | Mixed signals (PE=0.61, contact=0.47, NE |
| 250 | routine_05c | 84.4 | PE | 0.61 | 0.46 | 0.14 | 0.68 | 0.46 | PE activity/isolation pattern leads (PE= |
| 260 | routine_05c | 83.8 | PE | 0.61 | 0.46 | 0.14 | 0.68 | 0.46 | PE activity/isolation pattern leads (PE= |
| 270 | routine_05c | 83.0 | PE | 0.61 | 0.45 | 0.14 | 0.68 | 0.45 | PE activity/isolation pattern leads (PE= |
| 280 | routine_05c | 82.2 | PE | 0.61 | 0.44 | 0.13 | 0.68 | 0.44 | PE activity/isolation pattern leads (PE= |
| 290 | routine_05c | 81.3 | PE | 0.61 | 0.43 | 0.13 | 0.68 | 0.43 | PE activity/isolation pattern leads (PE= |
| 300 | routine_05c | 80.2 | PE | 0.61 | 0.42 | 0.13 | 0.68 | 0.42 | PE activity/isolation pattern leads (PE= |
| 310 | routine_05c | 79.1 | mixed | 0.61 | 0.39 | 0.15 | 0.68 | 0.39 | Mixed signals (PE=0.61, contact=0.39, NE |
| 317 | rpt_c3 | 85.2 | PE | 0.61 | 0.31 | 0.09 | 0.75 | 0.31 | C/3 RPT anchor (not fade spike) |
| 318 | rpt_c3 | 85.7 | PE | 0.49 | 0.31 | 0.09 | 0.59 | 0.31 | C/3 RPT anchor (not fade spike) |
| 330 | routine_05c | 77.8 | mixed | 0.56 | 0.29 | 0.09 | 0.68 | 0.29 | Mixed signals (PE=0.56, contact=0.29, NE |
| 340 | routine_05c | 76.5 | shared | 0.49 | 0.26 | 0.08 | 0.58 | 0.26 | Shared modes lead (shared=0.57): solid_d |
| 350 | routine_05c | 75.3 | mixed | 0.54 | 0.27 | 0.10 | 0.58 | 0.27 | Mixed signals (PE=0.54, contact=0.27, NE |
| 360 | routine_05c | 74.1 | mixed | 0.51 | 0.26 | 0.08 | 0.67 | 0.26 | Mixed signals (PE=0.51, contact=0.26, NE |
| 370 | routine_05c | 73.2 | mixed | 0.51 | 0.25 | 0.07 | 0.68 | 0.25 | Mixed signals (PE=0.51, contact=0.25, NE |
| 380 | routine_05c | 72.3 | PE | 0.51 | 0.25 | 0.08 | 0.67 | 0.25 | PE activity/isolation pattern leads (PE= |
| 390 | routine_05c | 71.4 | PE | 0.51 | 0.23 | 0.07 | 0.67 | 0.23 | PE activity/isolation pattern leads (PE= |
| 400 | routine_05c | 70.4 | PE | 0.54 | 0.27 | 0.08 | 0.73 | 0.27 | PE activity/isolation pattern leads (PE= |
| 410 | routine_05c | 69.7 | PE | 0.56 | 0.26 | 0.08 | 0.75 | 0.26 | PE activity/isolation pattern leads (PE= |
| 420 | routine_05c | 69.0 | PE | 0.65 | 0.27 | 0.08 | 0.87 | 0.27 | PE activity/isolation pattern leads (PE= |
| 422 | rpt_c3 | 74.5 | PE | 0.65 | 0.22 | 0.07 | 0.87 | 0.22 | C/3 RPT anchor (not fade spike) |
| 423 | rpt_c3 | 74.9 | PE | 0.60 | 0.21 | 0.06 | 0.80 | 0.21 | C/3 RPT anchor (not fade spike) |
| 430 | routine_05c | 69.2 | PE | 0.57 | 0.18 | 0.05 | 0.77 | 0.18 | PE activity/isolation pattern leads (PE= |
| 440 | routine_05c | 68.3 | PE | 0.63 | 0.18 | 0.05 | 0.84 | 0.18 | PE activity/isolation pattern leads (PE= |
| 450 | routine_05c | 67.6 | PE | 0.67 | 0.18 | 0.05 | 0.90 | 0.18 | PE activity/isolation pattern leads (PE= |
| 460 | routine_05c | 67.0 | PE | 0.69 | 0.17 | 0.05 | 0.92 | 0.17 | PE activity/isolation pattern leads (PE= |
| 470 | routine_05c | 66.5 | PE | 0.70 | 0.18 | 0.05 | 0.93 | 0.18 | PE activity/isolation pattern leads (PE= |
| 480 | routine_05c | 66.0 | PE | 0.69 | 0.19 | 0.07 | 0.92 | 0.19 | PE activity/isolation pattern leads (PE= |
| 490 | routine_05c | 65.5 | PE | 0.70 | 0.17 | 0.05 | 0.93 | 0.17 | PE activity/isolation pattern leads (PE= |
| 500 | routine_05c | 65.0 | PE | 0.72 | 0.19 | 0.06 | 0.95 | 0.19 | PE activity/isolation pattern leads (PE= |
| 510 | routine_05c | 64.6 | PE | 0.71 | 0.20 | 0.06 | 0.95 | 0.20 | PE activity/isolation pattern leads (PE= |
| 520 | routine_05c | 64.1 | PE | 0.70 | 0.22 | 0.07 | 0.94 | 0.22 | PE activity/isolation pattern leads (PE= |
| 524 | routine_05c | 64.0 | PE | 0.71 | 0.22 | 0.07 | 0.94 | 0.22 | PE activity/isolation pattern leads (PE= |
| 525 | routine_05c | 63.9 | PE | 0.71 | 0.22 | 0.07 | 0.95 | 0.22 | PE activity/isolation pattern leads (PE= |
| 526 | routine_05c | 63.9 | PE | 0.72 | 0.21 | 0.06 | 0.96 | 0.21 | PE activity/isolation pattern leads (PE= |
| 527 | rpt_c3 | 68.5 | PE | 0.53 | 0.18 | 0.05 | 0.70 | 0.18 | C/3 RPT anchor (not fade spike) |
| 528 | rpt_c3 | 68.9 | PE | 0.58 | 0.18 | 0.06 | 0.77 | 0.18 | C/3 RPT anchor (not fade spike) |
| 532 | routine_05c | 64.5 | PE | 0.71 | 0.17 | 0.05 | 0.94 | 0.17 | PE activity/isolation pattern leads (PE= |
| 533 | routine_05c | 64.3 | PE | 0.71 | 0.18 | 0.05 | 0.95 | 0.18 | PE activity/isolation pattern leads (PE= |

> v1.3 Si-on-Gr · NCM82 secondary: mid-life SoHQ bumps = **C/3 RPT**. `contact_stack` = R-centric stack/contact. `NE` = Si chemo-mech co-sign only. PE = activity/isolation pattern (not LAM%). 절대 LAM% 금지. Gr stage monitoring은 후속.