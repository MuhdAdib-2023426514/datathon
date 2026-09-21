# Executive Presentation Deck: MYTourism Value Intelligence

**Competition**: Malaysia Tourism Datathon 2026  
**Platform**: MYTourism Value Intelligence (Malaysia Tourism Value Optimizer)  
**Authors**: purpleX  
**Audience**: Panel of Judges, MOTAC Leadership, Tourism Malaysia Executives, Senior Economists  
**Core Thesis**: *From More Tourists to More Value — Maximizing Sustainable Domestic Economic Value per Visitor-Day*

---

## Slide 1: The Macro Context — Volume Recovery vs. Value Generation

### Headline: Malaysia Has Recovered Tourist Volume; The Challenge is Value Capture

```text
       2019 (Pre-COVID Peak)       2020 (MCO Disruption)       2025 (Full Post-Recovery)
       ─────────────────────       ─────────────────────       ─────────────────────────
Tourists:    84.8 Million               41.7 Million               106.5 Million (+25.6%)
Expenditure: RM 103.3 Billion           RM 40.4 Billion            RM 112.8 Billion (+9.2%)
Real Yield:  RM 121.8 / day             RM 96.8 / day              RM 105.9 / day (-13.0%)
```

* **The Paradox of Recovery**: Total domestic tourist volume in 2025 has surpassed pre-pandemic records (106.5M overnight tourists, +25.6% vs 2019), yet real economic yield per visitor-day has lagged behind inflation-adjusted historical benchmarks.
* **The Structural Risk**: Pursuing unconstrained volume expansion without stay extension creates acute physical congestion, saturates weekend transport corridors, and strains municipal infrastructure without generating proportional local Gross Value Added (GVA).
* **Strategic Imperative**: Malaysia needs an analytical decision-support system to shift policy from *mass visitor volume* to *high-value visitor-days*.

---

## Slide 2: The Core Strategic Shift — From Volume to Value

### Headline: The Economic Dimension of Sustainable Tourism (UN SDG 8.9 & 12.b)

$$\boxed{
\begin{aligned}
\text{\bf Legacy Approach:} &\quad \text{Maximize Tourist Arrivals} \implies \text{Overcrowding, Short Stays, Low Margin} \\
\text{\bf Strategic Shift:} &\quad \text{Maximize Value per Visitor-Day} \implies \text{Longer Stays, High VAI, Capacity Headroom}
\end{aligned}
}$$

* **North-Star KPI**: **Tourism Value-Added Yield (TVAY)** per visitor-day:
  $$\text{TVAY}_{s,t} = \frac{\sum_i \text{Expenditure}_{s,i,t} \times \text{VAI}_{i,t}}{\text{VisitorDays}_{s,t}}$$
* **Core Accounting Lever**:
  $$\text{Accommodation Expenditure} \approx \text{Overnight Tourists} \times \text{ALOS} \times \text{Spend per Night}$$
* **Policy Levers Evaluated**:
  1. *Day-trip to overnight stay conversion* (capturing accommodation GVA).
  2. *Short stay to extended stay* (increasing ALOS from 2.1d to 2.5d+).
  3. *Unpaid VFR conversion* (transitioning informal visits into licensed boutique homestays).

---

## Slide 3: TSA Macro Accounting — Accommodation as Malaysia's #1 Value Engine

### Headline: Not All Tourism Products Create Equal Economic Value

```text
Product Activity                       Post-Recovery Median VAI    2025p VAI    Strategic Quadrant
────────────────────────────────────   ────────────────────────    ─────────    ──────────────────
1. Accommodation Services                      85.8%                 86.6%      High-Value Core Activity
2. Food & Beverage Serving Services            65.5%                 66.1%      High-Value Core Activity
3. Recreation & Cultural Services              60.4%                 61.2%      Growth Opportunity
4. Shopping (Retail Margin Share)              47.0%                 47.3%      Efficiency Priority
5. Passenger Transport Services                40.7%                 41.0%      Efficiency Priority
6. Travel Agencies & Reservation               28.5%                 28.8%      High Turnover / Low Margin
```

* **Why Accommodation Wins**: Gross Value Added represents **85.8%** of total domestic supply in Accommodation Services, because lodging operations rely primarily on domestic labor, local capital assets, and domestic real estate rather than imported intermediate inputs.
* **The Retail Margin Reality**: In contrast, Shopping generates only **47.0%** value-added intensity on retail margin (and <24% on gross shelf turnover), because intermediate acquisition costs absorb over 76% of retail revenue.
* **Policy Action**: Public promotional incentives must prioritize overnight lodging and cultural immersion over general retail discount subsidies.

---

## Slide 4: State Economic Productivity — The 4-Quadrant Typology

### Headline: Wide Divergence in State Economic Yield and Length of Stay

```text
                      HIGH YIELD (TVAY > National Median RM 48.2 / day)
                                     │
               Quadrant II           │            Quadrant I
           [Short Stay / High Yield] │       [Long Stay / High Yield]
           • Melaka (2.11d, RM 63.0) │       • Pulau Pinang (2.58d, RM 72.4)
           • Selangor (1.82d, RM 54) │       • W.P. Kuala Lumpur (2.61d, RM 81)
                                     │       • Sabah (2.84d, RM 78.5)
      ───────────────────────────────┼───────────────────────────────
               Quadrant IV           │            Quadrant III
           [Short Stay / Low Yield]  │       [Long Stay / Low Yield]
           • Negeri Sembilan (1.95d) │       • Kelantan (2.76d, RM 32.1)
           • Perlis (1.88d, RM 38.2) │       • Terengganu (2.64d, RM 39.4)
           • Kedah (2.15d, RM 42.1)  │       • Pahang (2.52d, RM 44.8)
                                     │
                       LOW YIELD (TVAY < National Median RM 48.2 / day)
```

* **The Melaka Syndrome (Quadrant II)**: Melaka captures high lodging spend per night (RM 63.00), but suffers from an Average Length of Stay of only **2.11 days** (below national median of 2.47 days). High visitor volume creates weekend congestion without maximizing economic stay potential.
* **The East Coast Opportunity (Quadrant III)**: Kelantan and Terengganu enjoy extended stays (2.76d and 2.64d), but suffer from low lodging expenditure due to high shares of unpaid Visiting Friends & Relatives (VFR) stays (>65%).

---

## Slide 5: The Econometric Engine — Factors Associated with Lodging Spend

### Headline: Panel Econometric Models with Two-Way Fixed Effects & Clustered Inference

$$\ln(\text{AccomSpendPerTourist}_{s,t}) = \beta_1 \ln(\text{ALOS}_{s,t}) + \beta_2 \ln(\text{Tourists}_{s,t}) + \alpha_s + \gamma_t + \varepsilon_{s,t}$$

```text
Model Specification        ln(ALOS) Elasticity    ln(Tourists)    ln(AOR)    Within R²    Clusters
───────────────────────    ───────────────────    ────────────    ───────    ─────────    ────────
Model 1: Pooled OLS         +0.5841 (p=0.002)      +0.6214          —          0.6210        16
Model 2: Two-Way FE         +0.6628 (p=0.0007)     +0.7327          —          0.6974        16
Model 4: Yield-Focused      +0.6104 (p=0.0012)     +0.6842        +0.2068      0.8018        16
```

* **Statistically Defensible Findings**:
  - **ALOS Elasticity (+0.6628, t = 3.41, p < 0.001)**: A 10% increase in length of stay is systematically associated with a 6.63% increase in accommodation spending per tourist.
  - **Occupancy Responsiveness (+0.2068, p = 0.0416)**: Tighter hotel capacity is positively associated with higher room yield.
* **16/16 Leave-One-State-Out Stability**: Re-estimating across 16 jackknife iterations confirms positive, statistically significant coefficients ($\beta_1 \in [0.4901, 0.7712]$) across all iterations, proving structural robustness.

---

## Slide 6: Spatial Mobility & PPML Gravity Modeling

### Headline: Accounting for Spatial Friction, Border Barriers, and Structural Zeros

$$\text{Flow}_{o,d,t} = \exp\left( \beta_0 + \beta_{\text{dist}} \ln(\text{Distance}_{o,d}) + \beta_{\text{cross}} \text{CrossRegion}_{o,d} + \theta_o + \mu_d + \tau_t \right) + \eta_{o,d,t}$$

```text
Gravity Model Parameter                               Coefficient    Std. Error    p-value
───────────────────────────────────────────────────   ───────────    ──────────    ───────
Distance Decay Friction (ln Distance km)                -0.4104        0.0241      <0.0001
Cross-Region Flight Barrier (Peninsula <-> Borneo)      -0.8022        0.0512      <0.0001
Temporal Holdout Out-of-Sample Predictive R² (2025)     0.5890         (Strict holdout test)
```

* **Why PPML**: Poisson Pseudo-Maximum Likelihood eliminates Jensen's inequality bias, correctly estimates log-linearized spatial friction, and naturally accommodates observed zero-flow corridors without arbitrary $y + 1$ transformations.
* **Temporal Holdout Validation**: Trained strictly on 2018–2024, the structural gravity model achieves an Out-of-Sample $R^2_{OOS} = 0.5890$ on the unobserved 2025 cross-section.
* **Structural Break Finding**: GLM interaction testing shows distance friction attenuated post-recovery ($\beta_{\text{dist} \times \text{post}} = +0.1359, p = 0.0008$), reflecting expanded post-pandemic regional road travel.

---

## Slide 7: Opportunity Engine — The 58 Non-Dominated Pareto Corridors

### Headline: Multi-Objective Pareto Optimization Replaces Arbitrary Weighted Scores

```text
  Pareto Objective                             Mathematical Definition                 Policy Goal
  ──────────────────────────────────────────   ─────────────────────────────────────   ────────────────────────
  O1: Structural Demand Gap                    max(0, Expected Flow - Actual Flow)     Capture gravity demand
  O2: Economic Yield (TVAY)                    RM Value-Added Yield / visitor-day      Maximize local GVA
  O3: Destination Capacity Headroom            100% - Average Occupancy Rate (AOR %)   Prevent saturation
  O4: Feeder Diversification                   Destination Origin Concentration (HHI)  Reduce single-feeder risk
  O5: Spatial Accessibility                    Inverse Centroid Friction               Ensure travel feasibility
```

* **Result**: Identifies exactly **58 non-dominated Pareto Front 1 corridors** nationwide.
* **Top Strategic Priorities**:
  - **Selangor $\rightarrow$ Melaka**: 2.73M tourists, 2.11d ALOS, RM 63.00/night (Priority Conversion).
  - **Johor $\rightarrow$ Melaka**: 1.42M tourists, below-median stay capture.
  - **Negeri Sembilan $\rightarrow$ Melaka**: 114k gravity flow gap, Rank 2 Pareto.
  - **Selangor $\rightarrow$ Perak**: High volume, massive off-peak accommodation capacity headroom.

---

## Slide 8: What-If Scenario Lab & Monte Carlo Uncertainty

### Headline: Translating Policy Interventions into Physical Room Demand & GVA

```text
Scenario Example: Selangor -> Melaka Stay Extension (+0.4 days, 15% campaign reach)
──────────────────────────────────────────────────────────────────────────────────
Additional Tourist Nights:              +163,560 nights
Additional Accommodation Spend:         +RM 17.9 Million
Potential Additional Value Added (GVA): +RM 15.4 Million (VAI = 85.8%)
Daily Hotel Rooms Demanded:             +249 rooms/day
Baseline Occupancy -> Projected AOR:    63.8% -> 65.4% (Headroom remaining: 14.6%)
Capacity Saturation Status:             SAFE (< 80.0% Planning Ceiling)
```

* **1,000-Draw Monte Carlo Uncertainty (P10–P90)**:
  - **Conservative (P10)**: +RM 11.2M GVA Proxy
  - **Median (P50)**: +RM 15.4M GVA Proxy
  - **Optimistic (P90)**: +RM 20.1M GVA Proxy
  - **Capacity Breach Probability**: **0.0%** (Low saturation risk under 15% reach).
* **Physical Guardrail**: Every simulation maps tourist nights into daily physical rooms demanded using 1.8 guests/room density scaling.

---

## Slide 9: Commercial Portfolio Optimization — Maximizing Budget Efficiency

### Headline: Mixed-Integer Linear Programming (MILP) Resource Allocation

$$\max_{x} \sum_{i} \text{ExpectedGVA}_i \cdot x_i \quad \text{s.t.} \quad \sum_{i} \text{Cost}_i \cdot x_i \le \text{Budget}, \quad \text{ProjectedAOR}_d \le 80.0\%$$

```text
MILP Optimized RM 5.0M Campaign Portfolio Benchmark:
────────────────────────────────────────────────────
• Total Budget Allocated:      RM 5.00 Million
• Total Budget Utilized:       RM 4.98 Million (99.6% efficiency)
• Expected Incremental GVA:    RM 140.3 Million
• Value-to-Cost Multiple:      28.1x (Scenario Benchmark Multiple)
• Optimal Corridors Funded:    18 high-yield inter-state corridors
• Destinations Protected:      Zero destinations breach the 80% AOR planning ceiling
```

* **Budget Monotonicity**: Reallocating promotional funds using branch-and-cut MILP optimizes cross-corridor feeder synergy, directing investments toward destinations with high lodging yield and ample physical room capacity.
* **Guardrail**: Labeled strictly as a *Value-to-Cost Scenario Benchmark* per AGENTS.md Rule 17.

---

## Slide 10: Institutional Adoption & SDG Impact

### Headline: A Decision-Support System Ready for National Deployment

```text
  Institutional User           Actionable Platform Output                   Policy Mechanism
  ─────────────────────────    ──────────────────────────────────────────   ────────────────────────────────
  MOTAC                        National Portfolio Optimizer (MILP)          Development budget allocation
  Tourism Malaysia             Value Corridor & Pareto Target Lists         Targeted domestic digital ads
  State Tourism Boards         States & Stays Map & Typologies              Master plan stay duration targets
  Local Authorities (PBTs)     Carrying Capacity & Headroom Watches         Infrastructure & room zoning
  Hotel Associations (MAH)     Scenario Simulator & VFR Conversion Lab      Mid-week staycation packages
```

* **SDG 8.9 Alignment**: Drives sustainable tourism that creates domestic employment and promotes local culture and products through high-yield accommodation capture.
* **SDG 12.b Alignment**: Provides continuous, reproducible monitoring tools to measure sustainable tourism economic yield and track physical carrying capacities.
* **The Final Message**:
  $$\boxed{\text{Do not only maximize tourists. Maximize sustainable economic value per visitor-day.}}$$
