"""Export band-based peak feature tables for ML."""



from __future__ import annotations



import json

from pathlib import Path



import numpy as np

import pandas as pd



from cyclediag.features.peak_assign import (

    PeakAssignBundle,

    PeakAssignConfig,

    train_peak_assign_from_raw,

)

from cyclediag.features.peak_stepemd_join import (

    correlate_peaks_with_fade,

    discover_stepend_for_raw,

    load_stepemd_cycle_table,

    merge_stepemd_into_wide,

)

from cyclediag.features.peak_trajectory import (

    PeakTrajectoryConfig,

    add_good_cycle_deltas,

    build_peak_tables,

)

from cyclediag.features.peak_tracking import build_peak_tracking_tables

from cyclediag.features.peak_plots import plot_peak_trajectories

from cyclediag.io.cycler_csv import load_cycler_csv

from cyclediag.io.cycle_protocol import apply_protocol_exclusion, build_protocol_exclusion

from cyclediag.io.stepemd_csv import load_stepemd_csv

from cyclediag.io.studio_map import studio_column_map



DEFAULT_GOOD_CYCLES = [10, 50, 80, 163, 210, 255, 283, 327, 426]





def peak_trajectory_config_from_args(

    *,

    relaxed: bool = False,

    assign_mode: str = "band",

    usable_mad_factor: float = 2.0,

    max_noise: float = 0.008,

    max_charge_hf: float = 0.68,

    max_discharge_hf: float = 0.58,

    max_band_gap: int = 0,

    min_usable_score: float = 0.0,

) -> PeakTrajectoryConfig:

    if relaxed:

        return PeakTrajectoryConfig(

            assign_mode=assign_mode,

            usable_mad_factor=2.5,

            max_noise_ratio=0.012,

            max_charge_hf_std=0.85,

            max_discharge_hf_std=0.85,

            max_band_gap=1,

            min_usable_score=0.0,

        )

    return PeakTrajectoryConfig(

        assign_mode=assign_mode,

        usable_mad_factor=usable_mad_factor,

        max_noise_ratio=max_noise,

        max_charge_hf_std=max_charge_hf,

        max_discharge_hf_std=max_discharge_hf,

        max_band_gap=max_band_gap,

        min_usable_score=min_usable_score,

    )





def _resolve_assign_bundle(

    *,

    df: pd.DataFrame,

    good_cycles: list[int],

    config: PeakTrajectoryConfig,

    out_dir: Path,

    cell_id: str,

    assign_model_dir: Path | str | None,

    retrain_assign: bool,

) -> tuple[PeakAssignBundle | None, Path | None]:

    """Load cached assign model, or train when hybrid/hungarian needs it."""

    if config.assign_mode == "band":

        return None, None



    assign_dir = Path(assign_model_dir) if assign_model_dir else out_dir / f"{cell_id}_peak_assign_model"

    model_file = assign_dir / "assign_model.joblib"



    if not retrain_assign and model_file.exists():

        return PeakAssignBundle.load(assign_dir), assign_dir



    bundle = train_peak_assign_from_raw(

        df,

        good_cycles,

        min_band_height_frac=config.min_band_height_frac,

        config=PeakAssignConfig(assign_mode=config.assign_mode),

    )

    bundle.save(assign_dir)

    return bundle, assign_dir





def _sync_usable_flags(wide_df: pd.DataFrame, long_df: pd.DataFrame) -> pd.DataFrame:

    usable_map = dict(zip(wide_df["cycle"], wide_df["usable"]))

    cha_map = dict(zip(wide_df["cycle"], wide_df["usable_charge"]))

    dis_map = dict(zip(wide_df["cycle"], wide_df["usable_discharge"]))

    long = long_df.copy()

    long["usable"] = long["cycle"].map(usable_map)

    is_charge = long["leg"] == "charge"

    long["usable_leg"] = np.where(is_charge, long["cycle"].map(cha_map), long["cycle"].map(dis_map))

    return long





def export_peak_feature_table(

    csv_path: Path,

    out_dir: Path,

    *,

    cell_id: str,

    good_cycles: list[int] | None = None,

    config: PeakTrajectoryConfig | None = None,

    stepemd_path: Path | str | None = None,

    assign_model_dir: Path | str | None = None,

    exclude_protocol: bool = True,

    write_plots: bool = True,

    retrain_assign: bool = False,

) -> dict:

    """Build wide/long peak tables and write CSV + meta JSON."""

    config = config or PeakTrajectoryConfig()

    good_cycles = good_cycles or DEFAULT_GOOD_CYCLES

    good_cycles_requested = list(good_cycles)

    out_dir.mkdir(parents=True, exist_ok=True)



    df = load_cycler_csv(str(csv_path), column_map=studio_column_map())

    stepemd_file = Path(stepemd_path) if stepemd_path else discover_stepend_for_raw(csv_path)

    step_df = pd.DataFrame()



    protocol = None

    if stepemd_file and stepemd_file.exists():

        step_df = load_stepemd_csv(stepemd_file)

        if exclude_protocol:

            protocol = build_protocol_exclusion(step_df)



    if protocol and protocol.excluded:

        good_cycles = [c for c in good_cycles if c not in protocol.excluded]



    assign_bundle, assign_dir = _resolve_assign_bundle(

        df=df,

        good_cycles=good_cycles,

        config=config,

        out_dir=out_dir,

        cell_id=cell_id,

        assign_model_dir=assign_model_dir,

        retrain_assign=retrain_assign,

    )



    long_df, wide_df = build_peak_tables(

        df,

        cell_id=cell_id,

        source_file=str(csv_path),

        config=config,

        assign_bundle=assign_bundle,

    )

    wide_df = add_good_cycle_deltas(wide_df, good_cycles)

    wide_df["good_cycle_ref"] = wide_df["cycle"].isin(good_cycles)



    if protocol is not None:

        wide_df, long_df = apply_protocol_exclusion(wide_df, long_df, protocol)

    else:

        wide_df["usable"] = wide_df["usable_auto"]

        long_df = _sync_usable_flags(wide_df, long_df)



    tracking_df, golden_df, summary_df = build_peak_tracking_tables(long_df, wide_df, good_cycles)



    stepemd_df = pd.DataFrame()

    merged_wide = wide_df

    fade_corr = pd.DataFrame()

    if not step_df.empty:

        stepemd_df = load_stepemd_cycle_table(stepemd_file, step_df=step_df)

        merged_wide = merge_stepemd_into_wide(wide_df, stepemd_df)

        fade_corr = correlate_peaks_with_fade(merged_wide)



    long_path = out_dir / f"{cell_id}_peak_trajectory_long.csv"

    wide_path = out_dir / f"{cell_id}_peak_features.csv"

    tracking_path = out_dir / f"{cell_id}_peak_tracking.csv"

    golden_path = out_dir / f"{cell_id}_peak_golden_ref.csv"

    summary_path = out_dir / f"{cell_id}_peak_tracking_summary.csv"

    merged_wide_path = out_dir / f"{cell_id}_peak_cycle_merged.csv"

    fade_corr_path = out_dir / f"{cell_id}_peak_fade_correlation.csv"

    plot_dir = out_dir / "plots"

    usable_path = out_dir / f"{cell_id}_peak_features_usable.csv"

    usable_ch_path = out_dir / f"{cell_id}_peak_features_usable_charge.csv"

    excluded_path = out_dir / f"{cell_id}_peak_features_excluded.csv"

    protocol_flags_path = out_dir / f"{cell_id}_protocol_flags.csv"

    protocol_json_path = out_dir / f"{cell_id}_protocol_exclude.json"



    def _safe_csv(frame: pd.DataFrame, path: Path) -> Path:

        try:

            frame.to_csv(path, index=False, encoding="utf-8-sig")

            return path

        except PermissionError:

            alt = path.with_name(path.stem + "_strict" + path.suffix)

            frame.to_csv(alt, index=False, encoding="utf-8-sig")

            return alt



    long_df.to_csv(long_path, index=False, encoding="utf-8-sig")

    wide_df.to_csv(wide_path, index=False, encoding="utf-8-sig")

    tracking_df.to_csv(tracking_path, index=False, encoding="utf-8-sig")

    golden_df.to_csv(golden_path, index=False, encoding="utf-8-sig")

    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    if not merged_wide.empty:

        merged_wide.to_csv(merged_wide_path, index=False, encoding="utf-8-sig")

    if not fade_corr.empty:

        fade_corr.to_csv(fade_corr_path, index=False, encoding="utf-8-sig")

    plot_paths = plot_peak_trajectories(tracking_df, plot_dir, cell_id=cell_id) if write_plots else []

    usable = wide_df[wide_df["usable"]].copy()

    usable_charge = wide_df[wide_df["usable_charge"]].copy()

    excluded = wide_df[~wide_df["usable"]].copy()

    usable_path = _safe_csv(usable, usable_path)

    usable_ch_path = _safe_csv(usable_charge, usable_ch_path)

    excluded_path = _safe_csv(excluded, excluded_path)

    if protocol is not None and not protocol.flags.empty:

        protocol.flags.to_csv(protocol_flags_path, index=False, encoding="utf-8-sig")

        protocol_json_path.write_text(

            json.dumps(protocol.to_meta(), indent=2, ensure_ascii=False),

            encoding="utf-8",

        )



    meta = {

        "cell_id": cell_id,

        "source_file": str(csv_path),

        "n_cycles_total": int(len(wide_df)),

        "n_cycles_usable": int(len(usable)),

        "n_cycles_usable_charge": int(len(usable_charge)),

        "n_cycles_excluded": int(len(excluded)),

        "good_cycles": good_cycles,

        "good_cycles_requested": good_cycles_requested,

        "exclude_protocol": exclude_protocol,

        "protocol_exclusion": protocol.to_meta() if protocol else None,

        "assign_mode": config.assign_mode,

        "assign_model": str(assign_dir) if assign_dir else None,

        "stepemd_file": str(stepemd_file) if stepemd_file else None,

        "config": {

            "sg_window": config.sg_window,

            "min_band_height_frac": config.min_band_height_frac,

            "assign_mode": config.assign_mode,

            "usable_mad_factor": config.usable_mad_factor,

            "max_noise_ratio": config.max_noise_ratio,

            "max_charge_hf_std": config.max_charge_hf_std,

            "max_discharge_hf_std": config.max_discharge_hf_std,

            "max_band_gap": config.max_band_gap,

            "min_usable_score": config.min_usable_score,

        },

        "quality_median": float(wide_df["quality_median"].iloc[0]) if len(wide_df) else None,

        "quality_threshold": float(wide_df["quality_threshold"].iloc[0]) if len(wide_df) else None,

        "outputs": {

            "long": str(long_path),

            "wide": str(wide_path),

            "tracking": str(tracking_path),

            "golden_ref": str(golden_path),

            "tracking_summary": str(summary_path),

            "assign_model": str(assign_dir) if assign_dir else None,

            "learned_criteria": str(assign_dir / "learned_criteria.json") if assign_dir else None,

            "merged_cycle": str(merged_wide_path) if not merged_wide.empty else None,

            "fade_correlation": str(fade_corr_path) if not fade_corr.empty else None,

            "plots": [str(p) for p in plot_paths],

            "usable": str(usable_path),

            "usable_charge": str(usable_ch_path),

            "excluded": str(excluded_path),

            "protocol_flags": str(protocol_flags_path) if protocol is not None and not protocol.flags.empty else None,

            "protocol_exclude": str(protocol_json_path) if protocol is not None and not protocol.flags.empty else None,

        },

    }

    meta_path = out_dir / f"{cell_id}_peak_features_meta.json"

    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")



    readme = out_dir / "README.txt"

    readme.write_text(

        f"Peak feature table — {cell_id}\n"

        f"Method: SG w={config.sg_window} + voltage band assign ({config.assign_mode})\n"

        f"Total cycles: {meta['n_cycles_total']}\n"

        f"Usable (both legs): {meta['n_cycles_usable']}\n"

        f"Usable charge only: {meta['n_cycles_usable_charge']}\n"

        f"Excluded: {meta['n_cycles_excluded']}\n\n"

        "Routine-life scope:\n"

        f"  exclude_protocol={exclude_protocol} (RPT + capacheck + {protocol.post_rpt_exclude if protocol else 5} cycles after each RPT block)\n\n"

        "Usable criteria (strict):\n"

        f"  quality_score <= median + {config.usable_mad_factor}*MAD\n"

        f"  usable_score >= {config.min_usable_score}\n"

        f"  noise_ratio_mean <= {config.max_noise_ratio}\n"

        f"  band_gap_total <= {config.max_band_gap}\n"

        f"  charge hf <= {config.max_charge_hf_std}, discharge hf <= {config.max_discharge_hf_std}\n"

        "  all charge/discharge bands present\n\n"

        "Main outputs:\n"

        f"  {cell_id}_peak_cycle_merged.csv — peaks + SoHQ\n"

        f"  {cell_id}_peak_tracking.csv — V, H_norm, drift\n"

        f"  {cell_id}_peak_fade_correlation.csv — peak vs fade r\n\n"

        f"Good cycles: {good_cycles}\n",

        encoding="utf-8",

    )

    return meta


