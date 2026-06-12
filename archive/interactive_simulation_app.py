"""
Interactive Risk Factor Simulation Application
Allows users to adjust risk factor values and run simulations
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Tuple, List
import json
import math
from datetime import datetime

from simulation_engine import SimulationEngine
from disease_model import DiseaseModel
from citizen import Citizen


def main():
    """Main Streamlit application."""
    
    st.set_page_config(
        page_title="Risk Factor Simulator",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title(" Interactive Risk Factor Simulation")
    st.markdown("""
    Adjust risk factor prevalence multipliers and run a demographic simulation 
    with 50,000 agents over 50 years to see impacts on population health.
    """)
    
    
    
    
    st.sidebar.header(" Simulation Parameters")
    
    with st.sidebar:
        st.subheader("Population Settings")
        
        population_size = st.slider(
            "Initial Population Size",
            min_value=1000,
            max_value=100000,
            value=50000,
            step=5000,
            help="Number of agents to simulate"
        )
        
        simulation_years = st.slider(
            "Simulation Duration (years)",
            min_value=5,
            max_value=50,
            value=50,
            step=5,
            help="Number of years to simulate"
        )
        
        fertility_mult = st.slider(
            "Fertility Multiplier",
            min_value=0.5,
            max_value=2.5,
            value=1.0,
            step=0.1,
            help="Adjust birth rates (1.0 = baseline)"
        )
        
        mortality_mult = st.slider(
            "Mortality Multiplier",
            min_value=0.3,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Adjust death rates (1.0 = baseline)"
        )
        
        st.divider()
        st.subheader("Risk Factor Adjustments")
        st.markdown("*Multipliers: 1.0 = baseline, <1.0 = reduced, >1.0 = increased*")
        
        
        rf_multipliers = {}
        rf_names = [
            "smoking",
            "obesity",
            "physical_inactivity",
            "alcohol_abuse",
            "high_cholesterol",
            "hypertension_stage0",
            "family_history"
        ]
        
        for rf in rf_names:
            rf_multipliers[rf] = st.slider(
                f"{rf.replace('_', ' ').title()}",
                min_value=0.0,
                max_value=3.0,
                value=1.0,
                step=0.1,
                help=f"Prevalence multiplier for {rf}"
            )
        
        st.divider()
        
        
        st.subheader("Quick Scenarios")
        scenario = st.selectbox(
            "Load preset:",
            ["Custom", "Healthy Population", "High-Risk", "Intervention (Best Case)"]
        )
        
        if scenario == "Healthy Population":
            for rf in rf_names:
                rf_multipliers[rf] = 0.5
        elif scenario == "High-Risk":
            for rf in rf_names:
                rf_multipliers[rf] = 1.5
        elif scenario == "Intervention (Best Case)":
            for rf in rf_names:
                rf_multipliers[rf] = 0.7
        
        run_simulation = st.button(
            " Run Simulation",
            key="run_button",
            use_container_width=True,
            type="primary"
        )
    
    
    
    
    
    if not run_simulation:
        st.info("""
        ### How to use:
        1. **Adjust parameters** in the sidebar (left panel)
        2. **Select risk factor multipliers** (0.0-3.0 scale)
        3. **Click "Run Simulation"** to start
        4. **View results** including population pyramid and risk analysis
        
        ### What it measures:
        - **Population Growth**: Final population after simulation period
        - **Age Pyramid**: Demographic distribution by age and sex
        - **Disease Impact**: CVD and Lung Cancer prevalence
        - **Risk Factor Analysis**: Contribution of each RF to disease burden
        """)
        return
    
    
    st.session_state['run_count'] = st.session_state.get('run_count', 0) + 1
    
    with st.spinner(" Running simulation... (this may take 1-2 minutes)"):
        results = run_simulation_with_rf(
            population_size=population_size,
            years=simulation_years,
            fertility_multiplier=fertility_mult,
            mortality_multiplier=mortality_mult,
            rf_multipliers=rf_multipliers
        )
    
    if results is None:
        st.error("Simulation failed. Please check parameters and try again.")
        return
    
    st.success(" Simulation complete!")
    
    
    
    
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Initial Population",
            f"{results['initial_pop']:,}",
            help="Starting number of agents"
        )
    
    with col2:
        final_pop = results['final_pop']
        change = final_pop - results['initial_pop']
        st.metric(
            "Final Population",
            f"{final_pop:,}",
            delta=f"{change:+,}",
            help="Population after simulation period"
        )
    
    with col3:
        survival_rate = (final_pop / results['initial_pop']) * 100 if results['initial_pop'] > 0 else 0
        st.metric(
            "Survival Rate",
            f"{survival_rate:.1f}%",
            help="Percentage of initial population still alive"
        )
    
    with col4:
        avg_age = results['avg_age_final']
        st.metric(
            "Average Age",
            f"{avg_age:.1f} years",
            help="Mean age of living population at end"
        )
    
    st.divider()
    
    
    st.subheader(" Population Age Pyramid (Year 50)")
    fig_pyramid = create_age_pyramid(results['final_pyramid'])
    st.plotly_chart(fig_pyramid, use_container_width=True)
    
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(" Disease Prevalence")
        fig_disease = create_disease_chart(results['disease_prevalence'])
        st.plotly_chart(fig_disease, use_container_width=True)
    
    
    with col2:
        st.subheader(" Risk Factor Impact")
        fig_rf = create_risk_factor_chart(results['rf_impact'])
        st.plotly_chart(fig_rf, use_container_width=True)
    
    st.divider()
    
    
    st.subheader(" Population Trends Over Time")
    fig_trends = create_trends_chart(results['yearly_stats'])
    st.plotly_chart(fig_trends, use_container_width=True)
    
    
    st.subheader(" Detailed Statistics")
    
    stats_df = pd.DataFrame({
        'Metric': [
            'Initial Population',
            'Final Population',
            'Deaths',
            'Births',
            'Net Change',
            'Survival Rate (%)',
            'Avg Age (Initial)',
            'Avg Age (Final)',
            'CVD Cases',
            'Lung Cancer Cases',
            'Multimorbidity (%)',
        ],
        'Value': [
            f"{results['initial_pop']:,.0f}",
            f"{results['final_pop']:,.0f}",
            f"{results['deaths']:,.0f}",
            f"{results['births']:,.0f}",
            f"{results['final_pop'] - results['initial_pop']:+,.0f}",
            f"{(results['final_pop']/results['initial_pop']*100):.2f}%",
            f"{results['avg_age_initial']:.1f}",
            f"{results['avg_age_final']:.1f}",
            f"{results['cvd_count']:,.0f}",
            f"{results['lung_cancer_count']:,.0f}",
            f"{results['multimorbidity_pct']:.1f}%",
        ]
    })
    
    st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    
    st.subheader(" Risk Factor Settings Applied")
    rf_df = pd.DataFrame({
        'Risk Factor': [rf.replace('_', ' ').title() for rf in rf_names],
        'Multiplier': [rf_multipliers[rf] for rf in rf_names],
        'Effect': [
            ' Reduced' if rf_multipliers[rf] < 1 else
            ' Increased' if rf_multipliers[rf] > 1 else
            ' Baseline'
            for rf in rf_names
        ]
    })
    st.dataframe(rf_df, use_container_width=True, hide_index=True)
    
    
    st.subheader(" Export Results")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        results_json = json.dumps({
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'population_size': population_size,
                'years': simulation_years,
                'fertility_multiplier': fertility_mult,
                'mortality_multiplier': mortality_mult,
                'risk_factors': rf_multipliers
            },
            'results': {
                'initial_pop': results['initial_pop'],
                'final_pop': results['final_pop'],
                'survival_rate': (results['final_pop']/results['initial_pop']*100),
            }
        }, indent=2)
        
        st.download_button(
            label=" Download Results (JSON)",
            data=results_json,
            file_name=f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with export_col2:
        st.info(" Tip: Screenshot the pyramid or download the JSON to compare scenarios")






def run_simulation_with_rf(
    population_size: int,
    years: int,
    fertility_multiplier: float,
    mortality_multiplier: float,
    rf_multipliers: Dict[str, float]
) -> Dict:
    """
    Run simulation with adjusted risk factors.
    
    Args:
        population_size: Initial population
        years: Simulation duration in years
        fertility_multiplier: Fertility adjustment
        mortality_multiplier: Mortality adjustment
        rf_multipliers: Dict of RF multipliers
    
    Returns:
        Dictionary of results or None if failed
    """
    try:
        
        disease_model = DiseaseModel()
        
        
        engine = SimulationEngine(
            disease_model=disease_model,
            seed=42
        )
        
        
        engine.fertility_rate = fertility_multiplier
        engine.mortality_multiplier = mortality_multiplier
        
        
        
        original_init_rf = engine._init_risk_factors
        
        def modified_init_rf(citizen):
            """Modified RF initialization with multipliers."""
            rf = original_init_rf(citizen)
            
            
            
            
            
            
            age_years = citizen.age_years
            
            if age_years >= 15:
                
                smoking_prob = 0.0
                if 20 <= age_years <= 70:
                    peak_age = 45
                    smoking_prob = 0.25 * (1 - ((age_years - peak_age) ** 2) / (50 ** 2))
                    smoking_prob = max(smoking_prob, 0.10)
                smoking_prob *= rf_multipliers.get("smoking", 1.0)
                if engine.rng.random() < min(smoking_prob, 1.0):
                    rf["smoking"] = 1
                
                
                obesity_prob = 0.15 + (age_years - 20) * 0.008 if age_years > 20 else 0.05
                obesity_prob = min(obesity_prob, 0.45) * rf_multipliers.get("obesity", 1.0)
                if engine.rng.random() < min(obesity_prob, 1.0):
                    rf["obesity"] = 1
                
                
                inactivity_prob = 0.2 + (age_years - 20) * 0.005 if age_years > 20 else 0.1
                inactivity_prob *= rf_multipliers.get("physical_inactivity", 1.0)
                if engine.rng.random() < min(inactivity_prob, 1.0):
                    rf["physical_inactivity"] = 1
                
                
                alcohol_prob = (0.08 if 20 <= age_years <= 65 else 0.02) * rf_multipliers.get("alcohol_abuse", 1.0)
                if engine.rng.random() < min(alcohol_prob, 1.0):
                    rf["alcohol_abuse"] = 1
                
                
                cholesterol_prob = ((age_years - 20) * 0.006 if age_years > 20 else 0.01) * rf_multipliers.get("high_cholesterol", 1.0)
                if engine.rng.random() < min(cholesterol_prob, 1.0):
                    rf["high_cholesterol"] = 1
                
                
                hypertension_prob = ((age_years - 30) * 0.008 if age_years > 30 else 0.01) * rf_multipliers.get("hypertension_stage0", 1.0)
                if engine.rng.random() < min(hypertension_prob, 1.0):
                    rf["hypertension_stage0"] = 1
                
                
                family_prob = 0.15 * rf_multipliers.get("family_history", 1.0)
                if engine.rng.random() < min(family_prob, 1.0):
                    rf["family_history"] = 1
            
            return rf
        
        engine._init_risk_factors = modified_init_rf
        
        
        engine._create_synthetic_population(population_size)
        initial_pop = len([c for c in engine.citizens.values() if c.alive])
        avg_age_initial = np.mean([c.age_years for c in engine.citizens.values() if c.alive])
        
        
        engine.run(months=years * 12)
        
        
        final_citizens = [c for c in engine.citizens.values() if c.alive]
        final_pop = len(final_citizens)
        avg_age_final = np.mean([c.age_years for c in final_citizens]) if final_pop > 0 else 0
        
        
        cvd_count = sum(1 for c in final_citizens if c.diseases.get("CVD", 0) == 1)
        lung_cancer_count = sum(1 for c in final_citizens if c.diseases.get("Lung Cancer", 0) == 1)
        multimorbidity_count = sum(1 for c in final_citizens if c.num_conditions() >= 2)
        multimorbidity_pct = (multimorbidity_count / final_pop * 100) if final_pop > 0 else 0
        
        
        pyramid = build_age_pyramid(final_citizens)
        
        
        rf_impact = calculate_rf_impact(final_citizens, disease_model)
        
        
        disease_prev = {
            'CVD': (cvd_count / final_pop * 100) if final_pop > 0 else 0,
            'Lung Cancer': (lung_cancer_count / final_pop * 100) if final_pop > 0 else 0
        }
        
        
        deaths = initial_pop - final_pop + len([c for c in engine.citizens.values() if c.alive])
        
        births = final_pop - initial_pop + deaths
        
        return {
            'initial_pop': initial_pop,
            'final_pop': final_pop,
            'avg_age_initial': avg_age_initial,
            'avg_age_final': avg_age_final,
            'deaths': deaths,
            'births': max(births, 0),
            'cvd_count': cvd_count,
            'lung_cancer_count': lung_cancer_count,
            'multimorbidity_pct': multimorbidity_pct,
            'disease_prevalence': disease_prev,
            'rf_impact': rf_impact,
            'final_pyramid': pyramid,
            'yearly_stats': engine.yearly_stats
        }
    
    except Exception as e:
        st.error(f"Error during simulation: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def build_age_pyramid(citizens: List[Citizen]) -> Dict[str, Dict[str, int]]:
    """Build age pyramid data."""
    age_groups = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39',
                  '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79',
                  '80-84', '85-89', '90+']
    
    pyramid = {group: {'male': 0, 'female': 0} for group in age_groups}
    
    for citizen in citizens:
        age = int(citizen.age_years)
        
        if age < 5:
            group = '0-4'
        elif age < 10:
            group = '5-9'
        elif age < 15:
            group = '10-14'
        else:
            group_idx = (age - 15) // 5
            if group_idx < len(age_groups) - 1:
                start = 15 + group_idx * 5
                group = f'{start}-{start+4}'
            else:
                group = '90+'
        
        if group in pyramid:
            pyramid[group][citizen.sex] += 1
    
    return pyramid


def create_age_pyramid(pyramid: Dict[str, Dict[str, int]]) -> go.Figure:
    """Create age pyramid visualization."""
    ages = list(pyramid.keys())
    males = [-pyramid[age]['male'] for age in ages]
    females = [pyramid[age]['female'] for age in ages]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=ages,
        x=males,
        orientation='h',
        name='Male',
        marker=dict(color='#3498db')
    ))
    
    fig.add_trace(go.Bar(
        y=ages,
        x=females,
        orientation='h',
        name='Female',
        marker=dict(color='#e74c3c')
    ))
    
    fig.update_layout(
        barmode='overlay',
        title='Population Age Pyramid',
        xaxis_title='Population',
        yaxis_title='Age Group',
        height=500,
        hovermode='closest'
    )
    
    return fig


def create_disease_chart(disease_prev: Dict[str, float]) -> go.Figure:
    """Create disease prevalence chart."""
    fig = go.Figure(data=[
        go.Bar(
            x=list(disease_prev.keys()),
            y=list(disease_prev.values()),
            marker=dict(color=['#e74c3c', '#f39c12'])
        )
    ])
    
    fig.update_layout(
        title='Disease Prevalence (%)',
        xaxis_title='Disease',
        yaxis_title='Prevalence (%)',
        height=400,
        showlegend=False
    )
    
    return fig


def create_risk_factor_chart(rf_impact: Dict[str, float]) -> go.Figure:
    """Create risk factor contribution chart."""
    rfs = list(rf_impact.keys())
    impacts = list(rf_impact.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=rfs,
            y=impacts,
            marker=dict(color='#16a085')
        )
    ])
    
    fig.update_layout(
        title='Risk Factor Contribution to Disease',
        xaxis_title='Risk Factor',
        yaxis_title='Relative Impact',
        height=400,
        xaxis=dict(tickangle=-45),
        showlegend=False
    )
    
    return fig


def create_trends_chart(yearly_stats: Dict) -> go.Figure:
    """Create population trends chart."""
    if not yearly_stats:
        return go.Figure().add_annotation(text="No data available")
    
    years = sorted(yearly_stats.keys())
    populations = [yearly_stats[y].get('total_population', 0) for y in years]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years,
        y=populations,
        mode='lines+markers',
        name='Population',
        line=dict(color='#3498db', width=3),
        marker=dict(size=5)
    ))
    
    fig.update_layout(
        title='Population Growth Over Time',
        xaxis_title='Year',
        yaxis_title='Population',
        height=400,
        hovermode='x unified'
    )
    
    return fig


def calculate_rf_impact(citizens: List[Citizen], disease_model: DiseaseModel) -> Dict[str, float]:
    """Calculate relative impact of each risk factor on disease burden."""
    rf_names = Citizen.DEFAULT_RISK_FACTORS
    
    
    rf_counts = {rf: 0 for rf in rf_names}
    rf_disease_burden = {rf: 0 for rf in rf_names}
    
    for citizen in citizens:
        disability = citizen.disability_score
        
        for rf, value in citizen.risk_factors.items():
            if value == 1:
                rf_counts[rf] += 1
                rf_disease_burden[rf] += disability
    
    total_citizens = len(citizens) if citizens else 1
    
    
    rf_impact = {}
    for rf in rf_names:
        if rf_counts[rf] > 0:
            rf_impact[rf] = rf_disease_burden[rf] / total_citizens
        else:
            rf_impact[rf] = 0
    
    return rf_impact


if __name__ == "__main__":
    main()
