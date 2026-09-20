"""
Official DOSM Population by State Ingestion Parser
Ingests `population_state.parquet` (DOSM Open Data current population series)
Extracts demographic slices for all 16 states & Federal Territories across 2018–2025:
  - Total population ('000 and millions)
  - Working-age population (Ages 15–64)
  - Youth / Young adult population (Ages 20–39)
  - Elderly population (Ages 65+)
  - Children population (Ages 0–14)
  - Dependency ratio ((0-14 + 65+) / 15-64 * 100)
  - Working-age share (%)
  - Average household size (Total Pop / HIES Households)

Standardizes against canonical state names, enriches DuckDB tables:
  - `state_demographics_annual`
  - Updates `state_demographics`
  - Enriches `state_panel_year`
Exports Parquet and CSV to `data/processed/`.
"""

import shutil
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
RAW_DIR = ROOT_DIR / "data/raw"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

SOURCE_PQ_ROOT = ROOT_DIR / "population_state.parquet"
TARGET_PQ_RAW = RAW_DIR / "population_state.parquet"

# Canonical state reference table
STATE_MAP: Dict[str, Dict[str, str]] = {
    "Johor": {"code": "MY-01", "region": "Southern"},
    "Kedah": {"code": "MY-02", "region": "Northern"},
    "Kelantan": {"code": "MY-03", "region": "East Coast"},
    "Melaka": {"code": "MY-04", "region": "Southern"},
    "Negeri Sembilan": {"code": "MY-05", "region": "Central"},
    "Pahang": {"code": "MY-06", "region": "East Coast"},
    "Pulau Pinang": {"code": "MY-07", "region": "Northern"},
    "Perak": {"code": "MY-08", "region": "Northern"},
    "Perlis": {"code": "MY-09", "region": "Northern"},
    "Selangor": {"code": "MY-10", "region": "Central"},
    "Terengganu": {"code": "MY-11", "region": "East Coast"},
    "Sabah": {"code": "MY-12", "region": "East Malaysia"},
    "Sarawak": {"code": "MY-13", "region": "East Malaysia"},
    "W.P. Kuala Lumpur": {"code": "MY-14", "region": "Central"},
    "W.P. Labuan": {"code": "MY-15", "region": "East Malaysia"},
    "W.P. Putrajaya": {"code": "MY-16", "region": "Central"},
}


def run_population_ingestion() -> pd.DataFrame:
    print("=" * 70)
    print("Official DOSM State Population & Demographics Ingestion")
    print("=" * 70)

    # Ensure raw copy exists
    if SOURCE_PQ_ROOT.exists() and not TARGET_PQ_RAW.exists():
        shutil.copy2(SOURCE_PQ_ROOT, TARGET_PQ_RAW)
        print(f"  Copied {SOURCE_PQ_ROOT.name} to {TARGET_PQ_RAW}")

    pq_file = TARGET_PQ_RAW if TARGET_PQ_RAW.exists() else SOURCE_PQ_ROOT
    if not pq_file.exists():
        raise FileNotFoundError(f"Population parquet not found at {pq_file}")

    print(f"Reading population records from: {pq_file.name}")
    con_temp = duckdb.connect()

    # Query demographic aggregation for 2018-2025 across all 16 states
    query = f"""
    WITH base AS (
        SELECT 
            EXTRACT(year FROM date) as year,
            state,
            -- Total Population
            MAX(CASE WHEN sex = 'both' AND age = 'overall' AND ethnicity = 'overall' THEN population END) as total_pop_k,
            -- Children 0-14
            SUM(CASE WHEN sex = 'both' AND ethnicity = 'overall' AND age IN (
                '0-4', '5-9', '10-14'
            ) THEN population ELSE 0 END) as children_0_14_pop_k,
            -- DTS Age Class 1: 15-24 (Belia / Young Adults)
            SUM(CASE WHEN sex = 'both' AND ethnicity = 'overall' AND age IN (
                '15-19', '20-24'
            ) THEN population ELSE 0 END) as dts_15_24_pop_k,
            -- DTS Age Class 2: 25-39 (Dewasa Muda / Prime Mobile Travelers)
            SUM(CASE WHEN sex = 'both' AND ethnicity = 'overall' AND age IN (
                '25-29', '30-34', '35-39'
            ) THEN population ELSE 0 END) as dts_25_39_pop_k,
            -- DTS Age Class 3: 40-54 (Pertengahan Umur / Family Travelers)
            SUM(CASE WHEN sex = 'both' AND ethnicity = 'overall' AND age IN (
                '40-44', '45-49', '50-54'
            ) THEN population ELSE 0 END) as dts_40_54_pop_k,
            -- DTS Age Class 4: 55+ (Warga Emas / Seniors & Retirees)
            SUM(CASE WHEN sex = 'both' AND ethnicity = 'overall' AND age IN (
                '55-59', '60-64', '65-69', '70-74', '75-79', '80-84', '85+'
            ) THEN population ELSE 0 END) as dts_55plus_pop_k,
            -- Working Age 15-64
            SUM(CASE WHEN sex = 'both' AND ethnicity = 'overall' AND age IN (
                '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64'
            ) THEN population ELSE 0 END) as working_age_pop_k,
            -- Elderly 65+
            SUM(CASE WHEN sex = 'both' AND ethnicity = 'overall' AND age IN (
                '65-69', '70-74', '75-79', '80-84', '85+'
            ) THEN population ELSE 0 END) as elderly_65plus_pop_k
        FROM '{pq_file}'
        WHERE EXTRACT(year FROM date) BETWEEN 2018 AND 2025
        GROUP BY 1, 2
    ),
    calc AS (
        SELECT 
            year,
            state,
            ROUND(total_pop_k, 2) as total_population_thousands,
            ROUND(total_pop_k / 1000.0, 4) as total_population_millions,
            ROUND(children_0_14_pop_k, 2) as children_0_14_thousands,
            ROUND(dts_15_24_pop_k, 2) as dts_15_24_thousands,
            ROUND(dts_25_39_pop_k, 2) as dts_25_39_thousands,
            ROUND(dts_40_54_pop_k, 2) as dts_40_54_thousands,
            ROUND(dts_55plus_pop_k, 2) as dts_55plus_thousands,
            ROUND(dts_15_24_pop_k + dts_25_39_pop_k + dts_40_54_pop_k + dts_55plus_pop_k, 2) as adult_15plus_thousands,
            ROUND(working_age_pop_k, 2) as working_age_thousands,
            ROUND(elderly_65plus_pop_k, 2) as elderly_65plus_thousands,
            -- Percentages of Total Population
            ROUND(children_0_14_pop_k * 100.0 / NULLIF(total_pop_k, 0), 1) as children_pct,
            ROUND(working_age_pop_k * 100.0 / NULLIF(total_pop_k, 0), 1) as working_age_pct,
            ROUND(elderly_65plus_pop_k * 100.0 / NULLIF(total_pop_k, 0), 1) as elderly_pct,
            -- DTS Adult (15+) Shares (Summing exactly to 100% of adults)
            ROUND(dts_15_24_pop_k * 100.0 / NULLIF(dts_15_24_pop_k + dts_25_39_pop_k + dts_40_54_pop_k + dts_55plus_pop_k, 0), 1) as dts_15_24_pct,
            ROUND(dts_25_39_pop_k * 100.0 / NULLIF(dts_15_24_pop_k + dts_25_39_pop_k + dts_40_54_pop_k + dts_55plus_pop_k, 0), 1) as dts_25_39_pct,
            ROUND(dts_40_54_pop_k * 100.0 / NULLIF(dts_15_24_pop_k + dts_25_39_pop_k + dts_40_54_pop_k + dts_55plus_pop_k, 0), 1) as dts_40_54_pct,
            ROUND(dts_55plus_pop_k * 100.0 / NULLIF(dts_15_24_pop_k + dts_25_39_pop_k + dts_40_54_pop_k + dts_55plus_pop_k, 0), 1) as dts_55plus_pct,
            -- Dependency Ratio
            ROUND((children_0_14_pop_k + elderly_65plus_pop_k) * 100.0 / NULLIF(working_age_pop_k, 0), 1) as dependency_ratio
        FROM base
    )
    SELECT * FROM calc
    ORDER BY year, state
    """

    df_pop = con_temp.execute(query).df()
    con_temp.close()

    # Add metadata
    df_pop["state_code"] = df_pop["state"].map(lambda s: STATE_MAP.get(s, {}).get("code", "MY-00"))
    df_pop["region"] = df_pop["state"].map(lambda s: STATE_MAP.get(s, {}).get("region", "Other"))

    print(f"Extracted {len(df_pop)} state-year demographic records across {df_pop['state'].nunique()} states (2018–2025).")

    # Connect to DuckDB warehouse
    con = duckdb.connect(str(DUCKDB_PATH))

    # Join with HIES households to compute dynamic average household size
    con.execute("CREATE OR REPLACE TEMP TABLE tmp_pop AS SELECT * FROM df_pop")
    df_demog_annual = con.execute("""
        SELECT 
            p.*,
            h.households_thousands,
            h.households_count,
            h.median_income_rm as median_household_income_rm,
            h.mean_income_rm as mean_household_income_rm,
            ROUND(p.total_population_thousands / NULLIF(h.households_thousands, 0), 2) as avg_household_size,
            'official_dosm_estimates' as data_status
        FROM tmp_pop p
        LEFT JOIN state_household_income_annual h
            ON p.state = h.state AND p.year = h.year
        ORDER BY p.state, p.year
    """).df()

    # Materialize state_demographics_annual table
    con.execute("CREATE OR REPLACE TABLE state_demographics_annual AS SELECT * FROM df_demog_annual")
    con.execute(f"COPY state_demographics_annual TO '{PROCESSED_DIR}/state_demographics_annual.parquet' (FORMAT PARQUET)")
    df_demog_annual.to_csv(PROCESSED_DIR / "state_demographics_annual.csv", index=False)
    print("  [1/3] Materialized `state_demographics_annual` (128 rows).")

    # Update latest baseline state_demographics (2025/2024 latest official)
    df_latest = df_demog_annual[df_demog_annual["year"] == 2025].copy()
    con.execute("CREATE OR REPLACE TABLE state_demographics AS SELECT * FROM df_latest")
    con.execute(f"COPY state_demographics TO '{PROCESSED_DIR}/state_demographics.parquet' (FORMAT PARQUET)")
    df_latest.to_csv(PROCESSED_DIR / "state_demographics.csv", index=False)
    print("  [2/3] Updated `state_demographics` benchmark (16 rows).")

    # Enrich state_panel_year with accurate annual population and working age
    con.execute("""
        CREATE OR REPLACE TABLE state_panel_year AS
        SELECT 
            p.year,
            p.period,
            p.state,
            p.state_code,
            p.region,
            p.latitude,
            p.longitude,
            p.visitors_thousands,
            p.tourists_thousands,
            p.excursionists_thousands,
            p.trips_thousands,
            p.alos_days,
            p.total_expenditure_rm_million,
            p.accommodation_expenditure_rm_million,
            p.food_expenditure_rm_million,
            p.shopping_expenditure_rm_million,
            p.transport_expenditure_rm_million,
            p.accommodation_share,
            p.spend_per_tourist_rm,
            p.spend_per_night_rm,
            p.tourist_nights_thousands,
            p.aor_pct,
            p.hotel_rooms_kpi,
            p.hotels_count_kpi,
            p.domestic_hotel_guests,
            p.foreign_hotel_guests,
            p.total_hotel_guests,
            p.foreign_guest_share_pct,
            p.homestay_rooms,
            p.homestay_operators,
            d.total_population_thousands,
            d.total_population_millions,
            d.adult_15plus_thousands,
            d.dts_15_24_thousands,
            d.dts_15_24_pct,
            d.dts_25_39_thousands,
            d.dts_25_39_pct,
            d.dts_40_54_thousands,
            d.dts_40_54_pct,
            d.dts_55plus_thousands,
            d.dts_55plus_pct,
            d.children_0_14_thousands,
            d.children_pct,
            d.working_age_thousands,
            d.working_age_pct,
            d.elderly_65plus_thousands,
            d.elderly_pct,
            d.dependency_ratio,
            d.households_thousands,
            d.households_count,
            d.median_household_income_rm,
            d.mean_household_income_rm,
            d.avg_household_size
        FROM state_panel_year p
        LEFT JOIN state_demographics_annual d
            ON p.state = d.state AND p.year = d.year
    """)
    cnt_panel = con.execute("SELECT COUNT(*) FROM state_panel_year").fetchone()[0]
    print(f"  [3/3] Enriched `state_panel_year` ({cnt_panel} rows) with annual demographics.")

    con.close()
    print("=" * 70)
    print("Demographics Ingestion Completed Successfully.")
    print("=" * 70)
    return df_demog_annual


if __name__ == "__main__":
    run_population_ingestion()
