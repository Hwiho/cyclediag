# Ch022 / Ch024 전극 가설 진단 요약 (v1.1 검증개정)

- PDF: `ASSB_SJ900_Ch022_Ch024_electrode_diagnosis_report.pdf`
- 계획: `cyclediag/planning/VALIDATION_IMPROVEMENT_PLAN.md`
- Level: `hypothesis_bol_ocp` · methodology `electrode_side_v1_1`

## 검증으로 고친 것
| 이슈 | 조치 | 결과 |
|---|---|---|
| pulse 0.5×I | thr 0.75×I | pulse_frac ≈ 3% (구 ~98%) |
| LAM_PE≈0.31 천장 | weights/proxy/baseline | ceiling_frac=0, nunique≈전 구간 |
| FC↔cathode V 매칭 | synth FC-OCP + Δhits | 허위 PE pad 제거 |
| contact→NE 원형 | contact_stack + Si co-sign | NE_hyp 낮음, 과신 서사 제거 |

## 개정 결론
- **Ch022:** 초·중반 **contact_stack** 우위 → 후반 PE와 경합(mixed). “중기 음극 확정” 아님.
- **Ch024:** contact/mixed 후 후반(**≈360+**) PE 구간이 더 분명.
