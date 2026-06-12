"""
Gridsearch z pełnym ABM (BEZ czynników ryzyka).

W odróżnieniu od `grid_search_improved_v3_fixed.py`, który używa analitycznego
proxy (BASE_CBR/CDR × mnożniki, ~1 ms/punkt), ten skrypt uruchamia PEŁNĄ
symulację ABM dla każdego punktu siatki — z modelem Coxa, akumulacją H_cum
i wszystkimi mechanizmami stochastycznymi.

Aby wynik był porównywalny z proxy (które nie modeluje RF):
  → wszystkie risk factors są zerowane (initial + newborn).
  → Cox jest aktywny, ale exp(Σ β·0) = 1, więc onset chorób zależy tylko od
    bazowego hazardu × wzrost z wiekiem (Gompertz).

Cel: zidentyfikować źródło rozbieżności proxy ↔ ABM:
  (a) efekty strukturalne populacji (proxy ich nie ma)
  (b) baseline disease hazard (proxy go nie ma)
  (c) risk factors (tu wyłączone, więc NIE wpływają)

Siatka: 12 × 12 = 144 punkty (identyczna z proxy → cell-by-cell diff)
Populacja: 50 000 agentów × 50 lat (600 mies.)
Runtime: ~25-40 min na 6-10 rdzeniach

Generuje:
  gridsearch_full_abm_no_rf_<timestamp>.json    — pełne wyniki
  heatmap_gridsearch_full_abm_no_rf_<timestamp>.png — heatmapa score%
  delta_proxy_vs_abm_<timestamp>.png (opcjonalnie, jeśli proxy JSON dostępny)
"""
import json
import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

import numpy as np


# Identyczna siatka jak w grid_search_improved_v3_fixed.py — cell-by-cell match
PARAM_GRID = {
    "fertility_multiplier":  np.linspace(0.4, 2.5, 12),
    "mortality_multiplier":  np.linspace(0.3, 1.6, 12),
}

POPULATION_SIZE = 50_000
SIM_MONTHS = 600  # 50 lat
SEED = 42


def run_sim_no_rf(fm: float, mm: float, seed: int = SEED):
    """
    Pełna symulacja ABM z wyzerowanymi czynnikami ryzyka.

    Zwraca:
        (final_pop, initial_pop, score_pct, mean_H_cum_CVD, mean_H_cum_LC,
         cvd_prev_pct, lc_prev_pct)
    """
    from simulation_engine import SimulationEngine
    from disease_model import DiseaseModel
    from citizen import Citizen

    engine = SimulationEngine(disease_model=DiseaseModel(), seed=seed)
    engine.fertility_rate = fm
    engine.mortality_multiplier = mm
    engine.household_split_probability = 0.001

    engine._create_synthetic_population(POPULATION_SIZE)

    # ZEROWANIE risk factors u wszystkich agentów (initial population).
    # Noworodki już są tworzone z RF=0 w handle_births (linia 595 simulation_engine.py),
    # więc to wystarczy do utrzymania "no RF" przez całą symulację.
    zero_rfs = {rf: 0 for rf in Citizen.DEFAULT_RISK_FACTORS}
    for c in engine.citizens.values():
        c.risk_factors = zero_rfs.copy()

    initial_pop = sum(1 for c in engine.citizens.values() if c.alive)

    engine.run(months=SIM_MONTHS)

    alive = [c for c in engine.citizens.values() if c.alive]
    final_pop = len(alive)
    score = ((final_pop - initial_pop) / initial_pop) * 100 if initial_pop else 0.0

    # Diagnostyka chorobowa (powinno być niskie — Cox bez RF)
    n_alive = max(len(alive), 1)
    cvd_prev = sum(1 for c in alive if c.diseases.get("CVD", 0) == 1) / n_alive * 100
    lc_prev = sum(1 for c in alive if c.diseases.get("Lung Cancer", 0) == 1) / n_alive * 100
    h_cvd = sum(c.cumulative_hazard.get("CVD", 0.0) for c in alive) / n_alive
    h_lc = sum(c.cumulative_hazard.get("Lung Cancer", 0.0) for c in alive) / n_alive

    return {
        "final_pop":    final_pop,
        "initial_pop":  initial_pop,
        "score":        score,
        "cvd_prev_pct": cvd_prev,
        "lc_prev_pct":  lc_prev,
        "mean_H_cvd":   h_cvd,
        "mean_H_lc":    h_lc,
    }


def _worker(args):
    combo_idx, fm, mm, seed = args
    t0 = time.time()
    try:
        result = run_sim_no_rf(fm, mm, seed)
        return (combo_idx, fm, mm, result, time.time() - t0, None)
    except Exception as e:
        import traceback
        return (combo_idx, fm, mm, None, time.time() - t0, f"{e}\n{traceback.format_exc()}")


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    fm_vals = PARAM_GRID["fertility_multiplier"]
    mm_vals = PARAM_GRID["mortality_multiplier"]

    # Lista wszystkich punktów (FM_idx × MM_idx → 144 kombinacji)
    tasks = []
    combo_idx = 1
    for mm in mm_vals:
        for fm in fm_vals:
            tasks.append((combo_idx, float(fm), float(mm), SEED))
            combo_idx += 1

    n_total = len(tasks)
    n_workers = min(mp.cpu_count(), n_total)

    print("=" * 78)
    print("ABM GRIDSEARCH — full simulation, NO risk factors")
    print("=" * 78)
    print(f"  Siatka:       12 × 12 = {n_total} kombinacji")
    print(f"  Populacja:    {POPULATION_SIZE:,} agentów")
    print(f"  Symulacja:    {SIM_MONTHS} mies. ({SIM_MONTHS//12} lat)")
    print(f"  Workers:      {n_workers} rdzeni")
    print(f"  Risk factors: WYŁĄCZONE (wszystkie agentom RF=0)")
    print(f"  Cox model:    AKTYWNY (ale exp(β·0)=1, więc bez amplifikacji)")
    print(f"  Seed:         {SEED}")
    print("=" * 78)

    t_start = time.time()
    results = []

    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futures = {ex.submit(_worker, t): t for t in tasks}
        done = 0
        for fut in as_completed(futures):
            combo_idx, fm, mm, result, dt, err = fut.result()
            done += 1
            if err:
                print(f"  [{done:3d}/{n_total}] [BŁĄD] FM={fm:.3f} MM={mm:.3f} ({dt:.1f}s): {err.splitlines()[0]}")
                results.append({
                    "combo": combo_idx, "iteration": 1,
                    "params": {"fertility_multiplier": fm, "mortality_multiplier": mm},
                    "score": float("nan"),
                    "error": err.splitlines()[0],
                })
            else:
                eta_min = (time.time() - t_start) / done * (n_total - done) / 60
                print(f"  [{done:3d}/{n_total}] FM={fm:.3f} MM={mm:.3f} → "
                      f"score={result['score']:+7.2f}%  pop={result['final_pop']:>6,}  "
                      f"CVD={result['cvd_prev_pct']:4.1f}%  LC={result['lc_prev_pct']:4.2f}%  "
                      f"({dt:.0f}s, ETA {eta_min:.0f}min)")
                results.append({
                    "combo":       combo_idx,
                    "iteration":   1,
                    "params":      {"fertility_multiplier": fm, "mortality_multiplier": mm},
                    "score":       result["score"],
                    "final_pop":   result["final_pop"],
                    "initial_pop": result["initial_pop"],
                    "cvd_prev_pct": result["cvd_prev_pct"],
                    "lc_prev_pct":  result["lc_prev_pct"],
                    "mean_H_cvd":   result["mean_H_cvd"],
                    "mean_H_lc":    result["mean_H_lc"],
                    "elapsed_s":    dt,
                })

    results.sort(key=lambda r: r["combo"])

    total_time = time.time() - t_start
    print()
    print(f"Całkowity czas: {total_time / 60:.1f} min")
    print()

    # Statystyki ogólne
    valid = [r for r in results if not np.isnan(r.get("score", float("nan")))]
    scores = [r["score"] for r in valid]
    if scores:
        print(f"Score min:    {min(scores):+.2f}%")
        print(f"Score max:    {max(scores):+.2f}%")
        print(f"Score mediana: {np.median(scores):+.2f}%")
        # Punkty stabilne (|score| < 2%)
        stable = [r for r in valid if abs(r["score"]) < 2.0]
        if stable:
            print(f"\nPunkty stabilne (|score|<2%): {len(stable)}")
            for r in sorted(stable, key=lambda x: abs(x["score"]))[:5]:
                p = r["params"]
                print(f"  FM={p['fertility_multiplier']:.3f}  MM={p['mortality_multiplier']:.3f}  "
                      f"score={r['score']:+.2f}%")

    # Zapis JSON (struktura zgodna z grid_search_improved_v3_fixed)
    json_file = f"gridsearch_full_abm_no_rf_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ JSON: {json_file}")

    # Heatmapa
    try:
        _plot_heatmap(results, fm_vals, mm_vals, timestamp)
    except Exception as e:
        print(f"  [BŁĄD heatmapy] {e}")

    print("\n" + "=" * 78)


def _plot_heatmap(results, fm_vals, mm_vals, timestamp):
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm

    # Mapuj wyniki w siatkę score[mm_idx, fm_idx]
    score_grid = np.full((len(mm_vals), len(fm_vals)), np.nan)
    for r in results:
        p = r["params"]
        fm_idx = int(np.argmin(np.abs(fm_vals - p["fertility_multiplier"])))
        mm_idx = int(np.argmin(np.abs(mm_vals - p["mortality_multiplier"])))
        score_grid[mm_idx, fm_idx] = r.get("score", np.nan)

    # Diverging colormap centrowana w 0%
    vmin = np.nanmin(score_grid)
    vmax = np.nanmax(score_grid)
    norm = TwoSlopeNorm(vcenter=0.0,
                        vmin=min(vmin, -1.0),
                        vmax=max(vmax,  1.0))

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(score_grid, cmap="RdBu_r", norm=norm,
                   aspect="auto", origin="lower")

    # Etykiety osi
    ax.set_xticks(range(len(fm_vals)))
    ax.set_xticklabels([f"{v:.2f}" for v in fm_vals], rotation=45, ha="right")
    ax.set_yticks(range(len(mm_vals)))
    ax.set_yticklabels([f"{v:.2f}" for v in mm_vals])
    ax.set_xlabel("fertility_multiplier (FM)", fontsize=12)
    ax.set_ylabel("mortality_multiplier (MM)", fontsize=12)
    ax.set_title(
        f"ABM gridsearch (BEZ risk factors) — score % po 50 latach\n"
        f"50 000 agentów × 50 lat | 12×12 = 144 kombinacji | seed={SEED}",
        fontsize=13,
    )

    # Wartości w komórkach
    for mm_idx in range(len(mm_vals)):
        for fm_idx in range(len(fm_vals)):
            val = score_grid[mm_idx, fm_idx]
            if not np.isnan(val):
                color = "white" if abs(val) > 30 else "black"
                ax.text(fm_idx, mm_idx, f"{val:+.0f}",
                        ha="center", va="center",
                        color=color, fontsize=7)

    cbar = plt.colorbar(im, ax=ax, label="Score (Δ populacja % po 50 latach)")

    # Adnotacja informacyjna
    fig.text(0.02, 0.02,
             "Bez RF: exp(Σ β·0)=1, Cox aktywny ale bez amplifikacji.\n"
             "Onset chorób tylko z baseline_hazard × age_growth (Gompertz).",
             fontsize=9, color="#555")

    plt.tight_layout()
    out = f"heatmap_gridsearch_full_abm_no_rf_{timestamp}.png"
    plt.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ Heatmapa: {out}")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
