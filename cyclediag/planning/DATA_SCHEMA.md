# VP Diagnosis — Data Schema

## 1. 입력: PNE Cycler CSV

pne_studio와 **동일 파일**을 읽되, cyclediag는 자체 파서를 사용한다.

### 필수 컬럼 (이름은 매핑 가능)

| 논리명 | 기본 컬럼명 예 | 타입 |
|--------|----------------|------|
| cycle | `CycleIndex` / `CycleNum` | int |
| voltage | `Voltage(V)` | float |
| capacity | `ChargeCapacity` / `DischargeCapacity` | float |
| step_type | `StepType` | str (`Charge` / `Discharge` / …) |

### 권장 컬럼

| 논리명 | 예 | 용도 |
|--------|-----|------|
| current | `Current(A)` | CC/CV 분리 |
| time | `TotalTime_sec` | CV 시간, rate |
| data_point | `Data_Point` | 정렬 |

### `_raw.csv` 추가

| 컬럼 | 용도 |
|------|------|
| `StepNo`, `CycleNum` | 사이클 매핑 |
| `TestType` (classification) | formation vs cycle |

→ `io/cycler_csv.py` 의 `ColumnMap` 으로 preset 제공 (`studio_default()` = PNE Studio / pne_studio2 UI columns).

---

## 2. Manifest (배치 처리)

여러 파일을 한 번에 처리할 때 `manifest.csv`:

```csv
file,cell_id,lot_id,label,active_mass_g,loading_mAh_cm2,cathode,notes
D:/data/cell_A01.csv,A01,lot2024Q1,normal,0.0123,3.5,NMC811,
D:/data/cell_B07.csv,B07,lot2024Q1,soft_short,0.0119,3.5,NMC811,visual swelling
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `file` | ✓ | CSV 경로 |
| `cell_id` | ✓ | 고유 셀 ID (CV split 단위) |
| `label` | | `normal`, `anomaly`, 또는 [LABELS.md](LABELS.md) taxonomy |
| `active_mass_g` | | F1.2 specific capacity |
| `lot_id`, `cathode`, … | | 그룹별 reference |

---

## 3. Golden Reference

Reference VP는 **JSON** 한 파일로 관리 (버전 포함):

```json
{
  "ref_id": "NMC811_3.5mg_formation_cycle3",
  "feature_set": "vp_v1_basic",
  "created": "2026-06-26",
  "source": "median of 12 normal cells, lot2024Q1",
  "features": {
    "Q_max": 4.12,
    "V_avg": 3.78,
    "peak1_V": 3.72
  },
  "vp_curve": {
    "q_norm": [0.0, 0.004, "..."],
    "v": [3.0, 3.1, "..."]
  }
}
```

---

## 4. Feature 출력

`features.parquet` (또는 `.csv`):

```
cell_id, file, cycle, leg, feature_set, f_Q_max, f_V_avg, ..., label
```

---

## 5. 모델 아티팩트

```
artifacts/
  vp_v1_basic/
    model.joblib          # sklearn / xgboost
    scaler.joblib
    feature_spec.json     # 사용 feature ID 목록 + 전처리 파라미터
    metrics.json          # val AUROC, F1, …
    training_manifest_hash.txt
```

---

## 6. 진단 리포트 (Phase 4)

`report_{cell_id}_{timestamp}.html`:

- 이상 점수, top contributing features
- VP vs golden overlay plot (matplotlib PNG embed)
- 사이클별 trend table

---

## 7. pne_studio와의 관계

| 항목 | cyclediag | pne_studio |
|------|---------|------------|
| CSV 읽기 | ✓ 자체 | ✓ |
| dQ/dV plot | 리포트용만 | ✓ 메인 |
| Mass / loading | manifest sidecar | ✓ UI |
| 코드 import | **금지** | — |

필요 시 pne_studio에서 export한 PNG/CSV를 **수동**으로 manifest에 넣을 수 있으나 자동 연동은 범위 외.
