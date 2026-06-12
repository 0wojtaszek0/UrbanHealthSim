"""
Wykresy funkcji ABM: reguła stabilności populacji.

Wczytuje wyniki pełnego gridsearch ABM (12x12 = 144 punktów), wyciąga empiryczne
punkty stabilności (gdzie score(FM, MM) ≈ 0), dopasowuje krzywą sigmoidalną
typu tanh i porównuje z liniową regułą z modelu proxy.

Wynik: pojedynczy interaktywny HTML z 3 panelami Plotly.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from typing import List, Tuple

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import curve_fit

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.gridspec import GridSpec


# =============================================================================
# 1. WCZYTANIE PRAWDZIWYCH DANYCH ABM
# =============================================================================

def load_abm_gridsearch() -> List[dict]:
    """Wczytaj wyniki najnowszego gridsearch ABM."""
    candidates = sorted(glob.glob("results/gridsearch_full_abm_no_rf_*.json"))
    if not candidates:
        sys.exit("Brak pliku results/gridsearch_full_abm_no_rf_*.json w katalogu roboczym.")
    path = candidates[-1]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"Wczytano {len(data)} punktów z {path}")
    return data


def to_matrix(records: List[dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Zwróć (fms, mms, Z) — siatkę FM, MM oraz macierz score Z[mm, fm]."""
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


# =============================================================================
# 2. WYCIĄGNIĘCIE EMPIRYCZNYCH PUNKTÓW STABILNOŚCI
# =============================================================================

def empirical_stability_line(fms: np.ndarray, mms: np.ndarray, Z: np.ndarray
                             ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Dla każdego MM znajdź wartość FM, w której score(FM, MM) = 0.

    Interpolacja liniowa między dwoma kolejnymi wartościami FM, gdzie funkcja
    score zmienia znak. Jeśli wiersz nigdy nie przecina zera — pomijamy MM.
    """
    stable_fm: List[float] = []
    stable_mm: List[float] = []
    for i, mm in enumerate(mms):
        row = Z[i, :]
        for j in range(len(fms) - 1):
            a, b = row[j], row[j + 1]
            if np.isnan(a) or np.isnan(b):
                continue
            if a <= 0 <= b or b <= 0 <= a:
                t = -a / (b - a) if b != a else 0.5
                fm_star = fms[j] + t * (fms[j + 1] - fms[j])
                stable_fm.append(fm_star)
                stable_mm.append(mm)
                break
    return np.array(stable_mm), np.array(stable_fm)


# =============================================================================
# 3. DOPASOWANIE KRZYWEJ TANH
# =============================================================================

def tanh_model(mm: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """FM_stable(MM) = a + b · tanh(c · (MM - d))."""
    return a + b * np.tanh(c * (mm - d))


def fit_tanh(stable_mm: np.ndarray, stable_fm: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Dopasuj parametry (a, b, c, d) metodą najmniejszych kwadratów.

    Ograniczenia (bounds) wymuszają sigmoidalny kształt w naszym zakresie:
      a ∈ [1.0, 2.5]   — wartość środkowa (między dolną a górną asymptotą)
      b ∈ [0.1, 1.0]   — amplituda (odległość od środka do asymptot)
      c ∈ [0.5, 5.0]   — nachylenie (czyli "stromość" sigmoidy)
      d ∈ [-0.5, 1.5]  — punkt przegięcia w naszym zakresie MM
    Bez tych granic curve_fit znajduje degeneracyjne rozwiązania, w których
    tanh staje się niemal liniowy w zakresie obserwacji.
    """
    p0 = [1.7, 0.35, 2.5, 0.4]
    bounds = ([1.0, 0.10, 0.5, -0.5], [2.5, 1.0, 5.0, 1.5])
    popt, pcov = curve_fit(
        tanh_model, stable_mm, stable_fm,
        p0=p0, bounds=bounds, maxfev=10000,
    )
    return popt, pcov


# =============================================================================
# 4. WIZUALIZACJA — 3 PANELE PLOTLY
# =============================================================================

PROXY_SLOPE = 0.01560 / 0.00830  # = 1.88, BASE_CDR/BASE_CBR (model "Przybliżony")

NAVY = "#1B2A41"
GOLD = "#A07840"
TEAL = "#2C5F7C"
INK_SOFT = "#34495E"
RED = "#C0392B"


def make_figure(fms: np.ndarray, mms: np.ndarray, Z: np.ndarray,
                stable_mm: np.ndarray, stable_fm: np.ndarray,
                tanh_params: np.ndarray) -> go.Figure:
    a, b, c, d = tanh_params
    mm_dense = np.linspace(mms.min(), mms.max(), 200)
    fm_abm = tanh_model(mm_dense, *tanh_params)
    fm_approx = PROXY_SLOPE * mm_dense
    asymptote_upper = a + b

    fig = make_subplots(
        rows=2, cols=1,
        specs=[[{"type": "heatmap"}], [{"type": "xy"}]],
        subplot_titles=(
            "<b>Score(FM, MM) — pełny ABM 50k × 50 lat × 144 punkty</b>",
            "<b>Reguła stabilności FM(MM)</b>",
        ),
        row_heights=[0.55, 0.45],
        vertical_spacing=0.15,
    )

    # -------- Panel A: heatmapa rzeczywistych score --------
    fig.add_trace(
        go.Heatmap(
            x=fms, y=mms, z=Z,
            colorscale=[
                [0.0, "#2C5F7C"],
                [0.5, "#FDFDFB"],
                [1.0, "#C0392B"],
            ],
            zmid=0,
            colorbar=dict(title="Score [%]", thickness=14, len=0.50,
                          y=0.78, yanchor="middle"),
            hovertemplate="FM = %{x:.2f}<br>MM = %{y:.2f}<br>Score = %{z:.1f}%<extra></extra>",
        ),
        row=1, col=1,
    )

    # nakładka: linia Przybliżony 1.88·MM
    fig.add_trace(
        go.Scatter(
            x=PROXY_SLOPE * mms, y=mms,
            mode="lines", line=dict(color=GOLD, width=2, dash="dash"),
            name=f"Przybliżony:  FM = {PROXY_SLOPE:.2f}·MM",
            hovertemplate="Przybliżony<br>FM=%{x:.2f}, MM=%{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # nakładka: krzywa ABM
    fig.add_trace(
        go.Scatter(
            x=fm_abm, y=mm_dense,
            mode="lines", line=dict(color=NAVY, width=3),
            name="ABM",
            hovertemplate="ABM<br>FM=%{x:.2f}, MM=%{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # -------- Panel B: krzywa FM_stable(MM) --------
    fig.add_trace(
        go.Scatter(
            x=mm_dense, y=fm_approx,
            mode="lines", line=dict(color=GOLD, width=2, dash="dash"),
            name="Przybliżony",
            showlegend=False,
            hovertemplate="Przybliżony: FM=%{y:.3f}<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=mm_dense, y=fm_abm,
            mode="lines", line=dict(color=NAVY, width=3),
            name="ABM",
            showlegend=False,
            hovertemplate="ABM: FM=%{y:.3f}<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_hline(
        y=asymptote_upper, line=dict(color=TEAL, width=1, dash="dot"),
        annotation_text=f"asymptota górna ≈ {asymptote_upper:.2f}",
        annotation_position="top right",
        annotation_font_size=10,
        row=2, col=1,
    )

    # -------- Layout ogólny --------
    fig.update_layout(
        title=dict(
            text=(
                "<b>Reguła stabilności populacji — pełny ABM vs Przybliżony</b><br>"
                f"<sub>Empiryczny fit: FM(MM) = {a:.3f} + {b:.3f}·tanh({c:.3f}·(MM − {d:.3f}))</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=17, color=NAVY),
        ),
        height=900, width=1100,
        paper_bgcolor="#FDFDFB",
        plot_bgcolor="#FDFDFB",
        font=dict(family="Inter, Arial, sans-serif", size=12, color=NAVY),
        legend=dict(
            x=0.99, y=0.99, xanchor="right", yanchor="top",
            bgcolor="rgba(253,253,251,0.85)", bordercolor=GOLD, borderwidth=1,
        ),
        margin=dict(l=70, r=30, t=110, b=60),
    )

    fig.update_xaxes(title_text="Fertility Multiplier (FM)", row=1, col=1)
    fig.update_yaxes(title_text="Mortality Multiplier (MM)", row=1, col=1)
    fig.update_xaxes(title_text="Mortality Multiplier (MM)", row=2, col=1,
                     showgrid=True, gridcolor="#E0E5EB")
    fig.update_yaxes(title_text="FM stabilności", row=2, col=1,
                     showgrid=True, gridcolor="#E0E5EB")

    return fig


# =============================================================================
# 4b. WIZUALIZACJA — MATPLOTLIB (eksport do JPG)
# =============================================================================

def make_figure_matplotlib(fms: np.ndarray, mms: np.ndarray, Z: np.ndarray,
                           stable_mm: np.ndarray, stable_fm: np.ndarray,
                           tanh_params: np.ndarray) -> plt.Figure:
    """Statyczny odpowiednik wykresu Plotly do zapisu jako JPG.

    Układ: dwa panele jeden pod drugim (heatmapa + krzywa stabilności).
    """
    a, b, c, d = tanh_params
    mm_dense = np.linspace(mms.min(), mms.max(), 200)
    fm_abm = tanh_model(mm_dense, *tanh_params)
    fm_approx = PROXY_SLOPE * mm_dense
    asymptote_upper = a + b

    # Paleta zgodna z prezentacją: granat / bronz / teal / czerwień
    cmap = LinearSegmentedColormap.from_list(
        "abm_stab", ["#2C5F7C", "#FDFDFB", "#C0392B"], N=256,
    )

    fig = plt.figure(figsize=(11, 12), facecolor="#FDFDFB")
    gs = GridSpec(
        2, 1, figure=fig,
        height_ratios=[1.1, 1.0],
        hspace=0.32,
        left=0.10, right=0.94, top=0.92, bottom=0.07,
    )

    # ---- Panel A: heatmapa ---------------------------------------------------
    axA = fig.add_subplot(gs[0, 0])
    fm_step = (fms[1] - fms[0]) / 2.0
    mm_step = (mms[1] - mms[0]) / 2.0
    extent = (fms[0] - fm_step, fms[-1] + fm_step,
              mms[0] - mm_step, mms[-1] + mm_step)
    vmax = max(abs(np.nanmin(Z)), abs(np.nanmax(Z)))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    im = axA.imshow(
        Z, origin="lower", extent=extent, aspect="auto",
        cmap=cmap, norm=norm, interpolation="bilinear",
    )
    cbar = fig.colorbar(im, ax=axA, pad=0.015, shrink=0.85)
    cbar.set_label("Score [%]", fontsize=10, color="#1B2A41")
    cbar.ax.tick_params(labelsize=9, colors="#1B2A41")

    # Nakładki
    axA.plot(PROXY_SLOPE * mms, mms, "--", color="#A07840", linewidth=2,
             label=f"Przybliżony: FM = {PROXY_SLOPE:.2f}·MM")
    axA.plot(fm_abm, mm_dense, "-", color="#1B2A41", linewidth=2.5,
             label="ABM")

    axA.set_xlim(fms[0] - fm_step, fms[-1] + fm_step)
    axA.set_ylim(mms[0] - mm_step, mms[-1] + mm_step)
    axA.set_xlabel("Fertility Multiplier (FM)", fontsize=11, color="#1B2A41")
    axA.set_ylabel("Mortality Multiplier (MM)", fontsize=11, color="#1B2A41")
    axA.set_title(
        "Score(FM, MM) — pełny ABM 50k × 50 lat × 144 punkty",
        fontsize=12, weight="bold", color="#1B2A41", pad=10,
    )
    axA.legend(loc="upper left", fontsize=9, framealpha=0.92,
               edgecolor="#A07840")
    axA.tick_params(colors="#1B2A41", labelsize=9)
    for spine in axA.spines.values():
        spine.set_color("#D8DEE5")

    # ---- Panel B: krzywa FM_stable(MM) --------------------------------------
    axB = fig.add_subplot(gs[1, 0])
    axB.plot(mm_dense, fm_approx, "--", color="#A07840", linewidth=2,
             label=f"Przybliżony  {PROXY_SLOPE:.2f}·MM")
    axB.plot(mm_dense, fm_abm, "-", color="#1B2A41", linewidth=2.5,
             label="ABM")
    axB.axhline(asymptote_upper, color="#2C5F7C", linestyle=":", linewidth=1.2)
    axB.text(mm_dense[-1], asymptote_upper, f"  asymptota ≈ {asymptote_upper:.2f}",
             color="#2C5F7C", fontsize=9, va="center")

    axB.set_xlabel("Mortality Multiplier (MM)", fontsize=11, color="#1B2A41")
    axB.set_ylabel("FM stabilności", fontsize=11, color="#1B2A41")
    axB.set_title("Reguła stabilności FM(MM)",
                  fontsize=12, weight="bold", color="#1B2A41", pad=10)
    axB.legend(loc="lower right", fontsize=9, framealpha=0.92,
               edgecolor="#A07840")
    axB.grid(True, color="#E0E5EB", linewidth=0.6)
    axB.set_facecolor("#FDFDFB")
    axB.tick_params(colors="#1B2A41", labelsize=9)
    for spine in axB.spines.values():
        spine.set_color("#D8DEE5")

    # ---- Tytuł i podtytuł ---------------------------------------------------
    fig.suptitle(
        "Reguła stabilności populacji — pełny ABM vs Przybliżony",
        fontsize=16, weight="bold", color="#1B2A41", y=0.975,
    )
    fig.text(
        0.5, 0.945,
        f"Empiryczny fit:  FM(MM) = {a:.3f} + {b:.3f}·tanh({c:.3f}·(MM − {d:.3f}))",
        fontsize=10, color="#34495E", ha="center", style="italic",
    )

    return fig


# =============================================================================
# 5. MAIN
# =============================================================================

def main() -> None:
    records = load_abm_gridsearch()
    fms, mms, Z = to_matrix(records)

    stable_mm, stable_fm = empirical_stability_line(fms, mms, Z)
    print(f"\nZnaleziono {len(stable_mm)} empirycznych punktów stabilności:")
    for mm, fm in zip(stable_mm, stable_fm):
        print(f"  MM = {mm:.3f}  →  FM* = {fm:.3f}")

    popt, _ = fit_tanh(stable_mm, stable_fm)
    a, b, c, d = popt
    print(f"\nDopasowany fit:")
    print(f"  FM(MM) = {a:.4f} + {b:.4f} · tanh({c:.4f} · (MM − {d:.4f}))")
    print(f"  Asymptota górna (MM → +∞): a + b = {a + b:.4f}")
    print(f"  Asymptota dolna (MM → −∞): a − b = {a - b:.4f}")
    print(f"  Środek transition:         MM = d = {d:.4f}")

    # Tabela porównawcza w wybranych punktach
    print(f"\n{'MM':>6} {'FM_Przybl':>12} {'FM_ABM':>10} {'ΔFM':>10}")
    for mm_val in [0.3, 0.5, 0.7, 1.0, 1.3, 1.6]:
        fp = PROXY_SLOPE * mm_val
        fa = tanh_model(np.array([mm_val]), *popt)[0]
        print(f"{mm_val:>6.2f} {fp:>12.3f} {fa:>10.3f} {fa - fp:>+10.3f}")

    # --- HTML (Plotly, interaktywny) ---
    fig_html = make_figure(fms, mms, Z, stable_mm, stable_fm, popt)
    out_html = "wykresy_funkcji_abm.html"
    fig_html.write_html(out_html, include_plotlyjs="cdn", full_html=True)
    print(f"\n✓ Zapisano: {out_html}")

    # --- JPG (matplotlib, statyczny, 300 dpi) ---
    fig_mpl = make_figure_matplotlib(fms, mms, Z, stable_mm, stable_fm, popt)
    out_jpg = "wykresy_funkcji_abm.jpg"
    fig_mpl.savefig(out_jpg, dpi=300, format="jpg", facecolor=fig_mpl.get_facecolor(),
                    bbox_inches="tight", pil_kwargs={"quality": 92})
    plt.close(fig_mpl)
    print(f"✓ Zapisano: {out_jpg}")


if __name__ == "__main__":
    main()
