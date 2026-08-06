# Spec: Feature Extraction Pipeline

**Status:** Draft · Phase 1

---

## Pipeline

```
CSV file
  → load (ColumnMap)
  → per cycle
      → split charge / discharge (StepType)
      → optional: trim CV (current threshold)
      → sort by Data_Point or time
  → per leg
      → extract Tier 1 scalars
      → optional: dQ/dV → Tier 2 peaks
      → optional: compare to golden → F1.16–F1.19
  → row in feature table
```

---

## CC/CV detection

1. `|I| < I_cv_frac × I_cc_mode` 가 연속 K 샘플 이상 → CV 시작
2. Defaults (config):
   - `I_cv_frac = 0.05`
   - `min_cc_points = 20`
3. Charge: CC from start to CV start; CV to end
4. Discharge: often CC-only — CV rare; same logic

**Feature scope flag:** `cc_only=True` → Tier 1·2는 CC 구간만.

---

## dQ/dV (Tier 2)

1. CC segment, monotonic Q
2. Interpolate to 500 points on Q
3. `dQdV = np.gradient(Q, V)` or `np.gradient(V, Q)` — **sign convention 문서화 필수**
   - cyclediag convention: **x=V, y=dQ/dV** (pne_studio plot과 동일)
4. Savitzky-Golay: window=21, poly=3 (odd window)
5. Peak find: `scipy.signal.find_peaks`, prominence = 0.02 × max(dQ/dV)

---

## DTW distance (F1.18)

- Input: `V_norm(Q*)` length 256, Q normalized to [0,1]
- Library: `fastdtw` optional, or `scipy.spatial.distance` on resampled grid (MVP: L2 on fixed grid, not full DTW)
- MVP: **Euclidean on resampled V** — rename to `curve_L2` until true DTW added

---

## API (planned)

```python
from cyclediag.io.cycler_csv import load_cycler_csv
from cyclediag.features.extract import extract_cycle_features, FeatureConfig

df = load_cycler_csv(path, column_map="pne_default")
rows = extract_cycle_features(df, cycles=[1, 2, 3], config=FeatureConfig(cc_only=True))
```

---

## Config file (`feature_spec.json`)

```json
{
  "feature_set": "vp_v1_basic",
  "cc_only": true,
  "dqdv": {"enabled": true, "n_interp": 500, "sg_window": 21, "sg_poly": 3},
  "resample_n": 256,
  "features": ["F1.1", "F1.4", "..."]
}
```

---

## Tests

- Synthetic VP: linear ramp + plateau → known Q_max, V_avg
- Golden JSON fixture → delta features match hand calculation
- Empty cycle / missing StepType → skip with warning
