# Ch022 / Ch024 전극 가설 진단 요약 (v1.3 · Si-on-Gr · NCM82)

- PDF: `ASSB_SJ900_Ch022_Ch024_electrode_diagnosis_report.pdf`
- 계획: `cyclediag/planning/VALIDATION_IMPROVEMENT_PLAN_v1_3.md`
- Level: `hypothesis_bol_ocp` · methodology `electrode_side_v1_3`
- Chemistry: **Si coating on graphite** · **NCM82 secondary particles**

## 검증에서 고친 것
| ID | 이슈 | 조치 |
|---|---|---|
| C1 | residual argmax = DOD | SOC=100−DOD |
| C2 | Q_relax가 routine에 없음 | RPT→routine forward-fill (coverage=1.0) |
| C3 | Si-rich 언어 | Si_on_Gr 레지스트리·서사 |
| C4 | baseline R 없을 때 absolute R | term skip |
| H1/H2 | Si 이중계산 · peak 혼매칭 | co-sign 분리 · charge unique FC hits |

## 결론 (routine only)
- **Ch022:** 초반 PE → 중기(~120–210) contact↔PE mixed (si≈0.4) → knee≈350 이후 PE activity lean
- **Ch024:** 유사하나 PE lean이 더 이름(≈290+)
- C/3 RPT bump = rate gap (+3~7%p), 회복 아님
- 절대 LAM% / “음극 확정” 금지
