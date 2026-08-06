# 열화 구간별 양·음극 가설 진단 — M01Ch022

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 70 cycles sampled; 세그먼트는 SoHQ≥50 capa-like

## 구간 요약 (패턴·양음극 지배 전환)

### Seg 1: cycle 2–3 · 양·음극 혼합(근소)
- SoHQ: 100.6% → 100.0% (2 points)
- 점수: PE=0.27 / NE=0.29 / shared=0.00 (Δ=0.01, conf=0.47)
- **이 구간 상대 지배: 음극(NE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.06, contact_loss=0.32, LLI=0.00

### Seg 2: cycle 10–30 · 양·음극 혼합(근소)
- SoHQ: 95.8% → 94.6% (3 points)
- 점수: PE=0.31 / NE=0.31 / shared=0.08 (Δ=0.00, conf=0.50)
- **이 구간 상대 지배: 음극(NE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.30, contact_loss=0.39, LLI=0.31

### Seg 3: cycle 40–70 · 양극(PE) 지배
- SoHQ: 94.3% → 93.4% (4 points)
- 점수: PE=0.40 / NE=0.31 / shared=0.08 (Δ=0.09, conf=0.60)
- **이 구간 상대 지배: 양극(PE)** (강도: 명확, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.30, contact_loss=0.38, LLI=0.33

### Seg 4: cycle 80–107 · 음극(NE) 지배
- SoHQ: 93.0% → 95.5% (4 points)
- 점수: PE=0.38 / NE=0.46 / shared=0.08 (Δ=0.09, conf=0.61)
- **이 구간 상대 지배: 음극(NE)** (강도: 명확, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.26, contact_loss=0.57, LLI=0.32

### Seg 5: cycle 108–120 · 양극(PE) 지배
- SoHQ: 95.4% → 91.6% (2 points)
- 점수: PE=0.43 / NE=0.38 / shared=0.07 (Δ=0.04, conf=0.54)
- **이 구간 상대 지배: 양극(PE)** (강도: 중간, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.25, contact_loss=0.46, LLI=0.28

### Seg 6: cycle 130–210 · 음극(NE) 지배
- SoHQ: 91.2% → 88.0% (9 points)
- 점수: PE=0.45 / NE=0.47 / shared=0.10 (Δ=0.02, conf=0.49)
- **이 구간 상대 지배: 음극(NE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.61, LLI=0.41

### Seg 7: cycle 212–240 · 음극(NE) 지배
- SoHQ: 92.7% → 86.6% (5 points)
- 점수: PE=0.35 / NE=0.41 / shared=0.09 (Δ=0.06, conf=0.58)
- **이 구간 상대 지배: 음극(NE)** (강도: 중간, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.22, contact_loss=0.48, LLI=0.36

### Seg 8: cycle 250–380 · 음극(NE) 지배
- SoHQ: 86.1% → 77.3% (15 points)
- 점수: PE=0.37 / NE=0.49 / shared=0.13 (Δ=0.12, conf=0.67)
- **이 구간 상대 지배: 음극(NE)** (강도: 명확, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.30, contact_loss=0.64, LLI=0.47

### Seg 9: cycle 390–423 · 양극(PE) 지배
- SoHQ: 76.1% → 80.3% (6 points)
- 점수: PE=0.48 / NE=0.40 / shared=0.12 (Δ=0.08, conf=0.63)
- **이 구간 상대 지배: 양극(PE)** (강도: 명확, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.51, LLI=0.50

### Seg 10: cycle 430–510 · 양극(PE) 지배
- SoHQ: 73.7% → 67.6% (9 points)
- 점수: PE=0.42 / NE=0.34 / shared=0.10 (Δ=0.08, conf=0.55)
- **이 구간 상대 지배: 양극(PE)** (강도: 명확, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.48, LLI=0.41

### Seg 11: cycle 520–527 · 음극(NE) 지배
- SoHQ: 67.1% → 72.2% (2 points)
- 점수: PE=0.38 / NE=0.42 / shared=0.09 (Δ=0.04, conf=0.51)
- **이 구간 상대 지배: 음극(NE)** (강도: 중간, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.57, LLI=0.37

### Seg 12: cycle 528–550 · 양극(PE) 지배
- SoHQ: 72.7% → 66.1% (3 points)
- 점수: PE=0.41 / NE=0.37 / shared=0.09 (Δ=0.04, conf=0.49)
- **이 구간 상대 지배: 양극(PE)** (강도: 중간, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.53, LLI=0.37

### Seg 13: cycle 560–564 · 음극(NE) 지배
- SoHQ: 65.6% → 65.4% (5 points)
- 점수: PE=0.33 / NE=0.37 / shared=0.08 (Δ=0.04, conf=0.49)
- **이 구간 상대 지배: 음극(NE)** (강도: 중간, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.53, LLI=0.31

## 수명 단계 롤업

- **early (1/3)** cyc 2–200: PE=0.39 NE=0.40 → **음극(NE)** (SoHQ 101→88%)
- **mid (1/3)** cyc 210–400: PE=0.38 NE=0.46 → **음극(NE)** (SoHQ 88→75%)
- **late (1/3)** cyc 410–564: PE=0.41 NE=0.37 → **양극(PE)** (SoHQ 74→65%)

## 사이클 궤적 (용량 사이클)

| cycle | SoHQ | lean | PE | NE | Δ | LAM_PE | contact | note |
|------:|-----:|:-----|---:|---:|--:|-------:|--------:|:-----|
| 2 | 100.6 | PE | 0.29 | 0.26 | +0.03 | 0.06 | 0.32 | Mixed PE/NE signals (PE=0.29, NE=0.26, Δ=0.03). Bo |
| 3 | 100.0 | NE | 0.25 | 0.31 | -0.06 | 0.00 | 0.32 | Mixed PE/NE signals (PE=0.25, NE=0.31, Δ=0.06). Bo |
| 10 | 95.8 | PE | 0.36 | 0.32 | +0.05 | 0.30 | 0.39 | Mixed PE/NE signals (PE=0.36, NE=0.32, Δ=0.05). Bo |
| 20 | 95.0 | PE | 0.36 | 0.31 | +0.05 | 0.30 | 0.39 | Mixed PE/NE signals (PE=0.36, NE=0.31, Δ=0.05). Bo |
| 30 | 94.6 | NE | 0.21 | 0.31 | -0.11 | 0.20 | 0.38 | NE-side hypothesis dominates (NE=0.31 > PE=0.21).  |
| 40 | 94.3 | PE | 0.42 | 0.31 | +0.11 | 0.30 | 0.38 | PE-side hypothesis dominates (PE=0.42 > NE=0.31).  |
| 50 | 94.0 | PE | 0.37 | 0.31 | +0.06 | 0.30 | 0.38 | Mixed PE/NE signals (PE=0.37, NE=0.31, Δ=0.06). Bo |
| 60 | 93.7 | PE | 0.42 | 0.31 | +0.11 | 0.30 | 0.38 | PE-side hypothesis dominates (PE=0.42 > NE=0.31).  |
| 70 | 93.4 | PE | 0.37 | 0.31 | +0.06 | 0.30 | 0.38 | Mixed PE/NE signals (PE=0.37, NE=0.31, Δ=0.06). Bo |
| 80 | 93.0 | NE | 0.37 | 0.56 | -0.19 | 0.30 | 0.67 | NE-side hypothesis dominates (NE=0.56 > PE=0.37).  |
| 90 | 92.6 | NE | 0.47 | 0.51 | -0.04 | 0.30 | 0.66 | Mixed PE/NE signals (PE=0.47, NE=0.51, Δ=0.04). Bo |
| 100 | 92.2 | NE | 0.43 | 0.49 | -0.06 | 0.31 | 0.64 | Mixed PE/NE signals (PE=0.43, NE=0.49, Δ=0.06). Bo |
| 107 | 95.5 | NE | 0.24 | 0.30 | -0.06 | 0.12 | 0.31 | Mixed PE/NE signals (PE=0.24, NE=0.30, Δ=0.06). Bo |
| 108 | 95.4 | PE | 0.33 | 0.30 | +0.02 | 0.18 | 0.31 | Mixed PE/NE signals (PE=0.33, NE=0.30, Δ=0.02). Bo |
| 120 | 91.6 | PE | 0.53 | 0.47 | +0.06 | 0.31 | 0.60 | Mixed PE/NE signals (PE=0.53, NE=0.47, Δ=0.06). Bo |
| 130 | 91.2 | ~ | 0.48 | 0.48 | -0.00 | 0.31 | 0.63 | Mixed PE/NE signals (PE=0.48, NE=0.48, Δ=0.00). Bo |
| 140 | 90.8 | ~ | 0.48 | 0.46 | +0.02 | 0.31 | 0.60 | Mixed PE/NE signals (PE=0.48, NE=0.46, Δ=0.02). Bo |
| 150 | 90.4 | PE | 0.53 | 0.47 | +0.06 | 0.31 | 0.62 | Mixed PE/NE signals (PE=0.53, NE=0.47, Δ=0.06). Bo |
| 160 | 90.2 | NE | 0.38 | 0.46 | -0.08 | 0.31 | 0.60 | NE-side hypothesis dominates (NE=0.46 > PE=0.38).  |
| 170 | 89.8 | ~ | 0.48 | 0.47 | +0.01 | 0.31 | 0.61 | Mixed PE/NE signals (PE=0.48, NE=0.47, Δ=0.01). Bo |
| 180 | 89.3 | NE | 0.43 | 0.47 | -0.04 | 0.31 | 0.61 | Mixed PE/NE signals (PE=0.43, NE=0.47, Δ=0.04). Bo |
| 190 | 88.9 | ~ | 0.48 | 0.49 | -0.01 | 0.31 | 0.64 | Mixed PE/NE signals (PE=0.48, NE=0.49, Δ=0.01). Bo |
| 200 | 88.4 | NE | 0.33 | 0.47 | -0.14 | 0.31 | 0.61 | NE-side hypothesis dominates (NE=0.47 > PE=0.33).  |
| 210 | 88.0 | ~ | 0.48 | 0.46 | +0.02 | 0.31 | 0.60 | Mixed PE/NE signals (PE=0.48, NE=0.46, Δ=0.02). Bo |
| 212 | 92.7 | NE | 0.25 | 0.30 | -0.04 | 0.14 | 0.30 | Mixed PE/NE signals (PE=0.25, NE=0.30, Δ=0.04). Bo |
| 213 | 92.7 | NE | 0.24 | 0.30 | -0.05 | 0.13 | 0.30 | Mixed PE/NE signals (PE=0.24, NE=0.30, Δ=0.05). Bo |
| 220 | 87.5 | NE | 0.43 | 0.50 | -0.07 | 0.31 | 0.66 | Mixed PE/NE signals (PE=0.43, NE=0.50, Δ=0.07). Bo |
| 230 | 87.1 | NE | 0.38 | 0.51 | -0.13 | 0.31 | 0.67 | NE-side hypothesis dominates (NE=0.51 > PE=0.38).  |
| 240 | 86.6 | ~ | 0.44 | 0.46 | -0.02 | 0.31 | 0.66 | Mixed PE/NE signals (PE=0.44, NE=0.46, Δ=0.02). Bo |
| 250 | 86.1 | NE | 0.38 | 0.51 | -0.13 | 0.31 | 0.67 | NE-side hypothesis dominates (NE=0.51 > PE=0.38).  |
| 260 | 85.6 | NE | 0.43 | 0.51 | -0.08 | 0.31 | 0.67 | NE-side hypothesis dominates (NE=0.51 > PE=0.43).  |
| 270 | 85.2 | NE | 0.43 | 0.51 | -0.08 | 0.31 | 0.67 | NE-side hypothesis dominates (NE=0.51 > PE=0.43).  |
| 280 | 84.6 | NE | 0.43 | 0.51 | -0.08 | 0.31 | 0.67 | NE-side hypothesis dominates (NE=0.51 > PE=0.43).  |
| 290 | 84.1 | NE | 0.33 | 0.52 | -0.19 | 0.31 | 0.68 | NE-side hypothesis dominates (NE=0.52 > PE=0.33).  |
| 300 | 83.6 | NE | 0.38 | 0.50 | -0.12 | 0.31 | 0.66 | NE-side hypothesis dominates (NE=0.50 > PE=0.38).  |
| 310 | 83.0 | NE | 0.38 | 0.51 | -0.13 | 0.31 | 0.66 | NE-side hypothesis dominates (NE=0.51 > PE=0.38).  |
| 317 | 88.8 | NE | 0.43 | 0.46 | -0.03 | 0.31 | 0.53 | Mixed PE/NE signals (PE=0.43, NE=0.46, Δ=0.03). Bo |
| 318 | 89.0 | NE | 0.38 | 0.48 | -0.10 | 0.31 | 0.56 | NE-side hypothesis dominates (NE=0.48 > PE=0.38).  |
| 330 | 82.0 | NE | 0.33 | 0.52 | -0.19 | 0.31 | 0.68 | NE-side hypothesis dominates (NE=0.52 > PE=0.33).  |
| 340 | 81.1 | NE | 0.33 | 0.49 | -0.17 | 0.31 | 0.65 | NE-side hypothesis dominates (NE=0.49 > PE=0.33).  |
| 350 | 80.3 | NE | 0.38 | 0.48 | -0.10 | 0.31 | 0.63 | NE-side hypothesis dominates (NE=0.48 > PE=0.38).  |
| 360 | 79.3 | NE | 0.26 | 0.51 | -0.24 | 0.22 | 0.57 | NE-side hypothesis dominates (NE=0.51 > PE=0.26).  |
| 370 | 78.3 | ~ | 0.43 | 0.43 | -0.01 | 0.31 | 0.56 | Mixed PE/NE signals (PE=0.43, NE=0.43, Δ=0.01). Bo |
| 380 | 77.3 | NE | 0.26 | 0.41 | -0.15 | 0.22 | 0.52 | NE-side hypothesis dominates (NE=0.41 > PE=0.26).  |
| 390 | 76.1 | PE | 0.43 | 0.40 | +0.03 | 0.31 | 0.51 | Mixed PE/NE signals (PE=0.43, NE=0.40, Δ=0.03). Bo |
| 400 | 75.1 | PE | 0.49 | 0.36 | +0.14 | 0.31 | 0.51 | PE-side hypothesis dominates (PE=0.49 > NE=0.36).  |
| 410 | 74.1 | PE | 0.49 | 0.32 | +0.17 | 0.31 | 0.46 | PE-side hypothesis dominates (PE=0.49 > NE=0.32).  |
| 420 | 73.2 | PE | 0.49 | 0.33 | +0.16 | 0.31 | 0.48 | PE-side hypothesis dominates (PE=0.49 > NE=0.33).  |
| 422 | 79.5 | PE | 0.53 | 0.47 | +0.06 | 0.31 | 0.61 | Mixed PE/NE signals (PE=0.53, NE=0.47, Δ=0.06). Bo |
| 423 | 80.3 | NE | 0.47 | 0.52 | -0.06 | 0.31 | 0.63 | Mixed PE/NE signals (PE=0.47, NE=0.52, Δ=0.06). Bo |
| 430 | 73.7 | PE | 0.49 | 0.36 | +0.13 | 0.31 | 0.51 | PE-side hypothesis dominates (PE=0.49 > NE=0.36).  |
| 440 | 72.3 | PE | 0.43 | 0.34 | +0.09 | 0.31 | 0.48 | PE-side hypothesis dominates (PE=0.43 > NE=0.34).  |
| 450 | 71.4 | PE | 0.38 | 0.33 | +0.05 | 0.31 | 0.47 | Mixed PE/NE signals (PE=0.38, NE=0.33, Δ=0.05). Bo |
| 460 | 70.6 | PE | 0.43 | 0.34 | +0.09 | 0.31 | 0.48 | PE-side hypothesis dominates (PE=0.43 > NE=0.34).  |
| 470 | 69.9 | PE | 0.38 | 0.34 | +0.04 | 0.31 | 0.48 | Mixed PE/NE signals (PE=0.38, NE=0.34, Δ=0.04). Bo |
| 480 | 69.3 | PE | 0.43 | 0.34 | +0.09 | 0.31 | 0.48 | PE-side hypothesis dominates (PE=0.43 > NE=0.34).  |
| 490 | 68.6 | PE | 0.38 | 0.33 | +0.04 | 0.31 | 0.48 | Mixed PE/NE signals (PE=0.38, NE=0.33, Δ=0.04). Bo |
| 500 | 68.1 | PE | 0.43 | 0.33 | +0.09 | 0.31 | 0.48 | PE-side hypothesis dominates (PE=0.43 > NE=0.33).  |
| 510 | 67.6 | PE | 0.43 | 0.33 | +0.10 | 0.31 | 0.48 | PE-side hypothesis dominates (PE=0.43 > NE=0.33).  |
| 520 | 67.1 | NE | 0.33 | 0.36 | -0.03 | 0.31 | 0.52 | Mixed PE/NE signals (PE=0.33, NE=0.36, Δ=0.03). Bo |
| 527 | 72.2 | NE | 0.43 | 0.48 | -0.05 | 0.31 | 0.63 | Mixed PE/NE signals (PE=0.43, NE=0.48, Δ=0.05). Bo |
| 528 | 72.7 | PE | 0.48 | 0.46 | +0.02 | 0.31 | 0.65 | Mixed PE/NE signals (PE=0.48, NE=0.46, Δ=0.02). Bo |
| 540 | 66.7 | PE | 0.38 | 0.34 | +0.04 | 0.31 | 0.48 | Mixed PE/NE signals (PE=0.38, NE=0.34, Δ=0.04). Bo |
| 550 | 66.1 | PE | 0.38 | 0.33 | +0.05 | 0.31 | 0.46 | Mixed PE/NE signals (PE=0.38, NE=0.33, Δ=0.05). Bo |
| 560 | 65.6 | NE | 0.33 | 0.37 | -0.04 | 0.31 | 0.53 | Mixed PE/NE signals (PE=0.33, NE=0.37, Δ=0.04). Bo |
| 561 | 65.6 | NE | 0.33 | 0.36 | -0.03 | 0.31 | 0.52 | Mixed PE/NE signals (PE=0.33, NE=0.36, Δ=0.03). Bo |
| 562 | 65.5 | NE | 0.33 | 0.38 | -0.05 | 0.31 | 0.54 | Mixed PE/NE signals (PE=0.33, NE=0.38, Δ=0.05). Bo |
| 563 | 65.5 | NE | 0.33 | 0.37 | -0.04 | 0.31 | 0.52 | Mixed PE/NE signals (PE=0.33, NE=0.37, Δ=0.04). Bo |
| 564 | 65.4 | NE | 0.33 | 0.37 | -0.04 | 0.31 | 0.52 | Mixed PE/NE signals (PE=0.33, NE=0.37, Δ=0.04). Bo |


> ASSB Si-rich: 관측 피크≈PE; `contact_loss`→NE(기계적 접촉) 가설. 절대 LAM%는 aged 하프셀 전까지 보고하지 않음. lean은 PE−NE 상대 비교.