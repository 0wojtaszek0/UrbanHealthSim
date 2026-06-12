"""
Piramida wieku i płci dla optymalnego punktu gridsearcha.
FM=2.1182, MM=1.1273  (score ≈ -0.023%, populacja quasi-stabilna)
"""
import multiprocessing as mp

FM_OPT = 2.118181818181818
MM_OPT = 1.1272727272727272
POPULATION_SIZE = 50_000
SIM_MONTHS = 600  # 50 lat

AGE_ORDER = [f"{s}-{s+4}" for s in range(0, 90, 5)] + ["90-94", "95-99", "100+"]


def run_sim(fm, mm, seed=42):
    from simulation_engine import SimulationEngine
    from disease_model import DiseaseModel

    engine = SimulationEngine(disease_model=DiseaseModel(), seed=seed)
    engine.fertility_rate = fm
    engine.mortality_multiplier = mm
    engine.household_split_probability = 0.001

    engine._create_synthetic_population(POPULATION_SIZE)
    initial_pop = sum(1 for c in engine.citizens.values() if c.alive)

    engine.run(months=SIM_MONTHS)

    final_pop = sum(1 for c in engine.citizens.values() if c.alive)
    score = ((final_pop - initial_pop) / initial_pop) * 100

    years = sorted(engine.yearly_stats.keys())
    pyramid = engine.yearly_stats[years[-1]]["age_pyramid"] if years else {}

    return pyramid, score, final_pop, initial_pop


def main():
    import plotly.graph_objects as go

    print(f"Uruchamiam symulację: FM={FM_OPT:.4f}, MM={MM_OPT:.4f}")
    print(f"Populacja: {POPULATION_SIZE:,}  |  {SIM_MONTHS} miesięcy (50 lat)")

    pyramid, score, final_pop, initial_pop = run_sim(FM_OPT, MM_OPT)

    males   = [pyramid.get(b, {}).get("male",   0) for b in AGE_ORDER]
    females = [pyramid.get(b, {}).get("female", 0) for b in AGE_ORDER]

    total_m = sum(males)
    total_f = sum(females)

    print(f"\nWyniki:")
    print(f"  Populacja startowa:  {initial_pop:,}")
    print(f"  Populacja końcowa:   {final_pop:,}  ({score:+.4f}%)")
    print(f"  Mężczyźni:           {total_m:,}")
    print(f"  Kobiety:             {total_f:,}")
    print(f"  Stosunek K/M:        {total_f/total_m:.3f}" if total_m else "")

    color_score = "#27ae60" if abs(score) <= 2 else ("#c0392b" if score > 0 else "#2471a3")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=AGE_ORDER,
        x=[-m for m in males],
        name="Mężczyźni",
        orientation="h",
        marker_color="#2980b9",
        hovertemplate="<b>%{y}</b><br>Mężczyźni: %{customdata}<extra></extra>",
        customdata=males,
    ))
    fig.add_trace(go.Bar(
        y=AGE_ORDER,
        x=females,
        name="Kobiety",
        orientation="h",
        marker_color="#e74c3c",
        hovertemplate="<b>%{y}</b><br>Kobiety: %{x}<extra></extra>",
    ))

    # Etykiety wartości bezwzględnych na osi X
    max_val = max(max(males), max(females)) if males or females else 1
    tick_step = max(50, (max_val // 100) * 20)
    tick_vals = list(range(-max_val - tick_step, max_val + tick_step + 1, tick_step))

    fig.update_layout(
        barmode="overlay",
        title=dict(
            text=(
                f"<b>Piramida wieku i płci – punkt optymalny gridsearcha</b><br>"
                f"<sub>FM={FM_OPT:.4f}  |  MM={MM_OPT:.4f}  |  "
                f"Populacja: {POPULATION_SIZE:,} → <b>{final_pop:,}</b>  "
                f"(<span style='color:{color_score}'><b>{score:+.4f}%</b></span>)  |  50 lat</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=16),
        ),
        height=750, width=900,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(
            title="Liczba osób",
            zeroline=True, zerolinecolor="black", zerolinewidth=2,
            showgrid=True, gridcolor="#eeeeee",
            tickvals=tick_vals,
            ticktext=[str(abs(v)) for v in tick_vals],
        ),
        yaxis=dict(title="Grupa wiekowa", autorange=True),
        legend=dict(x=0.5, y=-0.06, xanchor="center", orientation="h", font=dict(size=13)),
        font=dict(family="Arial, sans-serif", size=11),
        annotations=[
            dict(
                text=(
                    f"<b>Mężczyźni: {total_m:,}</b>"
                ),
                x=-0.02, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=12, color="#2980b9"),
                xanchor="right",
            ),
            dict(
                text=(
                    f"<b>Kobiety: {total_f:,}</b>"
                ),
                x=1.02, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=12, color="#e74c3c"),
                xanchor="left",
            ),
        ],
    )

    out = "piramida_optimum.html"
    fig.write_html(out)
    print(f"\n✓ Zapisano: {out}")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
