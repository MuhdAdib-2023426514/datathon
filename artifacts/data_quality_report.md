# Data Quality & Verification Audit Report

- **Generated At**: 2026-09-21 05:10:51 UTC
- **Database**: `/home/muhammad_adib/dosm/data/processed/tourism_data.duckdb`
- **Overall Verification Status**: **PASS**

## 1. Primary Key Uniqueness Verification

| Table | Primary Keys | Duplicates | Status |
| :--- | :--- | :---: | :---: |
| `tourism_product_year` | `product_id, year` | 0 | **PASS** |
| `tsa_macro_year` | `year` | 0 | **PASS** |
| `state_year` | `state, year` | 0 | **PASS** |
| `state_panel_year` | `state, year` | 0 | **PASS** |
| `hotel_operations_annual` | `state, year` | 0 | **PASS** |
| `origin_destination` | `origin, destination, year` | 0 | **PASS** |
| `origin_destination_panel` | `origin, destination, year` | 0 | **PASS** |
| `destination_concentration` | `destination, year` | 0 | **PASS** |
| `corridor_classification` | `origin, destination, year` | 0 | **PASS** |

## 2. Domain Range & Constraint Checks

| Table | Metric | Rule | Violations | Status |
| :--- | :--- | :--- | :---: | :---: |
| `tourism_product_year` | `vai (structural: 2015-2019, 2023-2025)` | `0.0 <= vai <= 1.0` | 0 | **PASS** |
| `tourism_product_year` | `vai (disruption: 2020-2022)` | `Documented MCO lockdown accounting anomaly` | 3 | **DOCUMENTED** |
| `hotel_operations_annual` | `aor_pct` | `0.0 <= aor_pct <= 100.0` | 0 | **PASS** |
| `origin_destination` | `tourist_flow_thousands` | `tourist_flow_thousands >= 0.0` | 0 | **PASS** |
| `state_panel_year` | `alos_days` | `alos_days > 0.0` | 0 | **PASS** |
| `state_year` | `mapping_coverage_pct (Sprint 2)` | `0.0 <= mapping_coverage_pct <= 100.0` | 0 | **PASS** |
| `state_year` | `tourism_gva_intensity_pct (Sprint 2)` | `0.0 <= tourism_gva_intensity_pct <= 100.0` | 0 | **PASS** |
| `state_year` | `tourism_economic_yield_per_day_rm (TEY)` | `TEY > 0.0` | 0 | **PASS** |

## 3. Core Table Inventory

| Table Name | Row Count |
| :--- | :---: |
| `accommodation_capacity` | 16 |
| `accommodation_drivers_meta` | 1 |
| `accommodation_drivers_summary` | 6 |
| `corridor_classification` | 240 |
| `corridor_classification_panel` | 1,920 |
| `corridor_gravity_model_summary` | 4 |
| `corridor_gravity_predictions` | 240 |
| `corridor_gravity_predictions_panel` | 1,920 |
| `corridor_gravity_validation` | 4 |
| `corridor_opportunity_gap` | 240 |
| `destination_concentration` | 16 |
| `destination_concentration_panel` | 128 |
| `homestay_operations_annual` | 28 |
| `hotel_operations_annual` | 160 |
| `meta` | 1 |
| `national_household_income_panel` | 91 |
| `national_income_class_panel` | 63 |
| `origin_destination` | 256 |
| `origin_destination_panel` | 2,048 |
| `panel_influence_diagnostics` | 126 |
| `panel_leave_one_out` | 80 |
| `panel_regression_summary` | 11 |
| `product_value_summary` | 8 |
| `sdg_sustainable_metrics` | 126 |
| `state_clusters` | 16 |
| `state_demographics` | 16 |
| `state_demographics_annual` | 128 |
| `state_diagnostics_correlations` | 9 |
| `state_driver_regression_summary` | 8 |
| `state_granular_profile` | 16 |
| `state_hotel_star_inventory` | 126 |
| `state_household_income_annual` | 128 |
| `state_household_income_panel` | 208 |
| `state_panel_year` | 126 |
| `state_purpose_of_visit_panel` | 126 |
| `state_recovery_trajectory` | 16 |
| `state_top_destinations` | 640 |
| `state_top_districts` | 465 |
| `state_tourist_income_panel` | 126 |
| `state_year` | 16 |
| `tourism_product_year` | 88 |
| `tsa_macro_year` | 11 |

## 4. Missing Value Profile in Core Tables

### `tourism_product_year` (N=88)
All required fields 100% complete.

### `state_year` (N=16)
All required fields 100% complete.

### `state_panel_year` (N=126)
| Column | Missing Rate (%) |
| :--- | :---: |
| `homestay_rooms` | 77.8% |
| `homestay_operators` | 77.8% |

### `origin_destination` (N=256)
All required fields 100% complete.

### `hotel_operations_annual` (N=160)
| Column | Missing Rate (%) |
| :--- | :---: |
| `domestic_hotel_guests` | 0.6% |
| `foreign_hotel_guests` | 0.6% |
| `total_hotel_guests` | 0.6% |
| `foreign_guest_share_pct` | 0.6% |

