# 열화 구간별 전극 가설 진단 v1.2 — M01Ch024

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- Methodology: electrode_side_v1_2 · FC-OCP peak Δhits · contact_stack vs NE(Si co-sign)
- Protocol dual-track: routine 0.5C 궤적 + C/3 RPT 앵커 (중간 SoHQ bump = RPT, 노이즈 아님)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 88 cycles (routine=58, rpt_c3=12); 세그먼트는 routine only · SoHQ≥50

## 구간 요약 (routine 0.5C)

### Seg 1: cycle 7–50 · 접촉/스택 저항 패턴 우위
- SoHQ(routine): 96.2% → 93.8% (8 points)
- 점수: PE=0.40 / contact_stack=0.54 / NE_hyp=0.10 / shared=0.55 (conf=0.44)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.53, contact_loss=0.54, LLI=0.41

### Seg 2: cycle 60–80 · 접촉/스택 저항 패턴 우위
- SoHQ(routine): 93.4% → 92.7% (3 points)
- 점수: PE=0.51 / contact_stack=0.61 / NE_hyp=0.12 / shared=0.51 (conf=0.53)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`interface_R,SE_decomposition,LLI,solid_diffusion`
- pattern: LAM_PE=0.69, contact_loss=0.61, LLI=0.48

### Seg 3: cycle 90–210 · 접촉/스택 저항 패턴 우위
- SoHQ(routine): 92.3% → 86.7% (12 points)
- 점수: PE=0.56 / contact_stack=0.65 / NE_hyp=0.19 / shared=0.61 (conf=0.53)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.17
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`interface_R,solid_diffusion,SE_decomposition,LLI`
- pattern: LAM_PE=0.70, contact_loss=0.65, LLI=0.55

### Seg 4: cycle 220–280 · 혼합/근소
- SoHQ(routine): 86.2% → 82.2% (7 points)
- 점수: PE=0.56 / contact_stack=0.59 / NE_hyp=0.20 / shared=0.64 (conf=0.57)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.23
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.68, contact_loss=0.59, LLI=0.58

### Seg 5: cycle 290–330 · 혼합/근소
- SoHQ(routine): 81.3% → 77.8% (4 points)
- 점수: PE=0.55 / contact_stack=0.56 / NE_hyp=0.20 / shared=0.68 (conf=0.69)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.25
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.68, contact_loss=0.56, LLI=0.70

### Seg 6: cycle 340–400 · 혼합/근소
- SoHQ(routine): 76.5% → 70.4% (7 points)
- 점수: PE=0.50 / contact_stack=0.50 / NE_hyp=0.17 / shared=0.63 (conf=0.65)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.23
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.66, contact_loss=0.50, LLI=0.57

### Seg 7: cycle 410–533 · 양극(PE) 가설 우위
- SoHQ(routine): 69.7% → 64.3% (17 points)
- 점수: PE=0.68 / contact_stack=0.48 / NE_hyp=0.16 / shared=0.57 (conf=0.63)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.21
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.91, contact_loss=0.48, LLI=0.44

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

- **early (1/3)** cyc 7–170: PE=0.49 contact=0.60 NE_hyp=0.14 → majority **혼합/근소** (SoHQ 96→89%)
- **mid (1/3)** cyc 180–370: PE=0.54 contact=0.58 NE_hyp=0.20 → majority **셀 공통/공유 모드** (SoHQ 88→73%)
- **late (1/3)** cyc 380–533: PE=0.66 contact=0.49 NE_hyp=0.16 → majority **양극(PE) 가설 우위** (SoHQ 72→64%)

## 사이클 궤적

| cycle | role | SoHQ | dominant | PE | contact | NE_hyp | LAM_PE | contact_loss | note |
|------:|:-----|-----:|:---------|---:|--------:|-------:|-------:|-------------:|:-----|
| 2 | rpt_c3 | 100.6 | PE | 0.25 | 0.00 | 0.06 | 0.21 | 0.00 | C/3 RPT anchor (not fade spike) |
| 3 | rpt_c3 | 100.0 | unknown | 0.15 | 0.02 | 0.07 | 0.13 | 0.02 | C/3 RPT anchor (not fade spike) |
| 7 | routine_05c | 96.2 | mixed | 0.54 | 0.54 | 0.10 | 0.66 | 0.54 | Mixed signals (PE=0.54, contact=0.54, NE |
| 8 | routine_05c | 96.0 | mixed | 0.37 | 0.54 | 0.10 | 0.50 | 0.54 | Mixed signals (PE=0.37, contact=0.54, NE |
| 9 | routine_05c | 95.8 | mixed | 0.41 | 0.54 | 0.10 | 0.55 | 0.54 | Mixed signals (PE=0.41, contact=0.54, NE |
| 10 | routine_05c | 95.7 | mixed | 0.42 | 0.54 | 0.10 | 0.56 | 0.54 | Mixed signals (PE=0.42, contact=0.54, NE |
| 20 | routine_05c | 94.9 | mixed | 0.34 | 0.54 | 0.10 | 0.45 | 0.54 | Mixed signals (PE=0.34, contact=0.54, NE |
| 30 | routine_05c | 94.5 | mixed | 0.35 | 0.54 | 0.10 | 0.47 | 0.54 | Mixed signals (PE=0.35, contact=0.54, NE |
| 40 | routine_05c | 94.1 | mixed | 0.42 | 0.54 | 0.10 | 0.56 | 0.54 | Mixed signals (PE=0.42, contact=0.54, NE |
| 50 | routine_05c | 93.8 | shared | 0.34 | 0.54 | 0.10 | 0.46 | 0.54 | Shared modes lead (shared=0.60): solid_d |
| 60 | routine_05c | 93.4 | mixed | 0.53 | 0.54 | 0.10 | 0.71 | 0.54 | Mixed signals (PE=0.53, contact=0.54, NE |
| 70 | routine_05c | 93.1 | contact_stack | 0.48 | 0.65 | 0.12 | 0.63 | 0.65 | Contact/stack ohmic pattern leads (conta |
| 80 | routine_05c | 92.7 | contact_stack | 0.54 | 0.64 | 0.12 | 0.72 | 0.64 | Contact/stack ohmic pattern leads (conta |
| 90 | routine_05c | 92.3 | PE | 0.72 | 0.63 | 0.12 | 0.96 | 0.63 | PE-side hypothesis leads (PE=0.72, conta |
| 100 | routine_05c | 91.8 | mixed | 0.60 | 0.63 | 0.12 | 0.80 | 0.63 | Mixed signals (PE=0.60, contact=0.63, NE |
| 107 | rpt_c3 | 95.3 | contact_stack | 0.17 | 0.47 | 0.19 | 0.23 | 0.47 | C/3 RPT anchor (not fade spike) |
| 108 | rpt_c3 | 95.3 | contact_stack | 0.23 | 0.47 | 0.19 | 0.31 | 0.47 | C/3 RPT anchor (not fade spike) |
| 120 | routine_05c | 91.1 | contact_stack | 0.46 | 0.66 | 0.21 | 0.61 | 0.66 | Contact/stack ohmic pattern leads (conta |
| 130 | routine_05c | 90.6 | mixed | 0.52 | 0.65 | 0.20 | 0.62 | 0.65 | Mixed signals (PE=0.52, contact=0.65, NE |
| 140 | routine_05c | 90.2 | mixed | 0.56 | 0.65 | 0.20 | 0.68 | 0.65 | Mixed signals (PE=0.56, contact=0.65, NE |
| 150 | routine_05c | 89.7 | mixed | 0.50 | 0.65 | 0.20 | 0.60 | 0.65 | Mixed signals (PE=0.50, contact=0.65, NE |
| 160 | routine_05c | 89.3 | mixed | 0.56 | 0.67 | 0.21 | 0.68 | 0.67 | Mixed signals (PE=0.56, contact=0.67, NE |
| 170 | routine_05c | 88.8 | contact_stack | 0.56 | 0.65 | 0.20 | 0.68 | 0.65 | Contact/stack ohmic pattern leads (conta |
| 180 | routine_05c | 88.3 | contact_stack | 0.56 | 0.66 | 0.21 | 0.68 | 0.66 | Contact/stack ohmic pattern leads (conta |
| 190 | routine_05c | 87.7 | mixed | 0.56 | 0.66 | 0.21 | 0.68 | 0.66 | Mixed signals (PE=0.56, contact=0.66, NE |
| 200 | routine_05c | 87.3 | mixed | 0.56 | 0.66 | 0.21 | 0.68 | 0.66 | Mixed signals (PE=0.56, contact=0.66, NE |
| 210 | routine_05c | 86.7 | mixed | 0.56 | 0.66 | 0.21 | 0.68 | 0.66 | Mixed signals (PE=0.56, contact=0.66, NE |
| 212 | rpt_c3 | 92.1 | PE | 0.60 | 0.54 | 0.17 | 0.80 | 0.54 | C/3 RPT anchor (not fade spike) |
| 213 | rpt_c3 | 92.0 | PE | 0.72 | 0.54 | 0.34 | 0.96 | 0.54 | C/3 RPT anchor (not fade spike) |
| 220 | routine_05c | 86.2 | mixed | 0.56 | 0.59 | 0.19 | 0.68 | 0.59 | Mixed signals (PE=0.56, contact=0.59, NE |
| 230 | routine_05c | 85.7 | mixed | 0.56 | 0.59 | 0.19 | 0.68 | 0.59 | Mixed signals (PE=0.56, contact=0.59, NE |
| 240 | routine_05c | 85.0 | shared | 0.56 | 0.60 | 0.26 | 0.68 | 0.60 | Shared modes lead (shared=0.68): solid_d |
| 250 | routine_05c | 84.4 | shared | 0.56 | 0.60 | 0.19 | 0.68 | 0.60 | Shared modes lead (shared=0.67): solid_d |
| 260 | routine_05c | 83.8 | shared | 0.56 | 0.60 | 0.19 | 0.68 | 0.60 | Shared modes lead (shared=0.67): solid_d |
| 270 | routine_05c | 83.0 | mixed | 0.56 | 0.59 | 0.19 | 0.68 | 0.59 | Mixed signals (PE=0.56, contact=0.59, NE |
| 280 | routine_05c | 82.2 | mixed | 0.56 | 0.59 | 0.19 | 0.68 | 0.59 | Mixed signals (PE=0.56, contact=0.59, NE |
| 290 | routine_05c | 81.3 | shared | 0.56 | 0.58 | 0.18 | 0.68 | 0.58 | Shared modes lead (shared=0.64): solid_d |
| 300 | routine_05c | 80.2 | shared | 0.56 | 0.57 | 0.18 | 0.68 | 0.57 | Shared modes lead (shared=0.67): solid_d |
| 310 | routine_05c | 79.1 | shared | 0.56 | 0.56 | 0.25 | 0.68 | 0.56 | Shared modes lead (shared=0.72): solid_d |
| 317 | rpt_c3 | 85.2 | mixed | 0.56 | 0.56 | 0.18 | 0.75 | 0.56 | C/3 RPT anchor (not fade spike) |
| 318 | rpt_c3 | 85.7 | contact_stack | 0.44 | 0.56 | 0.18 | 0.59 | 0.56 | C/3 RPT anchor (not fade spike) |
| 330 | routine_05c | 77.8 | shared | 0.51 | 0.52 | 0.17 | 0.68 | 0.52 | Shared modes lead (shared=0.70): solid_d |
| 340 | routine_05c | 76.5 | shared | 0.44 | 0.51 | 0.16 | 0.58 | 0.51 | Shared modes lead (shared=0.70): solid_d |
| 350 | routine_05c | 75.3 | shared | 0.49 | 0.51 | 0.23 | 0.58 | 0.51 | Shared modes lead (shared=0.70): solid_d |
| 360 | routine_05c | 74.1 | shared | 0.51 | 0.51 | 0.17 | 0.67 | 0.51 | Shared modes lead (shared=0.68): solid_d |
| 370 | routine_05c | 73.2 | shared | 0.51 | 0.50 | 0.16 | 0.68 | 0.50 | Shared modes lead (shared=0.67): solid_d |
| 380 | routine_05c | 72.3 | mixed | 0.51 | 0.50 | 0.16 | 0.67 | 0.50 | Mixed signals (PE=0.51, contact=0.50, NE |
| 390 | routine_05c | 71.4 | mixed | 0.51 | 0.49 | 0.16 | 0.67 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE |
| 400 | routine_05c | 70.4 | mixed | 0.54 | 0.51 | 0.17 | 0.73 | 0.51 | Mixed signals (PE=0.54, contact=0.51, NE |
| 410 | routine_05c | 69.7 | mixed | 0.56 | 0.51 | 0.17 | 0.75 | 0.51 | Mixed signals (PE=0.56, contact=0.51, NE |
| 420 | routine_05c | 69.0 | mixed | 0.65 | 0.51 | 0.17 | 0.87 | 0.51 | Mixed signals (PE=0.65, contact=0.51, NE |
| 422 | rpt_c3 | 74.5 | PE | 0.65 | 0.54 | 0.17 | 0.87 | 0.54 | C/3 RPT anchor (not fade spike) |
| 423 | rpt_c3 | 74.9 | PE | 0.60 | 0.53 | 0.17 | 0.80 | 0.53 | C/3 RPT anchor (not fade spike) |
| 430 | routine_05c | 69.2 | mixed | 0.57 | 0.47 | 0.16 | 0.77 | 0.47 | Mixed signals (PE=0.57, contact=0.47, NE |
| 440 | routine_05c | 68.3 | mixed | 0.63 | 0.48 | 0.16 | 0.84 | 0.48 | Mixed signals (PE=0.63, contact=0.48, NE |
| 450 | routine_05c | 67.6 | PE | 0.67 | 0.47 | 0.16 | 0.90 | 0.47 | PE-side hypothesis leads (PE=0.67, conta |
| 460 | routine_05c | 67.0 | PE | 0.69 | 0.47 | 0.16 | 0.92 | 0.47 | PE-side hypothesis leads (PE=0.69, conta |
| 470 | routine_05c | 66.5 | PE | 0.70 | 0.47 | 0.16 | 0.93 | 0.47 | PE-side hypothesis leads (PE=0.70, conta |
| 480 | routine_05c | 66.0 | PE | 0.69 | 0.48 | 0.22 | 0.92 | 0.48 | PE-side hypothesis leads (PE=0.69, conta |
| 490 | routine_05c | 65.5 | PE | 0.70 | 0.47 | 0.16 | 0.93 | 0.47 | PE-side hypothesis leads (PE=0.70, conta |
| 500 | routine_05c | 65.0 | PE | 0.72 | 0.48 | 0.16 | 0.95 | 0.48 | PE-side hypothesis leads (PE=0.72, conta |
| 510 | routine_05c | 64.6 | PE | 0.71 | 0.49 | 0.16 | 0.95 | 0.49 | PE-side hypothesis leads (PE=0.71, conta |
| 520 | routine_05c | 64.1 | PE | 0.70 | 0.49 | 0.16 | 0.94 | 0.49 | PE-side hypothesis leads (PE=0.70, conta |
| 524 | routine_05c | 64.0 | PE | 0.71 | 0.49 | 0.16 | 0.94 | 0.49 | PE-side hypothesis leads (PE=0.71, conta |
| 525 | routine_05c | 63.9 | PE | 0.71 | 0.49 | 0.16 | 0.95 | 0.49 | PE-side hypothesis leads (PE=0.71, conta |
| 526 | routine_05c | 63.9 | PE | 0.72 | 0.49 | 0.16 | 0.96 | 0.49 | PE-side hypothesis leads (PE=0.72, conta |
| 527 | rpt_c3 | 68.5 | mixed | 0.53 | 0.53 | 0.17 | 0.70 | 0.53 | C/3 RPT anchor (not fade spike) |
| 528 | rpt_c3 | 68.9 | mixed | 0.58 | 0.53 | 0.17 | 0.77 | 0.53 | C/3 RPT anchor (not fade spike) |
| 532 | routine_05c | 64.5 | PE | 0.71 | 0.47 | 0.16 | 0.94 | 0.47 | PE-side hypothesis leads (PE=0.71, conta |
| 533 | routine_05c | 64.3 | PE | 0.71 | 0.48 | 0.16 | 0.95 | 0.48 | PE-side hypothesis leads (PE=0.71, conta |

> v1.2: mid-life SoHQ bumps = **C/3 RPT**. `contact_stack` = 전극 미분해 접촉/스택 저항. `NE`는 Si co-sign이 있을 때만. 절대 LAM% 금지.