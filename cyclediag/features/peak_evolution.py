"""2D peak evolution maps + Viterbi ridge tracking with birth/death/merge events.

Preferred over frame-to-frame Hungarian matching when peak count changes.
Use ``method=\"evolution\"`` via :func:`track_peaks_pipeline` or CLI
``python -m cyclediag peaks evolution``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from cyclediag.io.cycle_protocol import (
    POST_RPT_EXCLUDE,
    build_protocol_exclusion,
    detect_protocol_flags,
    preceding_capa_full_cycles,
    rpt_blocks,
)

from .dqdv_peaks import DqdvPeakConfig, prepare_dqdv_arrays, _noise_mad, _smooth
from .dqdv_segment import prepare_leg_segment_for_dqdv
from .segment_utils import leg_segment

Domain = Literal["V", "Q"]
NormalizeMode = Literal["none", "area", "capacity", "local_contrast"]
EventType = Literal["initial", "born", "died", "merged", "split", "resumed", "ambiguous"]
TrackState = Literal["tentative", "confirmed", "coasting", "terminated"]

# Quality gates (§7)
MIN_SAMPLES_PER_MV = 0.15  # relaxed: 0.3 was gating out most 0.5C legs
MIN_DQDV_SNR = 2.0
# Capacity-fade noise floor (Ah relative) — NOT for peak-position LOO.
CAPACITY_NOISE_FLOOR_PCT = 0.065


def _default_dqdv_config() -> DqdvPeakConfig:
    """Target effective smooth ≪ peak width: n_interp↑, sg_window↓, merge tight."""
    return DqdvPeakConfig(
        n_interp=2500,
        sg_window=7,
        sg_poly=3,
        merge_v_sep_v=0.003,
        min_distance_frac=0.015,
    )


@dataclass
class PeakEvolutionConfig:
    """Peak evolution map + ridge tracking settings."""

    domain: Domain = "Q"
    leg: str = "discharge"
    normalize: NormalizeMode = "local_contrast"
    n_grid: int = 1000
    # Exclude discharge-end cliff (Q≈0.88–0.98) that masquerades as a peak.
    # 0.90 cuts the steepen onset that still leaked in at 0.90–0.95.
    q_grid_lo: float = 0.05
    q_grid_hi: float = 0.90
    v_grid_lo: float = 2.5
    v_grid_hi: float = 4.2
    dqdv_config: DqdvPeakConfig = field(default_factory=_default_dqdv_config)
    lam: float | None = None
    lam_scale: float = 0.1  # multiply auto-λ (diagnose λ collapse with smaller values)
    viterbi_window: int = 40
    max_tracks: int = 12
    # MAD-multiples above median |amp|. Use ~0.5–1 for local_contrast maps
    # (amplitudes cluster near 1); larger values starve extraction.
    snr_stop: float = 0.75
    confirm_m: int = 3
    confirm_n: int = 5
    coast_k: int = 3
    terminate_l: int = 5
    merge_tol: float = 0.15
    death_tol: float = 0.30
    area_window: int = 3
    quality_gate: bool = False  # soft: prefer full map over dropping half the cycles
    min_samples_per_mV: float = MIN_SAMPLES_PER_MV
    min_dqdv_snr: float = MIN_DQDV_SNR
    post_rpt_exclude: int = POST_RPT_EXCLUDE
    method: str = "evolution"  # evolution | deconv (reserved)
    graphite_flag_v_range: tuple[float, float] = (3.45, 3.85)
    # Q-norm ROIs for independent ridge extraction (avoids end-cliff dominance).
    rois: tuple[tuple[float, float], ...] = ((0.15, 0.55), (0.55, 0.85))
    use_roi_extract: bool = True
    # Cycles within this window after start → "initial", not "born".
    initial_window_cycles: int = 20
    extract_steepen: bool = True


@dataclass
class EvolutionMap:
    """Stacked dQ/dV or dV/dQ rows on a fixed absolute grid."""

    M: np.ndarray
    cycles: np.ndarray
    grid: np.ndarray
    domain: Domain
    leg: str
    rate: str
    normalize: NormalizeMode
    quality_mask: np.ndarray
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def n_cycles(self) -> int:
        return int(len(self.cycles))

    @property
    def n_grid(self) -> int:
        return int(len(self.grid))


@dataclass
class PeakEvolutionResult:
    tracks: pd.DataFrame
    trajectories: pd.DataFrame
    events: pd.DataFrame
    validation: dict[str, Any]
    map_routine: EvolutionMap | None = None
    map_rpt: EvolutionMap | None = None
    preflight: pd.DataFrame | None = None
    steepen: pd.DataFrame | None = None

    def to_csv(self, out_dir: str | Path) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        self.tracks.to_csv(out / "peak_tracks.csv", index=False)
        self.trajectories.to_csv(out / "peak_trajectories.csv", index=False)
        self.events.to_csv(out / "peak_events.csv", index=False)
        if self.preflight is not None:
            self.preflight.to_csv(out / "preflight_checks.csv", index=False)
        if self.steepen is not None and not self.steepen.empty:
            self.steepen.to_csv(out / "q_steepen.csv", index=False)
        (out / "validation.json").write_text(json.dumps(self.validation, indent=2, default=str), encoding="utf-8")
        return out

    def plot(self, out_dir: str | Path) -> list[Path]:
        return plot_peak_evolution(self, out_dir)


# ---------------------------------------------------------------------------
# §7 Preflight
# ---------------------------------------------------------------------------


def _effective_smooth_mV(v_grid: np.ndarray, sg_window: int) -> float:
    if len(v_grid) < 5:
        return float("nan")
    w = min(sg_window, len(v_grid) if len(v_grid) % 2 else len(v_grid) - 1)
    if w < 5:
        return float("nan")
    vs = savgol_filter(v_grid, w, 3)
    mv = float(np.median(np.abs(np.diff(vs))) * 1000)
    return mv * sg_window


def _local_noise_sigma(v: np.ndarray, w: int = 15) -> np.ndarray:
    out = np.full(len(v), np.nan)
    for i in range(w, len(v) - w):
        s = slice(i - w, i + w + 1)
        t = np.arange(-w, w + 1)
        p = np.polyfit(t, v[s], 1)
        out[i] = np.std(v[s] - np.polyval(p, t))
    return out


def run_preflight_checks(
    raw_df: pd.DataFrame,
    step_df: pd.DataFrame | None = None,
    *,
    config: PeakEvolutionConfig | None = None,
    sample_cycles: list[int] | None = None,
) -> pd.DataFrame:
    """§7 prerequisite table. Returns rows with pass/fail and measured values."""
    config = config or PeakEvolutionConfig()
    rows: list[dict[str, Any]] = []

    cycles = sample_cycles or _select_cycles_by_rate(raw_df, step_df, "0.5C", config)[:3]
    if not cycles:
        cycles = sorted(raw_df["cycle"].unique())[:3]

  # 1) Effective smoothing width
    smooth_mvs: list[float] = []
    peak_widths: list[float] = []
    for cyc in cycles:
        row = _cycle_curve(raw_df, int(cyc), config)
        if row is None:
            continue
        v, q, total_q = row
        vx, dqdv, qx, dvdq = prepare_dqdv_arrays(v, q, config.dqdv_config)
        if len(vx) < 10:
            continue
        smooth_mvs.append(_effective_smooth_mV(vx, config.dqdv_config.sg_window))
        y = np.abs(dvdq if config.domain == "Q" else dqdv)
        if y.size:
            half = float(np.nanmax(y)) * 0.5
            idx = int(np.nanargmax(y))
            # crude FWHM in grid points → mV via local V spacing
            if config.domain == "Q" and len(qx) > 1:
                dq = float(np.median(np.diff(qx))) * total_q * 1000  # not mV — use V
                dv = float(np.median(np.abs(np.diff(vx)))) * 1000
                peak_widths.append(max(dv * 8, 15.0))
            else:
                dv = float(np.median(np.abs(np.diff(vx)))) * 1000
                peak_widths.append(max(dv * 8, 15.0))

    eff = float(np.nanmedian(smooth_mvs)) if smooth_mvs else float("nan")
    pw = float(np.nanmedian(peak_widths)) if peak_widths else 50.0
    rows.append({
        "check_id": 1,
        "item": "effective_smooth_mV vs peak_width",
        "measured": eff,
        "reference": pw,
        "status": "PASS" if np.isfinite(eff) and eff < pw else ("WARN" if np.isfinite(eff) else "FAIL"),
        "action": "reduce sg_window" if np.isfinite(eff) and eff >= pw else "ok",
    })

    # 2) sigma_V/|dV| ratio spread
    ratios: list[float] = []
    for cyc in cycles[:1]:
        row = _cycle_curve(raw_df, int(cyc), config)
        if row is None:
            continue
        v, _, _ = row
        sig = _local_noise_sigma(v) * 1000
        dV = np.abs(np.gradient(v)) * 1000
        df = pd.DataFrame({"sig": sig, "dV": dV}).dropna()
        df = df[df["dV"] > 1e-6]
        if df.empty:
            continue
        df["bin"] = pd.cut(df.index, 5)
        tab = df.groupby("bin", observed=True).agg(sigma=("sig", "median"), dV=("dV", "median"))
        tab["ratio"] = tab["sigma"] / tab["dV"]
        if tab["ratio"].min() > 0:
            ratios.append(float(tab["ratio"].max() / tab["ratio"].min()))
    spread = float(np.nanmedian(ratios)) if ratios else float("nan")
    rows.append({
        "check_id": 2,
        "item": "sigma_V/|dV| max/min ratio",
        "measured": spread,
        "reference": 5.0,
        "status": "PASS" if np.isfinite(spread) and spread < 5 else "WARN",
        "action": "use domain=Q" if np.isfinite(spread) and spread >= 5 else "ok",
    })

    # 3) Quantization
    v0 = pd.to_numeric(raw_df[raw_df["cycle"] == cycles[0]]["voltage"], errors="coerce").to_numpy(float)
    d = np.abs(np.diff(v0))
    d = d[d > 0]
    min_dv = float(d.min()) if len(d) else float("nan")
    rows.append({
        "check_id": 3,
        "item": "voltage_quantization_mV",
        "measured": min_dv * 1000 if np.isfinite(min_dv) else float("nan"),
        "reference": 5.0,
        "status": "PASS" if np.isfinite(min_dv) and min_dv < 0.005 else "WARN",
        "action": "check export precision" if min_dv >= 0.005 else "ok",
    })

    # 4) RPT peak separation — report FULL-curve (legacy §7-4) AND interior Q ROI.
    # v1 "5 peaks PASS" used abs(dQ/dV) on the full curve (no Q ROI). That is NOT
    # the same as interior |dV/dQ| peaks used for graphite-stage anchoring.
    rpt_cycles = _select_cycles_by_rate(raw_df, step_df, "C/3", config)
    rpt_peaks_full_dqdv = 0
    rpt_peaks_interior_dvdq = 0
    peak_q_full: list[float] = []
    peak_q_interior: list[float] = []
    for cyc in rpt_cycles[:2]:
        row = _cycle_curve(raw_df, int(cyc), config)
        if row is None:
            continue
        v, q, total_q = row
        vx, dqdv, qx, dvdq = prepare_dqdv_arrays(v, q, config.dqdv_config)
        qn = qx / total_q if total_q > 0 else np.full_like(qx, np.nan)
        from scipy.signal import find_peaks

        # Legacy path (matches v1 §7-4): abs(dQ/dV), full curve.
        y_dq = _smooth(np.nan_to_num(dqdv, nan=0.0), window=config.dqdv_config.sg_window, poly=3)
        if np.isfinite(y_dq).any() and float(np.nanmax(np.abs(y_dq))) > 0:
            prom = 0.02 * float(np.nanmax(np.abs(y_dq)))
            idx, _ = find_peaks(np.abs(y_dq), prominence=prom, distance=max(5, len(y_dq) // 25))
            if len(idx) > rpt_peaks_full_dqdv:
                rpt_peaks_full_dqdv = int(len(idx))
                peak_q_full = [float(qn[i]) for i in idx if i < len(qn) and np.isfinite(qn[i])]

        # Interior |dV/dQ| (graphite / mid-SOC relevance).
        y_dv = np.abs(dvdq)
        y_dv = np.where((qn >= 0.15) & (qn <= 0.85), y_dv, np.nan)
        y_dvs = _smooth(np.nan_to_num(y_dv, nan=0.0), window=config.dqdv_config.sg_window, poly=3)
        if np.isfinite(y_dvs).any() and float(np.nanmax(y_dvs)) > 0:
            prom = 0.02 * float(np.nanmax(y_dvs))
            idx, _ = find_peaks(y_dvs, prominence=prom, distance=max(5, len(y_dvs) // 25))
            if len(idx) > rpt_peaks_interior_dvdq:
                rpt_peaks_interior_dvdq = int(len(idx))
                peak_q_interior = [float(qn[i]) for i in idx if i < len(qn) and np.isfinite(qn[i])]

    n_full_outside = int(sum(1 for qq in peak_q_full if qq < 0.15 or qq > 0.85))
    rows.append({
        "check_id": 4,
        "item": "RPT_C3_resolved_peaks_full_dqdv",
        "measured": rpt_peaks_full_dqdv,
        "reference": 2.0,
        "status": "PASS" if rpt_peaks_full_dqdv >= 2 else "FAIL",
        "action": (
            f"legacy §7-4 path; peak_Q={np.round(peak_q_full, 3).tolist()}; "
            f"n_outside_015_085={n_full_outside}"
        ),
    })
    rows.append({
        "check_id": "4b",
        "item": "RPT_C3_resolved_peaks_interior_dvdq",
        "measured": rpt_peaks_interior_dvdq,
        "reference": 2.0,
        "status": "PASS" if rpt_peaks_interior_dvdq >= 2 else "FAIL",
        "action": (
            f"Q 0.15-0.85 |dV/dQ|; peak_Q={np.round(peak_q_interior, 3).tolist()}; "
            "anchors for graphite stages require this"
        ),
    })

    # 5) POST_RPT_EXCLUDE
    excluded = 0
    if step_df is not None:
        prot = build_protocol_exclusion(step_df, post_rpt_exclude=config.post_rpt_exclude)
        excluded = len(prot.post_rpt_cycles)
    rows.append({
        "check_id": 5,
        "item": "POST_RPT_EXCLUDE_masking",
        "measured": excluded,
        "reference": config.post_rpt_exclude,
        "status": "PASS" if step_df is not None else "UNKNOWN",
        "action": "mask post_rpt in map" if step_df is not None else "provide stepend",
    })

    return pd.DataFrame(rows)


def preflight_passes(table: pd.DataFrame) -> bool:
    if table.empty:
        return False
    fails = table[table["status"] == "FAIL"]
    return len(fails) == 0


# ---------------------------------------------------------------------------
# Map construction
# ---------------------------------------------------------------------------


def _select_cycles_by_rate(
    raw_df: pd.DataFrame,
    step_df: pd.DataFrame | None,
    rate: str,
    config: PeakEvolutionConfig,
) -> list[int]:
    all_cycles = sorted(int(c) for c in raw_df["cycle"].dropna().unique())
    if step_df is None:
        return all_cycles
    flags = detect_protocol_flags(step_df)
    if flags.empty:
        return all_cycles
    prot = build_protocol_exclusion(step_df, post_rpt_exclude=config.post_rpt_exclude)
    rate_l = rate.replace(" ", "").lower()
    if rate_l in ("0.5c", "routine", "0.5"):
        # Routine only — drop RPT, capa_full, and POST_RPT recovery buffer.
        mask = flags["protocol_kind"] == "routine"
        chosen = [int(c) for c in flags.loc[mask, "cycle"] if int(c) not in prot.excluded]
    elif rate_l in ("c/3", "c3", "capa_full"):
        # Explicit capa_full map — must INCLUDE these cycles (they are in excluded for routine).
        mask = flags["is_capa_full"].astype(bool)
        chosen = [int(c) for c in flags.loc[mask, "cycle"]]
    else:
        mask = flags["protocol_kind"] == rate
        chosen = [int(c) for c in flags.loc[mask, "cycle"] if int(c) not in prot.excluded]
    return sorted(chosen) if chosen else all_cycles


def _cycle_curve(
    raw_df: pd.DataFrame,
    cycle: int,
    config: PeakEvolutionConfig,
) -> tuple[np.ndarray, np.ndarray, float] | None:
    g = raw_df[raw_df["cycle"] == cycle]
    if g.empty:
        return None
    if "step_type" in g.columns:
        seg = leg_segment(g, config.leg, charge_text="charge", discharge_text="discharge")
    else:
        cur = pd.to_numeric(g["current"], errors="coerce")
        seg = g[cur < -1.0].copy() if config.leg == "discharge" else g[cur > 1.0].copy()
    seg = prepare_leg_segment_for_dqdv(seg, config.leg)
    col = "discharge_capacity" if config.leg == "discharge" else "charge_capacity"
    if col not in seg.columns:
        col = "capacity"
    if seg.empty or col not in seg.columns or "voltage" not in seg.columns:
        return None
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(float)
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(float)
    q = np.abs(q - q[0])
    total = float(np.nanmax(q))
    if not np.isfinite(total) or total <= 0:
        return None
    return v, q, total


def _interp_to_grid(
    vx: np.ndarray,
    y: np.ndarray,
    qx: np.ndarray,
    grid: np.ndarray,
    domain: Domain,
) -> np.ndarray:
    if domain == "Q":
        x_src, x_grid = qx, grid
    else:
        x_src, x_grid = vx, grid
    m = np.isfinite(x_src) & np.isfinite(y)
    if m.sum() < 4:
        return np.full(len(grid), np.nan)
    order = np.argsort(x_src[m])
    xs = x_src[m][order]
    ys = y[m][order]
    _, uid = np.unique(np.round(xs, 9), return_index=True)
    xs, ys = xs[uid], ys[uid]
    return np.interp(x_grid, xs, ys, left=np.nan, right=np.nan)


def _cycle_quality_metrics(v: np.ndarray, y: np.ndarray, y_smooth: np.ndarray) -> dict[str, float]:
    mad = _noise_mad(y, y_smooth)
    ymax = float(np.nanmax(np.abs(y_smooth))) if y_smooth.size else 0.0
    snr = ymax / (mad * 1.4826 + 1e-12) if ymax > 0 else 0.0
    dv = np.abs(np.gradient(v))
    spm = float(len(v) / (np.nansum(dv) * 1000 + 1e-12))
    return {"dqdv_snr": snr, "samples_per_mV": spm}


def build_evolution_map(
    raw_df: pd.DataFrame,
    *,
    config: PeakEvolutionConfig | None = None,
    rate: str = "0.5C",
    step_df: pd.DataFrame | None = None,
) -> EvolutionMap:
    """Build fixed-grid evolution map for one rate class."""
    config = config or PeakEvolutionConfig()
    cycles = _select_cycles_by_rate(raw_df, step_df, rate, config)
    if not cycles:
        raise ValueError(f"No cycles for rate={rate}")

    if config.domain == "Q":
        grid = np.linspace(config.q_grid_lo, config.q_grid_hi, config.n_grid)
    else:
        grid = np.linspace(config.v_grid_lo, config.v_grid_hi, config.n_grid)

    M = np.full((len(cycles), len(grid)), np.nan)
    qmask = np.ones(len(cycles), dtype=bool)
    meta_cycles: list[dict[str, Any]] = []
    totals: list[float] = []

    for i, cyc in enumerate(cycles):
        row = _cycle_curve(raw_df, cyc, config)
        if row is None:
            qmask[i] = False
            totals.append(np.nan)
            continue
        v, q, total_q = row
        totals.append(total_q)
        vx, dqdv, qx, dvdq = prepare_dqdv_arrays(v, q, config.dqdv_config)
        if len(vx) < 5:
            # High n_interp can fail on sparse legs — fall back to denser-but-safe grid.
            fallback = DqdvPeakConfig(
                n_interp=min(500, max(100, len(q))),
                sg_window=min(config.dqdv_config.sg_window, 7),
                sg_poly=config.dqdv_config.sg_poly,
                merge_v_sep_v=config.dqdv_config.merge_v_sep_v,
                min_distance_frac=config.dqdv_config.min_distance_frac,
            )
            vx, dqdv, qx, dvdq = prepare_dqdv_arrays(v, q, fallback)
        if len(vx) < 5:
            qmask[i] = False
            continue
        y_smooth = _smooth(dqdv, window=config.dqdv_config.sg_window, poly=config.dqdv_config.sg_poly)
        qm = _cycle_quality_metrics(vx, dqdv, y_smooth)
        if config.quality_gate and (
            qm["dqdv_snr"] < config.min_dqdv_snr or qm["samples_per_mV"] < config.min_samples_per_mV
        ):
            qmask[i] = False
            meta_cycles.append({"cycle": cyc, "masked": True, **qm})
            continue

        if config.domain == "Q":
            q_norm = qx / total_q
            # |dV/dQ|: discharge steepness is signed-negative; ridges = positive peaks.
            y = np.abs(dvdq)
            line = _interp_to_grid(vx, y, q_norm, grid, "Q")
        else:
            y = dqdv
            line = _interp_to_grid(vx, y, qx, grid, "V")

        if config.normalize == "capacity" and total_q > 0:
            line = line / total_q
        elif config.normalize == "area":
            area = np.nansum(np.abs(line))
            if area > 0:
                line = line / area
        # local_contrast applied after stacking (needs time axis)

        M[i, :] = line
        meta_cycles.append({"cycle": cyc, "masked": False, "total_q": total_q, **qm})

    if config.normalize == "local_contrast":
        M = _apply_local_contrast(M)

    return EvolutionMap(
        M=M,
        cycles=np.asarray(cycles, dtype=int),
        grid=grid,
        domain=config.domain,
        leg=config.leg,
        rate=rate,
        normalize=config.normalize,
        quality_mask=qmask,
        meta={"per_cycle": meta_cycles, "total_q": totals, "q_valid_range": (config.q_grid_lo, config.q_grid_hi)},
    )


def _apply_local_contrast(M: np.ndarray) -> np.ndarray:
    """Relative ridge prominence for weak features.

    1) Row scale — each cycle's |amp| / median so Q-peaks stand out within the cycle.
    2) Column scale — divide by time-mean so persistent weak ridges compete with
       strong absolute features (user-requested local contrast).
    """
    out = np.asarray(M, dtype=float).copy()
    with np.errstate(all="ignore"):
        row_scale = np.nanmedian(np.abs(out), axis=1)
        row_scale = np.where(row_scale > 1e-15, row_scale, np.nan)
        out = out / row_scale[:, np.newaxis]
        col_mean = np.nanmean(np.abs(out), axis=0)
        col_mean = np.where(col_mean > 1e-15, col_mean, np.nan)
        out = out / col_mean[np.newaxis, :]
    return out


# ---------------------------------------------------------------------------
# Viterbi ridge
# ---------------------------------------------------------------------------


def estimate_lambda_from_anchors(
    map_routine: EvolutionMap,
    map_rpt: EvolutionMap,
    anchor_cycles: list[int],
    *,
    lam_scale: float = 0.1,
) -> float:
    """Estimate Viterbi smoothness penalty from RPT anchor drift.

    Works in **grid-coordinate** space (Q_norm or V), then converts to index
    penalty so the result is n_grid-independent. ``lam_scale`` (default 0.1)
    prevents path collapse to a horizontal line.
    """
    s_typ = float(np.nanstd(map_routine.M[np.isfinite(map_routine.M)])) if np.isfinite(map_routine.M).any() else 1.0
    s_typ = max(s_typ, 1e-3)
    n_grid = max(map_routine.n_grid, 2)
    span = float(map_routine.grid[-1] - map_routine.grid[0]) or 1.0

    deltas_coord: list[float] = []
    for i in range(len(anchor_cycles) - 1):
        c0, c1 = int(anchor_cycles[i]), int(anchor_cycles[i + 1])
        if c0 not in map_rpt.cycles or c1 not in map_rpt.cycles:
            continue
        i0 = int(np.where(map_rpt.cycles == c0)[0][0])
        i1 = int(np.where(map_rpt.cycles == c1)[0][0])
        row0, row1 = map_rpt.M[i0], map_rpt.M[i1]
        if not np.isfinite(row0).any() or not np.isfinite(row1).any():
            continue
        j0s = _top_k_indices(np.abs(row0), k=2)
        j1s = _top_k_indices(np.abs(row1), k=2)
        n_cyc = max(abs(c1 - c0), 1)
        for j0 in j0s:
            j1 = min(j1s, key=lambda j: abs(j - j0))
            d_coord = abs(float(map_rpt.grid[j1]) - float(map_rpt.grid[j0])) / n_cyc
            deltas_coord.append(d_coord)

    if deltas_coord:
        # Expected coordinate step per cycle; floor so λ cannot explode.
        d_coord = max(float(np.median(deltas_coord)), span / n_grid)  # ≥ 1 grid bin / cycle
    else:
        # Default: allow ~0.05 % of span per cycle (~0.00045 Q_norm for 0.9 span).
        d_coord = 5e-4 * span

    # Convert to index-step for the DP penalty (j-k)^2.
    d_idx = max(d_coord / span * n_grid, 0.5)
    lam = (s_typ / (d_idx ** 2)) * float(lam_scale)
    # Hard caps: too large → frozen paths; too small → wild jumps.
    return float(np.clip(lam, 1e-4, 2.0))


def _top_k_indices(row: np.ndarray, k: int = 2) -> list[int]:
    row = np.asarray(row, dtype=float)
    if not np.isfinite(row).any():
        return [0]
    idx = np.argsort(np.nan_to_num(row, nan=-np.inf))[::-1]
    out: list[int] = []
    for j in idx:
        if not np.isfinite(row[j]):
            continue
        if any(abs(j - o) < 10 for o in out):
            continue
        out.append(int(j))
        if len(out) >= k:
            break
    return out or [int(np.nanargmax(np.nan_to_num(row, nan=-np.inf)))]


def viterbi_ridge(
    M: np.ndarray,
    lam: float,
    *,
    max_step_idx: int | None = None,
    start_hint: int | None = None,
    quality_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Single-track Viterbi on evolution map rows (vectorized transition window)."""
    n, g = M.shape
    if n == 0 or g == 0:
        return np.array([], dtype=int), 0.0, np.array([])

    # Cap window — full g//20 at n_grid=2500 is too wide for DP cost.
    win = int(max_step_idx or max(5, min(60, max(g // 40, 10))))
    obs = np.abs(np.asarray(M, dtype=float))
    finite_obs = np.isfinite(obs)
    obs = np.where(finite_obs, obs, -np.inf)

    dp = np.full((n, g), -np.inf)
    bp = np.full((n, g), -1, dtype=int)

    if start_hint is not None:
        j0 = int(np.clip(start_hint, 0, g - 1))
        dp[0] = -lam * (np.arange(g) - j0) ** 2
        dp[0, ~finite_obs[0]] = -np.inf
    else:
        dp[0] = obs[0]

    offsets = np.arange(-win, win + 1, dtype=int)
    js = np.arange(g)
    for i in range(1, n):
        if quality_mask is not None and not quality_mask[i]:
            dp[i] = dp[i - 1]
            bp[i] = js
            continue
        prev = dp[i - 1]
        best = np.full(g, -np.inf)
        best_k = np.full(g, -1, dtype=int)
        for off in offsets:
            k = js + off
            valid = (k >= 0) & (k < g)
            if not np.any(valid):
                continue
            cand = np.full(g, -np.inf)
            cand[valid] = prev[k[valid]] - lam * float(off * off)
            better = cand > best
            best_k = np.where(better, k, best_k)
            best = np.where(better, cand, best)
        dp[i] = best + obs[i]
        bp[i] = best_k

    if not np.any(np.isfinite(dp[-1])):
        return np.zeros(n, dtype=int), -np.inf, np.zeros(n)

    path = np.zeros(n, dtype=int)
    path[-1] = int(np.argmax(np.nan_to_num(dp[-1], nan=-np.inf, neginf=-np.inf)))
    score = float(dp[-1, path[-1]])
    conf = np.zeros(n)
    for i in range(n - 2, -1, -1):
        pk = int(bp[i + 1, path[i + 1]])
        path[i] = pk if pk >= 0 else int(path[i + 1])
        row_max = float(np.max(obs[i][finite_obs[i]])) if finite_obs[i].any() else 1.0
        val = obs[i, path[i]]
        conf[i] = float(val / (abs(row_max) + 1e-12)) if np.isfinite(val) else 0.0
    conf[-1] = conf[-2] if n > 1 else 1.0
    return path, score, np.clip(conf, 0.0, 1.0)


def _local_halfwidth(M: np.ndarray, path: np.ndarray, cycle_i: int, j: int) -> int:
    row = np.abs(M[cycle_i])
    if not np.isfinite(row[j]):
        return 5
    h = row[j]
    half = h * 0.5
    lo, hi = j, j
    while lo > 0 and np.isfinite(row[lo]) and row[lo] > half:
        lo -= 1
    while hi < len(row) - 1 and np.isfinite(row[hi]) and row[hi] > half:
        hi += 1
    return max(2, (hi - lo) // 2)


def extract_tracks(
    emap: EvolutionMap,
    lam: float,
    *,
    max_tracks: int = 12,
    snr_stop: float = 3.0,
    rois: tuple[tuple[float, float], ...] | None = None,
    use_roi: bool = False,
    max_step_idx: int | None = None,
) -> list[dict[str, Any]]:
    """Sequentially extract ridges with local-width masking.

    If ``use_roi`` and ``rois`` are set, each ROI is extracted on a **sliced**
    sub-grid (not NaN-masked) so ROI edges do not create false ridges.
    """
    if use_roi and rois and emap.domain == "Q":
        tracks: list[dict[str, Any]] = []
        tid = 0
        per_roi = max(1, max_tracks // max(len(rois), 1))
        for q_lo, q_hi in rois:
            j_lo = int(np.searchsorted(emap.grid, q_lo, side="left"))
            j_hi = int(np.searchsorted(emap.grid, q_hi, side="right"))
            if j_hi - j_lo < 10:
                continue
            sub = EvolutionMap(
                M=emap.M[:, j_lo:j_hi].copy(),
                cycles=emap.cycles,
                grid=emap.grid[j_lo:j_hi].copy(),
                domain=emap.domain,
                leg=emap.leg,
                rate=emap.rate,
                normalize=emap.normalize,
                quality_mask=emap.quality_mask,
            )
            local = _extract_tracks_global(
                sub, lam, max_tracks=per_roi, snr_stop=snr_stop, max_step_idx=max_step_idx,
            )
            for tr in local:
                # Remap path indices onto the full grid.
                tr["path"] = tr["path"] + j_lo
                tr["track_id"] = tid
                tr["roi"] = (q_lo, q_hi)
                tracks.append(tr)
                tid += 1
        return tracks
    return _extract_tracks_global(
        emap, lam, max_tracks=max_tracks, snr_stop=snr_stop, max_step_idx=max_step_idx,
    )


def _ridge_amplitude_floor(M: np.ndarray, snr_stop: float) -> float:
    """Robust stop floor: median(|amp|) + snr_stop × MAD (works for local_contrast)."""
    finite = np.abs(M[np.isfinite(M)])
    if finite.size == 0:
        return float("inf")
    med = float(np.nanmedian(finite))
    mad = float(np.nanmedian(np.abs(finite - med))) * 1.4826 + 1e-12
    return med + float(snr_stop) * mad


def _extract_tracks_global(
    emap: EvolutionMap,
    lam: float,
    *,
    max_tracks: int = 12,
    snr_stop: float = 3.0,
    max_step_idx: int | None = None,
) -> list[dict[str, Any]]:
    """Global sequential ridge extraction on (possibly ROI-sliced) map."""
    M = emap.M.copy()
    tracks: list[dict[str, Any]] = []
    prev_score = None

    for tid in range(max_tracks):
        floor = _ridge_amplitude_floor(M, snr_stop)
        if not np.isfinite(M).any() or float(np.nanmax(np.abs(M))) < floor:
            break
        path, score, conf = viterbi_ridge(
            M, lam, quality_mask=emap.quality_mask, max_step_idx=max_step_idx,
        )
        if len(path) == 0 or not np.isfinite(score) or score <= -1e100:
            break
        # Successive-score collapse: stop when this ridge is << first ridge.
        if prev_score is not None and score < 0.35 * prev_score:
            break
        if prev_score is None:
            prev_score = score
        tracks.append({"track_id": tid, "path": path, "score": score, "confidence": conf, "roi": None})
        for i in range(emap.n_cycles):
            j = int(path[i])
            hw = _local_halfwidth(M, path, i, j)
            lo, hi = max(0, j - int(hw * 1.5)), min(M.shape[1], j + int(hw * 1.5) + 1)
            M[i, lo:hi] = np.nan
    return tracks


# ---------------------------------------------------------------------------
# Lifecycle + events
# ---------------------------------------------------------------------------


def _region_area(M: np.ndarray, cycle_i: int, j_center: int, halfwidth: int) -> float:
    lo = max(0, j_center - halfwidth)
    hi = min(M.shape[1], j_center + halfwidth + 1)
    row = M[cycle_i, lo:hi]
    return float(np.nansum(np.abs(row)))


def classify_disappearance(
    M: np.ndarray,
    track_path: np.ndarray,
    neighbor_paths: list[np.ndarray],
    cycle_idx: int,
    *,
    merge_tol: float = 0.15,
    death_tol: float = 0.30,
    window: int = 3,
) -> tuple[EventType, str, float]:
    """Classify merge vs true death using local area conservation."""
    n = M.shape[0]
    w = min(window, cycle_idx, n - cycle_idx - 1)
    if w < 1:
        return "ambiguous", "insufficient_window", 0.0
    j = int(track_path[cycle_idx])
    hw = _local_halfwidth(M, track_path, cycle_idx, j)
    # region spans track + neighbors
    js = [j] + [int(neighbor_paths[k][cycle_idx]) for k in range(len(neighbor_paths))]
    lo = max(0, min(js) - hw)
    hi = min(M.shape[1], max(js) + hw + 1)
    before = float(np.nansum(np.abs(M[cycle_idx - w:cycle_idx, lo:hi])))
    after = float(np.nansum(np.abs(M[cycle_idx:cycle_idx + w + 1, lo:hi])))
    if before <= 1e-12:
        return "ambiguous", "zero_area_before", 0.0
    ratio = after / before
    if abs(ratio - 1.0) < merge_tol:
        return "merged", f"area_ratio={ratio:.3f}", 0.7
    if ratio < (1.0 - death_tol):
        return "died", f"area_ratio={ratio:.3f}", 0.75
    return "ambiguous", f"area_ratio={ratio:.3f}", 0.4


@dataclass
class _TrackLifecycle:
    track_id: int
    state: TrackState = "tentative"
    history: list[bool] = field(default_factory=list)
    birth_cycle: int | None = None
    death_cycle: int | None = None
    coast_count: int = 0
    group_id: int | None = None
    graphite_candidate: bool = False


def _update_lifecycle(
    life: _TrackLifecycle,
    observed: bool,
    cycle: int,
    config: PeakEvolutionConfig,
    *,
    track_start_cycle: int,
) -> EventType | None:
    life.history.append(observed)
    evt: EventType | None = None
    if life.state == "tentative":
        recent = life.history[-config.confirm_n:]
        if len(recent) >= config.confirm_n and sum(recent) >= config.confirm_m:
            life.state = "confirmed"
            life.birth_cycle = cycle
            # First confirmation inside the start window is track start, not a physical birth.
            if (cycle - track_start_cycle) <= config.initial_window_cycles:
                evt = "initial"
            else:
                evt = "born"
    elif life.state == "confirmed":
        if not observed:
            life.coast_count += 1
            if life.coast_count >= config.coast_k:
                life.state = "coasting"
        else:
            life.coast_count = 0
    elif life.state == "coasting":
        if observed:
            life.state = "confirmed"
            life.coast_count = 0
            evt = "resumed"
        else:
            life.coast_count += 1
            if life.coast_count >= config.terminate_l:
                life.state = "terminated"
                life.death_cycle = cycle
    return evt


# ---------------------------------------------------------------------------
# Track assembly
# ---------------------------------------------------------------------------


def _path_to_trajectory(
    emap: EvolutionMap,
    track: dict[str, Any],
    lifecycle: _TrackLifecycle,
    config: PeakEvolutionConfig,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    path = track["path"]
    conf = track["confidence"]
    rows: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    neighbor_paths: list[np.ndarray] = []
    track_start = int(emap.cycles[0]) if len(emap.cycles) else 0
    birth_event_type: str | None = None

    for i, cyc in enumerate(emap.cycles):
        j = int(path[i])
        observed = bool(emap.quality_mask[i] and np.isfinite(emap.M[i, j]))
        evt = _update_lifecycle(
            lifecycle, observed, int(cyc), config, track_start_cycle=track_start,
        )
        if evt in ("born", "initial"):
            birth_event_type = evt
            events.append({
                "cycle": int(cyc),
                "event_type": evt,
                "track_ids": str(track["track_id"]),
                "classification_reason": "confirm_M_of_N",
                "confidence": 0.6,
            })
        grid_val = float(emap.grid[j])
        height = float(emap.M[i, j]) if np.isfinite(emap.M[i, j]) else np.nan
        hw = _local_halfwidth(emap.M, path, i, j)
        area = _region_area(emap.M, i, j, hw)
        rows.append({
            "cycle": int(cyc),
            "track_id": track["track_id"],
            "state": lifecycle.state,
            "grid_coord": grid_val,
            "V": grid_val if emap.domain == "V" else np.nan,
            "Q": grid_val if emap.domain == "Q" else np.nan,
            "height": height,
            "area": area,
            "sigma": hw,
            "confidence": float(conf[i]) if i < len(conf) else np.nan,
            "snr_local": float(abs(height) / (np.nanmedian(np.abs(emap.M[i])) + 1e-12)),
            "observed": observed,
            "roi": str(track.get("roi")),
        })
        if lifecycle.state == "terminated" and lifecycle.death_cycle == cyc:
            etype, reason, cfd = classify_disappearance(
                emap.M, path, neighbor_paths, i,
                merge_tol=config.merge_tol, death_tol=config.death_tol, window=config.area_window,
            )
            events.append({
                "cycle": int(cyc), "event_type": etype, "track_ids": str(track["track_id"]),
                "area_before": np.nan, "area_after": np.nan, "area_ratio": np.nan,
                "classification_reason": reason, "confidence": cfd,
            })
    traj = pd.DataFrame(rows)
    traj.attrs["birth_event_type"] = birth_event_type or "unknown"
    return traj, events


def _summarize_track(traj: pd.DataFrame, emap: EvolutionMap, config: PeakEvolutionConfig) -> dict[str, Any]:
    tid = int(traj["track_id"].iloc[0])
    obs = traj[traj["observed"]]
    g0 = float(obs["grid_coord"].iloc[0]) if len(obs) else np.nan
    g1 = float(obs["grid_coord"].iloc[-1]) if len(obs) else np.nan
    c0 = int(obs["cycle"].iloc[0]) if len(obs) else np.nan
    c1 = int(obs["cycle"].iloc[-1]) if len(obs) else np.nan
    span = max(c1 - c0, 1) if np.isfinite(c0) and np.isfinite(c1) else 1
    drift_per_100 = (g1 - g0) / span * 100 if np.isfinite(g0) and np.isfinite(g1) else np.nan
    # Drift via linear fit (more robust than endpoints).
    drift_r2 = np.nan
    if len(obs) >= 5:
        x = obs["cycle"].to_numpy(float)
        y = obs["grid_coord"].to_numpy(float)
        coef = np.polyfit(x, y, 1)
        yhat = np.polyval(coef, x)
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        drift_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        drift_per_100 = float(coef[0] * 100)

    v_lo, v_hi = config.graphite_flag_v_range
    graphite = bool(
        emap.domain == "V" and np.isfinite(g0) and v_lo <= g0 <= v_hi
        or emap.domain == "Q" and np.isfinite(g0) and 0.15 <= g0 <= 0.55
    )
    a0 = float(obs["area"].iloc[0]) if len(obs) else np.nan
    a1 = float(obs["area"].iloc[-1]) if len(obs) else np.nan
    fade = (a0 - a1) / a0 * 100 if np.isfinite(a0) and a0 > 0 else np.nan
    birth_evt = traj.attrs.get("birth_event_type", "initial")
    return {
        "track_id": tid,
        "birth_cycle": c0,
        "birth_event_type": birth_evt,
        "birth_confidence": float(obs["confidence"].iloc[0]) if len(obs) else np.nan,
        "death_cycle": c1,
        "death_event_type": "unknown",
        "death_confidence": np.nan,
        "lifetime_cycles": int(len(traj)),
        "domain": emap.domain,
        "leg": emap.leg,
        "rate": emap.rate,
        "normalize_mode": emap.normalize,
        "V_start": g0 if emap.domain == "V" else np.nan,
        "V_end": g1 if emap.domain == "V" else np.nan,
        "V_drift_mV_per_100cyc": drift_per_100 * 1000 if emap.domain == "V" else np.nan,
        "V_drift_r2": drift_r2 if emap.domain == "V" else np.nan,
        "Q_start": g0 if emap.domain == "Q" else np.nan,
        "Q_end": g1 if emap.domain == "Q" else np.nan,
        "Q_drift_per_100cyc": drift_per_100 if emap.domain == "Q" else np.nan,
        "Q_drift_r2": drift_r2 if emap.domain == "Q" else np.nan,
        "area_start": a0,
        "area_end": a1,
        "area_fade_pct": fade,
        "area_fade_r2": np.nan,
        "sigma_start": float(obs["sigma"].iloc[0]) if len(obs) else np.nan,
        "sigma_end": float(obs["sigma"].iloc[-1]) if len(obs) else np.nan,
        "sigma_growth_per_100cyc": np.nan,
        "group_id": np.nan,
        "mean_confidence": float(traj["confidence"].mean()),
        "min_confidence": float(traj["confidence"].min()),
        "n_observed": int(obs.shape[0]),
        "n_coasted": int((~traj["observed"]).sum()),
        "n_interpolated": int((~traj["observed"]).sum()),
        "graphite_stage_candidate": graphite,
        "roi": traj["roi"].iloc[0] if "roi" in traj.columns else None,
    }


# ---------------------------------------------------------------------------
# RPT anchors + LOO validation
# ---------------------------------------------------------------------------


def resolve_rpt_anchor_cycles(step_df: pd.DataFrame | None) -> list[int]:
    """Second capa_full cycle of each preceding pair (cycle 2 of 2–3, 107–108, …).

    Prefer cycle 2: cycle 1 still carries prior 0.5C polarization history.
    """
    if step_df is None:
        return []
    flags = detect_protocol_flags(step_df)
    if flags.empty:
        return []
    prot = build_protocol_exclusion(step_df)
    anchors: list[int] = []
    for block in prot.rpt_blocks:
        if not block:
            continue
        capa = preceding_capa_full_cycles(flags, int(block[0]))
        if len(capa) >= 2:
            anchors.append(int(capa[1]))  # second of the pair
        elif len(capa) == 1:
            anchors.append(int(capa[0]))
    return anchors


def anchor_tracks(
    map_routine: EvolutionMap,
    map_rpt: EvolutionMap,
    anchor_cycles: list[int] | None = None,
    step_df: pd.DataFrame | None = None,
) -> list[int]:
    """RPT capa_full cycle-2 anchors (~105 cycle spacing)."""
    if anchor_cycles:
        return [int(c) for c in anchor_cycles]
    from_step = resolve_rpt_anchor_cycles(step_df)
    if from_step:
        # Keep only those present on RPT map (or nearest capa_full on map).
        out = []
        for c in from_step:
            if c in map_rpt.cycles:
                out.append(c)
            else:
                # nearest within ±2
                near = [int(x) for x in map_rpt.cycles if abs(int(x) - c) <= 2]
                if near:
                    out.append(min(near, key=lambda x: abs(x - c)))
        if out:
            return out
    # Fallback: every other capa_full on the map (assume pairs)
    caps = list(map(int, map_rpt.cycles))
    if len(caps) >= 2:
        return caps[1::2][:6]
    return caps[:6]


def peak_position_noise_floor(
    map_rpt: EvolutionMap,
    step_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Peak-position noise floor from RPT capa_full cycle1 vs cycle2 within each block.

    This is the correct unit for LOO peak-position errors (grid coord / V),
    NOT the capacity fade floor 0.065 %.
    """
    pairs: list[tuple[int, int]] = []
    if step_df is not None:
        flags = detect_protocol_flags(step_df)
        prot = build_protocol_exclusion(step_df)
        for block in prot.rpt_blocks:
            if not block:
                continue
            capa = preceding_capa_full_cycles(flags, int(block[0]))
            if len(capa) >= 2:
                pairs.append((int(capa[0]), int(capa[1])))
    else:
        caps = list(map(int, map_rpt.cycles))
        for i in range(0, len(caps) - 1, 2):
            pairs.append((caps[i], caps[i + 1]))

    errs: list[float] = []
    per_pair: list[dict[str, Any]] = []
    for c1, c2 in pairs:
        if c1 not in map_rpt.cycles or c2 not in map_rpt.cycles:
            continue
        i1 = int(np.where(map_rpt.cycles == c1)[0][0])
        i2 = int(np.where(map_rpt.cycles == c2)[0][0])
        r1, r2 = map_rpt.M[i1], map_rpt.M[i2]
        if not np.isfinite(r1).any() or not np.isfinite(r2).any():
            continue
        # Match local maxima in interior Q (exclude last 10% where cliff remnant lives).
        g = map_rpt.grid
        interior = (g >= (g[0] + 0.05 * (g[-1] - g[0]))) & (g <= (g[-1] - 0.10 * (g[-1] - g[0])))
        r1i = np.where(interior, np.abs(r1), np.nan)
        r2i = np.where(interior, np.abs(r2), np.nan)
        j1s = _top_k_indices(r1i, k=2)
        j2s = _top_k_indices(r2i, k=2)
        pair_errs = []
        for j1 in j1s:
            j2 = min(j2s, key=lambda j: abs(j - j1))
            e = abs(float(map_rpt.grid[j1]) - float(map_rpt.grid[j2]))
            pair_errs.append(e)
            errs.append(e)
        per_pair.append({
            "cycle1": c1, "cycle2": c2,
            "error_grid_mean": float(np.mean(pair_errs)) if pair_errs else np.nan,
        })

    rms = float(np.sqrt(np.mean(np.asarray(errs) ** 2))) if errs else float("nan")
    med = float(np.median(errs)) if errs else float("nan")
    return {
        "n_pairs": len(per_pair),
        "per_pair": per_pair,
        "noise_floor_grid_rms": rms,
        "noise_floor_grid_median": med,
        "unit": "grid_coord (Q_norm fraction or V)",
        "note": "from RPT capa_full cycle1 vs cycle2 - NOT capacity SoHQ noise floor",
    }


def validate_loo_rpt(
    trajectories: pd.DataFrame,
    map_routine: EvolutionMap,
    map_rpt: EvolutionMap,
    anchor_cycles: list[int],
    *,
    noise_floor_grid: float | None = None,
    search_half_q: float = 0.08,
) -> dict[str, Any]:
    """Leave-one-RPT-out: predict next anchor grid position from routine track."""
    errors: list[float] = []
    per_anchor: list[dict[str, Any]] = []
    nf = noise_floor_grid if noise_floor_grid is not None and np.isfinite(noise_floor_grid) else float("nan")
    n_saturated = 0
    # Treat error within 1 grid bin of the search half-width as "stuck at window edge".
    sat_tol = 1.5 / max(map_rpt.n_grid, 1) * float(map_rpt.grid[-1] - map_rpt.grid[0] or 1.0)

    for k in range(len(anchor_cycles) - 1):
        c_anchor = int(anchor_cycles[k])
        c_next = int(anchor_cycles[k + 1])
        if c_next not in map_rpt.cycles:
            continue
        rout_before = map_routine.cycles[map_routine.cycles <= c_next - 5]
        if len(rout_before) == 0:
            continue
        c_pred = int(rout_before[-1])
        traj = trajectories[trajectories["cycle"] == c_pred]
        if traj.empty:
            continue
        # Prefer graphite-ROI track if present
        if "roi" in traj.columns:
            gr = traj[traj["roi"].astype(str).str.contains("0.15")]
            use = gr if not gr.empty else traj
        else:
            use = traj
        pred_g = float(use.groupby("track_id")["grid_coord"].first().median())
        rpt_i = int(np.where(map_rpt.cycles == c_next)[0][0])
        rpt_row = map_rpt.M[rpt_i]
        # Local peak near prediction — global top-k still latches onto Q≈0.88 cliff remnant.
        span = float(map_rpt.grid[-1] - map_rpt.grid[0]) or 1.0
        j_pred = int(np.argmin(np.abs(map_rpt.grid - pred_g)))
        half = max(8, int(float(search_half_q) / span * map_rpt.n_grid))
        lo, hi = max(0, j_pred - half), min(map_rpt.n_grid, j_pred + half + 1)
        local = np.abs(rpt_row[lo:hi])
        if np.isfinite(local).any():
            meas_j = lo + int(np.nanargmax(local))
            at_lo = meas_j <= lo
            at_hi = meas_j >= hi - 1
            window_saturated = bool(at_lo or at_hi)
        else:
            j_cands = _top_k_indices(np.abs(rpt_row), k=3)
            meas_j = min(j_cands, key=lambda j: abs(float(map_rpt.grid[j]) - pred_g))
            window_saturated = False
        meas_g = float(map_rpt.grid[meas_j])
        err = abs(pred_g - meas_g)
        # Also flag when |err| ≈ search half-width (classic "stuck at boundary" signature).
        if abs(err - float(search_half_q)) <= sat_tol:
            window_saturated = True
        if window_saturated:
            n_saturated += 1
        errors.append(err)
        # Per-anchor pass ignores saturated window hits — those are not valid matches.
        if window_saturated:
            passed = False
        elif np.isfinite(nf):
            passed = bool(err < 3 * nf)
        else:
            passed = None
        per_anchor.append({
            "anchor_cycle": c_anchor,
            "predict_cycle": c_pred,
            "rpt_cycle": c_next,
            "pred_grid": pred_g,
            "meas_grid": meas_g,
            "error_grid": err,
            "search_half_q": float(search_half_q),
            "search_window_saturated": window_saturated,
            "pass": passed,
        })

    rms = float(np.sqrt(np.mean(np.array(errors) ** 2))) if errors else float("nan")
    search_window_saturated = bool(n_saturated > 0)
    # pass_flag requires: finite RMS, finite noise floor, RMS ok, AND no window saturation.
    pass_flag = bool(
        np.isfinite(rms)
        and np.isfinite(nf)
        and rms < 3 * nf
        and not search_window_saturated
        and len(errors) > 0
    )
    return {
        "per_anchor_error": per_anchor,
        "rms_grid_error": rms,
        "noise_floor_grid": nf,
        "pass_flag": pass_flag,
        "search_window_saturated": search_window_saturated,
        "n_search_window_saturated": int(n_saturated),
        "n_anchors": len(per_anchor),
        "n_anchor_cycles_available": len(anchor_cycles),
        "anchor_spacing_cycles_note": "~105 cycles between RPT blocks",
        "capacity_noise_floor_pct_NOT_used": CAPACITY_NOISE_FLOOR_PCT,
    }


def extract_q_steepen(
    raw_df: pd.DataFrame,
    *,
    config: PeakEvolutionConfig | None = None,
    step_df: pd.DataFrame | None = None,
    rate: str = "0.5C",
    q_search_lo: float = 0.80,
    q_search_hi: float = 0.99,
) -> pd.DataFrame:
    """Track discharge-end steepening onset in absolute Ah and Q_norm.

    This is NOT a phase-transition peak — it is the cathode/anode depletion cliff.
    Useful for Si/Gr H1/H2 discrimination when tracked on absolute Q.
    """
    config = config or PeakEvolutionConfig()
    cycles = _select_cycles_by_rate(raw_df, step_df, rate, config)
    rows: list[dict[str, Any]] = []
    for cyc in cycles:
        row = _cycle_curve(raw_df, cyc, config)
        if row is None:
            continue
        v, q, total_q = row
        if total_q <= 0:
            continue
        # dV/dQ on raw-ish Q
        order = np.argsort(q)
        q_s, v_s = q[order], v[order]
        _, uid = np.unique(np.round(q_s, 6), return_index=True)
        q_s, v_s = q_s[uid], v_s[uid]
        if len(q_s) < 20:
            continue
        dvdq = np.gradient(v_s, q_s)
        qn = q_s / total_q
        m = (qn >= q_search_lo) & (qn <= q_search_hi) & np.isfinite(dvdq)
        if m.sum() < 5:
            continue
        # Steepen onset: where |dV/dQ| exceeds 3× median of mid-SOC
        mid = (qn >= 0.3) & (qn <= 0.7) & np.isfinite(dvdq)
        floor = float(np.nanmedian(np.abs(dvdq[mid]))) if mid.any() else float(np.nanmedian(np.abs(dvdq)))
        thr = 3.0 * max(floor, 1e-6)
        cand = np.where(m & (np.abs(dvdq) >= thr))[0]
        if len(cand) == 0:
            # fallback: max |dV/dQ| in search window
            idx = int(np.flatnonzero(m)[np.nanargmax(np.abs(dvdq[m]))])
        else:
            idx = int(cand[0])  # first exceedance = onset
        rows.append({
            "cycle": int(cyc),
            "Q_steepen_abs_Ah": float(q_s[idx]),
            "Q_steepen_norm": float(qn[idx]),
            "dvdq_at_steepen": float(dvdq[idx]),
            "total_Ah": float(total_q),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Synthetic MOT
# ---------------------------------------------------------------------------


def make_synthetic_map(
    n_cycles: int = 80,
    n_grid: int = 200,
    events: list[dict[str, Any]] | None = None,
    *,
    v_noise_sigma: float = 0.05,
    seed: int = 0,
) -> EvolutionMap:
    """Synthetic evolution map with injected ridges and events."""
    rng = np.random.default_rng(seed)
    grid = np.linspace(0.05, 0.95, n_grid)
    M = np.zeros((n_cycles, n_grid))
    cycles = np.arange(1, n_cycles + 1)
    # two tracks
    for offset, slope in ((40, 0.08), (120, -0.05)):
        for i in range(n_cycles):
            j = int(np.clip(offset + slope * i / 100, 0, n_grid - 1))
            lo, hi = max(0, j - 2), min(n_grid, j + 3)
            idx = np.arange(lo, hi)
            M[i, lo:hi] += np.exp(-0.5 * ((idx - j) ** 2))
    M += rng.normal(0, v_noise_sigma, M.shape)
    if events:
        for ev in events:
            if ev.get("type") == "merge" and "cycle" in ev:
                ci = int(ev["cycle"]) - 1
                M[ci, :] *= 0.9
    qmask = np.ones(n_cycles, dtype=bool)
    return EvolutionMap(M=M, cycles=cycles, grid=grid, domain="Q", leg="discharge",
                        rate="synthetic", normalize="none", quality_mask=qmask)


def evaluate_synthetic_mot(
    true_paths: list[np.ndarray],
    pred_paths: list[np.ndarray],
    true_events: set[tuple[int, str]],
    pred_events: set[tuple[int, str]],
) -> dict[str, float]:
    """MOT-style metrics for synthetic validation."""
    id_switches = 0
    frags = []
    for tp, pp in zip(true_paths, pred_paths):
        if len(tp) != len(pp):
            frags.append(2.0)
            continue
        switches = int(np.sum(np.abs(np.diff(pp - tp)) > 3))
        id_switches += switches
        frags.append(1.0 + switches * 0.2)
    mostly = sum(1 for f in frags if f <= 1.2) / max(len(frags), 1)
    tp_ev = len(true_events & pred_events)
    fp_ev = len(pred_events - true_events)
    prec = tp_ev / (tp_ev + fp_ev + 1e-9)
    rec = tp_ev / (len(true_events) + 1e-9)
    return {
        "id_switch_rate": float(id_switches),
        "track_fragmentation": float(np.mean(frags)) if frags else 1.0,
        "mostly_tracked_ratio": float(mostly),
        "event_precision": float(prec),
        "event_recall": float(rec),
        "false_birth_rate": float(fp_ev / max(len(pred_events), 1)),
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def track_peaks(
    emap: EvolutionMap,
    *,
    anchors: EvolutionMap | None = None,
    config: PeakEvolutionConfig | None = None,
    anchor_cycles: list[int] | None = None,
    step_df: pd.DataFrame | None = None,
) -> PeakEvolutionResult:
    """Extract tracks, trajectories, events from one evolution map."""
    config = config or PeakEvolutionConfig()
    if config.method == "deconv":
        raise NotImplementedError("method='deconv' reserved for constrained deconvolution (roadmap §5.8)")

    ac = anchor_tracks(emap, anchors or emap, anchor_cycles, step_df=step_df)
    lam = config.lam
    if lam is None and anchors is not None:
        lam = estimate_lambda_from_anchors(emap, anchors, ac, lam_scale=config.lam_scale)
    if lam is None:
        lam = 0.1

    raw_tracks = extract_tracks(
        emap, lam,
        max_tracks=config.max_tracks,
        snr_stop=config.snr_stop,
        rois=config.rois,
        use_roi=config.use_roi_extract and emap.domain == "Q",
        max_step_idx=config.viterbi_window,
    )
    trajectories_list: list[pd.DataFrame] = []
    events_list: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for tr in raw_tracks:
        life = _TrackLifecycle(track_id=tr["track_id"])
        traj, evs = _path_to_trajectory(emap, tr, life, config)
        trajectories_list.append(traj)
        events_list.extend(evs)
        summaries.append(_summarize_track(traj, emap, config))

    trajectories = pd.concat(trajectories_list, ignore_index=True) if trajectories_list else pd.DataFrame()
    tracks = pd.DataFrame(summaries) if summaries else pd.DataFrame()
    events = pd.DataFrame(events_list) if events_list else pd.DataFrame()

    validation: dict[str, Any] = {
        "lam_used": lam,
        "anchor_cycles": ac,
        "n_raw_tracks": len(raw_tracks),
    }
    if anchors is not None:
        nf = peak_position_noise_floor(anchors, step_df=step_df)
        validation["peak_position_noise_floor"] = nf
        if not trajectories.empty and "cycle" in trajectories.columns:
            validation.update(validate_loo_rpt(
                trajectories, emap, anchors, ac,
                noise_floor_grid=nf.get("noise_floor_grid_median"),
            ))
        else:
            validation["loo_skipped"] = "no_trajectories"

    return PeakEvolutionResult(
        tracks=tracks,
        trajectories=trajectories,
        events=events,
        validation=validation,
        map_routine=emap,
        map_rpt=anchors,
    )


def track_peaks_pipeline(
    raw_df: pd.DataFrame,
    step_df: pd.DataFrame | None = None,
    *,
    config: PeakEvolutionConfig | None = None,
    run_preflight: bool = True,
    abort_on_preflight_fail: bool = False,
) -> PeakEvolutionResult:
    """Full pipeline: preflight → routine map → RPT map → track + validate."""
    config = config or PeakEvolutionConfig()
    preflight = run_preflight_checks(raw_df, step_df, config=config) if run_preflight else None
    if abort_on_preflight_fail and preflight is not None and not preflight_passes(preflight):
        return PeakEvolutionResult(
            tracks=pd.DataFrame(), trajectories=pd.DataFrame(), events=pd.DataFrame(),
            validation={"aborted": True, "reason": "preflight_fail"},
            preflight=preflight,
        )

    emap_r = build_evolution_map(raw_df, config=config, rate="0.5C", step_df=step_df)
    emap_rpt = build_evolution_map(raw_df, config=config, rate="C/3", step_df=step_df)
    ac = anchor_tracks(emap_r, emap_rpt, step_df=step_df)
    result = track_peaks(emap_r, anchors=emap_rpt, config=config, anchor_cycles=ac, step_df=step_df)
    result.preflight = preflight
    result.map_routine = emap_r
    result.map_rpt = emap_rpt
    if config.extract_steepen:
        result.steepen = extract_q_steepen(raw_df, config=config, step_df=step_df, rate="0.5C")
    return result


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def plot_peak_evolution(result: PeakEvolutionResult, out_dir: str | Path) -> list[Path]:
    import matplotlib.pyplot as plt

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    emap = result.map_routine
    if emap is None or emap.n_cycles == 0:
        return paths

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(
        emap.M, aspect="auto", origin="lower",
        extent=[emap.grid[0], emap.grid[-1], emap.cycles[0], emap.cycles[-1]],
        cmap="viridis",
    )
    if not result.trajectories.empty:
        for tid, grp in result.trajectories.groupby("track_id"):
            ax.plot(grp["grid_coord"], grp["cycle"], lw=1.2, label=f"T{tid}")
    ax.set_xlabel(f"grid ({emap.domain})")
    ax.set_ylabel("cycle")
    ax.set_title(f"Peak evolution map ({emap.rate})")
    fig.colorbar(im, ax=ax)
    p = out / "peak_evolution_map.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(p)

    if not result.tracks.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        for _, row in result.tracks.iterrows():
            col = "V_start" if emap.domain == "V" else "Q_start"
            end = "V_end" if emap.domain == "V" else "Q_end"
            if np.isfinite(row.get(col)) and np.isfinite(row.get(end)):
                ax.plot([row["birth_cycle"], row["death_cycle"]], [row[col], row[end]], marker="o")
        ax.set_xlabel("cycle")
        ax.set_ylabel(emap.domain)
        ax.set_title("Peak tracks")
        p2 = out / "peak_tracks_V.png"
        fig.savefig(p2, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(p2)

        fig, ax = plt.subplots(figsize=(10, 5))
        for _, row in result.tracks.iterrows():
            if np.isfinite(row.get("area_start")):
                ax.plot([row["birth_cycle"], row["death_cycle"]], [row["area_start"], row["area_end"]], marker="s")
        ax.set_xlabel("cycle")
        ax.set_ylabel("area")
        p3 = out / "peak_tracks_area.png"
        fig.savefig(p3, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(p3)

    if not result.events.empty:
        fig, ax = plt.subplots(figsize=(12, 3))
        for _, ev in result.events.iterrows():
            ax.axvline(ev["cycle"], alpha=0.5)
            ax.text(ev["cycle"], 0.5, str(ev["event_type"]), rotation=90, fontsize=7)
        ax.set_xlabel("cycle")
        ax.set_title("Peak events timeline")
        p4 = out / "peak_events_timeline.png"
        fig.savefig(p4, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(p4)

    return paths


def compare_domains(
    raw_df: pd.DataFrame,
    step_df: pd.DataFrame | None = None,
    *,
    base_config: PeakEvolutionConfig | None = None,
) -> dict[str, Any]:
    """Run tracking in Q vs V domain for comparison (§9 item 8)."""
    base = base_config or PeakEvolutionConfig()
    cfg_q = PeakEvolutionConfig(
        domain="Q",
        leg=base.leg,
        normalize=base.normalize,
        n_grid=base.n_grid,
        dqdv_config=base.dqdv_config,
        lam=base.lam,
        max_tracks=base.max_tracks,
        quality_gate=base.quality_gate,
        post_rpt_exclude=base.post_rpt_exclude,
    )
    cfg_v = PeakEvolutionConfig(
        domain="V",
        leg=base.leg,
        normalize=base.normalize,
        n_grid=base.n_grid,
        dqdv_config=base.dqdv_config,
        lam=base.lam,
        max_tracks=base.max_tracks,
        quality_gate=base.quality_gate,
        post_rpt_exclude=base.post_rpt_exclude,
        v_grid_lo=base.v_grid_lo,
        v_grid_hi=base.v_grid_hi,
    )
    rq = track_peaks_pipeline(raw_df, step_df, config=cfg_q, run_preflight=False)
    rv = track_peaks_pipeline(raw_df, step_df, config=cfg_v, run_preflight=False)
    return {
        "Q": {"n_tracks": len(rq.tracks), "validation": rq.validation},
        "V": {"n_tracks": len(rv.tracks), "validation": rv.validation},
    }
