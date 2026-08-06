"""Method A — config-driven degradation-mode pattern scoring."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .schema import (
    DIAGNOSIS_MODEL_VERSION,
    DIAGNOSIS_VERSION_FULLCELL,
    DiagnosisResult,
    PATTERN_MODES,
)

_CONFIG_DIR = Path(__file__).resolve().parent / "config"
_DEFAULT_CONFIG = _CONFIG_DIR / "mode_weights_fullcell_v1.json"


def load_mode_weights(path: str | Path | None = None) -> dict[str, Any]:
    """Load mode weight config (JSON). Optional YAML if PyYAML is installed.

    Default: ASSB Si-rich weights when present, else fullcell_v1.
    """
    if path is None:
        assb = _CONFIG_DIR / "mode_weights_assb_si_v1.json"
        cfg_path = assb if assb.exists() else _DEFAULT_CONFIG
    else:
        cfg_path = Path(path)
    text = cfg_path.read_text(encoding="utf-8")
    if cfg_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "PyYAML required for .yaml config; use mode_weights_fullcell_v1.json"
            ) from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict) or "modes" not in data:
        raise ValueError(f"Invalid diagnosis weight config: {cfg_path}")
    # Invalidate cached default when configs are reloaded from disk
    _cached_default_config.cache_clear()
    return data


@lru_cache(maxsize=4)
def _cached_default_config() -> dict[str, Any]:
    assb = _CONFIG_DIR / "mode_weights_assb_si_v1.json"
    return load_mode_weights(assb if assb.exists() else _DEFAULT_CONFIG)


def _finite(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


def _signed_evidence(
    value: float,
    *,
    direction: str,
    scale: float,
    baseline: float | None = None,
) -> float:
    """Map raw feature → signed evidence in [-1, 1] (positive = supports mode)."""
    s = abs(float(scale)) if scale and abs(scale) > 1e-15 else 1.0
    d = (direction or "increase").lower()

    if d == "increase":
        if baseline is not None and math.isfinite(baseline):
            raw = (value - baseline) / s
        else:
            raw = value / s
    elif d == "decrease":
        if baseline is not None and math.isfinite(baseline):
            raw = (baseline - value) / s
        else:
            raw = -value / s
    elif d == "either":
        if baseline is not None and math.isfinite(baseline):
            raw = abs(value - baseline) / s
        else:
            raw = abs(value) / s
    elif d == "decrease_from_100":
        raw = (100.0 - value) / s
    elif d == "decrease_vs_baseline":
        if baseline is None or not math.isfinite(baseline) or abs(baseline) < 1e-15:
            return 0.0
        raw = (baseline - value) / (abs(baseline) * 0.1 + s * 0.1)
    elif d == "increase_vs_baseline":
        if baseline is None or not math.isfinite(baseline):
            return 0.0
        raw = (value - baseline) / s
    else:
        raw = value / s

    # tanh soft clip
    return float(math.tanh(raw))


def _evidence_for_term(
    row: Mapping[str, Any],
    term: Mapping[str, Any],
    baseline_row: Mapping[str, Any] | None,
) -> tuple[str, float | None]:
    feat = str(term["feature"])
    val = _finite(row.get(feat))
    if val is None:
        return feat, None
    # Guard invalid coulombic efficiency extracts (often >100% on mismatched Ah)
    if feat in ("CE", "CE_rev", "CE_local_20") and (val > 102.0 or val < 85.0):
        return feat, None
    direction = str(term.get("direction", "increase"))
    # Non-positive curve proxies are not supportive "increase" evidence
    if feat.endswith("_curve_proxy") and direction in ("increase", "increase_vs_baseline") and val <= 0:
        return feat, None

    baseline = None
    use_base = bool(term.get("use_baseline")) or direction in (
        "decrease_vs_baseline", "increase_vs_baseline",
    ) or term.get("baseline_ref") is not None
    if use_base:
        if baseline_row is None:
            # Required baseline missing → skip (do not absolute-score FF'd R etc.)
            return feat, None
        ref = term.get("baseline_ref") or feat
        baseline = _finite(baseline_row.get(ref))
        if baseline is None:
            return feat, None
    signed = _signed_evidence(
        val,
        direction=direction,
        scale=float(term.get("scale", 1.0)),
        baseline=baseline,
    )
    return feat, signed


def score_mode_for_row(
    row: Mapping[str, Any],
    mode: str,
    config: dict[str, Any],
    *,
    baseline_row: Mapping[str, Any] | None = None,
    other_mode_scores: Mapping[str, float] | None = None,
) -> DiagnosisResult:
    """Compute Level-1 pattern DiagnosisResult for one mode on one cycle row."""
    modes = config.get("modes") or {}
    mode_cfg = modes.get(mode) or {}
    evidence_terms = list(mode_cfg.get("evidence") or [])
    support_thr = float(config.get("support_threshold", 0.25))
    conflict_thr = float(config.get("conflict_threshold", 0.25))
    min_ev = int(config.get("min_evidence_for_valid", 2))
    collision_thr = float(config.get("mode_collision_score", 0.65))

    weights: list[float] = []
    signed_vals: list[float] = []
    names: list[str] = []
    for term in evidence_terms:
        w = float(term.get("weight", 1.0))
        name, signed = _evidence_for_term(row, term, baseline_row)
        if signed is None:
            continue
        names.append(name)
        signed_vals.append(signed)
        weights.append(max(0.0, w))

    n = len(signed_vals)
    data_quality = float(n / max(1, len(evidence_terms))) if evidence_terms else 0.0

    if n == 0 or sum(weights) <= 0:
        return DiagnosisResult(
            degradation_mode=mode,
            level=1,
            estimate=None,
            unit="pattern_score_0_1",
            confidence=0.0,
            evidence_count=0,
            supporting_features=[],
            conflicting_features=[],
            data_quality_score=data_quality,
            diagnosis_valid=False,
            diagnosis_version=str(config.get("diagnosis_version", DIAGNOSIS_VERSION_FULLCELL)),
            diagnosis_method=str(config.get("diagnosis_method", "rule_pattern")),
            diagnosis_model_version=str(
                config.get("diagnosis_model_version", DIAGNOSIS_MODEL_VERSION)
            ),
        )

    w_arr = np.asarray(weights, dtype=float)
    s_arr = np.asarray(signed_vals, dtype=float)
    # Pattern score: weighted mean of positive-part evidence, clipped to [0,1]
    pos = np.clip(s_arr, 0.0, None)
    score = float(np.average(pos, weights=w_arr))
    score = float(np.clip(score, 0.0, 1.0))

    supporting = [n for n, s in zip(names, signed_vals) if s >= support_thr]
    conflicting = [n for n, s in zip(names, signed_vals) if s <= -conflict_thr]

    agree = float(np.average((s_arr > 0).astype(float), weights=w_arr))
    conf = 0.45 * data_quality + 0.40 * agree + 0.15 * min(1.0, n / 5.0)

    # Mode collision: another mode also high → lower confidence
    if other_mode_scores:
        rivals = [
            v for k, v in other_mode_scores.items()
            if k != mode and v is not None and v >= collision_thr and score >= collision_thr
        ]
        if rivals:
            conf *= 0.7

    conf = float(np.clip(conf, 0.0, 1.0))
    valid = n >= min_ev and data_quality >= 0.3 and conf >= 0.25

    return DiagnosisResult(
        degradation_mode=mode,
        level=1,
        estimate=score,
        unit="pattern_score_0_1",
        confidence=conf,
        evidence_count=n,
        supporting_features=supporting,
        conflicting_features=conflicting,
        data_quality_score=data_quality,
        diagnosis_valid=valid,
        diagnosis_version=str(config.get("diagnosis_version", DIAGNOSIS_VERSION_FULLCELL)),
        diagnosis_method=str(config.get("diagnosis_method", "rule_pattern")),
        diagnosis_model_version=str(
            config.get("diagnosis_model_version", DIAGNOSIS_MODEL_VERSION)
        ),
    )


def score_all_modes_for_row(
    row: Mapping[str, Any],
    config: dict[str, Any] | None = None,
    *,
    baseline_row: Mapping[str, Any] | None = None,
    modes: tuple[str, ...] | None = None,
) -> dict[str, DiagnosisResult]:
    """Two-pass scoring so mode-collision can use peer scores."""
    cfg = config or _cached_default_config()
    if modes is None:
        cfg_modes = tuple(cfg.get("modes", {}).keys())
        mode_list = cfg_modes or PATTERN_MODES
    else:
        mode_list = modes
    prelim: dict[str, float] = {}
    # first pass without collision
    first: dict[str, DiagnosisResult] = {}
    for mode in mode_list:
        r = score_mode_for_row(row, mode, cfg, baseline_row=baseline_row)
        first[mode] = r
        prelim[mode] = float(r.estimate or 0.0)
    # second pass with collision awareness
    out: dict[str, DiagnosisResult] = {}
    for mode in mode_list:
        out[mode] = score_mode_for_row(
            row, mode, cfg,
            baseline_row=baseline_row,
            other_mode_scores=prelim,
        )
    return out
