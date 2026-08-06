# Fixtures by DOE

CycleDiag fixtures are grouped by **comparison DOE**, not only by cell series.

| DOE folder | Question | Arms |
|------------|----------|------|
| [`doe/900wet_vs_900dry/`](doe/900wet_vs_900dry/) | SJ900 wet vs dry process | `set1_SJ900` · `set4_SJ900` |
| [`doe/900dry_vs_1300dry/`](doe/900dry_vs_1300dry/) | SJ900 dry vs SJ1300 dry | `SJ1300_dry` (+ SJ900 dry arm = see wet/dry DOE) |
| [`doe/set3_bimodal_vs_S83S/`](doe/set3_bimodal_vs_S83S/) | **Cathode** Bimodal vs S83S | `Bimodal` · `S83S` |
| [`halfcell/`](halfcell/) | BOL half-cell OCP (C/20) | anode · cathode |

Master index: [`manifest.json`](manifest.json)

```bash
git lfs install
git lfs pull
python -m cyclediag extract --input example/fixtures/doe/900wet_vs_900dry/set4_SJ900/M01Ch025_raw.csv --out /tmp/f.csv
```

Large `*_raw.csv` / halfcell files use **Git LFS**.
