# Spec: Evaluation

**Status:** Draft

---

## Splits

| Method | When |
|--------|------|
| **GroupKFold (k=5)** by `cell_id` | Default — prevents leakage across cycles |
| Temporal split | 수명 예측: early cycles train, late test |
| Lot hold-out | 새 lot 일반화 검증 |

Never random row split across same cell.

---

## Metrics

### Unsupervised / anomaly

| Metric | Notes |
|--------|-------|
| AUROC | if binary labels available |
| PR-AUC | imbalanced anomalies |
| Precision@k | top k flagged vs known bad |

### Supervised multi-class

| Metric | Notes |
|--------|-------|
| Macro-F1 | class imbalance |
| Confusion matrix | per-class |
| Calibration | reliability diagram (optional) |

### Regression (SOH)

| Metric | Notes |
|--------|-------|
| MAE, RMSE | on SOH or Q_max |
| R² | |

---

## Baselines (must beat)

1. **Rule-only:** `|delta_Q_pct| > 5%` → anomaly
2. **Single feature:** F1.1 alone threshold
3. **Reference L2:** F1.18 only

ML model should beat (1) or (3) on val AUROC before deploy.

---

## Reporting

`metrics.json`:

```json
{
  "mode": "unsupervised",
  "feature_set": "vp_v1_basic",
  "cv": {"auroc_mean": 0.92, "auroc_std": 0.04},
  "baselines": {"rule_delta_Q": 0.85, "curve_L2": 0.88},
  "n_cells_train": 40,
  "n_cells_val": 10
}
```

---

## Data size guidelines

| Goal | Min rough scale |
|------|-----------------|
| Reference distance QC | 10–20 normal cells for golden |
| Isolation Forest | 50+ legs (unlabeled OK) |
| XGBoost 5-class | 30+ per class |
| 1D-CNN | 500+ labeled curves |
