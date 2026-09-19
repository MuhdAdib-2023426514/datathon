"""
Multi-Year Origin-Destination Panel Ingestion Module (2018–2025)
Parses all 8 national DTS publications (TABLE DTS 2018 to 2025, Sheet 10 / Jadual 10).
Extracts all 2,048 directed corridor flows (256 pairs x 8 years).
Enriches corridors with geospatial distance, cross-region flags, destination operations,
longitudinal HHI concentration, and COVID recovery trajectory classifications.

Adheres strictly to:
- AGENTS.md (Sections 3, 5, 7 - Stage D & E)
- .agents/skills/tourism-corridor-scenarios/SKILL.md
- .agents/skills/malaysia-geo-standards/SKILL.md
- .agents/skills/data-pipeline-validation/SKILL.md
"""

import glob
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import duckdb
import numpy as np
import openpyxl
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DTS_DIR = ROOT_DIR / "data/dts"
PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

# Canonical metadata for all 16 Malaysian States and Federal Territories
STATE_METADATA: Dict[str, Dict] = {
    "Johor": {"code": "MY-01", "region": "Southern", "lat": 1.9344, "lon": 103.3587},
    "Kedah": {"code": "MY-02", "region": "Northern", "lat": 6.1184, "lon": 100.3685},
    "Kelantan": {"code": "MY-03", "region": "East Coast", "lat": 5.3117, "lon": 102.0040},
    "Melaka": {"code": "MY-04", "region": "Southern", "lat": 2.2458, "lon": 102.2741},
    "Negeri Sembilan": {"code": "MY-05", "region": "Central", "lat": 2.7258, "lon": 102.2430},
    "Pahang": {"code": "MY-06", "region": "East Coast", "lat": 3.8126, "lon": 102.3256},
    "Pulau Pinang": {"code": "MY-07", "region": "Northern", "lat": 5.4141, "lon": 100.3288},
    "Perak": {"code": "MY-08", "region": "Northern", "lat": 4.6940, "lon": 101.0901},
    "Perlis": {"code": "MY-09", "region": "Northern", "lat": 6.4449, "lon": 100.2048},
    "Selangor": {"code": "MY-10", "region": "Central", "lat": 3.0738, "lon": 101.5183},
    "Terengganu": {"code": "MY-11", "region": "East Coast", "lat": 4.8810, "lon": 103.1167},
    "Sabah": {"code": "MY-12", "region": "East Malaysia", "lat": 5.9788, "lon": 116.0753},
    "Sarawak": {"code": "MY-13", "region": "East Malaysia", "lat": 2.5574, "lon": 113.0012},
    "W.P. Kuala Lumpur": {"code": "MY-14", "region": "Central", "lat": 3.1390, "lon": 101.6869},
    "W.P. Labuan": {"code": "MY-15", "region": "East Malaysia", "lat": 5.2831, "lon": 115.2308},
    "W.P. Putrajaya": {"code": "MY-16", "region": "Central", "lat": 2.9264, "lon": 101.6964},
}

STATE_COLS = list(STATE_METADATA.keys())


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle geodesic distance between two points in km."""
    R = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def parse_all_od_workbooks() -> pd.DataFrame:
    """
    Parses Table 10 from national DTS workbooks for all years 2018 to 2025.
    Returns a unified DataFrame of 2,048 corridor records.
    """
    all_rows = []

    for year in range(2018, 2026):
        pattern = f"{DTS_DIR}/{year}/national/*.xlsx"
        matched = glob.glob(pattern)
        if not matched:
            raise FileNotFoundError(f"No national workbook found matching: {pattern}")
        file_path = matched[0]

        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet_name = "Jadual 10" if "Jadual 10" in wb.sheetnames else "10"
        ws = wb[sheet_name]

        # In Table 10, origins are in rows 9 to 24
        # Destinations are in cols 5 to 20 (Col 4 is Malaysia total)
        for r_idx, orig_name in enumerate(STATE_COLS, start=9):
            o_meta = STATE_METADATA[orig_name]
            for c_idx, dest_name in enumerate(STATE_COLS, start=5):
                d_meta = STATE_METADATA[dest_name]
                raw_val = ws.cell(r_idx, c_idx).value
                try:
                    flow_k = float(raw_val) if raw_val is not None else 0.0
                except (ValueError, TypeError):
                    flow_k = 0.0

                dist = haversine_distance_km(
                    o_meta["lat"], o_meta["lon"],
                    d_meta["lat"], d_meta["lon"]
                ) if orig_name != dest_name else 0.0

                is_cross_region = (o_meta["region"] == "East Malaysia") != (d_meta["region"] == "East Malaysia")

                all_rows.append({
                    "year": year,
                    "origin": orig_name,
                    "origin_code": o_meta["code"],
                    "origin_region": o_meta["region"],
                    "origin_lat": o_meta["lat"],
                    "origin_lon": o_meta["lon"],
                    "destination": dest_name,
                    "destination_code": d_meta["code"],
                    "destination_region": d_meta["region"],
                    "destination_lat": d_meta["lat"],
                    "destination_lon": d_meta["lon"],
                    "is_interstate": (orig_name != dest_name),
                    "is_cross_region": is_cross_region,
                    "distance_km": dist,
                    "tourist_flow_thousands": round(flow_k, 3)
                })

    df = pd.DataFrame(all_rows)
    print(f"Parsed {len(df)} total raw OD records across 2018–2025.")
    return df


def compute_concentration_and_shares(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes origin share of destination intake and longitudinal HHI market concentration.
    """
    # Destination intake by year (sum across all origins)
    dest_totals = df.groupby(["year", "destination"])["tourist_flow_thousands"].transform("sum")
    df["dest_total_tourists_thousands"] = dest_totals
    df["origin_market_share_pct"] = np.where(
        df["dest_total_tourists_thousands"] > 0,
        (df["tourist_flow_thousands"] / df["dest_total_tourists_thousands"]) * 100.0,
        0.0
    ).round(2)

    # Calculate longitudinal HHI per destination-year
    # HHI = sum((origin_share)^2) where shares are in percentages (0-100)
    hhi_records = []
    for (year, dest), grp in df.groupby(["year", "destination"]):
        total_in = grp["tourist_flow_thousands"].sum()
        if total_in > 0:
            shares = (grp["tourist_flow_thousands"] / total_in) * 100.0
            hhi = round((shares ** 2).sum(), 2)
            # Top feeder
            top_orig = grp.sort_values(by="tourist_flow_thousands", ascending=False).iloc[0]
            top_feeder = top_orig["origin"]
            top_share = round(shares.loc[top_orig.name], 2)
        else:
            hhi = 0.0
            top_feeder = "None"
            top_share = 0.0

        if hhi < 1500:
            hhi_tier = "Diversified (<1,500)"
        elif hhi <= 2500:
            hhi_tier = "Moderate Concentration (1,500 - 2,500)"
        else:
            hhi_tier = "High Concentration (>2,500)"

        hhi_records.append({
            "year": year,
            "destination": dest,
            "total_tourists_thousands": round(total_in, 2),
            "top_feeder_state": top_feeder,
            "top_feeder_share_pct": top_share,
            "hhi": hhi,
            "concentration_tier": hhi_tier
        })

    df_hhi = pd.DataFrame(hhi_records)
    return df, df_hhi


def enrich_with_destination_operations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges destination operational metrics from state_panel_year (ALOS, spend, AOR, rooms).
    """
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df_panel = con.execute("""
        SELECT 
            year,
            state as destination,
            alos_days as dest_alos_days,
            spend_per_night_rm as dest_spend_per_night_rm,
            accommodation_expenditure_rm_million as dest_accommodation_expenditure_rm_million,
            aor_pct as dest_aor_pct,
            hotel_rooms_kpi as dest_rooms_count,
            domestic_hotel_guests as dest_domestic_hotel_guests,
            foreign_hotel_guests as dest_foreign_hotel_guests,
            foreign_guest_share_pct as dest_foreign_guest_share_pct
        FROM state_panel_year
    """).df()
    con.close()

    df_merged = df.merge(df_panel, on=["year", "destination"], how="left")

    # Corridor Economic Yield proxy (flow * spend per tourist in destination)
    # spend_per_tourist = (dest_accommodation_spend_m * 1e6) / (dest_tourists_k * 1e3)
    df_merged["corridor_implied_accom_spend_rm_million"] = np.where(
        df_merged["dest_total_tourists_thousands"] > 0,
        (df_merged["tourist_flow_thousands"] / df_merged["dest_total_tourists_thousands"]) *
        df_merged["dest_accommodation_expenditure_rm_million"],
        0.0
    ).round(2)

    return df_merged


def compute_corridor_trajectories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes corridor recovery rates (2025 vs 2019 pre-COVID peak) and trajectory categories.
    """
    # Extract 2019 baseline flow
    df_2019 = df[df["year"] == 2019][["origin", "destination", "tourist_flow_thousands"]].rename(
        columns={"tourist_flow_thousands": "flow_2019_thousands"}
    )
    df = df.merge(df_2019, on=["origin", "destination"], how="left")

    # Recovery rate vs 2019 (%)
    df["recovery_rate_vs_2019_pct"] = np.where(
        (df["flow_2019_thousands"] > 0) & (df["year"] == 2025),
        (df["tourist_flow_thousands"] / df["flow_2019_thousands"]) * 100.0,
        np.nan
    ).round(1)

    # Classify 2025 trajectory
    def classify_trajectory(row):
        if not row["is_interstate"]:
            return "Intra-State Anchor"
        rec = row["recovery_rate_vs_2019_pct"]
        flow = row["tourist_flow_thousands"]
        if pd.isna(rec):
            return "Unclassified"
        if rec >= 125.0 and flow >= 500.0:
            return "Structural Gainer (Surge)"
        elif rec >= 90.0:
            return "Resilient Anchor"
        elif rec < 75.0 and flow >= 200.0:
            return "Laggard / At-Risk"
        else:
            return "Emerging / Modest Growth"

    # Map trajectory classification
    traj_map = {}
    df_2025 = df[df["year"] == 2025]
    for _, r in df_2025.iterrows():
        traj_map[(r["origin"], r["destination"])] = classify_trajectory(r)

    df["corridor_trajectory_class"] = df.apply(
        lambda r: traj_map.get((r["origin"], r["destination"]), "Unclassified"), axis=1
    )

    return df


def main():
    print("=" * 70)
    print("INGESTING MULTI-YEAR ORIGIN-DESTINATION PANEL (2018–2025)")
    print("=" * 70)

    # 1. Parse raw OD workbooks
    df_od = parse_all_od_workbooks()

    # 2. Compute shares and longitudinal HHI
    df_od, df_hhi = compute_concentration_and_shares(df_od)

    # 3. Enrich with destination operations
    df_od = enrich_with_destination_operations(df_od)

    # 4. Compute trajectory classifications
    df_od = compute_corridor_trajectories(df_od)

    # 5. Materialize to DuckDB and Parquet (using DuckDB's native high-speed Parquet engine)
    parquet_od = PROCESSED_DIR / "origin_destination_panel.parquet"
    parquet_hhi = PROCESSED_DIR / "destination_concentration_panel.parquet"

    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE origin_destination_panel AS SELECT * FROM df_od")
    con.execute("CREATE OR REPLACE TABLE destination_concentration_panel AS SELECT * FROM df_hhi")
    con.execute(f"COPY origin_destination_panel TO '{parquet_od}' (FORMAT PARQUET)")
    con.execute(f"COPY destination_concentration_panel TO '{parquet_hhi}' (FORMAT PARQUET)")
    con.close()

    print(f"\nSuccessfully materialized:")
    print(f"  - origin_destination_panel: {len(df_od)} rows -> DuckDB & {parquet_od.name}")
    print(f"  - destination_concentration_panel: {len(df_hhi)} rows -> DuckDB & {parquet_hhi.name}")

    # Display key highlights
    print("\nSummary of Total Domestic Tourists by Macro Era:")
    print(df_od.groupby("year")["tourist_flow_thousands"].sum().map("{:,.1f}k".format))

    print("\nTop 5 Structural Gainer Corridors (2025 vs 2019):")
    gainers = df_od[(df_od["year"] == 2025) & (df_od["is_interstate"])].sort_values(
        by="recovery_rate_vs_2019_pct", ascending=False
    ).head(5)
    for _, r in gainers.iterrows():
        print(f"  {r['origin']} -> {r['destination']}: {r['tourist_flow_thousands']:,.1f}k (2025) vs {r['flow_2019_thousands']:,.1f}k (2019) [{r['recovery_rate_vs_2019_pct']:.1f}%]")

    print("\n" + "=" * 70)
    print("MULTI-YEAR OD PANEL INGESTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
