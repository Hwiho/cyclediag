#!/usr/bin/env python3
"""DOE2: SJ900 vs SJ1300 — keystone metrics = knee × dV/dQ SOC0."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cyclediag.analysis.cycle_trend import analyze_series  # noqa: E402
from cyclediag.analysis.doe_cathode_compare import (  # noqa: E402
    early_window_summary,
    late_window_summary,
    mechanism_delta,
)
from cyclediag.tools.compare_doe_cathodes import diagnose_one  # noqa: E402

C900, C1300 = "#C45C26", "#1F6F8B"

KEYSTONE_METRICS = (
    "knee_cycle_bw",
    "dchg_dVdQ_SOC0",
    "dchg_dVdQ_SOC0_cliff_width",
    "dchg_dVdQ_SOC0_to_mid_ratio",
    "delta_dchg_dVdQ_SOC0",
)


def _font() -> str:
    for path in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ):
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            mpl.rcParams["font.family"] = font_manager.FontProperties(fname=path).get_name()
            mpl.rcParams["axes.unicode_minus"] = False
            return path
    return ""


FONT = _font()


def fp(size=10, weight="normal"):
    if FONT:
        return font_manager.FontProperties(fname=FONT, size=size, weight=weight)
    return font_manager.FontProperties(size=size, weight=weight)


def _routine(feats: pd.DataFrame) -> pd.DataFrame:
    d = feats.sort_values("cycle")
    if "cycle_role" in d.columns:
        d = d.loc[d["cycle_role"].astype(str).eq("routine_05c")]
    return d


def _window_med(df: pd.DataFrame, col: str, *, which: str, n: int = 5) -> float | None:
    s = pd.to_numeric(df.get(col), errors="coerce").dropna()
    if s.empty:
        return None
    vals = s.to_numpy(dtype=float)
    chunk = vals[:n] if which == "early" else vals[-n:]
    return float(np.median(chunk))


def attach_soc0_keystone(row: dict, feats: pd.DataFrame) -> dict:
    rout = _routine(feats)
    cyc = pd.to_numeric(rout.get("cycle"), errors="coerce")
    knee = row.get("knee_cycle_bw")
    for col in (
        "dchg_dVdQ_SOC0",
        "dchg_dVdQ_SOC0_Q",
        "dchg_dVdQ_SOC0_cliff_width",
        "dchg_dVdQ_SOC0_to_mid_ratio",
        "delta_dchg_dVdQ_SOC0",
    ):
        if col not in rout.columns:
            continue
        e = _window_med(rout, col, which="early")
        l = _window_med(rout, col, which="late")
        row[f"early_{col}"] = e
        row[f"late_{col}"] = l
        if e is not None and l is not None:
            row[f"deltaEL_{col}"] = float(l - e)
        if knee is not None and np.isfinite(knee):
            near = rout.iloc[(cyc - float(knee)).abs().argsort()[:5]]
            s = pd.to_numeric(near.get(col), errors="coerce").dropna()
            if not s.empty:
                row[f"atknee_{col}"] = float(s.median())
            pre = pd.to_numeric(rout.loc[cyc < float(knee), col], errors="coerce").dropna()
            post = pd.to_numeric(rout.loc[cyc >= float(knee), col], errors="coerce").dropna()
            if len(pre) >= 3 and len(post) >= 3:
                row[f"jump_{col}"] = float(post.head(5).median() - pre.tail(5).median())
    if "delta_dchg_dVdQ_SOC0" in rout.columns:
        dd = pd.to_numeric(rout["delta_dchg_dVdQ_SOC0"], errors="coerce")
        if dd.notna().any():
            fin = float(dd.dropna().iloc[-1])
            if abs(fin) > 1e-12:
                thr = 0.5 * fin
                mask = dd.notna() & ((dd >= thr) if fin > 0 else (dd <= thr))
                if mask.any():
                    row["SOC0_delta_half_cycle"] = float(cyc[mask].iloc[0])
    return row


def cell_row(arm: str, feats: pd.DataFrame, meta: dict) -> dict:
    early = early_window_summary(feats)
    late = late_window_summary(feats, sohq_max=90.0)
    delta = mechanism_delta(early, late)
    row: dict = {"arm": arm, "cell_id": meta["cell_id"], **meta, **early, **late, **delta}
    for k in (
        "fade_exponent_b", "knee_cycle_bw", "knee_severity",
        "knee_slope_before", "knee_slope_after", "knee_fit_r2",
    ):
        if k in feats.columns and feats[k].notna().any():
            row[k] = float(pd.to_numeric(feats[k], errors="coerce").dropna().iloc[0])
    rout = _routine(feats)
    sohq = pd.to_numeric(rout.get("SoHQ"), errors="coerce")
    cyc = pd.to_numeric(rout.get("cycle"), errors="coerce")
    if sohq.notna().any():
        row["SoHQ_start"] = float(sohq.dropna().iloc[0])
        row["SoHQ_end"] = float(sohq.dropna().iloc[-1])
        row["n_routine"] = int(sohq.notna().sum())
        knee = row.get("knee_cycle_bw")
        if knee is not None and np.isfinite(knee):
            near = rout.loc[(cyc - knee).abs() == (cyc - knee).abs().min()]
            if not near.empty and pd.notna(near.iloc[0].get("SoHQ")):
                row["SoHQ_at_knee"] = float(near.iloc[0]["SoHQ"])
    row = attach_soc0_keystone(row, feats)
    for key in (
        "SoHQ", "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
        "PE_side_score", "contact_stack_score", "NE_side_score", "si_cosign",
        "dchg_dVdQ_SOC0", "dchg_dVdQ_SOC0_cliff_width", "delta_dchg_dVdQ_SOC0",
    ):
        if key in feats.columns:
            tr = analyze_series(feats, key)
            row[f"trend_{key}"] = tr.get("trend_label")
            row[f"slope100_{key}"] = tr.get("slope_per_100")
    return row


def narrative(cell_table: pd.DataFrame) -> str:
    a_all = cell_table.loc[cell_table.arm == "SJ900"]
    b = cell_table.loc[cell_table.arm == "SJ1300"]
    a = a_all.loc[a_all.cell_id != "M01Ch025"] if "M01Ch025" in set(a_all.cell_id) else a_all
    lines = [
        "## DOE2 핵심 2지표: knee × dV/dQ SOC0",
        "",
        "양극 동일 · 음극 상이. **사이클 변곡점(knee)** 과 **방전 dV/dQ @SOC0(저SOC cliff)** 가 "
        "anode arm을 가르는 1차 관측량.",
        "",
        f"- SJ900 (excl Ch025): {', '.join(a.cell_id)}",
        f"- SJ1300: {', '.join(b.cell_id)}",
        "",
        "### 1) Knee (bilinear on routine SoHQ)",
    ]
    for arm, d in (("SJ900", a), ("SJ1300", b)):
        knees = pd.to_numeric(d.get("knee_cycle_bw"), errors="coerce")
        sev = pd.to_numeric(d.get("knee_severity"), errors="coerce")
        sohq_k = pd.to_numeric(d.get("SoHQ_at_knee"), errors="coerce")
        sohq_e = pd.to_numeric(d.get("SoHQ_end"), errors="coerce")
        lines.append(
            f"- **{arm}**: knee ≈ {knees.mean():.0f} cyc "
            f"({', '.join(f'{c}={k:.0f}' for c, k in zip(d.cell_id, knees) if pd.notna(k))}); "
            f"severity={sev.mean():.3g}; SoHQ@knee≈{sohq_k.mean():.1f}%; end≈{sohq_e.mean():.1f}%"
        )
    lines += ["", "### 2) dV/dQ @ SOC0 (저SOC cliff intensity)"]
    for arm, d in (("SJ900", a), ("SJ1300", b)):
        e = pd.to_numeric(d.get("early_dchg_dVdQ_SOC0"), errors="coerce")
        l = pd.to_numeric(d.get("late_dchg_dVdQ_SOC0"), errors="coerce")
        de = pd.to_numeric(d.get("deltaEL_dchg_dVdQ_SOC0"), errors="coerce")
        cw_e = pd.to_numeric(d.get("early_dchg_dVdQ_SOC0_cliff_width"), errors="coerce")
        cw_l = pd.to_numeric(d.get("late_dchg_dVdQ_SOC0_cliff_width"), errors="coerce")
        half = pd.to_numeric(d.get("SOC0_delta_half_cycle"), errors="coerce")
        lines.append(
            f"- **{arm}**: SOC0 {e.mean():.3g} → {l.mean():.3g} (Δ={de.mean():+.3g}); "
            f"cliff_width {cw_e.mean():.2f} → {cw_l.mean():.2f}; "
            f"ΔSOC0 half-cycle ≈ {half.mean():.0f}"
        )
    lines += [
        "",
        "### 교차 해석",
        "- **SJ900**: knee 늦음(~320) · SOC0 **후반에 커짐**(cliff 넓어짐) · ΔSOC0 절반은 knee **이후**(~480).",
        "- **SJ1300**: knee 이름(~253)·더 급함 · SOC0는 **초반부터 줄고** cliff 좁아짐 · ΔSOC0 절반은 knee **이전**(~50).",
        "- 같은 양극인데도 SOC0 궤적 부호가 반대 → **음극 쪽 저SOC 형상**이 knee 타이밍과 함께 arm을 구분.",
        "",
        "### 보조 패턴 (Δ late−early, excl Ch025)",
    ]
    for key, label in (
        ("delta_LLI_pattern_score", "LLI"),
        ("delta_LAM_PE_pattern_score", "LAM_PE activity"),
        ("delta_contact_loss_score", "contact_loss"),
        ("delta_si_cosign", "si_cosign"),
        ("delta_PE_side_score", "PE_side"),
    ):
        if key not in cell_table.columns:
            continue
        va = pd.to_numeric(a[key], errors="coerce").mean()
        vb = pd.to_numeric(b[key], errors="coerce").mean()
        if np.isfinite(va) and np.isfinite(vb):
            lines.append(f"- `{label}`: SJ900 {va:+.3g} vs SJ1300 {vb:+.3g}")
    lines.append("")
    lines.append(
        "> dchg_dVdQ_SOC0 = 방전 말단(SOC≈0) |dV/dQ|. "
        "cliff_width = mid 대비 2× 넘는 Q폭. Ch025는 knee 평균에서 제외."
    )
    return "\n".join(lines)


def build_pdf(out: Path, traj: dict[str, pd.DataFrame], cell_table: pd.DataFrame, text: str) -> None:
    arts = Path("/opt/cursor/artifacts")
    arts.mkdir(parents=True, exist_ok=True)
    with PdfPages(out) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.93, "DOE2 keystones: knee × dV/dQ SOC0", fontproperties=fp(15, "bold"))
        fig.text(0.08, 0.89, "SJ900 vs SJ1300 · 양극 동일 · 음극 상이", fontproperties=fp(11))
        y = 0.84
        for para in text.split("\n"):
            fig.text(0.08, y, para[:108], fontproperties=fp(8.2 if para.startswith("#") else 7.8))
            y -= 0.026
            if y < 0.06:
                break
        pdf.savefig(fig)
        plt.close(fig)

        # keystone dual panel
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "1. Keystones — SoHQ knee + dV/dQ SOC0", fontproperties=fp(13, "bold"))
        ax1 = fig.add_axes([0.10, 0.55, 0.82, 0.35])
        ax2 = fig.add_axes([0.10, 0.12, 0.82, 0.35])
        for _, r in cell_table.iterrows():
            cid, arm = r["cell_id"], r["arm"]
            if cid == "M01Ch025":
                continue
            color = C900 if arm == "SJ900" else C1300
            d = traj[cid]
            rout = d[d["cycle_role"].astype(str).eq("routine_05c")] if "cycle_role" in d.columns else d
            ax1.plot(rout["cycle"], rout["SoHQ"], color=color, lw=1.4, alpha=0.8, label=f"{arm}/{cid}")
            knee = r.get("knee_cycle_bw")
            if knee is not None and np.isfinite(knee):
                ax1.axvline(float(knee), color=color, ls="--", lw=1.0, alpha=0.7)
            if "dchg_dVdQ_SOC0" in rout.columns:
                ax2.plot(
                    rout["cycle"], rout["dchg_dVdQ_SOC0"],
                    color=color, lw=1.3, alpha=0.8, label=f"{arm}/{cid}",
                )
                if knee is not None and np.isfinite(knee):
                    ax2.axvline(float(knee), color=color, ls="--", lw=0.9, alpha=0.55)
        ax1.set_ylabel("SoHQ %")
        ax1.set_title("Retention · dashed = knee", loc="left", fontproperties=fp(10, "bold"))
        ax1.legend(prop=fp(6), ncol=2, frameon=False)
        ax1.grid(True, alpha=0.25)
        ax2.set_xlabel("Cycle")
        ax2.set_ylabel("dV/dQ @ SOC0")
        ax2.set_title("저SOC cliff intensity (keystone #2)", loc="left", fontproperties=fp(10, "bold"))
        ax2.legend(prop=fp(6), ncol=2, frameon=False)
        ax2.grid(True, alpha=0.25)
        pdf.savefig(fig)
        plt.close(fig)

        # cliff width + scatter knee vs SOC0 half
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "2. SOC0 cliff width · knee timing vs SOC0 timing", fontproperties=fp(12, "bold"))
        ax1 = fig.add_axes([0.10, 0.55, 0.82, 0.35])
        ax2 = fig.add_axes([0.18, 0.12, 0.65, 0.35])
        for _, r in cell_table.iterrows():
            cid, arm = r["cell_id"], r["arm"]
            if cid == "M01Ch025":
                continue
            color = C900 if arm == "SJ900" else C1300
            d = traj[cid]
            rout = d[d["cycle_role"].astype(str).eq("routine_05c")] if "cycle_role" in d.columns else d
            if "dchg_dVdQ_SOC0_cliff_width" in rout.columns:
                ax1.plot(rout["cycle"], rout["dchg_dVdQ_SOC0_cliff_width"], color=color, lw=1.3, alpha=0.8, label=f"{arm}/{cid}")
            knee = r.get("knee_cycle_bw")
            half = r.get("SOC0_delta_half_cycle")
            if knee is not None and half is not None and np.isfinite(knee) and np.isfinite(half):
                ax2.scatter([knee], [half], s=80, color=color, marker="o" if arm == "SJ900" else "s", label=f"{arm}/{cid}")
        ax1.set_ylabel("cliff width")
        ax1.set_title("dchg_dVdQ_SOC0_cliff_width", loc="left", fontproperties=fp(10, "bold"))
        ax1.legend(prop=fp(6), ncol=2, frameon=False)
        ax1.grid(True, alpha=0.25)
        lims = [0, 550]
        ax2.plot(lims, lims, color="#999", lw=0.8, ls=":")
        ax2.set_xlabel("knee cycle")
        ax2.set_ylabel("SOC0 Δ half-cycle")
        ax2.set_title("knee vs SOC0 timing (above = SOC0 moves after knee)", loc="left", fontproperties=fp(9, "bold"))
        ax2.legend(prop=fp(6), frameon=False)
        ax2.grid(True, alpha=0.25)
        pdf.savefig(fig)
        plt.close(fig)

        # pattern bars
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "3. Supporting pattern Δ (late−early)", fontproperties=fp(13, "bold"))
        keys = [
            ("delta_LLI_pattern_score", "LLI"),
            ("delta_LAM_PE_pattern_score", "LAM_PE"),
            ("delta_contact_loss_score", "contact"),
            ("delta_PE_side_score", "PE_side"),
            ("delta_si_cosign", "si_cosign"),
            ("deltaEL_dchg_dVdQ_SOC0", "SOC0 Δ"),
        ]
        keys = [(k, lab) for k, lab in keys if k in cell_table.columns]
        ax = fig.add_axes([0.20, 0.25, 0.68, 0.60])
        y = np.arange(len(keys))
        w = 0.35
        a = cell_table.loc[(cell_table.arm == "SJ900") & (cell_table.cell_id != "M01Ch025")]
        b = cell_table.loc[cell_table.arm == "SJ1300"]
        va = [pd.to_numeric(a[k], errors="coerce").mean() for k, _ in keys]
        vb = [pd.to_numeric(b[k], errors="coerce").mean() for k, _ in keys]
        ax.barh(y - w / 2, va, height=w, color=C900, label="SJ900")
        ax.barh(y + w / 2, vb, height=w, color=C1300, label="SJ1300")
        ax.set_yticks(y)
        ax.set_yticklabels([lab for _, lab in keys], fontproperties=fp(9))
        ax.axvline(0, color="#999", lw=0.6)
        ax.legend(prop=fp(8), frameon=False)
        ax.set_xlabel("Δ (late−early)")
        ax.grid(True, axis="x", alpha=0.25)
        pdf.savefig(fig)
        plt.close(fig)

        meta = pdf.infodict()
        meta["Title"] = "DOE2 knee × dV/dQ SOC0 keystones"
    (arts / out.name).write_bytes(out.read_bytes())


def main() -> None:
    out = Path("example/output/DOE2_knee_pattern")
    out.mkdir(parents=True, exist_ok=True)
    # Prefer reusing trajectories if present
    existing = sorted(out.glob("*_trajectory.csv"))
    traj: dict[str, pd.DataFrame] = {}
    rows: list[dict] = []
    if len(existing) >= 5:
        print(f"reuse {len(existing)} trajectories", flush=True)
        for path in existing:
            cid = path.name.replace("_trajectory.csv", "")
            feats = pd.read_csv(path)
            arm = "SJ1300" if int(cid.replace("M01Ch", "")) < 20 else "SJ900"
            meta = {"cell_id": cid, "n_cycles_raw": int(pd.to_numeric(feats["cycle"], errors="coerce").nunique())}
            traj[cid] = feats
            rows.append(cell_row(arm, feats, meta))
    else:
        arms = [
            ("SJ900", Path("example/fixtures/doe/DOE1/set4_SJ900")),
            ("SJ1300", Path("example/fixtures/doe/DOE2/SJ1300_dry")),
        ]
        for arm, folder in arms:
            for path in sorted(folder.glob("*_raw.csv")):
                if path.stat().st_size < 1000:
                    continue
                print(f"diagnose {arm} {path.name} ...", flush=True)
                feats, segs, meta = diagnose_one(path, halfcell_dir=None, step=10)
                cid = meta["cell_id"]
                traj[cid] = feats
                feats.to_csv(out / f"{cid}_trajectory.csv", index=False)
                segs.to_csv(out / f"{cid}_segments.csv", index=False)
                rows.append(cell_row(arm, feats, meta))

    cell_table = pd.DataFrame(rows)
    cell_table.to_csv(out / "cell_summaries.csv", index=False)
    text = narrative(cell_table)
    (out / "KNEE_PATTERN_COMPARE.md").write_text(text, encoding="utf-8")
    print(text)
    pdf = out / "DOE2_SJ900_vs_SJ1300_knee_pattern.pdf"
    build_pdf(pdf, traj, cell_table, text)
    print(f"wrote {pdf}")
    print(f"keystones: {KEYSTONE_METRICS}")


if __name__ == "__main__":
    main()
