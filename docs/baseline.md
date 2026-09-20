# Baseline Analytical Report

**Project**: Malaysia Tourism Value Optimizer  
**Baseline Date**: 2026-09-20  
**Baseline Commit**: `4a022d6`  
**Status**: Snapshot established prior to Sprint 1 execution

---

## 1. System Environment

- **Operating System**: Linux (Ubuntu 24.04 LTS on WSL2)
- **Python Version**: 3.14.3
- **Node.js Version**: 24.21.0
- **Package Manager**: uv / pip / npm
- **Database**: DuckDB v1.5.5 (`data/processed/tourism_data.duckdb`)
- **Dashboard Framework**: React 18.3.1 + Vite 7.0.0 + Apache ECharts 6.0.0

---

## 2. Test Suite Status

Current unit and validation test suite: **7 passed, 0 failed, 0 errors**.

| Test Module | Tests | Status | Scope |
| :--- | :---: | :---: | :--- |
| `tests/test_accounting_fixtures.py` | 3 | PASS | Pure accounting formulas, VAI, GVA proxy |
| `tests/test_scenario_fixtures.py` | 2 | PASS | Capacity portfolio tiers, decoupled ALOS vs day-trips |
| `tests/test_gravity_fixtures.py` | 2 | PASS | Log-OLS holdouts, PPML non-negative gravity |
| `src/validation/test_tsa_accounting.py` | 1 | PASS | Official TSA table reconciliation (2015–2025) |
| `src/validation/test_state_and_corridors.py` | 1 | PASS | 16-state survey reconciliations and OD flow matrices |

Dashboard Production Build:
- `cd dashboard && npm run build` $\to$ **Exit code 0** (Build duration: 475ms).

---

## 3. Database Inventory (DuckDB)

Total tables: **40 tables** loaded across 2015–2025. Key analytical tables:

| Table Name | Row Count | Temporal Scope | Primary Key |
| :--- | :---: | :---: | :--- |
| `tourism_product_year` | 88 | 2015–2025 (8 products $\times$ 11 years) | `(product_id, year)` |
| `tsa_macro_year` | 11 | 2015–2025 | `(year)` |
| `state_year` | 16 | 2025 snapshot | `(state)` |
| `state_panel_year` | 126 | 2018–2025 (16 states) | `(state, year)` |
| `hotel_operations_annual` | 176 | 2015–2025 (16 states $\times$ 11 years) | `(state, year)` |
| `origin_destination` | 240 | 2025 snapshot (16 $\times$ 15 pairs) | `(origin, destination)` |
| `origin_destination_panel` | 1,680 | 2018–2025 panel flows | `(origin, destination, year)` |
| `destination_concentration` | 16 | 2025 inbound HHI | `(destination)` |
| `corridor_classification` | 240 | 2025 corridor taxonomy | `(origin, destination)` |
| `corridor_opportunity_gap` | 240 | 2025 gravity gap benchmarks | `(origin, destination)` |

---

## 4. Key Analytical Baseline Metrics

### A. National Accounting & TSA (RQ1 & RQ2)
- **Top VAI Product (2025)**: Accommodation Services ($\text{VAI} = 0.8659$, post-recovery median $0.8579$).
- **Food & Beverage Services**: $\text{VAI}_{2025} = 0.3804$, post-recovery median $0.3804$.
- **Shopping**: $\text{VAI}_{2025} = 0.5898$, post-recovery median $0.5901$.
- **Passenger Transport**: $\text{VAI}_{2025} = 0.4496$, post-recovery median $0.4497$.

### B. Econometric Panel Models (RQ3 & RQ4)
- **Model 1 (One-Way State FE)**:
  - $\beta_{\text{ALOS}} = +1.6067$, $t = 8.12$, $p < 0.0001$, within-$R^2 = 0.4859$.
- **Model 2 (Two-Way State + Year FE, Clustered SEs)**:
  - $\beta_{\text{ALOS}} = +0.6628$, robust SE = $0.3972$, $t = 1.67$, $p = 0.0952$ (95% CI: $[-0.1157, 1.4413]$).
  - Highlights sensitivity of ALOS elasticity when controlling for nationwide macro shocks.

### C. Spatial Gravity Models (RQ6)
- **Log-OLS Model**:
  - Distance friction $\beta_{\ln(\text{dist})} = -0.6031$.
  - In-sample log-$R^2 = 0.7092$; Out-of-sample levels predictive $R^2 = 0.4863$; Spearman $r = 0.7672$ ($N = 1,650$).
- **PPML Model (Silva & Tenreyro 2006)**:
  - Distance friction $\beta_{\ln(\text{dist})} = -0.4648$.
  - Out-of-sample levels predictive $R^2 = 0.5177$; levels correlation $r = 0.8120$.

### D. Market Concentration (RQ5)
- **Interstate Origin HHI**: Excludes intra-state residents (e.g. Sabah = 1,449.92, Diversified).
- **All-Origin HHI**: Includes intra-state residents (e.g. Sabah = 5,746.95, reflecting 75.22% intra-Sabah local excursion/travel).

### E. Scenario Simulation & Capacity (RQ7)
- Decoupled corridor stay extension vs destination excursionist conversion.
- 4 Capacity tiers: Optimal (<70%), Moderate (70–80%), High Saturation (>80–100%), Severe Physical Deficit (>100%).

---

## 5. Saved Baseline Files in `artifacts/baseline/`

1. `tsa_product_ranking.csv` (88 rows)
2. `state_metrics.csv` (16 rows)
3. `panel_coefficients.csv` (8 rows)
4. `gravity_coefficients.csv` (6 rows)
5. `gravity_predictions.csv` (240 rows)
6. `corridor_classifications.csv` (240 rows)
7. `scenario_examples.json` (Formatted baseline scenarios)
8. `model_metrics.json` (Combined model performance metrics)
