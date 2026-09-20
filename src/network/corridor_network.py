"""
Origin-Destination Network & Corridor Classification Module (Stages D & E)
Implements:
1. Out-Strength (origin feeder capacity) and In-Strength (destination volume).
2. Herfindahl-Hirschman Index (HHI) for origin market concentration:
   - interstate_origin_hhi: 15 external feeder states only (shares sum to 100%)
   - all_origin_hhi: all 16 origins including intra-state stayers
   - intrastate_share_pct: destination residents' share of domestic trips
3. 4-Tier Tourism Value Corridor classification computed annually:
   - Priority Conversion Corridor
   - Protect & Deepen
   - Growth Opportunity
   - Lower Strategic Priority
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


def compute_destination_concentration_panel(df_od_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Computes inbound concentration metrics, HHI, and intra-state shares
    for each destination state across all years.
    """
    records = []
    for (year, dest), grp in df_od_panel.groupby(["year", "destination"]):
        total_all = grp["tourist_flow_thousands"].sum()
        intra_row = grp[~grp["is_interstate"]]
        intra_flow = intra_row["tourist_flow_thousands"].sum() if not intra_row.empty else 0.0
        intrastate_share_pct = round((intra_flow / total_all * 100.0), 2) if total_all > 0 else 0.0

        # 1. All-origin HHI (including intra-state stayers)
        if total_all > 0:
            shares_all = (grp["tourist_flow_thousands"] / total_all) * 100.0
            hhi_all = round(float((shares_all ** 2).sum()), 2)
            top_all_row = grp.sort_values("tourist_flow_thousands", ascending=False).iloc[0]
            top_all_state = top_all_row["origin"]
            top_all_share = round(float(shares_all.loc[top_all_row.name]), 2)
        else:
            hhi_all = np.nan
            top_all_state = "None"
            top_all_share = 0.0

        # 2. Interstate-only HHI (15 external feeder states)
        grp_inter = grp[grp["is_interstate"]].copy()
        total_inter = grp_inter["tourist_flow_thousands"].sum()
        if total_inter > 0:
            shares_inter = (grp_inter["tourist_flow_thousands"] / total_inter) * 100.0
            hhi_inter = round(float((shares_inter ** 2).sum()), 2)
            top_inter_row = grp_inter.sort_values("tourist_flow_thousands", ascending=False).iloc[0]
            top_inter_state = top_inter_row["origin"]
            top_inter_share = round(float(shares_inter.loc[top_inter_row.name]), 2)
            if hhi_inter < 1500:
                inter_tier = "Diversified (< 1,500)"
            elif hhi_inter <= 2500:
                inter_tier = "Moderate (1,500 - 2,500)"
            else:
                inter_tier = "Highly Concentrated (> 2,500)"
        else:
            hhi_inter = np.nan
            top_inter_state = "None"
            top_inter_share = 0.0
            inter_tier = "No Inter-state Inbound"

        records.append({
            "year": int(year),
            "destination": dest,
            "total_inbound_thousands": round(total_all, 2),
            "interstate_inbound_thousands": round(total_inter, 2),
            "intrastate_tourists_thousands": round(intra_flow, 2),
            "intrastate_share_pct": intrastate_share_pct,
            "top_feeder_origin": top_inter_state,
            "top_feeder_share_pct": top_inter_share,
            "interstate_origin_hhi": hhi_inter,
            "all_origin_hhi": hhi_all,
            "hhi": hhi_inter,  # Default for downstream views
            "concentration_tier": inter_tier,
        })

    df_conc = pd.DataFrame(records).sort_values(["year", "interstate_inbound_thousands"], ascending=[True, False])
    return df_conc


def classify_tourism_corridors_panel(df_state_panel: pd.DataFrame, df_od_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Classifies inter-state origin-destination corridors into 4 policy categories annually:
    1. Priority Conversion Corridor
    2. Protect & Deepen
    3. Growth Opportunity
    4. Lower Strategic Priority
    """
    interstate_od = df_od_panel[df_od_panel["is_interstate"]].copy()

    # Destination metrics by year
    dest_metrics = df_state_panel[[
        "year",
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

    merged = interstate_od.merge(dest_metrics, on=["year", "destination"], how="left")

    classified_chunks = []
    for yr, group in merged.groupby("year"):
        grp = group.copy()
        # Annual empirical medians
        flow_median = grp["tourist_flow_thousands"].median()
        alos_median = grp["dest_alos"].median()
        spend_median = grp["dest_spend_per_tourist"].median()

        def assign_tier(row):
            flow = row["tourist_flow_thousands"]
            alos = row["dest_alos"]
            spt = row["dest_spend_per_tourist"]

            if pd.isna(flow) or pd.isna(alos) or pd.isna(spt):
                return "Unclassified (Missing Data)"

            high_flow = flow >= flow_median
            strong_yield = (alos >= alos_median) and (spt >= spend_median)

            if high_flow and not strong_yield:
                return "Priority Conversion Corridor"
            elif high_flow and strong_yield:
                return "Protect & Deepen"
            elif not high_flow and strong_yield:
                return "Growth Opportunity"
            else:
                return "Lower Strategic Priority"

        grp["corridor_tier"] = grp.apply(assign_tier, axis=1)

        # Origin share of destination inbound
        dest_totals = grp.groupby("destination")["tourist_flow_thousands"].transform("sum")
        grp["origin_share_of_dest_pct"] = np.where(
            dest_totals > 0,
            (grp["tourist_flow_thousands"] / dest_totals * 100.0).round(2),
            0.0
        )
        classified_chunks.append(grp)

    df_all_classified = pd.concat(classified_chunks, ignore_index=True)
    return df_all_classified.sort_values(["year", "tourist_flow_thousands"], ascending=[True, False])


def run_network_pipeline() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes Stages D and E: Concentration analysis and corridor classification
    both longitudinally (2018-2025 panel) and for the 2025 baseline snapshot.
    """
    con = duckdb.connect(str(DUCKDB_PATH))
    df_state_panel = con.execute("SELECT * FROM state_panel_year").df()
    df_od_panel = con.execute("SELECT * FROM origin_destination_panel").df()

    df_conc_panel = compute_destination_concentration_panel(df_od_panel)
    df_corridors_panel = classify_tourism_corridors_panel(df_state_panel, df_od_panel)

    # 2025 snapshots
    df_conc_2025 = df_conc_panel[df_conc_panel["year"] == 2025].copy()
    df_corridors_2025 = df_corridors_panel[df_corridors_panel["year"] == 2025].copy()

    # Export to DuckDB & Parquet
    con.execute("CREATE OR REPLACE TABLE destination_concentration_panel AS SELECT * FROM df_conc_panel")
    con.execute("CREATE OR REPLACE TABLE destination_concentration AS SELECT * FROM df_conc_2025")
    con.execute("CREATE OR REPLACE TABLE corridor_classification_panel AS SELECT * FROM df_corridors_panel")
    con.execute("CREATE OR REPLACE TABLE corridor_classification AS SELECT * FROM df_corridors_2025")

    conc_p_parquet = PROCESSED_DIR / "destination_concentration_panel.parquet"
    conc_parquet = PROCESSED_DIR / "destination_concentration.parquet"
    corr_p_parquet = PROCESSED_DIR / "corridor_classification_panel.parquet"
    corr_parquet = PROCESSED_DIR / "corridor_classification.parquet"

    con.execute(f"COPY destination_concentration_panel TO '{conc_p_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY destination_concentration TO '{conc_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY corridor_classification_panel TO '{corr_p_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY corridor_classification TO '{corr_parquet}' (FORMAT PARQUET)")
    con.close()

    print(f"Computed concentration for {len(df_conc_panel)} destination-years ({len(df_conc_2025)} in 2025).")
    print(f"Classified {len(df_corridors_panel)} corridor-years ({len(df_corridors_2025)} in 2025).")
    return df_conc_2025, df_corridors_2025


if __name__ == "__main__":
    df_conc, df_corridors = run_network_pipeline()
    print("\n=== 2025 DESTINATION CONCENTRATION & HHI SEPARATION ===")
    cols_hhi = ["destination", "interstate_inbound_thousands", "intrastate_share_pct", "top_feeder_origin", "interstate_origin_hhi", "all_origin_hhi"]
    print(df_conc[cols_hhi].head(8).to_string(index=False))

    print("\n=== 2025 TOP 10 PRIORITY CONVERSION CORRIDORS ===")
    priority = df_corridors[df_corridors["corridor_tier"] == "Priority Conversion Corridor"]
    cols = ["origin", "destination", "tourist_flow_thousands", "dest_alos", "dest_spend_per_tourist", "corridor_tier"]
    print(priority[cols].head(10).to_string(index=False))
