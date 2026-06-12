"""
Analiza piramid wieku i płci dla różnych wartości gridsearch.
Populacja: 50 000, symulacja: 50 lat (600 miesięcy).

Parametry:
  fertility_multiplier  - mnożnik płodności (1.0 = kalibracja ABM, CBR≈8.3/1000/rok)
  mortality_multiplier  - mnożnik śmiertelności (1.0 = kalibracja ABM, CDR≈15.6/1000/rok)
  Punkt stabilności: fertility_mult ≈ 1.88 × mortality_mult

Generuje:
  piramidy_gridsearch_siatka.html    - 9 piramid (3×3 siatka z gridsearch)
  piramidy_diagonale_gridsearch.html - profil wzdłuż 3 zestawów diagonali (4 punkty każdy)
"""

import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Parametry – SPÓJNE z grid_search_improved_v3_fixed.py
# ---------------------------------------------------------------------------
PARAM_GRID = {
    "fertility_multiplier":  np.linspace(0.4, 2.5, 12),
    "mortality_multiplier":  np.linspace(0.3, 1.6, 12),
}

POPULATION_SIZE = 50_000
SIM_MONTHS      = 600        # 50 lat

# Grupy wiekowe produkowane przez SimulationEngine._build_age_pyramid
AGE_ORDER = [f"{s}-{s+4}" for s in range(0, 90, 5)] + ["90-94", "95-99", "100+"]


# ---------------------------------------------------------------------------
# Symulacja (musi być na poziomie modułu dla multiprocessingu)
# ---------------------------------------------------------------------------
def run_sim(fertility_multiplier: float, mortality_multiplier: float, seed: int = 42):
    """
    Uruchom pełną symulację ABM (50 000 agentów, 50 lat).
    Zwraca (pyramid_dict, score_pct, final_pop).

    POPRAWNA implementacja: fertility_rate i mortality_multiplier to
    bezpośrednie mnożniki domyślnych tabel – tak jak w SimulationEngine.
    Wartość 1.0 = polskie dane demograficzne.
    """
    from simulation_engine import SimulationEngine
    from disease_model import DiseaseModel

    disease_model = DiseaseModel()
    engine = SimulationEngine(disease_model=disease_model, seed=seed)

    # Bezpośrednie mnożniki – NIE skalujemy tabel, tylko ustawiamy mnożniki
    engine.fertility_rate       = fertility_multiplier
    engine.mortality_multiplier = mortality_multiplier
    engine.household_split_probability = 0.001

    engine._create_synthetic_population(POPULATION_SIZE)
    initial_pop = sum(1 for c in engine.citizens.values() if c.alive)

    engine.run(months=SIM_MONTHS)

    final_pop = sum(1 for c in engine.citizens.values() if c.alive)
    score = ((final_pop - initial_pop) / initial_pop) * 100

    years = sorted(engine.yearly_stats.keys())
    pyramid = engine.yearly_stats[years[-1]]["age_pyramid"] if years else {}

    return pyramid, score, final_pop


def _worker(args):
    """Wrapper do multiprocessingu (musi być na poziomie modułu)."""
    fm, mm, seed = args
    try:
        pyramid, score, final_pop = run_sim(fm, mm, seed)
        return (fm, mm, pyramid, score, final_pop, None)
    except Exception as e:
        return (fm, mm, {}, float('nan'), 0, str(e))


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------
def pyramid_bars(pyramid: dict):
    males   = [pyramid.get(b, {}).get("male",   0) for b in AGE_ORDER]
    females = [pyramid.get(b, {}).get("female", 0) for b in AGE_ORDER]
    return males, females


def score_color(score: float) -> str:
    if score > 2:
        return "#c0392b"   # czerwony – wzrost
    elif score < -2:
        return "#2471a3"   # niebieski – spadek
    return "#27ae60"       # zielony – stabilny


def _run_parallel(tasks: list) -> dict:
    """
    Uruchom zadania równolegle.
    tasks: lista (fertility_mult, mortality_mult, seed)
    Zwraca dict {(fm, mm): (pyramid, score, final_pop)}
    """
    n_workers = min(mp.cpu_count(), len(tasks))
    print(f"  Parallel execution: {len(tasks)} symulacji × {n_workers} wątków CPU")

    results = {}
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futures = {ex.submit(_worker, t): t for t in tasks}
        done = 0
        for fut in as_completed(futures):
            done += 1
            fm, mm, pyramid, score, final_pop, err = fut.result()
            if err:
                print(f"  [BŁĄD] FM={fm:.3f} MM={mm:.3f}: {err}")
            else:
                print(f"  [{done}/{len(tasks)}] FM={fm:.3f} MM={mm:.3f} → "
                      f"score={score:+.1f}%  final_pop={final_pop}")
            results[(fm, mm)] = (pyramid, score, final_pop)
    return results


# ---------------------------------------------------------------------------
# 1. Siatka 3×3
# ---------------------------------------------------------------------------
def create_grid_pyramids(output_file: str = "piramidy_gridsearch_siatka.html"):
    """
    9 piramid na siatce 3×3 wybranych z przestrzeni gridsearch.
    Kolumny: fertility_multiplier (niski→wysoki)
    Wiersze:  mortality_multiplier (niski→wysoki)
    """
    fm_vals = PARAM_GRID["fertility_multiplier"]
    mm_vals = PARAM_GRID["mortality_multiplier"]

    fm_idx = [0, len(fm_vals) // 2, len(fm_vals) - 1]
    mm_idx = [0, len(mm_vals) // 2, len(mm_vals) - 1]

    # (mm, fm) – wiersz=mm, kolumna=fm
    combos = [(mm_vals[mi], fm_vals[fi]) for mi in mm_idx for fi in fm_idx]

    tasks = [(fm, mm, 42) for mm, fm in combos]

    print("\n=== [1/2] Piramidy 3×3 ===")
    sim_results = _run_parallel(tasks)

    subtitles = [f"FM={fm:.2f} | MM={mm:.2f}" for mm, fm in combos]
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=subtitles,
        vertical_spacing=0.14,
        horizontal_spacing=0.07,
    )

    for idx, (mm, fm) in enumerate(combos):
        row = idx // 3 + 1
        col = idx % 3 + 1
        pyramid, score, final_pop = sim_results.get((fm, mm), ({}, float('nan'), 0))
        males, females = pyramid_bars(pyramid)

        show_leg = (idx == 0)
        fig.add_trace(go.Bar(
            y=AGE_ORDER, x=[-m for m in males],
            name="Mężczyźni", orientation="h",
            marker_color="#2980b9", showlegend=show_leg,
            hovertemplate="<b>%{y}</b><br>M: %{customdata}<extra></extra>",
            customdata=males,
        ), row=row, col=col)
        fig.add_trace(go.Bar(
            y=AGE_ORDER, x=females,
            name="Kobiety", orientation="h",
            marker_color="#e74c3c", showlegend=show_leg,
            hovertemplate="<b>%{y}</b><br>K: %{x}<extra></extra>",
        ), row=row, col=col)

        fig.add_annotation(
            row=row, col=col,
            text=f"<b>{score:+.1f}%</b>  n={final_pop}",
            x=0.5, y=0.98, xref="x domain", yref="y domain",
            xanchor="center", yanchor="top", showarrow=False,
            font=dict(size=9, color=score_color(score)),
        )

    fig.update_layout(
        barmode="overlay",
        title=dict(
            text=(
                "<b>Piramidy wieku i płci – różne wartości gridsearch (50 000 os., 50 lat)</b><br>"
                "<sub>Kolumny: fertility_multiplier (↑)  |  Wiersze: mortality_multiplier (↑)</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=15),
        ),
        height=1300, width=1400,
        paper_bgcolor="white",
        legend=dict(x=0.5, y=-0.03, xanchor="center", orientation="h"),
        font=dict(family="Arial, sans-serif", size=10),
    )
    for i in range(1, 10):
        key = f"xaxis{i if i > 1 else ''}"
        fig.update_layout({key: dict(
            zeroline=True, zerolinecolor="black", zerolinewidth=1.5,
            showgrid=True, gridcolor="lightgray",
        )})

    fig.write_html(output_file)
    print(f"\n✓ Zapisano: {output_file}")


# ---------------------------------------------------------------------------
# 2. Profile wzdłuż diagonali – 3 zestawy
# ---------------------------------------------------------------------------
def create_diagonal_profiles(output_file: str = "piramidy_diagonale_gridsearch.html"):
    """
    Zmiana profilu wzdłuż 3 zestawów punktów z diagonali gridsearch.
      Zestaw 1: główna przekątna        (FM[i], MM[i])
      Zestaw 2: wyższa płodność +2 poz. (FM[i+2], MM[i])
      Zestaw 3: wyższa śmiertelność +2  (FM[i], MM[i+2])
    Każdy zestaw ma 4 punkty.
    """
    fm_vals = PARAM_GRID["fertility_multiplier"]
    mm_vals = PARAM_GRID["mortality_multiplier"]
    n     = min(len(fm_vals), len(mm_vals))
    shift = 2

    step     = max(1, n // 4)
    diag_idx = [min(i * step, n - 1) for i in range(4)]

    sets = [
        {
            "label":   "Zestaw 1: Główna przekątna",
            "color_m": "#2980b9", "color_f": "#e74c3c",
            "points":  [(fm_vals[min(i, n-1)],       mm_vals[min(i, n-1)])       for i in diag_idx],
        },
        {
            "label":   "Zestaw 2: Wyższy fertility (+2)",
            "color_m": "#27ae60", "color_f": "#f39c12",
            "points":  [(fm_vals[min(i+shift, n-1)], mm_vals[min(i, n-1)])       for i in diag_idx],
        },
        {
            "label":   "Zestaw 3: Wyższy mortality (+2)",
            "color_m": "#8e44ad", "color_f": "#c0392b",
            "points":  [(fm_vals[min(i, n-1)],       mm_vals[min(i+shift, n-1)]) for i in diag_idx],
        },
    ]

    # Zbierz unikalne (fm, mm) do równoległego uruchomienia
    unique = list({(fm, mm) for s in sets for fm, mm in s["points"]})
    tasks  = [(fm, mm, 42) for fm, mm in unique]

    print("\n=== [2/2] Profile diagonalne (3 zestawy × 4 punkty) ===")
    sim_results = _run_parallel(tasks)

    n_rows = len(sets)
    n_cols = len(diag_idx)

    subtitles = []
    for s in sets:
        for fm, mm in s["points"]:
            subtitles.append(f"FM={fm:.2f} / MM={mm:.2f}")

    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=subtitles,
        shared_yaxes="rows",
        vertical_spacing=0.12,
        horizontal_spacing=0.05,
    )

    for si, s in enumerate(sets):
        row = si + 1
        for pi, (fm, mm) in enumerate(s["points"]):
            col = pi + 1
            pyramid, score, final_pop = sim_results.get((fm, mm), ({}, float('nan'), 0))
            males, females = pyramid_bars(pyramid)

            show_leg = (si == 0 and pi == 0)
            fig.add_trace(go.Bar(
                y=AGE_ORDER, x=[-m for m in males],
                name="Mężczyźni", orientation="h",
                marker_color=s["color_m"], showlegend=show_leg,
                hovertemplate="<b>%{y}</b><br>M: %{customdata}<extra></extra>",
                customdata=males,
            ), row=row, col=col)
            fig.add_trace(go.Bar(
                y=AGE_ORDER, x=females,
                name="Kobiety", orientation="h",
                marker_color=s["color_f"], showlegend=show_leg,
                hovertemplate="<b>%{y}</b><br>K: %{x}<extra></extra>",
            ), row=row, col=col)

            fig.add_annotation(
                row=row, col=col,
                text=f"<b>{score:+.1f}%</b>  n={final_pop}",
                x=0.5, y=0.98, xref="x domain", yref="y domain",
                xanchor="center", yanchor="top", showarrow=False,
                font=dict(size=9, color=score_color(score)),
            )

    # Etykiety zestawów po lewej stronie
    for si, s in enumerate(sets):
        y_pos = 1.0 - (si + 0.5) / n_rows
        fig.add_annotation(
            x=-0.02, y=y_pos, xref="paper", yref="paper",
            text=f"<b>{s['label']}</b>",
            showarrow=False, textangle=-90,
            font=dict(size=10), xanchor="right", yanchor="middle",
        )

    fig.update_layout(
        barmode="overlay",
        title=dict(
            text=(
                "<b>Zmiana profilu wieku wzdłuż diagonali gridsearch – 3 zestawy (50 000 os., 50 lat)</b><br>"
                "<sub>"
                "Z1: główna przekątna  |  "
                "Z2: fertility+2 poz.  |  "
                "Z3: mortality+2 poz."
                "</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=14),
        ),
        height=1600, width=1600,
        paper_bgcolor="white",
        legend=dict(x=0.5, y=-0.02, xanchor="center", orientation="h"),
        font=dict(family="Arial, sans-serif", size=9),
    )
    for i in range(1, n_rows * n_cols + 1):
        key = f"xaxis{i if i > 1 else ''}"
        fig.update_layout({key: dict(
            zeroline=True, zerolinecolor="black", zerolinewidth=1.5,
            showgrid=True, gridcolor="lightgray",
        )})

    fig.write_html(output_file)
    print(f"\n✓ Zapisano: {output_file}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Na macOS/Windows multiprocessing wymaga guard
    mp.set_start_method("spawn", force=True)

    print("=" * 65)
    print("ANALIZA PIRAMID WIEKU – GRIDSEARCH")
    print(f"Populacja: {POPULATION_SIZE:,}  |  Symulacja: {SIM_MONTHS} miesięcy (50 lat)")
    print(f"Parametry: fertility_mult ∈ [{PARAM_GRID['fertility_multiplier'][0]:.2f}, "
          f"{PARAM_GRID['fertility_multiplier'][-1]:.2f}]  |  "
          f"mortality_mult ∈ [{PARAM_GRID['mortality_multiplier'][0]:.2f}, "
          f"{PARAM_GRID['mortality_multiplier'][-1]:.2f}]")
    print(f"Stabilność: fertility_mult ≈ 1.88 × mortality_mult")
    print("=" * 65)

    create_grid_pyramids("piramidy_gridsearch_siatka.html")
    create_diagonal_profiles("piramidy_diagonale_gridsearch.html")

    print("\n" + "=" * 65)
    print("GOTOWE!")
    print("  → piramidy_gridsearch_siatka.html")
    print("  → piramidy_diagonale_gridsearch.html")
    print("=" * 65)
