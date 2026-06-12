"""
Porównanie 2 piramid wieku z aktywnym modelem ryzyka (Cox-style cumulative hazard):

  Lewy panel:  OPTIMUM gridsearcha           FM=2.12, MM=1.13
  Prawy panel: DOLNY-ŚRODKOWY z siatki 3x3   FM=1.55, MM=1.60

Cel: pokazać efekt "wycinania" górnej części piramidy po dodaniu dynamicznego
modelu chorób (CVD, Lung Cancer) reagującego na risk factors (smoking,
obesity, inactivity, alcohol, hypertension, hipercholesterolemia, family hist.).
"""
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

POPULATION_SIZE = 50_000
SIM_MONTHS = 600  # 50 lat

POINTS = [
    {
        "label":   "OPTIMUM gridsearcha",
        "fm":      2.118181818181818,
        "mm":      1.1272727272727272,
        "note":    "baseline quasi-stabilny przed modelem ryzyka",
        "color_m": "#2980b9",
        "color_f": "#e74c3c",
    },
    {
        "label":   "DOLNY-ŚRODKOWY siatki 3x3",
        "fm":      1.5454545454545454,
        "mm":      1.6,
        "note":    "wysoka śmiertelność + niska płodność",
        "color_m": "#34495e",
        "color_f": "#9b59b6",
    },
]

AGE_ORDER = [f"{s}-{s+4}" for s in range(0, 90, 5)] + ["90-94", "95-99", "100+"]


def run_sim(fm: float, mm: float, seed: int = 42):
    from simulation_engine import SimulationEngine
    from disease_model import DiseaseModel

    engine = SimulationEngine(disease_model=DiseaseModel(), seed=seed)
    engine.fertility_rate = fm
    engine.mortality_multiplier = mm
    engine.household_split_probability = 0.001

    engine._create_synthetic_population(POPULATION_SIZE)
    initial_pop = sum(1 for c in engine.citizens.values() if c.alive)

    engine.run(months=SIM_MONTHS)

    alive = [c for c in engine.citizens.values() if c.alive]
    final_pop = len(alive)
    score = ((final_pop - initial_pop) / initial_pop) * 100

    years = sorted(engine.yearly_stats.keys())
    pyramid = engine.yearly_stats[years[-1]]["age_pyramid"] if years else {}

    # Statystyki chorobowe końcowe
    disease_stats = {}
    for disease in DiseaseModel.DEFAULT_DISEASES:
        prev = sum(1 for c in alive if c.diseases.get(disease, 0) == 1)
        prev_pct = prev / max(len(alive), 1) * 100
        h_mean = sum(c.cumulative_hazard.get(disease, 0.0) for c in alive) / max(len(alive), 1)
        disease_stats[disease] = {"prevalence_pct": prev_pct, "mean_H_cum": h_mean}

    # Risk factor breakdown
    smokers = [c for c in alive if c.risk_factors.get("smoking", 0) == 1]
    non_smokers = [c for c in alive if c.risk_factors.get("smoking", 0) == 0]
    n_alive = max(len(alive), 1)
    rf_stats = {
        "smoking_pct":      len(smokers) / n_alive * 100,
        "obesity_pct":      sum(1 for c in alive if c.risk_factors.get("obesity", 0) == 1) / n_alive * 100,
        "inactivity_pct":   sum(1 for c in alive if c.risk_factors.get("physical_inactivity", 0) == 1) / n_alive * 100,
        "chol_pct":         sum(1 for c in alive if c.risk_factors.get("high_cholesterol", 0) == 1) / n_alive * 100,
        "hypertension_pct": sum(1 for c in alive if c.risk_factors.get("hypertension_stage0", 0) == 1) / n_alive * 100,
    }

    # Mediana wieku (po wycięciu dolnych grup pokazuje "starzenie się")
    ages = sorted(c.age_years for c in alive)
    median_age = ages[len(ages) // 2] if ages else 0.0

    return {
        "pyramid":        pyramid,
        "score":          score,
        "initial_pop":    initial_pop,
        "final_pop":      final_pop,
        "disease_stats":  disease_stats,
        "rf_stats":       rf_stats,
        "median_age":     median_age,
    }


def _worker(args):
    label, fm, mm, seed = args
    try:
        result = run_sim(fm, mm, seed)
        return (label, result, None)
    except Exception as e:
        import traceback
        return (label, None, f"{e}\n{traceback.format_exc()}")


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

    print("=" * 75)
    print("PORÓWNANIE PIRAMID — model ryzyka Cox (CVD + Lung Cancer + Hipercholesterol.)")
    print(f"Populacja: {POPULATION_SIZE:,} | Symulacja: {SIM_MONTHS} mies. ({SIM_MONTHS//12} lat)")
    print("=" * 75)

    tasks = [(p["label"], p["fm"], p["mm"], 42) for p in POINTS]
    n_workers = min(mp.cpu_count(), len(tasks)) if tasks else 1

    print(f"\nUruchamiam {len(tasks)} symulacji równolegle na {n_workers} rdzeniach...")
    results = {}
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futures = {ex.submit(_worker, t): t for t in tasks}
        for fut in as_completed(futures):
            label, result, err = fut.result()
            if err:
                print(f"  [BŁĄD] {label}: {err}")
            else:
                print(f"  [OK]  {label}: score={result['score']:+.2f}%  "
                      f"final_pop={result['final_pop']}")
            results[label] = result

    # Wypisz statystyki chorobowe
    print("\n" + "=" * 75)
    print("STATYSTYKI KOŃCOWE (po 50 latach)")
    print("=" * 75)
    for p in POINTS:
        r = results.get(p["label"])
        if r is None:
            continue
        print(f"\n[{p['label']}]  FM={p['fm']:.4f}  MM={p['mm']:.4f}")
        print(f"  Populacja:  {r['initial_pop']:,} → {r['final_pop']:,}  ({r['score']:+.2f}%)")
        print(f"  Mediana wieku: {r['median_age']:.1f} lat")
        for disease, ds in r["disease_stats"].items():
            print(f"  {disease:25s} prev={ds['prevalence_pct']:5.2f}%  mean H_cum={ds['mean_H_cum']:.4f}")
        rf = r["rf_stats"]
        print(f"  RF: smoking={rf['smoking_pct']:.1f}%  obesity={rf['obesity_pct']:.1f}%  "
              f"chol={rf['chol_pct']:.1f}%  hyper={rf['hypertension_pct']:.1f}%")

    # ------------------------------------------------------------------
    # Wizualizacja
    # ------------------------------------------------------------------
    subtitles = [
        f"<b>{p['label']}</b><br>FM={p['fm']:.2f} | MM={p['mm']:.2f} | {p['note']}"
        for p in POINTS
    ]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=subtitles,
        shared_yaxes=True,
        horizontal_spacing=0.10,
    )

    max_count = 0
    for col_idx, p in enumerate(POINTS, start=1):
        r = results.get(p["label"])
        if r is None:
            continue
        males, females = pyramid_bars(r["pyramid"])
        max_count = max(max_count, max(males + females, default=0))

        show_leg = (col_idx == 1)
        fig.add_trace(go.Bar(
            y=AGE_ORDER, x=[-m for m in males],
            name="Mężczyźni", orientation="h",
            marker_color=p["color_m"], showlegend=show_leg,
            hovertemplate="<b>%{y}</b><br>M: %{customdata}<extra></extra>",
            customdata=males,
        ), row=1, col=col_idx)
        fig.add_trace(go.Bar(
            y=AGE_ORDER, x=females,
            name="Kobiety", orientation="h",
            marker_color=p["color_f"], showlegend=show_leg,
            hovertemplate="<b>%{y}</b><br>K: %{x}<extra></extra>",
        ), row=1, col=col_idx)

        # Adnotacja: score + statystyki chorobowe + RF (zwięźle)
        ds = r["disease_stats"]
        rf = r["rf_stats"]
        ann_text = (
            f"<b>{r['score']:+.1f}%</b>  n={r['final_pop']:,}  "
            f"<span style='color:#555'>(mediana {r['median_age']:.0f} lat)</span><br>"
            f"<sub><b>Choroby:</b> CVD {ds['CVD']['prevalence_pct']:.1f}%  |  "
            f"LC {ds['Lung Cancer']['prevalence_pct']:.2f}%</sub><br>"
            f"<sub><b>RF:</b> palenie {rf['smoking_pct']:.0f}%  |  "
            f"otyłość {rf['obesity_pct']:.0f}%  |  "
            f"chol {rf['chol_pct']:.0f}%  |  "
            f"hiper {rf['hypertension_pct']:.0f}%</sub>"
        )
        fig.add_annotation(
            row=1, col=col_idx,
            text=ann_text,
            x=0.5, y=0.99, xref="x domain", yref="y domain",
            xanchor="center", yanchor="top", showarrow=False,
            font=dict(size=11, color=score_color(r["score"])),
            align="center",
            bgcolor="rgba(255,255,255,0.85)", bordercolor="lightgray",
            borderwidth=1, borderpad=6,
        )

    # Symetryczne osie X
    tick_step = max(50, (max_count // 100) * 20)
    tick_vals = list(range(-max_count - tick_step, max_count + tick_step + 1, tick_step))
    tick_text = [str(abs(v)) for v in tick_vals]

    fig.update_layout(
        barmode="overlay",
        title=dict(
            text=(
                "<b>Piramida wieku z dynamicznym modelem ryzyka (Cox)</b><br>"
                "<sub>2 choroby: CVD, Lung Cancer | 7 risk factors (w tym hipercholesterolemia) | "
                f"akumulacja H_cum przez 50 lat | {POPULATION_SIZE:,} agentów</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=16),
        ),
        height=800, width=1500,
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(x=0.5, y=-0.06, xanchor="center", orientation="h", font=dict(size=12)),
        font=dict(family="Arial, sans-serif", size=11),
    )

    for col_idx in (1, 2):
        axis_name = "xaxis" if col_idx == 1 else f"xaxis{col_idx}"
        fig.update_layout({axis_name: dict(
            title="Liczba osób",
            zeroline=True, zerolinecolor="black", zerolinewidth=2,
            showgrid=True, gridcolor="#eeeeee",
            tickvals=tick_vals, ticktext=tick_text,
        )})
    fig.update_yaxes(title="Grupa wiekowa", row=1, col=1)

    out = "piramida_porownanie_ryzyko.html"
    fig.write_html(out)
    print(f"\n✓ Zapisano: {out}")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
