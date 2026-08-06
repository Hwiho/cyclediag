# Spec — Full-cell degradation-mode diagnosis

**Policy source:** [../planning/LLI_LAM_DIAGNOSIS.md](../planning/LLI_LAM_DIAGNOSIS.md)  
**Target feature set:** `vp_lges_cycle_v2`  
**Diagnosis versions:** `fullcell_v1` (Phase 1–2) · `hc_calibrated_v1` (Phase 3+)

---

## 1. Scope

| In scope (now) | Out of scope (now) |
|----------------|--------------------|
| Level 1 pattern scores | Treating scores as absolute loss % without unit/definition |
| Level 2 estimates only when definition + validation exist | Disabling LLI/LAM because half-cell is missing |
| Uncertainty payload per mode | Hard-coded unexplained weights in source |
| Calibration **schema** + empty adapter for half-cell | Phase 3 half-cell measurement pipeline itself |

---

## 2. Module layout (target)

```
cyclediag/
  diagnosis/
    __init__.py
    schema.py              # DiagnosisResult, CalibrationRecord
    pattern_scoring.py     # Method A — config-driven weights
    curve_fitting.py       # Method B — optional
    data_driven.py         # Method C — optional
    config/
      mode_weights_fullcell_v1.yaml
    halfcell/
      calibration_schema.py
      calibrate.py         # Phase 3 — maps fullcell est → hc_calibrated
```

Cycle feature table (`vp_lges_cycle_v*`) → diagnosis engine → wide columns **and/or** JSON sidecar.

---

## 3. `DiagnosisResult` schema

```python
@dataclass
class DiagnosisResult:
    degradation_mode: str          # LLI | LAM_PE | LAM_NE | impedance | ...
    level: int                     # 1=pattern, 2=est, 3=hc_calibrated
    estimate: float | None
    unit: str                      # "pattern_score_0_1" | "relative_fraction" | ...
    confidence: float              # 0..1
    evidence_count: int
    supporting_features: list[str]
    conflicting_features: list[str]
    data_quality_score: float
    diagnosis_valid: bool
    diagnosis_version: str         # "fullcell_v1" | "hc_calibrated_v1"
    diagnosis_method: str          # "rule_pattern" | "curve_fit" | "ml" | ...
    diagnosis_model_version: str
```

Wide-table aliases (cycle row):

- scores: `LLI_pattern_score`, `LAM_PE_pattern_score`, …
- est: `LLI_est`, …
- conf: `LLI_confidence`, …
- meta: `diagnosis_quality_score`, `diagnosis_valid`, `diagnosis_method`, `diagnosis_model_version`

---

## 4. Method A — config-driven pattern score

1. Map existing features → signed evidence terms (direction known a priori).  
2. Load weights from YAML/artifact (`mode_weights_fullcell_v1.yaml`).  
3. Aggregate to score in `[0, 1]` (or standardized z→sigmoid).  
4. Split features into supporting vs conflicting by sign agreement.  
5. Confidence from: coverage, agreement ratio, data_quality, mode-separability.

Do **not** embed magic weights in Python constants without a config key.

---

## 5. Half-cell calibration schema (define now, implement Phase 3)

Purpose: compare full-cell estimates with half-cell / harvested-electrode truth **without replacing** full-cell outputs.

### 5.1 Record

```json
{
  "schema_version": "hc_calibration_v0",
  "cell_id": "M01Ch022",
  "chemistry": "SJ900",
  "aged_cycle_ref": 502,
  "fullcell": {
    "diagnosis_version": "fullcell_v1",
    "LLI_est": 0.12,
    "LAM_PE_est": 0.05,
    "LAM_NE_est": 0.08,
    "LLI_pattern_score": 0.81,
    "supporting_features": ["peak_spacing_shift", "dchg_V_cutoff_margin"]
  },
  "halfcell": {
    "source": "harvested",
    "PE_reversible_capacity_frac": 0.94,
    "NE_reversible_capacity_frac": 0.90,
    "LLI_proxy": 0.11,
    "notes": "optional post-mortem"
  },
  "calibration": {
    "status": "pending",
    "LLI_scale": null,
    "LAM_PE_scale": null,
    "LAM_NE_scale": null,
    "residual": null
  }
}
```

### 5.2 Interface contract

```text
calibrate(fullcell_result, halfcell_truth, chemistry) -> DiagnosisResult
  - diagnosis_version = "hc_calibrated_v1"
  - preserves original fullcell fields in sidecar / parallel columns
  - never overwrites fullcell_v1 columns in place
```

Parallel columns after calibration:

- `LLI_est` (fullcell) remains  
- `LLI_est_hc_calibrated` added  

---

## 6. Validity gates

Set `diagnosis_valid=false` or lower confidence when:

| Gate | Example |
|------|---------|
| coverage | too few cycles / sparse Q-V |
| peak_match | low assignment confidence |
| protocol_drift | cutoff, C-rate, rest duration changed |
| baseline_quality | cycle-1 profile noisy / incomplete |
| mode_collision | LLI vs LAM scores both high with shared features |

---

## 7. Acceptance tests (Phase 1)

- With only full-cell CSV, diagnosis module runs and emits Level 1 scores.  
- Output includes `confidence` and non-empty `supporting_features` when valid.  
- No code path that skips LLI/LAM solely because half-cell files are absent.  
- `diagnosis_version` is `fullcell_v1`.  
- Calibration schema validates against sample JSON; `calibrate()` may be stub returning `NotImplemented` until Phase 3.
