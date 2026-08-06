# Fixtures by DOE

비교할 때 **`DOE1` / `DOE2` / `DOE3`** 만 말하면 됩니다.

| ID | 폴더 | 비교 | Arms |
|----|------|------|------|
| **DOE1** | [`doe/DOE1/`](doe/DOE1/) | SJ900 **wet vs dry** | `set1_SJ900` · `set4_SJ900` |
| **DOE2** | [`doe/DOE2/`](doe/DOE2/) | SJ900 **dry vs SJ1300 dry** | `SJ1300_dry` (+ SJ900 dry = DOE1 `set4`, 확정 전) |
| **DOE3** | [`doe/DOE3/`](doe/DOE3/) | **양극** Bimodal vs S83S | `Bimodal` · `S83S` |
| — | [`halfcell/`](halfcell/) | BOL half-cell OCP (C/20) | anode · cathode (**aged 없음**) |

Master index: [`manifest.json`](manifest.json)

```bash
git lfs install
git lfs pull

# 예: DOE1 set4 Ch25
python -m cyclediag extract --input example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv --out /tmp/f.csv

# 예: DOE3 Bimodal
python -m cyclediag extract --input example/fixtures/doe/DOE3/Bimodal/M02Ch109_raw.csv --out /tmp/f.csv
```

Large `*_raw.csv` / halfcell files use **Git LFS**.
