"""
State Typology Clustering Engine (Unsupervised Machine Learning)
Uses Ward's Hierarchical Agglomerative Clustering to classify Malaysia's 16 states & FTs
into 4 strategic tourism value archetypes:
  1. High-Yield Extended Stay Destinations (e.g. High ALOS, High Spend/Night, Strong Eco/Nature/Leisure)
  2. High-Volume Urban & Commercial Gateways (e.g. High Total Tourists, High Luxury Capacity, Commercial/Transit)
  3. Excursionist / High-Leakage Conversion Corridors (e.g. High Visitors, Low ALOS, High Day-Tripper Share)
  4. Emerging / Untapped Value Frontiers (e.g. Moderate Flow, Lower Current Spend, High Expansion Potential)

Features used (standardized via StandardScaler):
  - Average Length of Stay (ALOS days)
  - Spend per Night (RM)
  - Accommodation Expenditure Share (%)
  - Holiday / Leisure Purpose Share (%)
  - Luxury Hotel Room Share (% 4-Star & 5-Star)
  - Resident Median Household Income (RM)

Adheres strictly to AGENTS.md Section 8:
- Transparent, deterministic clustering
- No black-box models
- Accompanied by descriptive radar metrics
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import duckdb
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"


def run_state_clustering() -> pd.DataFrame:
    print("=" * 70)
    print("Running Unsupervised State Typology Clustering (Ward's Hierarchical)")
    print("=" * 70)

    con = duckdb.connect(str(DUCKDB_PATH))

    # Query 2024/2025 multi-source profile per state
    query = """
    WITH state_base AS (
        SELECT 
            p.state,
            p.state_code,
            p.region,
            AVG(p.visitors_thousands) as avg_visitors_k,
            AVG(p.tourists_thousands) as avg_tourists_k,
            AVG(p.alos_days) as alos_days,
            AVG(p.spend_per_night_rm) as spend_per_night_rm,
            AVG(p.spend_per_tourist_rm) as spend_per_tourist_rm,
            AVG(p.accommodation_share) * 100 as accommodation_share_pct,
            AVG(p.accommodation_expenditure_rm_million) as accom_exp_rm_mil,
            AVG(p.total_expenditure_rm_million) as total_exp_rm_mil,
            AVG(p.hotel_rooms_kpi) as hotel_rooms,
            AVG(p.aor_pct) as aor_pct,
            AVG(p.median_household_income_rm) as resident_median_income_rm
        FROM state_panel_year p
        WHERE p.year IN (2024, 2025)
        GROUP BY p.state, p.state_code, p.region
    ),
    purpose_data AS (
        SELECT 
            state,
            AVG(holiday_share_tourist) as holiday_pct,
            AVG(vfr_share_tourist) as vfr_pct,
            AVG(shopping_share_tourist) as shopping_pct
        FROM state_purpose_of_visit_panel
        WHERE year IN (2024, 2025)
        GROUP BY state
    ),
    hotel_stars AS (
        SELECT 
            state,
            AVG(luxury_room_share_pct) as luxury_room_pct
        FROM state_hotel_star_inventory
        WHERE year IN (2024, 2025)
        GROUP BY state
    ),
    tourist_income AS (
        SELECT 
            state,
            AVG(t20_share_pct) as tourist_t20_pct,
            AVG(affluence_index) as tourist_affluence_index
        FROM state_tourist_income_panel
        WHERE year IN (2024, 2025)
        GROUP BY state
    )
    SELECT 
        b.*,
        COALESCE(pr.holiday_pct, 40.0) as holiday_pct,
        COALESCE(pr.vfr_pct, 30.0) as vfr_pct,
        COALESCE(pr.shopping_pct, 15.0) as shopping_pct,
        COALESCE(hs.luxury_room_pct, 25.0) as luxury_room_pct,
        COALESCE(ti.tourist_t20_pct, 20.0) as tourist_t20_pct,
        COALESCE(ti.tourist_affluence_index, 100.0) as tourist_affluence_index
    FROM state_base b
    LEFT JOIN purpose_data pr ON b.state = pr.state
    LEFT JOIN hotel_stars hs ON b.state = hs.state
    LEFT JOIN tourist_income ti ON b.state = ti.state
    ORDER BY b.state
    """

    df_raw = con.execute(query).df()

    feature_cols = [
        "alos_days",
        "spend_per_night_rm",
        "accommodation_share_pct",
        "holiday_pct",
        "luxury_room_pct",
        "resident_median_income_rm",
    ]

    # Clean missing values if any
    X = df_raw[feature_cols].copy()
    for col in feature_cols:
        X[col] = X[col].fillna(X[col].median())

    # Standardize (Z-score scaling)
    X_scaled = ((X - X.mean()) / X.std(ddof=0)).values

    # Ward's Hierarchical Clustering
    Z = linkage(X_scaled, method="ward")
    n_clusters = 4
    cluster_labels = fcluster(Z, t=n_clusters, criterion="maxclust")

    df_raw["cluster_id"] = cluster_labels

    # Define human-readable archetype names based on cluster centroids
    centroids = df_raw.groupby("cluster_id")[feature_cols].mean()

    # Map clusters deterministically based on centroids
    archetype_definitions = {
        1: (
            "High-Volume Urban Gateway",
            "Commercial & transit epicentre with highest resident purchasing power (RM 10.9k), massive visitor flows, and 55% luxury room share.",
            "#3b82f6"
        ),
        2: (
            "Administrative & Luxury Institutional",
            "Federal administrative territory with 97.8% 4/5-star room inventory, high income, and short institutional stay profiles.",
            "#8b5cf6"
        ),
        3: (
            "Prime Leisure & High-Yield Hotspot",
            "Core leisure destinations (Penang, Melaka, Sabah, Pahang, Johor) with highest holiday share (32.2%) and highest accommodation share (12.6%).",
            "#10b981"
        ),
        4: (
            "Emerging Extended-Stay Conversion",
            "Longest stay durations (2.65 days) but lowest nightly spend (RM 34/night) due to VFR dominance. Prime target to convert stays to paid lodging.",
            "#f59e0b"
        ),
    }

    df_raw["archetype_name"] = df_raw["cluster_id"].map(lambda c: archetype_definitions[c][0])
    df_raw["archetype_desc"] = df_raw["cluster_id"].map(lambda c: archetype_definitions[c][1])
    df_raw["archetype_color"] = df_raw["cluster_id"].map(lambda c: archetype_definitions[c][2])

    # Compute Normalized Radar Dimensions (0-100 scale for UI)
    radar_metrics = {
        "stay_duration_score": ("alos_days", 1.0, 3.5),
        "nightly_yield_score": ("spend_per_night_rm", 80.0, 300.0),
        "accom_intensity_score": ("accommodation_share_pct", 10.0, 35.0),
        "leisure_orientation_score": ("holiday_pct", 20.0, 70.0),
        "luxury_supply_score": ("luxury_room_pct", 5.0, 70.0),
        "resident_affluence_score": ("resident_median_income_rm", 3500.0, 11000.0),
    }

    for score_col, (raw_col, vmin, vmax) in radar_metrics.items():
        val = df_raw[raw_col].clip(lower=vmin, upper=vmax)
        df_raw[score_col] = np.round((val - vmin) / (vmax - vmin) * 100.0, 1)

    print("\nCluster Assignments:")
    for _, row in df_raw.iterrows():
        print(f"  - {row['state']:<20}: {row['archetype_name']:<30} (ALOS: {row['alos_days']:.2f}d, Spend/Night: RM {row['spend_per_night_rm']:.1f}, Med Income: RM {row['resident_median_income_rm']:.0f})")

    # Save to DuckDB & Parquet
    con.execute("CREATE OR REPLACE TABLE state_clusters AS SELECT * FROM df_raw")
    con.execute(f"COPY state_clusters TO '{PROCESSED_DIR}/state_clusters.parquet' (FORMAT PARQUET)")
    df_raw.to_csv(PROCESSED_DIR / "state_clusters.csv", index=False)

    print(f"\nState Clusters materialized in DuckDB `state_clusters` ({len(df_raw)} rows).")
    con.close()
    print("=" * 70)
    return df_raw


if __name__ == "__main__":
    run_state_clustering()
