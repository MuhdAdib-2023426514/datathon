# Competition Defense & The Five Judge Questions

**Repository**: `Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)`  
**Authors**: purpleX  
**Reference Period**: 2015–2025 (Annual Accounts) & 2018–2025 (State Panel)  
**Authoritative Specifications**: [AGENTS.md](file:///home/muhammad_adib/dosm/AGENTS.md), [IMPLEMENTATION_PLAN.md](file:///home/muhammad_adib/dosm/IMPLEMENTATION_PLAN.md), and [methodology.md](file:///home/muhammad_adib/dosm/docs/methodology.md)

---

## Executive Summary & North-Star Principle

MYTourism Value Intelligence is designed to answer a single strategic shift for Malaysian tourism:

$$\boxed{\text{Do not only maximize tourists. Maximize sustainable domestic economic value per visitor-day.}}$$

This document directly addresses the five core questions that competition judges, policymakers, and senior economists will ask when evaluating this platform.

---

## Judge Question 1: Where did this number come from?

> *Show source, formula, status, and reconciliation.*

Every figure displayed in the platform is traceable through an unbroken cryptographic audit trail from official Malaysian government publications to the dashboard interface.

### 1. Primary Official Data Sources
All underlying figures originate from official Malaysian agencies, cryptographically verified with SHA-256 hashes in [data/metadata/source_registry.yaml](file:///home/muhammad_adib/dosm/data/metadata/source_registry.yaml):
1. **Tourism Satellite Account (TSA) 2015–2025p (DOSM)**: Internal Tourism Consumption (ITC, Jadual 4), Production Accounts/GVA (Jadual 5), Domestic Supply and Tourism Ratios (Jadual 6), Macro Aggregates (Jadual 1). SHA-256: `d33836e9e6ebc8e4d520313af376ec7016d82e68d6af217ba971fb854a4a7b63`.
2. **Domestic Tourism Survey (DTS) 2025 (DOSM)**: Visitors, tourists, trips, expenditure components, and ALOS across 16 states (Jadual 1, 8, 11, 12, 13a, 14, 15). SHA-256: `c9fe28d1c516e58e6a79bfefa2ff53ddcfef109511c8c8dbe117a7bf87d04c96`.
3. **DTS Longitudinal State & OD Panel 2018–2025 (DOSM)**: 126 state-year observations and 1,650 observed directional corridor movements.
4. **MOTAC Operational Indicators & Hotel Statistics 2016–2025**: Average Occupancy Rates (AOR %), registered hotel rooms, and homestay indicators across all 16 states. SHA-256: `ee4d81aea36d9b0654f20d85fc9c8f072eba3a3b40d1dab03ab591ec9330c448`.
5. **Consumer Price Index (CPI) 2015–2025 (DOSM)**: Used for Constant 2025 RM deflation ($2025 = 134.6$). SHA-256: `c9b4becce2f9aaf36cd07383fd2759ef95ba4ca33798063679bdd104e651e747`.

### 2. Core Mathematical Formulas
* **Value-Added Intensity (VAI)**:
  $$\text{VAI}_{i,t} = \frac{\text{GVA}_{i,t}}{\text{DomesticSupply}_{i,t}}$$
  *Strictly bounded in $[0, 1]$ across structural periods.*
* **Tourism Value-Added Yield (TVAY)**:
  $$\text{TVAY}_{s,t} = \frac{\sum_i \text{Expenditure}_{s,i,t} \times \text{VAI}_{i,t}}{\text{VisitorDays}_{s,t}}$$
* **Estimated Tourism-Attributable GVA Proxy**:
  $$\text{EstimatedTourismGVA}_{i,t} = \text{ITC}_{i,t} \times \text{VAI}_{i,t}$$
  *(Never labeled as official product TDGVA, per AGENTS.md Section 3).*
* **Herfindahl-Hirschman Index (HHI)**:
  $$\text{HHI}_d = \sum_{o \neq d} \left( \frac{\text{Flow}_{o,d}}{\sum_{k} \text{Flow}_{k,d}} \times 100 \right)^2$$

### 3. Data Status & Missing Value Semantics
* Status flags (`actual`, `preliminary`, `estimate`, `model_estimate`, `scenario_assumption`) are maintained for all data rows.
* Missing values strictly propagate as `np.nan` / `null`. Zero empirical fabrication is allowed.

---

## Judge Question 2: Why do you believe this relationship?

> *Show model specification, diagnostics, robustness, and limitations.*

We employ transparent, small-sample-appropriate econometric specifications rather than black-box machine learning.

### 1. State Panel Econometrics (Two-Way Fixed Effects)
To evaluate the factors associated with accommodation expenditure per tourist, we estimate:

$$\ln(\text{AccomSpendPerTourist}_{s,t}) = \beta_1 \ln(\text{ALOS}_{s,t}) + \beta_2 \ln(\text{Tourists}_{s,t}) + \alpha_s + \gamma_t + \varepsilon_{s,t}$$

* **Empirical Results (Model 2, Two-Way FE with 16 State Clusters)**:
  - $\beta_1 (\ln(\text{ALOS})) = +0.6628$ ($p = 0.0007$, $t = 3.41$): A 10% increase in length of stay is associated with a 6.63% increase in accommodation expenditure per tourist.
  - $\beta_2 (\ln(\text{Tourists})) = +0.7327$ ($p = 0.0016$, $t = 3.16$): Volume growth exhibits scale elasticity.
  - Overall Within-$R^2 = 0.6974$.
* **Yield-Focused Model (Model 4)**:
  - Adding capacity occupancy ($\ln(\text{AOR})$), foreign guest share, and public holiday share achieves $R^2 = 0.8018$.
  - $\beta_{\text{AOR}} = +0.2068$ ($p = 0.0416$): Higher hotel occupancy is significantly associated with higher lodging yield.

### 2. Robustness & Sensitivity Checks
* **Leave-One-State-Out Cross Validation**:
  - Re-estimating the Two-Way FE model dropping one state at a time ($N = 15$) yields positive, statistically significant coefficients in **16 out of 16 iterations** ($\beta_1 \in [0.4901, 0.7712]$).
  - Demonstrates that the positive relationship between ALOS and lodging expenditure is a structural characteristic of the Malaysian domestic economy, not an artifact of a single outlier state like Sabah or W.P. Kuala Lumpur.
* **Influence Diagnostics**: Cook's distance values remain well below the threshold of $4/N = 0.25$, confirming absence of highly leveraged distortive observations.
* **Non-Causal Guardrail**: Relationships are reported strictly as *statistical associations*, recognizing that length of stay is endogenous to destination characteristics.

---

## Judge Question 3: Why should this corridor be targeted?

> *Show flow gap, value yield, capacity headroom, and market evidence.*

Corridor targeting is determined through a structural **Poisson Pseudo-Maximum Likelihood (PPML) Gravity Model** combined with **Pareto Non-Domination Multi-Objective Optimization**.

### 1. PPML Structural Gravity Specification
To estimate expected tourist mobility between Malaysian states without Jensen's inequality bias or zero-flow distortion:

$$\text{Flow}_{o,d,t} = \exp\left( \beta_0 + \beta_{\text{dist}} \ln(\text{Distance}_{o,d}) + \beta_{\text{cross}} \text{CrossRegion}_{o,d} + \theta_o + \mu_d + \tau_t \right) + \eta_{o,d,t}$$

* **Gravity Parameters**:
  - Distance decay friction: $\beta_{\text{dist}} = -0.4104$ ($p < 0.0001$): Flow drops systematically with centroid distance.
  - Cross-region flight barrier (Peninsula $\leftrightarrow$ Borneo): $\beta_{\text{cross}} = -0.8022$ ($p < 0.0001$): Crossing the South China Sea reduces flow by $55.2\%$.
* **Out-of-Sample Holdout Validation**:
  - Validated using a strict temporal holdout (training on 2018–2024, testing on unobserved 2025): $R^2_{OOS} = 0.5890$.
  - Benchmarked against naive persistence ($R^2 = 0.7637$) and historical mean ($R^2 = 0.6732$). PPML is retained because autoregressive persistence cannot evaluate counterfactual policy interventions.

### 2. The 5-Objective Pareto Frontier
Rather than ranking corridors by arbitrary weighted scores or hypothetical spend assumptions, we evaluate corridors across 5 fundamental objectives:
1. **$O_1$ Structural Demand Gap**: $\max(0, \text{ExpectedFlow}_{o,d} - \text{ActualFlow}_{o,d})$ (unrealized gravity potential).
2. **$O_2$ Economic Yield (TVAY)**: RM Value-Added Yield per visitor-day at destination.
3. **$O_3$ Destination Capacity Headroom**: $100\% - \text{AOR}_d$ (available room buffer).
4. **$O_4$ Feeder Market Diversification**: Destination origin HHI (reducing vulnerability to single feeders).
5. **$O_5$ Spatial Accessibility**: Normalized inverse travel friction.

* **Result**: Exactly **58 non-dominated Pareto Front 1 corridors** are identified nationwide. Corridors on Front 1 cannot be improved along any objective without worsening another.
* **Target Priority Example**: **Selangor $\rightarrow$ Melaka** (2.73M tourists, ALOS 2.11d vs national median 2.47d, lodging spend RM 63.00/night) represents an ideal stay-extension priority because it combines massive feeder volume with below-median stay duration.

---

## Judge Question 4: What happens if your assumptions are wrong?

> *Show sensitivity, uncertainty, and physical constraints.*

All policy projections incorporate explicit uncertainty boundaries and physical hotel capacity constraints.

### 1. Monte Carlo Stochastic Uncertainty (1,000 Draws)
Instead of deterministic single-point projections, policy simulations model parameters as joint random variables:
* $\Delta \text{ALOS} \sim \text{TruncatedNormal}(\mu_{\text{ALOS}}, \sigma = 0.15 \mu)$
* $\text{SpendPerNight} \sim \text{Lognormal}(\mu_{\text{Spend}}, \sigma = 0.10 \mu)$
* $\text{VAI} \sim \text{Beta}(\alpha, \beta)$ parameterized around official TSA standard errors.

The engine reports **P10 (conservative)**, **P50 (median)**, and **P90 (optimistic)** percentiles. For a +0.4-day stay extension on Selangor $\rightarrow$ Melaka (15% campaign reach):
* P10 Potential GVA: **RM 11.2M**
* P50 Potential GVA: **RM 15.4M**
* P90 Potential GVA: **RM 20.1M**

### 2. Destination Carrying Capacity & Room Constraints
Every intervention translates additional tourist nights into physical daily hotel room demand:

$$\text{DailyRoomsDemanded} = \frac{\Delta \text{Nights}}{365 \times \text{GuestDensity}} \quad (\text{Default: } 1.8 \text{ guests/room})$$

$$\text{ProjectedAOR}_d = \text{BaselineAOR}_d + \left( \frac{\text{DailyRoomsDemanded}}{\text{AvailableRooms}_d} \times 100 \right)$$

If $\text{ProjectedAOR}_d > 80.0\%$ (Planning Ceiling), the dashboard issues a **Capacity Saturation Warning** and calculates the probability of physical capacity breach via Monte Carlo simulation.

---

## Judge Question 5: How would a real organization use this?

> *Show the implementation and decision workflow.*

MYTourism Value Intelligence is structured around a closed-loop institutional decision cycle across five stakeholder tiers.

### 1. Institutional Governance Matrix
| Stakeholder | Core Operational Decision | Platform Touchpoint |
| :--- | :--- | :--- |
| **MOTAC** | National budget allocation across states & tourism products | *Portfolio Optimizer (MILP) & TSA Value Monitor* |
| **Tourism Malaysia** | Domestic feeder-market campaign targeting & staycation vouchers | *Value Corridors & Pareto Frontier* |
| **State Tourism Action Councils** | State tourism master plans, length-of-stay & yield targets | *States & Stays Map & Decision Summaries* |
| **Local Authorities (PBTs)** | Destination carrying capacity, infrastructure & room caps | *Capacity Headroom & SDG 12.b Indicators* |
| **Hotel Associations (MAH/MyBHA)** | Joint mid-week promotional packages & homestay integration | *Scenario Simulator & VFR Conversion Lab* |

### 2. Closed-Loop Operating Model
```text
  [1. Official Data]  --> DOSM TSA, DTS, MOTAC KPI annual releases
         ↓
  [2. Economic Diagnosis] --> Identify states with short stays / low yield
         ↓
  [3. Opportunity Detection] --> Screen 58 Pareto-optimal feeder corridors
         ↓
  [4. Scenario Testing] --> Test stay-extension (+0.3d) under 80% AOR ceiling
         ↓
  [5. Portfolio Optimization] --> Allocate RM 5.0M budget via MILP (28.1x benchmark)
         ↓
  [6. Pilot Implementation] --> Tourism Malaysia co-funded digital campaigns
         ↓
  [7. Observed Outcomes] --> Post-campaign DTS survey wave & hotel guest counts
         ↓
  [8. Model Recalibration] --> Update gravity elasticities and state panel FE
```

### 3. Concrete Strategic Takeaway
* **The Strategic Shift**: Stop spending public marketing funds promoting mass excursionist weekend day-trips that saturate highways and generate negligible accommodation GVA.
* **The High-Yield Solution**: Deploy targeted staycation vouchers and cultural night passes along high-flow, short-stay corridors (e.g. Selangor $\rightarrow$ Melaka, Johor $\rightarrow$ Melaka) to convert day-trips into overnight stays, capturing Malaysia's highest-intensity tourism product: **Accommodation Services (85.8% VAI)**.
