"""Run new cyclediag ASSB metrics on SJ900 set4 and print interpretation tables."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.diagnosis.engine import diagnose_feature_table
from cyclediag.features.enrich_assb import enrich_feature_table
from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_features_table
from cyclediag.io.cycler_csv import load_cycler_csv
from cyclediag.io.studio_map import studio_column_map

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "example" / "output" / "set4_new"
OUT.mkdir(parents=True, exist_ok=True)


def _find_raw(patterns: list[str]) -> Path | None:
    for pat in patterns:
        hits = list(ROOT.glob(pat))
        if hits:
            return hits[0]
    return None


CELLS = {
    "M01Ch022": _find_raw(
        [
            "example/docs/features/M01Ch022/*Ch22*raw.csv",
            "example/docs/peak_review/_tmp_raw/*Ch22*raw.csv",
        ]
    ),
    "M01Ch025": _find_raw(
        [
            "example/docs/peak_review/_tmp_raw/*Ch25*raw.csv",
            "example/docs/features/**/*Ch25*raw.csv",
        ]
    ),
}


def pick_cycles(raw: pd.DataFrame) -> list[int]:
    """DCIR pulses + pre-capa pairs + routine every ~25 cycles."""
    i = pd.to_numeric(raw["current"], errors="coerce").abs()
    pulse = sorted(
        {
            int(c)
            for c, g in raw.groupby("cycle")
            if float(pd.to_numeric(g["current"], errors="coerce").abs().max()) >= 50
        }
    )
    cycles = set()
    for p in pulse:
        cycles.update([p - 2, p - 1, p])
        if p + 1 in raw["cycle"].values:
            cycles.add(p + 1)
        if p + 2 in raw["cycle"].values:
            cycles.add(p + 2)
    all_c = sorted(int(x) for x in raw["cycle"].dropna().unique())
    # sample routine trajectory
    for c in all_c[::25]:
        cycles.add(c)
    cycles.update(all_c[:5])
    cycles.update(all_c[-5:])
    return sorted(c for c in cycles if c in set(all_c))


def summarize_cell(cell_id: str, raw_path: Path) -> dict:
    print(f"\n=== {cell_id} ===")
    print("loading", raw_path.name)
    raw = load_cycler_csv(str(raw_path), column_map=studio_column_map())
    cycles = pick_cycles(raw)
    print(f"cycles selected: {len(cycles)} / {raw['cycle'].nunique()}")

    cfg = LgesExtractConfig(
        cell_id=cell_id,
        enrich_assb=True,
        with_diagnosis=True,
        auto_baseline=True,
        rest_current_max=0.5,
        expected_pulse_current=70.0,
        # peaks slow — keep default for now on subset
    )
    feats = extract_lges_features_table(
        raw, cycles=cycles, filepath=str(raw_path), config=cfg, raw_df=raw
    )
    # enrich already inside extract; ensure diagnosis columns present
    if "contact_loss_score" not in feats.columns and "LLI_pattern_score" not in feats.columns:
        feats = diagnose_feature_table(feats)

    out_csv = OUT / f"{cell_id}_new_subset.csv"
    feats.to_csv(out_csv, index=False)
    print("wrote", out_csv)

    # ---- trajectory summaries ----
    d = feats.copy()
    d = d.sort_values("cycle")

    def _series(col):
        if col not in d.columns:
            return None
        s = pd.to_numeric(d[col], errors="coerce")
        return s

    sohq = _series("SoHQ")
    ce = _series("CE")
    ve = _series("VE")
    rcf = _series("RCF")

    # DCIR soc50 rows
    pulse_mask = d["cycle"].isin(
        [
            int(c)
            for c, g in raw.groupby("cycle")
            if float(pd.to_numeric(g["current"], errors="coerce").abs().max()) >= 50
        ]
    )
    dcir = d.loc[pulse_mask].copy()

    def first_last(col):
        s = pd.to_numeric(dcir.get(col), errors="coerce").dropna()
        if s.empty:
            return None, None, None
        return float(s.iloc[0]), float(s.iloc[-1]), float(s.iloc[-1] - s.iloc[0])

    summary = {
        "cell_id": cell_id,
        "n_cycles_raw": int(raw["cycle"].nunique()),
        "n_cycles_analyzed": int(len(d)),
        "baseline_cycle": int(d["cycle"].iloc[0]) if len(d) else None,
        "SoHQ_first": float(sohq.dropna().iloc[0]) if sohq is not None and sohq.notna().any() else None,
        "SoHQ_last": float(sohq.dropna().iloc[-1]) if sohq is not None and sohq.notna().any() else None,
        "CE_median": float(ce.median()) if ce is not None else None,
        "VE_first": float(ve.dropna().iloc[0]) if ve is not None and ve.notna().any() else None,
        "VE_last": float(ve.dropna().iloc[-1]) if ve is not None and ve.notna().any() else None,
        "RCF_median": float(rcf.median()) if rcf is not None and rcf.notna().any() else None,
    }

    for col in (
        "R_ohmic_soc50",
        "R_ct_soc50",
        "A_diff_soc50",
        "R_30s_total_soc50",
        "self_discharge_rate_soc80",
        "Q_relax_pct",
        "hyst_frac_low",
        "quality_score",
        "contact_loss_score",
        "interface_R_score",
        "microshort_score",
        "LLI_pattern_score",
        "LAM_PE_pattern_score",
        "solid_diffusion_score",
    ):
        a, b, db = first_last(col) if "soc" in col or col.startswith("self") or col.startswith("R_") else (None, None, None)
        if col.startswith("R_") or col.startswith("self"):
            summary[f"{col}_first"] = a
            summary[f"{col}_last"] = b
            summary[f"{col}_delta"] = db
        else:
            s = pd.to_numeric(d.get(col), errors="coerce")
            if s is not None and s.notna().any():
                summary[f"{col}_med"] = float(s.median())
                summary[f"{col}_last"] = float(s.dropna().iloc[-1])

    # Q_relax table
    qr = d.dropna(subset=["Q_relax_pct"]) if "Q_relax_pct" in d.columns else pd.DataFrame()
    summary["Q_relax_blocks"] = (
        qr[["cycle", "Q_relax", "Q_relax_pct", "Q_relax_significant"]].drop_duplicates().to_dict("records")
        if len(qr)
        else []
    )

    # mode scores late vs early (non-pulse)
    routine = d.loc[~pulse_mask]
    for mode in (
        "contact_loss_score",
        "interface_R_score",
        "SE_decomposition_score",
        "microshort_score",
        "LLI_pattern_score",
        "LAM_PE_pattern_score",
        "solid_diffusion_score",
    ):
        if mode not in routine.columns:
            continue
        s = pd.to_numeric(routine[mode], errors="coerce").dropna()
        if len(s) < 4:
            continue
        summary[f"{mode}_early"] = float(s.iloc[: max(2, len(s)//5)].mean())
        summary[f"{mode}_late"] = float(s.iloc[-max(2, len(s)//5) :].mean())

    # DCIR trend table
    cols_dcir = [
        c
        for c in (
            "cycle",
            "R_ohmic_soc50",
            "R_ct_soc50",
            "tau_ct_soc50",
            "A_diff_soc50",
            "R_30s_total_soc50",
            "R_ohmic_frac_soc50",
            "self_discharge_rate_soc80",
            "R_ratio_20_50",
            "R_SOC_slope",
            "dcir_fit_valid_soc50",
        )
        if c in dcir.columns
    ]
    dcir_out = dcir[cols_dcir].drop_duplicates("cycle") if cols_dcir else pd.DataFrame()
    dcir_path = OUT / f"{cell_id}_dcir_trend.csv"
    dcir_out.to_csv(dcir_path, index=False)
    summary["dcir_trend_path"] = str(dcir_path)
    summary["dcir_n"] = int(len(dcir_out))

    (OUT / f"{cell_id}_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith("_blocks")}, indent=2, default=str)[:2500])
    return summary


def main():
    all_sum = []
    for cid, path in CELLS.items():
        if not path.exists():
            print("MISSING", path)
            continue
        all_sum.append(summarize_cell(cid, path))
    (OUT / "set4_summary.json").write_text(
        json.dumps(all_sum, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print("\nDONE", OUT)


if __name__ == "__main__":
    main()
