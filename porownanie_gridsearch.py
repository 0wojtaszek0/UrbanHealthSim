"""
Porównanie 3 heatmap obok siebie:

  Panel A: PROXY (grid_search_improved_v3_fixed) — analityczny, ~30s, brak ABM
  Panel B: ABM   (gridsearch_full_abm_no_rf)    — pełny ABM bez RF, ~49 min
  Panel C: DELTA (B − A)                          — gdzie proxy się myli

Dodatkowo: tabela z 5 punktami stabilności wg każdej metody + reguła stabilności.
"""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm


PROXY_JSON = "results/gridsearch_results_v3_fixed_20260504_131837.json"
ABM_JSON   = "results/gridsearch_full_abm_no_rf_20260511_114958.json"


def load_grid(path: str):
    """
    Wczytaj JSON i zwróć (fm_vals, mm_vals, score_grid).
    score_grid[mm_idx, fm_idx] = score%
    """
    with open(path) as f:
        data = json.load(f)

    fm_vals = sorted({r["params"]["fertility_multiplier"] for r in data})
    mm_vals = sorted({r["params"]["mortality_multiplier"] for r in data})

    grid = np.full((len(mm_vals), len(fm_vals)), np.nan)
    for r in data:
        fm = r["params"]["fertility_multiplier"]
        mm = r["params"]["mortality_multiplier"]
        fm_idx = int(np.argmin([abs(v - fm) for v in fm_vals]))
        mm_idx = int(np.argmin([abs(v - mm) for v in mm_vals]))
        grid[mm_idx, fm_idx] = r.get("score", np.nan)

    return np.array(fm_vals), np.array(mm_vals), grid


def render(ax, grid, fm_vals, mm_vals, title, vmin, vmax, vcenter=0.0):
    norm = TwoSlopeNorm(vcenter=vcenter, vmin=vmin, vmax=vmax)
    im = ax.imshow(grid, cmap="RdBu_r", norm=norm, aspect="auto", origin="lower")
    ax.set_xticks(range(len(fm_vals)))
    ax.set_xticklabels([f"{v:.2f}" for v in fm_vals], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(mm_vals)))
    ax.set_yticklabels([f"{v:.2f}" for v in mm_vals], fontsize=8)
    ax.set_xlabel("FM", fontsize=10)
    ax.set_ylabel("MM", fontsize=10)
    ax.set_title(title, fontsize=11)

    for mm_idx in range(len(mm_vals)):
        for fm_idx in range(len(fm_vals)):
            v = grid[mm_idx, fm_idx]
            if not np.isnan(v):
                color = "white" if abs(v) > 35 else "black"
                ax.text(fm_idx, mm_idx, f"{v:+.0f}",
                        ha="center", va="center", color=color, fontsize=6)

    return im


def main():
    fm_p, mm_p, grid_proxy = load_grid(PROXY_JSON)
    fm_a, mm_a, grid_abm   = load_grid(ABM_JSON)

    # Sanity check — siatki muszą być te same
    if not (np.allclose(fm_p, fm_a, atol=1e-3) and np.allclose(mm_p, mm_a, atol=1e-3)):
        print("BŁĄD: siatki proxy i ABM nie są zgodne")
        sys.exit(1)

    delta = grid_abm - grid_proxy   # różnica per komórka

    # Diagnostyka
    print("=" * 78)
    print("PORÓWNANIE PROXY ↔ ABM (144 punktów, identyczna siatka 12×12)")
    print("=" * 78)
    print(f"  Proxy:  range [{np.nanmin(grid_proxy):+.1f}%, {np.nanmax(grid_proxy):+.1f}%]"
          f"  median {np.nanmedian(grid_proxy):+.1f}%")
    print(f"  ABM:    range [{np.nanmin(grid_abm):+.1f}%, {np.nanmax(grid_abm):+.1f}%]"
          f"  median {np.nanmedian(grid_abm):+.1f}%")
    print(f"  Δ=ABM−proxy: range [{np.nanmin(delta):+.1f}%, {np.nanmax(delta):+.1f}%]"
          f"  mean |Δ| = {np.nanmean(np.abs(delta)):.1f}%")
    print()

    # Punkty stabilne wg obu
    print("PUNKTY STABILNE (|score| < 2%)")
    print()
    print("  Proxy:")
    proxy_stable = []
    for mm_idx, mm in enumerate(mm_p):
        for fm_idx, fm in enumerate(fm_p):
            s = grid_proxy[mm_idx, fm_idx]
            if not np.isnan(s) and abs(s) < 2.0:
                proxy_stable.append((fm, mm, s))
    for fm, mm, s in sorted(proxy_stable, key=lambda x: abs(x[2]))[:5]:
        print(f"    FM={fm:.3f}  MM={mm:.3f}  score={s:+.2f}%  →  ABM score = {grid_abm[mm_p.tolist().index(mm), fm_p.tolist().index(fm)]:+.2f}%")

    print()
    print("  ABM:")
    abm_stable = []
    for mm_idx, mm in enumerate(mm_a):
        for fm_idx, fm in enumerate(fm_a):
            s = grid_abm[mm_idx, fm_idx]
            if not np.isnan(s) and abs(s) < 2.0:
                abm_stable.append((fm, mm, s))
    for fm, mm, s in sorted(abm_stable, key=lambda x: abs(x[2]))[:5]:
        proxy_at = grid_proxy[mm_a.tolist().index(mm), fm_a.tolist().index(fm)]
        print(f"    FM={fm:.3f}  MM={mm:.3f}  score={s:+.2f}%  →  Proxy score = {proxy_at:+.2f}%")

    # ------------------------------------------------------------
    # Wizualizacja 3 paneli + delta
    # ------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))

    # Wspólny zakres dla A i B
    vmin = min(np.nanmin(grid_proxy), np.nanmin(grid_abm))
    vmax = max(np.nanmax(grid_proxy), np.nanmax(grid_abm))

    im_a = render(axes[0], grid_proxy, fm_p, mm_p,
                  f"A: PROXY analityczny (~30s)\n"
                  f"range [{np.nanmin(grid_proxy):+.0f}%, {np.nanmax(grid_proxy):+.0f}%]",
                  vmin, vmax)
    plt.colorbar(im_a, ax=axes[0], fraction=0.046, pad=0.04, label="score %")

    im_b = render(axes[1], grid_abm, fm_a, mm_a,
                  f"B: ABM pełny bez RF (~49 min)\n"
                  f"range [{np.nanmin(grid_abm):+.0f}%, {np.nanmax(grid_abm):+.0f}%]",
                  vmin, vmax)
    plt.colorbar(im_b, ax=axes[1], fraction=0.046, pad=0.04, label="score %")

    # Delta: symetryczna skala
    d_max = max(abs(np.nanmin(delta)), abs(np.nanmax(delta)))
    im_c = render(axes[2], delta, fm_a, mm_a,
                  f"C: DELTA = ABM − PROXY\n"
                  f"mean |Δ| = {np.nanmean(np.abs(delta)):.1f}%, max |Δ| = {d_max:.0f}%",
                  -d_max, d_max)
    plt.colorbar(im_c, ax=axes[2], fraction=0.046, pad=0.04, label="ABM − Proxy (pp)")

    fig.suptitle(
        "Gridsearch comparison: analityczny proxy vs. pełny ABM bez risk factors\n"
        f"144 punktów (12×12) | populacja 50 000 | 50 lat | seed=42",
        fontsize=13, y=1.00,
    )

    plt.tight_layout()
    out = "porownanie_gridsearch_proxy_vs_abm.png"
    plt.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"\n✓ Heatmapa porównawcza: {out}")

    # ------------------------------------------------------------
    # Reguła stabilności — fit liniowy na punktach blisko stabilności
    # ------------------------------------------------------------
    print()
    print("REGUŁA STABILNOŚCI: FM_stable jako funkcja MM")
    print()
    # Dla każdego MM znajdź FM, dla którego score ~ 0 (interpolacja)
    print("  MM   |  Proxy FM_stable  |  ABM FM_stable")
    print("  -----+-------------------+----------------")
    for mm_idx, mm in enumerate(mm_a):
        # Interpolacja: znajdź FM gdzie score przechodzi przez 0
        def interp_zero(scores):
            for i in range(len(scores) - 1):
                if scores[i] * scores[i+1] < 0:  # przejście przez 0
                    fm0, fm1 = fm_a[i], fm_a[i+1]
                    s0, s1 = scores[i], scores[i+1]
                    return fm0 - s0 * (fm1 - fm0) / (s1 - s0)
            return None

        proxy_fm = interp_zero(grid_proxy[mm_idx, :])
        abm_fm   = interp_zero(grid_abm[mm_idx, :])

        proxy_str = f"{proxy_fm:.3f}" if proxy_fm else "  poza"
        abm_str   = f"{abm_fm:.3f}"   if abm_fm   else "  poza"
        diff = ""
        if proxy_fm and abm_fm:
            diff = f"  (Δ = {abm_fm - proxy_fm:+.3f})"
        print(f"  {mm:.2f} |       {proxy_str:>8s}     |      {abm_str:>8s}{diff}")


if __name__ == "__main__":
    main()
