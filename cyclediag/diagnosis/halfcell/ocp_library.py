"""BOL half-cell OCP library — load C/20 anode/cathode templates.

Aged half-cell is NOT required for library construction. Use cycle 2–3 for
anode (cycle 1 is formation-heavy). Cathode fixtures may be single-leg only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cyclediag.features.dqdv_peaks import DqdvPeakConfig, find_dqdv_peaks

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HALFCELL_DIR = ROOT / "example" / "fixtures" / "halfcell"


@dataclass
class OcpCurve:
    electrode: str  # "anode" | "cathode"
    cell_id: str
    leg: str  # charge | discharge
    cycle: int
    q_norm: np.ndarray
    voltage: np.ndarray
    q_raw_span: float
    v_min: float
    v_max: float
    peaks: list[dict[str, Any]] = field(default_factory=list)
    source_path: str = ""


@dataclass
class OcpLibrary:
    anode: list[OcpCurve] = field(default_factory=list)
    cathode: list[OcpCurve] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def cathode_peak_voltages(self, *, leg: str = "charge", max_peaks: int = 6) -> list[float]:
        curves = [c for c in self.cathode if c.leg == leg and c.peaks]
        if not curves:
            curves = [c for c in self.cathode if c.peaks]
        if not curves:
            return []
        # prefer first available
        return [float(p["V"]) for p in curves[0].peaks[:max_peaks]]

    def anode_peak_voltages(self, *, leg: str = "discharge", max_peaks: int = 6) -> list[float]:
        curves = [c for c in self.anode if c.leg == leg and c.peaks]
        if not curves:
            curves = [c for c in self.anode if c.peaks]
        if not curves:
            return []
        # prefer cycle >= 2 when available
        ranked = sorted(curves, key=lambda c: (0 if c.cycle >= 2 else 1, -c.cycle))
        return [float(p["V"]) for p in ranked[0].peaks[:max_peaks]]


def _read_halfcell_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    rename = {
        "TotalCycle": "cycle",
        "Voltage": "voltage",
        "Capacity": "capacity",
        "StepType": "step_type",
        "TotalTime_sec": "time",
    }
    return df.rename(columns={k: v for k, v in rename.items() if k in df.columns})


def _leg_curve(
    df: pd.DataFrame,
    *,
    cycle: int,
    leg: str,
    electrode: str,
    cell_id: str,
    source_path: str,
    peak_cfg: DqdvPeakConfig | None = None,
) -> OcpCurve | None:
    if "cycle" not in df.columns or "voltage" not in df.columns:
        return None
    g = df[(df["cycle"] == int(cycle))]
    if "step_type" in g.columns:
        g = g[g["step_type"].astype(str).str.lower() == leg.lower()]
    if g.empty or "capacity" not in g.columns:
        return None
    v = pd.to_numeric(g["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(g["capacity"], errors="coerce").to_numpy(dtype=float)
    m = np.isfinite(v) & np.isfinite(q)
    v, q = v[m], q[m]
    if len(v) < 20:
        return None
    q = q - q[0]
    order = np.argsort(q)
    q, v = q[order], v[order]
    keep = np.ones(len(q), dtype=bool)
    keep[1:] = np.diff(q) > 1e-12
    q, v = q[keep], v[keep]
    qspan = float(q.max() - q.min()) if len(q) else 0.0
    if qspan <= 0:
        return None
    qn = (q - q.min()) / qspan
    peaks = find_dqdv_peaks(v, q, max_peaks=6, config=peak_cfg or DqdvPeakConfig())
    return OcpCurve(
        electrode=electrode,
        cell_id=cell_id,
        leg=leg,
        cycle=int(cycle),
        q_norm=qn,
        voltage=v,
        q_raw_span=qspan,
        v_min=float(np.nanmin(v)),
        v_max=float(np.nanmax(v)),
        peaks=peaks,
        source_path=source_path,
    )


def load_ocp_library(
    halfcell_dir: str | Path | None = None,
    *,
    anode_prefer_cycles: tuple[int, ...] = (2, 3, 1),
    include_all_cycles: bool = True,
) -> OcpLibrary:
    """Load BOL OCP library from fixture directory (manifest-driven)."""
    root = Path(halfcell_dir) if halfcell_dir else DEFAULT_HALFCELL_DIR
    lib = OcpLibrary(meta={"root": str(root), "aged_data": False, "rate": "C/20"})
    if not root.exists():
        lib.meta["error"] = "halfcell_dir_missing"
        return lib

    manifest_path = root / "manifest.json"
    cells: list[dict[str, Any]] = []
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        cells = list(man.get("cells") or [])
        lib.meta["manifest"] = str(manifest_path)
        lib.meta["aged_data"] = bool(man.get("aged_data", False))
    else:
        # fallback glob
        for p in sorted((root / "anode_SJ1300").glob("*_raw.csv")):
            cells.append({"electrode": "anode", "cell_id": p.stem, "path": str(p)})
        for p in sorted((root / "cathode_halfcell").glob("*_raw.csv")):
            cells.append({"electrode": "cathode", "cell_id": p.stem, "path": str(p)})

    for cell in cells:
        rel = cell.get("path") or ""
        path = Path(rel)
        if not path.is_absolute():
            # manifest paths are repo-relative
            cand = ROOT / rel
            path = cand if cand.exists() else root / Path(rel).name
            if not path.exists():
                # try under halfcell dir with relative suffix
                suffix = Path(*Path(rel).parts[-2:]) if len(Path(rel).parts) >= 2 else Path(rel).name
                path = root / suffix
        if not path.exists():
            continue
        # skip LFS pointers
        head = path.read_text(encoding="utf-8", errors="ignore")[:40]
        if head.startswith("version https://git-lfs"):
            lib.meta.setdefault("lfs_pointers", []).append(str(path))
            continue
        df = _read_halfcell_csv(path)
        electrode = str(cell.get("electrode", "unknown"))
        cell_id = str(cell.get("cell_id", path.stem))
        cycles = sorted(int(c) for c in df["cycle"].dropna().unique()) if "cycle" in df.columns else [1]
        use_cycles = cycles if include_all_cycles else [c for c in anode_prefer_cycles if c in cycles] or cycles[:1]
        for cyc in use_cycles:
            for leg in ("charge", "discharge"):
                curve = _leg_curve(
                    df, cycle=cyc, leg=leg, electrode=electrode,
                    cell_id=cell_id, source_path=str(path),
                )
                if curve is None:
                    continue
                if electrode == "anode":
                    lib.anode.append(curve)
                elif electrode == "cathode":
                    lib.cathode.append(curve)

    lib.meta["n_anode_curves"] = len(lib.anode)
    lib.meta["n_cathode_curves"] = len(lib.cathode)
    return lib


def synthesize_fullcell_ocp(
    library: OcpLibrary,
    *,
    anode_cycle: int = 2,
    cathode_leg: str = "charge",
    anode_leg: str = "charge",
    n_grid: int = 200,
) -> dict[str, Any] | None:
    """Rough BOL full-cell OCP: V_PE(Qn) - V_NE(Qn) on shared Q-norm.

    Capacity scales differ across fixtures — only shape is usable.
    """
    pe = next((c for c in library.cathode if c.leg == cathode_leg), None)
    ne = next(
        (c for c in library.anode if c.leg == anode_leg and c.cycle == anode_cycle),
        None,
    )
    if ne is None:
        ne = next((c for c in library.anode if c.leg == anode_leg), None)
    if pe is None or ne is None:
        return None
    grid = np.linspace(0.02, 0.98, n_grid)
    v_pe = np.interp(grid, pe.q_norm, pe.voltage)
    v_ne = np.interp(grid, ne.q_norm, ne.voltage)
    v_fc = v_pe - v_ne
    return {
        "q_norm": grid,
        "voltage": v_fc,
        "v_min": float(np.nanmin(v_fc)),
        "v_max": float(np.nanmax(v_fc)),
        "anode_cycle": ne.cycle,
        "cathode_source": pe.cell_id,
        "anode_source": ne.cell_id,
        "note": "Q-normalized shape only; absolute Ah not comparable across coin/pouch fixtures",
    }
