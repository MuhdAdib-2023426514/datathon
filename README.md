# Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

> **Economic Dimension of Sustainable Tourism — Aligned with UN SDG 8.9 & 12.b**  
> An analytical decision-support system integrating the **Malaysia Tourism Satellite Account (TSA 2015–2025)**, the **Domestic Tourism Survey (DTS 2018–2025)**, official **MyTourism KPI hotel & homestay operations (2016–2025)**, and an 8-year longitudinal **Origin–Destination (OD) spatial network (2,048 corridor observations)** to shift strategic focus from volume expansion to domestic economic value capture.

[![Tests](https://img.shields.io/badge/tests-100%25%20passed-success)](tests/)
[![TSA-VAI](https://img.shields.io/badge/TSA%20Accommodation%20VAI-85.8%25%20(%231)-purple)](data/processed/)
[![SDG](https://img.shields.io/badge/UN%20SDG-8.9%20%7C%2012.b-blue)](docs/analytics-methodology.md)
[![Audit](https://img.shields.io/badge/Audit-10%2F10%20Defects%20Resolved-emerald)](docs/analytics-validation-report.md)

---

## 1. Core Strategic Thesis

$$\text{Volume Expansion } (\text{More Visitors}) \longrightarrow \text{Value Capture } (\text{More Economic Value from Existing Visitors})$$

Malaysia's post-pandemic domestic tourism has fully surpassed pre-COVID volume peaks, reaching **290.1 million domestic visitors** and **106.5 million overnight tourists** in 2025 (vs. 239.1M and 84.7M in 2019). However, multiple destination states suffer from a **"Volume-Rich, Value-Poor" trap**: heavy excursionist day-tripper traffic, shortening average length of stay (ALOS), and weak accommodation capture.

This project delivers an econometrically audited framework to:
1. **Identify** which tourism products consistently generate the highest domestic Gross Value Added (GVA) per ringgit of supply.
2. **Diagnose** why specific states face value leakage (commercial hotel penetration vs. unpaid Visiting Friends & Relatives lodging).
3. **Bridge Demand with Supply** by integrating 10 years of MOTAC hotel operations (Average Occupancy Rate, room inventory, domestic vs. foreign guests).
4. **Model Longitudinal Spatial Gravity Flows** across 240 bilateral corridors over 8 years (1,920 corridor-years) to quantify distance friction, outbound demographic drivers, and market concentration (HHI).
5. **Simulate Capacity-Constrained Scenarios** that decouple corridor stay extensions from destination day trips while enforcing multi-feeder hotel headroom checks.

> **Mandatory Scope Guardrail**: This project focuses strictly on the **economic dimension of sustainable tourism** (SDG 8.9: economic yield, domestic retention, and jobs; SDG 12.b: impact monitoring). It does not claim to measure complete environmental or social sustainability.

---

## 2. Key Empirical Findings & Econometric Models

### A. Accommodation Services Confirmed #1 in Value-Added Intensity (Stage A & B)
* **Value-Added Intensity Formulation**:
  $$\text{VAI}_{i,t} = \frac{\text{Gross Value Added (GVA)}_{i,t}}{\text{Domestic Supply}_{i,t}}$$
* **TSA 2015–2025 Benchmark**:
  * **Accommodation Services ranks #1 in Malaysia**: 2025 $\text{VAI} = \mathbf{0.8659}$ (86.59%), with a 2023–2025 post-recovery median of $\mathbf{0.8579}$ (CV: 0.039, highly stable across 11 years).
  * Out of every RM 100 spent on accommodation, **RM 85.79 is retained as domestic Gross Value Added (GVA)**, compared to RM 65.50 for Food & Beverage, RM 60.40 for Recreation, and RM 40.70 for Passenger Transport.
  * **Estimated Tourism-Attributable GVA Proxy**:
    $$\text{EstimatedTourismGVA}_{i,t} = \text{ITC}_{i,t} \times \text{VAI}_{i,t} = \text{IndustryGVA}_{i,t} \times \text{TourismRatio}_{i,t}$$
    *(Note: Per AGENTS.md, this analytical proxy is never labeled as official product-level TDGVA).*

---

### B. Econometric Panel Models: One-Way vs. Two-Way Fixed Effects ($N = 126$, 2018–2025, RQ3 & RQ4)
To evaluate the true intra-state elasticity of accommodation spend per tourist with respect to length of stay, two econometric specifications are evaluated across the 16 states over 2018–2025:

* **Model 1: One-Way State Fixed Effects**:
  $$\ln(\text{SpendPerTourist}_{st}) = \alpha_s + \mathbf{1.6067} \ln(\text{ALOS}_{st}) + 0.0075 \text{LuxuryShare}_{st} + 0.4437 \ln(\text{Income}_{st}) - 0.0089 \text{VFRShare}_{st}$$
  * Within-$R^2 = 0.6865$, ALOS $p < 0.0001$.
* **Model 2: Two-Way Fixed Effects (State + Year, State-Clustered Robust SEs)**:
  $$\ln(\text{SpendPerTourist}_{st}) = \alpha_s + \lambda_t + \mathbf{0.6628} \ln(\text{ALOS}_{st}) + 0.0078 \text{LuxuryShare}_{st} + 0.5056 \ln(\text{Income}_{st}) - 0.0094 \text{VFRShare}_{st}$$
  * Within-$R^2 = 0.6517$, ALOS coefficient $\hat{\beta}_1 = \mathbf{+0.6628}$ ($SE = 0.3972, p = 0.0952, 95\% \text{ CI } [-0.1157, 1.4413]$).
  * **Methodological Nuance**: Controlling for national inflation and post-pandemic recovery surges via year dummies $\lambda_t$, the isolated intra-state elasticity of spend per tourist with respect to length of stay is $+0.66$ (positive and marginally significant at $\alpha = 0.10$). Both models are reported side-by-side.

---

### C. Granular DTS Root Causes: Commercial Penetration vs. Unpaid VFR Trap
Ingesting sub-tables (`Jadual 8`, `11`, `12`, `13a`, `14`) across all 16 state DTS publications isolates the root cause of state-level spend discrepancies:
* **The East Coast VFR Paradox**:
  * **Kelantan** records an average stay of **2.89 nights** (2nd longest in Malaysia), but the lowest spend per night (**RM 16.10**) and low occupancy (**43.5% AOR** across 6,392 rooms).
  * **Root Cause**: Over **66.3%** of overnight stays in Kelantan are absorbed by unpaid private homes of friends and relatives (VFR). In Terengganu, unpaid VFR represents **55.1%**.
  * **Policy Insight**: The goal is **not** to induce more vehicle congestion on highways; it is to introduce experiential boutique lodging and certified community homestays that transition unpaid family stays into commercial overnight revenue.
* **High-Capture Transit States**:
  * **Melaka** (**58.3%** paid commercial lodging) and **Pulau Pinang** (**54.6%**) achieve higher spend per night (**RM 63.00** and **RM 72.28**), but face high day-tripper leakage.

---

### D. Spatial Gravity Econometrics: Log-OLS and PPML (2018–2025, $N = 1,890$, RQ6)
Across 240 bilateral interstate corridors over 8 years:

$$\ln(F_{od,t}) = \beta_0 + \mathbf{0.8904} \ln(\text{AdultPop}_{o,t}) + \mathbf{0.7252} \ln(\text{Income}_{o,t}) + \mathbf{0.7042} \ln(\text{DestPull}_{d,t}) - \mathbf{0.6031} \ln(\text{Distance}_{od}) - \mathbf{1.3323} \text{CrossRegion}_{od} + \varepsilon_{od,t}$$

* **Log-OLS Performance**:
  * In log-space: $R^2 = 0.7092$.
  * In original levels space (evaluated on 2025 holdout, $N = 240$): True Predictive **$R^2 = 1 - \frac{\text{SSE}}{\text{SST}} = \mathbf{0.4863}$**, squared correlation $r^2 = 0.5886$. Complete cases $N = 1,650$ panel observations.
  * Distance Friction: $\beta = -0.6031$ ($p < 0.0001$).
  * Cross-Region Air Barrier: $\beta = -1.3323$ (flight-mandatory routes between Peninsular and Borneo face a **$73.6\%$ volume penalty**).
* **Poisson Pseudo-Maximum Likelihood (PPML Gravity)**:
  * Following Silva & Tenreyro (2006) to account for heteroskedastic levels:
  * Distance Elasticity: $\beta = \mathbf{-0.4648}$ ($SE = 0.0381, p < 0.0001$).
  * Out-of-Sample Predictive $R^2 = \mathbf{0.5177}$ in levels, correlation $r = 0.8120$.

---

### E. Destination Market Concentration: Interstate vs. All-Origin HHI (RQ5)
Market fragility is evaluated using Herfindahl-Hirschman Index formulations:
* **Interstate Origin HHI**:
  $$\text{HHI}_{d,t}^{\text{interstate}} = \sum_{o \neq d} \left( \frac{F_{od,t}}{\sum_{k \neq d} F_{kd,t}} \times 100 \right)^2$$
* **Empirical Nuance**:
  * **Sabah 2025**: $75.22\%$ of domestic tourists are Sabah residents traveling within Sabah ($F_{\text{intrastate}} = 5,536\text{k}$). Consequently, All-Origin HHI is $5,746.95$, while its **Interstate Feeder HHI is $1,449.92$** (Diversified $< 1,500$).
  * **Melaka 2025**: $97.92\%$ of tourists originate interstate, yielding $\text{HHI}^{\text{interstate}} = 2,156.40$ (Moderately Concentrated, led by Selangor at $38.78\%$).
  * **Pulau Pinang 2025**: $\text{HHI}^{\text{interstate}} = 2,461.65$ (44.52% from Selangor).

---

### F. State Diagnostic Typology & Calibrated Radar Scores

| Archetype Cluster | Representative States | 2025 Operational Profile | Policy Intervention Mandate |
| :--- | :--- | :--- | :--- |
| **High-Volume Urban Gateway** | **Selangor, Johor, Perak** | High tourist volume ($>8\text{M}$), 46%–55% AOR | Target high-flow feeder corridors for stay extension; convert day trips to 2D1N weekend breaks. |
| **Administrative & Luxury Hub** | **KL, Putrajaya** | Highest spend/night (RM 102.8), high AOR (66.9%) | Premium business-leisure (bleisure), cultural programming, luxury accommodation yield optimization. |
| **Prime Leisure Hotspot** | **Penang, Melaka, Pahang** | High leisure share, constrained capacity (Pahang AOR 76.3%) | Off-peak seasonal dispersion; mid-week incentives; hotel capacity headroom expansion. |
| **Emerging Extended-Stay / High VFR** | **Kelantan, Terengganu, Kedah, Perlis, Sabah, Sarawak** | Long ALOS (2.4–2.9 days), high unpaid VFR ($>55\%$) | Expand registered boutique homestays (SDG 8.9) to monetize family stays without requiring massive hotel capex. |

* **Radar Normalization Recalibration**: Normalization scale for spend/night is calibrated to empirical bounds **$[\text{RM } 20.0, \text{RM } 110.0]$**, eliminating previous zero-collapse and yielding smooth scores from 5.4 (Perlis) to 92.1 (KL).

---

## 3. Sustainable Tourism Indicators (SDG 8.9 & 12.b)

1. **Destination Value Retention (DVR)**:
   $$\text{DVR}_s = \frac{\sum_{i \in \text{Core}} \left(\text{Expenditure}_{s,i} \times \text{VAI}_i\right)}{\text{TotalDomesticExpenditure}_s}$$
   * Incorporates Accommodation ($\text{VAI} = 0.858$), F&B ($0.655$), Transport ($0.407$), Retail ($0.470$), and Recreation ($0.604$).
   * Kuala Lumpur achieves **$\text{DVR} = 61.6\%$** (RM 10,406.6M attributable GVA), with accommodation generating RM 1,669.1M in direct value added.
2. **Excursionist Pressure Ratio (EPR)**:
   $$\text{EPR}_s = \frac{\text{Excursionists (Day-Trippers)}_s}{\text{Overnight Tourists}_s}$$
   * Melaka (1.90) and Negeri Sembilan (1.85) experience heavy daytime transit volume relative to overnight lodging capture.
3. **Tourism Intensity Ratio (TIR)**:
   $$\text{TIR}_s = \frac{\text{Total Domestic Visitors}_s}{\text{Resident Population}_s}$$
   * Evaluates carrying capacity pressure on host resident infrastructure.

---

## 4. Scenario Simulator & Multi-Corridor Capacity Engine (RQ7)

### Decoupled Policy Levers:
1. **Corridor Stay Extension (Bilateral Feeder Level)**:
   $$\Delta \text{TouristNights}_{od} = F_{od} \times \Delta \text{ALOS}$$
   $$\Delta \text{AccomSpend}_{od} = \Delta \text{TouristNights}_{od} \times \text{SpendPerNight}_d$$
2. **Excursionist Day-Trip Conversion (Destination Pool Level)**:
   $$\Delta \text{Tourists}_{d}^{\text{conv}} = \text{Excursionists}_d \times \text{ConversionRate}$$
   $$\Delta \text{TouristNights}_{d}^{\text{conv}} = \Delta \text{Tourists}_{d}^{\text{conv}} \times (\text{ALOS}_d + \Delta \text{ALOS})$$
3. **Potential Attributable TDGVA Proxy**:
   $$\Delta \text{GVAProxy} = \Delta \text{AccomSpend} \times 0.858$$

### Multi-Corridor Saturation & 4-Tier Capacity Check:
$$\text{SimulatedAOR}_d = \text{BaselineAOR}_d + \left( \frac{\sum_{o \in \text{Portfolio}} \Delta \text{TouristNights}_{od}}{\text{HotelRooms}_d \times 365 \times 1.75} \times 100 \right)$$

* **Four Explicit Saturation Tiers**:
  1. **Optimal (< 70%)**: Ample room inventory to absorb simulated stays.
  2. **Moderate Saturation (70%–80%)**: Capacity tight during peak weekend/holiday surges.
  3. **High Saturation (> 80%–100%)**: Severe peak-season bottleneck; requires room inventory expansion.
  4. **Severe Deficit (> 100%)**: Room inventory physically exceeded under scenario demand.
* **Empirical Validation**:
  * **Selangor $\rightarrow$ Melaka (+0.5 nights)**: $+1.36\text{M}$ nights $\rightarrow$ +RM 85.87M spend (+RM 73.67M GVA proxy). Simulated AOR rises from $46.1\%$ to **$55.5\%$** (Optimal tier, 100% feasible).
  * **Pahang Portfolio (15 feeders, +0.5 nights)**: Increases required room nights from $16.96\text{M}$ to $20.93\text{M}$, driving simulated AOR from $76.3\%$ to **$95.0\%$** (High Saturation tier alert).

> **Mandatory Methodological Notice**: *Scenario estimate, not a causal forecast.*

---

## 5. Repository Structure

```text
dosm/
├── AGENTS.md                          # Non-negotiable analytical rules & guardrails
├── README.md                          # Project documentation & empirical findings
├── pyproject.toml                     # Python dependencies (uv / pip)
├── docs/
│   ├── analytics-methodology.md       # Full mathematical & econometric equations
│   ├── analytics-validation-report.md # Before/after audit resolving 10 review findings
│   └── improvingplan.md               # Work package execution blueprint
├── data/
│   ├── processed/
│   │   ├── tourism_data.duckdb        # Analytical database (40 tables)
│   │   └── *.parquet                  # Native Parquet data models
│   └── geo/                           # WGS84 GeoJSON boundaries (16 states)
├── src/
│   ├── ingestion/                     # Ingestion parsers (TSA, DTS, MOTAC KPI, OD panel)
│   ├── analytics/
│   │   ├── accounting.py              # Authoritative national accounting module
│   │   ├── product_value.py           # TSA VAI calculation & quadrants
│   │   ├── panel_econometrics.py      # Two-Way & One-Way FE panel regressions
│   │   ├── gravity_corridor_model.py  # Spatial gravity (Log-OLS & PPML)
│   │   ├── state_diagnostics.py       # Typologies, SDG metrics (DVR, EPR, TIR)
│   │   ├── state_clustering.py        # Archetype clustering & calibrated radar
│   │   ├── accommodation_drivers_ml.py# RQ3 driver attribution
│   │   └── export_dashboard_json.py   # Pre-aggregated JSON exporter
│   ├── network/
│   │   └── corridor_network.py        # OD network & HHI concentration
│   ├── scenarios/
│   │   └── simulator.py               # Decoupled simulator & portfolio capacity
│   ├── validation/                    # Accounting & econometric test suites
│   └── pipeline.py                    # Deterministic stage runner
├── tests/                             # Synthetic unit test fixtures
│   ├── test_accounting_fixtures.py    # Unit tests for VAI, DVR, and proxies
│   ├── test_scenario_fixtures.py      # Unit tests for decoupled scenarios & capacity
│   └── test_gravity_fixtures.py       # Unit tests for gravity predictions & PPML
└── dashboard/                         # Interactive React Decision-Support System
    ├── package.json
    ├── src/
    │   ├── App.tsx
    │   ├── types.ts                   # Authoritative TypeScript interfaces
    │   └── components/
    │       ├── TourismValueMonitor.tsx# View 1: Macro trajectory & VAI rankings
    │       ├── AccommodationMap.tsx   # View 2: State opportunity choropleth & radar
    │       ├── CorridorNetwork.tsx    # View 3: Bilateral OD arcs & HHI concentration
    │       └── ScenarioSimulator.tsx  # View 4: Transparent policy simulator
    └── public/data/                   # Pre-aggregated JSON contracts
```

---

## 6. Quickstart & Reproducibility

### 1. Python Environment Setup
```bash
# Clone repository
git clone https://github.com/MuhdAdib-2023426514/datathon.git
cd datathon

# Install dependencies using uv or venv
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Run Deterministic Analytical Pipeline
```bash
# Run complete end-to-end pipeline (ingest -> analytics -> validate -> export)
python src/pipeline.py --stage all

# Or inspect pipeline status and DuckDB table inventory
python src/pipeline.py --status
```

### 3. Run Automated Validation & Unit Test Suites
```bash
# Run unit test fixtures (accounting, scenarios, gravity)
python -m unittest discover -s tests -p 'test_*.py'

# Run national accounting and corridor verification tests
python src/validation/test_tsa_accounting.py
python src/validation/test_state_and_corridors.py
```

### 4. Launch Interactive Decision-Support Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser to explore the interactive dashboard.

---

## 7. Strategic Value for Policymakers (MOTAC & State Tourism Boards)

1. **Monitor**: Track internal consumption vs. direct TDGVA and focus resources on highest-yield products (Accommodation $\text{VAI} = 85.8\%$).
2. **Diagnose**: Distinguish destinations suffering from unpaid VFR traps (East Coast) from transit day-trip leakage (West Coast).
3. **Target**: Prioritize the highest-volume conversion corridors (e.g. Selangor $\rightarrow$ Melaka, Johor $\rightarrow$ Melaka) where ample hotel room headroom exists.
4. **Simulate**: Test transparent policy interventions with real-time feedback on tourist nights, accommodation revenue, potential GVA, and physical hotel saturation.
