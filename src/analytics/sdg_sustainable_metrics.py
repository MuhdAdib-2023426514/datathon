"""
Sustainable Tourism & SDG Economic Metrics Engine
Aligned with UN SDG Target 8.9 (Sustainable Tourism & Local Job Creation)
and Target 12.b (Monitoring Sustainable Development Impacts).

Calculates core economic sustainability dimensions:
  1. Total Visitor-Days Footprint: (Tourists * ALOS) + Excursionists
  2. Tourism Economic Yield per Visitor-Day (TEY, RM/day)
  3. Accommodation Yield per Overnight Night (RM/night)
  4. Tourism GVA Intensity (%): Empirical TSA GVA density of mapped tourism expenditure
  5. Mapping Coverage (%): Share of survey expenditure mapped to empirical TSA VAI
  6. Tourism Value-Added Yield (TVAY, RM/visitor-day): Attributable GVA per visitor-day
  7. Real RM series (Constant 2025 RM) deflated by official DOSM CPI
  8. Excursionist Pressure Ratio (EPR = Excursionists / Overnight Tourists)
  9. Tourism Intensity Ratio (TIR = Total Visitors / Resident Population)
  10. Resident Yield per Household (RYH = Accommodation Spend / Resident Households)
  11. Feeder Concentration HHI (from inbound OD flows)
  12. State Yield Typology (ALOS vs TVAY 4 quadrants)
  13. Policy Diagnosis & Action Classification Matrix

Mandatory Guardrails (AGENTS.md Sections 1, 3, 9, 11 & IMPLEMENTATION_PLAN.md Phases 5-8, 13):
  - Focuses exclusively on the economic dimension of sustainable tourism.
  - Zero arbitrary VAI fallback: Unmapped expenditure is not assumed to have 0.50 VAI.
  - Domestic Value Retention (DVR) replaced with Tourism GVA Intensity.
  - Avoid representing unpaid lodging as total leakage; frame as commercial conversion opportunity.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import duckdb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.analytics.accounting import (
    calc_real_value,
    calc_visitor_days,
    calc_tey,
    calc_accommodation_yield,
    calc_estimated_tourism_gva_state,
    calc_mapping_coverage,
    calc_tourism_gva_intensity,
    calc_tvay,
    classify_state_yield_typology,
)

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

# Empirical Post-Recovery Medians (2023-2025) for core DTS categories
# Explicitly NO 'other': 0.50 fallback per Phase 6.1
FALLBACK_TSA_VAI = {
    "accommodation": 0.8579,
    "food_beverage": 0.4318,
    "shopping": 0.7088,
    "transport": 0.1627,
}


def load_price_index() -> Dict[int, float]:
    """Loads official DOSM annual Consumer Price Index (2010=100) from price_index.csv."""
    price_csv = PROCESSED_DIR / "price_index.csv"
    if price_csv.exists():
        try:
            df_pi = pd.read_csv(price_csv)
            return dict(zip(df_pi["year"].astype(int), df_pi["index"].astype(float)))
        except Exception as e:
            print(f"Warning: Could not parse price_index.csv ({e}), defaulting base index.")
    return {2025: 134.6}


def load_annual_vai_table(con: duckdb.DuckDBPyConnection) -> Dict[int, Dict[str, float]]:
    """
    Loads empirical annual VAI mappings from tourism_product_year.
    Adheres strictly to Phase 6.1: No arbitrary fallback for unmapped categories.
    """
    try:
        df_prod = con.execute(
            "SELECT year, product_id, vai FROM tourism_product_year WHERE vai IS NOT NULL"
        ).df()
        annual_vai = {}
        for yr, group in df_prod.groupby("year"):
            vai_dict = dict(zip(group["product_id"], group["vai"]))
            annual_vai[int(yr)] = {
                "accommodation": float(vai_dict.get("accommodation", FALLBACK_TSA_VAI["accommodation"])),
                "food_beverage": float(vai_dict.get("food_beverage", FALLBACK_TSA_VAI["food_beverage"])),
                "shopping": float(vai_dict.get("country_specific_goods", FALLBACK_TSA_VAI["shopping"])),
                "transport": float(vai_dict.get("passenger_transport", FALLBACK_TSA_VAI["transport"])),
            }
        return annual_vai
    except Exception as e:
        print(f"Warning: Could not load dynamic VAI table ({e}), using fallback medians.")
        return {}


def run_sdg_metrics() -> pd.DataFrame:
    print("=" * 70)
    print("Calculating SDG 8.9 & 12.b Sustainable Tourism Economic Metrics (Sprint 2)")
    print("=" * 70)

    con = duckdb.connect(str(DUCKDB_PATH))
    annual_vai_map = load_annual_vai_table(con)
    price_index_map = load_price_index()

    # Query state panel with demographics, expenditure, and concentration
    query = """
    WITH state_base AS (
        SELECT 
            p.year,
            p.state,
            p.state_code,
            p.region,
            p.visitors_thousands,
            p.tourists_thousands,
            p.excursionists_thousands,
            p.alos_days,
            p.total_expenditure_rm_million,
            p.accommodation_expenditure_rm_million,
            p.food_expenditure_rm_million,
            p.shopping_expenditure_rm_million,
            p.transport_expenditure_rm_million,
            p.accommodation_share,
            p.hotel_rooms_kpi,
            p.total_population_thousands,
            p.working_age_thousands,
            p.households_thousands,
            p.households_count,
            p.median_household_income_rm as resident_median_income_rm,
            p.avg_household_size
        FROM state_panel_year p
        WHERE p.year BETWEEN 2018 AND 2025
    ),
    hhi_base AS (
        SELECT 
            year,
            destination as state,
            hhi as feeder_hhi,
            top_feeder_share_pct
        FROM destination_concentration_panel
    )
    SELECT 
        b.*,
        COALESCE(h.feeder_hhi, 2000.0) as feeder_hhi,
        COALESCE(h.top_feeder_share_pct, 30.0) as top_origin_share_pct
    FROM state_base b
    LEFT JOIN hhi_base h ON b.year = h.year AND b.state = h.state
    ORDER BY b.state, b.year
    """

    df = con.execute(query).df()

    # 1. Total Visitor-Days Footprint: (Tourists * ALOS) + Excursionists
    df["tourist_nights_k"] = df["tourists_thousands"] * df["alos_days"]
    df["total_visitor_days_k"] = [
        calc_visitor_days(t, alos, exc)
        for t, alos, exc in zip(df["tourists_thousands"], df["alos_days"], df["excursionists_thousands"])
    ]

    # 2. Tourism Economic Yield per Visitor-Day (TEY in RM/day)
    df["tey_rm_per_day"] = np.round(
        [
            calc_tey(tot_exp * 1e6, vis_days * 1e3)
            for tot_exp, vis_days in zip(df["total_expenditure_rm_million"], df["total_visitor_days_k"])
        ],
        1,
    )

    # 3. Accommodation Yield per Overnight Night (RM/night)
    df["accommodation_yield_rm_per_night"] = np.round(
        [
            calc_accommodation_yield(accom_exp * 1e6, t * 1e3, alos)
            for accom_exp, t, alos in zip(
                df["accommodation_expenditure_rm_million"], df["tourists_thousands"], df["alos_days"]
            )
        ],
        1,
    )

    # 4. Excursionist Pressure Ratio (EPR = Excursionists / Overnight Tourists)
    df["epr_ratio"] = np.round(df["excursionists_thousands"] / df["tourists_thousands"].clip(lower=0.1), 2)

    # 5. Tourism GVA Intensity (%) & Mapping Coverage (%)
    # Adheres to Phase 6 & 6.1: Zero arbitrary 0.50 fallback
    attributable_gvas = []
    mapped_exps = []
    mapping_coverages = []
    gva_intensities = []
    tvay_yields = []

    for _, row in df.iterrows():
        yr = int(row["year"])
        vai_dict = annual_vai_map.get(yr, FALLBACK_TSA_VAI)

        tot_exp = row["total_expenditure_rm_million"] or 0.0
        accom_exp = row["accommodation_expenditure_rm_million"]
        food_exp = row["food_expenditure_rm_million"]
        shop_exp = row["shopping_expenditure_rm_million"]
        trans_exp = row["transport_expenditure_rm_million"]

        exp_dict = {
            "accommodation": accom_exp,
            "food_beverage": food_exp,
            "shopping": shop_exp,
            "transport": trans_exp,
        }

        gva_val, mapped_val = calc_estimated_tourism_gva_state(exp_dict, vai_dict)
        cov_pct = calc_mapping_coverage(mapped_val, tot_exp)
        intensity_pct = calc_tourism_gva_intensity(gva_val, mapped_val)

        vis_days_k = row["total_visitor_days_k"]
        tvay_val = calc_tvay(gva_val * 1e6, vis_days_k * 1e3) if vis_days_k and vis_days_k > 0 else np.nan

        attributable_gvas.append(gva_val)
        mapped_exps.append(mapped_val)
        mapping_coverages.append(cov_pct)
        gva_intensities.append(intensity_pct)
        tvay_yields.append(tvay_val)

    df["estimated_tourism_gva_rm_million"] = np.round(attributable_gvas, 2)
    df["mapped_expenditure_rm_million"] = np.round(mapped_exps, 2)
    df["mapping_coverage_pct"] = np.round(mapping_coverages, 1)
    df["tourism_gva_intensity_pct"] = np.round(gva_intensities, 1)
    df["tvay_rm_per_day"] = np.round(tvay_yields, 1)

    # Maintain dvr_retention_rate_pct as alias for backward compatibility
    df["dvr_retention_rate_pct"] = df["tourism_gva_intensity_pct"]

    # 6. Real RM Deflation Series (Constant 2025 RM per Phase 5)
    df["real_total_expenditure_rm_million"] = np.round(
        [
            calc_real_value(exp, yr, price_index_map, base_year=2025)
            for exp, yr in zip(df["total_expenditure_rm_million"], df["year"])
        ],
        2,
    )
    df["real_accommodation_expenditure_rm_million"] = np.round(
        [
            calc_real_value(exp, yr, price_index_map, base_year=2025)
            for exp, yr in zip(df["accommodation_expenditure_rm_million"], df["year"])
        ],
        2,
    )
    df["real_tey_rm_per_day"] = np.round(
        [
            calc_real_value(tey, yr, price_index_map, base_year=2025)
            for tey, yr in zip(df["tey_rm_per_day"], df["year"])
        ],
        1,
    )
    df["real_accommodation_yield_rm_per_night"] = np.round(
        [
            calc_real_value(ay, yr, price_index_map, base_year=2025)
            for ay, yr in zip(df["accommodation_yield_rm_per_night"], df["year"])
        ],
        1,
    )
    df["real_estimated_tourism_gva_rm_million"] = np.round(
        [
            calc_real_value(gva, yr, price_index_map, base_year=2025)
            for gva, yr in zip(df["estimated_tourism_gva_rm_million"], df["year"])
        ],
        2,
    )
    df["real_tvay_rm_per_day"] = np.round(
        [
            calc_real_value(tvay, yr, price_index_map, base_year=2025)
            for tvay, yr in zip(df["tvay_rm_per_day"], df["year"])
        ],
        1,
    )

    # 7. Tourism Intensity Ratio (TIR = Visitors / Resident Population)
    df["tir_visitors_per_resident"] = np.round(
        df["visitors_thousands"] / df["total_population_thousands"].clip(lower=10.0), 2
    )
    df["tir_tourists_per_resident"] = np.round(
        df["tourists_thousands"] / df["total_population_thousands"].clip(lower=10.0), 2
    )

    # 8. Resident Economic Yield per Household (RYH in RM accommodation yield per resident household)
    df["ryh_accom_per_household_rm"] = np.round(
        (df["accommodation_expenditure_rm_million"] * 1e6) / (df["households_thousands"].clip(lower=1.0) * 1e3), 1
    )

    # 9. State Typology Rebuild (Phase 8: ALOS vs TVAY 4-Quadrant Classification)
    alos_median = df["alos_days"].median()
    tvay_median = df["tvay_rm_per_day"].median()

    df["yield_typology"] = [
        classify_state_yield_typology(alos, tvay, alos_median, tvay_median)
        for alos, tvay in zip(df["alos_days"], df["tvay_rm_per_day"])
    ]

    # 10. Policy Diagnosis & Action Classification Matrix
    # Follows Phase 13: Accurate VFR framing (not 'leakage', but commercial accommodation opportunity)
    def classify_sdg_policy(row) -> Tuple[str, str, str]:
        epr = row["epr_ratio"]
        tey = row["tey_rm_per_day"]
        hhi = row["feeder_hhi"]
        intensity = row["tourism_gva_intensity_pct"]

        if epr >= 2.0 and tey < 120:
            return (
                "High Day-Trip Congestion / Low Overnight Capture",
                "High day-tripper volume absorbing local infrastructure with low commercial accommodation capture. Note: Day visitors contribute to food, retail, and local transport, but represent prime targets for commercial accommodation and overnight conversion via evening cultural events and multi-day packages.",
                "#f59e0b",
            )
        elif hhi >= 2500:
            return (
                "Single-Origin Fragility",
                f"Excessive market concentration (HHI: {hhi:.0f}) with over-reliance on a single origin feeder. Priority: Aggressively diversify marketing to secondary origin states.",
                "#ef4444",
            )
        elif tey >= 140 and intensity >= 52:
            return (
                "Sustainable High-Yield Benchmark",
                "Exceptional tourism GVA intensity and high economic return per visitor-day. Priority: Monitor carrying capacity and safeguard natural/cultural assets.",
                "#10b981",
            )
        elif row["tir_visitors_per_resident"] >= 15.0:
            return (
                "Carrying Capacity Volume Pressure",
                f"High visitor intensity ({row['tir_visitors_per_resident']:.1f} visitors per resident). Priority: Shift from visitor volume targets to yield-per-visitor optimization.",
                "#3b82f6",
            )
        else:
            return (
                "Value Growth Frontier",
                "Healthy absorption capacity with significant upside to expand length of stay and accommodation spend. Priority: Expand accommodation inventory and targeted promotion.",
                "#8b5cf6",
            )

    labels = [classify_sdg_policy(r) for _, r in df.iterrows()]
    df["sdg_diagnosis"] = [l[0] for l in labels]
    df["sdg_policy_action"] = [l[1] for l in labels]
    df["sdg_status_color"] = [l[2] for l in labels]

    # Save to DuckDB & Parquet/CSV
    con.execute("CREATE OR REPLACE TABLE sdg_sustainable_metrics AS SELECT * FROM df")
    con.execute(f"COPY sdg_sustainable_metrics TO '{PROCESSED_DIR}/sdg_sustainable_metrics.parquet' (FORMAT PARQUET)")
    df.to_csv(PROCESSED_DIR / "sdg_sustainable_metrics.csv", index=False)

    print(f"\nSDG Sustainable Metrics materialized in DuckDB `sdg_sustainable_metrics` ({len(df)} rows).")

    # Print 2025 baseline summary
    df_2025 = df[df["year"] == 2025]
    print("\n2025 Baseline State SDG Sustainability Summary:")
    print(
        df_2025[
            [
                "state",
                "tey_rm_per_day",
                "tvay_rm_per_day",
                "tourism_gva_intensity_pct",
                "mapping_coverage_pct",
                "yield_typology",
                "sdg_diagnosis",
            ]
        ].head(8)
    )

    con.close()
    print("=" * 70)
    return df


if __name__ == "__main__":
    run_sdg_metrics()
