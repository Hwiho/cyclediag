#!/usr/bin/env python3
"""DOE2: SJ900 vs SJ1300 — knee + degradation pattern contrast (same cathode)."""

from __future__ import annotations

import json
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


def _font():
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


def cell_row(arm: str, feats: pd.DataFrame, meta: dict) -> dict:
    early = early_window_summary(feats)
    late = late_window_summary(feats, sohq_max=90.0)
    delta = mechanism_delta(early, late)
    row = {"arm": arm, "cell_id": meta["cell_id"], **meta, **early, **late, **delta}
    for k in ("fade_exponent_b", "knee_cycle_bw", "knee_severity", "knee_slope_before", "knee_slope_after", "knee_fit_r2"):
        if k in feats.columns and feats[k].notna().any():
            row[k] = float(pd.to_numeric(feats[k], errors="coerce").dropna().iloc[0])
    # SoHQ at knee / end
    rout = feats
    if "cycle_role" in feats.columns:
        rout = feats.loc[feats["cycle_role"].astype(str).eq("routine_05c")]
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
    # trend labels for key modes
    for key in (
        "SoHQ", "LAM_PE_pattern_score", "contact_loss_score", "LLI_pattern_score",
        "PE_side_score", "contact_stack_score", "NE_side_score", "si_cosign",
        "hyst_area_low", "R_ohmic_soc50", "mech_vs_chem_ratio",
    ):
        if key in feats.columns:
            tr = analyze_series(feats, key)
            row[f"trend_{key}"] = tr.get("trend_label")
            row[f"slope100_{key}"] = tr.get("slope_per_100")
            row[f"delta_{key}_el"] = tr.get("delta_late_early")
    return row


def narrative(cell_table: pd.DataFrame) -> str:
    a = cell_table.loc[cell_table.arm == "SJ900"]
    b = cell_table.loc[cell_table.arm == "SJ1300"]
    lines = [
        "## DOE2 변곡점·패턴 대비 (양극 동일 · 음극 상이)",
        "",
        f"- SJ900 dry (provisional set4): {', '.join(a.cell_id)}",
        f"- SJ1300 dry: {', '.join(b.cell_id)}",
        "",
        "### Knee (bilinear on routine SoHQ)",
    ]
    for arm, d in (("SJ900", a), ("SJ1300", b)):
        knees = pd.to_numeric(d.get("knee_cycle_bw"), errors="coerce")
        sev = pd.to_numeric(d.get("knee_severity"), errors="coerce")
        sohq_k = pd.to_numeric(d.get("SoHQ_at_knee"), errors="coerce")
        sohq_e = pd.to_numeric(d.get("SoHQ_end"), errors="coerce")
        lines.append(
            f"- **{arm}**: knee ≈ {knees.mean():.0f} ± {knees.std(ddof=0):.0f} cyc "
            f"(cells: {', '.join(f'{c}={k:.0f}' for c,k in zip(d.cell_id, knees) if pd.notna(k))}); "
            f"severity={sev.mean():.3g}; SoHQ@knee≈{sohq_k.mean():.1f}%; end SoHQ≈{sohq_e.mean():.1f}%"
        )
    lines.append("")
    lines.append("### 열화 패턴 (Δ late−early, arm mean)")
    for key, label in (
        ("delta_LAM_PE_pattern_score", "LAM_PE activity"),
        ("delta_contact_loss_score", "contact_loss"),
        ("delta_LLI_pattern_score", "LLI"),
        ("delta_PE_side_score", "PE_side"),
        ("delta_contact_stack_score", "contact_stack"),
        ("delta_NE_side_score", "NE_hyp"),
        ("delta_si_cosign", "si_cosign"),
        ("delta_mech_vs_chem_ratio", "mech/chem"),
    ):
        if key not in cell_table.columns:
            continue
        va = pd.to_numeric(a[key], errors="coerce").mean()
        vb = pd.to_numeric(b[key], errors="coerce").mean()
        if not (np.isfinite(va) and np.isfinite(vb)):
            continue
        lines.append(f"- `{label}`: SJ900 {va:+.3g} vs SJ1300 {vb:+.3g} (Δ1300−900={vb-va:+.3g})")
    lines.append("")
    lines.append(
        "> SJ900 set4 = provisional dry arm (DOE2 README). "
        "Ch025는 사이클 짧아 knee 해석 시 주의. 절대 LAM% 아님."
    )
    return "\n".join(lines)


def build_pdf(out: Path, traj: dict[str, pd.DataFrame], cell_table: pd.DataFrame, text: str):
    arts = Path("/opt/cursor/artifacts")
    arts.mkdir(parents=True, exist_ok=True)
    with PdfPages(out) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.92, "DOE2: SJ900 vs SJ1300", fontproperties=fp(16, "bold"))
        fig.text(0.08, 0.88, "양극 동일 · 음극 상이 — knee & pattern", fontproperties=fp(11))
        y = 0.82
        for para in text.split("\n"):
            fig.text(0.08, y, para[:110], fontproperties=fp(8.5 if para.startswith("#") else 8))
            y -= 0.028
            if y < 0.08:
                break
        pdf.savefig(fig); plt.close(fig)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "1. SoHQ + knee markers", fontproperties=fp(13, "bold"))
        ax = fig.add_axes([0.10, 0.55, 0.82, 0.35])
        ax2 = fig.add_axes([0.10, 0.12, 0.82, 0.35])
        for _, r in cell_table.iterrows():
            cid, arm = r["cell_id"], r["arm"]
            color = C900 if arm == "SJ900" else C1300
            d = traj[cid]
            rout = d[d["cycle_role"].astype(str).eq("routine_05c")] if "cycle_role" in d.columns else d
            ax.plot(rout["cycle"], rout["SoHQ"], color=color, lw=1.3, alpha=0.75, label=f"{arm}/{cid}")
            knee = r.get("knee_cycle_bw")
            if knee is not None and np.isfinite(knee):
                ax.axvline(float(knee), color=color, ls="--", lw=0.9, alpha=0.6)
            if "PE_side_score" in rout and "contact_stack_score" in rout:
                ax2.plot(
                    rout["cycle"],
                    rout["PE_side_score"] - rout["contact_stack_score"],
                    color=color, lw=1.2, alpha=0.75,
                )
        ax.set_ylabel("SoHQ %"); ax.set_title("Retention (dashed=knee)", loc="left", fontproperties=fp(10, "bold"))
        ax.legend(prop=fp(6), ncol=2, frameon=False); ax.grid(True, alpha=0.25)
        ax2.axhline(0, color="#999", lw=0.6)
        ax2.set_xlabel("Cycle"); ax2.set_ylabel("PE − contact")
        ax2.set_title("Lean (양수=PE activity)", loc="left", fontproperties=fp(10, "bold"))
        ax2.grid(True, alpha=0.25)
        pdf.savefig(fig); plt.close(fig)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "2. Pattern Δ (late−early) by arm", fontproperties=fp(13, "bold"))
        keys = [
            ("delta_LAM_PE_pattern_score", "LAM_PE"),
            ("delta_contact_loss_score", "contact"),
            ("delta_LLI_pattern_score", "LLI"),
            ("delta_PE_side_score", "PE_side"),
            ("delta_contact_stack_score", "contact_stack"),
            ("delta_NE_side_score", "NE_hyp"),
            ("delta_si_cosign", "si_cosign"),
        ]
        keys = [(k, lab) for k, lab in keys if k in cell_table.columns]
        ax = fig.add_axes([0.18, 0.25, 0.70, 0.60])
        y = np.arange(len(keys))
        w = 0.35
        a = cell_table.loc[cell_table.arm == "SJ900"]
        b = cell_table.loc[cell_table.arm == "SJ1300"]
        va = [pd.to_numeric(a[k], errors="coerce").mean() for k, _ in keys]
        vb = [pd.to_numeric(b[k], errors="coerce").mean() for k, _ in keys]
        ax.barh(y - w / 2, va, height=w, color=C900, label="SJ900")
        ax.barh(y + w / 2, vb, height=w, color=C1300, label="SJ1300")
        ax.set_yticks(y); ax.set_yticklabels([lab for _, lab in keys], fontproperties=fp(9))
        ax.axvline(0, color="#999", lw=0.6); ax.legend(prop=fp(8), frameon=False)
        ax.set_xlabel("Δ score (late−early)"); ax.grid(True, axis="x", alpha=0.25)
        pdf.savefig(fig); plt.close(fig)

        meta = pdf.infodict()
        meta["Title"] = "DOE2 SJ900 vs SJ1300 knee pattern"
    (arts / out.name).write_bytes(out.read_bytes())


def main():
    out = Path("example/output/DOE2_knee_pattern")
    out.mkdir(parents=True, exist_ok=True)
    arms = [
        ("SJ900", Path("example/fixtures/doe/DOE1/set4_SJ900")),
        ("SJ1300", Path("example/fixtures/doe/DOE2/SJ1300_dry")),
    ]
    traj = {}
    rows = []
    for arm, folder in arms:
        for path in sorted(folder.glob("*_raw.csv")):
            # skip tiny incomplete if any
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


if __name__ == "__main__":
    main()
