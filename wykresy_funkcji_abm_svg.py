"""
Generuje dwa osobne wykresy SVG (wektorowe — idealna jakość przy dowolnym
powiększeniu), które zastępują rastrowe „wyniki gridsercha po lewej.png"
oraz „wyniki gridserch po prawej.png" w prezentacji index.html.

Wynik:
  wykres_score_heatmap.svg   — Panel A: Score(FM, MM) heatmapa + nakładki
  wykres_regula_stabilnosci.svg — Panel B: krzywa FM_stable(MM) z asymptotą
"""
from __future__ import annotations

import glob
import json
import sys
from typing import List, Tuple

import numpy as np
from scipy.optimize import curve_fit

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


# =============================================================================
# DANE
# =============================================================================

def load_abm_gridsearch() -> List[dict]:
    candidates = sorted(glob.glob("results/gridsearch_full_abm_no_rf_*.json"))
    if not candidates:
        sys.exit("Brak pliku results/gridsearch_full_abm_no_rf_*.json")
    with open(candidates[-1], encoding="utf-8") as f:
        return json.load(f)


def to_matrix(records: List[dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    pts = [
        (r["params"]["fertility_multiplier"],
         r["params"]["mortality_multiplier"],
         r["score"])
        for r in records
    ]
    fms = np.array(sorted({p[0] for p in pts}))
    mms = np.array(sorted({p[1] for p in pts}))
    Z = np.full((len(mms), len(fms)), np.nan)
    for fm, mm, s in pts:
        i = int(np.argmin(np.abs(mms - mm)))
        j = int(np.argmin(np.abs(fms - fm)))
        Z[i, j] = s
    return fms, mms, Z


def empirical_stability_line(fms, mms, Z):
    stable_fm, stable_mm = [], []
    for i, mm in enumerate(mms):
        row = Z[i, :]
        for j in range(len(fms) - 1):
            a, b = row[j], row[j + 1]
            if np.isnan(a) or np.isnan(b):
                continue
            if a <= 0 <= b or b <= 0 <= a:
                t = -a / (b - a) if b != a else 0.5
                stable_fm.append(fms[j] + t * (fms[j + 1] - fms[j]))
                stable_mm.append(mm)
                break
    return np.array(stable_mm), np.array(stable_fm)


def tanh_model(mm, a, b, c, d):
    return a + b * np.tanh(c * (mm - d))


def fit_tanh(stable_mm, stable_fm):
    p0 = [1.7, 0.35, 2.5, 0.4]
    bounds = ([1.0, 0.10, 0.5, -0.5], [2.5, 1.0, 5.0, 1.5])
    popt, _ = curve_fit(tanh_model, stable_mm, stable_fm,
                        p0=p0, bounds=bounds, maxfev=10000)
    return popt


# =============================================================================
# WYKRESY
# =============================================================================

PROXY_SLOPE = 0.01560 / 0.00830  # = 1.88

NAVY = "#1B2A41"
GOLD = "#A07840"
TEAL = "#2C5F7C"
INK_SOFT = "#34495E"
RULE = "#D8DEE5"
PAPER = "#FDFDFB"

# Wspólne ustawienia typograficzne
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Arial", "Helvetica", "DejaVu Sans"],
    "axes.edgecolor": RULE,
    "axes.labelcolor": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "text.color": NAVY,
})


def make_heatmap_svg(fms, mms, Z, tanh_params, path: str) -> None:
    """Panel A — heatmapa Score(FM, MM) z nakładkami ABM i Przybliżony."""
    a, b, c, d = tanh_params
    mm_dense = np.linspace(mms.min(), mms.max(), 200)
    fm_abm = tanh_model(mm_dense, *tanh_params)

    cmap = LinearSegmentedColormap.from_list(
        "abm_stab", ["#2C5F7C", "#FDFDFB", "#C0392B"], N=256,
    )

    fig, ax = plt.subplots(figsize=(11, 7), facecolor=PAPER)
    fm_step = (fms[1] - fms[0]) / 2.0
    mm_step = (mms[1] - mms[0]) / 2.0
    extent = (fms[0] - fm_step, fms[-1] + fm_step,
              mms[0] - mm_step, mms[-1] + mm_step)
    vmax = max(abs(np.nanmin(Z)), abs(np.nanmax(Z)))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    im = ax.imshow(
        Z, origin="lower", extent=extent, aspect="auto",
        cmap=cmap, norm=norm, interpolation="bilinear",
    )
    cbar = fig.colorbar(im, ax=ax, pad=0.015, shrink=0.92)
    cbar.set_label("Score [%]", fontsize=12, color=NAVY)
    cbar.ax.tick_params(labelsize=10, colors=NAVY)

    ax.plot(PROXY_SLOPE * mms, mms, "--", color=GOLD, linewidth=2.2,
            label=f"Przybliżony: FM = {PROXY_SLOPE:.2f}·MM")
    ax.plot(fm_abm, mm_dense, "-", color=NAVY, linewidth=2.8, label="ABM")

    ax.set_xlim(fms[0] - fm_step, fms[-1] + fm_step)
    ax.set_ylim(mms[0] - mm_step, mms[-1] + mm_step)
    ax.set_xlabel("Fertility Multiplier (FM)", fontsize=13)
    ax.set_ylabel("Mortality Multiplier (MM)", fontsize=13)
    ax.tick_params(labelsize=11)
    ax.legend(loc="upper left", fontsize=11, framealpha=0.95,
              edgecolor=GOLD, facecolor=PAPER)
    ax.set_facecolor(PAPER)
    for spine in ax.spines.values():
        spine.set_color(RULE)

    fig.tight_layout()
    fig.savefig(path, format="svg", facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ Zapisano: {path}")


def make_stability_curve_svg(mms, tanh_params, path: str) -> None:
    """Panel B — krzywa FM_stable(MM) z asymptotą i porównaniem do 1.88·MM."""
    a, b, c, d = tanh_params
    mm_dense = np.linspace(mms.min(), mms.max(), 400)
    fm_abm = tanh_model(mm_dense, *tanh_params)
    fm_approx = PROXY_SLOPE * mm_dense
    asymptote_upper = a + b

    fig, ax = plt.subplots(figsize=(11, 7), facecolor=PAPER)
    ax.plot(mm_dense, fm_approx, "--", color=GOLD, linewidth=2.2,
            label=f"Przybliżony  {PROXY_SLOPE:.2f}·MM")
    ax.plot(mm_dense, fm_abm, "-", color=NAVY, linewidth=2.8, label="ABM")
    ax.axhline(asymptote_upper, color=TEAL, linestyle=":", linewidth=1.4)
    ax.text(mm_dense[-1], asymptote_upper,
            f"  asymptota ≈ {asymptote_upper:.2f}",
            color=TEAL, fontsize=11, va="center")

    ax.set_xlabel("Mortality Multiplier (MM)", fontsize=13)
    ax.set_ylabel("FM stabilności", fontsize=13)
    ax.tick_params(labelsize=11)
    ax.legend(loc="lower right", fontsize=11, framealpha=0.95,
              edgecolor=GOLD, facecolor=PAPER)
    ax.grid(True, color="#E0E5EB", linewidth=0.7)
    ax.set_facecolor(PAPER)
    for spine in ax.spines.values():
        spine.set_color(RULE)

    fig.tight_layout()
    fig.savefig(path, format="svg", facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ Zapisano: {path}")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    records = load_abm_gridsearch()
    fms, mms, Z = to_matrix(records)
    stable_mm, stable_fm = empirical_stability_line(fms, mms, Z)
    popt = fit_tanh(stable_mm, stable_fm)

    make_heatmap_svg(fms, mms, Z, popt, "wykres_score_heatmap.svg")
    make_stability_curve_svg(mms, popt, "wykres_regula_stabilnosci.svg")


if __name__ == "__main__":
    main()
