"""ML soft-map: which 0.33C RPT peaks overlap / collapse on 0.5C routine bumps."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from cyclediag.features.dqdv_peaks import (
    DqdvPeakConfig,
    find_dqdv_peaks_prepared,
    prepare_dqdv_arrays,
    _smooth,
)
from cyclediag.features.dqdv_segment import prepare_leg_segment_for_dqdv
from cyclediag.features.rpt_anchor import (
    RptAnchorConfig,
    RptCheckpoint,
    RateShift,
    _capacity_col,
    _extract_leg_peaks,
)
from cyclediag.features.segment_utils import leg_segment
from cyclediag.io.cycle_protocol import ProtocolExclusion


@dataclass
class RptOverlapConfig:
    """Train / soft-map settings for 0.33C → 0.5C peak overlap."""

    n_estimators: int = 160
    random_state: int = 42
    soft_radius_v: float = 0.12
    collapse_score_min: float = 0.18
    share_frac_of_best: float = 0.55
    hard_zone_half: int = 10
    n_pairs_train_cap: int = 8000
    sg_window_rpt: int = 21
    sg_window_routine: int = 31


@dataclass
class RptOverlapBundle:
    """Per-leg RF classifying peak_id from V/H (+ rate code)."""

    rf_models: dict[str, Pipeline] = field(default_factory=dict)
    peak_ids: dict[str, list[str]] = field(default_factory=dict)
    rate_shift_lookup: dict[tuple[int, str, str], float] = field(default_factory=dict)
    config: RptOverlapConfig = field(default_factory=RptOverlapConfig)
    train_rows: int = 0
    training_meta: dict[str, Any] = field(default_factory=dict)

    def save(self, out_dir: str | Path) -> Path:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "rf_models": self.rf_models,
                "peak_ids": self.peak_ids,
                "rate_shift_lookup": {
                    f"{k[0]}|{k[1]}|{k[2]}": v for k, v in self.rate_shift_lookup.items()
                },
                "config": asdict(self.config),
                "train_rows": self.train_rows,
                "training_meta": self.training_meta,
            },
            out_dir / "rpt_overlap_model.joblib",
        )
        (out_dir / "rpt_overlap_meta.json").write_text(
            json.dumps(
                {
                    "train_rows": self.train_rows,
                    "peak_ids": self.peak_ids,
                    "config": asdict(self.config),
                    "training_meta": self.training_meta,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return out_dir

    @classmethod
    def load(cls, model_dir: str | Path) -> RptOverlapBundle:
        raw = joblib.load(Path(model_dir) / "rpt_overlap_model.joblib")
        cfg = RptOverlapConfig(**{
            k: v for k, v in dict(raw.get("config", {})).items()
            if k in RptOverlapConfig.__dataclass_fields__
        })
        lookup_raw = dict(raw.get("rate_shift_lookup", {}))
        lookup: dict[tuple[int, str, str], float] = {}
        for key, val in lookup_raw.items():
            life, leg, pid = str(key).split("|", 2)
            lookup[(int(life), leg, pid)] = float(val)
        return cls(
            rf_models=dict(raw.get("rf_models", {})),
            peak_ids=dict(raw.get("peak_ids", {})),
            rate_shift_lookup=lookup,
            config=cfg,
            train_rows=int(raw.get("train_rows", 0)),
            training_meta=dict(raw.get("training_meta", {})),
        )


def _feat_row(v: float, h: float, rate_c: float) -> list[float]:
    h_abs = abs(float(h))
    return [float(v), float(h), h_abs, float(np.log1p(h_abs)), float(rate_c)]


def _leg_curve(
    df: pd.DataFrame,
    cycle: int,
    leg: str,
    *,
    sg_window: int,
) -> tuple[np.ndarray, np.ndarray] | None:
    cyc = df[df["cycle"] == int(cycle)]
    if cyc.empty:
        return None
    seg = leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge")
    seg = prepare_leg_segment_for_dqdv(seg, leg)
    col = _capacity_col(seg, leg)
    if seg.empty or col is None or "voltage" not in seg.columns:
        return None
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
    dqcfg = DqdvPeakConfig(sg_window=sg_window)
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
    if len(vx) < 5:
        return None
    y = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)
    m = np.isfinite(vx) & np.isfinite(y)
    return vx[m], y[m]


def _unbanded_peaks(
    df: pd.DataFrame,
    cycle: int,
    leg: str,
    *,
    sg_window: int,
    max_peaks: int = 12,
) -> list[dict]:
    cyc = df[df["cycle"] == int(cycle)]
    if cyc.empty:
        return []
    seg = prepare_leg_segment_for_dqdv(
        leg_segment(cyc, leg, charge_text="charge", discharge_text="discharge"),
        leg,
    )
    col = _capacity_col(seg, leg)
    if seg.empty or col is None:
        return []
    v = pd.to_numeric(seg["voltage"], errors="coerce").to_numpy(dtype=float)
    q = pd.to_numeric(seg[col], errors="coerce").to_numpy(dtype=float)
    dqcfg = DqdvPeakConfig(sg_window=sg_window)
    vx, dqdv, _, _ = prepare_dqdv_arrays(v, q, dqcfg)
    if len(vx) < 5:
        return []
    y = _smooth(dqdv, window=dqcfg.sg_window, poly=dqcfg.sg_poly)
    return find_dqdv_peaks_prepared(vx, dqdv, y, max_peaks=max_peaks, config=dqcfg)


def _shift_mV(shifts: list[RateShift], life: int, leg: str, peak_id: str) -> float:
    hits = [
        s for s in shifts
        if int(s.life_cycle) == int(life) and s.leg == leg and s.peak_id == peak_id
    ]
    if not hits:
        same = [s for s in shifts if s.leg == leg and s.peak_id == peak_id]
        if not same:
            return 0.0
        return float(min(same, key=lambda s: abs(int(s.life_cycle) - int(life))).delta_v_mV)
    return float(hits[0].delta_v_mV)


def build_overlap_training_rows(
    df: pd.DataFrame,
    checkpoints: list[RptCheckpoint],
    shifts: list[RateShift],
    protocol: ProtocolExclusion,
    *,
    config: RptOverlapConfig | None = None,
    legs: tuple[str, ...] = ("charge", "discharge"),
) -> pd.DataFrame:
    """Labeled rows: 0.33C band peaks + hard-zone 0.5C peaks nearest rate-shifted V."""
    config = config or RptOverlapConfig()
    anchor_cfg = RptAnchorConfig(
        sg_window_rpt=config.sg_window_rpt,
        sg_window_routine=config.sg_window_routine,
    )
    rows: list[dict] = []

    if protocol.flags.empty:
        routine: list[int] = []
    else:
        routine = sorted(
            int(c)
            for c in protocol.flags.loc[
                (~protocol.flags["cycle"].isin(protocol.excluded))
                & (protocol.flags["protocol_kind"] == "routine"),
                "cycle",
            ]
        )

    for ckpt in checkpoints:
        if not ckpt.peaks:
            continue
        for leg in legs:
            for raw_cyc in ckpt.anchor_raw_cycles:
                for pk in _extract_leg_peaks(
                    df, int(raw_cyc), leg, config=anchor_cfg, for_rpt=True,
                ):
                    pid = str(pk.get("peak_id", pk.get("band", "")))
                    if not pid:
                        continue
                    rows.append({
                        "source": "rpt_0p33",
                        "life_cycle": ckpt.life_cycle,
                        "cycle": int(raw_cyc),
                        "leg": leg,
                        "peak_id": pid,
                        "V": float(pk["V"]),
                        "H": float(pk["H"]),
                        "rate_c": 0.33,
                        "V_expected": float(pk["V"]),
                    })

        lo = ckpt.life_cycle - config.hard_zone_half
        hi = ckpt.life_cycle + config.hard_zone_half
        near = [c for c in routine if lo <= c <= hi]
        for leg in legs:
            refs = ckpt.peaks.get(leg) or []
            if not refs:
                continue
            for rc in near:
                cands = _unbanded_peaks(
                    df, rc, leg, sg_window=config.sg_window_routine, max_peaks=12,
                )
                if not cands:
                    continue
                used: set[int] = set()
                for ref in refs:
                    d_mV = _shift_mV(shifts, ckpt.life_cycle, leg, ref.peak_id)
                    v_exp = float(ref.V) + d_mV / 1000.0
                    best_i, best_dv = None, 1e9
                    for i, cand in enumerate(cands):
                        if i in used:
                            continue
                        dv = abs(float(cand["V"]) - v_exp)
                        if dv < best_dv:
                            best_dv, best_i = dv, i
                    if best_i is None or best_dv > config.soft_radius_v:
                        continue
                    used.add(best_i)
                    cand = cands[best_i]
                    rows.append({
                        "source": "routine_0p5",
                        "life_cycle": ckpt.life_cycle,
                        "cycle": int(rc),
                        "leg": leg,
                        "peak_id": ref.peak_id,
                        "V": float(cand["V"]),
                        "H": float(cand["H"]),
                        "rate_c": 0.5,
                        "V_expected": v_exp,
                        "delta_v_to_exp": float(cand["V"]) - v_exp,
                    })

    out = pd.DataFrame(rows)
    if len(out) > config.n_pairs_train_cap:
        out = out.sample(config.n_pairs_train_cap, random_state=config.random_state)
    return out.reset_index(drop=True)


def train_rpt_overlap_model(
    train_df: pd.DataFrame,
    shifts: list[RateShift],
    *,
    config: RptOverlapConfig | None = None,
) -> RptOverlapBundle:
    """Train per-leg RF: features [V, H, H_abs, logH, rate_c] → peak_id."""
    config = config or RptOverlapConfig()
    rf_models: dict[str, Pipeline] = {}
    peak_ids: dict[str, list[str]] = {}
    if train_df.empty:
        return RptOverlapBundle(config=config)

    for leg, grp in train_df.groupby("leg"):
        labels = grp["peak_id"].astype(str)
        if labels.nunique() < 2 or len(grp) < 8:
            continue
        X = np.array(
            [_feat_row(r.V, r.H, r.rate_c) for r in grp.itertuples()],
            dtype=float,
        )
        y = labels.to_numpy()
        pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("rf", RandomForestClassifier(
                n_estimators=config.n_estimators,
                random_state=config.random_state,
                class_weight="balanced_subsample",
                min_samples_leaf=2,
            )),
        ])
        pipe.fit(X, y)
        rf_models[str(leg)] = pipe
        peak_ids[str(leg)] = sorted(labels.unique().tolist())

    lookup = {
        (int(s.life_cycle), s.leg, s.peak_id): float(s.delta_v_mV) for s in shifts
    }
    return RptOverlapBundle(
        rf_models=rf_models,
        peak_ids=peak_ids,
        rate_shift_lookup=lookup,
        config=config,
        train_rows=len(train_df),
        training_meta={
            "n_rpt": int((train_df["source"] == "rpt_0p33").sum()),
            "n_routine": int((train_df["source"] == "routine_0p5").sum()),
            "legs": sorted(train_df["leg"].unique().tolist()),
        },
    )


def _rf_proba(model: Pipeline | None, v: float, h: float, rate_c: float) -> dict[str, float]:
    if model is None:
        return {}
    proba = model.predict_proba(np.array([_feat_row(v, h, rate_c)], dtype=float))[0]
    classes = [str(c) for c in model.named_steps["rf"].classes_]
    return {c: float(p) for c, p in zip(classes, proba)}


def soft_map_checkpoint(
    df: pd.DataFrame,
    ckpt: RptCheckpoint,
    shifts: list[RateShift],
    bundle: RptOverlapBundle,
    *,
    routine_cycle: int | None = None,
    legs: tuple[str, ...] = ("charge", "discharge"),
) -> pd.DataFrame:
    """Soft scores: each 0.5C candidate × each 0.33C peak_id at one checkpoint."""
    config = bundle.config
    life = int(ckpt.life_cycle)
    rout = int(routine_cycle if routine_cycle is not None else life)
    rows: list[dict] = []

    for leg in legs:
        refs = ckpt.peaks.get(leg) or []
        if not refs:
            continue
        cands = _unbanded_peaks(
            df, rout, leg, sg_window=config.sg_window_routine, max_peaks=12,
        )
        if not cands:
            continue
        model = bundle.rf_models.get(leg)
        for ci, cand in enumerate(cands):
            rf_map = _rf_proba(model, float(cand["V"]), float(cand["H"]), 0.5)
            for ref in refs:
                d_mV = _shift_mV(shifts, life, leg, ref.peak_id)
                v_exp = float(ref.V) + d_mV / 1000.0
                dv = float(cand["V"]) - v_exp
                geom = float(np.exp(-abs(dv) / max(config.soft_radius_v, 1e-3)))
                if abs(dv) > config.soft_radius_v * 1.5:
                    geom = 0.0
                rf_p = float(rf_map.get(ref.peak_id, 0.0))
                score = 0.55 * rf_p + 0.45 * geom
                rows.append({
                    "life_cycle": life,
                    "routine_cycle": rout,
                    "rpt_cycle": int(ckpt.anchor_raw_cycle),
                    "leg": leg,
                    "cand_idx": ci,
                    "cand_V": float(cand["V"]),
                    "cand_H": float(cand["H"]),
                    "rpt_peak_id": ref.peak_id,
                    "rpt_V": float(ref.V),
                    "rpt_H": float(ref.H),
                    "V_expected_0p5": v_exp,
                    "delta_v": dv,
                    "geom_score": geom,
                    "rf_proba": rf_p,
                    "score": score,
                })
    return pd.DataFrame(rows)


def detect_collapses(
    soft_df: pd.DataFrame,
    *,
    config: RptOverlapConfig | None = None,
) -> pd.DataFrame:
    """Find 0.5C bumps that absorb 2+ 0.33C peak identities."""
    config = config or RptOverlapConfig()
    if soft_df.empty:
        return pd.DataFrame()

    collapses: list[dict] = []
    for (life, rout, leg), grp in soft_df.groupby(["life_cycle", "routine_cycle", "leg"]):
        for cand_idx, g in grp.groupby("cand_idx"):
            g = g.sort_values("score", ascending=False)
            best = float(g.iloc[0]["score"])
            if best < config.collapse_score_min:
                continue
            share = g[
                g["score"] >= max(config.collapse_score_min, best * config.share_frac_of_best)
            ]
            pids = sorted(share["rpt_peak_id"].astype(str).unique().tolist())
            if len(pids) < 2:
                continue
            collapses.append({
                "life_cycle": int(life),
                "routine_cycle": int(rout),
                "leg": leg,
                "cand_idx": int(cand_idx),
                "cand_V": float(g.iloc[0]["cand_V"]),
                "cand_H": float(g.iloc[0]["cand_H"]),
                "n_rpt_peaks": len(pids),
                "rpt_peak_ids": ",".join(pids),
                "best_score": best,
                "member_scores": ",".join(
                    f"{r.rpt_peak_id}:{r.score:.2f}" for r in share.itertuples()
                ),
            })
    if not collapses:
        return pd.DataFrame()
    return pd.DataFrame(collapses).sort_values(
        ["life_cycle", "leg", "cand_V"]
    ).reset_index(drop=True)


def best_rpt_links(soft_df: pd.DataFrame) -> pd.DataFrame:
    """Each RPT peak → best 0.5C candidate (many-to-one allowed)."""
    if soft_df.empty:
        return pd.DataFrame()
    rows = []
    for (life, rout, leg), grp in soft_df.groupby(["life_cycle", "routine_cycle", "leg"]):
        for pid, g in grp.groupby("rpt_peak_id"):
            top = g.sort_values("score", ascending=False).iloc[0]
            rows.append({
                "life_cycle": int(life),
                "routine_cycle": int(rout),
                "leg": leg,
                "rpt_peak_id": str(pid),
                "rpt_V": float(top["rpt_V"]),
                "cand_idx": int(top["cand_idx"]),
                "cand_V": float(top["cand_V"]),
                "V_expected_0p5": float(top["V_expected_0p5"]),
                "score": float(top["score"]),
                "rf_proba": float(top["rf_proba"]),
                "geom_score": float(top["geom_score"]),
            })
    return pd.DataFrame(rows)


def build_rpt_overlap_artifacts(
    df: pd.DataFrame,
    checkpoints: list[RptCheckpoint],
    shifts: list[RateShift],
    protocol: ProtocolExclusion,
    *,
    config: RptOverlapConfig | None = None,
    legs: tuple[str, ...] = ("charge", "discharge"),
) -> tuple[RptOverlapBundle, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Train + soft-map all checkpoints. Returns bundle, train, soft, links, collapses."""
    config = config or RptOverlapConfig()
    train_df = build_overlap_training_rows(
        df, checkpoints, shifts, protocol, config=config, legs=legs,
    )
    bundle = train_rpt_overlap_model(train_df, shifts, config=config)
    soft_parts: list[pd.DataFrame] = []
    for ckpt in checkpoints:
        if not ckpt.peaks:
            continue
        soft_parts.append(
            soft_map_checkpoint(
                df, ckpt, shifts, bundle, routine_cycle=ckpt.life_cycle, legs=legs,
            )
        )
    soft_df = pd.concat(soft_parts, ignore_index=True) if soft_parts else pd.DataFrame()
    links = best_rpt_links(soft_df)
    collapses = detect_collapses(soft_df, config=config)
    return bundle, train_df, soft_df, links, collapses


def plot_overlap_overlay(
    df: pd.DataFrame,
    ckpt: RptCheckpoint,
    soft_df: pd.DataFrame,
    collapses: pd.DataFrame,
    *,
    leg: str = "discharge",
    routine_cycle: int | None = None,
    config: RptOverlapConfig | None = None,
):
    """dQ/dV overlay: 0.33C vs 0.5C with collapse / soft-link annotations."""
    import matplotlib.pyplot as plt

    config = config or RptOverlapConfig()
    rout = int(routine_cycle if routine_cycle is not None else ckpt.life_cycle)
    rpt_cyc = int(ckpt.anchor_raw_cycles[-1]) if ckpt.anchor_raw_cycles else int(ckpt.anchor_raw_cycle)

    rpt_curve = _leg_curve(df, rpt_cyc, leg, sg_window=config.sg_window_rpt)
    rout_curve = _leg_curve(df, rout, leg, sg_window=config.sg_window_routine)
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    if rpt_curve is not None:
        ax.plot(rpt_curve[0], rpt_curve[1], color="#1f77b4", lw=1.6, label=f"0.33C TC{rpt_cyc}")
    if rout_curve is not None:
        ax.plot(rout_curve[0], rout_curve[1], color="#d62728", lw=1.6, alpha=0.9, label=f"0.5C TC{rout}")

    sub = pd.DataFrame()
    if soft_df is not None and not soft_df.empty:
        sub = soft_df[
            (soft_df["life_cycle"] == ckpt.life_cycle)
            & (soft_df["routine_cycle"] == rout)
            & (soft_df["leg"] == leg)
        ]
    links = best_rpt_links(sub) if not sub.empty else pd.DataFrame()

    collapsed_cands: set[int] = set()
    y_top = 0.0
    if rout_curve is not None and len(rout_curve[1]):
        y_top = float(np.nanmax(np.abs(rout_curve[1])))
    if rpt_curve is not None and len(rpt_curve[1]):
        y_top = max(y_top, float(np.nanmax(np.abs(rpt_curve[1]))))

    if collapses is not None and not collapses.empty:
        csub = collapses[
            (collapses["life_cycle"] == ckpt.life_cycle)
            & (collapses["routine_cycle"] == rout)
            & (collapses["leg"] == leg)
        ]
        for r in csub.itertuples():
            collapsed_cands.add(int(r.cand_idx))
            ax.axvline(float(r.cand_V), color="#9467bd", ls="--", lw=1.4, alpha=0.85)
            ax.text(
                float(r.cand_V),
                y_top * 0.92 if y_top else 0.0,
                f"overlap\n{r.rpt_peak_ids}",
                color="#9467bd",
                fontsize=8,
                ha="center",
                va="top",
            )

    for r in links.itertuples() if not links.empty else []:
        color = "#9467bd" if int(r.cand_idx) in collapsed_cands else "#2ca02c"
        ax.scatter([float(r.rpt_V)], [0.0], color="#1f77b4", s=28, zorder=5)
        ax.scatter(
            [float(r.cand_V)],
            [0.0],
            color=color,
            s=36,
            zorder=5,
            marker="s" if int(r.cand_idx) in collapsed_cands else "o",
        )
        ax.annotate(
            str(r.rpt_peak_id),
            (float(r.rpt_V), 0.0),
            textcoords="offset points",
            xytext=(0, 8),
            fontsize=7,
            color="#1f77b4",
            ha="center",
        )

    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("dQ/dV (Ah/V)")
    ax.set_title(
        f"Life {ckpt.life_cycle} {leg}: 0.33C peaks → 0.5C bumps "
        "(purple = collapsed / overlap)"
    )
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig
