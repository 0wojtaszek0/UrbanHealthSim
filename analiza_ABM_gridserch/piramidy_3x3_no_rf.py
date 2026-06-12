"""
Siatka 3×3 piramid wieku dla ABM gridsearch (BEZ risk factors).

Bierze 9 punktów z siatki 12×12 — skrajne + środkowe indeksy:
  fm_idx = [0, 6, 11]  → FM = [0.40, 1.545, 2.50]
  mm_idx = [0, 6, 11]  → MM = [0.30, 1.009, 1.60]

Dla każdego punktu:
  - 50 000 agentów × 50 lat (600 mies.)
  - Wszystkie risk factors = 0 (kalibracja zgodna z gridsearch_full_abm_no_rf.py)
  - Cox model aktywny ale bez amplifikacji (exp(β·0)=1)
  - Bazowy onset z baseline_hazard × Gompertz growth

Wynik: piramidy_3x3_no_rf.html — siatka 3×3 piramid z adnotacjami
       (score%, n, mediana wieku, prevalencje CVD/LC).
"""
import multiprocessing as mp
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

# Pozwala importować simulation_engine, disease_model, citizen z parent dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))


PARAM_GRID = {
    "fertility_multiplier":  np.linspace(0.4, 2.5, 12),
    "mortality_multiplier":  np.linspace(0.3, 1.6, 12),
}

POPULATION_SIZE = 50_000
SIM_MONTHS = 600  # 50 lat
SEED = 42

AGE_ORDER = [f"{s}-{s+4}" for s in range(0, 90, 5)] + ["90-94", "95-99", "100+"]


def run_sim_no_rf(fm: float, mm: float, seed: int = SEED):
    from simulation_engine import SimulationEngine
    from disease_model import DiseaseModel
    from citizen import Citizen

    engine = SimulationEngine(disease_model=DiseaseModel(), seed=seed)
    engine.fertility_rate = fm
    engine.mortality_multiplier = mm
    engine.household_split_probability = 0.001

    engine._create_synthetic_population(POPULATION_SIZE)

    # Zerowanie RF — kalibracja zgodna z gridsearch_full_abm_no_rf.py
    zero_rfs = {rf: 0 for rf in Citizen.DEFAULT_RISK_FACTORS}
    for c in engine.citizens.values():
        c.risk_factors = zero_rfs.copy()

    initial_pop = sum(1 for c in engine.citizens.values() if c.alive)

    engine.run(months=SIM_MONTHS)

    alive = [c for c in engine.citizens.values() if c.alive]
    final_pop = len(alive)
    score = ((final_pop - initial_pop) / initial_pop) * 100 if initial_pop else 0.0

    years = sorted(engine.yearly_stats.keys())
    pyramid = engine.yearly_stats[years[-1]]["age_pyramid"] if years else {}

    n_alive = max(len(alive), 1)
    cvd_prev = sum(1 for c in alive if c.diseases.get("CVD", 0) == 1) / n_alive * 100
    lc_prev = sum(1 for c in alive if c.diseases.get("Lung Cancer", 0) == 1) / n_alive * 100
    ages = sorted(c.age_years for c in alive)
    median_age = ages[len(ages) // 2] if ages else 0.0

    return {
        "pyramid":     pyramid,
        "score":       score,
        "final_pop":   final_pop,
        "initial_pop": initial_pop,
        "median_age":  median_age,
        "cvd_prev":    cvd_prev,
        "lc_prev":     lc_prev,
    }


def _worker(args):
    fm, mm, seed = args
    try:
        return (fm, mm, run_sim_no_rf(fm, mm, seed), None)
    except Exception as e:
        import traceback
        return (fm, mm, None, f"{e}\n{traceback.format_exc()}")


def pyramid_bars(pyramid: dict):
    males = [pyramid.get(b, {}).get("male", 0) for b in AGE_ORDER]
    females = [pyramid.get(b, {}).get("female", 0) for b in AGE_ORDER]
    return males, females


def score_color(score: float) -> str:
    if score > 2:
        return "#c0392b"
    if score < -2:
        return "#2471a3"
    return "#27ae60"


def main():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fm_vals = PARAM_GRID["fertility_multiplier"]
    mm_vals = PARAM_GRID["mortality_multiplier"]

    fm_idx = [0, len(fm_vals) // 2, len(fm_vals) - 1]
    mm_idx = [0, len(mm_vals) // 2, len(mm_vals) - 1]

    # Kolejność: wiersz=mm, kolumna=fm → 9 kombinacji
    combos = [(float(mm_vals[mi]), float(fm_vals[fi])) for mi in mm_idx for fi in fm_idx]
    tasks = [(fm, mm, SEED) for mm, fm in combos]

    print("=" * 78)
    print("PIRAMIDY 3×3 — ABM gridsearch, bez risk factors")
    print("=" * 78)
    print(f"  Siatka:    9 punktów (skrajne + środkowe z 12×12)")
    print(f"  FM ∈ {[f'{fm_vals[i]:.2f}' for i in fm_idx]}")
    print(f"  MM ∈ {[f'{mm_vals[i]:.2f}' for i in mm_idx]}")
    print(f"  Populacja: {POPULATION_SIZE:,} | {SIM_MONTHS} mies. ({SIM_MONTHS//12} lat)")
    n_workers = min(mp.cpu_count(), len(tasks)) if tasks else 1
    print(f"  Workers:   {n_workers} rdzeni")
    print("=" * 78)

    sim_results = {}
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futures = {ex.submit(_worker, t): t for t in tasks}
        done = 0
        for fut in as_completed(futures):
            done += 1
            fm, mm, result, err = fut.result()
            if err:
                print(f"  [{done}/9] BŁĄD FM={fm:.3f} MM={mm:.3f}: {err.splitlines()[0]}")
                sim_results[(fm, mm)] = None
            else:
                print(f"  [{done}/9] FM={fm:.3f} MM={mm:.3f} → "
                      f"score={result['score']:+7.2f}%  pop={result['final_pop']:>6,}  "
                      f"mediana={result['median_age']:.1f}lat  "
                      f"CVD={result['cvd_prev']:4.1f}%  LC={result['lc_prev']:4.2f}%")
                sim_results[(fm, mm)] = result

    # ---------------- Wizualizacja ----------------
    subtitles = [f"FM={fm:.2f} | MM={mm:.2f}" for mm, fm in combos]
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=subtitles,
        vertical_spacing=0.10,
        horizontal_spacing=0.06,
    )

    for idx, (mm, fm) in enumerate(combos):
        row = idx // 3 + 1
        col = idx % 3 + 1
        r = sim_results.get((fm, mm))
        if r is None:
            continue

        males, females = pyramid_bars(r["pyramid"])

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

        # Adnotacja w komórce
        ann = (
            f"<b>{r['score']:+.1f}%</b>  n={r['final_pop']:,}<br>"
            f"<sub>mediana {r['median_age']:.0f}lat | "
            f"CVD {r['cvd_prev']:.1f}% | LC {r['lc_prev']:.2f}%</sub>"
        )
        fig.add_annotation(
            row=row, col=col,
            text=ann,
            x=0.5, y=0.98, xref="x domain", yref="y domain",
            xanchor="center", yanchor="top", showarrow=False,
            font=dict(size=9, color=score_color(r["score"])),
            bgcolor="rgba(255,255,255,0.82)", bordercolor="lightgray",
            borderwidth=1, borderpad=3,
        )

    fig.update_layout(
        barmode="overlay",
        title=dict(
            text=(
                "<b>Siatka 3×3 piramid wieku — ABM gridsearch (BEZ risk factors)</b><br>"
                "<sub>Kolumny: FM ↑ | Wiersze: MM ↑ | "
                f"{POPULATION_SIZE:,} agentów × {SIM_MONTHS//12} lat | "
                "Cox aktywny ale exp(β·0)=1</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=15),
        ),
        height=1300, width=1500,
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(x=0.5, y=-0.03, xanchor="center", orientation="h"),
        font=dict(family="Arial, sans-serif", size=10),
    )

    for i in range(1, 10):
        key = f"xaxis{i if i > 1 else ''}"
        fig.update_layout({key: dict(
            zeroline=True, zerolinecolor="black", zerolinewidth=1.5,
            showgrid=True, gridcolor="#eeeeee",
        )})

    out = "piramidy_3x3_no_rf.html"
    fig.write_html(out)
    print(f"\n✓ Zapisano: {out}")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
