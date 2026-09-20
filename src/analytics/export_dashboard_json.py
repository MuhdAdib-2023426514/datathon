"""
Dashboard Data Exporter
Extracts and serializes pre-aggregated, optimized JSON data structures from DuckDB
into `dashboard/public/data/` for high-performance client-side rendering.

Generates:
  1. geo_malaysia.json - 16-state boundary GeoJSON (MultiPolygon)
  2. tsa_macro.json - TSA 2015-2025 macro indicators & product-level VAI rankings
  3. state_profiles.json - Comprehensive 16-state multi-year profiles, radar metrics, archetypes & SDG diagnostics
  4. od_corridors.json - Inter-state flows, geodesic coordinates, corridor classifications & gravity metrics
  5. scenario_engine.json - What-if simulation parameters, baseline metrics & causal disclaimer
  6. drivers_rq3.json - Feature attribution, standardized betas & importance for Research Question 3
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List
import duckdb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"
GEO_FILE = ROOT_DIR / "data/geo/malaysia.geojson"
DASHBOARD_DATA_DIR = ROOT_DIR / "dashboard/public/data"


def clean_nan(obj: Any) -> Any:
    """Recursively clean NaN, Infinity and numpy types for standard JSON serialization."""
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return round(obj, 4)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return round(float(obj), 4)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


def export_dashboard_data():
    print("=" * 70)
    print("Exporting Pre-Aggregated Dashboard JSON Data")
    print("=" * 70)

    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    # 1. GeoJSON (malaysia.geojson)
    if GEO_FILE.exists():
        target_geo = DASHBOARD_DATA_DIR / "geo_malaysia.json"
        shutil.copy2(GEO_FILE, target_geo)
        print(f"  [1/6] Exported GeoJSON: {target_geo.name} ({target_geo.stat().st_size / 1024:.1f} KB)")
    else:
        print("  [Warning] GeoJSON file not found at:", GEO_FILE)

    # 2. TSA Macro (tsa_macro.json)
    df_tsa_macro = con.execute("SELECT * FROM tsa_macro_year ORDER BY year").df()
    df_tsa_products = con.execute("SELECT * FROM tourism_product_year ORDER BY product, year").df()
    df_product_summary = con.execute("SELECT * FROM product_value_summary ORDER BY vai_rank ASC").df()

    tsa_data = {
        "macro_series": df_tsa_macro.to_dict(orient="records"),
        "product_series": df_tsa_products.to_dict(orient="records"),
        "product_summary": df_product_summary.to_dict(orient="records"),
    }
    with open(DASHBOARD_DATA_DIR / "tsa_macro.json", "w", encoding="utf-8") as f:
        json.dump(clean_nan(tsa_data), f, indent=2)
    print(f"  [2/6] Exported TSA Macro: tsa_macro.json ({len(df_tsa_macro)} macro years, {len(df_product_summary)} products)")

    # 3. State Profiles (state_profiles.json)
    # Comprehensive state profiles joining clusters, demographics, SDG metrics, purpose, hotel stars, and time series
    df_clusters = con.execute("SELECT * FROM state_clusters").df()
    df_sdg = con.execute("SELECT * FROM sdg_sustainable_metrics WHERE year = 2025").df()
    df_stars = con.execute("SELECT * FROM state_hotel_star_inventory WHERE year = 2025").df()
    df_purpose = con.execute("SELECT * FROM state_purpose_of_visit_panel WHERE year = 2025").df()
    df_tourist_inc = con.execute("SELECT * FROM state_tourist_income_panel WHERE year = 2025").df()
    df_demog_2025 = con.execute("SELECT * FROM state_demographics_annual WHERE year = 2025").df()
    df_panel = con.execute("SELECT * FROM state_panel_year ORDER BY state, year").df()

    states_dict = {}
    for _, c_row in df_clusters.iterrows():
        st = c_row["state"]
        sdg_row = df_sdg[df_sdg["state"] == st]
        sdg_info = sdg_row.iloc[0].to_dict() if len(sdg_row) > 0 else {}
        star_row = df_stars[df_stars["state"] == st]
        star_info = star_row.iloc[0].to_dict() if len(star_row) > 0 else {}
        purp_row = df_purpose[df_purpose["state"] == st]
        purp_info = purp_row.iloc[0].to_dict() if len(purp_row) > 0 else {}
        inc_row = df_tourist_inc[df_tourist_inc["state"] == st]
        inc_info = inc_row.iloc[0].to_dict() if len(inc_row) > 0 else {}
        demog_row = df_demog_2025[df_demog_2025["state"] == st]
        demog_info = demog_row.iloc[0].to_dict() if len(demog_row) > 0 else {}

        time_series = df_panel[df_panel["state"] == st].to_dict(orient="records")

        states_dict[st] = {
            "state": st,
            "state_code": c_row["state_code"],
            "region": c_row["region"],
            "archetype_name": c_row["archetype_name"],
            "archetype_desc": c_row["archetype_desc"],
            "archetype_color": c_row["archetype_color"],
            "cluster_id": int(c_row["cluster_id"]),
            "radar_scores": {
                "stay_duration": float(c_row.get("stay_duration_score", 50.0)),
                "nightly_yield": float(c_row.get("nightly_yield_score", 50.0)),
                "accom_intensity": float(c_row.get("accom_intensity_score", 50.0)),
                "leisure_orientation": float(c_row.get("leisure_orientation_score", 50.0)),
                "luxury_supply": float(c_row.get("luxury_supply_score", 50.0)),
                "resident_affluence": float(c_row.get("resident_affluence_score", 50.0)),
            },
            "baseline_2025": {
                "visitors_thousands": float(c_row["avg_visitors_k"]),
                "tourists_thousands": float(c_row["avg_tourists_k"]),
                "alos_days": float(c_row["alos_days"]),
                "spend_per_night_rm": float(c_row["spend_per_night_rm"]),
                "spend_per_tourist_rm": float(c_row["spend_per_tourist_rm"]),
                "accommodation_share_pct": float(c_row["accommodation_share_pct"]),
                "accommodation_expenditure_rm_million": float(c_row["accom_exp_rm_mil"]),
                "total_expenditure_rm_million": float(c_row["total_exp_rm_mil"]),
                "hotel_rooms": int(c_row["hotel_rooms"]) if pd.notnull(c_row["hotel_rooms"]) else 0,
                "aor_pct": float(c_row["aor_pct"]) if pd.notnull(c_row["aor_pct"]) else 0.0,
                "resident_median_income_rm": float(c_row["resident_median_income_rm"]),
            },
            "demographics": {
                "total_population_thousands": float(demog_info.get("total_population_thousands", 1000.0)),
                "total_population_millions": float(demog_info.get("total_population_millions", 1.0)),
                "adult_15plus_thousands": float(demog_info.get("adult_15plus_thousands", 750.0)),
                "children_0_14_thousands": float(demog_info.get("children_0_14_thousands", 250.0)),
                "children_pct": float(demog_info.get("children_pct", 20.0)),
                "working_age_thousands": float(demog_info.get("working_age_thousands", 700.0)),
                "working_age_pct": float(demog_info.get("working_age_pct", 70.0)),
                "elderly_65plus_thousands": float(demog_info.get("elderly_65plus_thousands", 80.0)),
                "elderly_pct": float(demog_info.get("elderly_pct", 8.0)),
                "dependency_ratio": float(demog_info.get("dependency_ratio", 40.0)),
                "dts_age_classes": {
                    "age_15_24_k": float(demog_info.get("dts_15_24_thousands", 200.0)),
                    "age_15_24_pct": float(demog_info.get("dts_15_24_pct", 25.0)),
                    "age_25_39_k": float(demog_info.get("dts_25_39_thousands", 300.0)),
                    "age_25_39_pct": float(demog_info.get("dts_25_39_pct", 35.0)),
                    "age_40_54_k": float(demog_info.get("dts_40_54_thousands", 200.0)),
                    "age_40_54_pct": float(demog_info.get("dts_40_54_pct", 23.0)),
                    "age_55plus_k": float(demog_info.get("dts_55plus_thousands", 150.0)),
                    "age_55plus_pct": float(demog_info.get("dts_55plus_pct", 17.0)),
                },
                "households_thousands": float(demog_info.get("households_thousands", 250.0)),
                "median_household_income_rm": float(demog_info.get("median_household_income_rm", 6000.0)),
                "avg_household_size": float(demog_info.get("avg_household_size", 3.9)),
            },
            "sdg_metrics": {
                "tey_rm_per_day": float(sdg_info.get("tey_rm_per_day", 0.0)),
                "epr_ratio": float(sdg_info.get("epr_ratio", 1.0)),
                "dvr_retention_rate_pct": float(sdg_info.get("dvr_retention_rate_pct", 50.0)),
                "tir_visitors_per_resident": float(sdg_info.get("tir_visitors_per_resident", 5.0)),
                "ryh_accom_per_household_rm": float(sdg_info.get("ryh_accom_per_household_rm", 0.0)),
                "sdg_diagnosis": sdg_info.get("sdg_diagnosis", "Value Growth Frontier"),
                "sdg_policy_action": sdg_info.get("sdg_policy_action", ""),
                "sdg_status_color": sdg_info.get("sdg_status_color", "#10b981"),
            },
            "hotel_stars": {
                "hotels_5star": int(star_info.get("hotels_5star", 0)),
                "rooms_5star": int(star_info.get("rooms_5star", 0)),
                "hotels_4star": int(star_info.get("hotels_4star", 0)),
                "rooms_4star": int(star_info.get("rooms_4star", 0)),
                "hotels_3star": int(star_info.get("hotels_3star", 0)),
                "rooms_3star": int(star_info.get("rooms_3star", 0)),
                "luxury_room_share_pct": float(star_info.get("luxury_room_share_pct", 20.0)),
                "total_hotels": int(star_info.get("total_hotels", 0)),
                "total_rooms": int(star_info.get("total_rooms", 0)),
            },
            "purpose_shares": {
                "holiday": float(purp_info.get("holiday_share_tourist", 35.0)),
                "vfr": float(purp_info.get("vfr_share_tourist", 30.0)),
                "shopping": float(purp_info.get("shopping_share_tourist", 15.0)),
                "business": float(purp_info.get("business_share_tourist", 8.0)),
                "medical": float(purp_info.get("medical_share_tourist", 4.0)),
            },
            "tourist_income": {
                "b40_pct": float(inc_info.get("b40_share_pct", 40.0)),
                "m40_pct": float(inc_info.get("m40_share_pct", 40.0)),
                "t20_pct": float(inc_info.get("t20_share_pct", 20.0)),
                "affluence_index": float(inc_info.get("affluence_index", 100.0)),
            },
            "time_series": time_series,
        }

    with open(DASHBOARD_DATA_DIR / "state_profiles.json", "w", encoding="utf-8") as f:
        json.dump(clean_nan(states_dict), f, indent=2)
    print(f"  [3/6] Exported State Profiles: state_profiles.json ({len(states_dict)} states)")

    # 4. Origin-Destination Corridors (od_corridors.json)
    df_corridors = con.execute("""
        SELECT 
            c.*,
            c.corridor_tier as corridor_category,
            g.expected_flow_thousands as gravity_flow_thousands,
            g.performance_ratio as gravity_performance_ratio,
            s_orig.latitude as orig_lat,
            s_orig.longitude as orig_lon,
            s_dest.latitude as dest_lat,
            s_dest.longitude as dest_lon
        FROM corridor_classification c
        LEFT JOIN corridor_gravity_predictions g
            ON c.origin = g.origin AND c.destination = g.destination
        LEFT JOIN state_panel_year s_orig 
            ON s_orig.year = 2025 AND c.origin = s_orig.state
        LEFT JOIN state_panel_year s_dest 
            ON s_dest.year = 2025 AND c.destination = s_dest.state
        ORDER BY c.tourist_flow_thousands DESC
    """).df()

    # Destination concentration panel
    df_hhi = con.execute("SELECT * FROM destination_concentration_panel WHERE year = 2025").df()

    corridor_data = {
        "corridors_2025": df_corridors.to_dict(orient="records"),
        "destination_concentration": df_hhi.to_dict(orient="records"),
        "category_summary": df_corridors["corridor_tier"].value_counts().to_dict(),
    }
    with open(DASHBOARD_DATA_DIR / "od_corridors.json", "w", encoding="utf-8") as f:
        json.dump(clean_nan(corridor_data), f, indent=2)
    print(f"  [4/6] Exported OD Corridors: od_corridors.json ({len(df_corridors)} inter-state corridors)")

    # 5. Scenario Simulator Engine Data (scenario_engine.json)
    # Provides baseline multipliers and state metrics for real-time frontend calculations
    state_sim_baselines = {}
    for st, sdata in states_dict.items():
        b = sdata["baseline_2025"]
        state_sim_baselines[st] = {
            "alos": b["alos_days"],
            "spend_per_night": b["spend_per_night_rm"],
            "tourists_k": b["tourists_thousands"],
            "hotel_rooms": b["hotel_rooms"],
            "aor": b["aor_pct"],
        }

    scenario_config = {
        "constants": {
            "accommodation_vai": 0.858,  # Official TSA 2025
            "fnb_vai": 0.432,
            "overall_tourism_vai": 0.528,
            "disclaimer": "Scenario estimate, not a causal forecast.",
        },
        "state_baselines": state_sim_baselines,
        "gravity_elasticities": {
            "distance_friction": -0.6031,
            "origin_working_age": 0.8903,
            "origin_income": 0.7250,
            "destination_pull": 0.7035,
            "cross_region_barrier": -1.3319,
        },
    }
    with open(DASHBOARD_DATA_DIR / "scenario_engine.json", "w", encoding="utf-8") as f:
        json.dump(clean_nan(scenario_config), f, indent=2)
    print(f"  [5/6] Exported Scenario Engine Config: scenario_engine.json")

    # 6. Research Question 3 Driver Attribution (drivers_rq3.json)
    df_drivers = con.execute("SELECT * FROM accommodation_drivers_summary").df()
    df_meta = con.execute("SELECT * FROM accommodation_drivers_meta").df()

    drivers_data = {
        "model_metadata": df_meta.iloc[0].to_dict() if len(df_meta) > 0 else {},
        "feature_attributions": df_drivers.to_dict(orient="records"),
    }
    with open(DASHBOARD_DATA_DIR / "drivers_rq3.json", "w", encoding="utf-8") as f:
        json.dump(clean_nan(drivers_data), f, indent=2)
    print(f"  [6/6] Exported RQ3 Drivers: drivers_rq3.json ({len(df_drivers)} drivers)")

    con.close()
    print("=" * 70)
    print("Dashboard JSON Export Completed Successfully.")
    print("=" * 70)


if __name__ == "__main__":
    export_dashboard_data()
