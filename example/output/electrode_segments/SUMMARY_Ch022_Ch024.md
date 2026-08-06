# Ch022 / Ch024 구간별 양·음극 가설 진단 (v1.1)

Level: `hypothesis_bol_ocp` · aged 하프셀 교정 아님  
도구: `cyclediag/tools/diagnose_electrode_segments.py`  
상세 CSV/MD: `example/output/electrode_segments/`

## 한줄 요약

| 셀 | 초·중기 | 전환 | 후기 |
|---|---|---|---|
| **Ch022** | 중기(~80–380) **음극(NE)** 명확 — contact_loss | ~cyc **390** | 후기(~390–550) **양극(PE)** 명확 |
| **Ch024** | 초기는 **양극(PE)** 경향 · 중기(~240–350) **음극** 구간 | ~cyc **360** | 후기(~360–EOL) **양극(PE)** |

둘 다 후반에 PE 쪽으로 기울지만, Ch022는 중기 NE(접촉 손실) 구간이 더 길고 강하다.

---

## M01Ch022 (SoHQ ~100% → ~65%)

| 구간 | cycle | SoHQ | 상대 지배 | 강도 | 비고 |
|---|---|---|---|---|---|
| 초반 | 2–70 | 101→93% | 혼합→**PE** | 약~명확 | 형성·조기 |
| NE 강화 | 80–380 | 93→77% | **음극(NE)** | 명확 | contact_loss↑ (0.5–0.7) |
| PE 전환 | 390–550 | 76→66% | **양극(PE)** | 명확 | LAM_PE 신호 + PE lean |
| EOL | 560–564 | ~65% | NE 근소 | 약 | 마진 작음 |

**수명 롤업:** early NE 근소 · mid **NE** · late **PE**

---

## M01Ch024 (SoHQ ~100% → ~64%)

| 구간 | cycle | SoHQ | 상대 지배 | 강도 | 비고 |
|---|---|---|---|---|---|
| 초반 | 2–90 | 101→92% | **양극(PE)** | 중 | PE lean |
| 중기 혼재 | 100–230 | 92→86% | 혼합 | 약 | PE↔NE 진동 |
| NE 구간 | 240–350 | 85→75% | **음극(NE)** | 명확 | contact_loss |
| PE 후기 | 360–533 | 74→64% | **양극(PE)** | 약~중 | 후반 PE lean |

**수명 롤업:** early **PE** · mid NE 근소 · late **PE**

---

## 해석 주의

- ASSB Si-rich: 관측 ICA 피크 ≈ PE; `contact_loss`는 **음극 기계적 접촉** 가설.
- 절대 LAM_PE / LAM_NE %는 aged 하프셀 전까지 **미보고**.
- lean = PE_side_score − NE_side_score (상대 비교).
