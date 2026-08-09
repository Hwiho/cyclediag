# CycleDiag

Standalone **cycle / voltage-profile diagnosis** package.

GUI 없음 · `pne_studio2` 불필요 · 단독 구동.

**Version:** 1.0.0

## Example fixtures (Git LFS) — **DOE1 / DOE2 / DOE3**

비교할 때 **`DOE1`**, **`DOE2`**, **`DOE3`** 만 말하면 됩니다.  
상세: [`example/fixtures/README.md`](example/fixtures/README.md) · [`manifest.json`](example/fixtures/manifest.json)

| ID | 비교 | Arms |
|----|------|------|
| **DOE1** | SJ900 wet vs dry | set1 · set4 |
| **DOE2** | SJ900 dry vs SJ1300 dry | SJ1300_dry (+ DOE1 set4 ref) |
| **DOE3** | **양극** Bimodal vs S83S | Ch109–111 · Ch103–105 |
| halfcell | BOL OCP C/20 | anode · cathode (**aged 없음**) |

```bash
git lfs install
git lfs pull
python run_cyclediag.py extract --input example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv --out /tmp/f.csv
```
## Cursor Cloud Agents

이 레포를 Cloud Agents에 연결하면 `.cursor/environment.json`의 install이 의존성을 설치합니다.

1. [Cloud Agents dashboard](https://cursor.com/dashboard/cloud-agents#environments) → GitHub에서 이 레포 선택
2. Environment 셋업(에이전트 자동 설치 권장)
3. 태스크 예: `DOE1`의 `example/fixtures/doe/DOE1/set4_SJ900/M01Ch025_raw.csv`로 diagnose 돌리고 결과 요약해 PR 열어줘

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
python run_cyclediag.py compare-doe --doe DOE2 --out example/output/DOE2_compare
python run_cyclediag.py peaks export --input raw.csv --out-dir example/docs/features --cell-id Cell01
```

## SoHQ BP + voltage-profile presentation (tagged)

Tagged-routine SoHQ regimes (BP1/BP2, 3 zones) and every-N-cycle V–Q / dQ/dV around each BP:

```bash
# all default cells (set4 SJ900 + SJ1300 dry)
python -m cyclediag.tools.run_sohq_bp_presentation --out example/output/sohq_bp_presentation

# smoke (one cell, coarser stride)
python -m cyclediag.tools.run_sohq_bp_presentation --cells M01Ch022 --step 40 --out /tmp/bp_pres
```

Outputs per cell: `*_sohq_dsohq_regimes.png`, `*_BP1_BP2_VQ_dQdV.png`, regime slope CSV.

**Cloud / CI:** GitHub Actions workflow `cyclediag-ci` runs pytest + this presentation (artifact upload).  
Cursor Cloud Agents: clone this repo → install via `.cursor/environment.json` → run the same command.

## Layout

```
cyclediag/          # package (diagnosis params under diagnosis/config/)
example/fixtures/   # DOE raw.csv + halfcell/ BOL OCP (Git LFS)
.cursor/            # Cloud Agent environment
run_cyclediag.py
```

`pne_studio2` Diagnosis 탭 · rest_voltage는 이 패키지를 사용합니다.
