"""Band-based dQ/dV peak trajectory + internal cycle quality scoring."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .dqdv_peaks import (
    DqdvPeakConfig,
    _noise_mad,
    _smooth,
    charge_discharge_bands,
    prepare_dqdv_arrays,
)
from .peak_assign import PeakAssignBundle, assign_peaks_for_leg
from .dqdv_segment import prepare_leg_segment_for_dqdv
from .segment_utils import leg_segment


@dataclass
class PeakTrajectoryConfig:
    sg_window: int = 31
    min_band_height_frac: float = 0.12
    min_leg_points: int = 100
    expected_charge_bands: int = 4
    expected_discharge_bands: int = 3
    # Auto-usable thresholds (strict defaults for trend analysis)
    usable_mad_factor: float = 2.0
    max_noise_ratio: float = 0.008
    max_charge_hf_std: float = 0.68
    max_discharge_hf_std: float = 0.58
    max_band_gap: int = 0
    min_usable_score: float = 0.0
    assign_mode: str = "band"  # band | hungarian | hybrid | evolution | deconv


def _capacity_col(seg: pd.DataFrame, leg: str) -> str | None:
    col = "charge_capacity" if leg == "charge" else "discharge_capacity"
    if col in seg.columns:
        return col
    return "capacity" if "capacity" in seg.columns else None


def _leg_metrics(
    cycle_df: pd.DataFrame,
    leg: str,
    cfg: PeakTrajectoryConfig,
    *,
    assign_bundle: PeakAssignBundle | None = None,
) -> dict | None:
    dqcfg = DqdvPeakConfig(sg_window=cfg.sg_window)
    seg = leg_segment(cycle_df, leg, charge_text="charge", discharge_text="discharge")
    seg = prepare_leg_segment_for_dqdv(seg, leg)
    col = _capacity_col(seg, leg)
    if seg.empty or col is None or "voltage" not in seg.columns:
        return None

    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
    if len(vx) < 5:
        return None

    y_smooth = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)
    mad = _noise_mad(dqdv, y_smooth)
    ymax = float(np.nanmax(np.abs(y_smooth))) if len(y_smooth) else 0.0
    noise_ratio = mad / ymax if ymax > 0 else 999.0
    hf_std = float(np.nanstd(np.diff(y_smooth))) if len(y_smooth) > 2 else 999.0

    peaks = assign_peaks_for_leg(
        v,
        q,
        leg,
        dqcfg=dqcfg,
        min_band_height_frac=cfg.min_band_height_frac,
        bundle=assign_bundle,
        assign_mode=cfg.assign_mode,
        vx=vx,
        dqdv=dqdv,
        y_smooth=y_smooth,
    )
    expected = cfg.expected_charge_bands if leg == "charge" else cfg.expected_discharge_bands

    return {
        "leg": leg,
        "n_pts": len(seg),
        "noise_ratio": noise_ratio,
        "hf_std": hf_std,
        "n_bands": len(peaks),
        "expected_bands": expected,
        "band_gap": max(0, expected - len(peaks)),
        "peaks": peaks,
    }


def cycle_quality_score(ch: dict | None, dc: dict | None, cfg: PeakTrajectoryConfig) -> dict:
    """Lower quality_score = cleaner cycle. Higher usable_score = cleaner (0–1)."""
    parts: list[str] = []
    noise_vals: list[float] = []
    hf_vals: list[float] = []
    band_gap = 0
    n_pts_min = 0

    for leg_dict, name in ((ch, "charge"), (dc, "discharge")):
        if leg_dict is None:
            parts.append(f"missing_{name}")
            band_gap += cfg.expected_charge_bands if name == "charge" else cfg.expected_discharge_bands
            continue
        noise_vals.append(float(leg_dict["noise_ratio"]))
        hf_vals.append(float(leg_dict["hf_std"]))
        band_gap += int(leg_dict["band_gap"])
        n_pts_min = max(n_pts_min, int(leg_dict["n_pts"])) if n_pts_min == 0 else min(n_pts_min, int(leg_dict["n_pts"]))

    noise = float(np.mean(noise_vals)) if noise_vals else 999.0
    hf = float(np.mean(hf_vals)) if hf_vals else 999.0
    pts_pen = 5.0 if n_pts_min < cfg.min_leg_points else 0.0
    quality = noise * 3.0 + hf * 0.15 + band_gap * 0.35 + pts_pen

    return {
        "noise_ratio_mean": noise,
        "hf_std_mean": hf,
        "band_gap_total": band_gap,
        "n_pts_min": n_pts_min,
        "quality_score": quality,
        "exclude_flags": "|".join(parts) if parts else "",
    }


def _leg_usable(leg_dict: dict | None, leg: str, cfg: PeakTrajectoryConfig) -> bool:
    if leg_dict is None:
        return False
    expected = cfg.expected_charge_bands if leg == "charge" else cfg.expected_discharge_bands
    hf_cap = cfg.max_charge_hf_std if leg == "charge" else cfg.max_discharge_hf_std
    return (
        int(leg_dict["n_bands"]) >= expected
        and int(leg_dict["n_pts"]) >= cfg.min_leg_points
        and float(leg_dict["noise_ratio"]) <= cfg.max_noise_ratio
        and float(leg_dict["hf_std"]) <= hf_cap
    )


def _composite_usable_score(
    quality_score: float,
    noise_ratio: float,
    hf_std: float,
    *,
    quality_median: float,
    quality_mad: float,
    cfg: PeakTrajectoryConfig,
) -> float:
    """0–1 cleanliness rank; higher is better. Uses quality + noise + hf penalties."""
    if quality_score > 100:
        return 0.0
    q_pen = np.clip((quality_score - quality_median) / (3.0 * quality_mad * 1.4826 + 1e-9), 0.0, 1.5)
    n_pen = np.clip(noise_ratio / cfg.max_noise_ratio, 0.0, 1.5)
    hf_cap = max(cfg.max_charge_hf_std, cfg.max_discharge_hf_std)
    h_pen = np.clip(hf_std / hf_cap, 0.0, 1.5)
    penalty = 0.5 * q_pen + 0.25 * n_pen + 0.25 * h_pen
    return float(np.clip(1.0 - penalty / 1.2, 0.0, 1.0))


def build_peak_tables(
    df: pd.DataFrame,
    *,
    cell_id: str = "",
    source_file: str = "",
    config: PeakTrajectoryConfig | None = None,
    assign_bundle: PeakAssignBundle | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (long_trajectory, wide_features) for all cycles in df."""
    config = config or PeakTrajectoryConfig()
    grouped = {
        int(tc): grp for tc, grp in df.groupby("cycle", sort=True)
    }
    cycles = sorted(grouped)

    cycle_rows: list[dict] = []
    long_rows: list[dict] = []

    for tc in cycles:
        cyc = grouped[tc]
        ch = _leg_metrics(cyc, "charge", config, assign_bundle=assign_bundle)
        dc = _leg_metrics(cyc, "discharge", config, assign_bundle=assign_bundle)
        qmeta = cycle_quality_score(ch, dc, config)

        wide: dict = {
            "cell_id": cell_id,
            "source_file": source_file,
            "cycle": tc,
            **qmeta,
            "usable_charge": _leg_usable(ch, "charge", config),
            "usable_discharge": _leg_usable(dc, "discharge", config),
        }
        if not wide.get("exclude_flags"):
            wide["exclude_flags"] = ""

        for leg_dict in (ch, dc):
            if leg_dict is None:
                continue
            leg = leg_dict["leg"]
            wide[f"{leg[:3]}_n_bands"] = leg_dict["n_bands"]
            wide[f"{leg[:3]}_noise_ratio"] = leg_dict["noise_ratio"]
            wide[f"{leg[:3]}_hf_std"] = leg_dict["hf_std"]
            for pk in leg_dict["peaks"]:
                band = str(pk["band"])
                prefix = f"{leg[:3]}_{band}"
                wide[f"{prefix}_V"] = pk["V"]
                wide[f"{prefix}_H"] = pk["H"]
                long_rows.append({
                    "cell_id": cell_id,
                    "source_file": source_file,
                    "cycle": tc,
                    "leg": leg,
                    "band": band,
                    "V": pk["V"],
                    "H": pk["H"],
                    "band_height_frac": pk.get("band_height_frac"),
                    "assign_confidence": pk.get("assign_confidence"),
                    "assign_method": pk.get("assign_method", "band"),
                    "ml_peak_id": pk.get("ml_peak_id", ""),
                    "ml_assign_confidence": pk.get("ml_assign_confidence"),
                    "noise_ratio": leg_dict["noise_ratio"],
                    "hf_std": leg_dict["hf_std"],
                })

        cycle_rows.append(wide)

    wide_df = pd.DataFrame(cycle_rows)
    long_df = pd.DataFrame(long_rows)

    if wide_df.empty:
        wide_df["usable"] = []
        wide_df["usable_score"] = []
        return long_df, wide_df

    q = wide_df["quality_score"].to_numpy(dtype=float)
    med = float(np.median(q))
    mad = float(np.median(np.abs(q - med)))
    mad = mad if mad > 1e-12 else float(np.std(q)) or 1e-6
    threshold = med + config.usable_mad_factor * mad * 1.4826

    wide_df["quality_median"] = med
    wide_df["quality_threshold"] = threshold

    q_arr = wide_df["quality_score"].to_numpy(dtype=float)
    n_arr = wide_df["noise_ratio_mean"].to_numpy(dtype=float)
    h_arr = wide_df["hf_std_mean"].to_numpy(dtype=float)
    hf_cap = max(config.max_charge_hf_std, config.max_discharge_hf_std)
    q_pen = np.clip((q_arr - med) / (3.0 * mad * 1.4826 + 1e-9), 0.0, 1.5)
    n_pen = np.clip(n_arr / config.max_noise_ratio, 0.0, 1.5)
    h_pen = np.clip(h_arr / hf_cap, 0.0, 1.5)
    penalty = 0.5 * q_pen + 0.25 * n_pen + 0.25 * h_pen
    wide_df["usable_score"] = np.clip(1.0 - penalty / 1.2, 0.0, 1.0)
    wide_df.loc[q_arr > 100, "usable_score"] = 0.0

    wide_df["usable_auto"] = (
        (wide_df["quality_score"] <= threshold)
        & (wide_df["noise_ratio_mean"] <= config.max_noise_ratio)
        & (wide_df["band_gap_total"] <= config.max_band_gap)
        & (wide_df["exclude_flags"] == "")
        & wide_df["usable_charge"]
        & wide_df["usable_discharge"]
    )
    if config.min_usable_score > 0:
        wide_df["usable_auto"] = wide_df["usable_auto"] & (
            wide_df["usable_score"] >= config.min_usable_score
        )
    wide_df["usable"] = wide_df["usable_auto"]

    return long_df, wide_df


def add_good_cycle_deltas(
    wide_df: pd.DataFrame,
    good_cycles: list[int],
    *,
    value_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Add delta vs median of good_cycles for numeric peak columns."""
    if wide_df.empty or not good_cycles:
        return wide_df

    out = wide_df.copy()
    good = out[out["cycle"].isin(good_cycles)]
    if good.empty:
        return out

    if value_cols is None:
        value_cols = [c for c in out.columns if c.endswith("_V") or c.endswith("_H")]

    for col in value_cols:
        if col not in out.columns:
            continue
        ref = good[col].median(numeric_only=True)
        if pd.notna(ref):
            out[f"d_{col}"] = out[col] - ref

    return out
