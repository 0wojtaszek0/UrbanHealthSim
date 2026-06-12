#!/usr/bin/env python3
"""
Quick demo of the risk factor adjustment system.
Shows how to modify risk factors and compare results.
"""

import json
from typing import Dict
from simulation_engine import SimulationEngine
from disease_model import DiseaseModel
from citizen import Citizen


def run_comparison_demo():
    """Run two simulations with different risk factor settings."""
    
    print("=" * 80)
    print("RISK FACTOR SIMULATION COMPARISON DEMO")
    print("=" * 80)
    print()
    
    # Scenario 1: Baseline
    print("📊 SCENARIO 1: BASELINE (All RF multipliers = 1.0)")
    print("-" * 80)
    result1 = run_scenario(
        "Baseline",
        population=10000,
        years=10,
        fertility_mult=1.0,
        mortality_mult=1.0,
        rf_multipliers={
            "smoking": 1.0,
            "obesity": 1.0,
            "physical_inactivity": 1.0,
            "alcohol_abuse": 1.0,
            "high_cholesterol": 1.0,
            "hypertension_stage0": 1.0,
            "family_history": 1.0,
        }
    )
    print()
    
    # Scenario 2: Health intervention (reduced RF)
    print("📊 SCENARIO 2: HEALTH INTERVENTION (RF multipliers = 0.5)")
    print("-" * 80)
    result2 = run_scenario(
        "Intervention",
        population=10000,
        years=10,
        fertility_mult=1.0,
        mortality_mult=1.0,
        rf_multipliers={
            "smoking": 0.5,
            "obesity": 0.5,
            "physical_inactivity": 0.5,
            "alcohol_abuse": 0.5,
            "high_cholesterol": 0.5,
            "hypertension_stage0": 0.5,
            "family_history": 1.0,  # Family history can't be changed
        }
    )
    print()
    
    # Comparison
    print("=" * 80)
    print("COMPARISON: BASELINE vs INTERVENTION")
    print("=" * 80)
    
    print(f"\n{'Metric':<40} {'Baseline':>15} {'Intervention':>15} {'Difference':>15}")
    print("-" * 80)
    
    metrics = {
        'Final Population': ('final_pop', lambda x: f"{x:,.0f}"),
        'Survival Rate (%)': ('survival_pct', lambda x: f"{x:.1f}%"),
        'Average Age': ('avg_age', lambda x: f"{x:.1f} yrs"),
        'CVD Prevalence (%)': ('cvd_prev', lambda x: f"{x:.1f}%"),
        'Lung Cancer Prevalence (%)': ('lung_cancer_prev', lambda x: f"{x:.1f}%"),
    }
    
    for label, (key, formatter) in metrics.items():
        val1 = result1[key]
        val2 = result2[key]
        
        if isinstance(val1, float) and isinstance(val2, float):
            diff = val2 - val1
            diff_str = f"{diff:+.1f}"
        else:
            diff_str = "N/A"
        
        print(f"{label:<40} {formatter(val1):>15} {formatter(val2):>15} {diff_str:>15}")
    
    print()
    print("✅ Demo complete!")
    print("\n💡 To run the interactive app:")
    print("   streamlit run interactive_simulation_app.py")


def run_scenario(
    name: str,
    population: int,
    years: int,
    fertility_mult: float,
    mortality_mult: float,
    rf_multipliers: Dict[str, float]
) -> Dict:
    """
    Run a single simulation scenario.
    
    Args:
        name: Scenario name (for printing)
        population: Initial population size
        years: Simulation duration
        fertility_mult: Fertility multiplier
        mortality_mult: Mortality multiplier
        rf_multipliers: Risk factor multipliers
    
    Returns:
        Dictionary of results
    """
    print(f"Scenario: {name}")
    print(f"  Population: {population:,}")
    print(f"  Duration: {years} years")
    print(f"  Fertility multiplier: {fertility_mult}")
    print(f"  Mortality multiplier: {mortality_mult}")
    print(f"  Risk factors: {', '.join([f'{rf}={mult}' for rf, mult in rf_multipliers.items() if mult != 1.0])}")
    print()
    
    # Create disease model
    disease_model = DiseaseModel()
    
    # Create engine
    engine = SimulationEngine(disease_model=disease_model, seed=42)
    engine.fertility_rate = fertility_mult
    engine.mortality_multiplier = mortality_mult
    
    # Modify RF initialization
    original_init_rf = engine._init_risk_factors
    
    def modified_init_rf(citizen):
        rf = original_init_rf(citizen)
        age_years = citizen.age_years
        
        if age_years >= 15:
            # Apply multipliers
            if rf.get("smoking", 0) and rf_multipliers.get("smoking", 1.0) < 1.0:
                if engine.rng.random() > rf_multipliers.get("smoking", 1.0):
                    rf["smoking"] = 0
            
            # Similar for other RFs (simplified for demo)
            for rf_name in rf_multipliers:
                if rf_multipliers[rf_name] < 1.0:
                    if rf.get(rf_name, 0) == 1 and engine.rng.random() > rf_multipliers[rf_name]:
                        rf[rf_name] = 0
        
        return rf
    
    engine._init_risk_factors = modified_init_rf
    
    # Create population
    print(f"  Creating {population:,} citizens...")
    engine._create_synthetic_population(population)
    initial_pop = len([c for c in engine.citizens.values() if c.alive])
    
    # Run simulation
    print(f"  Running {years}-year simulation...")
    engine.run(months=years * 12)
    
    # Collect results
    final_citizens = [c for c in engine.citizens.values() if c.alive]
    final_pop = len(final_citizens)
    avg_age = sum(c.age_years for c in final_citizens) / len(final_citizens) if final_citizens else 0
    
    cvd_count = sum(1 for c in final_citizens if c.diseases.get("CVD", 0) == 1)
    lung_cancer_count = sum(1 for c in final_citizens if c.diseases.get("Lung Cancer", 0) == 1)
    
    cvd_prev = (cvd_count / final_pop * 100) if final_pop > 0 else 0
    lung_cancer_prev = (lung_cancer_count / final_pop * 100) if final_pop > 0 else 0
    survival_pct = (final_pop / initial_pop * 100) if initial_pop > 0 else 0
    
    results = {
        'final_pop': final_pop,
        'survival_pct': survival_pct,
        'avg_age': avg_age,
        'cvd_prev': cvd_prev,
        'lung_cancer_prev': lung_cancer_prev,
    }
    
    print(f"  Results:")
    print(f"    - Final population: {final_pop:,}")
    print(f"    - Survival rate: {survival_pct:.1f}%")
    print(f"    - Average age: {avg_age:.1f} years")
    print(f"    - CVD prevalence: {cvd_prev:.1f}%")
    print(f"    - Lung Cancer prevalence: {lung_cancer_prev:.1f}%")
    
    return results


if __name__ == "__main__":
    run_comparison_demo()
