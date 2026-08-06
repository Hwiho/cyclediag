"""ML-assisted dQ/dV peak assign — learn from golden cycles, Hungarian match candidates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .dqdv_peaks import (
    DqdvPeakConfig,
    charge_discharge_bands,
    find_dqdv_peaks_banded,
    find_dqdv_peaks_banded_prepared,
    find_dqdv_peaks_prepared,
    prepare_dqdv_arrays,
    _smooth,
)
from .dqdv_segment import prepare_leg_segment_for_dqdv
from .segment_utils import leg_segment


@dataclass
class PeakAssignConfig:
    """Peak identity assignment settings."""

    assign_mode: str = "hybrid"  # band | hungarian | hybrid | evolution | deconv
    v_window_sigma: float = 2.0
    v_window_min_v: float = 0.03
    v_window_max_v: float = 0.06
    max_match_cost: float = 0.12
    h_cost_weight: float = 0.015
    rf_cost_weight: float = 0.5
    reject_cost: float = 1e6
    rf_min_proba: float = 0.25
    n_estimators: int = 120
    random_state: int = 42


@dataclass
class PeakAssignBundle:
    """Learned peak assign model + golden centroids."""

    centroids: pd.DataFrame
    rf_models: dict[str, Pipeline]
    config: PeakAssignConfig
    good_cycles: list[int] = field(default_factory=list)
    train_rows: int = 0
    peak_ids: dict[str, list[str]] = field(default_factory=dict)
    training_cells: list[str] = field(default_factory=list)
    version: str = "peak_assign_v2"

    def save(self, out_dir: str | Path) -> Path:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "centroids": self.centroids,
                "rf_models": self.rf_models,
                "config": asdict(self.config),
                "good_cycles": self.good_cycles,
                "train_rows": self.train_rows,
                "peak_ids": self.peak_ids,
                "training_cells": self.training_cells,
                "version": self.version,
            },
            out_dir / "assign_model.joblib",
        )
        criteria = {
            "version": self.version,
            "good_cycles": self.good_cycles,
            "train_rows": self.train_rows,
            "peak_ids": self.peak_ids,
            "training_cells": self.training_cells,
            "centroids": self.centroids.to_dict(orient="records"),
            "config": asdict(self.config),
        }
        (out_dir / "learned_criteria.json").write_text(
            json.dumps(criteria, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return out_dir

    @classmethod
    def load(cls, model_dir: str | Path) -> PeakAssignBundle:
        raw: dict[str, Any] = joblib.load(Path(model_dir) / "assign_model.joblib")
        cfg_dict = dict(raw.get("config", {}))
        config = PeakAssignConfig(
            **{k: v for k, v in cfg_dict.items() if k in PeakAssignConfig.__dataclass_fields__}
        )
        return cls(
            centroids=raw["centroids"],
            rf_models=dict(raw.get("rf_models", {})),
            config=config,
            good_cycles=list(raw.get("good_cycles", [])),
            train_rows=int(raw.get("train_rows", 0)),
            peak_ids=dict(raw.get("peak_ids", {})),
            training_cells=list(raw.get("training_cells", [])),
            version=str(raw.get("version", "peak_assign_v2")),
        )


@dataclass
class PeakAssignSample:
    """One cell's golden-labeled peaks for multi-cell training."""

    cell_id: str
    labels: pd.DataFrame
    good_cycles: list[int]


def _capacity_col(seg: pd.DataFrame, leg: str) -> str | None:
    col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if col in seg.columns:
        return col
    return "capacity" if "capacity" in seg.columns else None


def _peak_features(v: float, h: float) -> np.ndarray:
    h_abs = abs(h)
    return np.array([v, h, h_abs, np.log1p(h_abs)], dtype=float)


def _train_rf_for_leg(train_df: pd.DataFrame, config: PeakAssignConfig) -> Pipeline | None:
    if train_df.empty or train_df["peak_id"].nunique() < 2:
        return None
    x = np.vstack([_peak_features(r.V, r.H) for r in train_df.itertuples()])
    y = train_df["peak_id"].astype(str).to_numpy()
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        (
            "model",
            RandomForestClassifier(
                n_estimators=config.n_estimators,
                random_state=config.random_state,
                class_weight="balanced_subsample",
                min_samples_leaf=1,
            ),
        ),
    ])
    pipe.fit(x, y)
    return pipe


def _centroids_from_labels(labels: pd.DataFrame, config: PeakAssignConfig) -> pd.DataFrame:
    rows: list[dict] = []
    for (leg, peak_id), grp in labels.groupby(["leg", "peak_id"], sort=False):
        v = grp["V"].astype(float)
        h = grp["H"].astype(float)
        v_med = float(v.median())
        v_mad = float((v - v_med).abs().median()) or float(v.std(ddof=0)) or config.v_window_min_v
        half = float(np.clip(config.v_window_sigma * v_mad * 1.4826, config.v_window_min_v, config.v_window_max_v))
        h_med = float(h.median())
        h_abs_med = float(h.abs().median())
        rows.append({
            "leg": leg,
            "peak_id": peak_id,
            "V": v_med,
            "H": h_med,
            "H_abs": h_abs_med,
            "v_lo": v_med - half,
            "v_hi": v_med + half,
            "n_ref": int(len(grp)),
        })
    return pd.DataFrame(rows)


def train_peak_assign_from_long(
    long_df: pd.DataFrame,
    good_cycles: list[int],
    *,
    config: PeakAssignConfig | None = None,
) -> PeakAssignBundle:
    """Train RF + centroids from band-labeled golden rows in long trajectory table."""
    config = config or PeakAssignConfig()
    if long_df.empty or not good_cycles:
        raise ValueError("long_df and good_cycles required")

    train = long_df[long_df["cycle"].isin(good_cycles)].copy()
    if "usable_leg" in train.columns:
        train = train[train["usable_leg"]]
    if train.empty:
        train = long_df[long_df["cycle"].isin(good_cycles)].copy()
    if "peak_id" not in train.columns and "band" in train.columns:
        train = train.rename(columns={"band": "peak_id"})
    elif "peak_id" in train.columns and "band" in train.columns:
        train = train.drop(columns=["band"])
    if "peak_id" not in train.columns:
        raise ValueError("long_df must include band or peak_id")

    centroids = _centroids_from_labels(train, config)
    rf_models: dict[str, Pipeline] = {}
    peak_ids: dict[str, list[str]] = {}
    for leg, grp in centroids.groupby("leg"):
        leg_train = train[train["leg"] == leg]
        model = _train_rf_for_leg(leg_train, config)
        if model is not None:
            rf_models[leg] = model
        peak_ids[leg] = grp.sort_values("V")["peak_id"].astype(str).tolist()

    return PeakAssignBundle(
        centroids=centroids,
        rf_models=rf_models,
        config=config,
        good_cycles=sorted(int(c) for c in good_cycles),
        train_rows=len(train),
        peak_ids=peak_ids,
        training_cells=sorted(train["cell_id"].unique().tolist()) if "cell_id" in train.columns else [],
    )


def _prepare_label_frame(labels: pd.DataFrame) -> pd.DataFrame:
    train = labels.copy()
    if "peak_id" not in train.columns and "band" in train.columns:
        train = train.rename(columns={"band": "peak_id"})
    elif "peak_id" in train.columns and "band" in train.columns:
        train = train.drop(columns=["band"])
    required = {"leg", "peak_id", "V", "H"}
    if not required.issubset(train.columns):
        raise ValueError(f"labels need columns {required}")
    return train


def train_peak_assign_multi(
    samples: Iterable[PeakAssignSample],
    *,
    config: PeakAssignConfig | None = None,
) -> PeakAssignBundle:
    """Train assign rules from multiple cells (cross-sample generalization)."""
    config = config or PeakAssignConfig()
    parts: list[pd.DataFrame] = []
    all_good: set[int] = set()
    cells: list[str] = []
    for sample in samples:
        cells.append(sample.cell_id)
        all_good.update(int(c) for c in sample.good_cycles)
        frame = _prepare_label_frame(sample.labels)
        if "cycle" in frame.columns and sample.good_cycles:
            frame = frame[frame["cycle"].isin(sample.good_cycles)]
        frame = frame.copy()
        frame["cell_id"] = sample.cell_id
        parts.append(frame)
    if not parts:
        raise ValueError("no training samples")
    train = pd.concat(parts, ignore_index=True)
    centroids = _centroids_from_labels(train, config)
    rf_models: dict[str, Pipeline] = {}
    peak_ids: dict[str, list[str]] = {}
    for leg, grp in centroids.groupby("leg"):
        leg_train = train[train["leg"] == leg]
        model = _train_rf_for_leg(leg_train, config)
        if model is not None:
            rf_models[leg] = model
        peak_ids[leg] = grp.sort_values("V")["peak_id"].astype(str).tolist()
    return PeakAssignBundle(
        centroids=centroids,
        rf_models=rf_models,
        config=config,
        good_cycles=sorted(all_good),
        train_rows=len(train),
        peak_ids=peak_ids,
        training_cells=sorted(set(cells)),
    )


def train_peak_assign_from_raw(
    df: pd.DataFrame,
    good_cycles: list[int],
    *,
    dqcfg: DqdvPeakConfig | None = None,
    min_band_height_frac: float = 0.12,
    config: PeakAssignConfig | None = None,
) -> PeakAssignBundle:
    """Train from golden cycles only — band assign labels on subset, then fit ML."""
    dqcfg = dqcfg or DqdvPeakConfig(sg_window=31)
    config = config or PeakAssignConfig()
    rows: list[dict] = []
    for tc in good_cycles:
        cyc = df[df["cycle"] == tc]
        if cyc.empty:
            continue
        for leg in ("charge", "discharge"):
            seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
            seg = prepare_leg_segment_for_dqdv(seg, leg)
            col = _capacity_col(seg, leg)
            if seg.empty or col is None:
                continue
            v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
            q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
            bands = charge_discharge_bands(leg)
            for pk in find_dqdv_peaks_banded(
                v, q, bands, config=dqcfg, min_band_height_frac=min_band_height_frac,
            ):
                rows.append({
                    "cycle": int(tc),
                    "leg": leg,
                    "peak_id": pk["band"],
                    "V": pk["V"],
                    "H": pk["H"],
                })
    labels = pd.DataFrame(rows)
    if labels.empty:
        raise ValueError("no golden peak labels extracted")
    return train_peak_assign_from_long(labels, good_cycles, config=config)


def _match_cost(candidate: dict, ref: pd.Series, config: PeakAssignConfig) -> float:
    dv = abs(float(candidate["V"]) - float(ref["V"]))
    dh = abs(abs(float(candidate["H"])) - float(ref["H_abs"]))
    return dv + config.h_cost_weight * dh


def _rf_proba_map(cand: dict, model: Pipeline | None) -> dict[str, float]:
    if model is None:
        return {}
    x = _peak_features(cand["V"], cand["H"]).reshape(1, -1)
    classes = list(model.named_steps["model"].classes_)
    proba = model.predict_proba(x)[0]
    return {str(c): float(p) for c, p in zip(classes, proba)}


def build_assign_cost_matrix(
    candidates: list[dict],
    refs: pd.DataFrame,
    *,
    bundle: PeakAssignBundle | None = None,
    leg: str = "",
    config: PeakAssignConfig | None = None,
) -> np.ndarray:
    """Cost matrix [n_candidates x n_peak_ids] for Hungarian matching."""
    config = config or (bundle.config if bundle else PeakAssignConfig())
    n_c, n_r = len(candidates), len(refs)
    cost = np.full((n_c, n_r), config.reject_cost, dtype=float)
    model = bundle.rf_models.get(leg) if bundle else None
    for i, cand in enumerate(candidates):
        rf_map = _rf_proba_map(cand, model)
        for j in range(n_r):
            ref = refs.iloc[j]
            base = _match_cost(cand, ref, config)
            pid = str(ref["peak_id"])
            bonus = rf_map.get(pid, 0.0)
            cost[i, j] = base * (1.0 - config.rf_cost_weight * bonus)
    return cost


def hungarian_assign_peaks(
    candidates: list[dict],
    refs: pd.DataFrame,
    *,
    bundle: PeakAssignBundle | None = None,
    leg: str = "",
    config: PeakAssignConfig | None = None,
) -> list[dict]:
    """Optimal one-to-one assign: candidates ↔ learned peak_id (Hungarian)."""
    if not candidates or refs.empty:
        return []
    config = config or (bundle.config if bundle else PeakAssignConfig())
    cost = build_assign_cost_matrix(candidates, refs, bundle=bundle, leg=leg, config=config)
    row_ind, col_ind = linear_sum_assignment(cost)

    assigned: list[dict] = []
    used_peaks: set[str] = set()
    for i, j in zip(row_ind, col_ind):
        if cost[i, j] >= config.reject_cost / 2:
            continue
        if cost[i, j] > config.max_match_cost:
            continue
        ref = refs.iloc[j]
        peak_id = str(ref["peak_id"])
        if peak_id in used_peaks:
            continue
        cand = dict(candidates[i])
        ml_conf = float(1.0 - min(1.0, cost[i, j] / config.max_match_cost))
        cand.update({
            "band": peak_id,
            "peak_id": peak_id,
            "band_v_min": float(ref["v_lo"]),
            "band_v_max": float(ref["v_hi"]),
            "assign_method": "hungarian",
            "assign_confidence": ml_conf,
            "ml_assign_confidence": ml_conf,
            "ml_peak_id": peak_id,
            "match_cost": float(cost[i, j]),
        })
        assigned.append(cand)
        used_peaks.add(peak_id)
    assigned.sort(key=lambda p: p["V"])
    return assigned


def assign_peaks_ml(
    v: np.ndarray,
    q: np.ndarray,
    leg: str,
    bundle: PeakAssignBundle,
    *,
    dqcfg: DqdvPeakConfig | None = None,
    vx: np.ndarray | None = None,
    dqdv: np.ndarray | None = None,
    y_smooth: np.ndarray | None = None,
) -> list[dict]:
    """Detect candidates → Hungarian assign with RF-weighted costs."""
    dqcfg = dqcfg or DqdvPeakConfig(sg_window=31)
    if vx is None or dqdv is None or y_smooth is None:
        vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
        y_smooth = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)
    candidates = find_dqdv_peaks_prepared(vx, dqdv, y_smooth, config=dqcfg)
    if not candidates:
        return []
    refs = bundle.centroids[bundle.centroids["leg"] == leg]
    return hungarian_assign_peaks(candidates, refs, bundle=bundle, leg=leg)


def _fill_missing_with_hungarian(
    band_peaks: list[dict],
    leg: str,
    expected: list[str],
    bundle: PeakAssignBundle,
    *,
    dqcfg: DqdvPeakConfig,
    vx: np.ndarray,
    dqdv: np.ndarray,
    y_smooth: np.ndarray,
) -> list[dict]:
    by_id: dict[str, dict] = {}
    for pk in band_peaks:
        pid = str(pk.get("band", pk.get("peak_id", "")))
        if pid:
            by_id[pid] = dict(pk)

    missing = [pid for pid in expected if pid not in by_id]
    if not missing:
        return band_peaks

    candidates = find_dqdv_peaks_prepared(vx, dqdv, y_smooth, max_peaks=8, config=dqcfg)
    used_v = [float(p["V"]) for p in band_peaks]
    leftover = [
        c for c in candidates
        if not any(abs(float(c["V"]) - uv) < 0.012 for uv in used_v)
    ]
    refs = bundle.centroids[
        (bundle.centroids["leg"] == leg) & (bundle.centroids["peak_id"].isin(missing))
    ]
    for pk in hungarian_assign_peaks(leftover, refs, bundle=bundle, leg=leg):
        pid = str(pk["peak_id"])
        pk["assign_method"] = "hybrid_hungarian"
        by_id[pid] = pk

    merged = [by_id[pid] for pid in expected if pid in by_id]
    extras = [by_id[k] for k in sorted(by_id) if k not in expected]
    merged.extend(extras)
    return merged


def assign_peaks_for_leg(
    v: np.ndarray,
    q: np.ndarray,
    leg: str,
    *,
    dqcfg: DqdvPeakConfig | None = None,
    min_band_height_frac: float = 0.12,
    bundle: PeakAssignBundle | None = None,
    assign_mode: str = "band",
    vx: np.ndarray | None = None,
    dqdv: np.ndarray | None = None,
    y_smooth: np.ndarray | None = None,
) -> list[dict]:
    """Unified peak assign: band, hungarian, or hybrid."""
    if assign_mode in ("evolution", "deconv"):
        raise ValueError(
            f"assign_mode={assign_mode!r} is multi-cycle; use "
            "peak_assign.run_evolution_tracking() or `cyclediag peaks evolution`"
        )
    dqcfg = dqcfg or DqdvPeakConfig(sg_window=31)
    bands = charge_discharge_bands(leg)
    expected = [b[2] for b in bands]

    if vx is None or dqdv is None or y_smooth is None:
        vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
        y_smooth = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)

    if assign_mode == "band":
        peaks = find_dqdv_peaks_banded_prepared(
            vx, y_smooth, bands, min_band_height_frac=min_band_height_frac,
        )
        for pk in peaks:
            pk.setdefault("assign_method", "band")
            pk.setdefault("ml_peak_id", "")
            pk.setdefault("ml_assign_confidence", np.nan)
        return peaks

    if bundle is None:
        raise ValueError("assign_mode hungarian/hybrid requires PeakAssignBundle")

    if assign_mode == "hungarian":
        return assign_peaks_ml(
            v, q, leg, bundle, dqcfg=dqcfg, vx=vx, dqdv=dqdv, y_smooth=y_smooth,
        )

    band_peaks = find_dqdv_peaks_banded_prepared(
        vx, y_smooth, bands, min_band_height_frac=min_band_height_frac,
    )
    for pk in band_peaks:
        pk.setdefault("assign_method", "band")
        pk.setdefault("ml_peak_id", "")
        pk.setdefault("ml_assign_confidence", np.nan)

    return _fill_missing_with_hungarian(
        band_peaks, leg, expected, bundle, dqcfg=dqcfg, vx=vx, dqdv=dqdv, y_smooth=y_smooth,
    )


def run_evolution_tracking(
    raw_df: pd.DataFrame,
    step_df: pd.DataFrame | None = None,
    *,
    config: "PeakEvolutionConfig | None" = None,
):
    """Evolution-based multi-cycle tracking (``method=\"evolution\"``)."""
    from .peak_evolution import PeakEvolutionConfig, track_peaks_pipeline

    cfg = config or PeakEvolutionConfig()
    return track_peaks_pipeline(raw_df, step_df, config=cfg)
