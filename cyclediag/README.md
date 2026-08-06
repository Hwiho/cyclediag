# CycleDiag

Standalone **cycle / voltage-profile diagnosis** package.

GUI 없음 · `pne_studio2` 불필요 · 단독 구동.

**Version:** 1.0.0

## Install

```bash
pip install -r cyclediag/requirements.txt
# repo root
set PYTHONPATH=.
```

또는:

```bash
pip install -e cyclediag
```

## Library

```python
from cyclediag import diagnose_csv, extract_features
from cyclediag.models.predict import predict_features

result = diagnose_csv("cell_raw.csv")
print(result["scored"][["cycle", "SoHQ", "anomaly_score", "flag"]].head())
```

## CLI

```bash
python -m cyclediag --help
python run_cyclediag.py extract --input raw.csv --out features.csv
python run_cyclediag.py diagnose --input raw.csv --out-dir out/diag
python run_cyclediag.py predict --features features.csv --out scores.csv
python run_cyclediag.py report --input-dir path/to/folder
python run_cyclediag.py peaks export --input raw.csv --out-dir example/docs/features --cell-id Cell01
```

## Layout

```
cyclediag/          # lean package (~code only)
  api.py            # diagnose_csv / diagnose_folder
  features/         # LGES indicators, peaks, export
  models/           # z-score anomaly + peak ML
  analysis/         # indicator / dQ/dV screen, batch report
  diagnosis/        # LLI/LAM pattern scoring
  io/               # cycler / StepEnd / rest voltage
  tools/            # scripts
  archive/          # legacy CLI / experiments
  tests/
  planning/ specs/

example/            # sample data & artifacts (repo root, not packaged)
  docs/             # peak_review, features, models
  output/           # diagnosis / indicator samples
```

`pne_studio2` Diagnosis 탭 · rest_voltage는 이 패키지를 사용합니다.
