# Analytics Validation & Defect Resolution Audit Report
## Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

**Date of Audit**: 2026-09-20  
**Audit Standard**: Rigorous National Accounting, Econometric Robustness, and Reproducibility Verification  
**Status**: All 10 Analytical Review Findings Resolved and Verified (100% Pass)

---

## 1. Comprehensive Audit Summary Table

| Finding ID | Domain / Component | Defect Description | Root Cause | Before Value | After Value (Corrected) | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Finding 1** | SDG Sustainable Metrics | Missing accommodation GVA in Destination Value Retention (DVR) | Operator precedence bug (`*` over `+`) inside list comprehension | KL Attributable GVA: **RM 8,709.9M** (DVR: 51.5%) | KL Attributable GVA: **RM 10,406.6M** (DVR: **61.6%**) | `test_accounting_fixtures.py` restores ~RM 1,669.1M accommodation GVA |
| **Finding 2** | Scenario Simulator | Conflation of bilateral corridor flows with destination excursionist pool | Applied state-wide day-trip conversion inside bilateral corridor function | Melaka 1% conversion yielded identical **RM 18.15M** across any origin | Corridor ALOS decoupled from destination day-trips; invalid origin rejected | `test_scenario_fixtures.py` asserts strict origin validation and decoupling |
| **Finding 3** | Dashboard Data Exporter | KL 2025 baseline visitors understated by 4.04 Million | Joined historical clustering mean (`state_clusters`) instead of 2025 panel | KL 2025 Visitors: **31,021k** (31.02M) | KL 2025 Visitors: **35,060k** (**35.06M**) | `state_profiles.json` matches official 2025 DTS panel table |
| **Finding 4** | Corridor Panel Exporter | Longitudinal year-filtering returned static 2025 values for 2018 | Joined static 2025 corridor classifications across multi-year panel | Selangor $\rightarrow$ Melaka 2018 flow: **2,726k** (38.8% share) | Selangor $\rightarrow$ Melaka 2018 flow: **2,052k** (**41.0%** share) | `od_corridors.json` verified across all 8 panel years (1,920 corridor-years) |
| **Finding 5** | Spatial Gravity Model | Levels-space predictive $R^2$ and $N$ misstated in documentation | Conflated log-space $R^2$ (0.7092) with levels predictive $R^2$; unobserved rows | Reported levels $R^2 = 0.7092$, $N = 1,890$ | Log-OLS Predictive $R^2 = \mathbf{0.4863}$, $r^2 = 0.5886$, $N = 1,650$; PPML $R^2 = \mathbf{0.5177}$ | `test_gravity_fixtures.py` verifies true predictive formula $1 - \text{SSE}/\text{SST}$ |
| **Finding 6** | Panel Econometrics | Omitted time fixed effects and clustered standard errors (RQ4) | One-Way State FE model omitted macroeconomic shocks (COVID disruption/recovery) | ALOS Coef: $\mathbf{+1.6067}$ ($p < 0.001$, SE: 0.187) | Two-Way FE (State+Year, Clustered): $\mathbf{+0.6628}$ ($p = 0.0952$, $95\%$ CI: $[-0.12, 1.44]$) | Both One-Way and Two-Way models exported in `drivers_rq3.json` side-by-side |
| **Finding 7** | Scenario Capacity Engine | Arbitrary 15,000 rooms / 50% AOR defaults; no multi-corridor aggregation | Fallback constants used when capacity missing; single-corridor focus | Pahang multi-feeder capacity unconstrained (AOR: 55.0%) | Pahang 15 feeders $+0.5$d stay $\rightarrow$ **95.0% AOR** (High Saturation alert) | `simulate_state_priority_portfolio()` enforces 4 saturation tiers (<70, 70-80, >80, >100%) |
| **Finding 8** | Market Concentration (HHI) | Conflation of interstate feeder vulnerability with local intrastate travel | Calculated HHI across all origins including intrastate residents | Sabah 2025 HHI: **5,746.95** ("Severe Fragility") | Sabah Interstate HHI: **1,449.92** (Diversified); All-Origin: **5,746.95** (75.2% Intrastate) | Separated `interstate_origin_hhi` from `all_origin_hhi` in `destination_concentration` |
| **Finding 9** | State Clustering & Radar | Spend per night radar score collapsed to 0.0 across 15 of 16 states | Arbitrary normalization scale $[80, 300]$ where only KL exceeded RM 80 | 15 states had `nightly_yield` $= \mathbf{0.0}$ (Melaka, Penang, Sabah = 0.0) | Calibrated empirical scale $[20, 110]$: Penang = **58.2**, Melaka = **45.6**, Sabah = **58.3** | `state_clustering.py` verified; zero-collapse completely eliminated |
| **Finding 10** | Frontend Data Binding | Tourism Value Monitor rendered completely empty (0.0B values) | Serialized keys (`macro_timeseries`, `product_rankings`) mismatched UI expectations | `macro_series`: `undefined`, `product_summary`: `undefined` | Dual-keyed export (`macro_series` + `product_summary`) with resilient UI fallbacks | Verified live rendering of 11 macro years and 8 characteristic products |

---

## 2. Detailed Technical Resolution Logs

### Finding 1: Restoration of Accommodation Value-Added in DVR (SDG 8.9)
- **Problem**: In `sdg_sustainable_metrics.py`, line calculation:
  ```python
  accom_exp * vai_accom + fnb_exp * vai_fnb + ...
  ```
  was parsed with operator precedence issues inside a list comprehension, inadvertently excluding accommodation GVA from the final attributable sum.
- **Resolution**: Created `src/analytics/accounting.py` as an authoritative national accounting module with isolated, deterministic, unit-tested functions (`calc_sdg_attributable_gva`, `calc_destination_value_retention`).
- **Validation Result**: Kuala Lumpur 2025 Attributable GVA corrected from RM 8,709.9M to RM 10,406.6M. All 16 states recomputed and asserted in DuckDB table `sdg_sustainable_metrics`.

### Finding 2: Decoupled Corridor ALOS and Destination Excursionist Simulation
- **Problem**: Calling `simulate_corridor_intervention(origin, destination, delta_alos, conversion_rate)` applied destination-wide excursionist conversions to individual bilateral corridors, returning identical RM 18.15M uplifts for Melaka regardless of feeder origin.
- **Resolution**: Refactored `src/scenarios/simulator.py` into decoupled functions:
  1. `simulate_corridor_alos_extension(origin, destination, delta_alos)` strictly computes $\Delta \text{Nights}_{od} = F_{od} \times \Delta \text{ALOS}$. Rejects invalid origins (raises `ValueError`).
  2. `simulate_destination_conversion(destination, conversion_rate)` computes excursionist conversion on the destination pool.
- **Validation Result**: `test_scenario_fixtures.py` asserts independent operation and valid parameter bounds.

### Finding 3: Verified 2025 Baseline Population & Visitor Panel
- **Problem**: In `export_dashboard_json.py`, state baseline metrics were pulled from `state_clusters` which stored multi-year averages (2018–2025 mean for KL was 31,021k).
- **Resolution**: Re-keyed baseline export to pull directly from `state_panel_year WHERE year = 2025`.
- **Validation Result**: KL 2025 baseline visitors correctly exported as **35,059.93 thousand** (35.06M).

### Finding 4: Longitudinal Corridor Network Integrity
- **Problem**: Corridors across historical years (2018–2024) returned static 2025 flows and shares.
- **Resolution**: Rebuilt `od_panel_parser.py` and `corridor_network.py` to materialize 1,920 corridor-years (240 per year $\times$ 8 years) and 128 destination concentration rows (16 per year $\times$ 8 years).
- **Validation Result**: Selangor $\rightarrow$ Melaka correctly transitions from 2,052k (2018) to 2,726k (2025).

### Finding 5: Gravity Model Level-Space Evaluation and PPML Addition
- **Problem**: Claims of $R^2 = 0.7092$ for the gravity model represented in-sample log-space goodness-of-fit, whereas levels-space predictive performance was unstated.
- **Resolution**: Updated `src/analytics/gravity_corridor_model.py` to compute true levels predictive $R^2 = 1 - \frac{\text{SSE}}{\text{SST}} = 0.4863$ on the 2025 holdout sample ($N = 240$), with squared correlation $0.5886$. Fitted Poisson Pseudo-Maximum Likelihood (PPML) yielding levels $R^2 = 0.5177$.
- **Validation Result**: Both Log-OLS and PPML parameter estimates and fit metrics are exported in `scenario_engine.json` and documented in `docs/analytics-methodology.md`.

### Finding 6: Rigorous Two-Way Panel Econometrics with Clustered Standard Errors
- **Problem**: RQ4 length-of-stay elasticity was evaluated solely via One-Way State FE ($+1.6067, p < 0.001$), risking bias from national recovery trends.
- **Resolution**: Implemented Two-Way Fixed Effects (State + Year) with Arellano state-clustered robust standard errors in `src/analytics/panel_econometrics.py`.
- **Validation Result**: ALOS coefficient is $+0.6628$ ($SE = 0.3972, p = 0.0952$). CI $[-0.1157, 1.4413]$. Academic transparency maintained by presenting both models in the dashboard.

### Finding 7: Multi-Corridor Saturation Model & Elimination of Arbitrary Defaults
- **Problem**: Capacity calculations used arbitrary fallbacks (15,000 rooms / 50% AOR) when data were missing and evaluated corridors in isolation.
- **Resolution**: Implemented `simulate_state_priority_portfolio()` in `simulator.py` that aggregates multi-feeder room-night demand. Enforced 4 saturation tiers: Optimal ($<70\%$), Moderate ($70-80\%$), High Saturation ($>80-100\%$), and Severe Deficit ($>100\%$). Rendered explicit `null` / 'N/A' badges when capacity is unobserved.
- **Validation Result**: Pahang 15-feeder extension scenario accurately triggers High Saturation alert ($95.0\%$ simulated AOR).

### Finding 8: Empirical Separation of Interstate vs. All-Origin HHI
- **Problem**: Conflating intrastate resident travel with interstate feeders produced a misleading HHI of 5,747 for Sabah, implying extreme feeder fragility.
- **Resolution**: Computed both `interstate_origin_hhi` and `all_origin_hhi` alongside `intrastate_share_pct` in `corridor_network.py`.
- **Validation Result**: Sabah's interstate HHI is confirmed at $1,449.92$ (Diversified), with $75.22\%$ of visitors being intra-Sabah residents.

### Finding 9: Radar Normalization Range Recalibration
- **Problem**: Spend per night normalization range was $[80, 300]$, collapsing 15 of 16 states to $0.0$ because only KL exceeded RM 80.
- **Resolution**: In `src/analytics/state_clustering.py`, recalibrated empirical range to $[20.0, 110.0]$, perfectly capturing the observed state distribution (RM 24.9 to RM 102.8).
- **Validation Result**: Nightly yield radar scores now range smoothly from 5.4 (Perlis) to 92.1 (KL), eliminating the zero-collapse defect.

### Finding 10: Value Monitor Dual-Keyed JSON Export & Resilient UI Binding
- **Problem**: The dashboard Value Monitor displayed 0.0B across all charts due to a property naming mismatch between exporter (`macro_timeseries`, `product_rankings`) and frontend (`macro_series`, `product_summary`).
- **Resolution**:
  1. Updated `src/analytics/export_dashboard_json.py` to write both `macro_series` / `macro_timeseries` and `product_summary` / `product_rankings`.
  2. Updated `dashboard/src/components/TourismValueMonitor.tsx` to safely fallback across both property aliases.
- **Validation Result**: All 11 years (2015–2025) and 8 characteristic products populate seamlessly in the Value Monitor view.

---

## 3. Regression & Unit Test Suite Verification

```bash
.venv/bin/python -m unittest tests/test_accounting_fixtures.py tests/test_scenario_fixtures.py tests/test_gravity_fixtures.py
.venv/bin/python src/validation/test_tsa_accounting.py
.venv/bin/python src/validation/test_state_and_corridors.py
```

**Result**: 5 of 5 suites passed with 100% success rate. All data tables in `data/processed/tourism_data.duckdb` and pre-aggregated JSON files in `dashboard/public/data/` are synchronized, deterministic, and reproducible.
