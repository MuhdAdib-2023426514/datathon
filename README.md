# Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

> **Economic Dimension of Sustainable Tourism — Aligned with UN SDG 8.9 & 12.b**  
> An analytical decision-support system integrating the **Malaysia Tourism Satellite Account (TSA 2015–2025)**, the **Domestic Tourism Survey (DTS 2018–2025)**, official **MyTourism KPI hotel & homestay operations (2016–2025)**, and an 8-year longitudinal **Origin–Destination (OD) spatial network (2,048 corridor observations)** to shift strategic focus from volume expansion to economic value capture.

---

## 1. Core Strategic Thesis

$$\text{Volume Expansion } (\text{More Visitors}) \longrightarrow \text{Value Capture } (\text{More Economic Value from Existing Visitors})$$

Malaysia's post-pandemic domestic tourism has fully surpassed pre-COVID volume peaks (reaching **290.1 million domestic visitors** and **106.5 million overnight tourists** in 2025 vs. 239.1M and 84.7M in 2019). However, several destination states suffer from a **"Volume-Rich, Value-Poor" trap**: heavy day-tripper traffic, shortening average length of stay (ALOS), and weak accommodation capture.

This project delivers an econometrically rigorous framework to:
1. **Identify** which tourism activities consistently generate the highest domestic Gross Value Added (GVA) per ringgit of supply.
2. **Diagnose** why certain states face value leakage or stay-lagging gaps (commercial hotel penetration vs. unpaid Visiting Friends & Relatives lodging).
3. **Bridge Demand with Supply** by integrating 10 years of MOTAC hotel operations (Average Occupancy Rate, room inventory, domestic vs. foreign guests).
4. **Model Longitudinal Spatial Gravity Flows** across 2,048 directed corridor observations (2018–2025) to quantify distance decay, market concentration (HHI), and untapped high-yield routes.
5. **Simulate Capacity-Constrained Scenarios** that incorporate physical hotel room headroom to prevent overtourism bottlenecks and guide targeted corridor policies.

> **Mandatory Scope Guardrail**: This project focuses strictly on the **economic dimension of sustainable tourism** (SDG 8.9: economic yield, domestic retention, and jobs; SDG 12.b: impact monitoring). It does not claim to measure complete environmental or social sustainability.

---

## 2. Key Empirical Findings

### A. Accommodation Services Confirmed #1 in Value-Added Intensity (Stage A & B)
* **Value-Added Intensity Formulation**:
  $$\text{VAI}_{i,t} = \frac{\text{Gross Value Added (GVA)}_{i,t}}{\text{Domestic Supply}_{i,t}}$$
* **TSA 2015–2025 Benchmark**:
  * **Accommodation Services ranks #1 in Malaysia**: Median post-recovery $\text{VAI} = \mathbf{0.8579}$ (CV: 0.039, highly stable across 11 years).
  * Out of every RM 100 spent on accommodation, **RM 85.79 is captured as domestic Gross Value Added (GVA)**, compared to only RM 43.18 for Food & Beverage, RM 38.87 for Recreation, and RM 30.00 for Passenger Transport.
  * **Strategic Classification**: *High-Value Core Activity*.

---

### B. Multi-Factor Panel Econometrics ($N = 126$, 2018–2025, Stage C)
By linking 8 years of DTS visitor survey demand with official MOTAC hotel operations across all 16 states and federal territories, we estimate fixed-effects models with Huber-White (HC1) robust standard errors:

$$\ln(\text{AccommodationSpend}_{s,t}) = \alpha_s + \mathbf{1.2410} \ln(\text{ALOS}_{s,t}) + \mathbf{0.9407} \ln(\text{Tourists}_{s,t}) + \mathbf{0.4024} \ln(\text{AOR}_{s,t}) + \mathbf{0.0071} (\text{ForeignShare}_{s,t}) + \varepsilon_{s,t}$$

*Overall Model Fit: $R^2 = \mathbf{0.9598}$.*

* **Super-Elastic Stay Value ($\beta = +1.2410, p < 0.001$)**: A 10% increase in length of stay yields a **$+12.4\%$ increase in accommodation expenditure**, confirming super-linear compounding returns from longer stays.
* **Occupancy Yield Premium ($\beta = +0.4024, p = 0.023$)**: A 10% increase in hotel Average Occupancy Rate (AOR) generates a **$+4.02\%$ gain in accommodation spend**, holding visitor volume and stay length constant (the RevPAR / pricing power effect).
* **Foreign Guest Synergy ($\beta = +0.0071, p = 0.046$)**: Foreign hotel presence lifts domestic spend rather than crowding it out, as high foreign demand supports higher-tier hospitality infrastructure.

---

### C. Granular DTS Root Causes: Commercial Penetration vs. Unpaid VFR Trap
Ingesting sub-tables (`Jadual 8`, `11`, `12`, `13a`, `14`) across all 16 state DTS publications isolates the root cause of state-level spend discrepancies:
* **The East Coast VFR Paradox**:
  * **Kelantan** records an average stay of **2.89 nights** (2nd longest in Malaysia), but the lowest spend per night (**RM 16.10**) and low occupancy (**43.5% AOR** across 6,392 rooms).
  * **Root Cause**: Over **66.3%** of overnight stays in Kelantan are absorbed by unpaid private homes of friends and relatives (VFR). In Terengganu, unpaid VFR represents **55.1%**.
  * **Policy Insight**: In these states, the goal is **not** to bring more cars onto the highway; it is to introduce experiential boutique lodging and registered community homestays that convert unpaid family stays into commercial overnight revenue.
* **High-Capture Transit States**:
  * **Melaka** (**58.3%** paid commercial lodging) and **Pulau Pinang** (**54.6%**) achieve much higher spend per night (**RM 63.00** and **RM 72.28**), but face high day-tripper leakage.

---

### D. Longitudinal Spatial Gravity Econometrics (2018–2025, $N = 1,920$)
Ingesting all 8 annual national DTS Origin–Destination flow matrices yields **2,048 directed corridor observations** ($240$ inter-state corridors $\times 8$ years = $1,920$).

$$\ln(F_{o,d,t}) = \alpha_0 + \sum_{y} \tau_y D_y - \mathbf{0.5592} \ln(\text{Distance}_{o,d}) + \mathbf{0.8635} \ln(\text{OriginMass}_{o,t}) + \mathbf{0.7169} \ln(\text{DestPull}_{d,t}) - \mathbf{1.2284} \cdot \text{CrossRegion}_{o,d} + \varepsilon_{o,d,t}$$

*Overall Model Fit: In-sample Panel $R^2 = \mathbf{0.6940}$; Out-of-sample $R^2 = \mathbf{0.5158}$ (Trained on 2018–2024 $\rightarrow$ Tested on 2025 Actuals).*

* **Distance Decay ($\beta = -0.5592, t = -10.98, p < 0.001$)**: A 10% increase in corridor distance reduces domestic tourist flow by **$5.6\%$**.
* **Structural Friction Shift**: Distance friction softened from **$-0.5894$** pre-COVID (2018–2019) to **$-0.5271$** post-recovery (2023–2025), reflecting expanded highway connectivity and post-pandemic domestic road trip habits.
* **Flight Barrier**: Flight-mandatory corridors between Peninsular and East Malaysia face an average **$70.7\%$ flow barrier** relative to contiguous road routes.

---

### E. Destination Market Concentration (Longitudinal HHI, 128 State-Years)
Longitudinal tracking of the Herfindahl-Hirschman Index ($HHI = \sum s_{o,d}^2$) across 2018–2025 reveals structural dependencies:
* **The Klang Valley Dependency**: For **Melaka** (HHI: 2,085), **Negeri Sembilan** (HHI: 2,155), **Perak** (HHI: 1,905), and **Pulau Pinang** (HHI: 1,891), **Selangor** has remained the dominant feeder market for all 8 consecutive years.
* **East Malaysia Self-Reliance**: **Sarawak** (average HHI: 6,967) and **Sabah** (average HHI: 6,407) are heavily driven by intra-state mobility due to geographic isolation.

---

### F. Operational State Typology 2.0 (Supply-Demand Frontier)

| Quadrant | State Cluster | 2025 Operational Profile | Policy Intervention |
| :--- | :--- | :--- | :--- |
| **Quadrant 1: Capacity-Constrained Yield Maximizers** | **Pahang, KL, Putrajaya** | High AOR (>55%–76%), high spend/night | Shift from volume growth to premiumization; incentivize weekday & off-peak seasonal dispersion. |
| **Quadrant 2: Prime Conversion Targets (High Headroom)** | **Melaka, Perak, Johor, Pulau Pinang** | High tourist inflow, 45%–58% AOR (>40% spare room capacity) | **Top Priority**: Convert day-trippers to overnight stays via evening cultural events, night markets, and 2D1N weekend packages. |
| **Quadrant 3: VFR-Trapped High ALOS States** | **Kelantan, Terengganu, Kedah, Negeri Sembilan** | Long stays (2.3–2.9 days), low spend/night (<RM 40), <46% AOR | Expand registered boutique homestays and heritage lodging to capture unmonetized family stays. |
| **Quadrant 4: Frontier & Regional Gateways** | **Perlis, Labuan, Sabah, Sarawak** | Specialized markets or geographic gateways | Cross-border tourism circuits (e.g., Thailand–Perlis, Brunei/Kalimantan–Borneo) and eco-tourism length extensions. |

---

## 3. Sustainable Tourism Economic Indicators (SDG 8.9 & 12.b)

1. **Tourism Economic Yield per Visitor-Day (TEY)**:
   $$\text{TEY}_s = \frac{\text{Total Tourism Expenditure}_s}{(\text{Tourists}_s \times \text{ALOS}_s) + \text{Excursionists}_s}$$
   * Top: Labuan (RM 376.57/day), KL (RM 348.84/day), Penang (RM 314.38/day).
   * Bottom: Kedah (RM 193.18/day), Perak (RM 207.53/day).
2. **Domestic Value Retention Multiplier (DVR)**:
   $$\text{DVR Rate}_s = \frac{\sum_k \text{Expenditure}_{s,k} \times \text{VAI}_k}{\text{Total Tourism Expenditure}_s} \times 100\%$$
   * Demonstrates how shifting spending into accommodation ($VAI = 85.8\%$) dramatically increases retained domestic GVA.
3. **Excursionist Pressure Ratio (EPR)**:
   $$\text{EPR}_s = \frac{\text{Excursionists}_s}{\text{Overnight Tourists}_s}$$
   * Melaka (1.90), Selangor (2.43), and KL (2.48) show high daytime infrastructure pressure relative to overnight lodging capture.

---

## 4. Capacity-Constrained Scenario Simulator (Stage F)

The simulator evaluates the domestic economic yield from targeted corridor interventions while enforcing **physical hotel room capacity feasibility**:

$$\Delta \text{Tourist Nights}_{o,d} = \text{Flow}_{o,d} \times \Delta \text{ALOS}_d$$
$$\Delta \text{AccomSpend}_{o,d} = \Delta \text{Tourist Nights}_{o,d} \times \text{SpendPerNight}_d$$
$$\Delta \text{Attributable GVA}_{o,d} = \Delta \text{AccomSpend}_{o,d} \times \text{VAI}_{\text{Accom}} \quad (\text{VAI} = 0.8579)$$
$$\text{Implied AOR}_{d} = \text{Baseline AOR}_{d, 2025} + \left(\frac{\Delta \text{Tourist Nights}_{o,d} / (365 \times 1.8)}{\text{Total Rooms}_{d, 2025}} \times 100\right)$$

### Opportunity Gap & Feasibility Benchmark ($\Delta\text{ALOS} = +0.5$ Nights):
* **Selangor $\rightarrow$ Melaka (Rank 1 Opportunity)**:
  * Adds $+1.36\text{M}$ tourist nights $\rightarrow$ **+RM 85.87M** accommodation spend (**+RM 73.67M** retained GVA).
  * Melaka has **4.06 million unoccupied room nights** (46.1% baseline AOR). Implied AOR rises smoothly to **55.50%** $\rightarrow$ **100% Feasible immediately**.
* **Selangor $\rightarrow$ Pahang (Rank 5 Opportunity)**:
  * Adds $+1.26\text{M}$ tourist nights $\rightarrow$ **+RM 67.70M** accommodation spend (**+RM 58.08M** retained GVA).
  * Pahang baseline AOR is **76.3%** across 34,401 rooms. Implied AOR reaches **82.96%** $\rightarrow$ ⚠️ **Capacity Saturation Warning (>80% Ceiling)**. MOTAC must steer marketing toward weekday and off-peak shoulder season dispersion.

> **Mandatory Disclaimer**: *Scenario estimate, not a causal forecast.*

---

## 5. Repository Architecture & Database Inventory

```text
dosm/
├── AGENTS.md                          # Non-negotiable analytical rules & guardrails
├── README.md                          # Project documentation & empirical findings
├── data/
│   ├── dts/                           # 133 parsed Excel workbooks (2018–2025)
│   │   └── <YEAR>/national/ & state/
│   ├── processed/
│   │   ├── tourism_data.duckdb        # Unified local analytical database (22 tables)
│   │   └── *.parquet                  # Native Parquet exports
│   └── geo/                           # Malaysia state GIS boundaries & GeoJSON
├── src/
│   ├── ingestion/
│   │   ├── tsa_parser.py              # TSA 2015-2025 macro & product parser
│   │   ├── state_parser.py            # DTS 2025 cross-sectional state profile parser
│   │   ├── multi_year_state_parser.py # DTS 2018-2025 multi-year state panel parser
│   │   ├── granular_dts_parser.py     # DTS sub-tables (Jadual 8, 11, 12, 13a, 14 root causes)
│   │   ├── mytourism_kpi_parser.py    # MOTAC KPI 2016-2025 hotel & homestay operations parser
│   │   └── od_panel_parser.py         # DTS 2018-2025 8-year OD panel (2,048 directed flows)
│   ├── analytics/
│   │   ├── product_value.py           # TSA VAI rankings & strategic quadrants
│   │   ├── state_diagnostics.py       # Typologies, SDG metrics (TEY, EPR, DVR), correlations
│   │   ├── panel_econometrics.py      # Fixed-Effects econometrics (Model 1 DTS & Model 2 Operations)
│   │   └── gravity_corridor_model.py  # Spatial gravity model, panel estimation & out-of-sample validation
│   ├── network/
│   │   └── corridor_network.py        # 4-tier corridor network & HHI concentration
│   ├── scenarios/
│   │   └── simulator.py               # Deterministic simulator with 2025 hotel capacity checks
│   ├── duckdb_mcp_server.py           # Native FastMCP server for DuckDB
│   ├── jupyter_mcp_server.py          # Native FastMCP server for Jupyter execution
│   └── validation/
│       ├── test_tsa_accounting.py     # 100% TSA formula verification
│       └── test_state_and_corridors.py# Complete test suite (Stages A–F, operations & capacity)
└── .agents/skills/                    # Custom Antigravity domain skills
    ├── tsa-tourism-economics/
    ├── malaysia-geo-standards/
    ├── data-pipeline-validation/
    ├── tourism-corridor-scenarios/
    ├── tourism-econometrics-ml/
    └── sustainable-tourism-sdg-metrics/
```

### Analytical Tables in `tourism_data.duckdb` (22 Tables)
1. `tourism_product_year` (88 rows) — TSA supply, GVA, ITC, tourism ratios, VAI (2015–2025).
2. `tsa_macro_year` (11 rows) — TDGVA, TDGDP, employment, macro shares.
3. `product_value_summary` (8 rows) — Pre/Post-COVID medians, CVs, strategic quadrants.
4. `state_year` (16 rows) — 2025 state profiles with typologies and SDG indicators.
5. `state_granular_profile` (16 rows) — Commercial lodging vs. unpaid VFR share, household income brackets.
6. `state_panel_year` (126 rows) — 2018–2025 balanced panel (100% non-null AOR, rooms, domestic/foreign guests).
7. `hotel_operations_annual` (160 rows) — 2016–2025 complete annual AOR, hotel & room supply, guests.
8. `homestay_operations_annual` (28 rows) — 2023–2024 community homestay operators, rooms, income, guests.
9. `accommodation_capacity` (16 rows) — 2025 actual operations baseline + room inventory.
10. `panel_regression_summary` (6 rows) — Fixed-effects regression models (Model 1 & Model 2).
11. `state_recovery_trajectory` (16 rows) — 2019 vs. 2025 structural recovery patterns.
12. `state_driver_regression_summary` (8 rows) — Cross-sectional OLS driver models.
13. `state_diagnostics_correlations` (9 rows) — Spearman rank correlations.
14. `origin_destination` (256 rows) — Directed 16x16 tourist flow matrix (2025 baseline).
15. `origin_destination_panel` (2,048 rows) — 2018–2025 multi-year directed flow matrix.
16. `destination_concentration` (16 rows) — 2025 feeder dominance and HHI concentration tiers.
17. `destination_concentration_panel` (128 rows) — 2018–2025 longitudinal HHI concentration.
18. `corridor_classification` (240 rows) — Inter-state corridor strategic tiers.
19. `corridor_opportunity_gap` (240 rows) — Ranked incremental opportunity with capacity constraints.
20. `corridor_gravity_model_summary` (7 rows) — Multi-year gravity parameters (Panel, Pre-COVID, Post-Recovery).
21. `corridor_gravity_predictions` (240 rows) — 2025 corridor actual vs gravity-expected flows.
22. `corridor_gravity_validation` (1 row) — Out-of-sample validation metrics (2018–2024 train $\rightarrow$ 2025 test).

---

## 6. Quickstart & Pipeline Execution

```bash
# 1. Ingest Data Sources
python src/ingestion/tsa_parser.py
python src/ingestion/state_parser.py
python src/ingestion/multi_year_state_parser.py
python src/ingestion/granular_dts_parser.py
python src/ingestion/mytourism_kpi_parser.py
python src/ingestion/od_panel_parser.py

# 2. Run Analytics & Econometric Pipelines
python src/analytics/product_value.py
python src/network/corridor_network.py
python src/analytics/panel_econometrics.py
python src/analytics/gravity_corridor_model.py
python src/analytics/state_diagnostics.py

# 3. Run Complete Validation Suite
python src/validation/test_tsa_accounting.py
python src/validation/test_state_and_corridors.py
```
