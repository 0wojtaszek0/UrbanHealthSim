# Risk Factors Implementation Documentation
## Urban Health Agent-Based Model (URBAN-ABM)

---

## Executive Summary

Risk factors are behavioral and physiological characteristics that increase the probability of disease onset and mortality. The simulation implements 7 risk factors using a **Cox Proportional Hazards** model:

- **Smoking**, **Obesity**, **Physical Inactivity**, **Alcohol Abuse**
- **High Cholesterol**, **Hypertension (Stage 0)**, **Family History**

Each risk factor has a disease-specific hazard ratio (HR) that multiplicatively increases disease onset risk.

---

## 1. RISK FACTORS OVERVIEW

### 1.1 List of Risk Factors

| # | Risk Factor | Diseases Affected | Hazard Ratios |
|---|-------------|-------------------|---------------|
| 1 | **smoking** | CVD, Lung Cancer | HR=2.5, HR=15.0 |
| 2 | **obesity** | CVD | HR=1.7 |
| 3 | **physical_inactivity** | CVD, Lung Cancer | HR=1.4, HR=1.2 |
| 4 | **alcohol_abuse** | CVD, Lung Cancer | HR=1.3, HR=1.3 |
| 5 | **high_cholesterol** | CVD | HR=2.0 |
| 6 | **hypertension_stage0** | CVD | HR=2.2 |
| 7 | **family_history** | CVD, Lung Cancer | HR=1.5, HR=1.5 |

### 1.2 Hazard Ratios Explained

A **Hazard Ratio (HR)** quantifies the relative increase in disease risk:
- **HR = 1.0**: No effect (baseline risk)
- **HR > 1.0**: Increased risk
- **HR = 2.5**: Smokers have 2.5× higher risk of CVD compared to non-smokers

In the model, HRs are converted to β coefficients: **β = ln(HR)**

---

## 2. RISK FACTOR INITIALIZATION

### 2.1 Age-Based Prevalence

Risk factors are assigned during synthetic population creation based on age:

```python
# Smoking (20-70 years)
smoking_prob = 0.25 * (1 - ((age - 45)² / 50²))  # Peak at age 45
smoking_prob = max(smoking_prob, 0.10)

# Obesity (increases with age)
obesity_prob = 0.15 + (age - 20) * 0.008  # Min 5%, Max 45%

# Physical Inactivity (increases with age)
inactivity_prob = 0.2 + (age - 20) * 0.005  # Min 10%, Max ~45%

# Alcohol Abuse (uniform by age: 20-65)
alcohol_prob = 0.08  # 8% of working-age population

# High Cholesterol (increases with age)
cholesterol_prob = (age - 20) * 0.006  # Min 1%, Max 40%

# Hypertension Stage 0 (increases after age 30)
hypertension_prob = (age - 30) * 0.008  # Min 1%, Max 35%

# Family History (constant, age-independent)
family_history_prob = 0.15  # 15% of population
```

### 2.2 Prevalence Assumptions

These probabilities are calibrated to match epidemiological data:
- **Smoking**: ~20-25% prevalence in working-age (Polish population)
- **Obesity**: ~15-35% increasing with age (BMI ≥ 30)
- **Physical Inactivity**: ~20-40% increasing with age
- **Alcohol Abuse**: ~8% working-age population
- **High Cholesterol**: ~1-40% increasing with age (total cholesterol > 200 mg/dL)
- **Hypertension Stage 0**: ~1-35% increasing with age (SBP 120-139 or DBP 80-89)
- **Family History**: ~15% constant (one parent or sibling with CVD/cancer)

### 2.3 Risk Factor Storage

Each citizen has a **risk_factors dictionary**:

```python
citizen.risk_factors = {
    "smoking": 1,              # Has risk factor (1) or not (0)
    "obesity": 0,
    "physical_inactivity": 1,
    "alcohol_abuse": 0,
    "high_cholesterol": 1,
    "hypertension_stage0": 0,
    "family_history": 0,
}
```

---

## 3. MATHEMATICAL MODEL: COX PROPORTIONAL HAZARDS

### 3.1 Monthly Hazard Increment

Each month, the cumulative disease hazard increases for each citizen:

```
Δh = λ₀ × exp(γ·(age-30)) × exp(Σ βᵢ·RFᵢ)
```

Where:
- **λ₀** = Baseline hazard at age 30 (disease-specific)
- **γ** = Age hazard growth coefficient (Gompertz-like aging)
- **βᵢ** = Log hazard ratio for risk factor i: βᵢ = ln(HRᵢ)
- **RFᵢ** = Risk factor presence (0 or 1)
- **Δh** = Monthly hazard increment

### 3.2 Baseline Hazards (λ₀)

Monthly baseline hazards at age 30 (disease-specific):

| Disease | Baseline Hazard | Annual Equiv. |
|---------|-----------------|---------------|
| CVD | 6.0×10⁻⁵ | ~0.72% |
| Lung Cancer | 3.0×10⁻⁶ | ~0.036% |

**Calibration note**: These are calibrated so that a 70-year-old smoker has ~15-20% lifetime risk of lung cancer.

### 3.3 Age Hazard Growth (γ)

Exponential hazard acceleration with age (Gompertz model):

```
λ(age) = λ₀ × exp(γ·(age-30))
```

| Disease | γ | Doubling Time | Effect |
|---------|---|---------------|--------|
| CVD | 0.06 | ~12 years | Hazard doubles every 12 years |
| Lung Cancer | 0.075 | ~9 years | Hazard doubles every 9 years |

### 3.4 Risk Factor β Coefficients

Logarithm of hazard ratios used in the exponential:

**For CVD:**
```
β_smoking = ln(2.5) = 0.916
β_obesity = ln(1.7) = 0.531
β_physical_inactivity = ln(1.4) = 0.336
β_alcohol_abuse = ln(1.3) = 0.262
β_high_cholesterol = ln(2.0) = 0.693
β_hypertension = ln(2.2) = 0.788
β_family_history = ln(1.5) = 0.405
```

**For Lung Cancer:**
```
β_smoking = ln(15.0) = 2.708  ← Dominant risk factor
β_physical_inactivity = ln(1.2) = 0.182
β_alcohol_abuse = ln(1.3) = 0.262
β_family_history = ln(1.5) = 0.405
β_obesity = 0.0  ← No effect
β_high_cholesterol = 0.0  ← No effect
β_hypertension = 0.0  ← No effect
```

### 3.5 Example Calculation

**Scenario**: 60-year-old male with smoking, high cholesterol, and hypertension (CVD)

```
Δh = 6.0×10⁻⁵ × exp(0.06 × (60-30)) × exp(0.916 + 0.693 + 0.788)

Step 1: Age factor
  exp(0.06 × 30) = exp(1.8) ≈ 6.05

Step 2: Risk factor modifier
  exp(0.916 + 0.693 + 0.788) = exp(2.397) ≈ 10.99

Step 3: Final hazard
  Δh = 6.0×10⁻⁵ × 6.05 × 10.99 ≈ 3.99×10⁻³ (0.4%)

Compare to baseline (no risk factors):
  Δh_baseline = 6.0×10⁻⁵ × 6.05 ≈ 3.63×10⁻⁴ (0.036%)

Hazard ratio = 0.399% / 0.0363% ≈ 11× higher risk
```

### 3.6 Disease Onset (Poisson Approximation)

Once monthly hazard is calculated, disease onset occurs with probability:

```
P(onset) = 1 - exp(-Δh)
```

For small Δh, this approximates Poisson: P(onset) ≈ Δh

When disease onset occurs: `citizen.diseases[disease] = 1`

The cumulative hazard accumulates: `citizen.cumulative_hazard[disease] += Δh`

---

## 4. IMPACT ON MORTALITY

### 4.1 Mortality Calculation Components

Monthly mortality risk has multiple components:

```
P(death) = base_rate × disease_multiplier × cox_multiplier × global_multiplier
```

Where:
- **base_rate** = GUS-derived age-sex mortality table (per month)
- **disease_multiplier** = 1.0 + 0.04 × disability_score
- **cox_multiplier** = exp(Σ γ_d · min(H_cum[d], cap) · 1{disease_d active})
- **global_multiplier** = engine.mortality_multiplier (calibrated from GridSearch)

### 4.2 Cox Mortality Multiplier

Active diseases (status=1) increase mortality based on accumulated hazard:

```
ln(cox_multiplier) = Σ γ_d · min(H_cum[d], HAZARD_CAP)
```

Where:
| Disease | γ_d | Effect |
|---------|-----|--------|
| CVD | 1.2 | Moderate increase |
| Lung Cancer | 2.5 | Strong increase |

**HAZARD_CAP = 1.5** prevents numerical overflow from exp().

### 4.3 Example: Mortality Impact

**60-year-old male with active CVD** (H_cum = 0.8):

```
Base mortality (GUS table, age 60, male): 1.375×10⁻³ (per month)

Disease multiplier (disability_score ≈ 0.25):
  1.0 + 0.04 × 0.25 = 1.01

Cox multiplier (CVD active, γ = 1.2):
  exp(1.2 × min(0.8, 1.5)) = exp(0.96) ≈ 2.61

Global multiplier (engine.mortality_multiplier ≈ 0.5, from GridSearch):
  0.5

Total monthly mortality:
  1.375×10⁻³ × 1.01 × 2.61 × 0.5 ≈ 1.81×10⁻³ (0.18%)

Annual mortality risk:
  1 - (1 - 0.00181)^12 ≈ 2.16%
```

---

## 5. RISK FACTOR INTERACTIONS & DEPENDENCIES

### 5.1 Multiplicative (Non-Additive) Model

Risk factors act multiplicatively in the exponential:

```
Relative Risk = exp(Σ β_i · RF_i)
```

**Example**: Two risk factors (smoking + cholesterol)

```
Single smoking:     RR = exp(0.916) ≈ 2.5
Single cholesterol: RR = exp(0.693) ≈ 2.0
Together:           RR = exp(0.916 + 0.693) = exp(1.609) ≈ 5.0
                    (NOT 2.5 + 2.0 = 4.5)
```

### 5.2 Independence Assumption

Risk factors are **modeled independently**:
- Presence of one RF doesn't affect prevalence of another (in code)
- However, they jointly increase disease hazard (mathematically)
- **Not captured**: Confounding (e.g., smokers more likely to be inactive)

### 5.3 Age Thresholds

- **Children (< 15 years)**: All RF initialized to 0 (no disease onset)
- **Adults (≥ 18 years)**: RF-based hazard accumulation begins
- **Effective age cap**: Age clamped to ≥ 18 in hazard formula (no acceleration before age 18)

---

## 6. SIMULATION CALIBRATION

### 6.1 GridSearch Optimization

The simulation uses GridSearch to find optimal:
- **fertility_multiplier**: Adjusts birth rates (grid: 0.5 to 2.1)
- **mortality_multiplier**: Adjusts all mortality rates (grid: 0.5 to 2.1)

Purpose: Achieve realistic population growth over 50 years.

### 6.2 Typical Results

After 50 years with 50,000 initial population:
- **Final population**: ~45,000-55,000 (depending on multipliers)
- **Survival rate**: ~90-92%
- **Average disease prevalence**: ~35-40% (CVD), ~4-5% (Lung Cancer)

---

## 7. RISK FACTOR MODIFICATIONS IN SIMULATION

### 7.1 Static vs Dynamic

**Current implementation**: Risk factors are:
- Assigned at birth/population creation
- **Static** during simulation (don't change month-to-month)
- Exception: Newborns start with RF=0

### 7.2 Potential Extensions

Future enhancements could include:
- **RF progression**: smoking → hypertension → CVD (multi-stage)
- **Intervention modeling**: RF reduction (e.g., smoking cessation)
- **Population-level trends**: RF prevalence changing over time
- **Spatial variation**: Zone-specific RF distributions

---

## 8. DATA SOURCES & CALIBRATION

### 8.1 Polish Demographics (GUS)

- Mortality tables: GUS "Tablice Trwania Życia" (Life Tables) 2021
- Age distribution: Central Statistical Office Poland 2021 Census
- Fertility rates: GUS reproduction data (TFR ≈ 1.26)

### 8.2 Disease Epidemiology

- **CVD**: WHO, ESC (European Society of Cardiology)
  - Prevalence: ~35% in adult population
  - HR estimates: smoking 2.5×, obesity 1.7×, cholesterol 2.0×
  
- **Lung Cancer**: GLOBOCAN 2020, CDC
  - Prevalence: ~4.5% (in simulation)
  - Smoking HR: ~15× (dominant risk factor)
  - Baseline 10-year lifetime risk (nonsmoker, age 60): ~0.5%

### 8.3 Hazard Ratio Sources

| RF | Disease | Source | Value |
|---|---------|--------|-------|
| Smoking | CVD | Framingham, ESC | 2.5 |
| Smoking | Lung Cancer | CDC, IARC | 15.0 |
| Obesity | CVD | Framingham, AHA | 1.7 |
| Hypertension | CVD | ESC Guidelines | 2.2 |
| Cholesterol | CVD | Framingham, ATP III | 2.0 |
| Physical Inactivity | CVD | WHO, AHA | 1.4 |
| Family History | CVD/Cancer | Framingham, BRCA | 1.5 |
| Alcohol | CVD | Meta-analysis | 1.3 |

---

## 9. IMPLEMENTATION CODE LOCATIONS

### 9.1 File Structure

```
disease_model.py
├── DiseaseModel class
├── HAZARD_BETA (β coefficients)
├── BASELINE_HAZARD (λ₀ values)
├── AGE_HAZARD_GROWTH (γ coefficients)
├── MORTALITY_GAMMA (γ_d for mortality)
├── monthly_hazard_increment()
└── cox_mortality_log_hazard()

simulation_engine.py
├── SimulationEngine class
├── _init_risk_factors() [RF initialization]
├── handle_deaths() [hazard accumulation & mortality]
└── disease_model.monthly_hazard_increment() [called each month]

citizen.py
├── Citizen class
├── risk_factors dict
├── cumulative_hazard dict
├── mortality_risk() [legacy method]
└── compute_disability_score()
```

### 9.2 Key Methods

1. **Initialization**: `SimulationEngine._init_risk_factors(citizen)`
   - Assigns RF based on age profiles
   
2. **Hazard accumulation**: `DiseaseModel.monthly_hazard_increment(disease, age, RF)`
   - Computes Δh each month
   
3. **Onset**: `SimulationEngine.handle_deaths()` step 1
   - P(onset) = 1 - exp(-Δh)
   
4. **Mortality**: `SimulationEngine.handle_deaths()` step 3
   - Combines multiple multipliers

---

## 10. VISUALIZATION & ANALYSIS

### 10.1 Risk Factor Impact Reports

Output files track RF effects:
- `risk_factor_rankings.csv`: RF contribution to disease burden
- `risk_factor_summary.txt`: Text summary of RF prevalence

### 10.2 Comparative Analysis

GridSearch runs compare:
- Baseline scenario (RF multiplier = 1.0)
- High-risk scenario (RF multiplier = 1.5+)
- Health promotion scenario (RF multiplier = 0.5)

---

## APPENDIX: GLOSSARY

- **Hazard**: Instantaneous risk of an event (disease onset or death) at a given time
- **Cumulative Hazard (H_cum)**: Accumulated hazard over time (biological "damage")
- **Hazard Ratio (HR)**: Relative increase in hazard for exposed vs. unexposed
- **β coefficient**: Natural log of hazard ratio (used in Cox model exponential)
- **Onset**: First occurrence of disease (transition from inactive to active state)
- **Disability Score**: Weighted sum of active diseases (impacts mortality and fertility)
- **Cox Model**: Proportional Hazards model (assumes HR constant over time)
- **Gompertz**: Exponential aging model (mortality/hazard doubles at fixed time intervals)
- **Poisson Approximation**: For rare events, P(event) ≈ Δh when Δh is small

---

**Document Version**: 1.0  
**Last Updated**: May 2026  
**Simulation**: URBAN-ABM v1.0 (Polish Demographics, 50,000 agents, 50 years)
