# Spec: Voltage Cliffs — Physics Interpretation

**Status:** Draft · 사용자 방향 반영 (2026-06-26)

---

## 가설

동일 활물질(NMC811, LFP, …)이면 loading·area·stack 등 **설계가 조금 달라도** 열화에 따른 VP 변화 패턴(peak 이동, cliff 출현·이동)은 **유사한 궤적**을 가질 수 있다.

→ Reference를 `lot_id`가 아니라 **`chemistry` + 정규화 좌표** 로 잡는다.

---

## Cliff 정의 (알고리즘)

CC 구간 V(Q)에서:

1. `dVdQ = dV/dQ` (용량 미분 기준)
2. **Cliff 후보:** `|dVdQ|` 가 local maximum이고 threshold 초과
   - `|dVdQ| > k × median(|dVdQ|)` (k≈3) 또는 prominence 기반
3. 각 cliff에 대해 기록:
   - `V_cliff`, `Q_cliff`, `SOC_norm = Q_cliff/Q_max`
   - `slope = dVdQ` (부호 포함: discharge에서 음 = 전압 하강)
   - `width_Q`: |dVdQ| > half-max 인 Q 폭
   - `leg`: charge / discharge

**Plateau vs cliff:** plateau는 `|dVdQ| ≈ 0` 넓은 구간; cliff는 좁고 가파른 구간.

---

## 물리 해석 맵 (후보 — cathode intercalation 기준)

> 단일 VP만으로 확정 진단 불가. **후보 메커니즘 + 신뢰도** 로 리포트.

### Discharge (전압 하강 방향)

| 전압 구간 (예: NMC) | Cliff / 급강하 시 흔한 해석 | 열화 시 변화 |
|---------------------|------------------------------|--------------|
| 고전압 shoulder (~4.0–4.2 V) | H1↔H2 상 전이, particle별 불균일 | peak/blunting, cliff 완만해짐 |
| 중전압 (~3.6–3.8 V) | 주 intercalation plateau 끝 | plateau 축소, cliff V 이동 |
| 저전압 tail | 활물질 미활용·kinetic limit, Li inventory loss | tail cliff 앞당겨짐, Q_max ↓ |

### Charge

| 구간 | 해석 | 주의 |
|------|------|------|
| 고전압 급상승/꺾임 | CV 진입, concentration polarization | 설계·C-rate 의존 |
| 중전압 cliff | 상전이 (discharge 대칭) | |
| 이상 고전압 shoulder | Li plating **의심** (저온·고율) | 온도·protocol 확인 |

### 설계·비물리적 요인 (cliff 오인 방지)

- **IR drop** (leg 초반): contact, tab resistance — `ir_drop_proxy` 와 분리
- **CV 구간**: CC에서만 cliff 탐지 (`cc_only=True`)
- **N/P, limiting electrode** 바뀌면 cliff V가 shift — chemistry reference에 N/P band 메타데이터

---

## Cross-design 정규화

| 방법 | 용도 |
|------|------|
| `Q_norm = Q/Q_max` | 용량 스케일 제거 |
| `V` 절대값 + **dQ/dV peak V 정렬** | 물질 fingerprint 앵커 |
| `ΔV` vs chemistry reference curve (DTW on Q_norm) | 설계 무관 shape 비교 |
| `loading`, `area`를 메타 feature | 같은 chemistry 내 잔차 보정 |

**Material reference:** chemistry별 dQ/dV golden + cliff catalog (위치, 평균 width).

---

## Cycle trajectory features (열화 거동)

단일 사이클이 아니라 **cliff가 cycle에 따라 어떻게 움직이는지**:

| ID | Feature | 의미 |
|----|---------|------|
| C1 | `cliff1_V_drift` | cycle N vs 1 의 V_cliff 차 |
| C2 | `cliff1_width_growth` | cliff 폭 증가 (inhomogeneity) |
| C3 | `new_cliff_count` | reference에 없던 cliff 출현 |
| C4 | `plateau_Q_loss` | plateau 구간 Q_max 감소율 |

→ “비슷한 열화 거동” = **C1–C4 궤적**이 chemistry reference envelope 안에 있는지.

---

## 리포트 형식 (목표)

```
Cell A01, cycle 50, discharge
  Cliff #1 @ 3.72 V (SOC_norm 0.45), slope -0.8 V/mAh, width 0.12 mAh
    → 후보: 중전압 plateau 종료 / active material utilization loss
    → vs NMC811 ref: V shifted -15 mV from cycle 3 (aging signal)
```

---

## 구현 Phase

1. Phase 1b: cliff detector + scalar features (V, Q, width, slope)
2. Phase 1c: chemistry reference JSON + drift vs ref
3. Phase 2: multi-cycle trajectory clustering (같은 chemistry 설계들)
4. Phase 3: labeled mechanism map (전문가 라벨로 맵 보정)
