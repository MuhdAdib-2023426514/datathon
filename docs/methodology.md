# Methodological & Econometric Specification Manual
## Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

**Authoritative Standard**: Antigravity Data Science & Economics Team  
**Data Sources**: Department of Statistics Malaysia (DOSM) Tourism Satellite Account (TSA 2015–2025), Domestic Tourism Survey (DTS 2018–2025), Household Income & Expenditure Survey (HIES 2024), MOTAC Accommodation & Homestay Operations Registries (2016–2025).  
**Core Strategic Mandate**: *Scenario estimates, not causal forecasts. All models evaluate empirical associations, structural elasticity parameters, and capacity-constrained economic yield.*

---

## 1. Problem Statement: Volume vs. Economic Value

$$\text{Volume Expansion } (\text{More Visitors}) \longrightarrow \text{Value Capture } (\text{More Economic Value from Existing Visitors})$$

Following pandemic recovery, Malaysia reached **290.1 million domestic visitors** and **106.5 million overnight tourists** in 2025. However, destination states frequently experience a **"Volume-Rich, Value-Poor" trap**: heavy day-tripper vehicle traffic, shortening average length of stay (ALOS), and weak lodging capture.

The economic dimension of sustainable tourism (UN SDG 8.9 and 12.b) requires destinations to maximize domestic Gross Value Added (GVA) and economic yield per visitor-day while respecting destination physical carrying capacity.

---

## 2. National Accounting Decomposition (TSA & DTS)

### 2.1 Value-Added Intensity (VAI)
In strict compliance with the UN Tourism Satellite Account Recommended Methodological Framework (TSA:RMF 2008) and `AGENTS.md Section 3`:

$$\text{VAI}_{i,t} = \frac{\text{GVA}_{i,t}}{\text{DomesticSupply}_{i,t}}$$

- $\text{GVA}_{i,t}$: Gross Value Added of tourism industry $i$ in year $t$ at basic prices (RM Million).
- $\text{DomesticSupply}_{i,t}$: Total domestic supply/gross output of tourism product $i$ in year $t$ at basic prices (RM Million).
- **Interpretation**: The proportion of each industry's supply/output represented by Gross Value Added rather than intermediate consumption or imports.
- **Empirical Benchmark**: Accommodation services achieves a 2023–2025 post-recovery median of **$0.8579$** (85.79%, CV: 0.039), ranking #1 across characteristic tourism products.

### 2.2 Estimated Tourism-Attributable GVA (Analytical Proxy)
Per `AGENTS.md Section 3`, product-level gross value added cannot be labeled as official product-level TDGVA. It is formally designated as **Estimated Tourism-Attributable GVA** or **Tourism Value-Added Proxy**:

$$\text{EstimatedTourismGVA}_{i,t} = \text{ITC}_{i,t} \times \text{VAI}_{i,t} = \text{IndustryGVA}_{i,t} \times \text{TourismRatio}_{i,t}$$

*Guardrail*: Never multiply an attributable GVA proxy by the tourism ratio a second time.

### 2.3 Constant-Price Deflation (Real 2025 RM)
To remove pure price inflation across 2015–2025, nominal values are deflated to Constant 2025 RM using the official Consumer Price Index:

$$\text{RealExpenditure}_{s,t} = \text{NominalExpenditure}_{s,t} \times \left( \frac{\text{CPI}_{2025}}{\text{CPI}_{t}} \right)$$

---

## 3. State Productivity Metrics & 4-Quadrant Typology

### 3.1 Visitor-Days and Economic Yields
$$\text{VisitorDays}_s = \text{OvernightTourists}_s \times \text{ALOS}_s + \text{Excursionists}_s$$

$$\text{TourismEconomicYield (TEY)}_s = \frac{\text{TotalExpenditure}_s}{\text{VisitorDays}_s} \quad (\text{RM/day})$$

$$\text{TourismValueAddedYield (TVAY)}_s = \frac{\text{EstimatedTourismGVA}_s}{\text{VisitorDays}_s} \quad (\text{RM/day})$$

$$\text{TourismGVAIntensity}_s = \frac{\text{EstimatedTourismGVA}_s}{\text{MappedExpenditure}_s} \times 100\%$$

### 3.2 4-Quadrant State Typology
States are classified along two structural dimensions using national medians ($\text{ALOS} = 2.47 \text{ days}$, $\text{TVAY} = \text{RM } 78.40\text{/day}$):

1. **Short Stay / Low Yield**: Transit/day-trip destinations with low capture (e.g., Perlis, Kedah). Policy: Convert day trips to overnight stays, expand paid lodging.
2. **Short Stay / High Yield**: Premium transit hubs (e.g., Melaka, Pulau Pinang). Policy: Length-of-stay extension, off-peak dispersion.
3. **Long Stay / Low Yield**: Extended-stay high-VFR destinations (e.g., Kelantan, Terengganu). Policy: Commercial lodging conversion, boutique homestay certification.
4. **Long Stay / High Yield**: Core high-value capture destinations (e.g., W.P. Kuala Lumpur, Sabah). Policy: Capacity preservation, yield depth.

---

## 4. Econometric Panel Models of Accommodation Yield

To evaluate factors associated with real accommodation spending across 16 states over 2018–2025 ($N = 126$ state-years):

### 4.1 Two-Way Fixed Effects Model (State + Year, State-Clustered SEs)
$$\ln(\text{RealAccomSpend}_{st}) = \alpha_s + \lambda_t + \beta_1 \ln(\text{ALOS}_{st}) + \beta_2 \ln(\text{Tourists}_{st}) + \varepsilon_{st}$$

- **State-Clustered Standard Errors** (16 clusters): Accounts for within-state temporal persistence.
- Within-$R^2 = 0.9725$.
- **ALOS Elasticity $\hat{\beta}_1 = +0.6628$** ($SE = 0.3972, p = 0.0952, 95\% \text{ CI } [-0.1157, 1.4413]$).
- **Tourists Elasticity $\hat{\beta}_2 = +0.7327$** ($SE = 0.1168, p < 0.0001$).
- **Methodological & Non-Causal Interpretation**: Controlling for state fixed effects, year effects, and price inflation, ALOS retains a positive estimated association with real accommodation expenditure. The coefficient is approximately 0.66 and is statistically imprecise at the conventional 5% level ($p = 0.0952$). This is reported strictly as an observational relationship, not a causal guarantee.
- **Leave-One-State-Out Robustness**: Iterative re-estimation across 16 subsets confirms 16/16 sign stability ($\beta \in [+0.52, +0.81]$), indicating the positive association is structurally stable and not driven by any single state.

### 4.2 Accommodation Yield Model (Model 4)
$$\ln(\text{RealYieldPerNight}_{st}) = \alpha_s + \lambda_t + \gamma_1 \ln(\text{AOR}_{st}) + \gamma_2 \text{ForeignShare}_{st} + \gamma_3 \text{HolidayShare}_{st} + \varepsilon_{st}$$

- $R^2 = 0.8018$.
- AOR elasticity $\hat{\gamma}_1 = +0.2068$ ($SE = 0.1868, p = 0.2683$).
- Captures lodging yield responsiveness under tighter destination occupancy and leisure profiles.

---

## 5. Structural Spatial Gravity Model (PPML)

### 5.0 Observation Counts Disentangled
The empirical mobility network covers 16 Malaysian states across 8 years (2018–2025):
- **Total Bilateral Network**: $16 \text{ origins} \times 16 \text{ destinations} = 256 \text{ pairs} \times 8 \text{ years} = 2,048 \text{ panel observations}$.
- **Interstate Corridors**: $16 \text{ origins} \times 15 \text{ destinations} = 240 \text{ directed corridors} \times 8 \text{ years} = 1,920 \text{ corridor-years}$ ($1,680$ training observations across 2018–2024 and $240$ out-of-sample holdout observations for 2025).
- **Intrastate Pairs**: $16$ intra-state domestic pairs $\times 8 \text{ years} = 128 \text{ observations}$ (retained in general totals but excluded from inter-state corridor interventions).

### 5.1 PPML Specification (Santos Silva & Tenreyro 2006)
$$F_{od,t} = \exp\left( \alpha_o + \alpha_d + \lambda_t + \beta_1 \ln(\text{Distance}_{od}) + \beta_2 \text{CrossRegion}_{od} \right) \cdot \eta_{od,t}$$

- **Zero-Flow Robust**: Directly estimates in levels, avoiding Jensen's inequality and undefined $\ln(0)$.
- **Zero Target Leakage**: Destination visitor totals eliminated from right-hand predictors; absorbed non-parametrically via destination fixed effects $\alpha_d$.
- **Distance Decay Friction**: $\beta_1 = \mathbf{-0.4104}$ ($SE = 0.0517, p < 0.0001$). A 10% increase in distance reduces flow by 4.1%.
- **Cross-Region Flight Barrier**: $\beta_2 = \mathbf{-0.8022}$ ($SE = 0.1289, p < 0.0001$). Crossing between Peninsular Malaysia and Borneo imposes an additional 55.2% volume penalty.
- **Out-of-Sample Validation (2025 Holdout, $N=240$)**: True predictive $R^2_{OOS} = \mathbf{0.5890}$, correlation $r = 0.8759$, $\text{MAE} = 175.50\text{k}$.
- **Structural Invariance**: Interaction test $\ln(\text{Distance}) \times \text{PostRecovery}$ yields $\beta = +0.1023$ ($p = 0.1198$), which is not statistically significant at conventional thresholds ($\alpha = 0.05$). Distance sensitivity did not change materially post-COVID; spatial friction remains structurally invariant.

### 5.2 Dual Model Roles: Structural Benchmarking vs. Short-Term Forecasting
- **Structural Model (PPML Gravity)**: $R^2_{OOS} = 0.5890$ on 2025 holdout. Retained for structural corridor benchmarking, flow gap detection, and counterfactual policy simulation under capacity limits.
- **Short-Term Forecast Benchmark (Lagged Persistence)**: $R^2_{OOS} = 0.7637$ on 2025 holdout. Outperforms PPML for pure 1-step point forecasting due to year-over-year corridor inertia, but cannot evaluate counterfactual policy interventions.

---

## 6. Multi-Dimensional Opportunity Framework & Pareto Frontier

Corridor opportunities decouple statistical model residuals from strategic value:

1. **Structural Demand Gap**: $\text{FlowGap}_{od} = \max(0, \hat{F}_{od} - F_{od})$.
2. **Capacity Headroom**: $\text{Headroom}_d = 100\% - \text{AOR}_d$.
3. **Economic Yield**: Destination spend per night and TVAY.
4. **Feeder Diversification**: Inbound origin Herfindahl-Hirschman Index:
   $$\text{HHI}_d = \sum_{o \neq d} \left( \frac{F_{od}}{\sum_{k \neq d} F_{kd}} \times 100 \right)^2$$
5. **Pareto Frontier**: Corridors are evaluated across non-dominated objective fronts. Exactly **58 corridors** reside on Pareto Front 1, led by high-flow, high-yield, capacity-feasible pairs (e.g., Selangor $\rightarrow$ W.P. Kuala Lumpur, Negeri Sembilan $\rightarrow$ Melaka).

---

## 7. Capacity-Aware Scenario Simulator Engine

For any origin-destination pair or state portfolio:

$$\Delta \text{TouristNights}_{od} = F_{od} \times \text{AffectedShare} \times \Delta \text{ALOS}$$

$$\Delta \text{AccomSpend}_{od} = \Delta \text{TouristNights}_{od} \times \text{SpendPerNight}_d$$

$$\Delta \text{GVAProxy}_{od} = \Delta \text{AccomSpend}_{od} \times \text{VAI}_{\text{accom}} \quad (\text{VAI} = 0.8579)$$

### Physical Capacity Check:
$$\Delta \text{RequiredRooms}_{d} = \frac{\sum_o \Delta \text{TouristNights}_{od}}{365 \times \text{GuestsPerRoom}} \quad (\text{GuestsPerRoom} = 1.8)$$

$$\text{SimulatedAOR}_d = \text{BaselineAOR}_d + \left( \frac{\Delta \text{RequiredRooms}_d}{\text{AvailableHotelRooms}_d} \times 100\% \right)$$

Four saturation alert tiers: Optimal ($<70\%$), Moderate ($70\%-80\%$), High Saturation ($>80\%-100\%$), Severe Deficit ($>100\%$).

---

## 8. Uncertainty & Optimization

- **Monte Carlo Simulation (1,000 Draws)**: Quantifies outcome uncertainty across log-normal stay distributions, uniform campaign reach $[0.05, 0.25]$, and triangular yield variations, outputting P10–P90 confidence bounds and capacity breach probabilities.
- **MILP Portfolio Optimizer**: Solves a Mixed-Integer Linear Program to maximize total incremental GVA under fixed state promotional budgets and hotel room capacity constraints.

---

## 9. UN SDG Alignment

- **SDG Target 8.9**: Devise and implement policies to promote sustainable tourism that creates jobs and promotes local culture and products. Measured via TVAY per visitor-day, accommodation GVA capture, and homestay operations.
- **SDG Target 12.b**: Develop and implement tools to monitor sustainable development impacts for sustainable tourism. Implemented via the MYTourism Value Intelligence decision-support platform, multi-feeder saturation monitoring, and corridor concentration tracking.
