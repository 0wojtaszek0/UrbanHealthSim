"""
Porównanie dwóch podejść parametryzacji demograficznej:

PODEJŚCIE A (flat rate):
  birth_rate  – stała roczna stopa urodzeń na kobietę 15–50, niezależna od wieku
  mortality_rate – stała roczna stopa zgonów na osobę, niezależna od wieku

PODEJŚCIE B (multiplier, AKTUALNE):
  fertility_multiplier – mnożnik tabel wiekowych płodności
  mortality_multiplier – mnożnik tabel wiekowych śmiertelności

Generuje: comparison_flatrate_vs_multiplier.html (6 piramid – 2 podejścia × 3 scenariusze)
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

POPULATION_SIZE = 50_000
SIM_MONTHS      = 600   # 50 lat

AGE_ORDER = [f"{s}-{s+4}" for s in range(0, 90, 5)] + ["90-94", "95-99", "100+"]


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------
def pyramid_bars(pyramid: dict):
    males   = [pyramid.get(b, {}).get("male",   0) for b in AGE_ORDER]
    females = [pyramid.get(b, {}).get("female", 0) for b in AGE_ORDER]
    return males, females


def score_color(score: float) -> str:
    if score > 2:   return "#c0392b"
    elif score < -2: return "#2471a3"
    return "#27ae60"


# ---------------------------------------------------------------------------
# Scenariusze
# ---------------------------------------------------------------------------
# Trzy scenariusze demograficzne:
#   1. Spadek (niskie narodziny, wysoka śmiertelność)
#   2. Quasi-stabilny
#   3. Wzrost (wysokie narodziny, niska śmiertelność)
#
# Kalibracja: FM=1.0, MM=1.0  →  CBR≈8.30/1000/rok, CDR≈15.60/1000/rok
BASE_CBR = 0.00830
BASE_CDR = 0.01560

# Multiplier scenarios (FM, MM) – dobrze dobrane, dają czytelną wiekową piramidę
MULTIPLIER_SCENARIOS = [
    (0.50, 1.00, "Spadek\nFM=0.50, MM=1.00"),
    (1.88, 1.00, "Stabilny\nFM=1.88, MM=1.00"),
    (2.50, 0.60, "Wzrost\nFM=2.50, MM=0.60"),
]

# Flat-rate scenarios – parametry dobrane tak by ZAMIERZONE CBR/CDR były identyczne
# z multiplier scenarios.  Np. FM=0.50 → zamierzone CBR = 0.50 * 8.30 = 4.15/1000
# → flat birth_rate = 4.15/1000/rok.  Analogicznie mortality_rate.
FLAT_SCENARIOS = [
    (BASE_CBR * 0.50, BASE_CDR * 1.00, "Spadek (flat)\nbr=4.1‰, mr=15.6‰"),
    (BASE_CBR * 1.88, BASE_CDR * 1.00, "Stabilny (flat)\nbr=15.6‰, mr=15.6‰"),
    (BASE_CBR * 2.50, BASE_CDR * 0.60, "Wzrost (flat)\nbr=20.7‰, mr=9.4‰"),
]


# ---------------------------------------------------------------------------
# Worker: multiplier (standardowy silnik ABM)
# ---------------------------------------------------------------------------
def _worker_multiplier(args):
    fm, mm, label, seed = args
    try:
        from simulation_engine import SimulationEngine
        from disease_model import DiseaseModel

        dm = DiseaseModel()
        eng = SimulationEngine(disease_model=dm, seed=seed)
        eng.fertility_rate       = fm
        eng.mortality_multiplier = mm
        eng.household_split_probability = 0.001
        eng._create_synthetic_population(POPULATION_SIZE)
        init_pop = sum(1 for c in eng.citizens.values() if c.alive)
        eng.run(months=SIM_MONTHS)
        final_pop = sum(1 for c in eng.citizens.values() if c.alive)
        score = (final_pop - init_pop) / init_pop * 100
        years = sorted(eng.yearly_stats.keys())
        pyramid = eng.yearly_stats[years[-1]]["age_pyramid"] if years else {}
        return (label, pyramid, score, final_pop, None)
    except Exception as e:
        return (label, {}, float('nan'), 0, str(e))


# ---------------------------------------------------------------------------
# Worker: flat rate (stała stopa dla wszystkich wieków)
# ---------------------------------------------------------------------------
def _worker_flatrate(args):
    birth_rate, mortality_rate, label, seed = args
    try:
        from simulation_engine import SimulationEngine
        from disease_model import DiseaseModel
        from citizen import Citizen

        dm = DiseaseModel()
        eng = SimulationEngine(disease_model=dm, seed=seed)
        eng.household_split_probability = 0.001
        eng._create_synthetic_population(POPULATION_SIZE)
        init_pop = sum(1 for c in eng.citizens.values() if c.alive)

        # Miesięczne prawdopodobieństwa – stałe dla wszystkich wieków
        monthly_birth_prob = birth_rate / 12.0
        monthly_death_prob = mortality_rate / 12.0

        # ----- Podmiana metod silnika na wersję flat-rate -----
        rng = eng.rng

        def flat_handle_births():
            """Każda kobieta 15–50 ma tę SAMĄ szansę urodzenia, bez tabeli wiekowej."""
            births = []
            for citizen in eng.citizens.values():
                if citizen.alive and citizen.sex == "female":
                    if 15.0 <= citizen.age_years <= 50.0:
                        if rng.random() < monthly_birth_prob:
                            births.append(citizen)
            for mother in births:
                newborn = Citizen(
                    sex=rng.choice(["male", "female"]),
                    age_months=0,
                    household_id=mother.household_id,
                    zone_id=mother.zone_id,
                    diseases=dm.get_initial_diseases(),
                )
                newborn.risk_factors = {rf: 0 for rf in Citizen.DEFAULT_RISK_FACTORS}
                eng.citizens[newborn.id] = newborn
                hh = eng.households.get(mother.household_id)
                if hh:
                    hh.add_member(newborn.id)

        def flat_handle_deaths():
            """Każdy żyjący ma tę SAMĄ szansę zgonu, bez tabeli wiekowej."""
            deaths = []
            for cid, citizen in eng.citizens.items():
                if citizen.alive and rng.random() < monthly_death_prob:
                    deaths.append(cid)
            for cid in deaths:
                citizen = eng.citizens[cid]
                citizen.alive = False
                hh = eng.households.get(citizen.household_id)
                if hh:
                    hh.remove_member(cid)

        eng.handle_births  = flat_handle_births
        eng.handle_deaths  = flat_handle_deaths

        eng.run(months=SIM_MONTHS)
        final_pop = sum(1 for c in eng.citizens.values() if c.alive)
        score = (final_pop - init_pop) / init_pop * 100
        years = sorted(eng.yearly_stats.keys())
        pyramid = eng.yearly_stats[years[-1]]["age_pyramid"] if years else {}
        return (label, pyramid, score, final_pop, None)
    except Exception as e:
        return (label, {}, float('nan'), 0, str(e))


# ---------------------------------------------------------------------------
# Równoległe uruchamianie
# ---------------------------------------------------------------------------
def run_all():
    tasks_mult = [
        (fm, mm, label, 42)
        for fm, mm, label in MULTIPLIER_SCENARIOS
    ]
    tasks_flat = [
        (br, mr, label, 42)
        for br, mr, label in FLAT_SCENARIOS
    ]

    results_mult = {}
    results_flat = {}

    all_tasks = (
        [("mult", t) for t in tasks_mult] +
        [("flat", t) for t in tasks_flat]
    )

    n_workers = min(mp.cpu_count(), len(all_tasks))
    print(f"Uruchamianie {len(all_tasks)} symulacji × {n_workers} wątków CPU")

    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futures = {}
        for kind, t in all_tasks:
            if kind == "mult":
                f = ex.submit(_worker_multiplier, t)
            else:
                f = ex.submit(_worker_flatrate, t)
            futures[f] = (kind, t[-2])  # (kind, label)

        done = 0
        for fut in as_completed(futures):
            done += 1
            kind, label = futures[fut]
            label_res, pyramid, score, final_pop, err = fut.result()
            tag = label_res.split('\n')[0]
            if err:
                print(f"  [BŁĄD] {kind} {tag}: {err}")
            else:
                print(f"  [{done}/{len(all_tasks)}] {kind:4s} | {tag:25s} → score={score:+.1f}%  n={final_pop}")
            if kind == "mult":
                results_mult[label_res] = (pyramid, score, final_pop)
            else:
                results_flat[label_res] = (pyramid, score, final_pop)

    return results_mult, results_flat


# ---------------------------------------------------------------------------
# Wizualizacja
# ---------------------------------------------------------------------------
def make_html(results_mult, results_flat,
              output_file="comparison_flatrate_vs_multiplier.html"):

    # Wiersze: [multiplier, flat]  Kolumny: [spadek, stabilny, wzrost]
    row_labels = [
        "<b>PODEJŚCIE B – Mnożnik tabel wiekowych</b><br>"
        "<sub>fertility_multiplier × mortality_multiplier | aktualna implementacja</sub>",
        "<b>PODEJŚCIE A – Stała stopa (flat rate)</b><br>"
        "<sub>birth_rate / mortality_rate, jednakowe dla wszystkich wieków</sub>",
    ]

    mult_labels = [s[2] for s in MULTIPLIER_SCENARIOS]
    flat_labels = [s[2] for s in FLAT_SCENARIOS]

    subtitles = []
    for row in [mult_labels, flat_labels]:
        for lbl in row:
            subtitles.append(lbl.replace("\n", "<br>"))

    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=subtitles,
        shared_yaxes="rows",
        vertical_spacing=0.18,
        horizontal_spacing=0.05,
    )

    colors = [
        ("#2980b9", "#e74c3c"),   # wiersz 1: standardowe niebieskie/czerwone
        ("#1a7a4a", "#e67e22"),   # wiersz 2: zielone/pomarańczowe → odróżnienie
    ]

    for ri, (labels, results, col_m, col_f) in enumerate([
        (mult_labels, results_mult, *colors[0]),
        (flat_labels, results_flat, *colors[1]),
    ]):
        row = ri + 1
        for ci, label in enumerate(labels):
            col = ci + 1
            pyramid, score, final_pop = results.get(label, ({}, float('nan'), 0))
            males, females = pyramid_bars(pyramid)

            show_leg = (ri == 0 and ci == 0)
            fig.add_trace(go.Bar(
                y=AGE_ORDER, x=[-m for m in males],
                name="Mężczyźni", orientation="h",
                marker_color=col_m, showlegend=show_leg,
                hovertemplate="<b>%{y}</b><br>M: %{customdata}<extra></extra>",
                customdata=males,
            ), row=row, col=col)
            fig.add_trace(go.Bar(
                y=AGE_ORDER, x=females,
                name="Kobiety", orientation="h",
                marker_color=col_f, showlegend=show_leg,
                hovertemplate="<b>%{y}</b><br>K: %{x}<extra></extra>",
            ), row=row, col=col)

            fig.add_annotation(
                row=row, col=col,
                text=f"<b>{score:+.1f}%</b>  n={final_pop:,}",
                x=0.5, y=0.98, xref="x domain", yref="y domain",
                xanchor="center", yanchor="top", showarrow=False,
                font=dict(size=9, color=score_color(score)),
            )

    # Etykiety wierszy
    for ri, label in enumerate(row_labels):
        y_pos = 1.0 - (ri + 0.5) / 2
        fig.add_annotation(
            x=-0.01, y=y_pos, xref="paper", yref="paper",
            text=label, showarrow=False, textangle=-90,
            font=dict(size=9), xanchor="right", yanchor="middle",
        )

    fig.update_layout(
        barmode="overlay",
        title=dict(
            text=(
                "<b>Podejście A (flat rate) vs Podejście B (mnożnik tabel) – 50 000 os., 50 lat</b><br>"
                "<sub>"
                "Górny rząd: mnożnik tabel wiekowych (aktualne) | "
                "Dolny rząd: stała stopa flat-rate (równa dla wszystkich wieków) | "
                "Scenariusze: Spadek / Stabilny / Wzrost"
                "</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=13),
        ),
        height=1200, width=1600,
        paper_bgcolor="white",
        legend=dict(x=0.5, y=-0.03, xanchor="center", orientation="h"),
        font=dict(family="Arial, sans-serif", size=9),
    )

    for i in range(1, 7):
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
    mp.set_start_method("spawn", force=True)

    print("=" * 65)
    print("PORÓWNANIE: flat-rate vs mnożnik tabel wiekowych")
    print(f"Populacja: {POPULATION_SIZE:,}  |  Symulacja: {SIM_MONTHS} miesięcy (50 lat)")
    print(f"Kalibracja: CBR={BASE_CBR*1000:.2f}/1000/rok, CDR={BASE_CDR*1000:.2f}/1000/rok")
    print()
    print("Scenariusze (ZAMIERZONE identyczne CBR/CDR w obu podejściach):")
    for (fm, mm, lab), (br, mr, _) in zip(MULTIPLIER_SCENARIOS, FLAT_SCENARIOS):
        cbr_t = BASE_CBR * fm * 1000
        cdr_t = BASE_CDR * mm * 1000
        print(f"  Spadek/Wzrost: FM={fm}, MM={mm}  → CBR≈{cbr_t:.1f}‰, CDR≈{cdr_t:.1f}‰")
    print("=" * 65)

    results_mult, results_flat = run_all()
    make_html(results_mult, results_flat)

    print("\n" + "=" * 65)
    print("GOTOWE! → comparison_flatrate_vs_multiplier.html")
    print("=" * 65)
