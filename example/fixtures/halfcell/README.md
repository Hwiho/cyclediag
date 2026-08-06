# Half-cell BOL OCP fixtures (pristine / early cycles)

**Status (2026-08-06):** 양·음극 **하프셀 데이터가 존재한다.**  
로컬 원본: `C:\Halfcell` → 이 폴더에 BOL(초기) fixture로 게시.

| | |
|--|--|
| Rate | **C/20** (저율 / pseudo-OCV용) |
| Coverage | **초기(첫) 사이클** — 음극 CSV는 **cycle 1–3** 확인 |
| Aged / harvested | **없음** — 열화 후 하프셀·disassembly OCP는 아직 없음 |
| 용도 | DM-P3 OCP library · full-cell↔half-cell DMA 교정 입력 (PyDMA/PyProBE 참고) |

> Full-cell 진단(F1–F8)은 하프셀 없이도 진행한다.  
> 하프셀은 **검증·교정**용이다. 열화 후 하프셀이 생기면 이 폴더에 `aged/`를 추가한다.

## Contents

### Anode — SJ1300 / Si-rich (`anode_SJ1300/`)

BioLogic txt → `convert_halfcell_to_pne.py` → PNE-like `*_raw.csv`.

| File | Voltage window | Cycles in CSV |
|------|----------------|---------------|
| `55mV-1.5V_AHC_#4_C09_C10_C11_raw.csv` | ~0.055–1.70 V | 1, 2, 3 |
| `5mV-1.5V_AHC_#4_C09_C10_raw.csv` | ~0.005–1.82 V | 1, 2, 3 |
| `75mV-1_C09_raw.csv` | ~0.075–1.82 V | 1, 2, 3 |

Columns: `TotalCycle,Voltage,Capacity,StepType,TotalTime_sec`

### Cathode (`cathode_halfcell/`)

`source/cathode_halfcell.xlsx`에서 변환.

| File | Notes |
|------|--------|
| `cathode_halfcell_ch1_raw.csv` | ~3.40–4.25 V, charge leg (현재 CSV는 cycle 1) |
| `cathode_halfcell_ch2_raw.csv` | ~3.00–4.24 V, discharge leg (현재 CSV는 cycle 1) |

> **주의:** 현 xlsx export는 채널당 ~216 s 분량으로, 음극처럼 cycle 1–3이 모두 들어 있지 않을 수 있다.  
> OCP **형상** 라이브러리로는 사용 가능. 절대 용량·다중 사이클이 필요하면 BioLogic 원본으로 재변환 권장.

### Source / tools

| Path | Description |
|------|-------------|
| `source/cathode_halfcell.xlsx` | Cathode raw workbook |
| `source/SJ900_anode_halfcell.xlsx` | SJ900 anode workbook (별도; CSV 변환본은 SJ1300 폴더 위주) |
| `convert_halfcell_to_pne.py` | BioLogic txt / cathode xlsx → `*_raw.csv` |

목록: [`manifest.json`](manifest.json)

## Git LFS

```bash
git lfs install
git lfs pull
```

`example/fixtures/halfcell/**/*.csv` 및 `source/**/*.xlsx`는 LFS 추적.

## Relation to CycleDiag

- Planning: `cyclediag/planning/IMPROVEMENT_ROADMAP.md` §0 (full-cell first), §12.3–12.4 (DMA)
- Policy: `cyclediag/planning/LLI_LAM_DIAGNOSIS.md` — Level 3 `*_est_hc_calibrated`는 이 BOL OCP + (향후) aged 데이터로 채움
- **아직 없는 것:** aged half-cell OCP after cycling
