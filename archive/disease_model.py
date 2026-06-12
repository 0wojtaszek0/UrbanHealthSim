"""
Module for disease modeling in the simulation.
Handles disease selection, disability weights, and disease initialization.
"""

import math
from typing import Dict, List, Optional


class DiseaseModel:
    """
    Manages disease definitions and characteristics in the simulation.
    
    Attributes:
        diseases: List of selected disease names
        disability_weights: Dictionary mapping disease names to disability weights
        disease_prevalence: Dictionary mapping disease names to prevalence rates
        transition_probabilities: Dictionary mapping health states to transition probabilities
    """
    
    
    DEFAULT_DISEASES = [
        "CVD",
        "Lung Cancer",
    ]

    
    DEFAULT_PREVALENCE = {
        "CVD": 35.0,
        "Lung Cancer": 4.5,
    }

    
    DEFAULT_DISABILITY_WEIGHTS = {
        "CVD": 0.25,
        "Lung Cancer": 0.55,
    }

    
    
    
    
    
    
    
    HAZARD_BETA: Dict[str, Dict[str, float]] = {
        "CVD": {
            "smoking":              math.log(2.5),
            "obesity":              math.log(1.7),
            "physical_inactivity":  math.log(1.4),
            "alcohol_abuse":        math.log(1.3),
            "high_cholesterol":     math.log(2.0),
            "hypertension_stage0":  math.log(2.2),
            "family_history":       math.log(1.5),
        },
        "Lung Cancer": {
            "smoking":              math.log(15.0),
            "obesity":              0.0,
            "physical_inactivity":  math.log(1.2),
            "alcohol_abuse":        math.log(1.3),
            "high_cholesterol":     0.0,
            "hypertension_stage0":  0.0,
            "family_history":       math.log(1.5),
        },
    }

    
    
    BASELINE_HAZARD: Dict[str, float] = {
        "CVD":                 6.0e-5,
        "Lung Cancer":         3.0e-6,
    }

    
    AGE_HAZARD_GROWTH: Dict[str, float] = {
        "CVD":                 0.06,   
        "Lung Cancer":         0.075,  
    }

    
    
    MORTALITY_GAMMA: Dict[str, float] = {
        "CVD":                  1.2,
        "Lung Cancer":          2.5,
    }

    
    HAZARD_CAP_FOR_MORTALITY: float = 1.5

    
    HEALTH_STATES = ["healthy", "exposed", "infected", "severe", "recovered"]

    
    DEFAULT_TRANSITION_PROBABILITIES = {
        "healthy_to_exposed": 0.01,
        "exposed_to_infected": 0.1,
        "infected_to_severe": 0.05,
        "severe_to_recovered": 0.2,
        "infected_to_recovered": 0.15,
        "severe_to_death": 0.1
    }
    
    def __init__(
        self,
        diseases: Optional[List[str]] = None,
        disability_weights: Optional[Dict[str, float]] = None,
        prevalence_rates: Optional[Dict[str, float]] = None,
        transition_probabilities: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Initialize the disease model.
        
        Args:
            diseases: List of disease names (defaults to top 3)
            disability_weights: Dictionary mapping disease names to disability scores
            prevalence_rates: Dictionary mapping disease names to prevalence percentages
            transition_probabilities: Dictionary mapping health states to transition probabilities
        """
        self.diseases: List[str] = diseases or self.DEFAULT_DISEASES.copy()
        self.disability_weights: Dict[str, float] = (
            disability_weights or self.DEFAULT_DISABILITY_WEIGHTS.copy()
        )
        self.disease_prevalence: Dict[str, float] = (
            prevalence_rates or self.DEFAULT_PREVALENCE.copy()
        )
        self.transition_probabilities: Dict[str, float] = (
            transition_probabilities or self.DEFAULT_TRANSITION_PROBABILITIES.copy()
        )
    
    def get_initial_diseases(self) -> Dict[str, int]:
        """
        Get a dictionary of all diseases initialized to 0 (not present).
        
        Returns:
            Dictionary with disease names as keys and 0 as values
        """
        return {disease: 0 for disease in self.diseases}
    
    def get_prevalence(self, disease_name: str) -> float:
        """
        Get the prevalence rate for a disease.
        
        Args:
            disease_name: Name of the disease
        
        Returns:
            Prevalence rate as percentage (0-100)
        """
        return self.disease_prevalence.get(disease_name, 0.0)
    
    def get_disability_weight(self, disease_name: str) -> float:
        """
        Get the disability weight for a disease.
        
        Args:
            disease_name: Name of the disease
        
        Returns:
            Disability weight (0-1 scale)
        """
        return self.disability_weights.get(disease_name, 0.1)
    
    def get_disease_count(self) -> int:
        """Get the total number of diseases in the model."""
        return len(self.diseases)
    
    def get_all_disability_weights(self) -> Dict[str, float]:
        """Get all disability weights as a dictionary."""
        return self.disability_weights.copy()
    
    def monthly_hazard_increment(
        self,
        disease: str,
        age_years: float,
        risk_factors: Dict[str, int],
    ) -> float:
        """
        Oblicz miesięczny przyrost hazardu Δh dla danej choroby u agenta.

        Δh = λ_0 × exp(γ·(age-30)) × exp(Σ β_i · RF_i)

        Args:
            disease: nazwa choroby
            age_years: wiek agenta (lata)
            risk_factors: słownik {RF: 0/1}

        Returns:
            miesięczny przyrost skumulowanego hazardu (≥ 0)
        """
        if disease not in self.HAZARD_BETA:
            return 0.0

        
        effective_age = max(age_years, 18.0)

        baseline = self.BASELINE_HAZARD[disease]
        gamma_age = self.AGE_HAZARD_GROWTH[disease]
        age_factor = math.exp(gamma_age * (effective_age - 30.0))

        beta_map = self.HAZARD_BETA[disease]
        log_modifier = sum(
            beta * risk_factors.get(rf, 0)
            for rf, beta in beta_map.items()
        )
        rf_modifier = math.exp(log_modifier)

        return baseline * age_factor * rf_modifier

    def cox_mortality_log_hazard(
        self,
        diseases: Dict[str, int],
        cumulative_hazard: Dict[str, float],
    ) -> float:
        """
        Logarytm mnożnika mortality wynikający z aktywnych chorób i ich akumulowanego H_cum.

        ln(multiplier) = Σ γ_d · min(H_cum[d], cap) · 1{disease_d active}

        Args:
            diseases: {disease: 0/1}
            cumulative_hazard: {disease: H_cum}

        Returns:
            log-hazard (do podstawienia w exp(·))
        """
        total = 0.0
        for disease, active in diseases.items():
            if active != 1:
                continue
            gamma = self.MORTALITY_GAMMA.get(disease, 0.0)
            if gamma == 0.0:
                continue
            h = cumulative_hazard.get(disease, 0.0)
            total += gamma * min(h, self.HAZARD_CAP_FOR_MORTALITY)
        return total

    def get_transition_probability(self, from_state: str, to_state: str) -> float:
        """
        Get the transition probability between two health states.

        Args:
            from_state: Current health state
            to_state: Target health state

        Returns:
            Probability of transitioning from `from_state` to `to_state`
        """
        key = f"{from_state}_to_{to_state}"
        return self.transition_probabilities.get(key, 0.0)
    
    def __repr__(self) -> str:
        """
        String representation for debugging.
        """
        disease_count = self.get_disease_count()
        total_prevalence = sum(self.disease_prevalence.values())
        return "DiseaseModel(diseases={}, total_prevalence={:.1f}%)".format(
            disease_count, total_prevalence
        )
