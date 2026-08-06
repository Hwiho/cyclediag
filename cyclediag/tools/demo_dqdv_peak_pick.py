"""Demo: how cyclediag picks dQ/dV peaks (Q-interp 500pt + robust find_peaks)."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.features.dqdv_peaks import (  # noqa: E402
    DEFAULT_DQDV_PEAK_CONFIG,
    _noise_mad,
    _robust_peak_indices,
    _smooth,
    find_dqdv_peaks,
    prepare_dqdv_arrays,
)


def synthetic_leg(n: int = 220, peak_v: float = 3.55):
    """Charge-like V–Q with one main dQ/dV hump near peak_v + small noise spikes."""
    rng = np.random.default_rng(42)
    v = np.linspace(3.05, 4.12, n)
    q = 52 * (1 - np.exp(-(v - 3.05) / 0.30))
    bump = 70 * np.exp(-((v - peak_v) ** 2) / (2 * 0.020**2))
    q = q + np.cumsum(bump) * (v[1] - v[0])
    for _ in range(25):
        i = int(rng.integers(15, n - 15))
        if abs(v[i] - peak_v) < 0.07:
            continue
        q[i] += rng.uniform(0.03, 0.12)
    return v, q


def main():
    cfg = DEFAULT_DQDV_PEAK_CONFIG
    v_raw, q_raw = synthetic_leg()
    vx, dqdv, _, _ = prepare_dqdv_arrays(v_raw, q_raw, cfg)
    y_smooth = _smooth(dqdv, window=cfg.sg_window, poly=cfg.sg_poly)
    idx, _ = _robust_peak_indices(dqdv, cfg)
    peaks = find_dqdv_peaks(v_raw, q_raw, max_peaks=4, config=cfg)

    y_abs = np.abs(y_smooth)
    ymax = float(np.nanmax(y_abs))
    mad = _noise_mad(dqdv, y_smooth)
    prom = max(cfg.prominence_frac * ymax, cfg.mad_prominence_factor * mad * 1.4826, 1e-9)
    distance = max(cfg.min_width_points, int(cfg.n_interp * cfg.min_distance_frac))

  # also show rejected narrow spikes from a looser find_peaks
    all_idx, _ = find_peaks(
        y_abs,
        prominence=prom * 0.3,
        distance=3,
        width=1,
    )
    rejected = [i for i in all_idx if i not in set(idx)]

    out = ROOT / "example" / "docs" / "dqdv_peak_pick_demo.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(13, 9), facecolor="#fafafa")
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.2, 0.9], hspace=0.38, wspace=0.28)

    # --- Panel A: raw V-Q ---
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.plot(q_raw, v_raw, color="#2563eb", lw=1.2, label="raw V(Q)")
    ax0.set_xlabel("Capacity Q")
    ax0.set_ylabel("Voltage V")
    ax0.set_title("① Raw charge leg")
    ax0.grid(alpha=0.25)
    ax0.legend(fontsize=8)

    # --- Panel B: after Q-interp 500 ---
    ax1 = fig.add_subplot(gs[0, 1])
    ax1.plot(vx, dqdv, color="#94a3b8", lw=0.8, alpha=0.7, label="dQ/dV (500pt Q-grid)")
    ax1.plot(vx, y_smooth, color="#0f766e", lw=2.0, label=f"SG smooth w={cfg.sg_window}")
    ax1.set_xlabel("Voltage V")
    ax1.set_ylabel("dQ/dV")
    ax1.set_title("② Q-axis 500pt → dQ/dV + smooth")
    ax1.grid(alpha=0.25)
    ax1.legend(fontsize=8)

    # --- Panel C: peak picking (main) ---
    ax2 = fig.add_subplot(gs[1, :])
    ax2.plot(vx, np.abs(dqdv), color="#cbd5e1", lw=0.9, label="|dQ/dV| raw")
    ax2.plot(vx, y_abs, color="#0f766e", lw=2.2, label="|dQ/dV| smoothed")
    if rejected:
        ax2.scatter(vx[rejected], y_abs[rejected], s=28, c="#f97316", marker="x",
                    linewidths=1.5, zorder=4, label=f"rejected spikes ({len(rejected)})")
    if len(idx):
        ax2.scatter(vx[idx], y_abs[idx], s=90, facecolors="none", edgecolors="#dc2626",
                    linewidths=2.2, zorder=5, label="kept peaks")
        for i, p in zip(idx, peaks):
            ax2.annotate(
                f"peak @ {p['V']:.3f} V",
                xy=(vx[i], y_abs[i]),
                xytext=(vx[i] + 0.06, y_abs[i] * 0.85),
                fontsize=9, color="#991b1b",
                arrowprops=dict(arrowstyle="->", color="#991b1b", lw=1.2),
            )
    ax2.axhline(prom, color="#7c3aed", ls="--", lw=1.2, alpha=0.8,
                label=f"prominence floor ≈ {prom:.2g}")
    ax2.set_xlabel("Voltage V")
    ax2.set_ylabel("|dQ/dV|")
    ax2.set_title("③ Peak pick: prominence + width + distance + spike filter")
    ax2.grid(alpha=0.25)
    ax2.legend(loc="upper right", fontsize=8, ncol=2)

    # --- Panel D: flow diagram (text) ---
    ax3 = fig.add_subplot(gs[2, :])
    ax3.axis("off")
    steps = [
        ("Q uniform 500pt", "pne_studio와 동일 보간"),
        ("dQ/dV + |dV|≥1mV", "고전압 knee artifact 제거"),
        ("SG smooth", f"window={cfg.sg_window}"),
        ("find_peaks", f"prom≥{cfg.prominence_frac:.0%}·max, dist≥{distance}pt, width≥{cfg.min_width_points}"),
        ("spike filter", f"raw/smooth ≤ {cfg.spike_ratio_max}"),
        ("merge + rank", f"ΔV<{cfg.merge_v_sep_v*1000:.0f}mV 병합"),
    ]
    x0, y0 = 0.02, 0.55
    for k, (title, sub) in enumerate(steps):
        x = x0 + k * 0.165
        ax3.add_patch(plt.Rectangle((x, y0), 0.14, 0.35, fill=True,
                                    facecolor="#e0f2fe", edgecolor="#0284c7", lw=1.2))
        ax3.text(x + 0.07, y0 + 0.24, title, ha="center", va="center", fontsize=9, fontweight="bold")
        ax3.text(x + 0.07, y0 + 0.10, sub, ha="center", va="center", fontsize=7.5, color="#334155")
        if k < len(steps) - 1:
            ax3.add_patch(FancyArrowPatch((x + 0.145, y0 + 0.17), (x + 0.165, y0 + 0.17),
                                          arrowstyle="->", mutation_scale=12, color="#64748b"))

    peak_txt = ", ".join(f"{p['V']:.3f}V (H={p['H']:.2g})" for p in peaks) or "(none)"
    ax3.text(0.02, 0.08,
             f"Result on demo data: {len(peaks)} peak(s) → {peak_txt}",
             fontsize=10, color="#0f172a")

    fig.suptitle("cyclediag dQ/dV peak picking demo (Q-interp 500pt)", fontsize=13, fontweight="bold", y=0.98)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(out)
    print("PEAKS:", peaks)


if __name__ == "__main__":
    main()
