"""
Sustainable Tourism & SDG Economic Metrics Engine
Aligned with UN SDG Target 8.9 (Sustainable Tourism & Local Job Creation)
and Target 12.b (Monitoring Sustainable Development Impacts).

Calculates core economic sustainability dimensions:
  1. Tourism Economic Yield per Visitor-Day (TEY, RM/day)
  2. Domestic Value Retention Rate (DVR, %) using TSA Value-Added Intensities
  3. Excursionist Pressure Ratio (EPR = Excursionists / Overnight Tourists)
  4. Tourism Intensity Ratio (TIR = Total Visitors / Resident Population)
  5. Resident Yield per Household (RYH = Accommodation Spend / Resident Households)
  6. Feeder Concentration HHI (from inbound OD flows)
  7. Policy Diagnosis & Action Classification Matrix

Mandatory Guardrail (AGENTS.md Section 1, 9, 11):
  "This project focuses on the economic dimension of sustainable tourism.
   It does not claim to measure complete environmental or social sustainability."
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

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

# TSA 2025 Value-Added Intensities (VAI)
TSA_VAI = {
    "accommodation": 0.858,  # 85.8% GVA per RM supply (Accommodation is highest value-efficiency)
    "food_beverage": 0.432,  # 43.2%
    "shopping": 0.709,       # 70.9% (Country-specific retail goods)
    "transport": 0.285,      # 28.5%
    "other": 0.500,          # 50.0%
}


def run_sdg_metrics() -> pd.DataFrame:
    print("=" * 70)
    print("Calculating SDG 8.9 & 12.b Sustainable Tourism Economic Metrics")
    print("=" * 70)

    con = duckdb.connect(str(DUCKDB_PATH))

    # Query state panel with demographics and expenditure breakdown
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
            d.population_thousands,
            d.households_thousands,
            d.households_count,
            d.median_income_rm as resident_median_income_rm
        FROM state_panel_year p
        LEFT JOIN state_demographics d ON p.state = d.state
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

    # 1. Total Visitor-Days: (Tourists * ALOS) + Excursionists (1-day visit)
    df["tourist_nights_k"] = df["tourists_thousands"] * df["alos_days"]
    df["total_visitor_days_k"] = df["tourist_nights_k"] + df["excursionists_thousands"]

    # 2. Tourism Economic Yield per Visitor-Day (TEY in RM/day)
    df["tey_rm_per_day"] = np.round(
        (df["total_expenditure_rm_million"] * 1e6) / (df["total_visitor_days_k"].clip(lower=1.0) * 1e3), 1
    )

    # 3. Excursionist Pressure Ratio (EPR = Excursionists / Overnight Tourists)
    df["epr_ratio"] = np.round(df["excursionists_thousands"] / df["tourists_thousands"].clip(lower=0.1), 2)

    # 4. Domestic Value Retention Rate (DVR %)
    # Attributable GVA = Sum(Expenditure_k * VAI_k)
    other_exp = (
        df["total_expenditure_rm_million"]
        - df["accommodation_expenditure_rm_million"]
        - df["food_expenditure_rm_million"]
        - df["shopping_expenditure_rm_million"]
        - df["transport_expenditure_rm_million"]
    ).clip(lower=0.0)

    gva_proxy = (
        df["accommodation_expenditure_rm_million"] * TSA_VAI["accommodation"]
        + df["food_beverage_expenditure_rm_million"] * TSA_VAI["food_beverage"]
        if "food_beverage_expenditure_rm_million" in df.columns
        else df["food_expenditure_rm_million"] * TSA_VAI["food_beverage"]
    )
    gva_proxy += df["shopping_expenditure_rm_million"] * TSA_VAI["shopping"]
    gva_proxy += df["transport_expenditure_rm_million"] * TSA_VAI["transport"]
    gva_proxy += other_exp * TSA_VAI["other"]

    df["attributable_gva_rm_million"] = np.round(gva_proxy, 1)
    df["dvr_retention_rate_pct"] = np.round(
        (df["attributable_gva_rm_million"] / df["total_expenditure_rm_million"].clip(lower=1.0)) * 100.0, 1
    )

    # 5. Tourism Intensity Ratio (TIR = Visitors / Resident Population)
    df["tir_visitors_per_resident"] = np.round(
        df["visitors_thousands"] / df["population_thousands"].clip(lower=10.0), 2
    )
    df["tir_tourists_per_resident"] = np.round(
        df["tourists_thousands"] / df["population_thousands"].clip(lower=10.0), 2
    )

    # 6. Resident Economic Yield per Household (RYH in RM accommodation yield per resident household)
    df["ryh_accom_per_household_rm"] = np.round(
        (df["accommodation_expenditure_rm_million"] * 1e6) / (df["households_thousands"].clip(lower=1.0) * 1e3), 1
    )

    # 7. Policy Diagnosis & Action Classification Matrix
    def classify_sdg_policy(row) -> Tuple[str, str, str]:
        epr = row["epr_ratio"]
        tey = row["tey_rm_per_day"]
        hhi = row["feeder_hhi"]
        dvr = row["dvr_retention_rate_pct"]

        if epr >= 2.0 and tey < 120:
            return (
                "Excursionist Day-Trip Leakage",
                "High day-tripper volume absorbing local infrastructure without generating overnight hotel yield. Priority: Develop night markets, evening cultural events, and 2-day pass incentives.",
                "#f59e0b",
            )
        elif hhi >= 2500:
            return (
                "Single-Origin Fragility",
                f"Excessive market concentration (HHI: {hhi:.0f}) with over-reliance on a single origin feeder. Priority: Aggressively diversify marketing to secondary origin states.",
                "#ef4444",
            )
        elif tey >= 140 and dvr >= 52:
            return (
                "Sustainable High-Value Benchmark",
                "Exceptional domestic value retention and high economic return per visitor-day. Priority: Monitor carrying capacity and safeguard natural/cultural assets.",
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
    print(df_2025[["state", "tey_rm_per_day", "epr_ratio", "dvr_retention_rate_pct", "tir_visitors_per_resident", "sdg_diagnosis"]].head(8))

    con.close()
    print("=" * 70)
    return df


if __name__ == "__main__":
    run_sdg_metrics()
