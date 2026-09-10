"""Archived CLI entry points — restore to cyclediag/__main__.py to re-enable python -m cyclediag."""

from __future__ import annotations

import argparse
import sys

from cyclediag import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cyclediag",
        description="ML-based Voltage Profile diagnosis (Studio 2 engine)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("planning", help="Print path to planning docs")

    extract = sub.add_parser("extract", help="Raw CSV → feature table")
    extract.add_argument("--input", required=True)
    extract.add_argument("--out", required=True)
    extract.add_argument("--charge-step", default="charge")
    extract.add_argument("--discharge-step", default="discharge")
    extract.add_argument("--column-map", choices=("studio", "pne"), default="studio")
    extract.add_argument("--cv-only", action="store_true", help="CV regions table only (legacy)")
    extract.add_argument(
        "--feature-set",
        choices=("vp_v1_basic", "vp_lges_cycle_v1"),
        default="vp_lges_cycle_v1",
        help="Feature catalog (default: LGES cycle indicators)",
    )

    peaks = sub.add_parser("peaks", help="dQ/dV peak feature pipeline")
    peaks_sub = peaks.add_subparsers(dest="peaks_command", required=True)

    peaks_export = peaks_sub.add_parser("export", help="Raw CSV → peak feature tables")
    peaks_export.add_argument("--input", required=True)
    peaks_export.add_argument("--out-dir", required=True)
    peaks_export.add_argument("--cell-id", required=True)
    peaks_export.add_argument(
        "--good-cycles",
        default="10,50,80,163,210,255,283,327,426",
        help="Reference cycles for delta features",
    )
    peaks_export.add_argument("--relaxed", action="store_true", help="Looser usable filter")
    peaks_export.add_argument("--usable-mad-factor", type=float, default=2.0)
    peaks_export.add_argument("--max-noise", type=float, default=0.008)
    peaks_export.add_argument("--max-charge-hf", type=float, default=0.68)
    peaks_export.add_argument("--max-discharge-hf", type=float, default=0.58)
    peaks_export.add_argument("--max-band-gap", type=int, default=0)
    peaks_export.add_argument("--min-usable-score", type=float, default=0.0)

    train = sub.add_parser("train", help="Train peak ML model (Isolation Forest)")
    train.add_argument("--features", required=True, help="Peak feature CSV (usable rows)")
    train.add_argument("--out", required=True)
    train.add_argument(
        "--good-cycles",
        default="10,50,80,163,210,255,283,327",
        help="Reference cycles (metadata only)",
    )
    train.add_argument("--train-on", choices=("good_cycles", "usable", "all_complete"), default="usable")
    train.add_argument("--no-require-usable", action="store_true")

    predict = sub.add_parser("predict", help="Feature table → anomaly scores")
    predict.add_argument("--features", required=True)
    predict.add_argument("--out", required=True)
    predict.add_argument("--reference", default="", help="Reference table for z-score mode")
    predict.add_argument("--model", default="", help="Trained peak ML model directory")

    report = sub.add_parser("report", help="Batch diagnosis report (StepEnd folder)")
    report.add_argument("--input-dir", required=True)
    report.add_argument("--output-dir", default="")
    report.add_argument("--encoding", default="cp949")
    report.add_argument("--top-n", type=int, default=12)

    return p


def _load_table(path: str):
    from pathlib import Path

    import pandas as pd

    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p)


def _write_table(df, path: str) -> None:
    from pathlib import Path

    p = Path(path)
    if p.suffix.lower() == ".parquet":
        df.to_parquet(p, index=False)
    else:
        df.to_csv(p, index=False)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command is None:
        build_parser().print_help()
        return 0
    if args.command == "planning":
        from pathlib import Path

        root = Path(__file__).resolve().parents[2] / "planning"
        print(root)
        print("  ROADMAP.md  - phases")
        print("  FEATURES.md - ML feature catalog")
        print("  NOTES.md    - your instructions")
        return 0
    if args.command == "extract":
        from cyclediag.features.cv_extract import extract_cv_regions_table
        from cyclediag.features.extract import FeatureConfig, extract_features_table
        from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv

        cmap = (
            ColumnMap.studio_default()
            if args.column_map == "studio"
            else ColumnMap.pne_default()
        )
        df = load_cycler_csv(args.input, column_map=cmap)
        if args.cv_only:
            table = extract_cv_regions_table(
                df,
                charge_step=args.charge_step,
                discharge_step=args.discharge_step,
            )
        else:
            cfg = FeatureConfig(
                charge_step=args.charge_step,
                discharge_step=args.discharge_step,
                feature_set=args.feature_set,
            )
            table = extract_features_table(df, filepath=args.input, config=cfg)
        _write_table(table, args.out)
        print(f"Wrote {len(table)} row(s) → {args.out}")
        return 0
    if args.command == "peaks" and args.peaks_command == "export":
        from pathlib import Path

        from cyclediag.features.peak_export import (
            export_peak_feature_table,
            peak_trajectory_config_from_args,
        )

        good = [int(x.strip()) for x in args.good_cycles.split(",") if x.strip()]
        cfg = peak_trajectory_config_from_args(
            relaxed=args.relaxed,
            usable_mad_factor=args.usable_mad_factor,
            max_noise=args.max_noise,
            max_charge_hf=args.max_charge_hf,
            max_discharge_hf=args.max_discharge_hf,
            max_band_gap=args.max_band_gap,
            min_usable_score=args.min_usable_score,
        )
        out_dir = Path(args.out_dir) / args.cell_id
        meta = export_peak_feature_table(
            Path(args.input),
            out_dir,
            cell_id=args.cell_id,
            good_cycles=good,
            config=cfg,
        )
        print(f"Cell: {meta['cell_id']}")
        print(f"Total cycles: {meta['n_cycles_total']}")
        print(f"Usable: {meta['n_cycles_usable']} → {meta['outputs']['usable']}")
        return 0
    if args.command == "predict":
        feats = _load_table(args.features)
        if args.model:
            from cyclediag.models.peak_ml import PeakMlBundle, predict_peak_model

            bundle = PeakMlBundle.load(args.model)
            out = predict_peak_model(feats, bundle)
        else:
            from cyclediag.models.predict import predict_features

            ref = _load_table(args.reference) if args.reference else None
            out = predict_features(feats, reference=ref)
        _write_table(out, args.out)
        print(f"Wrote {len(out)} row(s) → {args.out}")
        return 0
    if args.command == "train":
        from cyclediag.models.peak_ml import PeakMlConfig, train_peak_model

        feats = _load_table(args.features)
        good = [int(x.strip()) for x in args.good_cycles.split(",") if x.strip()]
        cfg = PeakMlConfig(
            train_on=args.train_on,
            require_usable=not args.no_require_usable,
        )
        bundle = train_peak_model(feats, good_cycles=good, config=cfg)
        out_dir = bundle.save(args.out)
        print(f"Peak ML model saved → {out_dir}")
        print(f"  train rows: {bundle.train_rows}")
        print(f"  train cycles: {bundle.train_cycles}")
        print(f"  features: {len(bundle.feature_columns)}")
        return 0
    if args.command == "report":
        from cyclediag.analysis.batch_report import run_batch_report

        out_dir = args.output_dir or None
        summary = run_batch_report(
            args.input_dir,
            output_dir=out_dir,
            encoding=args.encoding,
            top_n=args.top_n,
        )
        odir = summary["output_dir"]
        print(f"Report written → {odir}")
        print(f"  HTML: {odir}/diagnosis_report.html")
        print(f"  Cells: {summary['n_cells_ok']}/{summary['n_files']}")
        return 0
    print("Unknown command — run with --help")
    return 1


if __name__ == "__main__":
    sys.exit(main())
