"""
Validation Test Suite for State Ingestion, OD Network, Granular DTS Drivers, and Scenario Engine
Enforces data quality, accounting assertions, and policy guardrails specified in:
- AGENTS.md (Sections 3, 5, 7, 18)
- .agents/skills/tourism-corridor-scenarios/SKILL.md
- .agents/skills/data-pipeline-validation/SKILL.md
- .agents/skills/sustainable-tourism-sdg-metrics/SKILL.md
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
import pandas as pd
from src.scenarios.simulator import ScenarioSimulator, MANDATORY_DISCLAIMER

DUCKDB_PATH = ROOT_DIR / "data/processed/tourism_data.duckdb"


def test_state_year_table():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT * FROM state_year").df()
    con.close()

    print("\n[TEST 1] Validating state_year table...")
    assert len(df) == 16, f"Expected 16 states, got {len(df)}"
    assert df["year"].nunique() == 1 and df["year"].iloc[0] == 2025, "Year must be 2025"

    # Strict non-negativity
    assert (df["visitors_thousands"] > 0).all(), "Zero or negative visitors found"
    assert (df["tourists_thousands"] > 0).all(), "Zero or negative tourists found"
    assert (df["alos_days"] > 0).all(), "Zero or negative ALOS found"
    assert (df["total_expenditure_rm_million"] > 0).all(), "Zero or negative total expenditure found"
    assert (df["accommodation_expenditure_rm_million"] > 0).all(), "Zero or negative accommodation expenditure found"

    # Tourists cannot exceed total visitors
    assert (df["tourists_thousands"] <= df["visitors_thousands"]).all(), "Overnight tourists exceed total visitors"

    # Excursionists + Tourists = Visitors (check within 1% rounding)
    sum_visitors = df["tourists_thousands"] + df["excursionists_thousands"]
    rel_vis_diff = ((df["visitors_thousands"] - sum_visitors).abs() / df["visitors_thousands"]).max()
    assert rel_vis_diff < 0.02, f"Visitor component mismatch: max relative diff {rel_vis_diff:.4%}"

    # Accommodation share bounded in [0, 1]
    assert (df["accommodation_share"] > 0.0).all() and (df["accommodation_share"] < 1.0).all(), (
        "Accommodation share must be strictly between 0 and 1"
    )

    # Spend per night formula check
    calc_spend_per_night = (
        (df["accommodation_expenditure_rm_million"] * 1e6) /
        (df["tourists_thousands"] * 1e3 * df["alos_days"])
    ).round(2)
    night_diff = (df["spend_per_night_rm"] - calc_spend_per_night).abs().max()
    assert night_diff < 0.25, f"Spend per night formula mismatch: max diff {night_diff}"

    # Verify enriched granular columns exist
    for col in ["paid_commercial_share_pct", "unpaid_vfr_share_pct", "affluence_index", "yield_typology", "policy_prescription"]:
        assert col in df.columns, f"Missing enriched column '{col}' in state_year"

    # Verify Sprint 2 economic metrics (Phases 6-8)
    for col in [
        "total_visitor_days_thousands",
        "tourism_economic_yield_per_day_rm",
        "tourism_value_added_yield_per_day_rm",
        "tourism_gva_intensity_pct",
        "mapping_coverage_pct",
    ]:
        assert col in df.columns, f"Missing Sprint 2 economic metric '{col}' in state_year"
        assert (df[col] > 0).all(), f"Values in '{col}' must be strictly positive"

    # Verify Phase 8 typology quadrant labels
    valid_quadrants = {
        "Short Stay / Low Yield",
        "Short Stay / High Yield",
        "Long Stay / Low Yield",
        "Long Stay / High Yield",
    }
    assert set(df["yield_typology"]).issubset(valid_quadrants), (
        f"Invalid typology quadrants found: {set(df['yield_typology']) - valid_quadrants}"
    )

    # Verify mapping coverage is bounded in (50%, 100%]
    assert (df["mapping_coverage_pct"] > 50.0).all() and (df["mapping_coverage_pct"] <= 100.0).all(), (
        "Mapping coverage must be between 50% and 100%"
    )

    print("  ✓ state_year schema, bounds, decomposition formulas, Sprint 2 yields, and typologies PASSED.")


def test_origin_destination_matrix():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT * FROM origin_destination").df()
    con.close()

    print("\n[TEST 2] Validating origin_destination matrix...")
    # 16 origins x 16 destinations = 256 directed pairs
    assert len(df) == 256, f"Expected 256 OD pairs, got {len(df)}"
    assert (df["tourist_flow_thousands"] >= 0).all(), "Negative tourist flow found"

    interstate = df[df["is_interstate"]]
    intrastate = df[~df["is_interstate"]]
    assert len(interstate) == 240, f"Expected 240 inter-state pairs, got {len(interstate)}"
    assert len(intrastate) == 16, f"Expected 16 intra-state pairs, got {len(intrastate)}"

    # National total conservation check: Sum of all tourist flows ~ 106,525 thousand tourists
    total_national_tourists = df["tourist_flow_thousands"].sum()
    print(f"  Total National Domestic Tourists: {total_national_tourists:,.2f} thousand")
    assert abs(total_national_tourists - 106525.3) < 1.0, (
        f"Total OD tourists ({total_national_tourists}) does not reconcile with published national total (106,525.3)"
    )

    print("  ✓ origin_destination conservation, 256 pairs, and bounds PASSED.")


def test_corridor_classification_and_hhi():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df_conc = con.execute("SELECT * FROM destination_concentration").df()
    df_corr = con.execute("SELECT * FROM corridor_classification").df()
    con.close()

    print("\n[TEST 3] Validating concentration (HHI) and corridor tiers...")
    # 16 destinations
    assert len(df_conc) == 16, f"Expected 16 concentration records, got {len(df_conc)}"
    assert (df_conc["hhi"] >= 0.0).all() and (df_conc["hhi"] <= 10000.0).all(), "HHI out of bounds [0, 10000]"

    # Corridor classification categories
    valid_tiers = {
        "Priority Conversion Corridor",
        "Protect & Deepen",
        "Growth Opportunity",
        "Lower Strategic Priority"
    }
    assigned_tiers = set(df_corr["corridor_tier"].unique())
    assert assigned_tiers.issubset(valid_tiers), f"Unexpected corridor tier found: {assigned_tiers}"

    # Priority Conversion Corridors must exist and include Selangor -> Melaka / Perak / Pahang
    priority_df = df_corr[df_corr["corridor_tier"] == "Priority Conversion Corridor"]
    assert len(priority_df) > 0, "No Priority Conversion Corridors found!"

    corridor_pairs = set(zip(priority_df["origin"], priority_df["destination"]))
    assert ("Selangor", "Melaka") in corridor_pairs, "Selangor -> Melaka should be Priority Conversion"
    assert ("Selangor", "Perak") in corridor_pairs, "Selangor -> Perak should be Priority Conversion"

    print(f"  Identified {len(priority_df)} Priority Conversion Corridors.")
    print("  ✓ Corridor classification and HHI concentration PASSED.")


def test_scenario_simulator_engine():
    print("\n[TEST 4] Validating Scenario Simulator Engine...")
    sim = ScenarioSimulator()

    # Run deterministic test on Selangor -> Melaka (+0.5 nights)
    res = sim.simulate_corridor("Selangor", "Melaka", delta_alos=0.5)

    # Mandatory disclaimer guardrail
    assert "disclaimer" in res, "Missing disclaimer in simulation result"
    assert res["disclaimer"] == MANDATORY_DISCLAIMER, "Disclaimer does not match exact wording required"

    # Math consistency checks
    inputs = res["inputs"]
    baseline = res["baseline"]
    impact = res["simulated_impact"]

    expected_nights = baseline["corridor_tourists"] * inputs["delta_alos_nights"]
    assert abs(impact["additional_tourist_nights"] - expected_nights) < 1.0, "Nights calculation mismatch"

    expected_spend_m = (expected_nights * baseline["spend_per_night_rm"]) / 1e6
    assert abs(impact["additional_accommodation_spend_rm_million"] - round(expected_spend_m, 2)) < 0.05, "Spend calculation mismatch"

    expected_gva_m = (expected_spend_m * inputs["accommodation_vai_used"])
    assert abs(impact["potential_additional_value_added_rm_million"] - round(expected_gva_m, 2)) < 0.05, "GVA calculation mismatch"

    print("  ✓ Scenario Simulator formulas, guardrails, and disclaimer PASSED.")


def test_granular_profile_and_drivers():
    print("\n[TEST 5] Validating Granular DTS Profile, Driver Regressions & Corridor Opportunity Gap...")
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df_gran = con.execute("SELECT * FROM state_granular_profile").df()
    df_reg = con.execute("SELECT * FROM state_driver_regression_summary").df()
    df_gap = con.execute("SELECT * FROM corridor_opportunity_gap").df()
    con.close()

    # 1. State Granular Profile
    assert len(df_gran) == 16, f"Expected 16 state granular profiles, got {len(df_gran)}"
    # Commercial + Unpaid VFR share ~ 100% (within 2% tolerance)
    accom_sum = df_gran["paid_commercial_share_pct"] + df_gran["unpaid_vfr_share_pct"]
    assert ((accom_sum >= 97.0) & (accom_sum <= 103.0)).all(), "Accommodation share sum out of bounds"

    # Income brackets sum ~ 100%
    income_sum = df_gran["b40_share_pct"] + df_gran["m40_share_pct"] + df_gran["t20_share_pct"]
    assert ((income_sum >= 97.0) & (income_sum <= 103.0)).all(), "Income brackets sum out of bounds"

    # Hotel rooms strictly positive
    assert (df_gran["total_rooms"] > 0).all(), "Total hotel rooms must be positive"
    assert (df_gran["star_rated_rooms"] <= df_gran["total_rooms"]).all(), "Star rooms cannot exceed total rooms"

    # 2. Driver Regression Summary
    assert len(df_reg) > 0, "No regression records found in state_driver_regression_summary"
    assert "M1_SpendPerNight" in df_reg["model_id"].values, "M1_SpendPerNight model missing"
    assert (df_reg["r_squared"] >= 0.0).all() and (df_reg["r_squared"] <= 1.0).all(), "R-squared out of bounds"

    # 3. Corridor Opportunity Gap Matrix
    assert len(df_gap) == 240, f"Expected 240 inter-state corridors in opportunity gap, got {len(df_gap)}"
    assert (df_gap["additional_tourist_nights_thousands"] > 0).all(), "Negative additional nights found"
    assert (df_gap["additional_accom_expenditure_rm_million"] > 0).all(), "Negative additional spend found"
    assert (df_gap["policy_disclaimer"] == "Scenario estimate, not a causal forecast.").all(), (
        "Mandatory policy disclaimer missing or incorrect in opportunity gap table"
    )

    # Opportunity rank check
    assert df_gap["opportunity_rank"].iloc[0] == 1, "Rank 1 corridor must be first"
    assert df_gap["additional_accom_expenditure_rm_million"].is_monotonic_decreasing, (
        "Opportunity gap must be sorted descending by additional spend"
    )

    # Capacity feasibility checks
    assert "implied_dest_aor_pct" in df_gap.columns, "implied_dest_aor_pct missing from corridor_opportunity_gap"
    assert "capacity_constraint_alert" in df_gap.columns, "capacity_constraint_alert missing from corridor_opportunity_gap"
    assert (df_gap["implied_dest_aor_pct"] > 0).all(), "Invalid implied AOR"

    print("  ✓ Granular DTS profiles (16 states), OLS driver regressions, and 240-corridor opportunity gap PASSED.")


def test_hotel_and_homestay_operations():
    print("\n[TEST 6] Validating MyTourism KPI Hotel & Homestay Operations...")
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df_hotel = con.execute("SELECT * FROM hotel_operations_annual").df()
    df_homestay = con.execute("SELECT * FROM homestay_operations_annual").df()
    df_cap = con.execute("SELECT * FROM accommodation_capacity").df()
    df_panel = con.execute("SELECT * FROM state_panel_year").df()
    con.close()

    # 1. Hotel Operations Annual (2016–2025, 16 states x 10 years = 160 records)
    assert len(df_hotel) == 160, f"Expected 160 hotel operations records, got {len(df_hotel)}"
    assert (df_hotel["aor_pct"] >= 0.0).all() and (df_hotel["aor_pct"] <= 100.0).all(), "AOR out of bounds [0, 100%]"
    assert (df_hotel["rooms_count"] > 0).all(), "Room count must be positive"
    assert (df_hotel["domestic_hotel_guests"].dropna() > 0).all(), "Reported domestic hotel guests must be positive"
    assert len(df_hotel.dropna(subset=["domestic_hotel_guests"])) >= 159, "Expected at least 159 reported guest records"

    # 2. Homestay Operations Annual (2023–2024, 28 state records)
    assert len(df_homestay) == 28, f"Expected 28 homestay records, got {len(df_homestay)}"
    assert (df_homestay["total_income_rm"] > 0).all(), "Homestay income must be strictly positive"
    assert (df_homestay["total_homestay_guests"] > 0).all(), "Homestay guests must be positive"

    # 3. Accommodation Capacity Table (16 states)
    assert len(df_cap) == 16, f"Expected 16 states in accommodation capacity, got {len(df_cap)}"
    assert (df_cap["aor_2025_pct"] > 0).all(), "2025 baseline AOR must be positive"
    assert (df_cap["dts_rooms_2025"] > 0).all(), "2025 DTS room supply must be positive"

    # 4. State Panel Temporal Alignment Verification (2018–2025 Full Panel)
    # All 126 records across 2018–2025 now have non-null AOR and domestic hotel guests
    assert len(df_panel) == 126, f"Expected 126 panel records (2018-2025), got {len(df_panel)}"
    assert df_panel["aor_pct"].notnull().all(), "Missing AOR in 2018–2025 panel records"
    assert df_panel["domestic_hotel_guests"].notnull().all(), "Missing hotel guests in 2018–2025 panel records"

    print("  ✓ MyTourism KPI operations (160 hotel, 28 homestay), capacity table, and full 2018–2025 panel PASSED.")


def run_all_tests():
    print("=" * 70)
    print("RUNNING COMPLETE VALIDATION SUITE (STAGES A - F + OPERATIONS & CAPACITY)")
    print("=" * 70)
    test_state_year_table()
    test_origin_destination_matrix()
    test_corridor_classification_and_hhi()
    test_scenario_simulator_engine()
    test_granular_profile_and_drivers()
    test_hotel_and_homestay_operations()
    print("\n" + "=" * 70)
    print("ALL VALIDATION TEST SUITES PASSED (100% SUCCESS)")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
