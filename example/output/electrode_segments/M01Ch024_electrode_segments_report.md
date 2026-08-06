# 열화 구간별 전극 가설 진단 v1.1 — M01Ch024

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- Methodology: electrode_side_v1_1 · FC-OCP peak Δhits · contact_stack vs NE(Si co-sign)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 66 cycles sampled; 세그먼트 SoHQ≥50

## 구간 요약

### Seg 1: cycle 2–130 · 접촉/스택 저항 패턴 우위
- SoHQ: 100.6% → 90.6% (16 points)
- 점수: PE=0.26 / contact_stack=0.46 / NE_hyp=0.10 / shared=0.10 (conf=0.71)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.05
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.31, contact_loss=0.46, LLI=0.39

### Seg 2: cycle 140–160 · 접촉/스택 저항 패턴 우위
- SoHQ: 90.2% → 89.3% (3 points)
- 점수: PE=0.51 / contact_stack=0.57 / NE_hyp=0.11 / shared=0.14 (conf=0.54)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.61, contact_loss=0.57, LLI=0.58

### Seg 3: cycle 170–210 · 혼합/근소
- SoHQ: 88.8% → 86.7% (5 points)
- 점수: PE=0.54 / contact_stack=0.57 / NE_hyp=0.11 / shared=0.14 (conf=0.48)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.65, contact_loss=0.57, LLI=0.56

### Seg 4: cycle 212–300 · 혼합/근소
- SoHQ: 92.1% → 80.2% (11 points)
- 점수: PE=0.53 / contact_stack=0.52 / NE_hyp=0.12 / shared=0.15 (conf=0.53)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.07
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.65, contact_loss=0.52, LLI=0.58

### Seg 5: cycle 310–318 · 혼합/근소
- SoHQ: 79.1% → 85.7% (3 points)
- 점수: PE=0.50 / contact_stack=0.52 / NE_hyp=0.17 / shared=0.17 (conf=0.61)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.20
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.62, contact_loss=0.52, LLI=0.56

### Seg 6: cycle 330–350 · 혼합/근소
- SoHQ: 77.8% → 75.3% (3 points)
- 점수: PE=0.51 / contact_stack=0.46 / NE_hyp=0.11 / shared=0.17 (conf=0.53)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.07
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.61, contact_loss=0.46, LLI=0.70

### Seg 7: cycle 360–400 · 양극(PE) 가설 우위
- SoHQ: 74.1% → 70.4% (5 points)
- 점수: PE=0.52 / contact_stack=0.43 / NE_hyp=0.08 / shared=0.13 (conf=0.55)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.67, contact_loss=0.43, LLI=0.53

### Seg 8: cycle 410–423 · 혼합/근소
- SoHQ: 69.7% → 74.9% (4 points)
- 점수: PE=0.48 / contact_stack=0.51 / NE_hyp=0.13 / shared=0.12 (conf=0.51)
- **상대 lean 라벨: 접촉·NE 쪽 lean** · si_cosign≈0.10
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.64, contact_loss=0.51, LLI=0.46

### Seg 9: cycle 430–500 · 양극(PE) 가설 우위
- SoHQ: 69.2% → 65.0% (8 points)
- 점수: PE=0.51 / contact_stack=0.43 / NE_hyp=0.09 / shared=0.12 (conf=0.52)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.03
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.68, contact_loss=0.43, LLI=0.45

### Seg 10: cycle 510–526 · 혼합/근소
- SoHQ: 64.6% → 63.9% (3 points)
- 점수: PE=0.51 / contact_stack=0.47 / NE_hyp=0.09 / shared=0.11 (conf=0.44)
- **상대 lean 라벨: 양극(PE) 가설 우위** · si_cosign≈0.00
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.68, contact_loss=0.47, LLI=0.45

### Seg 11: cycle 527–533 · 접촉/스택 저항 패턴 우위
- SoHQ: 68.5% → 64.3% (4 points)
- 점수: PE=0.50 / contact_stack=0.56 / NE_hyp=0.15 / shared=0.11 (conf=0.54)
- **상대 lean 라벨: 접촉/스택 저항 패턴 우위** · si_cosign≈0.10
- 모드: PE=`LAM_PE` · contact=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,solid_diffusion`
- pattern: LAM_PE=0.67, contact_loss=0.56, LLI=0.39

## 수명 단계 롤업

- **early (1/3)** cyc 2–180: PE=0.33 contact=0.49 NE_hyp=0.10 → majority **접촉/스택 저항 패턴 우위** (SoHQ 101→88%)
- **mid (1/3)** cyc 190–370: PE=0.53 contact=0.51 NE_hyp=0.12 → majority **혼합/근소** (SoHQ 88→73%)
- **late (1/3)** cyc 380–533: PE=0.50 contact=0.47 NE_hyp=0.11 → majority **양극(PE) 가설 우위** (SoHQ 72→64%)

## 사이클 궤적

| cycle | SoHQ | dominant | PE | contact | NE_hyp | LAM_PE | contact_loss | note |
|------:|-----:|:---------|---:|--------:|-------:|-------:|-------------:|:-----|
| 2 | 100.6 | contact_stack | 0.16 | 0.34 | 0.12 | 0.21 | 0.34 | Contact/stack ohmic pattern leads (contact=0.34) |
| 3 | 100.0 | contact_stack | 0.00 | 0.34 | 0.12 | 0.00 | 0.34 | Contact/stack ohmic pattern leads (contact=0.34) |
| 10 | 95.7 | contact_stack | 0.27 | 0.41 | 0.08 | 0.36 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 20 | 94.9 | contact_stack | 0.20 | 0.41 | 0.08 | 0.26 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 30 | 94.5 | contact_stack | 0.26 | 0.41 | 0.08 | 0.28 | 0.41 | Contact/stack ohmic pattern leads (contact=0.41) |
| 40 | 94.1 | contact_stack | 0.33 | 0.40 | 0.08 | 0.37 | 0.40 | Contact/stack ohmic pattern leads (contact=0.40) |
| 50 | 93.8 | contact_stack | 0.25 | 0.40 | 0.08 | 0.26 | 0.40 | Contact/stack ohmic pattern leads (contact=0.40) |
| 60 | 93.4 | contact_stack | 0.34 | 0.40 | 0.08 | 0.38 | 0.40 | Contact/stack ohmic pattern leads (contact=0.40) |
| 70 | 93.1 | contact_stack | 0.27 | 0.64 | 0.12 | 0.30 | 0.64 | Contact/stack ohmic pattern leads (contact=0.64) |
| 80 | 92.7 | contact_stack | 0.30 | 0.62 | 0.12 | 0.33 | 0.62 | Contact/stack ohmic pattern leads (contact=0.62) |
| 90 | 92.3 | contact_stack | 0.47 | 0.60 | 0.11 | 0.56 | 0.60 | Contact/stack ohmic pattern leads (contact=0.60) |
| 100 | 91.8 | contact_stack | 0.41 | 0.60 | 0.12 | 0.48 | 0.60 | Contact/stack ohmic pattern leads (contact=0.60) |
| 107 | 95.3 | contact_stack | 0.02 | 0.33 | 0.12 | 0.03 | 0.33 | Contact/stack ohmic pattern leads (contact=0.33) |
| 108 | 95.3 | contact_stack | 0.09 | 0.33 | 0.12 | 0.11 | 0.33 | Contact/stack ohmic pattern leads (contact=0.33) |
| 120 | 91.1 | contact_stack | 0.45 | 0.58 | 0.11 | 0.53 | 0.58 | Contact/stack ohmic pattern leads (contact=0.58) |
| 130 | 90.6 | contact_stack | 0.43 | 0.57 | 0.11 | 0.50 | 0.57 | Contact/stack ohmic pattern leads (contact=0.57) |
| 140 | 90.2 | mixed | 0.52 | 0.56 | 0.11 | 0.62 | 0.56 | Mixed signals (PE=0.52, contact=0.56, NE_hyp=0.1 |
| 150 | 89.7 | contact_stack | 0.47 | 0.54 | 0.10 | 0.56 | 0.54 | Contact/stack ohmic pattern leads (contact=0.54) |
| 160 | 89.3 | contact_stack | 0.53 | 0.59 | 0.11 | 0.64 | 0.59 | Contact/stack ohmic pattern leads (contact=0.59) |
| 170 | 88.8 | mixed | 0.53 | 0.56 | 0.11 | 0.65 | 0.56 | Mixed signals (PE=0.53, contact=0.56, NE_hyp=0.1 |
| 180 | 88.3 | mixed | 0.54 | 0.58 | 0.11 | 0.65 | 0.58 | Mixed signals (PE=0.54, contact=0.58, NE_hyp=0.1 |
| 190 | 87.7 | mixed | 0.54 | 0.57 | 0.11 | 0.65 | 0.57 | Mixed signals (PE=0.54, contact=0.57, NE_hyp=0.1 |
| 200 | 87.3 | mixed | 0.54 | 0.57 | 0.11 | 0.66 | 0.57 | Mixed signals (PE=0.54, contact=0.57, NE_hyp=0.1 |
| 210 | 86.7 | mixed | 0.55 | 0.57 | 0.11 | 0.66 | 0.57 | Mixed signals (PE=0.55, contact=0.57, NE_hyp=0.1 |
| 212 | 92.1 | PE | 0.39 | 0.32 | 0.12 | 0.46 | 0.32 | PE-side hypothesis leads (PE=0.39, contact=0.32, |
| 213 | 92.0 | PE | 0.52 | 0.33 | 0.17 | 0.63 | 0.33 | PE-side hypothesis leads (PE=0.52, contact=0.33, |
| 220 | 86.2 | mixed | 0.55 | 0.57 | 0.11 | 0.66 | 0.57 | Mixed signals (PE=0.55, contact=0.57, NE_hyp=0.1 |
| 230 | 85.7 | mixed | 0.55 | 0.57 | 0.11 | 0.66 | 0.57 | Mixed signals (PE=0.55, contact=0.57, NE_hyp=0.1 |
| 240 | 85.0 | mixed | 0.55 | 0.60 | 0.19 | 0.67 | 0.60 | Mixed signals (PE=0.55, contact=0.60, NE_hyp=0.1 |
| 250 | 84.4 | mixed | 0.55 | 0.60 | 0.11 | 0.67 | 0.60 | Mixed signals (PE=0.55, contact=0.60, NE_hyp=0.1 |
| 260 | 83.8 | mixed | 0.55 | 0.59 | 0.11 | 0.67 | 0.59 | Mixed signals (PE=0.55, contact=0.59, NE_hyp=0.1 |
| 270 | 83.0 | mixed | 0.55 | 0.57 | 0.11 | 0.67 | 0.57 | Mixed signals (PE=0.55, contact=0.57, NE_hyp=0.1 |
| 280 | 82.2 | mixed | 0.55 | 0.55 | 0.11 | 0.67 | 0.55 | Mixed signals (PE=0.55, contact=0.55, NE_hyp=0.1 |
| 290 | 81.3 | mixed | 0.55 | 0.53 | 0.10 | 0.67 | 0.53 | Mixed signals (PE=0.55, contact=0.53, NE_hyp=0.1 |
| 300 | 80.2 | mixed | 0.56 | 0.51 | 0.10 | 0.67 | 0.51 | Mixed signals (PE=0.56, contact=0.51, NE_hyp=0.1 |
| 310 | 79.1 | PE | 0.56 | 0.46 | 0.15 | 0.67 | 0.46 | PE-side hypothesis leads (PE=0.56, contact=0.46, |
| 317 | 85.2 | mixed | 0.50 | 0.55 | 0.18 | 0.60 | 0.55 | Mixed signals (PE=0.50, contact=0.55, NE_hyp=0.1 |
| 318 | 85.7 | contact_stack | 0.44 | 0.56 | 0.18 | 0.58 | 0.56 | Contact/stack ohmic pattern leads (contact=0.56) |
| 330 | 77.8 | PE | 0.56 | 0.48 | 0.09 | 0.68 | 0.48 | PE-side hypothesis leads (PE=0.56, contact=0.48, |
| 340 | 76.5 | mixed | 0.49 | 0.44 | 0.09 | 0.58 | 0.44 | Mixed signals (PE=0.49, contact=0.44, NE_hyp=0.0 |
| 350 | 75.3 | mixed | 0.49 | 0.45 | 0.15 | 0.58 | 0.45 | Mixed signals (PE=0.49, contact=0.45, NE_hyp=0.1 |
| 360 | 74.1 | PE | 0.55 | 0.45 | 0.09 | 0.67 | 0.45 | PE-side hypothesis leads (PE=0.55, contact=0.45, |
| 370 | 73.2 | PE | 0.51 | 0.42 | 0.08 | 0.68 | 0.42 | PE-side hypothesis leads (PE=0.51, contact=0.42, |
| 380 | 72.3 | PE | 0.50 | 0.43 | 0.08 | 0.67 | 0.43 | PE-side hypothesis leads (PE=0.50, contact=0.43, |
| 390 | 71.4 | PE | 0.50 | 0.40 | 0.08 | 0.67 | 0.40 | PE-side hypothesis leads (PE=0.50, contact=0.40, |
| 400 | 70.4 | mixed | 0.51 | 0.45 | 0.09 | 0.68 | 0.45 | Mixed signals (PE=0.51, contact=0.45, NE_hyp=0.0 |
| 410 | 69.7 | mixed | 0.44 | 0.44 | 0.08 | 0.58 | 0.44 | Mixed signals (PE=0.44, contact=0.44, NE_hyp=0.0 |
| 420 | 69.0 | PE | 0.51 | 0.44 | 0.09 | 0.67 | 0.44 | PE-side hypothesis leads (PE=0.51, contact=0.44, |
| 422 | 74.5 | contact_stack | 0.49 | 0.58 | 0.18 | 0.66 | 0.58 | Contact/stack ohmic pattern leads (contact=0.58) |
| 423 | 74.9 | contact_stack | 0.48 | 0.56 | 0.18 | 0.64 | 0.56 | Contact/stack ohmic pattern leads (contact=0.56) |
| 430 | 69.2 | PE | 0.51 | 0.44 | 0.08 | 0.67 | 0.44 | PE-side hypothesis leads (PE=0.51, contact=0.44, |
| 440 | 68.3 | PE | 0.51 | 0.44 | 0.09 | 0.67 | 0.44 | PE-side hypothesis leads (PE=0.51, contact=0.44, |
| 450 | 67.6 | PE | 0.51 | 0.43 | 0.08 | 0.68 | 0.43 | PE-side hypothesis leads (PE=0.51, contact=0.43, |
| 460 | 67.0 | PE | 0.51 | 0.42 | 0.08 | 0.68 | 0.42 | PE-side hypothesis leads (PE=0.51, contact=0.42, |
| 470 | 66.5 | PE | 0.51 | 0.43 | 0.08 | 0.68 | 0.43 | PE-side hypothesis leads (PE=0.51, contact=0.43, |
| 480 | 66.0 | PE | 0.51 | 0.43 | 0.14 | 0.68 | 0.43 | PE-side hypothesis leads (PE=0.51, contact=0.43, |
| 490 | 65.5 | PE | 0.51 | 0.42 | 0.08 | 0.68 | 0.42 | PE-side hypothesis leads (PE=0.51, contact=0.42, |
| 500 | 65.0 | PE | 0.51 | 0.45 | 0.09 | 0.68 | 0.45 | PE-side hypothesis leads (PE=0.51, contact=0.45, |
| 510 | 64.6 | mixed | 0.51 | 0.47 | 0.09 | 0.68 | 0.47 | Mixed signals (PE=0.51, contact=0.47, NE_hyp=0.0 |
| 520 | 64.1 | mixed | 0.51 | 0.48 | 0.09 | 0.68 | 0.48 | Mixed signals (PE=0.51, contact=0.48, NE_hyp=0.0 |
| 526 | 63.9 | mixed | 0.51 | 0.48 | 0.09 | 0.68 | 0.48 | Mixed signals (PE=0.51, contact=0.48, NE_hyp=0.0 |
| 527 | 68.5 | contact_stack | 0.50 | 0.63 | 0.20 | 0.67 | 0.63 | Contact/stack ohmic pattern leads (contact=0.63) |
| 528 | 68.9 | contact_stack | 0.50 | 0.64 | 0.20 | 0.67 | 0.64 | Contact/stack ohmic pattern leads (contact=0.64) |
| 532 | 64.5 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |
| 533 | 64.3 | mixed | 0.51 | 0.49 | 0.09 | 0.68 | 0.49 | Mixed signals (PE=0.51, contact=0.49, NE_hyp=0.0 |

> v1.1: `contact_stack` = 전극 미분해 접촉/스택 저항 패턴. `NE`는 Si co-sign(hyst_low·mech/chem·Q_relax)이 있을 때만. 절대 LAM% 금지. peak attribution은 synth FC-OCP 도메인.