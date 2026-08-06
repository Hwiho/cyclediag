"""RPT post-block capacity recovery: overlay, exponential fit, permanent-step test.

Physical frame (0.5C routine only — rate is unchanged across RPT):

    Q_obs(n) = Q_irreversible(n) + Q_reversible(n)

Long rest during RPT resets Q_reversible toward zero.  The post-block bump is
Q_reversible refilling; amplitude A measures accumulated reversible loss at rest.

Model (per block ending at cycle n0):

    Q(n) = Q_trend(n) + A · exp(-(n - n0) / λ)

Pre-RPT anchor (clean reference, saturated reversible loss):

    anchor_k = mean(SoHQ_routine[block_start - W : block_start])

bump_contamination (knee distortion metric):

    fade_rate_intra  ← slope within inter-RPT routine segment (includes bump)
    fade_rate_inter  ← slope between consecutive pre-RPT anchors
    bump_contamination = fade_rate_intra / fade_rate_inter - 1
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from cyclediag.io.cycle_protocol import (
    POST_RPT_EXCLUDE,
    ProtocolExclusion,
    build_protocol_exclusion,
)

# §5.10 Q_relax noise floor (RPT 2-cycle capacity difference)
Q_RELAX_NOISE_FLOOR_PCT = 0.065
DEFAULT_ANCHOR_WIDTH = 5


def _linear_trend(cycles: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    """Return (slope, intercept) for y = slope * x + intercept."""
    if len(cycles) == 0:
        return 0.0, np.nan
    if len(cycles) == 1:
        return 0.0, float(values[0])
    slope, intercept = np.polyfit(cycles.astype(float), values.astype(float), 1)
    return float(slope), float(intercept)


def _trend_at(slope: float, intercept: float, cycles: np.ndarray) -> np.ndarray:
    return slope * cycles.astype(float) + intercept


def _exp_decay(k: np.ndarray, a: float, lam: float) -> np.ndarray:
    return a * np.exp(-k / lam)


@dataclass
class BlockRecoveryFit:
    """Recovery fit for one RPT block."""

    block_id: int
    block_start: int
    block_end: int
    block_cycles: list[int]
    n_pre_routine: int
    n_post_routine: int
    rpt_recovery_amplitude: float | None = None  # A [% SoHQ or same unit as Q]
    rpt_recovery_decay_cycles: float | None = None  # λ [cycles]
    rpt_recovery_amplitude_ah: float | None = None
    fit_r2: float | None = None
    fit_rmse: float | None = None
    permanent_step_pct: float | None = None  # residual baseline shift after recovery
    permanent_step_ah: float | None = None
    post_rpt_exclude: int = POST_RPT_EXCLUDE
    q_trend_slope: float | None = None
    q_trend_intercept: float | None = None
    overlay_rel: list[int] = field(default_factory=list)
    overlay_sohq: list[float] = field(default_factory=list)
    overlay_trend: list[float] = field(default_factory=list)
    overlay_corrected: list[float] = field(default_factory=list)
    overlay_recovery: list[float] = field(default_factory=list)
    pre_rpt_anchor_sohq: float | None = None
    pre_rpt_anchor_cycle: float | None = None
    pre_rpt_anchor_n: int = 0
    post_first_sohq: float | None = None
    delta_first_vs_anchor: float | None = None
    pre_rpt_immediate_sohq: float | None = None
    delta_first_vs_immediate: float | None = None
    bump_significant: bool = False


@dataclass
class BumpSegmentMetrics:
    """Fade contamination for one inter-RPT routine segment."""

    segment_id: int
    block_end: int
    next_block_start: int
    anchor_cycle_start: float
    anchor_cycle_end: float
    anchor_sohq_start: float
    anchor_sohq_end: float
    fade_rate_inter_pct_per_cyc: float
    fade_rate_intra_pct_per_cyc: float
    bump_contamination: float
    n_routine_in_segment: int


@dataclass
class OnsetComparison:
    """bump_onset vs knee_onset ordering."""

    bump_onset_block_id: int | None
    bump_onset_cycle: float | None
    bump_onset_amplitude: float | None
    knee_onset_cycle: float | None
    knee_onset_method: str | None
    bump_precedes_knee: bool | None
    cycle_gap: float | None


@dataclass
class RptRecoveryResult:
    """Full RPT recovery analysis for one cell."""

    cell_id: str | None
    baseline_cycle: int
    n_blocks: int
    blocks: list[BlockRecoveryFit]
    series: pd.DataFrame
    contamination: pd.DataFrame
    post_window: int = 20
    anchors: pd.DataFrame = field(default_factory=pd.DataFrame)
    bump_segments: pd.DataFrame = field(default_factory=pd.DataFrame)
    onset: OnsetComparison | None = None
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT

    def blocks_table(self) -> pd.DataFrame:
        rows = []
        for b in self.blocks:
            rows.append({
                "block_id": b.block_id,
                "block_start": b.block_start,
                "block_end": b.block_end,
                "block_end_cycle": b.block_end,
                "n_post_routine": b.n_post_routine,
                "pre_rpt_anchor_sohq": b.pre_rpt_anchor_sohq,
                "pre_rpt_anchor_cycle": b.pre_rpt_anchor_cycle,
                "post_first_sohq": b.post_first_sohq,
                "delta_first_vs_anchor": b.delta_first_vs_anchor,
                "pre_rpt_immediate_sohq": b.pre_rpt_immediate_sohq,
                "delta_first_vs_immediate": b.delta_first_vs_immediate,
                "bump_significant": b.bump_significant,
                "rpt_recovery_amplitude": b.rpt_recovery_amplitude,
                "rpt_recovery_decay_cycles": b.rpt_recovery_decay_cycles,
                "rpt_recovery_amplitude_ah": b.rpt_recovery_amplitude_ah,
                "permanent_step_pct": b.permanent_step_pct,
                "permanent_step_ah": b.permanent_step_ah,
                "fit_r2": b.fit_r2,
                "fit_rmse": b.fit_rmse,
                "post_rpt_exclude": b.post_rpt_exclude,
            })
        return pd.DataFrame(rows)

    def overlay_table(self) -> pd.DataFrame:
        rows = []
        for b in self.blocks:
            for k, q, tr, corr, rec in zip(
                b.overlay_rel,
                b.overlay_sohq,
                b.overlay_trend,
                b.overlay_corrected,
                b.overlay_recovery,
                strict=True,
            ):
                rows.append({
                    "block_id": b.block_id,
                    "block_end": b.block_end,
                    "rel_cycle": k,
                    "abs_cycle": b.block_end + k,
                    "SoHQ_routine": q,
                    "Q_trend": tr,
                    "SoHQ_corrected": corr,
                    "recovery_component": rec,
                    "life_phase": "early" if b.block_id <= max(1, self.n_blocks // 2) else "late",
                })
        return pd.DataFrame(rows)


def attach_cycle_roles(
    table: pd.DataFrame,
    protocol: ProtocolExclusion,
) -> pd.DataFrame:
    """Label each cycle and split SoHQ into routine vs RPT (C/3 capa) series."""
    out = table.copy()
    flags = protocol.flags.set_index("cycle") if not protocol.flags.empty else pd.DataFrame()

    roles: list[str] = []
    sohq_routine: list[float | None] = []
    sohq_rpt: list[float | None] = []
    sohq_mixed = pd.to_numeric(out.get("SoHQ"), errors="coerce")

    for _, row in out.iterrows():
        cyc = int(row["cycle"])
        sohq = float(sohq_mixed.loc[row.name]) if pd.notna(sohq_mixed.loc[row.name]) else None
        if cyc in protocol.excluded:
            kind = "excluded"
            if cyc in protocol.rpt_cycles:
                kind = "rpt"
            elif cyc in protocol.capa_full_cycles:
                kind = "capa_full"
            elif cyc in protocol.post_rpt_cycles:
                kind = "post_rpt"
        elif cyc in flags.index and bool(flags.loc[cyc, "is_capa_full"]):
            kind = "capa_full"
        elif cyc in flags.index and bool(flags.loc[cyc, "is_rpt"]):
            kind = "rpt"
        else:
            kind = "routine"
        roles.append(kind)
        sohq_routine.append(sohq if kind == "routine" else None)
        sohq_rpt.append(sohq if kind == "capa_full" else None)

    out["cycle_role"] = roles
    out["SoHQ_mixed"] = sohq_mixed
    out["SoHQ_routine"] = sohq_routine
    out["SoHQ_rpt"] = sohq_rpt
    out["protocol_excluded"] = out["cycle"].isin(protocol.excluded)
    return out


def _routine_mask(series: pd.DataFrame) -> pd.Series:
    if "cycle_role" in series.columns:
        return series["cycle_role"] == "routine"
    return ~series.get("protocol_excluded", pd.Series(False, index=series.index))


def _pre_block_routine_cycles(
    series: pd.DataFrame,
    block_start: int,
    *,
    lookback: int = 20,
) -> pd.DataFrame:
    rout = series[_routine_mask(series)].copy()
    rout = rout[rout["cycle"] < block_start].sort_values("cycle")
    if rout.empty:
        return rout
    return rout.tail(lookback)


def _post_block_routine_cycles(
    series: pd.DataFrame,
    block_end: int,
    *,
    window: int,
    next_block_start: int | None,
) -> pd.DataFrame:
    rout = series[_routine_mask(series)].copy()
    rout = rout[rout["cycle"] > block_end].sort_values("cycle")
    if next_block_start is not None:
        rout = rout[rout["cycle"] < next_block_start]
    return rout.head(window)


def _last_routine_before(series: pd.DataFrame, block_start: int) -> tuple[float | None, int | None]:
    rout = series[_routine_mask(series)]
    rout = rout[rout["cycle"] < block_start].sort_values("cycle")
    if rout.empty:
        return None, None
    row = rout.iloc[-1]
    q = pd.to_numeric(row["SoHQ_routine"], errors="coerce")
    if not np.isfinite(q):
        return None, None
    return float(q), int(row["cycle"])


def _pre_rpt_anchor(
    series: pd.DataFrame,
    block_start: int,
    *,
    anchor_width: int = DEFAULT_ANCHOR_WIDTH,
) -> tuple[float | None, float | None, int]:
    """Mean SoHQ_routine over the last `anchor_width` routine cycles before block_start."""
    pre = _pre_block_routine_cycles(series, block_start, lookback=anchor_width)
    if pre.empty:
        return None, None, 0
    q = pd.to_numeric(pre["SoHQ_routine"], errors="coerce").dropna()
    if q.empty:
        return None, None, 0
    cyc = pd.to_numeric(pre["cycle"], errors="coerce").dropna()
    return float(q.mean()), float(cyc.mean()), int(len(q))


def compute_pre_rpt_anchors(
    blocks: list[BlockRecoveryFit],
    *,
    anchor_width: int = DEFAULT_ANCHOR_WIDTH,
) -> pd.DataFrame:
    rows = []
    for b in blocks:
        rows.append({
            "block_id": b.block_id,
            "block_start": b.block_start,
            "block_end": b.block_end,
            "anchor_cycle": b.pre_rpt_anchor_cycle,
            "anchor_sohq": b.pre_rpt_anchor_sohq,
            "anchor_n": b.pre_rpt_anchor_n,
            "anchor_width_target": anchor_width,
        })
    return pd.DataFrame(rows)


def compute_bump_contamination(
    series: pd.DataFrame,
    blocks: list[BlockRecoveryFit],
) -> pd.DataFrame:
    """Per inter-RPT segment: intra vs inter-block fade rates."""
    rows: list[dict] = []
    for i, b in enumerate(blocks):
        if b.pre_rpt_anchor_sohq is None or b.pre_rpt_anchor_cycle is None:
            continue
        if i + 1 >= len(blocks):
            break
        nxt = blocks[i + 1]
        if nxt.pre_rpt_anchor_sohq is None or nxt.pre_rpt_anchor_cycle is None:
            continue

        rout = series[_routine_mask(series)].sort_values("cycle")
        seg = rout[(rout["cycle"] > b.block_end) & (rout["cycle"] < nxt.block_start)]
        if len(seg) < 5:
            continue

        seg_cyc = seg["cycle"].to_numpy(dtype=float)
        seg_q = pd.to_numeric(seg["SoHQ_routine"], errors="coerce").to_numpy(dtype=float)
        slope_intra, _ = _linear_trend(seg_cyc, seg_q)

        dc = nxt.pre_rpt_anchor_cycle - b.pre_rpt_anchor_cycle
        dq = nxt.pre_rpt_anchor_sohq - b.pre_rpt_anchor_sohq
        if abs(dc) < 1e-9:
            continue
        slope_inter = dq / dc

        contam = float("nan")
        if abs(slope_inter) > 1e-9:
            contam = slope_intra / slope_inter - 1.0

        rows.append({
            "segment_id": i + 1,
            "block_end": b.block_end,
            "next_block_start": nxt.block_start,
            "anchor_cycle_start": b.pre_rpt_anchor_cycle,
            "anchor_cycle_end": nxt.pre_rpt_anchor_cycle,
            "anchor_sohq_start": b.pre_rpt_anchor_sohq,
            "anchor_sohq_end": nxt.pre_rpt_anchor_sohq,
            "fade_rate_intra_pct_per_cyc": slope_intra,
            "fade_rate_inter_pct_per_cyc": slope_inter,
            "bump_contamination": contam,
            "n_routine_in_segment": len(seg),
        })
    return pd.DataFrame(rows)


def detect_bump_onset(
    blocks: list[BlockRecoveryFit],
    *,
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT,
    min_fit_r2: float = 0.0,
) -> tuple[int | None, float | None, float | None]:
    """First block where fitted A exceeds Q_relax noise floor."""
    for b in blocks:
        a = b.rpt_recovery_amplitude
        r2 = b.fit_r2
        if a is None or a < noise_floor_pct:
            continue
        if r2 is not None and r2 < min_fit_r2:
            continue
        return b.block_id, float(b.block_start), float(a)
    return None, None, None


def detect_knee_onset_curvature(
    corrected: pd.DataFrame,
    *,
    sohq_col: str = "SoHQ_corrected",
    sigma_mult: float = 3.0,
    min_cycle: float = 100.0,
) -> tuple[float | None, str]:
    """First cycle where |d2 SoHQ/dN2| exceeds sigma_mult * noise sigma (routine only)."""
    rout = corrected[_routine_mask(corrected)].copy()
    rout = rout.dropna(subset=[sohq_col]).sort_values("cycle")
    if len(rout) < 40:
        return None, "insufficient_points"

    cyc = rout["cycle"].to_numpy(dtype=float)
    y = pd.to_numeric(rout[sohq_col], errors="coerce").to_numpy(dtype=float)
    n = len(y)
    win = max(11, n // 10)
    if win % 2 == 0:
        win += 1
    win = min(win, n - 2 if (n - 2) % 2 == 1 else n - 3)
    if win < 5:
        return None, "window_too_small"

    try:
        from scipy.signal import savgol_filter
        y_s = savgol_filter(y, win, 3)
    except ImportError:
        y_s = y

    d1 = np.gradient(y_s, cyc)
    d2 = np.gradient(d1, cyc)
    early = d2[: max(20, n // 5)]
    early = early[np.isfinite(early)]
    if len(early) < 5:
        return None, "noise_est_fail"
    sigma = float(np.nanstd(early))
    if sigma <= 0:
        sigma = float(np.nanmedian(np.abs(early - np.nanmedian(early)))) * 1.4826
    thr = sigma_mult * sigma

    for i in range(len(d2)):
        if cyc[i] < min_cycle:
            continue
        if np.isfinite(d2[i]) and abs(d2[i]) > thr:
            return float(cyc[i]), "d2_sohq_3sigma"
    return None, "no_exceedance"


def compare_bump_knee_onset(
    blocks: list[BlockRecoveryFit],
    corrected: pd.DataFrame,
    *,
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT,
) -> OnsetComparison:
    bid, bcyc, amp = detect_bump_onset(blocks, noise_floor_pct=noise_floor_pct, min_fit_r2=0.5)
    knee_cyc, knee_method = detect_knee_onset_curvature(corrected)
    precedes = None
    gap = None
    if bcyc is not None and knee_cyc is not None:
        precedes = bcyc < knee_cyc
        gap = knee_cyc - bcyc
    return OnsetComparison(
        bump_onset_block_id=bid,
        bump_onset_cycle=bcyc,
        bump_onset_amplitude=amp,
        knee_onset_cycle=knee_cyc,
        knee_onset_method=knee_method,
        bump_precedes_knee=precedes,
        cycle_gap=gap,
    )


def fit_block_recovery(
    series: pd.DataFrame,
    block: list[int],
    *,
    block_id: int,
    baseline_dchg_ah: float,
    post_window: int = 20,
    pre_lookback: int = 20,
    next_block_start: int | None = None,
    post_rpt_exclude: int = POST_RPT_EXCLUDE,
    anchor_width: int = DEFAULT_ANCHOR_WIDTH,
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT,
) -> BlockRecoveryFit:
    """Fit exponential recovery after one RPT block."""
    block_start = int(block[0])
    block_end = int(block[-1])
    fit = BlockRecoveryFit(
        block_id=block_id,
        block_start=block_start,
        block_end=block_end,
        block_cycles=[int(c) for c in block],
        n_pre_routine=0,
        n_post_routine=0,
    )

    pre = _pre_block_routine_cycles(series, block_start, lookback=pre_lookback)
    post = _post_block_routine_cycles(
        series,
        block_end,
        window=post_window,
        next_block_start=next_block_start,
    )
    fit.n_pre_routine = len(pre)
    fit.n_post_routine = len(post)

    anchor_q, anchor_cyc, anchor_n = _pre_rpt_anchor(series, block_start, anchor_width=anchor_width)
    fit.pre_rpt_anchor_sohq = anchor_q
    fit.pre_rpt_anchor_cycle = anchor_cyc
    fit.pre_rpt_anchor_n = anchor_n

    if len(post) >= 1:
        first_q = float(pd.to_numeric(post.iloc[0]["SoHQ_routine"], errors="coerce"))
        if np.isfinite(first_q):
            fit.post_first_sohq = first_q
            if anchor_q is not None:
                fit.delta_first_vs_anchor = first_q - anchor_q
            imm_q, _ = _last_routine_before(series, block_start)
            if imm_q is not None:
                fit.pre_rpt_immediate_sohq = imm_q
                fit.delta_first_vs_immediate = first_q - imm_q

    if len(pre) < 2 or len(post) < 4:
        return fit

    pre_cyc = pre["cycle"].to_numpy(dtype=float)
    pre_q = pd.to_numeric(pre["SoHQ_routine"], errors="coerce").to_numpy(dtype=float)
    slope, intercept = _linear_trend(pre_cyc, pre_q)
    fit.q_trend_slope = slope
    fit.q_trend_intercept = intercept

    post_cyc = post["cycle"].to_numpy(dtype=float)
    post_q = pd.to_numeric(post["SoHQ_routine"], errors="coerce").to_numpy(dtype=float)
    rel_k = post_cyc - block_end
    trend_q = _trend_at(slope, intercept, post_cyc)
    residual = post_q - trend_q

    # Initial guesses: A = first point residual, λ = POST_RPT_EXCLUDE
    a0 = max(float(residual[0]), 0.01) if np.isfinite(residual[0]) else 0.5
    lam0 = float(post_rpt_exclude)
    try:
        popt, _ = curve_fit(
            _exp_decay,
            rel_k,
            residual,
            p0=(a0, lam0),
            bounds=([0.0, 0.5], [20.0, 80.0]),
            maxfev=8000,
        )
        a_hat, lam_hat = float(popt[0]), float(popt[1])
        rec_fit = _exp_decay(rel_k, a_hat, lam_hat)
        corrected = post_q - rec_fit
        ss_res = float(np.sum((residual - rec_fit) ** 2))
        ss_tot = float(np.sum((residual - np.mean(residual)) ** 2))
        fit.rpt_recovery_amplitude = a_hat
        fit.rpt_recovery_decay_cycles = lam_hat
        fit.rpt_recovery_amplitude_ah = a_hat / 100.0 * baseline_dchg_ah
        fit.fit_r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else None
        fit.fit_rmse = float(np.sqrt(np.mean((residual - rec_fit) ** 2)))

        # Permanent step: mean corrected SoHQ in tail vs trend at same cycles
        tail_n = min(5, len(corrected))
        tail_corrected = corrected[-tail_n:]
        tail_trend = trend_q[-tail_n:]
        perm = float(np.mean(tail_corrected - tail_trend))
        fit.permanent_step_pct = perm
        fit.permanent_step_ah = perm / 100.0 * baseline_dchg_ah

        fit.overlay_rel = rel_k.astype(int).tolist()
        fit.overlay_sohq = post_q.tolist()
        fit.overlay_trend = trend_q.tolist()
        fit.overlay_corrected = corrected.tolist()
        fit.overlay_recovery = rec_fit.tolist()
        fit.bump_significant = a_hat >= noise_floor_pct and (fit.fit_r2 or 0) >= 0.5
    except (RuntimeError, ValueError):
        pass

    return fit


def build_contamination_report(series: pd.DataFrame, protocol: ProtocolExclusion) -> pd.DataFrame:
    """Quantify how mixed SoHQ differs from routine-only interpolation gaps."""
    rout = series[_routine_mask(series)].sort_values("cycle")
    if rout.empty:
        return pd.DataFrame()

    cyc = rout["cycle"].to_numpy(dtype=float)
    q = pd.to_numeric(rout["SoHQ_routine"], errors="coerce").to_numpy(dtype=float)
    slope, intercept = _linear_trend(cyc, q)

    rows = []
    mixed = pd.to_numeric(series.get("SoHQ_mixed", series.get("SoHQ")), errors="coerce")
    for cyc_i in sorted(protocol.excluded):
        row = series[series["cycle"] == cyc_i]
        if row.empty:
            continue
        m = float(mixed.loc[row.index[0]]) if pd.notna(mixed.loc[row.index[0]]) else None
        trend = float(slope * cyc_i + intercept)
        role = row["cycle_role"].iloc[0] if "cycle_role" in row.columns else "excluded"
        rows.append({
            "cycle": cyc_i,
            "cycle_role": role,
            "SoHQ_mixed": m,
            "SoHQ_routine_interp": trend,
            "delta_mixed_minus_routine": (m - trend) if m is not None else None,
            "in_post_rpt_buffer": cyc_i in protocol.post_rpt_cycles,
        })
    return pd.DataFrame(rows)


def analyze_rpt_recovery(
    table: pd.DataFrame,
    step_df: pd.DataFrame,
    *,
    cell_id: str | None = None,
    baseline_cycle: int | None = None,
    post_window: int = 20,
    pre_lookback: int = 20,
    post_rpt_exclude: int = POST_RPT_EXCLUDE,
    anchor_width: int = DEFAULT_ANCHOR_WIDTH,
    noise_floor_pct: float = Q_RELAX_NOISE_FLOOR_PCT,
) -> RptRecoveryResult:
    """Run full RPT recovery analysis on a stepemd feature table."""
    protocol = build_protocol_exclusion(step_df, post_rpt_exclude=post_rpt_exclude)
    series = attach_cycle_roles(table, protocol)

    base_cyc = baseline_cycle
    if base_cyc is None:
        good = series[_routine_mask(series)]
        good = good[pd.to_numeric(good["dchgCapa"], errors="coerce") > 1.0]
        base_cyc = int(good["cycle"].iloc[0]) if not good.empty else int(series["cycle"].iloc[0])
    base_row = series[series["cycle"] == base_cyc]
    if base_row.empty:
        base_row = series.sort_values("cycle").head(1)
    baseline_dchg = float(base_row.iloc[0]["dchgCapa"])

    blocks: list[BlockRecoveryFit] = []
    rpt_blocks = protocol.rpt_blocks
    # Periodic RPT blocks only (skip isolated cycle-1 flag and end-of-life tail)
    main_blocks = [b for b in rpt_blocks if len(b) >= 3]
    for i, block in enumerate(main_blocks):
        next_start = main_blocks[i + 1][0] if i + 1 < len(main_blocks) else None
        blocks.append(
            fit_block_recovery(
                series,
                block,
                block_id=i + 1,
                baseline_dchg_ah=baseline_dchg,
                post_window=post_window,
                pre_lookback=pre_lookback,
                next_block_start=next_start,
                post_rpt_exclude=post_rpt_exclude,
                anchor_width=anchor_width,
                noise_floor_pct=noise_floor_pct,
            )
        )

    contamination = build_contamination_report(series, protocol)
    anchors = compute_pre_rpt_anchors(blocks, anchor_width=anchor_width)
    bump_segments = compute_bump_contamination(series, blocks)
    corrected = apply_recovery_correction(
        RptRecoveryResult(
            cell_id=cell_id,
            baseline_cycle=base_cyc,
            n_blocks=len(blocks),
            blocks=blocks,
            series=series,
            contamination=contamination,
            post_window=post_window,
            noise_floor_pct=noise_floor_pct,
        )
    )
    onset = compare_bump_knee_onset(blocks, corrected, noise_floor_pct=noise_floor_pct)

    return RptRecoveryResult(
        cell_id=cell_id,
        baseline_cycle=base_cyc,
        n_blocks=len(blocks),
        blocks=blocks,
        series=series,
        contamination=contamination,
        post_window=post_window,
        anchors=anchors,
        bump_segments=bump_segments,
        onset=onset,
        noise_floor_pct=noise_floor_pct,
    )


def apply_recovery_correction(
    result: RptRecoveryResult,
) -> pd.DataFrame:
    """Return per-cycle table with SoHQ_corrected (routine + model-subtracted post-RPT)."""
    out = result.series.copy()
    out["SoHQ_corrected"] = out["SoHQ_routine"]
    out["recovery_component"] = 0.0

    for b in result.blocks:
        if b.rpt_recovery_amplitude is None or b.rpt_recovery_decay_cycles is None:
            continue
        if not b.overlay_rel:
            continue
        a = b.rpt_recovery_amplitude
        lam = b.rpt_recovery_decay_cycles
        slope = b.q_trend_slope or 0.0
        intercept = b.q_trend_intercept or 0.0
        for k, q, corr, rec in zip(
            b.overlay_rel,
            b.overlay_sohq,
            b.overlay_corrected,
            b.overlay_recovery,
            strict=True,
        ):
            cyc = b.block_end + k
            mask = out["cycle"] == cyc
            if not mask.any():
                continue
            out.loc[mask, "SoHQ_corrected"] = corr
            out.loc[mask, "recovery_component"] = rec
            out.loc[mask, "Q_trend"] = slope * cyc + intercept

    return out
