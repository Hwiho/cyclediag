# Spec: Model Pipeline

**Status:** Draft · Phase 2

---

## Modes

| Mode | Label needed | Algorithm | Output |
|------|--------------|-----------|--------|
| `reference` | No | Mahalanobis / curve L2 | distance score |
| `unsupervised` | No (eval optional) | Isolation Forest, PCA+T² | anomaly score |
| `supervised` | Yes | XGBoost / RF | class + proba |

---

## Training flow

```
features.parquet + manifest (labels)
  → drop NaN, align feature_set
  → StandardScaler fit on train only
  → GroupKFold(cell_id) for CV
  → fit model
  → save artifacts/ + metrics.json
```

---

## Inference flow

```
new CSV(s)
  → extract features (same feature_spec.json)
  → load scaler + model
  → predict score / class
  → write report row
```

---

## Hyperparameters (defaults)

### Isolation Forest

- `contamination=0.05` (tune on val)
- `n_estimators=200`
- `random_state=42`

### XGBoost (multi-class)

- `max_depth=4`, `n_estimators=200`, `learning_rate=0.05`
- `scale_pos_weight` per class if imbalanced

---

## Interpretability

- Tree models: `feature_importances_` → top 10 in report
- Optional SHAP (dependency: `shap`) — Phase 2.3

---

## CLI (planned)

```bash
python -m cyclediag train --features out/features.parquet --manifest data/manifest.csv --mode unsupervised --out artifacts/run001
python -m cyclediag predict --model artifacts/run001 --input data/new_cell.csv --out predictions.csv
python -m cyclediag evaluate --model artifacts/run001 --features out/features.parquet --manifest data/manifest.csv
```

---

## Dependencies (proposed)

```
# requirements-cyclediag.txt (separate from pne_studio)
pandas>=2.0
numpy>=1.26
scipy>=1.11
scikit-learn>=1.4
pyarrow>=14.0          # parquet
# optional Phase 2+
xgboost>=2.0
pyod>=1.1
# optional Phase 3
# torch
```
