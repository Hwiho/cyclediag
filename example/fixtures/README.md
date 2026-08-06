# CycleDiag fixtures

## Full-cell raw (`raw/`)

Source: `C:\260304_900wet_vs_900dry_vs_1300dry` — PNE cycler `*_raw.csv` only.

| Series | Cells | Notes |
|--------|-------|-------|
| `set1_SJ900` | M01Ch005, Ch011, Ch013 | SJ900 set1 |
| `set4_SJ900` | M01Ch022, Ch024, Ch025 | SJ900 set4 (often used in docs) |
| `SJ1300_dry` | M01Ch010, Ch011, Ch012 | SJ1300 dry RPT |

Paths: [`manifest.json`](manifest.json)

## Half-cell BOL (`halfcell/`) — **available**

Source: `C:\Halfcell` — cathode + anode **pristine / early-cycle** OCP at **C/20**.  
Anode CSVs: cycles **1–3**. **No aged half-cell yet.**

See [`halfcell/README.md`](halfcell/README.md) · [`halfcell/manifest.json`](halfcell/manifest.json)

```bash
# smoke (repo root, PYTHONPATH=.)
python -m cyclediag extract --input example/fixtures/raw/set4_SJ900/M01Ch025_raw.csv --out /tmp/f.csv
```

Large CSVs/xlsx are stored with **Git LFS**.
