"""DOE arm comparison — especially DOE2 (SJ900 vs SJ1300, same cathode / different anode).

Early-cycle parameter contrast + degradation-mode trajectory divergence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

# Key indicators for anode-driven differences (DOE2 narrative)
EARLY_PARAM_CANDIDATES: tuple[str, ...] = (
    "SoHQ",
    "CE",
    "CE_rev",
    "CE_local_20",
    "VE",
    "hyst_mean",
    "hyst_area",
    "hyst_area_SOC20",
    "hyst_area_SOC50",
    "hyst_area_SOC80",
    "EoD_chgR_0p1s",
    "EoD_chgR_10s",
    "EoD_chgR_30s",
    "EoD_chgR_60s",
    "EoD_chgR_R10_minus_R0p1",
    "EoD_chgR_R30_minus_R0p1",
    "EoC_dchgR_0p1s",
    "EoC_dchgR_10s",
    "EoC_dchgR_30s",
    "EoC_dchgR_60s",
    "EoC_dchgR_R10_minus_R0p1",
    "EoC_dchgR_R30_minus_R0p1",
    "dchg_Q_low_frac",
    "dchg_Q_high_frac",
    "dchg_f_graphite_proxy",
    "dchg_dQdV_peak1_V",
    "dchg_dQdV_peak2_V",
    "dchg_dQdV_peak3_V",
    "chg_dQdV_peak1_V",
    "chg_dQdV_peak2_V",
    "chg_dQdV_peak3_V",
    "dchgCapa",
    "chgCapa",
    "Q_CV_norm",
    "tau_CV",
    "R_30s_total_soc20",
    "R_30s_total_soc50",
    "R_30s_total_soc80",
    "R_SOC_diff_20_80",
    "R_SOC_slope",
    "PER",
)


@dataclass
class DoeArm:
    """One comparison arm (e.g. SJ900_dry)."""

    arm_id: str
    label: str
    anode: str
    cathode: str
    paths: list[Path] = field(default_factory=list)


@dataclass
class DoeCompareConfig:
    doe_id: str = "DOE2"
    early_cycles: int = 30
    mid_cycle: int = 100
    late_frac: float = 0.2
    fixtures_root: Path | None = None
    out_dir: Path | None = None
    run_diagnosis: bool = True
    write_plots: bool = True
    encoding: str = "cp949"
    # If set, only extract these cycles (faster smoke). None = all cycles.
    cycles: list[int] | None = None


def _repo_fixtures_root() -> Path:
    """Prefer workspace example/fixtures, then package-adjacent github clone layout."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "example" / "fixtures",  # …/Cursor/example/fixtures
        here.parents[1].parent / "example" / "fixtures",
        Path.cwd() / "example" / "fixtures",
    ]
    for c in candidates:
        if (c / "manifest.json").exists() or (c / "doe").exists():
            return c
    return candidates[0]


def _cell_id_from_path(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_raw"):
        stem = stem[: -len("_raw")]
    return stem


def load_doe2_arms(fixtures_root: Path | None = None) -> tuple[DoeArm, DoeArm]:
    """SJ900 dry (DOE1 set4, provisional) vs SJ1300 dry (DOE2)."""
    root = Path(fixtures_root) if fixtures_root else _repo_fixtures_root()
    sj900_dir = root / "doe" / "DOE1" / "set4_SJ900"
    sj1300_dir = root / "doe" / "DOE2" / "SJ1300_dry"
    sj900_paths = sorted(sj900_dir.glob("*_raw.csv")) if sj900_dir.is_dir() else []
    sj1300_paths = sorted(sj1300_dir.glob("*_raw.csv")) if sj1300_dir.is_dir() else []
    if not sj900_paths:
        raise FileNotFoundError(
            f"DOE2 SJ900 arm not found under {sj900_dir} "
            "(provisional dry = DOE1/set4_SJ900)"
        )
    if not sj1300_paths:
        raise FileNotFoundError(f"DOE2 SJ1300 arm not found under {sj1300_dir}")

    arm_a = DoeArm(
        arm_id="SJ900_dry",
        label="SJ900 (dry, provisional set4)",
        anode="SJ900 / ASG903-family",
        cathode="S83S (same)",
        paths=sj900_paths,
    )
    arm_b = DoeArm(
        arm_id="SJ1300_dry",
        label="SJ1300 dry",
        anode="SJ1300",
        cathode="S83S (same)",
        paths=sj1300_paths,
    )
    return arm_a, arm_b


def load_doe_arms_from_manifest(
    doe_id: str,
    fixtures_root: Path | None = None,
) -> list[DoeArm]:
    """Generic loader; DOE2 uses special SJ900 ref from sibling DOE1."""
    if doe_id.upper() == "DOE2":
        return list(load_doe2_arms(fixtures_root))

    root = Path(fixtures_root) if fixtures_root else _repo_fixtures_root()
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cells = [c for c in manifest.get("cells", []) if c.get("doe") == doe_id]
    if not cells:
        raise ValueError(f"No cells for {doe_id} in {manifest_path}")

    by_arm: dict[str, list[Path]] = {}
    for c in cells:
        arm = str(c.get("arm", "unknown"))
        path = root.parent.parent / c["path"] if not Path(c["path"]).is_absolute() else Path(c["path"])
        # manifest paths are repo-relative: example/fixtures/...
        rel = Path(c["path"])
        cand = [
            root / Path(*rel.parts[2:]) if rel.parts[:2] == ("example", "fixtures") else root / rel,
            Path.cwd() / rel,
            root.parent.parent / rel,
        ]
        resolved = next((p for p in cand if p.exists()), cand[0])
        by_arm.setdefault(arm, []).append(resolved)

    arms: list[DoeArm] = []
    for arm_id, paths in by_arm.items():
        arms.append(
            DoeArm(
                arm_id=arm_id,
                label=arm_id,
                anode="?",
                cathode="?",
                paths=sorted(paths),
            )
        )
    return arms


def extract_arm_features(
    arms: Sequence[DoeArm],
    *,
    encoding: str = "cp949",
    cycles: Iterable[int] | None = None,
) -> pd.DataFrame:
    """Extract LGES features for all cells; tag arm / anode / cathode."""
    from cyclediag.features.lges_extract import LgesExtractConfig, extract_lges_features_table
    from cyclediag.io.cycler_csv import ColumnMap, load_cycler_csv

    cmap = ColumnMap.studio_default()
    parts: list[pd.DataFrame] = []
    n_files = sum(len(a.paths) for a in arms)
    done = 0
    for arm in arms:
        for path in arm.paths:
            done += 1
            cell_id = _cell_id_from_path(path)
            print(f"[{done}/{n_files}] extract {arm.arm_id}/{cell_id} …", flush=True)
            df = load_cycler_csv(str(path), column_map=cmap)
            cfg = LgesExtractConfig(cell_id=cell_id)
            table = extract_lges_features_table(
                df,
                cycles=cycles,
                filepath=str(path),
                config=cfg,
                raw_df=df,
            )
            if table.empty:
                print(f"  empty → skip", flush=True)
                continue
            table = table.copy()
            table["arm"] = arm.arm_id
            table["arm_label"] = arm.label
            table["anode"] = arm.anode
            table["cathode"] = arm.cathode
            table["cell_id"] = cell_id
            table["file"] = str(path)
            parts.append(table)
            print(f"  rows={len(table)}", flush=True)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def _present_cols(df: pd.DataFrame, candidates: Iterable[str]) -> list[str]:
    return [c for c in candidates if c in df.columns]


def early_parameter_summary(
    features: pd.DataFrame,
    *,
    early_cycles: int = 30,
    param_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Per-arm early-window means — what differs from the start (anode effect)."""
    if features.empty or "arm" not in features.columns:
        return pd.DataFrame()
    cols = list(param_cols) if param_cols is not None else _present_cols(features, EARLY_PARAM_CANDIDATES)
    if not cols:
        return pd.DataFrame()

    cyc = pd.to_numeric(features["cycle"], errors="coerce")
    early = features[cyc <= float(early_cycles)].copy()
    if early.empty:
        early = features.sort_values("cycle").groupby("cell_id", group_keys=False).head(5)

    rows: list[dict[str, Any]] = []
    arms = sorted(early["arm"].dropna().unique())
    arm_stats: dict[str, dict[str, float]] = {}
    for arm in arms:
        sub = early[early["arm"] == arm]
        stats: dict[str, float] = {}
        for col in cols:
            s = pd.to_numeric(sub[col], errors="coerce")
            stats[col] = float(s.mean()) if s.notna().any() else float("nan")
        arm_stats[str(arm)] = stats
        rows.append(
            {
                "arm": arm,
                "window": f"cycle<={early_cycles}",
                "n_rows": int(len(sub)),
                "n_cells": int(sub["cell_id"].nunique()) if "cell_id" in sub.columns else 0,
                **{f"mean_{c}": stats[c] for c in cols},
            }
        )

    # pairwise delta (arm_b - arm_a) when exactly 2 arms
    if len(arms) == 2:
        a, b = arms[0], arms[1]
        delta = {
            "arm": f"delta:{b}-vs-{a}",
            "window": f"cycle<={early_cycles}",
            "n_rows": None,
            "n_cells": None,
        }
        for col in cols:
            va, vb = arm_stats[str(a)][col], arm_stats[str(b)][col]
            delta[f"mean_{col}"] = (
                float(vb - va) if np.isfinite(va) and np.isfinite(vb) else float("nan")
            )
            if np.isfinite(va) and abs(va) > 1e-12 and np.isfinite(vb):
                delta[f"pct_{col}"] = float(100.0 * (vb - va) / va)
            else:
                delta[f"pct_{col}"] = float("nan")
        rows.append(delta)

    return pd.DataFrame(rows)


def early_fade_rates(
    features: pd.DataFrame,
    *,
    early_cycles: int = 30,
    health_col: str = "SoHQ",
) -> pd.DataFrame:
    """Linear SoHQ vs cycle slope in the early window (per cell + arm mean)."""
    if features.empty or health_col not in features.columns:
        return pd.DataFrame()
    cyc = pd.to_numeric(features["cycle"], errors="coerce")
    early = features[cyc <= float(early_cycles)].copy()
    rows: list[dict[str, Any]] = []
    group_cols = [c for c in ("arm", "cell_id") if c in early.columns]
    for keys, grp in early.groupby(group_cols, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        meta = dict(zip(group_cols, keys))
        x = pd.to_numeric(grp["cycle"], errors="coerce")
        y = pd.to_numeric(grp[health_col], errors="coerce")
        m = x.notna() & y.notna()
        if m.sum() < 3:
            slope = float("nan")
        else:
            slope = float(np.polyfit(x[m].to_numpy(), y[m].to_numpy(), 1)[0])
        rows.append({**meta, "metric": f"d{health_col}_dN_early", "value": slope, "n": int(m.sum())})
    cell_df = pd.DataFrame(rows)
    if cell_df.empty or "arm" not in cell_df.columns:
        return cell_df
    arm_rows = []
    for arm, grp in cell_df.groupby("arm"):
        arm_rows.append(
            {
                "arm": arm,
                "cell_id": "__arm_mean__",
                "metric": f"d{health_col}_dN_early",
                "value": float(grp["value"].mean()),
                "n": int(grp["n"].sum()),
            }
        )
    return pd.concat([cell_df, pd.DataFrame(arm_rows)], ignore_index=True)


def compare_arms_trajectory(
    features: pd.DataFrame,
    *,
    cols: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Arm-mean trajectories and (armB - armA) on shared cycles."""
    if features.empty or "arm" not in features.columns:
        return pd.DataFrame()
    use_cols = list(cols) if cols is not None else _present_cols(features, EARLY_PARAM_CANDIDATES)
    if not use_cols:
        return pd.DataFrame()

    arms = sorted(features["arm"].dropna().unique())
    pieces: list[pd.DataFrame] = []
    for arm in arms:
        sub = features[features["arm"] == arm]
        g = (
            sub.groupby("cycle", as_index=False)[use_cols]
            .mean(numeric_only=True)
            .assign(arm=arm)
        )
        pieces.append(g)
    traj = pd.concat(pieces, ignore_index=True)
    if len(arms) != 2:
        return traj

    a, b = arms[0], arms[1]
    pa = traj[traj["arm"] == a].set_index("cycle")
    pb = traj[traj["arm"] == b].set_index("cycle")
    common = pa.index.intersection(pb.index)
    if len(common) == 0:
        return traj
    delta_rows = []
    for cyc in common:
        row: dict[str, Any] = {"cycle": int(cyc), "arm": f"delta:{b}-vs-{a}"}
        for col in use_cols:
            if col in pa.columns and col in pb.columns:
                row[col] = float(pb.loc[cyc, col] - pa.loc[cyc, col])
        delta_rows.append(row)
    return pd.concat([traj, pd.DataFrame(delta_rows)], ignore_index=True)


def compare_arms_late_spread(
    features: pd.DataFrame,
    *,
    late_frac: float = 0.2,
) -> pd.DataFrame:
    """Which indicators diverge most between arms in the late window."""
    if features.empty or "arm" not in features.columns:
        return pd.DataFrame()
    cols = _present_cols(features, EARLY_PARAM_CANDIDATES)
    cyc = pd.to_numeric(features["cycle"], errors="coerce")
    thr = float(cyc.quantile(1.0 - late_frac))
    late = features[cyc >= thr]
    if late.empty:
        late = features

    arms = sorted(late["arm"].dropna().unique())
    if len(arms) < 2:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for col in cols:
        means = {}
        for arm in arms:
            s = pd.to_numeric(late.loc[late["arm"] == arm, col], errors="coerce")
            means[str(arm)] = float(s.mean()) if s.notna().any() else float("nan")
        vals = [v for v in means.values() if np.isfinite(v)]
        if len(vals) < 2:
            continue
        spread = float(np.std(vals))
        ranked = sorted(means.items(), key=lambda kv: (-kv[1] if np.isfinite(kv[1]) else 0))
        rows.append(
            {
                "indicator": col,
                "late_cycle_thr": thr,
                "arm_spread_std": spread,
                "arm_means": json.dumps(means),
                "highest_arm": ranked[0][0],
                "lowest_arm": ranked[-1][0],
                "delta_high_minus_low": float(ranked[0][1] - ranked[-1][1])
                if np.isfinite(ranked[0][1]) and np.isfinite(ranked[-1][1])
                else float("nan"),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("arm_spread_std", ascending=False).reset_index(drop=True)


def si_proxy_arm_summary(
    features: pd.DataFrame,
    *,
    change_cycle_window: int = 5,
) -> pd.DataFrame:
    """Per-arm Si vs graphite proxy: band-Q fractions and low-V fade slope."""
    cols = _present_cols(
        features,
        (
            "dchg_Q_low_frac",
            "dchg_Q_high_frac",
            "dchg_f_graphite_proxy",
            "dchg_Q_low_V",
            "EoC_dchgR_R30_minus_R0p1",
            "hyst_area_SOC20",
        ),
    )
    if features.empty or "arm" not in features.columns or not cols:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for arm, grp in features.groupby("arm", sort=False):
        sub = grp.copy()
        cyc = pd.to_numeric(sub["cycle"], errors="coerce")
        row: dict[str, Any] = {"arm": arm, "n_rows": len(sub)}
        for col in cols:
            s = pd.to_numeric(sub[col], errors="coerce")
            row[f"mean_{col}"] = float(s.mean()) if s.notna().any() else float("nan")
            row[f"late_{col}"] = (
                float(s[cyc >= cyc.quantile(0.8)].mean())
                if s.notna().any() and cyc.notna().any()
                else float("nan")
            )
        qlow = pd.to_numeric(sub.get("dchg_Q_low_frac"), errors="coerce")
        if qlow.notna().sum() >= change_cycle_window + 2:
            ok = qlow.notna() & cyc.notna()
            slope, _ = np.polyfit(cyc[ok].to_numpy(), qlow[ok].to_numpy(), 1)
            row["dchg_Q_low_frac_slope_per_cycle"] = float(slope)
        else:
            row["dchg_Q_low_frac_slope_per_cycle"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def diagnose_by_arm(
    features: pd.DataFrame,
    *,
    config_path: Path | str | None = None,
) -> pd.DataFrame:
    """Append ASSB pattern scores (full-cell; no half-cell required)."""
    from cyclediag.diagnosis.engine import diagnose_feature_table

    return diagnose_feature_table(features, config_path=config_path, baseline_cycle=None)


def mode_score_arm_summary(diagnosed: pd.DataFrame) -> pd.DataFrame:
    """Arm-mean pattern scores early / mid / late."""
    from cyclediag.diagnosis.schema import ASSB_PATTERN_MODES, score_column_name

    score_cols = [
        score_column_name(m)
        for m in ASSB_PATTERN_MODES
        if score_column_name(m) in diagnosed.columns
    ]
    if not score_cols or "arm" not in diagnosed.columns:
        return pd.DataFrame()

    cyc = pd.to_numeric(diagnosed["cycle"], errors="coerce")
    q33, q66 = float(cyc.quantile(0.33)), float(cyc.quantile(0.66))

    def _bucket(c: float) -> str:
        if not np.isfinite(c):
            return "unknown"
        if c <= q33:
            return "early"
        if c <= q66:
            return "mid"
        return "late"

    df = diagnosed.copy()
    df["_phase"] = cyc.map(_bucket)
    rows: list[dict[str, Any]] = []
    for (arm, phase), grp in df.groupby(["arm", "_phase"], sort=False):
        row: dict[str, Any] = {"arm": arm, "phase": phase, "n": len(grp)}
        for col in score_cols:
            s = pd.to_numeric(grp[col], errors="coerce")
            row[col] = float(s.mean()) if s.notna().any() else float("nan")
        means = {c: row[c] for c in score_cols if np.isfinite(row[c])}
        if means:
            top = max(means, key=means.get)
            row["dominant_mode"] = (
                top.replace("_pattern_score", "").replace("_score", "")
            )
        else:
            row["dominant_mode"] = None
        rows.append(row)
    return pd.DataFrame(rows)


def si_proxy_arm_summary(
    features: pd.DataFrame,
    *,
    change_cycle_window: int = 5,
) -> pd.DataFrame:
    """Per-arm Si vs graphite proxy: band-Q fractions and low-V fade slope."""
    cols = _present_cols(
        features,
        (
            "dchg_Q_low_frac",
            "dchg_Q_high_frac",
            "dchg_f_graphite_proxy",
            "dchg_Q_low_V",
            "EoC_dchgR_R30_minus_R0p1",
            "hyst_area_SOC20",
        ),
    )
    if features.empty or "arm" not in features.columns or not cols:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for arm, grp in features.groupby("arm", sort=False):
        sub = grp.copy()
        cyc = pd.to_numeric(sub["cycle"], errors="coerce")
        row: dict[str, Any] = {"arm": arm, "n_rows": len(sub)}
        for col in cols:
            s = pd.to_numeric(sub[col], errors="coerce")
            row[f"mean_{col}"] = float(s.mean()) if s.notna().any() else float("nan")
            row[f"late_{col}"] = (
                float(s[cyc >= cyc.quantile(0.8)].mean())
                if s.notna().any() and cyc.notna().any()
                else float("nan")
            )
        qlow = pd.to_numeric(sub.get("dchg_Q_low_frac"), errors="coerce")
        if qlow.notna().sum() >= change_cycle_window + 2:
            ok = qlow.notna() & cyc.notna()
            slope, _ = np.polyfit(cyc[ok].to_numpy(), qlow[ok].to_numpy(), 1)
            row["dchg_Q_low_frac_slope_per_cycle"] = float(slope)
        else:
            row["dchg_Q_low_frac_slope_per_cycle"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def mechanism_contrast_narrative(
    early_summary: pd.DataFrame,
    mode_summary: pd.DataFrame,
    late_spread: pd.DataFrame,
    *,
    arm_a: str = "SJ900_dry",
    arm_b: str = "SJ1300_dry",
) -> list[str]:
    """Short bullet narrative for DOE2 (same cathode, different anode)."""
    lines = [
        f"DOE2 contrast: cathode held constant; anode differs ({arm_a} vs {arm_b}).",
        "Early parameters reflect formation / BOL anode utilization & kinetics.",
        "Resistance: landmark 0.1/10/30 s + R_slow=R30-R0.1 (routine); DC-IR fit gated on current settle.",
        "Si proxy: dchg_Q_low_frac / dchg_f_graphite_proxy (low-V vs high-V band capacity).",
        "Mode scores are full-cell pattern scores (not half-cell calibrated).",
    ]
    # top early deltas
    delta = early_summary[early_summary["arm"].astype(str).str.startswith("delta:")]
    if not delta.empty:
        row = delta.iloc[0]
        deltas = []
        for c in row.index:
            if not c.startswith("mean_"):
                continue
            v = row[c]
            if isinstance(v, (int, float)) and np.isfinite(v) and abs(v) > 0:
                deltas.append((c.replace("mean_", ""), float(v)))
        deltas.sort(key=lambda kv: abs(kv[1]), reverse=True)
        for name, val in deltas[:8]:
            lines.append(f"Early Δ({arm_b}-{arm_a}) {name}: {val:+.4g}")

    if not late_spread.empty:
        top = late_spread.head(5)
        lines.append("Late-life arm divergence (highest spread):")
        for _, r in top.iterrows():
            lines.append(
                f"  - {r['indicator']}: spread={r['arm_spread_std']:.4g}, "
                f"high={r['highest_arm']}, low={r['lowest_arm']}"
            )

    if not mode_summary.empty:
        late = mode_summary[mode_summary["phase"] == "late"]
        if not late.empty:
            lines.append("Late-phase dominant pattern modes by arm:")
            for _, r in late.iterrows():
                lines.append(f"  - {r['arm']}: {r.get('dominant_mode')}")
    return lines


def _write_plots(
    features: pd.DataFrame,
    traj: pd.DataFrame,
    mode_summary: pd.DataFrame,
    out_dir: Path,
    *,
    arm_a: str,
    arm_b: str,
) -> list[str]:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    colors = {arm_a: "#1f77b4", arm_b: "#d62728"}

    def _plot_metric(col: str, fname: str, ylabel: str | None = None) -> None:
        if col not in features.columns:
            return
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for arm, grp in features.groupby("arm"):
            sub = grp[["cycle", col]].copy()
            sub[col] = pd.to_numeric(sub[col], errors="coerce")
            g = sub.groupby("cycle", as_index=False)[col].mean()
            ax.plot(
                g["cycle"],
                g[col],
                label=str(arm),
                color=colors.get(str(arm)),
                lw=1.8,
            )
        ax.set_xlabel("cycle")
        ax.set_ylabel(ylabel or col)
        ax.set_title(f"DOE2 arm mean — {col}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        path = out_dir / fname
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        written.append(str(path))

    for col, fn in (
        ("SoHQ", "doe2_SoHQ.png"),
        ("CE", "doe2_CE.png"),
        ("EoD_chgR_30s", "doe2_EoD_R30s.png"),
        ("EoD_chgR_R30_minus_R0p1", "doe2_EoD_Rslow.png"),
        ("dchg_Q_low_frac", "doe2_Q_low_frac.png"),
        ("dchg_f_graphite_proxy", "doe2_f_graphite_proxy.png"),
        ("R_SOC_diff_20_80", "doe2_R_SOC_diff.png"),
        ("hyst_mean", "doe2_hyst.png"),
        ("dchg_dQdV_peak1_V", "doe2_dQdV_peak1_V.png"),
    ):
        _plot_metric(col, fn)

    # mode scores late bar
    if not mode_summary.empty:
        late = mode_summary[mode_summary["phase"] == "late"]
        score_cols = [
            c
            for c in late.columns
            if c.endswith("_pattern_score")
            or c
            in {
                "contact_loss_score",
                "interface_R_score",
                "SE_decomposition_score",
                "microshort_score",
                "solid_diffusion_score",
            }
        ]
        if not late.empty and score_cols:
            fig, ax = plt.subplots(figsize=(9, 4.5))
            x = np.arange(len(score_cols))
            width = 0.35
            for i, (_, r) in enumerate(late.iterrows()):
                vals = [r.get(c, np.nan) for c in score_cols]
                ax.bar(x + (i - 0.5) * width, vals, width, label=str(r["arm"]))
            ax.set_xticks(x)
            ax.set_xticklabels(
                [c.replace("_pattern_score", "").replace("_score", "") for c in score_cols],
                rotation=30,
                ha="right",
            )
            ax.set_ylabel("pattern score")
            ax.set_title("DOE2 late-phase mode scores by arm")
            ax.legend()
            ax.grid(True, axis="y", alpha=0.3)
            path = out_dir / "doe2_mode_scores_late.png"
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            written.append(str(path))

    return written


def run_doe_compare(cfg: DoeCompareConfig | None = None) -> dict[str, Any]:
    """Run full DOE comparison pipeline; write tables + optional plots."""
    cfg = cfg or DoeCompareConfig()
    fixtures = Path(cfg.fixtures_root) if cfg.fixtures_root else _repo_fixtures_root()
    out_dir = Path(cfg.out_dir) if cfg.out_dir else Path("example/output") / f"{cfg.doe_id}_compare"
    out_dir.mkdir(parents=True, exist_ok=True)

    if cfg.doe_id.upper() == "DOE2":
        arms = list(load_doe2_arms(fixtures))
    else:
        arms = load_doe_arms_from_manifest(cfg.doe_id, fixtures)

    features = extract_arm_features(arms, encoding=cfg.encoding, cycles=cfg.cycles)
    if features.empty:
        raise RuntimeError("No features extracted for DOE arms")

    early = early_parameter_summary(features, early_cycles=cfg.early_cycles)
    fade = early_fade_rates(features, early_cycles=cfg.early_cycles)
    traj = compare_arms_trajectory(features)
    late = compare_arms_late_spread(features, late_frac=cfg.late_frac)
    si_proxy = si_proxy_arm_summary(features)

    diagnosed = features
    mode_sum = pd.DataFrame()
    if cfg.run_diagnosis:
        diagnosed = diagnose_by_arm(features)
        mode_sum = mode_score_arm_summary(diagnosed)

    arm_ids = [a.arm_id for a in arms]
    arm_a = arm_ids[0] if arm_ids else "arm_a"
    arm_b = arm_ids[1] if len(arm_ids) > 1 else "arm_b"
    narrative = mechanism_contrast_narrative(
        early, mode_sum, late, arm_a=arm_a, arm_b=arm_b
    )

    # writes
    features.to_csv(out_dir / "all_features.csv", index=False)
    early.to_csv(out_dir / "early_parameters_by_arm.csv", index=False)
    fade.to_csv(out_dir / "early_fade_rates.csv", index=False)
    traj.to_csv(out_dir / "arm_trajectories.csv", index=False)
    late.to_csv(out_dir / "late_arm_divergence.csv", index=False)
    if not si_proxy.empty:
        si_proxy.to_csv(out_dir / "si_proxy_by_arm.csv", index=False)
    if cfg.run_diagnosis:
        diagnosed.to_csv(out_dir / "diagnosis_by_cycle.csv", index=False)
        mode_sum.to_csv(out_dir / "mode_scores_by_arm_phase.csv", index=False)

    (out_dir / "narrative.txt").write_text("\n".join(narrative) + "\n", encoding="utf-8")

    plots: list[str] = []
    if cfg.write_plots:
        plots = _write_plots(
            features, traj, mode_sum, out_dir / "plots", arm_a=arm_a, arm_b=arm_b
        )

    summary = {
        "doe_id": cfg.doe_id,
        "fixtures_root": str(fixtures),
        "out_dir": str(out_dir),
        "arms": [
            {
                "arm_id": a.arm_id,
                "label": a.label,
                "anode": a.anode,
                "cathode": a.cathode,
                "n_files": len(a.paths),
                "cells": [_cell_id_from_path(p) for p in a.paths],
            }
            for a in arms
        ],
        "early_cycles": cfg.early_cycles,
        "n_feature_rows": int(len(features)),
        "narrative": narrative,
        "plots": plots,
        "hypothesis": {
            "controlled": "cathode (S83S)",
            "varied": "anode (SJ900 vs SJ1300)",
            "expect_early": "R_slow (R30-R0.1), low-V Q band, hysteresis; cathode dQ/dV peaks aligned",
            "expect_aging": "Q_low fade + R_SOC_diff with contact_loss pattern; f_graphite_proxy may rise",
        },
    }
    if not si_proxy.empty:
        summary["si_proxy"] = si_proxy.to_dict(orient="records")
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary
