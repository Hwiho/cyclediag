# CycleDiag

Standalone **cycle / voltage-profile diagnosis** package.

GUI 없음 · `pne_studio2` 불필요 · 단독 구동.

**Version:** 1.0.0

## Example fixtures (Git LFS)

`example/fixtures/raw/` — `260304_900wet_vs_900dry_vs_1300dry`에서 가져온 `*_raw.csv` 9개만 포함.

| Series | Cells |
|--------|-------|
| set1_SJ900 | M01Ch005, Ch011, Ch013 |
| set4_SJ900 | M01Ch022, Ch024, Ch025 |
| SJ1300_dry | M01Ch010, Ch011, Ch012 |

목록: [`example/fixtures/manifest.json`](example/fixtures/manifest.json)

```bash
git lfs install
git lfs pull
python run_cyclediag.py extract --input example/fixtures/raw/set4_SJ900/M01Ch025_raw.csv --out /tmp/f.csv
```

## Cursor Cloud Agents

이 레포를 Cloud Agents에 연결하면 `.cursor/environment.json`의 install이 의존성을 설치합니다.

1. [Cloud Agents dashboard](https://cursor.com/dashboard/cloud-agents#environments) → GitHub에서 이 레포 선택
2. Environment 셋업(에이전트 자동 설치 권장)
3. 태스크 예: `example/fixtures/raw/set4_SJ900/M01Ch025_raw.csv`로 diagnose 돌리고 결과 요약해 PR 열어줘

## Install

```bash
pip install -r requirements.txt
pip install -e "./cyclediag[dev]"
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
cyclediag/          # package (diagnosis params under diagnosis/config/)
example/fixtures/   # raw.csv fixtures (Git LFS)
.cursor/            # Cloud Agent environment
run_cyclediag.py
```

`pne_studio2` Diagnosis 탭 · rest_voltage는 이 패키지를 사용합니다.
