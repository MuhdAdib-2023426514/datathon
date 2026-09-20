# Methodological & Econometric Specification Manual
## Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

**Project Lead / Authoritative Standard**: Antigravity Data Science & Economics Team  
**Data Sources**: Department of Statistics Malaysia (DOSM) Tourism Satellite Account (TSA 2015–2025), Domestic Tourism Survey (DTS 2018–2025), Household Income & Expenditure Survey (HIES 2024), MOTAC Accommodation & Homestay Capacity Registries.  
**Mandatory Guardrail**: *Scenario estimates, not causal forecasts. All models evaluate empirical associations and structural elasticity parameters.*

---

## 1. Non-Negotiable National Accounting Definitions

### 1.1 Value-Added Intensity (VAI)
In strict compliance with the UN Tourism Satellite Account Recommended Methodological Framework (TSA:RMF 2008) and `AGENTS.md Section 3`:

$$\text{VAI}_{i,t} = \frac{\text{GVA}_{i,t}}{\text{DomesticSupply}_{i,t}}$$

- $\text{GVA}_{i,t}$: Gross Value Added of tourism industry $i$ in year $t$ at basic prices (RM Million).
- $\text{DomesticSupply}_{i,t}$: Total domestic supply/gross output of tourism product $i$ in year $t$ at basic prices (RM Million).
- **Interpretation**: The proportion of each industry's gross output represented by direct value added rather than intermediate consumption or imports. VAI serves as the primary metric of domestic value efficiency.
- **Empirical TSA Benchmark (2025)**: Accommodation services achieves **$\text{VAI} = 0.8659$** (86.59%), with a 2023–2025 post-recovery median of **$0.8579$** (85.79%), ranking #1 across all 8 characteristic tourism products.

### 1.2 Tourism Ratio ($TR$)
The share of domestic supply absorbed by internal tourism visitors:

$$TR_{i,t} = \frac{\text{ITC}_{i,t}}{\text{DomesticSupply}_{i,t}}$$

- Under Malaysian official TSA practice, tourism consumption is evaluated at purchaser prices while supply is at basic prices (incorporating net taxes on products and trade/transport margins).
- For accommodation services, $TR_{2025} = 0.967$ (96.7% visitor absorption).

### 1.3 Estimated Tourism-Attributable GVA (Value-Added Proxy)
As mandated by `AGENTS.md Section 3`, product-level gross value added cannot be labeled as official product-level TDGVA. It is formally designated as **Estimated Tourism-Attributable GVA** or **Tourism Value-Added Proxy**:

$$\text{EstimatedTourismGVA}_{i,t} = \text{ITC}_{i,t} \times \text{VAI}_{i,t} = \text{IndustryGVA}_{i,t} \times TR_{i,t}$$

*Guardrail Rule*: Never multiply an attributable GVA proxy by the tourism ratio a second time.

---

## 2. UN Sustainable Development Goal Metrics (SDG 8.9 & 12.b)

### 2.1 Destination Value Retention (DVR)
Destination Value Retention evaluates the proportion of gross visitor receipts retained within local production:

$$\text{DVR}_s = \frac{\sum_{i \in \text{Core}} \left(\text{Expenditure}_{s,i} \times \text{VAI}_i\right)}{\text{TotalDomesticExpenditure}_s}$$

Core tourism activities include:
1. Accommodation ($\text{VAI}_{2025} = 0.858$)
2. Food & Beverage ($\text{VAI}_{2025} = 0.655$)
3. Passenger Transport ($\text{VAI}_{2025} = 0.407$)
4. Shopping & Retail Margin ($\text{VAI}_{2025} = 0.470$)
5. Recreation & Cultural Services ($\text{VAI}_{2025} = 0.604$)

*Correction Note (Review Finding 1)*: Operator precedence in prior code erroneously omitted accommodation receipts. In the corrected formulation, Kuala Lumpur's 2025 Attributable GVA equals **RM 10,406.6M** (DVR = **61.6%**), accurately reflecting RM 1,669.1M in direct accommodation value added.

### 2.2 Excursionist Pressure Ratio (EPR) & Tourism Intensity Ratio (TIR)
$$\text{EPR}_s = \frac{\text{Excursionists (Day-Trippers)}_s}{\text{Overnight Tourists}_s}$$

$$\text{TIR}_s = \frac{\text{Total Domestic Visitors}_s}{\text{Resident Population}_s}$$

- High EPR ($> 1.5$) denotes volume transit destinations (e.g. Melaka, Negeri Sembilan) vulnerable to local infrastructure wear without overnight economic yield.

---

## 3. Econometric Panel Models of Accommodation Yield (RQ3 & RQ4)

To evaluate what factors are associated with higher accommodation spending per tourist across 16 Malaysian states over 2018–2025 ($N = 126$ balanced state-year panel), two econometric specifications are estimated.

### 3.1 Model 1: One-Way State Fixed Effects
$$\ln(\text{SpendPerTourist}_{st}) = \alpha_s + \beta_1 \ln(\text{ALOS}_{st}) + \beta_2 \text{LuxuryShare}_{st} + \beta_3 \ln(\text{ResidentIncome}_{st}) + \beta_4 \text{VFRShare}_{st} + \varepsilon_{st}$$

- Within-$R^2$: $0.6865$
- ALOS Coefficient $\hat{\beta}_1 = +1.6067$ ($p < 0.0001$)
- *Limitation*: Omits macroeconomic aggregate shocks (e.g. 2020 COVID contraction and 2022–2023 recovery border re-openings), capturing cross-period trending.

### 3.2 Model 2: Two-Way Fixed Effects (State + Year, Clustered Standard Errors)
$$\ln(\text{SpendPerTourist}_{st}) = \alpha_s + \lambda_t + \beta_1 \ln(\text{ALOS}_{st}) + \beta_2 \text{LuxuryShare}_{st} + \beta_3 \ln(\text{ResidentIncome}_{st}) + \beta_4 \text{VFRShare}_{st} + \varepsilon_{st}$$

- **State-Clustered Standard Errors** (Arellano robust covariance):
  $$\text{Var}(\hat{\beta}) = (X'X)^{-1} \left( \sum_{s=1}^{16} X_s' e_s e_s' X_s \right) (X'X)^{-1}$$
- Within-$R^2$: $0.6517$ | Overall $R^2$: $0.5750$
- **ALOS Coefficient $\hat{\beta}_1 = +0.6628$** ($SE = 0.3972$, $t = 1.6687$, $p = 0.0952$, $95\% \text{ CI } [-0.1157, 1.4413]$).
- **Substantive Finding**: Controlling for national inflation and post-pandemic recovery surges via year dummies $\lambda_t$, the isolated intra-state elasticity of spend per tourist with respect to length of stay is $+0.66$ (positive and marginally significant at $\alpha = 0.10$). Both models are reported side-by-side to ensure academic honesty.

---

## 4. Spatial Econometrics: Tinbergen Gravity Model (RQ6)

The volume of tourist flow from origin state $o$ to destination state $d$ ($F_{od}$) is modeled across 240 bilateral interstate corridors ($1,890$ panel observations across 2018–2025).

### 4.1 Structural Log-Normal OLS Specification
$$\ln(F_{od,t}) = \beta_0 + \beta_1 \ln(\text{AdultPop}_{o,t}) + \beta_2 \ln(\text{Income}_{o,t}) + \beta_3 \ln(\text{Attraction}_{d,t}) - \beta_4 \ln(\text{Distance}_{od}) - \beta_5 \text{CrossRegion}_{od} + \varepsilon_{od,t}$$

- **Parameter Estimates**:
  - Outbound Demographic Mass $\beta_1 = +0.8904$ ($p < 0.0001$)
  - Origin Income Elasticity $\beta_2 = +0.7252$ ($p < 0.0001$)
  - Destination Economic Pull $\beta_3 = +0.7042$ ($p < 0.0001$)
  - Distance Friction Elasticity $\beta_4 = -0.6031$ ($p < 0.0001$)
  - Borneo Cross-Region Air Barrier $\beta_5 = -1.3323$ ($\exp(-1.3323) - 1 = -73.6\%$ volume penalty)
- **Predictive Performance on 2025 Holdout ($N = 240$)**:
  - In logarithmic space: $R^2 = 0.7092$
  - In original levels space ($\text{Predictive } R^2 = 1 - \frac{\text{SSE}}{\text{SST}}$): **$R^2 = 0.4863$**
  - Pearson correlation $r = 0.7672$ ($r^2 = 0.5886$)
  - Actual Observations: $N = 1,650$ panel rows with complete predictors (1,890 total with holdouts).

### 4.2 Poisson Pseudo-Maximum Likelihood (PPML) Gravity
Following Silva & Tenreyro (2006), PPML addresses heteroskedastic log errors in levels:

$$E[F_{od,t} \mid X_{od,t}] = \exp\left( X_{od,t} \beta \right)$$

- First-order condition: $\sum_{od,t} \left[ F_{od,t} - \exp(X_{od,t}\beta) \right] X_{od,t} = 0$
- **PPML Parameter Estimates**:
  - Distance Elasticity $\beta_4 = -0.4648$ ($SE = 0.0381, p < 0.0001$)
  - Out-of-Sample Predictive $R^2 = 0.5177$ (exceeding Log-OLS in levels)
  - Correlation in levels: $r = 0.8120$

---

## 5. Market Concentration: Herfindahl-Hirschman Index (HHI)

To measure destination inbound market fragility without conflating domestic regional residents with external interstate feeders, two distinct indices are computed:

### 5.1 Interstate Origin HHI
$$\text{HHI}_{d,t}^{\text{interstate}} = \sum_{o \neq d} \left( \frac{F_{od,t}}{\sum_{k \neq d} F_{kd,t}} \times 100 \right)^2$$

### 5.2 All-Origin HHI (including Intrastate)
$$\text{HHI}_{d,t}^{\text{all}} = \sum_{\text{all } o} \left( \frac{F_{od,t}}{\text{TotalTourists}_{d,t}} \times 100 \right)^2$$

- **Empirical Separation (Finding 8)**:
  - Sabah 2025: $75.22\%$ of domestic tourists are Sabah residents traveling within Sabah ($F_{\text{intrastate}} = 5,536\text{k}$). Consequently, $\text{HHI}^{\text{all}} = 5,746.95$, while its **Interstate Feeder HHI is $1,449.92$** (Diversified $< 1,500$).
  - Melaka 2025: $97.92\%$ of tourists originate interstate, yielding $\text{HHI}^{\text{interstate}} = 2,156.40$ and $\text{HHI}^{\text{all}} = 2,072.00$ (Moderately Concentrated, led by Selangor at $38.78\%$).

---

## 6. Transparent Scenario Simulation & Capacity Feasibility Engine

### 6.1 Decoupled Corridor vs. Destination Simulation
1. **Corridor Stay Extension (Bilateral Level)**:
   $$\Delta \text{TouristNights}_{od} = F_{od} \times \Delta \text{ALOS}$$
   $$\Delta \text{AccomSpend}_{od} = \Delta \text{TouristNights}_{od} \times \text{SpendPerNight}_d$$

2. **Excursionist Day-Trip Conversion (Destination Pool Level)**:
   $$\Delta \text{Tourists}_{d}^{\text{conv}} = \text{Excursionists}_d \times \text{ConversionRate}$$
   $$\Delta \text{TouristNights}_{d}^{\text{conv}} = \Delta \text{Tourists}_{d}^{\text{conv}} \times (\text{ALOS}_d + \Delta \text{ALOS})$$

3. **Potential Attributable TDGVA Proxy**:
   $$\Delta \text{GVAProxy} = \Delta \text{AccomSpend} \times \text{VAI}_{\text{accom}} \quad (\text{VAI} = 0.858)$$

### 6.2 Portfolio Multi-Corridor Saturation Model
When targeting multiple feeder origins simultaneously for destination state $d$:

$$\text{TotalSimulatedNights}_d = \text{BaselineTourists}_d \times \text{BaselineALOS}_d + \sum_{o \in \text{Target}} \Delta \text{TouristNights}_{od} + \Delta \text{TouristNights}_{d}^{\text{conv}}$$

$$\text{SimulatedAOR}_d = \frac{\text{TotalSimulatedNights}_d}{\text{HotelRooms}_d \times 365 \times \text{GuestsPerRoom}} \times 100$$

- Defaults: $\text{GuestsPerRoom} = 1.75$ (MOTAC standard).
- **Four-Tier Capacity Saturation Thresholds**:
  1. **Optimal** ($\text{AOR} < 70\%$): Sufficient room inventory to absorb simulated growth.
  2. **Moderate Saturation** ($70\% \le \text{AOR} < 80\%$): Approaching operational friction during peak periods.
  3. **High Saturation** ($80\% \le \text{AOR} \le 100\%$): Severe supply constraint; requires accommodation capacity expansion.
  4. **Severe Deficit** ($\text{AOR} > 100\%$): Room inventory physically exceeded under scenario demand.
- **Pahang Empirical Verification (Finding 7)**: Expanding all 15 feeders by $+0.5$ days increases Pahang's required room-nights from $16.96\text{M}$ to $20.93\text{M}$, driving simulated AOR from $76.3\%$ to **$95.0\%$**, triggering a High Saturation alert.
