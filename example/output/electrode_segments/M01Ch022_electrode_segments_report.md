# 열화 구간별 전극 가설 진단 v1.2 — M01Ch022

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- Methodology: electrode_side_v1_2 · FC-OCP peak Δhits · contact_stack vs NE(Si co-sign)
- Protocol dual-track: routine 0.5C 궤적 + C/3 RPT 앵커 (중간 SoHQ bump = RPT, 노이즈 아님)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 90 cycles (routine=60, rpt_c3=12); 세그먼트는 routine only · SoHQ≥50

## 구간 요약 (routine 0.5C)

### Seg 1: cycle 7–9 · 혼합/근소
- SoHQ(routine): 96.3% → 95.9% (3 points)
- 점수: PE=0.56 / contact_stack=0.54 / NE_hyp=0.10 / shared=0.51 (conf=0.47)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.69, contact_loss=0.54, LLI=0.39

### Seg 2: cycle 10–60 · 접촉/스택 저항 패턴 우위
- SoHQ(routine): 95.8% → 93.7% (6 points)
- 점수: PE=0.47 / contact_stack=0.54 / NE_hyp=0.10 / shared=0.55 (conf=0.48)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.60, contact_loss=0.54, LLI=0.41

### Seg 3: cycle 70–90 · 혼합/근소
- SoHQ(routine): 93.4% → 92.6% (3 points)
- 점수: PE=0.64 / contact_stack=0.62 / NE_hyp=0.15 / shared=0.51 (conf=0.46)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.07
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`interface_R,SE_decomposition,LLI,solid_diffusion`
- pattern: LAM_PE=0.83, contact_loss=0.62, LLI=0.46

### Seg 4: cycle 100–210 · 접촉/스택 저항 패턴 우위
- SoHQ(routine): 92.2% → 88.0% (11 points)
- 점수: PE=0.58 / contact_stack=0.66 / NE_hyp=0.20 / shared=0.59 (conf=0.56)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.18
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.72, contact_loss=0.66, LLI=0.53

### Seg 5: cycle 220–240 · 혼합/근소
- SoHQ(routine): 87.5% → 86.6% (3 points)
- 점수: PE=0.56 / contact_stack=0.61 / NE_hyp=0.19 / shared=0.63 (conf=0.52)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.20
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.68, contact_loss=0.61, LLI=0.53

### Seg 6: cycle 250–310 · 접촉/스택 저항 패턴 우위
- SoHQ(routine): 86.1% → 83.0% (7 points)
- 점수: PE=0.56 / contact_stack=0.61 / NE_hyp=0.19 / shared=0.64 (conf=0.54)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.20
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.68, contact_loss=0.61, LLI=0.58

### Seg 7: cycle 330–350 · 혼합/근소
- SoHQ(routine): 82.0% → 80.3% (3 points)
- 점수: PE=0.56 / contact_stack=0.57 / NE_hyp=0.18 / shared=0.70 (conf=0.70)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.20
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.68, contact_loss=0.57, LLI=0.68

### Seg 8: cycle 360–380 · 음극(NE) 가설 우위 (Si co-sign)
- SoHQ(routine): 79.3% → 77.3% (3 points)
- 점수: PE=0.48 / contact_stack=0.54 / NE_hyp=0.20 / shared=0.68 (conf=0.70)
- **상대 lean 라벨: 음극(NE) 가설 우위 (Si co-sign)** · si_cosign≈0.27
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,LLI,interface_R,SE_decomposition`
- pattern: LAM_PE=0.61, contact_loss=0.54, LLI=0.71

### Seg 9: cycle 390–490 · 혼합/근소
- SoHQ(routine): 76.1% → 68.6% (11 points)
- 점수: PE=0.51 / contact_stack=0.51 / NE_hyp=0.17 / shared=0.64 (conf=0.64)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.20
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,solid_diffusion,interface_R,SE_decomposition`
- pattern: LAM_PE=0.68, contact_loss=0.51, LLI=0.58

### Seg 10: cycle 500–564 · 양극(PE) 가설 우위
- SoHQ(routine): 68.1% → 65.4% (10 points)
- 점수: PE=0.67 / contact_stack=0.50 / NE_hyp=0.16 / shared=0.59 (conf=0.56)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.20
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`solid_diffusion,interface_R,SE_decomposition,LLI`
- pattern: LAM_PE=0.89, contact_loss=0.50, LLI=0.43

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

- **early (1/3)** cyc 7–180: PE=0.55 contact=0.60 NE_hyp=0.15 → majority **혼합/근소** (SoHQ 96→89%)
- **mid (1/3)** cyc 190–390: PE=0.55 contact=0.60 NE_hyp=0.19 → majority **혼합/근소** (SoHQ 89→76%)
- **late (1/3)** cyc 400–564: PE=0.59 contact=0.50 NE_hyp=0.16 → majority **셀 공통/공유 모드** (SoHQ 75→65%)

## 사이클 궤적

| cycle | role | SoHQ | dominant | PE | contact | NE_hyp | LAM_PE | contact_loss | note |
|------:|:-----|-----:|:---------|---:|--------:|-------:|-------:|-------------:|:-----|
| 2 | rpt_c3 | 100.6 | unknown | 0.17 | 0.00 | 0.06 | 0.05 | 0.00 | C/3 RPT anchor (not fade spike) |
| 3 | rpt_c3 | 100.0 | unknown | 0.13 | 0.02 | 0.07 | 0.00 | 0.02 | C/3 RPT anchor (not fade spike) |
| 7 | routine_05c | 96.3 | mixed | 0.59 | 0.54 | 0.10 | 0.72 | 0.54 | Mixed signals (PE=0.59, contact=0.54, NE |
| 8 | routine_05c | 96.1 | mixed | 0.51 | 0.54 | 0.10 | 0.63 | 0.54 | Mixed signals (PE=0.51, contact=0.54, NE |
| 9 | routine_05c | 95.9 | mixed | 0.58 | 0.54 | 0.10 | 0.73 | 0.54 | Mixed signals (PE=0.58, contact=0.54, NE |
| 10 | routine_05c | 95.8 | PE | 0.67 | 0.54 | 0.10 | 0.83 | 0.54 | PE-side hypothesis leads (PE=0.67, conta |
| 20 | routine_05c | 95.0 | mixed | 0.47 | 0.54 | 0.10 | 0.57 | 0.54 | Mixed signals (PE=0.47, contact=0.54, NE |
| 30 | routine_05c | 94.6 | mixed | 0.34 | 0.54 | 0.10 | 0.45 | 0.54 | Mixed signals (PE=0.34, contact=0.54, NE |
| 40 | routine_05c | 94.3 | mixed | 0.43 | 0.54 | 0.10 | 0.58 | 0.54 | Mixed signals (PE=0.43, contact=0.54, NE |
| 50 | routine_05c | 94.0 | mixed | 0.43 | 0.54 | 0.10 | 0.57 | 0.54 | Mixed signals (PE=0.43, contact=0.54, NE |
| 60 | routine_05c | 93.7 | contact_stack | 0.46 | 0.54 | 0.10 | 0.61 | 0.54 | Contact/stack ohmic pattern leads (conta |
| 70 | routine_05c | 93.4 | mixed | 0.56 | 0.54 | 0.10 | 0.75 | 0.54 | Mixed signals (PE=0.56, contact=0.54, NE |
| 80 | routine_05c | 93.0 | mixed | 0.70 | 0.67 | 0.21 | 0.87 | 0.67 | Mixed signals (PE=0.70, contact=0.67, NE |
| 90 | routine_05c | 92.6 | mixed | 0.65 | 0.66 | 0.13 | 0.87 | 0.66 | Mixed signals (PE=0.65, contact=0.66, NE |
| 100 | routine_05c | 92.2 | PE | 0.73 | 0.65 | 0.13 | 0.97 | 0.65 | PE-side hypothesis leads (PE=0.73, conta |
| 107 | rpt_c3 | 95.5 | mixed | 0.45 | 0.47 | 0.19 | 0.54 | 0.47 | C/3 RPT anchor (not fade spike) |
| 108 | rpt_c3 | 95.4 | contact_stack | 0.37 | 0.47 | 0.19 | 0.44 | 0.47 | C/3 RPT anchor (not fade spike) |
| 120 | routine_05c | 91.6 | mixed | 0.61 | 0.65 | 0.20 | 0.76 | 0.65 | Mixed signals (PE=0.61, contact=0.65, NE |
| 130 | routine_05c | 91.2 | contact_stack | 0.55 | 0.66 | 0.21 | 0.74 | 0.66 | Contact/stack ohmic pattern leads (conta |
| 140 | routine_05c | 90.8 | mixed | 0.54 | 0.65 | 0.20 | 0.67 | 0.65 | Mixed signals (PE=0.54, contact=0.65, NE |
| 150 | routine_05c | 90.4 | mixed | 0.54 | 0.66 | 0.21 | 0.67 | 0.66 | Mixed signals (PE=0.54, contact=0.66, NE |
| 160 | routine_05c | 90.2 | mixed | 0.56 | 0.66 | 0.20 | 0.68 | 0.66 | Mixed signals (PE=0.56, contact=0.66, NE |
| 170 | routine_05c | 89.8 | contact_stack | 0.56 | 0.66 | 0.21 | 0.68 | 0.66 | Contact/stack ohmic pattern leads (conta |
| 180 | routine_05c | 89.3 | contact_stack | 0.56 | 0.66 | 0.21 | 0.68 | 0.66 | Contact/stack ohmic pattern leads (conta |
| 190 | routine_05c | 88.9 | contact_stack | 0.60 | 0.67 | 0.21 | 0.67 | 0.67 | Contact/stack ohmic pattern leads (conta |
| 200 | routine_05c | 88.4 | mixed | 0.56 | 0.66 | 0.21 | 0.68 | 0.66 | Mixed signals (PE=0.56, contact=0.66, NE |
| 210 | routine_05c | 88.0 | mixed | 0.59 | 0.66 | 0.21 | 0.67 | 0.66 | Mixed signals (PE=0.59, contact=0.66, NE |
| 212 | rpt_c3 | 92.7 | PE | 0.59 | 0.52 | 0.17 | 0.73 | 0.52 | C/3 RPT anchor (not fade spike) |
| 213 | rpt_c3 | 92.7 | mixed | 0.58 | 0.52 | 0.27 | 0.72 | 0.52 | C/3 RPT anchor (not fade spike) |
| 220 | routine_05c | 87.5 | mixed | 0.56 | 0.60 | 0.19 | 0.68 | 0.60 | Mixed signals (PE=0.56, contact=0.60, NE |
| 230 | routine_05c | 87.1 | mixed | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.56, contact=0.61, NE |
| 240 | routine_05c | 86.6 | mixed | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.56, contact=0.61, NE |
| 250 | routine_05c | 86.1 | mixed | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.56, contact=0.61, NE |
| 260 | routine_05c | 85.6 | mixed | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.56, contact=0.61, NE |
| 270 | routine_05c | 85.2 | mixed | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.56, contact=0.61, NE |
| 280 | routine_05c | 84.6 | mixed | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.56, contact=0.61, NE |
| 290 | routine_05c | 84.1 | mixed | 0.56 | 0.62 | 0.19 | 0.68 | 0.62 | Mixed signals (PE=0.56, contact=0.62, NE |
| 300 | routine_05c | 83.6 | mixed | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Mixed signals (PE=0.56, contact=0.61, NE |
| 310 | routine_05c | 83.0 | shared | 0.56 | 0.61 | 0.19 | 0.68 | 0.61 | Shared modes lead (shared=0.67): solid_d |
| 317 | rpt_c3 | 88.8 | mixed | 0.54 | 0.55 | 0.18 | 0.67 | 0.55 | C/3 RPT anchor (not fade spike) |
| 318 | rpt_c3 | 89.0 | mixed | 0.51 | 0.56 | 0.18 | 0.68 | 0.56 | C/3 RPT anchor (not fade spike) |
| 330 | routine_05c | 82.0 | shared | 0.56 | 0.58 | 0.19 | 0.68 | 0.58 | Shared modes lead (shared=0.70): solid_d |
| 340 | routine_05c | 81.1 | shared | 0.56 | 0.57 | 0.18 | 0.68 | 0.57 | Shared modes lead (shared=0.70): solid_d |
| 350 | routine_05c | 80.3 | shared | 0.56 | 0.57 | 0.18 | 0.68 | 0.57 | Shared modes lead (shared=0.70): solid_d |
| 360 | routine_05c | 79.3 | shared | 0.49 | 0.55 | 0.25 | 0.58 | 0.55 | Shared modes lead (shared=0.74): solid_d |
| 370 | routine_05c | 78.3 | shared | 0.51 | 0.54 | 0.18 | 0.68 | 0.54 | Shared modes lead (shared=0.71): solid_d |
| 380 | routine_05c | 77.3 | mixed | 0.44 | 0.53 | 0.17 | 0.58 | 0.53 | Mixed signals (PE=0.44, contact=0.53, NE |
| 390 | routine_05c | 76.1 | shared | 0.51 | 0.53 | 0.17 | 0.68 | 0.53 | Shared modes lead (shared=0.63): LLI, so |
| 400 | routine_05c | 75.1 | shared | 0.51 | 0.53 | 0.17 | 0.68 | 0.53 | Shared modes lead (shared=0.65): solid_d |
| 410 | routine_05c | 74.1 | shared | 0.51 | 0.51 | 0.17 | 0.68 | 0.51 | Shared modes lead (shared=0.66): solid_d |
| 420 | routine_05c | 73.2 | shared | 0.51 | 0.52 | 0.17 | 0.68 | 0.52 | Shared modes lead (shared=0.66): solid_d |
| 422 | rpt_c3 | 79.5 | PE | 0.74 | 0.55 | 0.18 | 0.99 | 0.55 | C/3 RPT anchor (not fade spike) |
| 423 | rpt_c3 | 80.3 | mixed | 0.51 | 0.55 | 0.18 | 0.67 | 0.55 | C/3 RPT anchor (not fade spike) |
| 430 | routine_05c | 73.7 | shared | 0.51 | 0.51 | 0.17 | 0.68 | 0.51 | Shared modes lead (shared=0.67): solid_d |
| 440 | routine_05c | 72.3 | shared | 0.51 | 0.50 | 0.16 | 0.68 | 0.50 | Shared modes lead (shared=0.66): solid_d |
| 450 | routine_05c | 71.4 | shared | 0.51 | 0.50 | 0.16 | 0.68 | 0.50 | Shared modes lead (shared=0.65): solid_d |
| 460 | routine_05c | 70.6 | shared | 0.51 | 0.50 | 0.16 | 0.68 | 0.50 | Shared modes lead (shared=0.64): solid_d |
| 470 | routine_05c | 69.9 | shared | 0.51 | 0.50 | 0.16 | 0.68 | 0.50 | Shared modes lead (shared=0.63): solid_d |
| 480 | routine_05c | 69.3 | mixed | 0.51 | 0.50 | 0.16 | 0.68 | 0.50 | Mixed signals (PE=0.51, contact=0.50, NE |
| 490 | routine_05c | 68.6 | mixed | 0.51 | 0.50 | 0.16 | 0.69 | 0.50 | Mixed signals (PE=0.51, contact=0.50, NE |
| 500 | routine_05c | 68.1 | mixed | 0.59 | 0.50 | 0.16 | 0.79 | 0.50 | Mixed signals (PE=0.59, contact=0.50, NE |
| 510 | routine_05c | 67.6 | mixed | 0.64 | 0.50 | 0.16 | 0.85 | 0.50 | Mixed signals (PE=0.64, contact=0.50, NE |
| 520 | routine_05c | 67.1 | mixed | 0.66 | 0.51 | 0.17 | 0.88 | 0.51 | Mixed signals (PE=0.66, contact=0.51, NE |
| 527 | rpt_c3 | 72.2 | PE | 0.74 | 0.54 | 0.17 | 0.98 | 0.54 | C/3 RPT anchor (not fade spike) |
| 528 | rpt_c3 | 72.7 | PE | 0.63 | 0.54 | 0.17 | 0.84 | 0.54 | C/3 RPT anchor (not fade spike) |
| 540 | routine_05c | 66.7 | mixed | 0.64 | 0.48 | 0.16 | 0.85 | 0.48 | Mixed signals (PE=0.64, contact=0.48, NE |
| 550 | routine_05c | 66.1 | PE | 0.67 | 0.48 | 0.16 | 0.90 | 0.48 | PE-side hypothesis leads (PE=0.67, conta |
| 560 | routine_05c | 65.6 | PE | 0.69 | 0.50 | 0.16 | 0.92 | 0.50 | PE-side hypothesis leads (PE=0.69, conta |
| 561 | routine_05c | 65.6 | PE | 0.69 | 0.49 | 0.16 | 0.92 | 0.49 | PE-side hypothesis leads (PE=0.69, conta |
| 562 | routine_05c | 65.5 | PE | 0.69 | 0.50 | 0.16 | 0.92 | 0.50 | PE-side hypothesis leads (PE=0.69, conta |
| 563 | routine_05c | 65.5 | PE | 0.69 | 0.50 | 0.16 | 0.92 | 0.50 | PE-side hypothesis leads (PE=0.69, conta |
| 564 | routine_05c | 65.4 | PE | 0.70 | 0.50 | 0.16 | 0.93 | 0.50 | PE-side hypothesis leads (PE=0.70, conta |

> v1.2: mid-life SoHQ bumps = **C/3 RPT**. `contact_stack` = 전극 미분해 접촉/스택 저항. `NE`는 Si co-sign이 있을 때만. 절대 LAM% 금지.