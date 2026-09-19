"""
Origin-Destination Network & Corridor Classification Module (Stages D & E)
Implements:
1. Out-Strength (origin feeder capacity) and In-Strength (destination volume).
2. Herfindahl-Hirschman Index (HHI) for origin market concentration.
3. 4-Tier Tourism Value Corridor classification based on transparent percentiles.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple
import duckdb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"


def compute_destination_concentration(df_od: pd.DataFrame) -> pd.DataFrame:
    """
    Computes inbound concentration metrics and HHI for each destination state.
    """
    interstate_od = df_od[df_od["is_interstate"]].copy()

    records = []
    destinations = interstate_od["destination"].unique()

    for dest in destinations:
        dest_flows = interstate_od[interstate_od["destination"] == dest].copy()
        total_inbound = dest_flows["tourist_flow_thousands"].sum()

        if total_inbound > 0:
            dest_flows["share"] = (dest_flows["tourist_flow_thousands"] / total_inbound) * 100.0
            hhi = (dest_flows["share"] ** 2).sum()

            top_row = dest_flows.sort_values("tourist_flow_thousands", ascending=False).iloc[0]
            top_origin = top_row["origin"]
            top_share = top_row["share"]

            if hhi < 1500:
                concentration_tier = "Diversified (< 1,500)"
            elif hhi <= 2500:
                concentration_tier = "Moderate (1,500 - 2,500)"
            else:
                concentration_tier = "Highly Concentrated (> 2,500)"
        else:
            hhi = 0.0
            top_origin = "None"
            top_share = 0.0
            concentration_tier = "No Inter-state Inbound"

        records.append({
            "destination": dest,
            "total_inbound_thousands": round(total_inbound, 2),
            "hhi": round(hhi, 2),
            "concentration_tier": concentration_tier,
            "top_feeder_origin": top_origin,
            "top_feeder_share_pct": round(top_share, 2),
        })

    df_conc = pd.DataFrame(records).sort_values("total_inbound_thousands", ascending=False)
    return df_conc


def classify_tourism_corridors(df_state: pd.DataFrame, df_od: pd.DataFrame) -> pd.DataFrame:
    """
    Classifies all inter-state origin-destination corridors into 4 policy categories:
    1. Priority Conversion Corridor
    2. Protect & Deepen
    3. Growth Opportunity
    4. Lower Priority
    """
    interstate_od = df_od[df_od["is_interstate"] & (df_od["tourist_flow_thousands"] > 0)].copy()

    # Merge destination characteristics
    dest_metrics = df_state[[
        "state",
        "alos_days",
        "spend_per_tourist_rm",
        "spend_per_night_rm",
        "accommodation_share",
        "accommodation_expenditure_rm_million"
    ]].rename(columns={
        "state": "destination",
        "alos_days": "dest_alos",
        "spend_per_tourist_rm": "dest_spend_per_tourist",
        "spend_per_night_rm": "dest_spend_per_night",
        "accommodation_share": "dest_accom_share",
        "accommodation_expenditure_rm_million": "dest_accom_expenditure_m"
    })

    merged = interstate_od.merge(dest_metrics, on="destination", how="left")

    # Benchmark thresholds using empirical medians
    flow_median = merged["tourist_flow_thousands"].median()
    alos_median = df_state["alos_days"].median()  # National state median ALOS
    spend_median = df_state["spend_per_tourist_rm"].median()

    def assign_corridor_tier(row):
        high_flow = row["tourist_flow_thousands"] >= flow_median
        strong_yield = (row["dest_alos"] >= alos_median) and (row["dest_spend_per_tourist"] >= spend_median)

        if high_flow and not strong_yield:
            return "Priority Conversion Corridor"
        elif high_flow and strong_yield:
            return "Protect & Deepen"
        elif not high_flow and strong_yield:
            return "Growth Opportunity"
        else:
            return "Lower Strategic Priority"

    merged["corridor_tier"] = merged.apply(assign_corridor_tier, axis=1)

    # Calculate origin's share of destination's inbound market
    dest_totals = merged.groupby("destination")["tourist_flow_thousands"].transform("sum")
    merged["origin_share_of_dest_pct"] = (merged["tourist_flow_thousands"] / dest_totals * 100.0).round(2)

    return merged.sort_values("tourist_flow_thousands", ascending=False)


def run_network_pipeline() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes Stages D and E: Concentration analysis and corridor classification.
    Exports results to DuckDB and Parquet.
    """
    con = duckdb.connect(str(DUCKDB_PATH))
    df_state = con.execute("SELECT * FROM state_year").df()
    df_od = con.execute("SELECT * FROM origin_destination").df()

    df_conc = compute_destination_concentration(df_od)
    df_corridors = classify_tourism_corridors(df_state, df_od)

    conc_parquet = PROCESSED_DIR / "destination_concentration.parquet"
    corr_parquet = PROCESSED_DIR / "corridor_classification.parquet"

    con.execute("CREATE OR REPLACE TABLE destination_concentration AS SELECT * FROM df_conc")
    con.execute("CREATE OR REPLACE TABLE corridor_classification AS SELECT * FROM df_corridors")

    con.execute(f"COPY destination_concentration TO '{conc_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY corridor_classification TO '{corr_parquet}' (FORMAT PARQUET)")
    con.close()

    print(f"Computed concentration for {len(df_conc)} destinations.")
    print(f"Classified {len(df_corridors)} inter-state tourism corridors.")
    return df_conc, df_corridors


if __name__ == "__main__":
    df_conc, df_corridors = run_network_pipeline()
    print("\n=== TOP 5 DESTINATIONS BY INBOUND VOLUME & HHI ===")
    print(df_conc.head().to_string(index=False))

    print("\n=== TOP 10 PRIORITY CONVERSION CORRIDORS ===")
    priority = df_corridors[df_corridors["corridor_tier"] == "Priority Conversion Corridor"]
    cols = ["origin", "destination", "tourist_flow_thousands", "dest_alos", "dest_spend_per_tourist", "corridor_tier"]
    print(priority[cols].head(10).to_string(index=False))
