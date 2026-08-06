# Ch022 / Ch024 전극 가설 진단 요약 (v1.2 · C/3 RPT dual-track)

- PDF: `ASSB_SJ900_Ch022_Ch024_electrode_diagnosis_report.pdf`
- Level: `hypothesis_bol_ocp` · methodology `electrode_side_v1_2`

## 핵심 인식
중간 SoHQ “스파이크”는 노이즈가 아니라 **C/3 (~0.33C) RPT 용량**이다  
(|I|≈25.8 A vs routine 0.5C |I|≈38.7 A). Δ(RPT−routine) ≈ **+3~7%p**.

## 알고리즘 변경
| 트랙 | 용도 |
|---|---|
| `routine_05c` | fade / knee / lean / 세그먼트 |
| `rpt_c3` | SoHQ_rpt 앵커 · RCF · η(SOC) |
| `dcir_pulse` | R_ohmic/R_ct 분해 후 routine에 forward-fill (궤적 제외) |

## 개정 결론 (routine only)
- **Ch022:** 중기 **contact_stack** 고원 → knee≈350 이후 mixed → 후기(≈500+) **PE lean**. NE는 Si co-sign 있을 때만.
- **Ch024:** 초·중기 contact_stack → ≈410+ **PE**가 더 이름. fade≈1.28, knee≈290.
- 절대 LAM% / “중기 음극 확정” 서사 금지.
