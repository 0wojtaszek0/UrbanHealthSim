# 🏥 Interactive Risk Factor Simulation Application

A Streamlit web application that allows you to interactively adjust risk factors and run demographic simulations to see the impact on population health over 50 years.

---

## 📋 Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

Or install Streamlit manually if needed:
```bash
pip3 install streamlit
```

### 2. Run the Application

```bash
streamlit run interactive_simulation_app.py
```

The app will open in your default browser at `http://localhost:8501`

---

## 🎮 How to Use

### Sidebar Controls (Left Panel)

1. **Population Settings**
   - **Initial Population Size**: Number of agents (1,000 to 100,000)
   - **Simulation Duration**: Years to simulate (5 to 50)
   - **Fertility Multiplier**: Adjust birth rates (0.5 to 2.5)
   - **Mortality Multiplier**: Adjust death rates (0.3 to 2.0)

2. **Risk Factor Adjustments** (7 sliders)
   - Each risk factor has a multiplier (0.0 to 3.0):
     - **0.0** = Eliminate risk factor completely
     - **1.0** = Baseline population prevalence
     - **1.5** = 50% increase in prevalence
     - **2.0** = Double the prevalence
     - **3.0** = Triple the prevalence

   Available risk factors:
   - 🚬 Smoking
   - ⚖️ Obesity
   - 🚫 Physical Inactivity
   - 🍺 Alcohol Abuse
   - 🍔 High Cholesterol
   - 💊 Hypertension Stage 0
   - 👨‍👩‍👧 Family History

3. **Quick Scenarios** (Presets)
   - **Custom**: Manually set all parameters
   - **Healthy Population**: All RF multipliers = 0.5
   - **High-Risk**: All RF multipliers = 1.5
   - **Intervention (Best Case)**: All RF multipliers = 0.7

### Running Simulation

1. Adjust all parameters as desired
2. Click **"🚀 Run Simulation"** button
3. Wait for simulation to complete (1-2 minutes)
4. View results

---

## 📊 Results Output

After simulation completes, you'll see:

### 1. Summary Metrics
- Initial Population
- Final Population (with change delta)
- Survival Rate (%)
- Average Age

### 2. Population Age Pyramid
- Interactive visualization
- Separation by Male (blue) and Female (red)
- Hover for exact counts

### 3. Disease Prevalence
- CVD prevalence (%)
- Lung Cancer prevalence (%)

### 4. Risk Factor Impact
- Contribution of each RF to disease burden
- Relative impact visualization

### 5. Population Trends Over Time
- Year-by-year population changes
- Interactive line chart

### 6. Detailed Statistics Table
- Complete breakdown of results
- Multimorbidity rates
- Disease case counts

### 7. Risk Factor Settings Applied
- Summary of all RF multipliers used
- Effect indicators (🟢 Reduced, 🔴 Increased, ⚪ Baseline)

### 8. Export Options
- **Download Results (JSON)**: Save parameters and key results

---

## 📚 Understanding the Results

### Population Growth
```
Growth = (Final Population - Initial Population) / Initial Population × 100%
```
- **Positive**: Population growing
- **Negative**: Population shrinking (more deaths than births)
- **Healthy range**: -10% to +10% for stable population dynamics

### Survival Rate
```
Survival Rate = Final Population / Initial Population × 100%
```
- **90-100%**: Realistic for 50-year period
- **<80%**: High mortality (check multipliers)
- **>100%**: Growing population (check fertility)

### Disease Prevalence
Percentage of final population with:
- **CVD** (Cardiovascular Disease): Increases with risk factors
- **Lung Cancer**: Heavily influenced by smoking

### Risk Factor Impact
Relative contribution of each RF to total disease burden:
- Higher values = Greater disease impact
- Smoking typically has highest impact on Lung Cancer
- Hypertension typically highest for CVD

---

## 🔬 Example Scenarios

### Scenario 1: Smoking Reduction Campaign
```
All multipliers = 1.0 (baseline)
Except: Smoking = 0.5 (50% reduction)
Expected: Lung Cancer prevalence decreases significantly
```

### Scenario 2: Lifestyle Intervention
```
Smoking = 0.8
Obesity = 0.7
Physical Inactivity = 0.6
Cholesterol = 0.8
Hypertension = 0.7
Alcohol = 0.9
Family History = 1.0 (unchanged)
Expected: Overall disease burden reduced, population growth improved
```

### Scenario 3: High-Risk Population
```
All multipliers = 1.5-2.0
Expected: Higher disease prevalence, lower survival rates
```

---

## ⚙️ Technical Details

### Performance
- Simulation of 50,000 agents over 50 years
- Typically completes in 1-2 minutes
- Larger populations may take longer

### Model Features
- **Cox Proportional Hazards Model**: Disease onset based on RF combinations
- **Age-Dependent Risk**: Hazard increases exponentially with age
- **Disability Accumulation**: Multiple diseases increase mortality risk
- **Realistic Demographics**: Polish GUS demographic data

### Random Seed
- Fixed at seed=42 for reproducibility
- Same parameters = Same results

---

## 📖 Documentation

For detailed technical information about risk factors, see:
- `RISK_FACTORS_DOCUMENTATION.md` - Comprehensive RF implementation guide
- `README.md` - General simulation documentation

---

## 🐛 Troubleshooting

### App won't start
```bash
# Make sure all dependencies are installed
pip3 install -r requirements.txt

# Try running with verbose output
streamlit run interactive_simulation_app.py --logger.level=debug
```

### Simulation takes too long
- Reduce population size
- Reduce simulation years
- Check your system resources

### Results seem unrealistic
- Check multiplier values (should be 0.0-3.0)
- Verify fertility/mortality multipliers are reasonable
- Try a quick scenario preset first

### Browser won't open automatically
- Manually navigate to: `http://localhost:8501`
- Check terminal output for the correct port if different

---

## 📝 Saving Your Work

### Export Results
Click "📥 Download Results (JSON)" to save:
- All parameters used
- Key simulation results
- Timestamp

### Screenshot Recommendations
- **Population pyramid**: Use browser screenshot tool
- **Full results**: Screenshot entire dashboard
- **Comparisons**: Run multiple scenarios and screenshot each

---

## 🔗 Running Multiple Simulations

To compare different scenarios:

1. Run first simulation with parameters A
2. Screenshot/download results
3. Adjust parameters to scenario B
4. Run second simulation
5. Compare side-by-side

Streamlit will cache results for faster subsequent runs.

---

## 📧 Support

For questions about the simulation model:
- See `RISK_FACTORS_DOCUMENTATION.md` for RF details
- Check `simulation_engine.py` for implementation details
- Review `disease_model.py` for Cox model mathematics

---

**Version**: 1.0  
**Last Updated**: May 2026  
**Framework**: Streamlit 1.28+  
**Python**: 3.8+
