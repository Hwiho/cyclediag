# 열화 구간별 전극 가설 진단 v1.1 — M01Ch022

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- Methodology: electrode_side_v1_1 · FC-OCP peak Δhits · contact_stack vs NE(Si co-sign)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 70 cycles sampled; 세그먼트 SoHQ≥50

## 구간 요약

### Seg 1: cycle 2–310 · 접촉/스택 저항 패턴 우위
- SoHQ: 100.6% → 83.0% (36 points)
- 점수: PE=0.41 / contact_stack=0.55 / NE_hyp=0.12 / shared=0.12 (conf=0.65)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.04
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.50, contact_loss=0.55, LLI=0.46

### Seg 2: cycle 317–360 · 접촉/스택 저항 패턴 우위
- SoHQ: 88.8% → 79.3% (6 points)
- 점수: PE=0.54 / contact_stack=0.61 / NE_hyp=0.15 / shared=0.17 (conf=0.58)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.10
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.65, contact_loss=0.61, LLI=0.61

### Seg 3: cycle 370–400 · 혼합/근소
- SoHQ: 78.3% → 75.1% (4 points)
- 점수: PE=0.54 / contact_stack=0.54 / NE_hyp=0.10 / shared=0.17 (conf=0.49)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.65, contact_loss=0.54, LLI=0.69

### Seg 4: cycle 410–423 · 혼합/근소
- SoHQ: 74.1% → 80.3% (4 points)
- 점수: PE=0.53 / contact_stack=0.55 / NE_hyp=0.14 / shared=0.16 (conf=0.60)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.10
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.67, contact_loss=0.55, LLI=0.58

### Seg 5: cycle 430–520 · 혼합/근소
- SoHQ: 73.7% → 67.1% (10 points)
- 점수: PE=0.51 / contact_stack=0.50 / NE_hyp=0.10 / shared=0.13 (conf=0.42)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.68, contact_loss=0.50, LLI=0.51

### Seg 6: cycle 527–564 · 혼합/근소
- SoHQ: 72.2% → 65.4% (9 points)
- 점수: PE=0.51 / contact_stack=0.55 / NE_hyp=0.12 / shared=0.11 (conf=0.49)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.04
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.68, contact_loss=0.55, LLI=0.43

## 수명 단계 롤업

- **early (1/3)** cyc 2–200: PE=0.36 contact=0.51 NE_hyp=0.11 → majority **접촉/스택 저항 패턴 우위** (SoHQ 101→88%)
- **mid (1/3)** cyc 210–400: PE=0.52 contact=0.60 NE_hyp=0.13 → majority **접촉/스택 저항 패턴 우위** (SoHQ 88→75%)
- **late (1/3)** cyc 410–564: PE=0.51 contact=0.53 NE_hyp=0.11 → majority **혼합/근소** (SoHQ 74→65%)

## 사이클 궤적

| cycle | SoHQ | dominant | PE | contact | NE_hyp | LAM_PE | contact_loss | note |
|------:|-----:|:---------|---:|--------:|-------:|-------:|-------------:|:-----|
| 2 | 100.6 | contact_stack | 0.04 | 0.34 | 0.12 | 0.05 | 0.34 | Contact/stack ohmic pattern leads (contact=0.34) |
| 3 | 100.0 | contact_stack | 0.00 | 0.34 | 0.12 | 0.00 | 0.34 | Contact/stack ohmic pattern leads (contact=0.34) |
| 10 | 95.8 | contact_stack | 0.30 | 0.41 | 0.08 | 0.39 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 20 | 95.0 | contact_stack | 0.29 | 0.41 | 0.08 | 0.38 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 30 | 94.6 | contact_stack | 0.20 | 0.41 | 0.08 | 0.20 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 40 | 94.3 | contact_stack | 0.34 | 0.41 | 0.08 | 0.38 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 50 | 94.0 | contact_stack | 0.33 | 0.41 | 0.08 | 0.38 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 60 | 93.7 | contact_stack | 0.34 | 0.41 | 0.08 | 0.38 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 70 | 93.4 | contact_stack | 0.34 | 0.40 | 0.08 | 0.39 | 0.40 | Contact/stack ohmic pattern leads (contact=0.40) |
| 80 | 93.0 | contact_stack | 0.36 | 0.68 | 0.21 | 0.41 | 0.68 | Contact/stack ohmic pattern leads (contact=0.68) |
| 90 | 92.6 | contact_stack | 0.37 | 0.67 | 0.13 | 0.42 | 0.67 | Contact/stack ohmic pattern leads (contact=0.67) |
| 100 | 92.2 | contact_stack | 0.46 | 0.65 | 0.13 | 0.55 | 0.65 | Contact/stack ohmic pattern leads (contact=0.65) |
| 107 | 95.5 | contact_stack | 0.17 | 0.33 | 0.12 | 0.22 | 0.33 | Contact/stack ohmic pattern leads (contact=0.33) |
| 108 | 95.4 | contact_stack | 0.19 | 0.33 | 0.12 | 0.25 | 0.33 | Contact/stack ohmic pattern leads (contact=0.33) |
| 120 | 91.6 | contact_stack | 0.48 | 0.62 | 0.12 | 0.57 | 0.62 | Contact/stack ohmic pattern leads (contact=0.62) |
| 130 | 91.2 | contact_stack | 0.49 | 0.64 | 0.12 | 0.59 | 0.64 | Contact/stack ohmic pattern leads (contact=0.64) |
| 140 | 90.8 | contact_stack | 0.50 | 0.61 | 0.12 | 0.60 | 0.61 | Contact/stack ohmic pattern leads (contact=0.61) |
| 150 | 90.4 | contact_stack | 0.51 | 0.63 | 0.12 | 0.61 | 0.63 | Contact/stack ohmic pattern leads (contact=0.63) |
| 160 | 90.2 | contact_stack | 0.52 | 0.61 | 0.12 | 0.62 | 0.61 | Contact/stack ohmic pattern leads (contact=0.61) |
| 170 | 89.8 | contact_stack | 0.52 | 0.63 | 0.12 | 0.63 | 0.63 | Contact/stack ohmic pattern leads (contact=0.63) |
| 180 | 89.3 | contact_stack | 0.53 | 0.62 | 0.12 | 0.64 | 0.62 | Contact/stack ohmic pattern leads (contact=0.62) |
| 190 | 88.9 | contact_stack | 0.53 | 0.64 | 0.12 | 0.64 | 0.64 | Contact/stack ohmic pattern leads (contact=0.64) |
| 200 | 88.4 | contact_stack | 0.54 | 0.62 | 0.12 | 0.65 | 0.62 | Contact/stack ohmic pattern leads (contact=0.62) |
| 210 | 88.0 | contact_stack | 0.54 | 0.61 | 0.12 | 0.65 | 0.61 | Contact/stack ohmic pattern leads (contact=0.61) |
| 212 | 92.7 | contact_stack | 0.26 | 0.32 | 0.12 | 0.35 | 0.32 | Contact/stack ohmic pattern leads (contact=0.32) |
| 213 | 92.7 | contact_stack | 0.25 | 0.33 | 0.12 | 0.34 | 0.33 | Contact/stack ohmic pattern leads (contact=0.33) |
| 220 | 87.5 | contact_stack | 0.54 | 0.66 | 0.13 | 0.65 | 0.66 | Contact/stack ohmic pattern leads (contact=0.66) |
| 230 | 87.1 | contact_stack | 0.54 | 0.67 | 0.13 | 0.66 | 0.67 | Contact/stack ohmic pattern leads (contact=0.67) |
| 240 | 86.6 | contact_stack | 0.55 | 0.66 | 0.13 | 0.66 | 0.66 | Contact/stack ohmic pattern leads (contact=0.66) |
| 250 | 86.1 | contact_stack | 0.55 | 0.67 | 0.13 | 0.66 | 0.67 | Contact/stack ohmic pattern leads (contact=0.67) |
| 260 | 85.6 | contact_stack | 0.55 | 0.67 | 0.13 | 0.66 | 0.67 | Contact/stack ohmic pattern leads (contact=0.67) |
| 270 | 85.2 | contact_stack | 0.55 | 0.67 | 0.13 | 0.67 | 0.67 | Contact/stack ohmic pattern leads (contact=0.67) |
| 280 | 84.6 | contact_stack | 0.55 | 0.67 | 0.13 | 0.67 | 0.67 | Contact/stack ohmic pattern leads (contact=0.67) |
| 290 | 84.1 | contact_stack | 0.55 | 0.69 | 0.13 | 0.67 | 0.69 | Contact/stack ohmic pattern leads (contact=0.69) |
| 300 | 83.6 | contact_stack | 0.55 | 0.66 | 0.13 | 0.67 | 0.66 | Contact/stack ohmic pattern leads (contact=0.66) |
| 310 | 83.0 | contact_stack | 0.55 | 0.67 | 0.13 | 0.67 | 0.67 | Contact/stack ohmic pattern leads (contact=0.67) |
| 317 | 88.8 | mixed | 0.54 | 0.55 | 0.18 | 0.65 | 0.55 | Mixed signals (PE=0.54, contact=0.55, NE_hyp=0.1 |
| 318 | 89.0 | mixed | 0.54 | 0.58 | 0.18 | 0.66 | 0.58 | Mixed signals (PE=0.54, contact=0.58, NE_hyp=0.1 |
| 330 | 82.0 | contact_stack | 0.55 | 0.68 | 0.13 | 0.67 | 0.68 | Contact/stack ohmic pattern leads (contact=0.68) |
| 340 | 81.1 | contact_stack | 0.55 | 0.65 | 0.13 | 0.67 | 0.65 | Contact/stack ohmic pattern leads (contact=0.65) |
| 350 | 80.3 | contact_stack | 0.56 | 0.63 | 0.12 | 0.67 | 0.63 | Contact/stack ohmic pattern leads (contact=0.63) |
| 360 | 79.3 | contact_stack | 0.48 | 0.58 | 0.18 | 0.58 | 0.58 | Contact/stack ohmic pattern leads (contact=0.58) |
| 370 | 78.3 | mixed | 0.56 | 0.57 | 0.11 | 0.67 | 0.57 | Mixed signals (PE=0.56, contact=0.57, NE_hyp=0.1 |
| 380 | 77.3 | mixed | 0.49 | 0.53 | 0.10 | 0.58 | 0.53 | Mixed signals (PE=0.49, contact=0.53, NE_hyp=0.1 |
| 390 | 76.1 | mixed | 0.56 | 0.53 | 0.10 | 0.67 | 0.53 | Mixed signals (PE=0.56, contact=0.53, NE_hyp=0.1 |
| 400 | 75.1 | mixed | 0.56 | 0.52 | 0.10 | 0.68 | 0.52 | Mixed signals (PE=0.56, contact=0.52, NE_hyp=0.1 |
| 410 | 74.1 | PE | 0.56 | 0.47 | 0.09 | 0.68 | 0.47 | PE-side hypothesis leads (PE=0.56, contact=0.47, |
| 420 | 73.2 | PE | 0.56 | 0.49 | 0.09 | 0.68 | 0.49 | PE-side hypothesis leads (PE=0.56, contact=0.49, |
| 422 | 79.5 | contact_stack | 0.51 | 0.62 | 0.19 | 0.67 | 0.62 | Contact/stack ohmic pattern leads (contact=0.62) |
| 423 | 80.3 | contact_stack | 0.50 | 0.64 | 0.20 | 0.67 | 0.64 | Contact/stack ohmic pattern leads (contact=0.64) |
| 430 | 73.7 | mixed | 0.56 | 0.52 | 0.10 | 0.68 | 0.52 | Mixed signals (PE=0.56, contact=0.52, NE_hyp=0.1 |
| 440 | 72.3 | mixed | 0.51 | 0.50 | 0.10 | 0.68 | 0.50 | Mixed signals (PE=0.51, contact=0.50, NE_hyp=0.1 |
| 450 | 71.4 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 460 | 70.6 | mixed | 0.51 | 0.49 | 0.10 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.1 |
| 470 | 69.9 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 480 | 69.3 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 490 | 68.6 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 500 | 68.1 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 510 | 67.6 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 520 | 67.1 | mixed | 0.51 | 0.53 | 0.10 | 0.68 | 0.53 | Mixed signals (PE=0.51, contact=0.53, NE_hyp=0.1 |
| 527 | 72.2 | contact_stack | 0.51 | 0.64 | 0.20 | 0.68 | 0.64 | Contact/stack ohmic pattern leads (contact=0.64) |
| 528 | 72.7 | contact_stack | 0.51 | 0.66 | 0.21 | 0.68 | 0.66 | Contact/stack ohmic pattern leads (contact=0.66) |
| 540 | 66.7 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 550 | 66.1 | mixed | 0.51 | 0.48 | 0.09 | 0.68 | 0.48 | Mixed signals (PE=0.51, contact=0.48, NE_hyp=0.0 |
| 560 | 65.6 | mixed | 0.51 | 0.54 | 0.10 | 0.68 | 0.54 | Mixed signals (PE=0.51, contact=0.54, NE_hyp=0.1 |
| 561 | 65.6 | mixed | 0.51 | 0.53 | 0.10 | 0.68 | 0.53 | Mixed signals (PE=0.51, contact=0.53, NE_hyp=0.1 |
| 562 | 65.5 | mixed | 0.51 | 0.55 | 0.11 | 0.68 | 0.55 | Mixed signals (PE=0.51, contact=0.55, NE_hyp=0.1 |
| 563 | 65.5 | mixed | 0.51 | 0.53 | 0.10 | 0.68 | 0.53 | Mixed signals (PE=0.51, contact=0.53, NE_hyp=0.1 |
| 564 | 65.4 | mixed | 0.51 | 0.53 | 0.10 | 0.68 | 0.53 | Mixed signals (PE=0.51, contact=0.53, NE_hyp=0.1 |

> v1.1: `contact_stack` = 전극 미분해 접촉/스택 저항 패턴. `NE`는 Si co-sign(hyst_low·mech/chem·Q_relax)이 있을 때만. 절대 LAM% 금지. peak attribution은 synth FC-OCP 도메인.