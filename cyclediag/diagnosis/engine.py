"""Apply degradation-mode diagnosis to a cycle feature table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .pattern_scoring import load_mode_weights, score_all_modes_for_row
from .schema import (
    DIAGNOSIS_MODEL_VERSION,
    DIAGNOSIS_VERSION_FULLCELL,
    PATTERN_MODES,
    confidence_column_name,
    score_column_name,
)

META_COLS = (
    "diagnosis_quality_score",
    "diagnosis_valid",
    "diagnosis_method",
    "diagnosis_model_version",
    "diagnosis_version",
)


def diagnosis_wide_columns(modes: tuple[str, ...] = PATTERN_MODES) -> list[str]:
    cols: list[str] = []
    for mode in modes:
        cols.append(score_column_name(mode))
        cols.append(confidence_column_name(mode))
        cols.append(f"{mode}_supporting_features")
        cols.append(f"{mode}_conflicting_features")
        cols.append(f"{mode}_evidence_count")
    cols.extend(META_COLS)
    # Level-2 placeholders (null until validated models exist)
    cols.extend(["LLI_est", "LAM_PE_est", "LAM_NE_est", "electrode_slippage_est"])
    # Level-3 placeholders
    cols.extend([
        "LLI_est_hc_calibrated",
        "LAM_PE_est_hc_calibrated",
        "LAM_NE_est_hc_calibrated",
    ])
    return cols


def _baseline_row(grp: pd.DataFrame, baseline_cycle: int | None) -> dict[str, Any]:
    if grp.empty:
        return {}
    if baseline_cycle is not None and "cycle" in grp.columns:
        hit = grp[grp["cycle"] == baseline_cycle]
        if not hit.empty:
            return hit.iloc[0].to_dict()
    return grp.sort_values("cycle").iloc[0].to_dict()


def diagnose_feature_table(
    table: pd.DataFrame,
    *,
    config_path: str | Path | None = None,
    baseline_cycle: int | None = 1,
    write_json_sidecar: Path | str | None = None,
) -> pd.DataFrame:
    """Append Level-1 pattern diagnosis columns to a cycle feature DataFrame.

    Does **not** require half-cell data. Level-2/3 estimate columns are left null.
    """
    if table is None or table.empty:
        out = table.copy() if table is not None else pd.DataFrame()
        cfg0 = load_mode_weights(config_path) if config_path else load_mode_weights()
        modes0 = tuple(cfg0.get("modes", {}).keys()) or PATTERN_MODES
        for c in diagnosis_wide_columns(modes0):
            if c not in out.columns:
                out[c] = None
        return out

    cfg = load_mode_weights(config_path) if config_path else load_mode_weights()
    mode_list = tuple(cfg.get("modes", {}).keys()) or PATTERN_MODES
    out = table.copy()
    n = len(out)
    for c in diagnosis_wide_columns(mode_list):
        if c.endswith("_features") or c in (
            "diagnosis_method", "diagnosis_model_version", "diagnosis_version",
        ):
            out[c] = pd.Series([None] * n, dtype=object)
        elif c == "diagnosis_valid":
            out[c] = False
        else:
            out[c] = np.nan

    group_cols = [c for c in ("cell_id", "file") if c in out.columns]
    if group_cols:
        groups = list(out.groupby(group_cols, sort=False))
    else:
        groups = [(("__all__",), out)]

    sidecar_rows: list[dict[str, Any]] = []

    for _, grp in groups:
        base = _baseline_row(grp, baseline_cycle)
        for idx, row in grp.iterrows():
            row_dict = row.to_dict()
            results = score_all_modes_for_row(
                row_dict, cfg, baseline_row=base, modes=mode_list,
            )
            qualities = []
            valids = []
            for mode, res in results.items():
                out.at[idx, score_column_name(mode)] = res.estimate
                out.at[idx, confidence_column_name(mode)] = res.confidence
                out.at[idx, f"{mode}_supporting_features"] = ",".join(res.supporting_features)
                out.at[idx, f"{mode}_conflicting_features"] = ",".join(res.conflicting_features)
                out.at[idx, f"{mode}_evidence_count"] = res.evidence_count
                qualities.append(res.data_quality_score)
                valids.append(res.diagnosis_valid)
                sidecar_rows.append({
                    "cycle": row_dict.get("cycle"),
                    "tagged_cycle": row_dict.get("tagged_cycle"),
                    "cell_id": row_dict.get("cell_id"),
                    **res.to_dict(),
                })

            out.at[idx, "diagnosis_quality_score"] = float(np.nanmean(qualities)) if qualities else 0.0
            out.at[idx, "diagnosis_valid"] = bool(any(valids))
            out.at[idx, "diagnosis_method"] = str(cfg.get("diagnosis_method", "rule_pattern"))
            out.at[idx, "diagnosis_model_version"] = str(
                cfg.get("diagnosis_model_version", DIAGNOSIS_MODEL_VERSION)
            )
            out.at[idx, "diagnosis_version"] = str(
                cfg.get("diagnosis_version", DIAGNOSIS_VERSION_FULLCELL)
            )
            # Level 2/3 intentionally null (not validated absolute estimates)
            for c in (
                "LLI_est", "LAM_PE_est", "LAM_NE_est", "electrode_slippage_est",
                "LLI_est_hc_calibrated", "LAM_PE_est_hc_calibrated", "LAM_NE_est_hc_calibrated",
            ):
                out.at[idx, c] = None

    if write_json_sidecar is not None:
        path = Path(write_json_sidecar)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sidecar_rows, indent=2, ensure_ascii=False), encoding="utf-8")

    return out
