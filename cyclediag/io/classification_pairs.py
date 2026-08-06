"""Load PairLabel Cycle-N mapping from *_classification.csv (pne_studio parity)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class TaggedCycle:
    """One tagged (display) cycle mapped to raw TotalCycle."""

    tagged_cycle: int
    raw_cycle: int
    pair_label: str
    source: str  # classification | routine


def classification_path_for_raw(raw_path: str | Path) -> Path | None:
    path = Path(raw_path)
    cls = path.with_name(path.name.removesuffix("_raw.csv") + "_classification.csv")
    return cls if cls.is_file() else None


def _to_int(val: str) -> int | None:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def load_pair_cycles(classification_path: str | Path) -> dict[int, str]:
    """Map raw TotalCycle -> PairLabel (e.g. Cycle-001)."""
    cls_df = pd.read_csv(classification_path, on_bad_lines="skip", low_memory=False)
    pl_col = cyc_col = None
    for col in cls_df.columns:
        cc = str(col).lower().replace(" ", "").replace("_", "")
        if "pairlabel" in cc:
            pl_col = col
        if "totalcycle" in cc or cc == "cycle":
            cyc_col = col
    pair_cycles: dict[int, str] = {}
    if not pl_col or not cyc_col:
        return pair_cycles
    for _, row in cls_df.dropna(subset=[pl_col, cyc_col]).iterrows():
        label = str(row[pl_col]).strip()
        m = re.match(r"(?i)cycle-?(\d+)", label)
        if not m:
            continue
        raw_cyc = _to_int(str(row[cyc_col]))
        if raw_cyc is not None:
            pair_cycles[raw_cyc] = f"Cycle-{int(m.group(1))}"
    return pair_cycles


def tagged_entries(pair_cycles: dict[int, str]) -> list[tuple[int, int, str]]:
    """(tagged_number, raw_total_cycle, label) sorted by tagged_number."""
    out: list[tuple[int, int, str]] = []
    for raw, label in pair_cycles.items():
        m = re.match(r"(?i)cycle-?(\d+)", label)
        if m:
            out.append((int(m.group(1)), int(raw), label))
    return sorted(out, key=lambda x: (x[0], x[1]))


def resolve_tagged_raw_cycle(
    pair_cycles: dict[int, str],
    tagged_number: int = 1,
) -> tuple[int, str] | None:
    for tagged, raw, label in tagged_entries(pair_cycles):
        if tagged == tagged_number:
            return raw, label
    return None


def resolve_tagged_cycles_for_raw(
    raw_path: str | Path,
    *,
    allow_routine_fallback: bool = True,
) -> list[TaggedCycle]:
    """Tagged cycles for export/plot (PNE Studio «Tagged only» parity).

    1. ``*_classification.csv`` PairLabel ``Cycle-N`` rows
    2. Else routine life cycles from StepEnd protocol (if ``*_stepend.csv`` exists)
    """
    raw_path = Path(raw_path)
    cls_path = classification_path_for_raw(raw_path)
    if cls_path is not None:
        pairs = load_pair_cycles(cls_path)
        entries = tagged_entries(pairs)
        if entries:
            return [
                TaggedCycle(tagged, raw, label, "classification")
                for tagged, raw, label in entries
            ]

    if not allow_routine_fallback:
        return []

    try:
        from cyclediag.features.peak_stepemd_join import discover_stepend_for_raw
        from cyclediag.io.cycle_protocol import build_protocol_exclusion
        from cyclediag.io.stepemd_csv import load_stepemd_csv
    except ImportError:
        return []

    stepemd = discover_stepend_for_raw(raw_path)
    if stepemd is None or not stepemd.exists():
        return []

    protocol = build_protocol_exclusion(load_stepemd_csv(stepemd))
    flags = protocol.flags
    if flags is None or flags.empty:
        return []

    routine = flags[
        (flags["protocol_kind"] == "routine") & (~flags["protocol_excluded"])
    ].sort_values("cycle")
    out: list[TaggedCycle] = []
    for i, row in enumerate(routine.itertuples(index=False), start=1):
        raw_cyc = int(getattr(row, "cycle"))
        out.append(TaggedCycle(i, raw_cyc, f"Cycle-{i}", "routine"))
    return out


def tagged_raw_cycles(raw_path: str | Path, **kwargs) -> list[int]:
    """Raw TotalCycle ids for tagged cycles only."""
    return [t.raw_cycle for t in resolve_tagged_cycles_for_raw(raw_path, **kwargs)]


def baseline_raw_cycle_for_tagged(raw_path: str | Path, **kwargs) -> int | None:
    """Raw cycle for tagged Cycle-1 (SoHQ / delta baseline)."""
    tagged = resolve_tagged_cycles_for_raw(raw_path, **kwargs)
    for t in tagged:
        if t.tagged_cycle == 1:
            return t.raw_cycle
    return tagged[0].raw_cycle if tagged else None
