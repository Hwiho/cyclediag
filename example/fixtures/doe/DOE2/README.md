# DOE2 — SJ900 dry vs SJ1300 dry

**Short ID:** `DOE2`  
**Source:** `C:\260304_900wet_vs_900dry_vs_1300dry`  
**Question:** Anode / process dry variant — SJ900 dry arm vs SJ1300 dry.  
**Design:** **양극(cathode) 동일 · 음극(anode) 상이** → early parameter + aging mechanism contrast.

| Arm | Location | Cells |
|-----|----------|-------|
| SJ900 dry | **DOE1** [`../DOE1/`](../DOE1/) — provisional: `set4_SJ900` (confirm) | Ch022, Ch024, Ch025 |
| `SJ1300_dry/` | this folder (**DOE2**) | M01Ch010, Ch011, Ch012 |

## Compare CLI

```bash
# from repo root (fixtures under example/fixtures)
python -m cyclediag compare-doe --doe DOE2 --out example/output/DOE2_compare

# or
python -m cyclediag.tools.run_doe2_compare --out example/output/DOE2_compare
```

### Outputs (`example/output/DOE2_compare/`)

| File | Content |
|------|---------|
| `early_parameters_by_arm.csv` | 초반(default ≤30 cy) arm 평균 + Δ(SJ1300−SJ900) |
| `early_fade_rates.csv` | 초반 SoHQ slope (per cell / arm) |
| `arm_trajectories.csv` | cycle별 arm mean + delta |
| `late_arm_divergence.csv` | 말기 arm 간 벌어지는 지표 순위 |
| `diagnosis_by_cycle.csv` | ASSB pattern scores (full-cell) |
| `mode_scores_by_arm_phase.csv` | early/mid/late 모드 점수 |
| `narrative.txt` | 한 줄 요약 (음극 차이 관점) |
| `plots/` | SoHQ, CE, R, hyst, peak V, late mode bars |

SJ900 files are **not duplicated** here. Extract uses DOE1 `set4_SJ900` as provisional dry arm.
