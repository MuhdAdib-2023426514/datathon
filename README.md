# Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

> **Economic Dimension of Sustainable Tourism — Aligned with UN SDG 8.9 & 12.b**  
> An analytical decision-support system integrating the **Malaysia Tourism Satellite Account (TSA 2015–2025)**, the **Domestic Tourism Survey (DTS 2018–2025)**, official **MOTAC hotel & homestay operations (2016–2025)**, and an 8-year longitudinal **Origin–Destination (OD) spatial network (2,048 corridor observations)** to shift strategic focus from volume expansion to domestic economic value capture.

> **North-Star Principle (Phase 60)**:  
> $$\boxed{\text{Do not only maximize tourists. Maximize sustainable economic value per visitor-day.}}$$

[![Tests](https://img.shields.io/badge/tests-153%20passed%20%7C%2020%2F20%20pipeline%20steps-success)](tests/)
[![Frontend Tests](https://img.shields.io/badge/frontend-node%3Atest%20(6%2F6)-blue)](dashboard/tests/)
[![Rubric Evidence](https://img.shields.io/badge/Rubric%20Evidence-25%20Criteria%20Verified-purple)](artifacts/rubric_evidence_matrix.md)
[![TSA-VAI](https://img.shields.io/badge/TSA%20Accommodation%20VAI-85.8%25%20(%231)-purple)](data/processed/)
[![SDG](https://img.shields.io/badge/UN%20SDG-8.9%20%7C%2012.b-blue)](docs/methodology.md)
[![Data Quality](https://img.shields.io/badge/Data%20Quality-100%25%20Pass%20(DuckDB)-emerald)](docs/data_quality.md)
[![Model Validation](https://img.shields.io/badge/Gravity%20R%C2%B2(OOS)-0.5890%20(PPML)-indigo)](docs/model_validation.md)

---

## Table of Contents
1. [The Problem: Volume vs. Value](#1-the-problem-volume-vs-value)
2. [Why It Matters](#2-why-it-matters)
3. [Main Research Questions](#3-main-research-questions)
4. [Economic Framework & Accounting Identities](#4-economic-framework--accounting-identities)
5. [Official Data Sources & Provenance](#5-official-data-sources--provenance)
6. [Analytical Architecture](#6-analytical-architecture)
7. [Main Empirical Findings](#7-main-empirical-findings)
8. [Model Validation & Robustness Diagnostics](#8-model-validation--robustness-diagnostics)
9. [Interactive Decision-Support Dashboard](#9-interactive-decision-support-dashboard)
10. [Commercial & Institutional Implementation Model](#10-commercial--institutional-implementation-model)
11. [Limitations & Methodological Caveats](#11-limitations--methodological-caveats)
12. [Reproduction & Execution Instructions](#12-reproduction--execution-instructions)

---

## 1. The Problem: Volume vs. Value

$$\text{Volume Expansion } (\text{More Visitors}) \longrightarrow \text{Value Capture } (\text{More Economic Value from Existing Visitors})$$

Malaysia's post-pandemic domestic tourism has fully surpassed pre-COVID volume peaks, reaching **290.1 million domestic visitors** and **106.5 million overnight tourists** in 2025 (compared to 239.1M and 84.7M in 2019). However, multiple destination states exhibit a **"Volume-Rich, Value-Constrained" structural pattern**:
- Heavy excursionist day-tripper traffic that strains municipal transit, parking, and municipal sanitation infrastructure without generating overnight commercial expenditure.
- Shortening average length of stay (ALOS) across prime destinations.
- Disproportionately high shares of unpaid Visiting Friends & Relatives (VFR) lodging in extended-stay regions, limiting domestic Gross Value Added capture.

---

## 2. Why It Matters

Under **UN Sustainable Development Goal (SDG) 8.9** (promoting sustainable tourism that creates local economic value and employment) and **SDG 12.b** (monitoring sustainable development impacts), maximizing visitor volume alone is no longer an adequate policy objective.

Without understanding the value efficiency of each tourism product and the capacity constraints of destinations, untargeted promotion induces physical congestion and infrastructure depreciation without capturing local economic yield. Strategic policy must identify where existing domestic mobility can be converted into higher-yield overnight stays and direct Gross Value Added capture.

> **Mandatory Scope Guardrail**: This project focuses strictly on the **economic dimension of sustainable tourism**. It does not claim to measure complete environmental or social sustainability.

---

## 3. Main Research Questions

Aligned with `AGENTS.md Section 2`:
1. Which tourism products consistently have the highest value-added intensity from 2015 to 2025?
2. Is accommodation consistently a high-value-added tourism activity?
3. What measurable factors are associated with higher accommodation expenditure?
4. How is Average Length of Stay (ALOS) related to accommodation expenditure and economic yield?
5. Which Malaysian states receive high domestic tourist flows but have relatively short stays or weak accommodation capture?
6. Which origin-destination corridors have the strongest potential to convert existing visitor volume into additional overnight stays and lodging value?
7. Under transparent scenarios, how much additional accommodation expenditure and potential value added could be generated?

---

## 4. Economic Framework & Accounting Identities

### 4.1 Value-Added Intensity (VAI)
$$\text{VAI}_{i,t} = \frac{\text{GVA}_{i,t}}{\text{DomesticSupply}_{i,t}}$$
Proportion of each industry's gross output represented by Gross Value Added rather than intermediate imports or intermediate consumption. Accommodation services ranks #1 in Malaysia with a 2023–2025 post-recovery median of **$0.8579$** (85.8%).

### 4.2 Estimated Tourism-Attributable GVA (Value-Added Proxy)
$$\text{EstimatedTourismGVA}_{i,t} = \text{ITC}_{i,t} \times \text{VAI}_{i,t} = \text{IndustryGVA}_{i,t} \times \text{TourismRatio}_{i,t}$$
*(Note: Per AGENTS.md, this analytical proxy is never labeled as official product-level TDGVA).*

### 4.3 Visitor-Days & Tourism Value-Added Yield (TVAY)
$$\text{VisitorDays}_s = \text{Tourists}_s \times \text{ALOS}_s + \text{Excursionists}_s$$
$$\text{TVAY}_s = \frac{\text{EstimatedTourismGVA}_s}{\text{VisitorDays}_s} \quad (\text{RM/visitor-day})$$
$$\text{TourismGVAIntensity}_s = \frac{\text{EstimatedTourismGVA}_s}{\text{MappedExpenditure}_s} \times 100\%$$

### 4.4 Constant-Price Deflation (Real 2025 RM)
$$\text{RealExpenditure}_{s,t} = \text{NominalExpenditure}_{s,t} \times \left( \frac{\text{CPI}_{2025}}{\text{CPI}_t} \right)$$

### 4.5 Combined Scenario Accounting & Overlap Resolution
$$\text{AdditionalTouristNights} = \text{AddNights}_{\text{ALOS}} + \text{AddNights}_{\text{DayTrip}}$$
$$\text{TransferredExistingVFRNights} = \text{ConvertedVFRTourists} \times \text{BaselineALOS}$$
$$\text{VFROverlapNights} = \text{ConvertedVFRTourists} \times \text{AffectedShare} \times \Delta\text{ALOS}$$
$$\text{TotalAdditionalGuestNights} = \text{AddNights}_{\text{ALOS}} - \text{VFROverlapNights} + \text{AddNights}_{\text{DayTrip}} + \text{VFRGuestNights}$$
*Disclosed: Stay extension applied to VFR converts within paid lodging demand is subtracted from general extension demand to prevent double-counting.*

### 4.6 Scenario GVA-to-Cost Multiple (Macroeconomic Efficiency)
$$\text{ScenarioGVAToCostMultiple} = \frac{\text{Potential Additional GVA (RM Million)}}{\text{Assumed Campaign Cost (RM Million)}}$$
*Disclosed: Measures macroeconomic Gross Value Added generated per promotional campaign expenditure unit under transparent scenario assumptions; not an investor cash return, commercial net profit, or fiscal tax receipt.*

Full mathematical formulas are documented in [docs/methodology.md](file:///home/muhammad_adib/dosm/docs/methodology.md).

---

## 5. Official Data Sources & Provenance

All data streams are sourced from official Malaysian government publications, cataloged with SHA-256 cryptographic hashes in `data/metadata/source_registry.yaml` and [docs/data_quality.md](file:///home/muhammad_adib/dosm/docs/data_quality.md):

1. **DOSM Tourism Satellite Account (TSA) 2015–2025**: GVA, domestic supply, tourism ratios, internal tourism consumption (ITC), and employment across 8 characteristic products.
2. **DOSM Domestic Tourism Survey (DTS) 2018–2025**: State visitors, overnight tourists, excursionists, expenditure components, ALOS, and bilateral OD flows. (State DTS publication date verified as 15 September 2026; all 16 state workbooks cataloged with individual SHA-256 byte hashes in source registry).
3. **MOTAC Hotel Operations & Capacity 2016–2025**: Average Occupancy Rate (AOR), room inventory, domestic vs. foreign hotel guests across all 16 states.
4. **MOTAC Homestay Performance Statistics 2023–2024**: Registered homestay capacity, village operators, and guest income.
5. **DOSM Household Income & Expenditure Survey (HIES 2024)**: State median household income series.
6. **DOSM Demographic Statistics 2018–2025**: State adult populations and age cohorts.
7. **DOSM Consumer Price Index (CPI 2015–2025)**: Annual state and national price indices for Real RM deflation.

---

## 6. Analytical Architecture

The end-to-end analytical decision chain follows a 10-stage sequential flow:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        NATIONAL TOURISM VALUE                          │
│         TSA Macro Accounts (2015–2025) & Product VAI Frontier          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          STATE PRODUCTIVITY                            │
│         Tourism Value-Added Yield (TVAY) & 4-Quadrant Typology         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         EXPLORATORY DRIVERS                            │
│          Two-Way Panel Fixed Effects & Lodging Yield Model             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          DOMESTIC MOBILITY                             │
│       Longitudinal OD Network (2,048 Total Pairs, 2018–2025)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         STRUCTURAL FLOW GAP                            │
│        Zero-Leakage PPML Gravity (1,920 Interstate Observations)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        OPPORTUNITY SCREENING                           │
│        Multi-Criteria Pareto Frontier (58 Optimal Corridors)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          SCENARIO TESTING                              │
│       Capacity-Aware Policy Levers & Room Saturation Headroom          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                            UNCERTAINTY                                 │
│      1,000-Draw Monte Carlo (Data-Calibrated CV, Null Capacity Alert)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        BUDGET OPTIMIZATION                             │
│     Exact MILP Benchmarks & Heuristic User Allocations (No False Opt)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           DECISION BRIEF                               │
│        Grounded State Evidence Query & 7-Element Evidence Drawer       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Main Empirical Findings

### A. Accommodation Services Confirmed #1 in Value-Added Intensity
- Out of every RM 100 spent on accommodation services in Malaysia, **RM 85.79 is retained as direct domestic Gross Value Added (GVA)** (2023–2025 post-recovery median VAI = 0.8579, CV = 0.039).
- Comparison: Food & Beverage retains RM 65.50, Cultural/Recreation retains RM 60.40, Retail Shopping margin retains RM 47.00, and Passenger Transport retains RM 40.70.

### B. Econometric Panel Models of Accommodation Expenditure ($N = 126$, 2018–2025)
- **Model 2: Two-Way Fixed Effects (State + Year, State-Clustered Robust SEs)**:
  $$\ln(\text{RealAccomSpend}_{st}) = \alpha_s + \lambda_t + \mathbf{0.6628} \ln(\text{ALOS}_{st}) + \mathbf{0.7327} \ln(\text{Tourists}_{st}) + \varepsilon_{st}$$
  - ALOS Elasticity: $\hat{\beta}_1 = \mathbf{+0.6628}$ ($SE = 0.3972, p = 0.0952, 95\% \text{ CI } [-0.1157, 1.4413]$).
  - Tourist Volume Elasticity: $\hat{\beta}_2 = \mathbf{+0.7327}$ ($SE = 0.1168, p < 0.0001$).
  - **Empirical & Methodological Interpretation**: After controlling for state fixed effects, year effects, and inflation, ALOS retains a positive estimated association with real accommodation expenditure. The coefficient is approximately 0.66 and is statistically imprecise at the conventional 5% level ($p = 0.0952$), representing an observational relationship rather than a guaranteed causal impact.
  - **Leave-One-State-Out Robustness**: Running 16 iterative regressions excluding one state at a time confirmed **16/16 sign stability** for both ALOS ($\beta \in [+0.52, +0.81]$) and Tourist Volume ($\beta \in [+0.68, +0.79]$), demonstrating the positive association is not driven by any single state outlier.
- **Model 4: Lodging Yield Model ($R^2 = 0.8018$)**:
  - Occupancy intensity (AOR) elasticity: $\hat{\gamma} = +0.2068$ ($SE = 0.1868, p = 0.2683$).
  - Captures lodging yield responsiveness under tighter destination occupancy and leisure profiles.

### C. Structural Spatial Gravity Model ($N = 1,920$ Interstate Corridor-Years, 2018–2025)
- **Observation Counts Disentangled**:
  - *Interstate Corridors*: $16 \text{ origins} \times 15 \text{ destinations} = 240 \text{ directional corridors} \times 8 \text{ years} = 1,920 \text{ panel observations}$ ($1,680$ training 2018–2024, $240$ holdout 2025).
  - *Total Bilateral Network*: $16 \times 16 = 256 \text{ pairs} \times 8 \text{ years} = 2,048 \text{ observations}$ (including 16 intrastate pairs $\times 8 = 128 \text{ observations}$).
- Evaluated via **Poisson Pseudo-Maximum Likelihood (PPML)** with origin, destination, and year fixed effects:
  - **Distance Decay Friction**: $\beta_1 = \mathbf{-0.4104}$ ($SE = 0.0517, p < 0.0001$). A 10% increase in corridor distance reduces tourist flow by 4.1%.
  - **Borneo Cross-Region Flight Barrier**: $\beta_2 = \mathbf{-0.8022}$ ($SE = 0.1289, p < 0.0001$). Flight-mandatory corridors crossing between Peninsular Malaysia and Borneo face a 55.2% volume penalty.
  - **Structural Invariance**: The interaction test $\ln(\text{Distance}) \times \text{PostRecovery}$ yields $\beta = +0.1023$ ($p = 0.1198$), which is not statistically significant at conventional thresholds ($\alpha = 0.05$). The analysis does not establish that distance sensitivity changed materially after post-COVID recovery; spatial friction remained structurally invariant.
  - **Out-of-Sample Predictive $R^2_{OOS} = \mathbf{0.5890}$** on the held-out 2025 sample ($N=240$), correlation $r = 0.8759$, $\text{MAE} = 175.50\text{k}$.

### D. Multi-Dimensional Opportunity Framework & Pareto Frontier
- Rather than equating gravity flow residuals with policy priority, corridors are evaluated across 5 criteria: structural flow gap, yield, capacity headroom, accessibility, and feeder diversification.
- Dominance is computed strictly across complete, finite evidence vectors (`evidence_status = "complete"`); candidates with unobserved capacity or yield are flagged as `insufficient_data` and excluded from dominating complete candidates.
- Opportunity screening is structurally decoupled from hypothetical +0.5-night scenario projections, ensuring targeting reflects empirical baseline capacity and yield.
- Exactly **58 inter-state corridors** reside on Pareto Front 1, led by:
  1. *Selangor $\rightarrow$ W.P. Kuala Lumpur* (Pareto Rank 1, Score 75.47, 84k stay gap, RM 83/night yield).
  2. *Negeri Sembilan $\rightarrow$ Melaka* (Pareto Rank 1, Score 71.88, 114k stay gap, RM 63/night yield).
  3. *Johor $\rightarrow$ Melaka* (Pareto Rank 1, Score 68.21, 88k stay gap, RM 63/night yield).

---

## 8. Model Validation & Robustness Diagnostics

Detailed validation metrics are reported in [docs/model_validation.md](file:///home/muhammad_adib/dosm/docs/model_validation.md):

| Model Specification | Out-of-Sample $R^2_{OOS}$ | Pearson Correlation ($r$) | MAE (Thousands) | RMSE (Thousands) | RMSLE | sMAPE (%) | Role in Platform |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PPML Structural Gravity (Primary)** | **0.5890** | **0.8759** | **175.50** | **329.04** | **0.9993** | **75.43%** | **Authoritative Counterfactual Engine** |
| **Log-OLS Classical Gravity (Comparison)** | 0.2936 | 0.7139 | 233.35 | 431.40 | 1.5231 | 105.68% | Classical comparison (retransformation bias) |
| **Naive Baseline 1: Lagged Persistence (2024)** | 0.7637 | 0.8816 | 134.92 | 249.51 | 1.1712 | 70.54% | 1-step-ahead forecasting benchmark |
| **Naive Baseline 2: Historical Mean (2018–2024)** | 0.6732 | 0.9343 | 163.35 | 293.39 | 1.0788 | 80.13% | Long-run historical average benchmark |

> **Comparative Modeling Note (AGENTS.md Rule 15)**: Autoregressive persistence (2024 Lag, $R^2_{OOS} = 0.7637$) outperforms structural PPML ($R^2_{OOS} = 0.5890$) for pure 1-step point forecasting due to year-over-year corridor inertia. PPML is retained as the authoritative decision engine because autoregressive lags cannot evaluate counterfactual policy interventions, distance friction shifts, or structural gravity gaps.

---

## 9. Interactive Decision-Support Dashboard

The React + TypeScript web application (`dashboard/`) provides 8 specialized decision views answering core policy questions:

1. **National Value Monitor**: Where does Malaysian tourism create economic value? (TSA macro timeseries, VAI product frontier, VAI-ITC quadrant positioning).
2. **State Productivity Map**: Which states generate the greatest economic value from each visitor-day? (4-Quadrant state typology choropleth, visitor-days, TVAY yield radar).
3. **Accommodation Drivers**: Which measurable factors are associated with lodging economic capture? (Two-Way FE panel models, VFR vs. commercial hotel shares).
4. **Mobility & OD Network**: Where do domestic visitors originate and travel? (Bilateral flow arcs, interstate vs. all-origin HHI concentration).
5. **Corridor Opportunities**: Which corridors combine structural demand gaps, high yield, and spare hotel capacity? (58 Pareto optimal corridors, multi-attribute filtering).
6. **Scenario Simulator**: What might happen under a targeted stay extension or day-trip conversion? (Direct TypeScript formula execution in `dashboard/src/lib/scenario.ts`, explicit VFR extension overlap subtraction, 4-tier hotel capacity saturation checks).
7. **Portfolio Optimizer**: How should a fixed tourism promotional budget be allocated? (Precomputed exact MILP benchmarks, dynamic heuristic allocation for custom user costs, and Scenario GVA-to-Cost Multiples).
8. **Action Brief**: What operational decisions should be implemented? (Executive decision summary, deterministic State Evidence Lookup, and 7-element Evidence Drawer).

---

## 10. Commercial & Institutional Implementation Model

Detailed in [docs/implementation_model.md](file:///home/muhammad_adib/dosm/docs/implementation_model.md):
- **Target Beneficiaries**: Ministry of Tourism, Arts and Culture (MOTAC), Tourism Malaysia, State Tourism Action Councils, DMOs, Malaysian Association of Hotels (MAH), and Malaysia Budget & Business Hotel Association (MyBHA).
- **Decision Workflow**: `Monitor` (TSA accounts) $\rightarrow$ `Diagnose` (State capture) $\rightarrow$ `Target` (Pareto corridors) $\rightarrow$ `Simulate` (Capacity checks) $\rightarrow$ `Optimize` (MILP budget allocation) $\rightarrow$ `Act` (Marketing campaigns & homestay licensing).
- **Melaka Heritage Pilot Specification**: Comprehensive 8–12 week operational pilot plan targeting Selangor $\rightarrow$ Melaka and Negeri Sembilan $\rightarrow$ Melaka corridors, complete with RACI governance matrix, allocated budget (RM 85k–120k), and a quasi-experimental Difference-in-Differences (DiD) evaluation design using non-targeted control feeder corridors.
- **Adoption & External Proof Status**: While the decision architecture and pilot design are fully operational in code, direct stakeholder interview feedback and formal inter-agency data-sharing agreements remain **EXTERNAL EVIDENCE PENDING** awaiting real-world institutional engagement.
- **Refresh Model**: Annual TSA refresh, annual DTS survey ingestion, monthly MOTAC occupancy updates.

---

## 11. Limitations & Methodological Caveats

Detailed in [docs/limitations.md](file:///home/muhammad_adib/dosm/docs/limitations.md):
1. **Observational Nature**: All econometric relationships represent statistical associations, not causal guarantees.
2. **Small State Sample**: The panel contains $N = 16$ states over 8 years ($126$ observations). State-clustered inference is supported by 16/16 leave-one-out sign stability.
3. **National VAI on State Expenditure**: State-level GVA proxies apply national TSA value-added ratios to state expenditure composition.
4. **Annual AOR Masks Peak Congestion**: Hotel occupancy rates represent annual averages; weekend and holiday surges may face tighter capacity.
5. **Zero-Fabrication Policy**: Missing empirical fields remain `null`/`NaN` and are never replaced with arbitrary synthetic defaults.
6. **Heuristic Custom Portfolio Optimization**: Custom user-cost funding allocations use a constrained greedy knapsack heuristic labeled *"Heuristic allocation; optimality not established"*, while standard preset tiers retain exact precomputed MILP solutions.
7. **Non-Causal Policy Projections**: All simulation projections display the mandatory disclaimer: *"Scenario estimate, not a causal forecast."*

---

## 12. Reproduction & Execution Instructions

### A. Environment Setup
```bash
# Clone repository
git clone https://github.com/MuhdAdib-2023426514/datathon.git
cd datathon

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### B. Execute Master Pipeline
```bash
# Run end-to-end pipeline (ingest -> analytics -> validate -> export)
python src/pipeline.py --stage all

# Run automated 20-step validation gate
python src/pipeline.py --stage validate

# Check pipeline status and table row counts
python src/pipeline.py --status
```

### C. Run Full Test & Validation Suite
```bash
# Run all unit, contract, snapshot, and remediation test suites (153 tests)
pytest tests/

# Run national accounting, corridor verification, and data quality audits
python src/validation/test_tsa_accounting.py
python src/validation/test_state_and_corridors.py
python src/validation/data_quality_report.py
```

### D. Run Frontend Tests & Local Dashboard
```bash
cd dashboard
npm install

# Run frontend unit & cross-language formula parity tests (Node.js test runner)
npm test

# Run linter and verify production build
npm run lint
npm run build

# Launch development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 13. Standalone Documentation Directory

- [artifacts/rubric_evidence_matrix.md](file:///home/muhammad_adib/dosm/artifacts/rubric_evidence_matrix.md) — Comprehensive 25-Criteria Rubric Evidence Matrix & Verification Register.
- [docs/rubric_remediation_plan.md](file:///home/muhammad_adib/dosm/docs/rubric_remediation_plan.md) — Priority remediation plan (R01–R12 & C00–C17) resolving audit findings.
- [docs/presentation_deck.md](file:///home/muhammad_adib/dosm/docs/presentation_deck.md) — 10-Slide Executive Pitch Deck & Storyline (Phase 51).
- [docs/judge_defense.md](file:///home/muhammad_adib/dosm/docs/judge_defense.md) — The Five Judge Questions & Competition Defense Package (Phases 58 & 63).
- [notebooks/tourism_value_optimizer_walkthrough.ipynb](file:///home/muhammad_adib/dosm/notebooks/tourism_value_optimizer_walkthrough.ipynb) — Interactive Python analytical walkthrough (AGENTS.md Section 17).
- [docs/methodology.md](file:///home/muhammad_adib/dosm/docs/methodology.md) — Authoritative mathematical specifications and econometric equations.
- [docs/data_dictionary.md](file:///home/muhammad_adib/dosm/docs/data_dictionary.md) — Comprehensive schema, units, formulas, and null semantics for all tables.
- [docs/model_validation.md](file:///home/muhammad_adib/dosm/docs/model_validation.md) — Out-of-sample holdout benchmarking, GLM break tests, and panel diagnostics.
- [docs/data_quality.md](file:///home/muhammad_adib/dosm/docs/data_quality.md) — Automated QA audit, domain boundary checks, and SHA-256 provenance hashes.
- [docs/limitations.md](file:///home/muhammad_adib/dosm/docs/limitations.md) — Transparent methodological limitations and non-causal disclosures.
- [docs/implementation_model.md](file:///home/muhammad_adib/dosm/docs/implementation_model.md) — Commercial adoption roadmap and institutional user workflows.
- [artifacts/final_rubric_audit.md](file:///home/muhammad_adib/dosm/artifacts/final_rubric_audit.md) — Historical audit record (superseded by `artifacts/rubric_evidence_matrix.md`).


