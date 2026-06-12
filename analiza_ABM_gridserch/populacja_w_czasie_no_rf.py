"""
Trajektorie ludności w czasie (50 lat) dla 2 scenariuszy ABM bez RF:

  Lewy panel:  ABM OPTIMUM — FM=1.927, MM=1.009
  Prawy panel: DOLNY-ŚRODKOWY 3×3 — FM=1.545, MM=1.60

Pokazuje: total population + M/F, prevalencje końcowe CVD/LC.
"""
import multiprocessing as mp
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))


POPULATION_SIZE = 50_000
SIM_MONTHS = 600

POINTS = [
    {
        "label": "ABM OPTIMUM",
        "fm":    1.9272727272727272,
        "mm":    1.0090909090909091,
        "color": "#2980b9",
    },
    {
        "label": "DOLNY-ŚRODKOWY siatki 3×3",
        "fm":    1.5454545454545454,
        "mm":    1.6,
        "color": "#c0392b",
    },
]


def run_sim_yearly(fm: float, mm: float, seed: int = 42):
    from simulation_engine import SimulationEngine
    from disease_model import DiseaseModel
    from citizen import Citizen

    engine = SimulationEngine(disease_model=DiseaseModel(), seed=seed)
    engine.fertility_rate = fm
    engine.mortality_multiplier = mm
    engine.household_split_probability = 0.001

    engine._create_synthetic_population(POPULATION_SIZE)
    zero_rfs = {rf: 0 for rf in Citizen.DEFAULT_RISK_FACTORS}
    for c in engine.citizens.values():
        c.risk_factors = zero_rfs.copy()

    initial_pop = sum(1 for c in engine.citizens.values() if c.alive)
    engine.run(months=SIM_MONTHS)

    years = sorted(engine.yearly_stats.keys())
    total = [engine.yearly_stats[y]["total_population"] for y in years]
    males = [engine.yearly_stats[y]["num_males"]        for y in years]
    females = [engine.yearly_stats[y]["num_females"]    for y in years]

    alive = [c for c in engine.citizens.values() if c.alive]
    n_alive = max(len(alive), 1)
    cvd_final = sum(1 for c in alive if c.diseases.get("CVD", 0) == 1) / n_alive * 100
    lc_final = sum(1 for c in alive if c.diseases.get("Lung Cancer", 0) == 1) / n_alive * 100

    return {
        "years":         years,
        "total":         total,
        "males":         males,
        "females":       females,
        "initial_pop":   initial_pop,
        "final_pop":     total[-1] if total else 0,
        "cvd_prev_final": cvd_final,
        "lc_prev_final":  lc_final,
    }


def _worker(args):
    label, fm, mm, seed = args
    try:
        return (label, run_sim_yearly(fm, mm, seed), None)
    except Exception as e:
        import traceback
        return (label, None, f"{e}\n{traceback.format_exc()}")


def main():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    print("=" * 78)
    print("TRAJEKTORIE LUDNOŚCI — ABM bez RF")
    print(f"Populacja: {POPULATION_SIZE:,} | {SIM_MONTHS} mies. ({SIM_MONTHS//12} lat)")
    print("=" * 78)

    tasks = [(p["label"], p["fm"], p["mm"], 42) for p in POINTS]
    n_workers = min(mp.cpu_count(), len(tasks)) if tasks else 1
    print(f"  Workers:   {n_workers} rdzeni")
    results = {}
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futures = {ex.submit(_worker, t): t for t in tasks}
        for fut in as_completed(futures):
            label, result, err = fut.result()
            if err:
                print(f"  [BŁĄD] {label}: {err.splitlines()[0]}")
            else:
                delta = (result["final_pop"] - result["initial_pop"]) / result["initial_pop"] * 100
                print(f"  [OK]  {label}: {result['initial_pop']:,} → {result['final_pop']:,}  ({delta:+.2f}%)")
            results[label] = result

    # ---------------- Wizualizacja ----------------
    subtitles = [f"<b>{p['label']}</b><br>FM={p['fm']:.3f} | MM={p['mm']:.3f}" for p in POINTS]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=subtitles,
        shared_yaxes=False,
        horizontal_spacing=0.10,
    )

    for col_idx, p in enumerate(POINTS, start=1):
        r = results.get(p["label"])
        if r is None:
            continue
        show_leg = (col_idx == 1)

        fig.add_trace(go.Scatter(
            x=r["years"], y=r["total"],
            name="Populacja całk.",
            mode="lines+markers",
            line=dict(color=p["color"], width=3),
            marker=dict(size=6),
            showlegend=show_leg,
            hovertemplate="Rok %{x}<br>Populacja: %{y:,}<extra></extra>",
        ), row=1, col=col_idx)

        fig.add_trace(go.Scatter(
            x=r["years"], y=r["males"],
            name="Mężczyźni",
            mode="lines",
            line=dict(color="#2980b9", width=1.5, dash="dot"),
            showlegend=show_leg,
            hovertemplate="Rok %{x}<br>M: %{y:,}<extra></extra>",
        ), row=1, col=col_idx)

        fig.add_trace(go.Scatter(
            x=r["years"], y=r["females"],
            name="Kobiety",
            mode="lines",
            line=dict(color="#e74c3c", width=1.5, dash="dot"),
            showlegend=show_leg,
            hovertemplate="Rok %{x}<br>K: %{y:,}<extra></extra>",
        ), row=1, col=col_idx)

        initial = r["initial_pop"]
        final = r["final_pop"]
        delta_pct = (final - initial) / initial * 100
        color = "#27ae60" if abs(delta_pct) < 2 else ("#c0392b" if delta_pct < 0 else "#2471a3")

        fig.add_annotation(
            row=1, col=col_idx,
            text=(
                f"<b>{initial:,} → {final:,}</b><br>"
                f"<span style='color:{color}'><b>{delta_pct:+.1f}%</b></span><br>"
                f"<sub>CVD: {r['cvd_prev_final']:.2f}% | LC: {r['lc_prev_final']:.2f}%</sub>"
            ),
            x=0.02, y=0.98, xref="x domain", yref="y domain",
            xanchor="left", yanchor="top", showarrow=False,
            font=dict(size=12), align="left",
            bgcolor="rgba(255,255,255,0.85)", bordercolor="lightgray", borderwidth=1, borderpad=6,
        )

        fig.add_hline(
            y=initial, line_dash="dash", line_color="gray", line_width=1,
            row=1, col=col_idx,
        )

        fig.update_xaxes(title="Rok symulacji", row=1, col=col_idx, gridcolor="#eeeeee")
        fig.update_yaxes(
            title="Liczba osób" if col_idx == 1 else None,
            row=1, col=col_idx,
            gridcolor="#eeeeee",
            rangemode="tozero",
        )

    fig.update_layout(
        title=dict(
            text=(
                "<b>Trajektoria liczby ludności (50 lat) — ABM bez risk factors</b><br>"
                "<sub>Kalibracja: gridsearch_full_abm_no_rf | "
                f"{POPULATION_SIZE:,} agentów</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=16),
        ),
        height=650, width=1500,
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(x=0.5, y=-0.12, xanchor="center", orientation="h", font=dict(size=12)),
        font=dict(family="Arial, sans-serif", size=11),
        hovermode="x unified",
    )

    out = "populacja_w_czasie_no_rf.html"
    fig.write_html(out)
    print(f"\n✓ Zapisano: {out}")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
