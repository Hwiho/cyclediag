"""RPT / capacheck (0.33C) anchored peak assign for routine (0.5C) cycles.

Uses low-rate RPT peaks as local identity anchors. Within ±hard_radius life
cycles of each checkpoint, peaks are assigned with high confidence. Between
checkpoints, expected voltages are interpolated and C-rate shifts applied.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cyclediag.features.dqdv_peaks import (
    DqdvPeakConfig,
    charge_discharge_bands,
    find_dqdv_peaks_banded_prepared,
    find_dqdv_peaks_prepared,
    prepare_dqdv_arrays,
    _smooth,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv
from cyclediag.features.peak_assign import (
    PeakAssignConfig,
    hungarian_assign_peaks,
)
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import ProtocolExclusion, preceding_capa_full_cycles


@dataclass
class RptAnchorConfig:
  hard_radius: int = 10
  soft_radius: int = 30
  routine_shift_window: int = 5
  min_band_height_frac_rpt: float = 0.08
  min_band_height_frac_routine: float = 0.12
  sg_window_rpt: int = 21
  sg_window_routine: int = 31
  match_max_cost: float = 0.15
  v_window_min_v: float = 0.04
  v_window_max_v: float = 0.08
  # When Hungarian leaves peaks missing (merged 0.5C bump), sample local max
  # in exclusive sub-windows around each V_expected (from RPT spacing).
  enable_window_split: bool = True
  split_half_width_v: float = 0.06
  split_min_height_frac: float = 0.05
  split_prefer_local_extremum: bool = True


@dataclass
class RptPeakRef:
  peak_id: str
  V: float
  H: float
  leg: str


@dataclass
class RptCheckpoint:
  life_cycle: int
  anchor_raw_cycle: int
  anchor_raw_cycles: list[int]
  peaks: dict[str, list[RptPeakRef]] = field(default_factory=dict)


@dataclass
class RateShift:
  life_cycle: int
  leg: str
  peak_id: str
  delta_v_mV: float
  n_pairs: int = 0


def infer_checkpoint_life(block_start: int) -> int:
  """Map RPT block start raw cycle to routine life milestone (100, 200, …)."""
  if block_start <= 10:
    return 1
  return max(100, ((block_start - 1) // 100) * 100)


def discover_rpt_checkpoints(protocol: ProtocolExclusion) -> list[RptCheckpoint]:
  """Build checkpoint list from protocol RPT blocks.

  Prefer the 0.33C full-capacity cycles immediately before each DC-IR/RPT
  block (e.g. TC107–108 before TC109–111). Fall back to in-block capacheck /
  the RPT block itself when no preceding capa_full pair exists.
  """
  if not protocol.rpt_blocks:
    return []

  checkpoints: list[RptCheckpoint] = []
  seen_life: set[int] = set()

  for block in protocol.rpt_blocks:
    if len(block) < 1:
      continue
    pre_capa = preceding_capa_full_cycles(protocol.flags, block[0])
    cap_in_block = sorted(c for c in block if c in protocol.capacheck_cycles)
    anchor_cycles = pre_capa or cap_in_block or list(block)
    anchor_raw = int(np.median(anchor_cycles))
    life = infer_checkpoint_life(block[0])
    if life in seen_life:
      continue
    seen_life.add(life)
    checkpoints.append(
      RptCheckpoint(
        life_cycle=life,
        anchor_raw_cycle=anchor_raw,
        anchor_raw_cycles=anchor_cycles,
      )
    )

  return sorted(checkpoints, key=lambda c: c.life_cycle)


def _capacity_col(seg: pd.DataFrame, leg: str) -> str | None:
  col = "charge_capacity" if leg == "charge" else "discharge_capacity"
  if col in seg.columns:
    return col
  return "capacity" if "capacity" in seg.columns else None


def _extract_leg_peaks(
  df: pd.DataFrame,
  cycle: int,
  leg: str,
  *,
  config: RptAnchorConfig,
  for_rpt: bool,
) -> list[dict]:
  cyc = df[df["cycle"] == cycle]
  if cyc.empty:
    return []
  seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
  seg = prepare_leg_segment_for_dqdv(seg, leg)
  col = _capacity_col(seg, leg)
  if seg.empty or col is None or "voltage" not in seg.columns:
    return []

  v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
  q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
  sg = config.sg_window_rpt if for_rpt else config.sg_window_routine
  dqcfg = DqdvPeakConfig(sg_window=sg)
  vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
  if len(vx) < 5:
    return []
  y_smooth = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)
  bands = charge_discharge_bands(leg)
  frac = config.min_band_height_frac_rpt if for_rpt else config.min_band_height_frac_routine
  peaks = find_dqdv_peaks_banded_prepared(vx, y_smooth, bands, min_band_height_frac=frac)
  for pk in peaks:
    pk["peak_id"] = pk.get("band", "")
  return peaks


def extract_rpt_anchors(
  df: pd.DataFrame,
  checkpoints: list[RptCheckpoint],
  *,
  config: RptAnchorConfig | None = None,
  legs: tuple[str, ...] = ("charge", "discharge"),
) -> list[RptCheckpoint]:
  """Fill peak references from 0.33C capacheck cycles at each checkpoint."""
  config = config or RptAnchorConfig()
  filled: list[RptCheckpoint] = []

  for ckpt in checkpoints:
    peaks_by_leg: dict[str, list[RptPeakRef]] = {}
    for leg in legs:
      merged: dict[str, RptPeakRef] = {}
      for raw_cyc in ckpt.anchor_raw_cycles:
        for pk in _extract_leg_peaks(df, raw_cyc, leg, config=config, for_rpt=True):
          pid = str(pk.get("peak_id", pk.get("band", "")))
          if not pid:
            continue
          ref = RptPeakRef(peak_id=pid, V=float(pk["V"]), H=float(pk["H"]), leg=leg)
          if pid not in merged:
            merged[pid] = ref
          else:
            merged[pid].V = float(np.mean([merged[pid].V, ref.V]))
            merged[pid].H = float(np.mean([merged[pid].H, ref.H]))
      peaks_by_leg[leg] = sorted(merged.values(), key=lambda r: r.V)

    filled.append(
      RptCheckpoint(
        life_cycle=ckpt.life_cycle,
        anchor_raw_cycle=ckpt.anchor_raw_cycle,
        anchor_raw_cycles=ckpt.anchor_raw_cycles,
        peaks=peaks_by_leg,
      )
    )
  return filled


def _routine_cycles(flags: pd.DataFrame, excluded: set[int]) -> list[int]:
  if flags.empty:
    return []
  routine = flags[
    (~flags["cycle"].isin(excluded))
    & (flags["protocol_kind"] == "routine")
  ]
  return sorted(int(c) for c in routine["cycle"])


def estimate_rate_shifts(
  df: pd.DataFrame,
  checkpoints: list[RptCheckpoint],
  routine_cycles: list[int],
  *,
  config: RptAnchorConfig | None = None,
) -> list[RateShift]:
  """ΔV = V_routine − V_rpt for cycles just before each RPT checkpoint."""
  config = config or RptAnchorConfig()
  shifts: list[RateShift] = []

  for ckpt in checkpoints:
    if not ckpt.peaks:
      continue
    lo = ckpt.life_cycle - config.routine_shift_window
    hi = ckpt.life_cycle
    window = [c for c in routine_cycles if lo <= c <= hi]
    if not window:
      continue

    for leg, refs in ckpt.peaks.items():
      for ref in refs:
        deltas: list[float] = []
        for rc in window:
          obs = _extract_leg_peaks(df, rc, leg, config=config, for_rpt=False)
          match = min(
            (pk for pk in obs if str(pk.get("peak_id", pk.get("band", ""))) == ref.peak_id),
            key=lambda p: abs(float(p["V"]) - ref.V),
            default=None,
          )
          if match is None:
            near = min(obs, key=lambda p: abs(float(p["V"]) - ref.V), default=None)
            if near is not None and abs(float(near["V"]) - ref.V) < 0.08:
              deltas.append(float(near["V"]) - ref.V)
          else:
            deltas.append(float(match["V"]) - ref.V)
        if deltas:
          shifts.append(
            RateShift(
              life_cycle=ckpt.life_cycle,
              leg=leg,
              peak_id=ref.peak_id,
              delta_v_mV=float(np.median(deltas) * 1000.0),
              n_pairs=len(deltas),
            )
          )
  return shifts


def _shift_lookup(shifts: list[RateShift], life_cycle: int, leg: str, peak_id: str) -> float:
  same = [s for s in shifts if s.life_cycle == life_cycle and s.leg == leg and s.peak_id == peak_id]
  if same:
    return same[0].delta_v_mV / 1000.0
  leg_shifts = [s for s in shifts if s.leg == leg and s.peak_id == peak_id]
  if leg_shifts:
    nearest = min(leg_shifts, key=lambda s: abs(s.life_cycle - life_cycle))
    return nearest.delta_v_mV / 1000.0
  return 0.0


def _bracket_checkpoints(
  checkpoints: list[RptCheckpoint],
  life_cycle: int,
) -> tuple[RptCheckpoint | None, RptCheckpoint | None]:
  if not checkpoints:
    return None, None
  left = None
  right = None
  for ckpt in checkpoints:
    if ckpt.life_cycle <= life_cycle:
      left = ckpt
    if ckpt.life_cycle >= life_cycle and right is None:
      right = ckpt
  if left is None:
    left = checkpoints[0]
  if right is None:
    right = checkpoints[-1]
  return left, right


def interpolate_expected_v(
  checkpoints: list[RptCheckpoint],
  life_cycle: int,
  leg: str,
  peak_id: str,
  shifts: list[RateShift],
) -> tuple[float, int, int, str]:
  """Return (V_expected_0.5C, anchor_left, anchor_right, zone)."""
  left, right = _bracket_checkpoints(checkpoints, life_cycle)
  if left is None or right is None:
    return np.nan, -1, -1, "unknown"

  def _v_at(ckpt: RptCheckpoint) -> float | None:
    for ref in ckpt.peaks.get(leg, []):
      if ref.peak_id == peak_id:
        return ref.V + _shift_lookup(shifts, ckpt.life_cycle, leg, peak_id)
    return None

  v_left = _v_at(left)
  v_right = _v_at(right)
  if v_left is None and v_right is None:
    return np.nan, left.life_cycle, right.life_cycle, "unknown"
  if left.life_cycle == right.life_cycle or v_right is None:
    v = v_left if v_left is not None else v_right
    zone = _zone(life_cycle, left.life_cycle, right.life_cycle)
    return float(v), left.life_cycle, right.life_cycle, zone
  if v_left is None:
    zone = _zone(life_cycle, left.life_cycle, right.life_cycle)
    return float(v_right), left.life_cycle, right.life_cycle, zone

  w = (life_cycle - left.life_cycle) / max(right.life_cycle - left.life_cycle, 1)
  v = (1.0 - w) * v_left + w * float(v_right)
  zone = _zone(life_cycle, left.life_cycle, right.life_cycle)
  return float(v), left.life_cycle, right.life_cycle, zone


def _zone(life_cycle: int, left_life: int, right_life: int, config: RptAnchorConfig | None = None) -> str:
  config = config or RptAnchorConfig()
  dist_left = abs(life_cycle - left_life)
  dist_right = abs(life_cycle - right_life)
  dist = min(dist_left, dist_right)
  if dist <= config.hard_radius:
    return "hard"
  if dist <= config.soft_radius:
    return "soft"
  return "interpolated"


def _refs_from_expected(
  checkpoints: list[RptCheckpoint],
  life_cycle: int,
  leg: str,
  shifts: list[RateShift],
  config: RptAnchorConfig,
) -> pd.DataFrame:
  left, right = _bracket_checkpoints(checkpoints, life_cycle)
  peak_ids: set[str] = set()
  if left:
    peak_ids.update(r.peak_id for r in left.peaks.get(leg, []))
  if right:
    peak_ids.update(r.peak_id for r in right.peaks.get(leg, []))

  rows: list[dict] = []
  for pid in sorted(peak_ids):
    v_exp, a_left, a_right, zone = interpolate_expected_v(
      checkpoints, life_cycle, leg, pid, shifts,
    )
    if not np.isfinite(v_exp):
      continue
    half = config.v_window_min_v
    rows.append({
      "leg": leg,
      "peak_id": pid,
      "V": v_exp,
      "H_abs": 50.0,
      "v_lo": v_exp - half,
      "v_hi": v_exp + half,
    })
  return pd.DataFrame(rows)


def _evidence_type(
  match_cost: float,
  zone: str,
  n_candidates: int,
  n_expected: int,
  *,
  method: str = "rpt_anchor",
) -> str:
  if not np.isfinite(match_cost) and method != "rpt_window_split":
    return "missing"
  if method == "rpt_window_split":
    return "inferred_split"
  if match_cost > 0.12:
    return "inferred_split"
  if zone == "hard" and n_candidates >= n_expected:
    return "observed"
  if zone == "hard":
    return "shoulder"
  if zone == "soft":
    return "shoulder"
  return "inferred_split"


def _exclusive_windows_from_expected(
  v_expected: list[tuple[str, float]],
  *,
  half_width: float,
) -> dict[str, tuple[float, float]]:
  """Build non-overlapping voltage windows from sorted expected peak voltages.

  Adjacent peaks split at the midpoint so P2/P3 do not share the same local max
  when the 0.5C bump is merged.
  """
  ordered = sorted(((pid, float(v)) for pid, v in v_expected if np.isfinite(v)), key=lambda t: t[1])
  windows: dict[str, tuple[float, float]] = {}
  for i, (pid, v) in enumerate(ordered):
    lo = v - half_width
    hi = v + half_width
    if i > 0:
      mid = 0.5 * (ordered[i - 1][1] + v)
      lo = max(lo, mid)
    if i + 1 < len(ordered):
      mid = 0.5 * (v + ordered[i + 1][1])
      hi = min(hi, mid)
    if hi > lo + 0.005:
      windows[pid] = (lo, hi)
  return windows


def _local_max_in_window(
  vx: np.ndarray,
  y_smooth: np.ndarray,
  v_lo: float,
  v_hi: float,
  *,
  min_height: float = 0.0,
  prefer_extremum: bool = True,
) -> dict | None:
  """Return local |dQ/dV| maximum inside [v_lo, v_hi], optionally at a true extremum."""
  mask = (vx >= v_lo) & (vx <= v_hi) & np.isfinite(vx) & np.isfinite(y_smooth)
  if not mask.any():
    return None
  idx = np.flatnonzero(mask)
  y_abs = np.abs(y_smooth[idx])
  global_max = float(np.nanmax(np.abs(y_smooth))) if len(y_smooth) else 0.0
  floor = max(min_height, global_max * 0.0)

  if prefer_extremum and len(idx) >= 3:
    # Prefer points that are local maxima of |y| inside the window
    local_i: list[int] = []
    for k in range(1, len(idx) - 1):
      if y_abs[k] >= y_abs[k - 1] and y_abs[k] >= y_abs[k + 1] and y_abs[k] > floor:
        local_i.append(k)
    if local_i:
      best_k = max(local_i, key=lambda k: y_abs[k])
      i = int(idx[best_k])
      return {"V": float(vx[i]), "H": float(y_smooth[i]), "from_split": True}

  best_k = int(np.argmax(y_abs))
  if y_abs[best_k] < floor or (global_max > 0 and y_abs[best_k] < global_max * 0.02):
    # Still accept weak shoulder if above absolute floor
    if y_abs[best_k] < max(floor, 1e-6):
      return None
  i = int(idx[best_k])
  return {"V": float(vx[i]), "H": float(y_smooth[i]), "from_split": True}


def fill_missing_with_window_split(
  assigned_by_id: dict[str, dict],
  refs: pd.DataFrame,
  vx: np.ndarray,
  y_smooth: np.ndarray,
  *,
  config: RptAnchorConfig,
) -> dict[str, dict]:
  """Fill missing peak_ids by local max in RPT-spacing sub-windows."""
  if not config.enable_window_split or refs.empty:
    return assigned_by_id

  expected = [
    (str(r.peak_id), float(r.V))
    for r in refs.itertuples()
    if np.isfinite(float(r.V))
  ]
  windows = _exclusive_windows_from_expected(expected, half_width=config.split_half_width_v)
  global_max = float(np.nanmax(np.abs(y_smooth))) if len(y_smooth) else 0.0
  min_h = config.split_min_height_frac * global_max if global_max > 0 else 0.0

  filled = dict(assigned_by_id)
  for pid, (v_lo, v_hi) in windows.items():
    if pid in filled:
      continue
    pk = _local_max_in_window(
      vx, y_smooth, v_lo, v_hi,
      min_height=min_h,
      prefer_extremum=config.split_prefer_local_extremum,
    )
    if pk is None:
      continue
    v_exp = float(refs.loc[refs["peak_id"] == pid, "V"].iloc[0])
    cost = abs(float(pk["V"]) - v_exp)
    pk.update({
      "peak_id": pid,
      "band": pid,
      "assign_method": "rpt_window_split",
      "match_cost": cost,
      "band_v_min": v_lo,
      "band_v_max": v_hi,
    })
    filled[pid] = pk
  return filled


def assign_routine_cycle(
  df: pd.DataFrame,
  cycle: int,
  checkpoints: list[RptCheckpoint],
  shifts: list[RateShift],
  *,
  config: RptAnchorConfig | None = None,
  legs: tuple[str, ...] = ("charge", "discharge"),
) -> list[dict]:
  """Assign peaks for one routine cycle using RPT anchors."""
  config = config or RptAnchorConfig()
  life_cycle = int(cycle)
  rows: list[dict] = []
  left_ck, right_ck = _bracket_checkpoints(checkpoints, life_cycle)
  zone = _zone(
    life_cycle,
    left_ck.life_cycle if left_ck else 0,
    right_ck.life_cycle if right_ck else 0,
    config,
  )

  for leg in legs:
    refs = _refs_from_expected(checkpoints, life_cycle, leg, shifts, config)
    if refs.empty:
      continue

    cyc = df[df["cycle"] == cycle]
    seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
    seg = prepare_leg_segment_for_dqdv(seg, leg)
    col = _capacity_col(seg, leg)
    if seg.empty or col is None:
      continue
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
    dqcfg = DqdvPeakConfig(sg_window=config.sg_window_routine)
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
    if len(vx) < 5:
      continue
    y_smooth = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)
    candidates = find_dqdv_peaks_prepared(vx, dqdv, y_smooth, max_peaks=12, config=dqcfg)

    assign_cfg = PeakAssignConfig(max_match_cost=config.match_max_cost)
    assigned = hungarian_assign_peaks(
      candidates, refs, leg=leg, config=assign_cfg,
    )
    assigned_by_id = {
      str(a.get("peak_id", a.get("band", ""))): a for a in assigned
    }
    assigned_by_id = fill_missing_with_window_split(
      assigned_by_id, refs, vx, y_smooth, config=config,
    )

    for ref_row in refs.itertuples():
      pid = str(ref_row.peak_id)
      v_exp, a_left, a_right, _ = interpolate_expected_v(
        checkpoints, life_cycle, leg, pid, shifts,
      )
      match = assigned_by_id.get(pid)
      if match:
        cost = float(match.get("match_cost", np.nan))
        method = str(match.get("assign_method", "rpt_anchor"))
        evidence = _evidence_type(
          cost, zone, len(candidates), len(refs), method=method,
        )
        conf = float(1.0 - min(1.0, cost / config.match_max_cost)) if np.isfinite(cost) else 0.3
        if method == "rpt_window_split":
          conf = max(0.25, min(0.75, conf))
          if zone == "hard":
            conf = min(0.85, conf + 0.1)
        elif zone == "hard":
          conf = min(1.0, conf + 0.15)
        elif zone == "interpolated":
          conf = max(0.2, conf - 0.15)
        v_obs = float(match["V"])
        h_obs = float(match["H"])
      else:
        cost = np.nan
        evidence = "missing"
        conf = 0.0
        v_obs = np.nan
        h_obs = np.nan
        method = "rpt_anchor"

      rows.append({
        "cycle": cycle,
        "life_cycle": life_cycle,
        "leg": leg,
        "peak_id": pid,
        "V_expected": v_exp,
        "V_observed": v_obs,
        "H_observed": h_obs,
        "anchor_left": a_left,
        "anchor_right": a_right,
        "distance_to_rpt": min(abs(life_cycle - a_left), abs(life_cycle - a_right)),
        "rate_shift_mV": _shift_lookup(shifts, life_cycle, leg, pid) * 1000.0,
        "assign_zone": zone,
        "assign_method": method if match else "rpt_anchor",
        "assign_confidence": conf,
        "match_cost": cost,
        "evidence_type": evidence,
        "n_candidates": len(candidates),
      })

    expected_ids = {str(r.peak_id) for r in refs.itertuples()}
    for pid, pk in assigned_by_id.items():
      if pid not in expected_ids:
        rows.append({
          "cycle": cycle,
          "life_cycle": life_cycle,
          "leg": leg,
          "peak_id": pid,
          "V_expected": np.nan,
          "V_observed": float(pk["V"]),
          "H_observed": float(pk["H"]),
          "anchor_left": left_ck.life_cycle if left_ck else -1,
          "anchor_right": right_ck.life_cycle if right_ck else -1,
          "distance_to_rpt": np.nan,
          "rate_shift_mV": np.nan,
          "assign_zone": zone,
          "assign_method": "rpt_anchor_extra",
          "assign_confidence": 0.4,
          "match_cost": float(pk.get("match_cost", np.nan)),
          "evidence_type": "observed",
          "n_candidates": len(candidates),
        })

  return rows


def build_rpt_anchor_assign_table(
  df: pd.DataFrame,
  protocol: ProtocolExclusion,
  *,
  config: RptAnchorConfig | None = None,
  checkpoints: list[RptCheckpoint] | None = None,
) -> tuple[pd.DataFrame, list[RptCheckpoint], list[RateShift], dict[str, Any]]:
  """Full pipeline: discover anchors → rate shift → assign all routine cycles."""
  config = config or RptAnchorConfig()
  ckpts = checkpoints or discover_rpt_checkpoints(protocol)
  ckpts = extract_rpt_anchors(df, ckpts, config=config)
  routine = _routine_cycles(protocol.flags, protocol.excluded)
  shifts = estimate_rate_shifts(df, ckpts, routine, config=config)

  all_rows: list[dict] = []
  for cyc in routine:
    all_rows.extend(
      assign_routine_cycle(df, cyc, ckpts, shifts, config=config),
    )

  meta = {
    "n_checkpoints": len(ckpts),
    "checkpoints": [
      {
        "life_cycle": c.life_cycle,
        "anchor_raw_cycle": c.anchor_raw_cycle,
        "anchor_raw_cycles": c.anchor_raw_cycles,
        "n_peaks_charge": len(c.peaks.get("charge", [])),
        "n_peaks_discharge": len(c.peaks.get("discharge", [])),
      }
      for c in ckpts
    ],
    "n_rate_shifts": len(shifts),
    "n_routine_cycles": len(routine),
    "config": asdict(config),
  }
  return pd.DataFrame(all_rows), ckpts, shifts, meta


def save_rpt_anchor_artifacts(
  out_dir: Path,
  cell_id: str,
  assign_df: pd.DataFrame,
  checkpoints: list[RptCheckpoint],
  shifts: list[RateShift],
  meta: dict[str, Any],
) -> dict[str, Path]:
  out_dir.mkdir(parents=True, exist_ok=True)
  paths: dict[str, Path] = {}

  assign_path = out_dir / f"{cell_id}_rpt_anchor_assign.csv"
  assign_df.to_csv(assign_path, index=False, encoding="utf-8-sig")
  paths["assign"] = assign_path

  anchor_rows: list[dict] = []
  for ckpt in checkpoints:
    for leg, refs in ckpt.peaks.items():
      for ref in refs:
        anchor_rows.append({
          "life_cycle": ckpt.life_cycle,
          "anchor_raw_cycle": ckpt.anchor_raw_cycle,
          "leg": leg,
          "peak_id": ref.peak_id,
          "V_rpt": ref.V,
          "H_rpt": ref.H,
        })
  anchor_path = out_dir / f"{cell_id}_rpt_anchors.csv"
  pd.DataFrame(anchor_rows).to_csv(anchor_path, index=False, encoding="utf-8-sig")
  paths["anchors"] = anchor_path

  shift_path = out_dir / f"{cell_id}_rpt_rate_shifts.csv"
  pd.DataFrame([asdict(s) for s in shifts]).to_csv(shift_path, index=False, encoding="utf-8-sig")
  paths["rate_shifts"] = shift_path

  meta_path = out_dir / f"{cell_id}_rpt_anchor_meta.json"
  meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
  paths["meta"] = meta_path
  return paths
