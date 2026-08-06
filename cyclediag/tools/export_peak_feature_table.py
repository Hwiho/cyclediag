"""Thin script wrapper — library: cyclediag.features.peak_export"""



from __future__ import annotations



import argparse

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from cyclediag.features.peak_export import (  # noqa: E402

    DEFAULT_GOOD_CYCLES,

    export_peak_feature_table,

    peak_trajectory_config_from_args,

)





def main() -> None:

    parser = argparse.ArgumentParser(description="Export peak feature table with quality filter")

    parser.add_argument("--input", type=Path, required=True)

    parser.add_argument("--out-dir", type=Path, default=ROOT / "example" / "docs" / "features")

    parser.add_argument("--cell-id", type=str, required=True)

    parser.add_argument("--good-cycles", type=str, default=",".join(str(c) for c in DEFAULT_GOOD_CYCLES))

    parser.add_argument("--assign-mode", choices=("band", "hybrid", "hungarian"), default="band")

    parser.add_argument("--assign-model-dir", type=Path, default=None)

    parser.add_argument("--retrain-assign", action="store_true")

    parser.add_argument("--relaxed", action="store_true")

    parser.add_argument("--no-plots", action="store_true")

    parser.add_argument("--no-protocol-exclude", action="store_true")

    parser.add_argument("--usable-mad-factor", type=float, default=2.0)

    parser.add_argument("--max-noise", type=float, default=0.008)

    parser.add_argument("--max-charge-hf", type=float, default=0.68)

    parser.add_argument("--max-discharge-hf", type=float, default=0.58)

    parser.add_argument("--max-band-gap", type=int, default=0)

    parser.add_argument("--min-usable-score", type=float, default=0.0)

    args = parser.parse_args()



    good = [int(x.strip()) for x in args.good_cycles.split(",") if x.strip()]

    cfg = peak_trajectory_config_from_args(

        relaxed=args.relaxed,

        assign_mode=args.assign_mode,

        usable_mad_factor=args.usable_mad_factor,

        max_noise=args.max_noise,

        max_charge_hf=args.max_charge_hf,

        max_discharge_hf=args.max_discharge_hf,

        max_band_gap=args.max_band_gap,

        min_usable_score=args.min_usable_score,

    )

    meta = export_peak_feature_table(

        args.input,

        args.out_dir / args.cell_id,

        cell_id=args.cell_id,

        good_cycles=good,

        config=cfg,

        assign_model_dir=args.assign_model_dir,

        exclude_protocol=not args.no_protocol_exclude,

        write_plots=not args.no_plots,

        retrain_assign=args.retrain_assign,

    )

    print(f"Usable: {meta['n_cycles_usable']}/{meta['n_cycles_total']} → {meta['outputs']['usable']}")





if __name__ == "__main__":

    main()


