"""
Main entry point for the Urban Health ABM simulation.

This script orchestrates the entire simulation:
1. Initializes demographic engine with realistic Polish population structure
2. Runs 50-year (600-month) demographic simulation with 50,000 agents
3. Collects yearly statistics (age pyramid, households, mortality, etc.)
4. Generates interactive visualizations in Plotly format
"""

import sys
from simulation_engine import SimulationEngine
from disease_model import DiseaseModel
from visualization import SimulationVisualizer
from grid_search_optimization import GridSearchOptimization


def main() -> None:
    """Main simulation execution function."""

    print("=" * 70)
    print("URBAN HEALTH AGENT-BASED MODEL (URBAN-ABM)")
    print("Demographic Simulation with 50,000 Agents")
    print("Polish GUS-Inspired Population Structure")
    print("=" * 70)
    print()

    # ============================================================================
    # PHASE 1: PARAMETER OPTIMIZATION (GridSearch)
    # ============================================================================
    # Perform GridSearch to find optimal parameters
    print("\n" + "="*70)
    print("PHASE 1: GRIDSEARCH PARAMETER OPTIMIZATION")
    print("="*70)
    print("Running GridSearchOptimization to find optimal parameters...\n")

    def simulation_scoring_function(fertility_multiplier, mortality_multiplier):
        # GridSearch scoring function (2D: fixed birth_rate and mortality_rate)
        birth_rate = 0.03  # Fixed value for i=10
        mortality_rate = 0.0015  # Fixed value for i=10
        
        initial_population = 50000
        final_population = initial_population

        for year in range(50):
            births = final_population * birth_rate * fertility_multiplier
            deaths = final_population * mortality_rate * mortality_multiplier
            final_population += births - deaths

            if final_population < 0:
                final_population = 0
                break

        # Procentowa zmiana populacji
        score = ((final_population - initial_population) / initial_population) * 100
        return score

    param_grid = {
        "fertility_multiplier": [0.5 + i * 0.4 for i in range(5)],  # 5 values: 0.5, 0.9, 1.3, 1.7, 2.1
        "mortality_multiplier": [0.5 + i * 0.4 for i in range(5)],  # 5 values: 0.5, 0.9, 1.3, 1.7, 2.1
    }

    optimizer = GridSearchOptimization(param_grid, scoring_function=simulation_scoring_function, n_iter=1)
    best_params, best_score = optimizer.optimize()

    print("\n✅ OPTIMAL PARAMETERS FOUND:")
    print("-" * 70)
    for param, value in best_params.items():
        print(f"  {param:25} = {value}")
    print("-" * 70)
    print(f"  Best Score (population growth %):  {best_score:,.2f}%")
    print()

    # ============================================================================
    # PHASE 2: DISEASE MODEL INITIALIZATION
    # ============================================================================
    # Initialize disease model with top 15 diseases
    print("\n" + "="*70)
    print("PHASE 2: DISEASE MODEL INITIALIZATION")
    print("="*70)
    print("Initializing disease model...\n")
    disease_model = DiseaseModel()
    print(f"Selected {disease_model.get_disease_count()} diseases for simulation:")
    for i, disease in enumerate(disease_model.diseases, 1):
        prevalence = disease_model.get_prevalence(disease)
        weight = disease_model.get_disability_weight(disease)
        print(f"  {i:2}. {disease:<40} (prevalence={prevalence:5.1f}%, disability={weight:.2f})")
    print()

    # ============================================================================
    # PHASE 3: SIMULATION ENGINE SETUP
    # ============================================================================
    # Create simulation engine
    print("\n" + "="*70)
    print("PHASE 3: SIMULATION ENGINE SETUP")
    print("="*70)
    print("Creating simulation engine with demographic tables...\n")
    engine = SimulationEngine(
        disease_model=disease_model,
        seed=42,  # For reproducibility
    )

    # Configure simulation parameters based on GridSearch results
    engine.fertility_rate = best_params['fertility_multiplier']
    engine.mortality_multiplier = best_params['mortality_multiplier']
    engine.household_split_probability = 0.001  # Default value

    print("  Engine Configuration (from GridSearch):")
    print(f"    - Fertility rate multiplier: {engine.fertility_rate:.3f}")
    print(f"    - Mortality multiplier: {engine.mortality_multiplier:.3f}")
    print(f"    - Household split probability: {engine.household_split_probability:.4f}")
    print(f"    - Zones created: {len(engine.zones)}")
    print()

    # ============================================================================
    # PHASE 4: POPULATION INITIALIZATION
    # ============================================================================
    # Load initial population (create 50,000 synthetic with Polish demographics)
    print("\n" + "="*70)
    print("PHASE 4: SYNTHETIC POPULATION GENERATION")
    print("="*70)
    print("Generating initial population (50,000 agents)...\n")
    loaded = engine._create_synthetic_population(50000)

    print(f"  Initial households: {len(engine.households)}")
    print(f"  Total zones: {len(engine.zones)}")

    # Display age distribution
    alive = [c for c in engine.citizens.values() if c.alive]
    children = sum(1 for c in alive if c.age_years < 15)
    working = sum(1 for c in alive if 18 <= c.age_years < 65)
    elderly = sum(1 for c in alive if c.age_years >= 65)
    pct_female = sum(1 for c in alive if c.sex == "female") / len(alive) * 100

    print(f"  Population composition:")
    print(f"    - Children (0-14): {children} ({children/len(alive)*100:.1f}%)")
    print(f"    - Working-age (18-64): {working} ({working/len(alive)*100:.1f}%)")
    print(f"    - Elderly (65+): {elderly} ({elderly/len(alive)*100:.1f}%)")
    print(f"    - Female: {pct_female:.1f}%")
    print()

    # ============================================================================
    # PHASE 5: DEMOGRAPHIC SIMULATION (50 YEARS)
    # ============================================================================
    # Run simulation
    print("\n" + "="*70)
    print("PHASE 5: DEMOGRAPHIC SIMULATION (50 YEARS / 600 MONTHS)")
    print("="*70)
    print("\nRunning simulation with GridSearch-optimized parameters...\n")
    engine.run(months=600)
    print()

    # Display final statistics
    print(engine.get_statistics_summary())
    print()

    # ============================================================================
    # PHASE 6: VISUALIZATION & REPORTING
    # ============================================================================
    # Generate visualizations
    print("\n" + "="*70)
    print("PHASE 6: GENERATING VISUALIZATIONS")
    print("="*70)
    print("\nGenerating interactive visualizations...\n")
    visualizer = SimulationVisualizer(engine.yearly_stats)
    visualizer.generate_all_plots()
    print()

    print("=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
    print("\nGenerated output files:")
    print("  📊 DEMOGRAFIC PYRAMIDS (GUS-style, interactive):")
    print("     - piramida_wieku_rok_50.html (Age pyramid - year 50)")
    print("     - piramida_wieku_animowana.html (Animated pyramid with year slider)")
    print("  📈 POPULATION TRENDS:")
    print("     - population_trends.html (Population, multimorbidity, disability)")
    print("     - households_trends.html (Household dynamics)")
    print("     - gender_distribution.html (Male/Female temporal distribution)")
    print("\nOpen HTML files in a web browser to interactively analyze results.")
    print(f"\nTotal agents simulated: 50,000")
    print(f"Simulation duration: 50 years")
    print(f"Final population: {len([c for c in engine.citizens.values() if c.alive])}")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
