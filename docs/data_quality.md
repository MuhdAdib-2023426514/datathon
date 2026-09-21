# Data Quality & Verification Audit Standard
## Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

**Authoritative Standard**: Antigravity Data Science & Economics Team  
**Verification Framework**: Automated Execution via `src/validation/data_quality_report.py`  
**Overall Database Audit Status**: **100% PASS** across all core relational entities.

---

## 1. Primary Key Uniqueness & Referential Integrity

Primary key uniqueness was asserted across all primary analytical tables in `data/processed/tourism_data.duckdb`. Zero duplicate records exist.

| Table | Primary Key Definition | Record Count | Duplicate Violations | Audit Status |
| :--- | :--- | :---: | :---: | :---: |
| `tourism_product_year` | `(product_id, year)` | 88 | 0 | **PASS** |
| `tsa_macro_year` | `(year)` | 11 | 0 | **PASS** |
| `state_year` | `(state, year)` | 16 | 0 | **PASS** |
| `state_panel_year` | `(state, year)` | 126 | 0 | **PASS** |
| `hotel_operations_annual` | `(state, year)` | 160 | 0 | **PASS** |
| `origin_destination` | `(origin, destination, year)` | 256 | 0 | **PASS** |
| `origin_destination_panel` | `(origin, destination, year)` | 2,048 | 0 | **PASS** |
| `destination_concentration` | `(destination, year)` | 16 | 0 | **PASS** |
| `corridor_opportunity_gap` | `(origin, destination)` | 240 | 0 | **PASS** |

---

## 2. Domain Range & Logical Constraint Verification

All domain boundaries and logical inequalities are verified by automated test assertions:

| Table | Metric / Column | Logical Validation Rule | Violations | Audit Status |
| :--- | :--- | :--- | :---: | :---: |
| `tourism_product_year` | `vai` (Structural: 2015–2019, 2023–2025) | $0.0 \le \text{VAI} \le 1.0$ | 0 | **PASS** |
| `tourism_product_year` | `vai` (Disruption: 2020–2022) | Documented MCO lockdown supply collapse | 3 | **DOCUMENTED** |
| `hotel_operations_annual` | `aor_pct` | $0.0 \le \text{AOR} \le 100.0\%$ | 0 | **PASS** |
| `origin_destination` | `tourist_flow_thousands` | $\text{Flow} \ge 0.0$ | 0 | **PASS** |
| `state_panel_year` | `alos_days` | $\text{ALOS} > 0.0$ | 0 | **PASS** |
| `state_year` | `tourists_thousands` vs. `visitors_thousands` | $\text{Tourists} \le \text{Visitors}$ | 0 | **PASS** |
| `state_year` | `mapping_coverage_pct` | $50.0\% < \text{Coverage} \le 100.0\%$ | 0 | **PASS** |
| `state_year` | `tourism_gva_intensity_pct` | $0.0 < \text{Intensity} \le 100.0\%$ | 0 | **PASS** |
| `state_year` | `tourism_economic_yield_per_day_rm` | $\text{TEY} > 0.0$ | 0 | **PASS** |

---

## 3. Official Accounting Disclosures: 2021 MCO Lockdown Anomaly

Per `AGENTS.md Section 7 Stage A` and national accounting methodology:
- During the 2021 Movement Control Order (MCO), three tourism products recorded nominal domestic supply collapsing faster than annual gross value added (which includes ongoing enterprise operating subsidies and fixed asset maintenance).
- This produces mathematical $\text{VAI} > 1.0$ in 2021 for:
  1. *Passenger transport services* ($\text{VAI} = 1.34$)
  2. *Travel agencies and reservation services* ($\text{VAI} = 1.21$)
  3. *Cultural, sports, and recreation services* ($\text{VAI} = 1.15$)
- **Resolution**: Rather than altering official source figures, these records are preserved and documented as lockdown accounting anomalies. Structural conclusions are derived strictly from the pre-COVID (2015–2019) and post-recovery (2023–2025) structural periods.

---

## 4. Missing-Value Policy: Zero-Fabrication Architecture

In compliance with `AGENTS.md Rule 7`:
1. **No Synthetic Fallbacks**: Missing empirical observations remain `null` or `NaN`. They are never filled with arbitrary constants (such as 50.0% AOR or RM 120 spend).
2. **True Zeros vs. Unobserved**: Parsers strictly distinguish true observed numeric `0.0` from unobserved, empty, dash (`-`), or `N/A` cells.
3. **Capacity Protection**: Corridors targeting destinations with unobserved room inventory (e.g., W.P. Putrajaya in specific sub-tables) are assigned `capacity_tier = "Unknown (Capacity Data Unavailable)"` and flagged ineligible in automated budget allocation.

---

## 5. Cryptographic Source Provenance Registry

All 8 primary data streams are cataloged in `data/metadata/source_registry.yaml` and verified with SHA-256 cryptographic checksums:

| Dataset Identifier | Source Publication / Series | Period | Checksum (SHA-256 Prefix) | License |
| :--- | :--- | :---: | :---: | :--- |
| `tsa_macro_and_products` | DOSM Tourism Satellite Account Malaysia | 2015–2025 | `f87968516d00...` | Open Data Malaysia |
| `state_domestic_tourism_2025` | DOSM Domestic Tourism Survey (DTS) State Tables | 2025 | `43fb0f4da9b0...` | Open Data Malaysia |
| `multi_year_state_panel` | DOSM Domestic Tourism Survey Longitudinal Series | 2018–2025 | `d512a201b1a8...` | Open Data Malaysia |
| `motac_hotel_operations` | MOTAC Hotel Performance & Occupancy Statistics | 2016–2025 | `10be0ca35b2e...` | MOTAC Official |
| `motac_homestay_operations` | MOTAC Homestay Performance & Capacity Statistics | 2023–2024 | `11d73c7ebcc4...` | MOTAC Official |
| `dosm_household_income` | DOSM Household Income & Expenditure Survey (HIES) | 2024 | `2a84b0653655...` | Open Data Malaysia |
| `dosm_population_demographics`| DOSM State Population & Demographic Estimates | 2018–2025 | `f8615a133499...` | Open Data Malaysia |
| `dosm_cpi_inflation` | DOSM Consumer Price Index (Base 2025 = 100) | 2015–2025 | `ad4142f3ea90...` | Open Data Malaysia |
