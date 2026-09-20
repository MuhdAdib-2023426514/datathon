# Data Dictionary

**Project**: Malaysia Tourism Value Optimizer  
**Last Updated**: 2026-09-21

---

## 1. Core Analytical Tables

### `tourism_product_year`

| Field | Type | Unit | Description |
| :--- | :---: | :---: | :--- |
| `product_id` | string | — | TSA product identifier (e.g., `accommodation`, `food_beverage`) |
| `year` | int | — | Reference year (2015–2025) |
| `itc` | float | RM Million | Internal Tourism Consumption |
| `domestic_supply` | float | RM Million | Total domestic supply at basic prices |
| `gva` | float | RM Million | Gross Value Added at basic prices |
| `tourism_ratio` | float | ratio [0,1] | Share of supply consumed by visitors |
| `vai` | float | ratio [0,1] | Value-Added Intensity = GVA / DomesticSupply |
| `estimated_tourism_gva` | float | RM Million | ITC × VAI (analytical proxy) |
| `data_status` | string | — | `official`, `preliminary`, `estimate`, `revised` |

---

### `state_year`

| Field | Type | Unit | Description |
| :--- | :---: | :---: | :--- |
| `state` | string | — | Malaysian state name (16 states + FTs) |
| `year` | int | — | Reference year |
| `visitors` | float | thousands | Total visitors (tourists + excursionists) |
| `tourists` | float | thousands | Overnight tourists |
| `excursionists` | float | thousands | Same-day visitors |
| `trips` | float | thousands | Total trips |
| `total_expenditure` | float | RM Million | Total domestic tourism expenditure |
| `accommodation_expenditure` | float | RM Million | Accommodation component |
| `food_expenditure` | float | RM Million | Food & Beverage component |
| `transport_expenditure` | float | RM Million | Transport component |
| `shopping_expenditure` | float | RM Million | Shopping component |
| `recreation_expenditure` | float | RM Million | Recreation & entertainment |
| `alos` | float | days | Average Length of Stay |
| `aor_pct` | float | % [0,100] | Average Occupancy Rate |
| `spend_per_night` | float | RM | Accommodation expenditure per tourist-night |
| `visitor_days` | float | thousands | Tourists × ALOS + Excursionists |
| `tey_rm_per_day` | float | RM/day | Tourism Expenditure Yield |
| `tvay_rm_per_day` | float | RM/day | Tourism Value-Added Yield |
| `real_total_expenditure` | float | RM Million | Constant 2025 RM deflated |
| `real_accommodation_expenditure` | float | RM Million | Constant 2025 RM deflated |

---

### `origin_destination`

| Field | Type | Unit | Description |
| :--- | :---: | :---: | :--- |
| `origin` | string | — | Origin state |
| `destination` | string | — | Destination state |
| `year` | int | — | Reference year |
| `tourist_flow_thousands` | float | thousands | Bilateral tourist flow |
| `distance_km` | float | km | Centroid-to-centroid distance |
| `cross_region_int` | int | 0/1 | Peninsular-Borneo crossing indicator |

---

### `corridor_opportunity_gap`

| Field | Type | Unit | Description |
| :--- | :---: | :---: | :--- |
| `origin` | string | — | Origin state |
| `destination` | string | — | Destination state |
| `actual_flow_thousands` | float | thousands | Observed 2025 flow |
| `expected_flow_thousands` | float | thousands | PPML gravity-predicted flow |
| `performance_ratio` | float | ratio | Actual / Expected |
| `model_gap_category` | string | — | Below / Near / Above model expected |
| `capacity_headroom_pct` | float | % | 100% − AOR |
| `dest_spend_per_night_rm` | float | RM | Destination spend/night |
| `dest_tvay_rm_per_day` | float | RM/day | Destination TVAY |
| `is_pareto_optimal` | bool | — | Pareto frontier membership |
| `pareto_rank` | int | — | Pareto front rank (1 = optimal) |
| `composite_opportunity_score` | float | [0,100] | Multi-dimensional score |

---

### `destination_concentration`

| Field | Type | Unit | Description |
| :--- | :---: | :---: | :--- |
| `destination` | string | — | Destination state |
| `origin_hhi` | float | [0,10000] | Herfindahl-Hirschman Index |
| `top_origin_share_pct` | float | % | Largest feeder market share |
| `top_3_origin_share_pct` | float | % | Top-3 feeder cumulative share |
| `meaningful_origin_count` | int | count | Origins with ≥ 5% share |
| `concentration_class` | string | — | Diversified / Moderate / Highly Concentrated |

---

## 2. Derived Metrics & Formulas

| Metric | Formula | Unit |
| :--- | :--- | :---: |
| Value-Added Intensity (VAI) | GVA / DomesticSupply | ratio |
| Visitor-Days | Tourists × ALOS + Excursionists | days |
| Tourism Expenditure Yield (TEY) | TotalExpenditure / VisitorDays | RM/day |
| Accommodation Yield | AccomExpenditure / (Tourists × ALOS) | RM/night |
| Tourism GVA Intensity | EstimatedTourismGVA / MappedExpenditure | % |
| Mapping Coverage | MappedExpenditure / TotalExpenditure | % |
| Tourism Value-Added Yield (TVAY) | EstimatedTourismGVA / VisitorDays | RM/day |
| Real Value (Constant 2025 RM) | NominalValue × (CPI₂₀₂₅ / CPIₜ) | RM |
| HHI | Σ(share²) × 10,000 | index |

---

## 3. Data Status Codes

| Code | Meaning |
| :---: | :--- |
| `official` | Published DOSM final release |
| `preliminary` | Published DOSM preliminary release (e.g., 2025p) |
| `estimate` | Official estimate pending full enumeration |
| `revised` | Previously published, subsequently revised |
| `derived` | Computed from official data using accounting identities |
| `model_estimate` | Output of econometric or statistical model |
| `scenario_assumption` | User/analyst-specified policy parameter |
