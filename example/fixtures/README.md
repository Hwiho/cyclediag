# CycleDiag fixtures (raw only)

Source: `C:\260304_900wet_vs_900dry_vs_1300dry` — PNE cycler `*_raw.csv` only.

| Series | Cells | Notes |
|--------|-------|-------|
| `set1_SJ900` | M01Ch005, Ch011, Ch013 | SJ900 set1 |
| `set4_SJ900` | M01Ch022, Ch024, Ch025 | SJ900 set4 (often used in docs) |
| `SJ1300_dry` | M01Ch010, Ch011, Ch012 | SJ1300 dry RPT |

Paths are listed in [`manifest.json`](manifest.json).

```bash
# smoke (repo root, PYTHONPATH=.)
python -m cyclediag extract --input example/fixtures/raw/set4_SJ900/M01Ch025_raw.csv --out /tmp/f.csv
```

Large CSVs are stored with **Git LFS** in the published `cyclediag` repo.
