"""Train cross-cell peak assign model from multiple raw CSVs + golden cycles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import (  # noqa: E402
    DqdvPeakConfig,
    charge_discharge_bands,
    find_dqdv_peaks_banded,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv  # noqa: E402
from cyclediag.features.peak_assign import PeakAssignSample, train_peak_assign_multi  # noqa: E402
from cyclediag.features.segment_utils import leg_segment  # noqa: E402
from cyclediag.io.cycler_csv import load_cycler_csv  # noqa: E402
from cyclediag.io.studio_map import studio_column_map  # noqa: E402


def _labels_from_raw(raw_path: Path, good_cycles: list[int], cell_id: str) -> PeakAssignSample:
    df = load_cycler_csv(str(raw_path), column_map=studio_column_map())
    dqcfg = DqdvPeakConfig(sg_window=31)
    rows: list[dict] = []
    for tc in good_cycles:
        cyc = df[df["cycle"] == tc]
        for leg in ("charge", "discharge"):
            seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
            seg = prepare_leg_segment_for_dqdv(seg, leg)
            col = "charge_capacity" if leg == "charge" else "discharge_capacity"
            if col not in seg.columns:
                col = "capacity"
            if seg.empty or col not in seg.columns:
                continue
            v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
            q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
            for pk in find_dqdv_peaks_banded(v, q, charge_discharge_bands(leg), config=dqcfg):
                rows.append({
                    "cycle": int(tc),
                    "leg": leg,
                    "peak_id": pk["band"],
                    "V": pk["V"],
                    "H": pk["H"],
                })
    return PeakAssignSample(cell_id=cell_id, labels=pd.DataFrame(rows), good_cycles=good_cycles)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train global peak assign model")
    parser.add_argument("--config", type=Path, required=True, help="JSON list of {raw, cell_id, good_cycles}")
    parser.add_argument("--out", type=Path, default=ROOT / "example" / "docs" / "models" / "peak_assign_global_v1")
    args = parser.parse_args()

    spec = json.loads(args.config.read_text(encoding="utf-8"))
    samples = [
        _labels_from_raw(Path(entry["raw"]), [int(x) for x in entry["good_cycles"]], entry["cell_id"])
        for entry in spec
    ]
    bundle = train_peak_assign_multi(samples)
    out = bundle.save(args.out)
    print(f"Global assign model → {out}")
    print(f"  cells: {bundle.training_cells}")
    print(f"  train rows: {bundle.train_rows}")


if __name__ == "__main__":
    main()
