# DOE3 양극 비교: S83S vs Bimodal

- 음극: Si-on-Gr (동일) · 양극만 다름
- cells A: M02Ch103, M02Ch104, M02Ch105
- cells B: M02Ch109, M02Ch110, M02Ch111

## 열화기작 대비 요약 (Bimodal − S83S)

동일 음극(Si-on-Gr) · 양극만 다른 DOE에서, 초반 fingerprint와 수명 중 점수 증가(Δ=late−early)를 비교한다.

### 초반부터 다른 파라미터
- `early_LAM_curve_proxy`: S83S=-4.07 → Bimodal=-2.604 (Δ=+1.466, +21.70σ)
- `early_mech_vs_chem_ratio`: S83S=1.894 → Bimodal=1.488 (Δ=-0.4062, -18.79σ)
- `early_hyst_area_low`: S83S=0.07303 → Bimodal=0.08407 (Δ=+0.01104, +17.87σ)
- `early_R_ohmic_soc50`: S83S=1.368 → Bimodal=1.09 (Δ=-0.2783, -16.37σ)
- `early_VE`: S83S=0.8904 → Bimodal=0.9026 (Δ=+0.01216, +9.91σ)
- `early_LLI_curve_proxy`: S83S=-0.4469 → Bimodal=0.2517 (Δ=+0.6986, +9.02σ)

### 열화와 함께 갈라지는 기작 (Δ late−early)
- `mech_vs_chem_ratio` 증가량: S83S=+0.6168 vs Bimodal=+1.541 (차이 +0.9242, +20.85σ)
- `SoHQ` 증가량: S83S=-8.214 vs Bimodal=-9.957 (차이 -1.743, -11.59σ)
- `LAM_PE_pattern_score` 증가량: S83S=+0.3009 vs Bimodal=+0.3784 (차이 +0.07745, +4.35σ)
- `NE_side_score` 증가량: S83S=+0.09642 vs Bimodal=+0.1304 (차이 +0.03398, +3.82σ)
- `contact_loss_score` 증가량: S83S=+0.09377 vs Bimodal=+0.2217 (차이 +0.1279, +3.33σ)
- `contact_stack_score` 증가량: S83S=+0.09377 vs Bimodal=+0.2217 (차이 +0.1279, +3.33σ)

> 해석 주의: PE_side / LAM_PE_pattern은 NCM 이차입자 **activity/isolation pattern**이며 절대 LAM%가 아니다. contact_stack은 전극 미분해 스택/접촉 가설이다.

## 셀별 요약

```
    arm  cell_id  SoHQ_end  fade_exponent_b  knee_cycle_bw  early_SoHQ  early_LAM_PE_pattern_score  early_contact_loss_score  late_LAM_PE_pattern_score  late_contact_loss_score  delta_LAM_PE_pattern_score  delta_contact_loss_score  delta_PE_side_score  delta_contact_stack_score
   S83S M02Ch103 87.360724         0.637574           30.0   95.919220                    0.568152                  0.801288                   0.834751                 0.934380                    0.266599                  0.133092             0.218535                   0.133092
   S83S M02Ch104 87.687885         0.606607           30.0   95.949925                    0.604596                  0.869674                   0.930133                 0.942245                    0.325537                  0.072570             0.293564                   0.072570
   S83S M02Ch105 87.204608         0.623844           30.0   95.773221                    0.607127                  0.850732                   0.917793                 0.926366                    0.310666                  0.075634             0.248135                   0.075634
Bimodal M02Ch109 86.164659         0.681942           40.0   96.659388                    0.568979                  0.827481                   0.949893                 0.991490                    0.380914                  0.164009             0.307936                   0.164009
Bimodal M02Ch110 86.556955         0.602496           40.0   96.484505                    0.581995                  0.708388                   0.961389                 0.986459                    0.379394                  0.278072             0.297897                   0.278072
Bimodal M02Ch111 86.808166         0.673168           30.0   96.735296                    0.564592                  0.767657                   0.939438                 0.990529                    0.374846                  0.222872             0.305758                   0.222872
```