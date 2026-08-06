# VP Diagnosis — Label Taxonomy

라벨 전략은 [ROADMAP.md](ROADMAP.md) Phase 0에서 확정. 아래는 **초안**.

---

## Level 0 — 이진 (이상 탐지 MVP)

| Label | 설명 |
|-------|------|
| `normal` | golden/reference 대비 허용 범위 |
| `anomaly` | 명확한 이상 (원인 미분류) |

Unsupervised 모델은 라벨 없이 점수만 출력 → threshold로 위 이진 매핑.

---

## Level 1 — QC / 공정 (분류, supervised)

| Label | VP에서 흔한 신호 | 비고 |
|-------|------------------|------|
| `normal` | 기준 형태 | |
| `low_capacity` | Q_max ↓ | mass 오입력과 구분 필요 |
| `high_ir` | 초반 dV/dI ↑, IR proxy ↑ | 접촉 불량 |
| `cv_abnormal` | CV 시간·전류 decay 이상 | |
| `noisy` | dV/dQ·dQ/dV 스파이크 | 측정 노이즈 vs cell |
| `shape_shift` | plateau V 이동, peak 이동 | 화학·SOC 차이와 혼동 주의 |

---

## Level 2 — 실패 모드 (전문가 라벨, 데이터 충분 시)

| Label | 설명 |
|-------|------|
| `LLI` | Loss of Lithium Inventory (full-cell 추정 가능; half-cell로 교정) |
| `LAM_PE` | Positive active material loss |
| `LAM_NE` | Negative active material loss |
| `impedance_growth` | 저항·분극 성장 |
| `transport_limitation` | 수송/확산 제한 |
| `electrode_slippage` | 전극 window / stoichiometry shift |
| `soft_short` | 미세 단락 의심 |
| `li_plating` | 저온·고율 충전, dQ/dV 고전압 shoulder |
| `sei_growth` | impedance rise, hysteresis 증가 |
| `contact_loss` | 접촉·셀 수준 R 증가 의심 |
| `cathode_degradation` | peak fade / shift (LAM_PE와 연계) |
| `anode_degradation` | dV/dQ peak·cliff 변화 (LAM_NE와 연계) |

→ Phase 2 이후, 라벨당 최소 **~30 samples** 권장 (경험칙).

**출력 수준:** pattern score (`*_pattern_score`) → model estimate (`*_est`) → half-cell calibrated (`*_est_hc_calibrated`).  
정책: [LLI_LAM_DIAGNOSIS.md](LLI_LAM_DIAGNOSIS.md).

---

## Level 3 — 회귀 타깃 (수명)

| Target | 단위 | 설명 |
|--------|------|------|
| `soh` | 0–1 | 현재 Q / initial Q |
| `cycles_to_80` | int | 예측 (장기 과제) |

---

## 라벨링 규칙 (초안)

1. **단위:** `cell_id` + `cycle` (+ optional `leg`). 한 사이클에 charge/discharge 다르면 leg별 라벨.
2. **우선순위:** 실패 모드 > QC > binary. 복수 해당 시 `primary_label` + `secondary` JSON.
3. **불확실:** `label_confidence`: `high` / `medium` / `low` — low는 train에서 제외 옵션.
4. **출처:** `labeled_by`, `labeled_at` — manifest 또는 sidecar.

### Sidecar 예 (`cell_A01.labels.json`)

```json
{
  "cell_id": "A01",
  "entries": [
    {"cycle": 3, "leg": "discharge", "label": "normal", "confidence": "high"},
    {"cycle": 50, "leg": "discharge", "label": "low_capacity", "confidence": "medium", "note": "vs cycle 3 -8%"}
  ]
}
```

---

## 평가 시 주의

- **같은 셀**의 adjacent cycle은 상관 → **GroupKFold by cell_id**
- Formation cycle과 cycle life **분리 평가**
- Class imbalance → macro-F1, PR-AUC 병기

---

## 다음 결정 (NOTES.md)

- [ ] 실제 보유 라벨이 Level 0~2 중 어디까지인지
- [ ] `anomaly` 원인 불명 샘플을 train에 넣을지
