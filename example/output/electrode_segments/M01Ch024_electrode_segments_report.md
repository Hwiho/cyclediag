# 열화 구간별 양·음극 가설 진단 — M01Ch024

- Level: **hypothesis_bol_ocp** (aged 하프셀 교정 아님)
- OCP library: anode=18 cathode=2 aged=False
- 분석 포인트: 66 cycles sampled; 세그먼트는 SoHQ≥50 capa-like

## 구간 요약 (패턴·양음극 지배 전환)

### Seg 1: cycle 2–10 · 양극(PE) 지배
- SoHQ: 100.6% → 95.7% (3 points)
- 점수: PE=0.32 / NE=0.29 / shared=0.03 (Δ=0.02, conf=0.62)
- **이 구간 상대 지배: 양극(PE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.21, contact_loss=0.31, LLI=0.00

### Seg 2: cycle 20–90 · 양극(PE) 지배
- SoHQ: 94.9% → 92.3% (8 points)
- 점수: PE=0.42 / NE=0.37 / shared=0.09 (Δ=0.05, conf=0.59)
- **이 구간 상대 지배: 양극(PE)** (강도: 중간, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.28, contact_loss=0.42, LLI=0.35

### Seg 3: cycle 100–200 · 양·음극 혼합(근소)
- SoHQ: 91.8% → 87.3% (12 points)
- 점수: PE=0.40 / NE=0.41 / shared=0.10 (Δ=0.01, conf=0.49)
- **이 구간 상대 지배: 음극(NE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.16, contact_loss=0.40, LLI=0.27

### Seg 4: cycle 210–230 · 양극(PE) 지배
- SoHQ: 86.7% → 85.7% (5 points)
- 점수: PE=0.41 / NE=0.39 / shared=0.10 (Δ=0.02, conf=0.60)
- **이 구간 상대 지배: 양극(PE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.29, contact_loss=0.39, LLI=0.39

### Seg 5: cycle 240–260 · 음극(NE) 지배
- SoHQ: 85.0% → 83.8% (3 points)
- 점수: PE=0.38 / NE=0.47 / shared=0.13 (Δ=0.09, conf=0.64)
- **이 구간 상대 지배: 음극(NE)** (강도: 명확, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.59, LLI=0.44

### Seg 6: cycle 270–317 · 양·음극 혼합(근소)
- SoHQ: 83.0% → 85.2% (6 points)
- 점수: PE=0.42 / NE=0.42 / shared=0.13 (Δ=0.00, conf=0.49)
- **이 구간 상대 지배: 음극(NE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.55, LLI=0.50

### Seg 7: cycle 318–330 · 양·음극 혼합(근소)
- SoHQ: 85.7% → 77.8% (2 points)
- 점수: PE=0.42 / NE=0.42 / shared=0.11 (Δ=0.00, conf=0.49)
- **이 구간 상대 지배: 음극(NE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.30, contact_loss=0.51, LLI=0.46

### Seg 8: cycle 340–350 · 음극(NE) 지배
- SoHQ: 76.5% → 75.3% (2 points)
- 점수: PE=0.26 / NE=0.37 / shared=0.13 (Δ=0.10, conf=0.64)
- **이 구간 상대 지배: 음극(NE)** (강도: 명확, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.22, contact_loss=0.43, LLI=0.54

### Seg 9: cycle 360–410 · 양극(PE) 지배
- SoHQ: 74.1% → 69.7% (6 points)
- 점수: PE=0.37 / NE=0.29 / shared=0.10 (Δ=0.08, conf=0.60)
- **이 구간 상대 지배: 양극(PE)** (강도: 중간, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.41, LLI=0.41

### Seg 10: cycle 420–480 · 양극(PE) 지배
- SoHQ: 69.0% → 66.0% (9 points)
- 점수: PE=0.37 / NE=0.33 / shared=0.10 (Δ=0.04, conf=0.50)
- **이 구간 상대 지배: 양극(PE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.46, LLI=0.36

### Seg 11: cycle 490–520 · 양극(PE) 지배
- SoHQ: 65.5% → 64.1% (4 points)
- 점수: PE=0.34 / NE=0.31 / shared=0.09 (Δ=0.03, conf=0.48)
- **이 구간 상대 지배: 양극(PE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.42, LLI=0.36

### Seg 12: cycle 526–533 · 양·음극 혼합(근소)
- SoHQ: 63.9% → 64.3% (5 points)
- 점수: PE=0.39 / NE=0.38 / shared=0.08 (Δ=0.01, conf=0.45)
- **이 구간 상대 지배: 양극(PE)** (강도: 약함/근소, 가설)
- 모드: PE=`LAM_PE` · NE=`contact_loss` · shared=`LLI,interface_R,SE_decomposition,microshort`
- pattern: LAM_PE=0.31, contact_loss=0.57, LLI=0.35

## 수명 단계 롤업

- **early (1/3)** cyc 2–180: PE=0.39 NE=0.38 → **양극(PE)** (SoHQ 101→88%)
- **mid (1/3)** cyc 190–370: PE=0.40 NE=0.40 → **음극(NE)** (SoHQ 88→73%)
- **late (1/3)** cyc 380–533: PE=0.36 NE=0.33 → **양극(PE)** (SoHQ 72→64%)

## 사이클 궤적 (용량 사이클)

| cycle | SoHQ | lean | PE | NE | Δ | LAM_PE | contact | note |
|------:|-----:|:-----|---:|---:|--:|-------:|--------:|:-----|
| 2 | 100.6 | PE | 0.39 | 0.26 | +0.13 | 0.21 | 0.31 | PE-side hypothesis dominates (PE=0.39 > NE=0.26).  |
| 3 | 100.0 | NE | 0.25 | 0.31 | -0.06 | 0.00 | 0.32 | Mixed PE/NE signals (PE=0.25, NE=0.31, Δ=0.06). Bo |
| 10 | 95.7 | ~ | 0.30 | 0.31 | -0.01 | 0.29 | 0.39 | Mixed PE/NE signals (PE=0.30, NE=0.31, Δ=0.01). Bo |
| 20 | 94.9 | PE | 0.34 | 0.31 | +0.03 | 0.27 | 0.38 | Mixed PE/NE signals (PE=0.34, NE=0.31, Δ=0.03). Bo |
| 30 | 94.5 | PE | 0.41 | 0.31 | +0.10 | 0.28 | 0.38 | PE-side hypothesis dominates (PE=0.41 > NE=0.31).  |
| 40 | 94.1 | PE | 0.42 | 0.31 | +0.11 | 0.29 | 0.38 | PE-side hypothesis dominates (PE=0.42 > NE=0.31).  |
| 50 | 93.8 | PE | 0.40 | 0.31 | +0.10 | 0.27 | 0.38 | PE-side hypothesis dominates (PE=0.40 > NE=0.31).  |
| 60 | 93.4 | PE | 0.47 | 0.31 | +0.16 | 0.29 | 0.38 | PE-side hypothesis dominates (PE=0.47 > NE=0.31).  |
| 70 | 93.1 | PE | 0.50 | 0.48 | +0.02 | 0.27 | 0.63 | Mixed PE/NE signals (PE=0.50, NE=0.48, Δ=0.02). Bo |
| 80 | 92.7 | ~ | 0.46 | 0.47 | -0.01 | 0.28 | 0.61 | Mixed PE/NE signals (PE=0.46, NE=0.47, Δ=0.01). Bo |
| 90 | 92.3 | NE | 0.38 | 0.45 | -0.07 | 0.31 | 0.58 | Mixed PE/NE signals (PE=0.38, NE=0.45, Δ=0.07). Bo |
| 100 | 91.8 | ~ | 0.47 | 0.46 | +0.01 | 0.29 | 0.59 | Mixed PE/NE signals (PE=0.47, NE=0.46, Δ=0.01). Bo |
| 107 | 95.3 | ~ | 0.29 | 0.30 | -0.01 | 0.05 | 0.31 | Mixed PE/NE signals (PE=0.29, NE=0.30, Δ=0.01). Bo |
| 108 | 95.3 | ~ | 0.30 | 0.30 | -0.00 | 0.14 | 0.31 | Mixed PE/NE signals (PE=0.30, NE=0.30, Δ=0.00). Bo |
| 120 | 91.1 | PE | 0.47 | 0.44 | +0.03 | 0.30 | 0.57 | Mixed PE/NE signals (PE=0.47, NE=0.44, Δ=0.03). Bo |
| 130 | 90.6 | NE | 0.26 | 0.43 | -0.17 | 0.22 | 0.55 | NE-side hypothesis dominates (NE=0.43 > PE=0.26).  |
| 140 | 90.2 | ~ | 0.43 | 0.42 | +0.00 | 0.31 | 0.55 | Mixed PE/NE signals (PE=0.43, NE=0.42, Δ=0.00). Bo |
| 150 | 89.7 | PE | 0.47 | 0.41 | +0.06 | 0.30 | 0.53 | Mixed PE/NE signals (PE=0.47, NE=0.41, Δ=0.06). Bo |
| 160 | 89.3 | NE | 0.38 | 0.45 | -0.07 | 0.31 | 0.58 | Mixed PE/NE signals (PE=0.38, NE=0.45, Δ=0.07). Bo |
| 170 | 88.8 | ~ | 0.43 | 0.42 | +0.01 | 0.31 | 0.54 | Mixed PE/NE signals (PE=0.43, NE=0.42, Δ=0.01). Bo |
| 180 | 88.3 | NE | 0.38 | 0.44 | -0.06 | 0.31 | 0.57 | Mixed PE/NE signals (PE=0.38, NE=0.44, Δ=0.06). Bo |
| 190 | 87.7 | PE | 0.49 | 0.39 | +0.10 | 0.31 | 0.55 | PE-side hypothesis dominates (PE=0.49 > NE=0.39).  |
| 200 | 87.3 | ~ | 0.43 | 0.43 | -0.01 | 0.31 | 0.56 | Mixed PE/NE signals (PE=0.43, NE=0.43, Δ=0.01). Bo |
| 210 | 86.7 | PE | 0.48 | 0.43 | +0.05 | 0.31 | 0.56 | Mixed PE/NE signals (PE=0.48, NE=0.43, Δ=0.05). Bo |
| 212 | 92.1 | PE | 0.39 | 0.29 | +0.09 | 0.25 | 0.30 | PE-side hypothesis dominates (PE=0.39 > NE=0.29).  |
| 213 | 92.0 | PE | 0.38 | 0.34 | +0.04 | 0.31 | 0.30 | Mixed PE/NE signals (PE=0.38, NE=0.34, Δ=0.04). Bo |
| 220 | 86.2 | NE | 0.38 | 0.44 | -0.06 | 0.31 | 0.56 | Mixed PE/NE signals (PE=0.38, NE=0.44, Δ=0.06). Bo |
| 230 | 85.7 | ~ | 0.43 | 0.44 | -0.01 | 0.31 | 0.56 | Mixed PE/NE signals (PE=0.43, NE=0.44, Δ=0.01). Bo |
| 240 | 85.0 | NE | 0.38 | 0.52 | -0.14 | 0.31 | 0.59 | NE-side hypothesis dominates (NE=0.52 > PE=0.38).  |
| 250 | 84.4 | NE | 0.38 | 0.45 | -0.07 | 0.31 | 0.59 | Mixed PE/NE signals (PE=0.38, NE=0.45, Δ=0.07). Bo |
| 260 | 83.8 | NE | 0.38 | 0.45 | -0.07 | 0.31 | 0.58 | Mixed PE/NE signals (PE=0.38, NE=0.45, Δ=0.07). Bo |
| 270 | 83.0 | ~ | 0.43 | 0.44 | -0.01 | 0.31 | 0.56 | Mixed PE/NE signals (PE=0.43, NE=0.44, Δ=0.01). Bo |
| 280 | 82.2 | ~ | 0.43 | 0.42 | +0.01 | 0.31 | 0.54 | Mixed PE/NE signals (PE=0.43, NE=0.42, Δ=0.01). Bo |
| 290 | 81.3 | NE | 0.38 | 0.41 | -0.03 | 0.31 | 0.52 | Mixed PE/NE signals (PE=0.38, NE=0.41, Δ=0.03). Bo |
| 300 | 80.2 | ~ | 0.38 | 0.39 | -0.02 | 0.31 | 0.50 | Mixed PE/NE signals (PE=0.38, NE=0.39, Δ=0.02). Bo |
| 310 | 79.1 | NE | 0.38 | 0.42 | -0.04 | 0.31 | 0.45 | Mixed PE/NE signals (PE=0.38, NE=0.42, Δ=0.04). Bo |
| 317 | 85.2 | PE | 0.52 | 0.46 | +0.06 | 0.30 | 0.54 | Mixed PE/NE signals (PE=0.52, NE=0.46, Δ=0.06). Bo |
| 318 | 85.7 | ~ | 0.46 | 0.47 | -0.01 | 0.30 | 0.54 | Mixed PE/NE signals (PE=0.46, NE=0.47, Δ=0.01). Bo |
| 330 | 77.8 | ~ | 0.38 | 0.37 | +0.01 | 0.31 | 0.47 | Mixed PE/NE signals (PE=0.38, NE=0.37, Δ=0.01). Bo |
| 340 | 76.5 | NE | 0.26 | 0.34 | -0.08 | 0.22 | 0.43 | Mixed PE/NE signals (PE=0.26, NE=0.34, Δ=0.08). Bo |
| 350 | 75.3 | NE | 0.26 | 0.39 | -0.13 | 0.22 | 0.44 | NE-side hypothesis dominates (NE=0.39 > PE=0.26).  |
| 360 | 74.1 | PE | 0.49 | 0.30 | +0.19 | 0.31 | 0.43 | PE-side hypothesis dominates (PE=0.49 > NE=0.30).  |
| 370 | 73.2 | PE | 0.38 | 0.28 | +0.10 | 0.31 | 0.40 | PE-side hypothesis dominates (PE=0.38 > NE=0.28).  |
| 380 | 72.3 | PE | 0.43 | 0.29 | +0.14 | 0.31 | 0.41 | PE-side hypothesis dominates (PE=0.43 > NE=0.29).  |
| 390 | 71.4 | PE | 0.38 | 0.27 | +0.11 | 0.31 | 0.38 | PE-side hypothesis dominates (PE=0.38 > NE=0.27).  |
| 400 | 70.4 | PE | 0.33 | 0.31 | +0.02 | 0.31 | 0.44 | Mixed PE/NE signals (PE=0.33, NE=0.31, Δ=0.02). Bo |
| 410 | 69.7 | NE | 0.21 | 0.30 | -0.08 | 0.22 | 0.42 | NE-side hypothesis dominates (NE=0.30 > PE=0.21).  |
| 420 | 69.0 | PE | 0.33 | 0.30 | +0.03 | 0.31 | 0.43 | Mixed PE/NE signals (PE=0.33, NE=0.30, Δ=0.03). Bo |
| 422 | 74.5 | PE | 0.48 | 0.44 | +0.04 | 0.31 | 0.57 | Mixed PE/NE signals (PE=0.48, NE=0.44, Δ=0.04). Bo |
| 423 | 74.9 | PE | 0.48 | 0.43 | +0.05 | 0.31 | 0.55 | Mixed PE/NE signals (PE=0.48, NE=0.43, Δ=0.05). Bo |
| 430 | 69.2 | PE | 0.33 | 0.30 | +0.03 | 0.31 | 0.43 | Mixed PE/NE signals (PE=0.33, NE=0.30, Δ=0.03). Bo |
| 440 | 68.3 | PE | 0.33 | 0.30 | +0.03 | 0.31 | 0.43 | Mixed PE/NE signals (PE=0.33, NE=0.30, Δ=0.03). Bo |
| 450 | 67.6 | PE | 0.38 | 0.29 | +0.08 | 0.31 | 0.42 | PE-side hypothesis dominates (PE=0.38 > NE=0.29).  |
| 460 | 67.0 | PE | 0.33 | 0.28 | +0.04 | 0.31 | 0.41 | Mixed PE/NE signals (PE=0.33, NE=0.28, Δ=0.04). Bo |
| 470 | 66.5 | PE | 0.33 | 0.29 | +0.04 | 0.31 | 0.42 | Mixed PE/NE signals (PE=0.33, NE=0.29, Δ=0.04). Bo |
| 480 | 66.0 | NE | 0.33 | 0.35 | -0.02 | 0.31 | 0.42 | Mixed PE/NE signals (PE=0.33, NE=0.35, Δ=0.02). Bo |
| 490 | 65.5 | PE | 0.33 | 0.29 | +0.04 | 0.31 | 0.41 | Mixed PE/NE signals (PE=0.33, NE=0.29, Δ=0.04). Bo |
| 500 | 65.0 | PE | 0.33 | 0.30 | +0.02 | 0.31 | 0.44 | Mixed PE/NE signals (PE=0.33, NE=0.30, Δ=0.02). Bo |
| 510 | 64.6 | ~ | 0.33 | 0.32 | +0.01 | 0.31 | 0.45 | Mixed PE/NE signals (PE=0.33, NE=0.32, Δ=0.01). Bo |
| 520 | 64.1 | PE | 0.38 | 0.33 | +0.05 | 0.31 | 0.47 | Mixed PE/NE signals (PE=0.38, NE=0.33, Δ=0.05). Bo |
| 526 | 63.9 | ~ | 0.33 | 0.33 | +0.00 | 0.31 | 0.47 | Mixed PE/NE signals (PE=0.33, NE=0.33, Δ=0.00). Bo |
| 527 | 68.5 | ~ | 0.48 | 0.48 | +0.00 | 0.31 | 0.62 | Mixed PE/NE signals (PE=0.48, NE=0.48, Δ=0.00). Bo |
| 528 | 68.9 | ~ | 0.43 | 0.44 | -0.01 | 0.31 | 0.63 | Mixed PE/NE signals (PE=0.43, NE=0.44, Δ=0.01). Bo |
| 532 | 64.5 | PE | 0.38 | 0.34 | +0.04 | 0.31 | 0.48 | Mixed PE/NE signals (PE=0.38, NE=0.34, Δ=0.04). Bo |
| 533 | 64.3 | ~ | 0.33 | 0.34 | -0.01 | 0.31 | 0.48 | Mixed PE/NE signals (PE=0.33, NE=0.34, Δ=0.01). Bo |


> ASSB Si-rich: 관측 피크≈PE; `contact_loss`→NE(기계적 접촉) 가설. 절대 LAM%는 aged 하프셀 전까지 보고하지 않음. lean은 PE−NE 상대 비교.