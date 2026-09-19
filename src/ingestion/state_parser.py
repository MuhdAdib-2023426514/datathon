"""
State & Origin-Destination Data Ingestion Module (Stage C & D)
Parses all 16 state DTS 2025 publications and the National DTS OD matrix (Sheet 10).
Extracts visitors, tourists, ALOS, detailed expenditure components, and directed inter-state flows.
Standardizes data according to malaysia-geo-standards and data-pipeline-validation skills.
"""

import glob
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import duckdb
import openpyxl
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

STATE_DIR = ROOT_DIR / "data/state"
NATIONAL_DTS_PATH = ROOT_DIR / "data/malaysia/TABLE DTS 2025.xlsx"
PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

# Canonical metadata for all 16 Malaysian States and Federal Territories
STATE_METADATA: Dict[str, Dict] = {
    "JOHOR": {"name": "Johor", "code": "MY-01", "region": "Southern", "lat": 1.9344, "lon": 103.3587},
    "KEDAH": {"name": "Kedah", "code": "MY-02", "region": "Northern", "lat": 6.1184, "lon": 100.3685},
    "KELANTAN": {"name": "Kelantan", "code": "MY-03", "region": "East Coast", "lat": 5.3117, "lon": 102.0040},
    "MELAKA": {"name": "Melaka", "code": "MY-04", "region": "Southern", "lat": 2.2458, "lon": 102.2741},
    "NEGERI SEMBILAN": {"name": "Negeri Sembilan", "code": "MY-05", "region": "Central", "lat": 2.7258, "lon": 102.2430},
    "PAHANG": {"name": "Pahang", "code": "MY-06", "region": "East Coast", "lat": 3.8126, "lon": 102.3256},
    "PULAU PINANG": {"name": "Pulau Pinang", "code": "MY-07", "region": "Northern", "lat": 5.4141, "lon": 100.3288},
    "PERAK": {"name": "Perak", "code": "MY-08", "region": "Northern", "lat": 4.6940, "lon": 101.0901},
    "PERLIS": {"name": "Perlis", "code": "MY-09", "region": "Northern", "lat": 6.4449, "lon": 100.2048},
    "SELANGOR": {"name": "Selangor", "code": "MY-10", "region": "Central", "lat": 3.0738, "lon": 101.5183},
    "TERENGGANU": {"name": "Terengganu", "code": "MY-11", "region": "East Coast", "lat": 4.8810, "lon": 103.1167},
    "SABAH": {"name": "Sabah", "code": "MY-12", "region": "East Malaysia", "lat": 5.9788, "lon": 116.0753},
    "SARAWAK": {"name": "Sarawak", "code": "MY-13", "region": "East Malaysia", "lat": 2.5574, "lon": 113.0012},
    "W.P. KUALA LUMPUR": {"name": "W.P. Kuala Lumpur", "code": "MY-14", "region": "Central", "lat": 3.1390, "lon": 101.6869},
    "W.P. LABUAN": {"name": "W.P. Labuan", "code": "MY-15", "region": "East Malaysia", "lat": 5.2831, "lon": 115.2308},
    "W.P. PUTRAJAYA": {"name": "W.P. Putrajaya", "code": "MY-16", "region": "Central", "lat": 2.9264, "lon": 101.6964},
}


def match_state_key(raw_str: str) -> str:
    """Matches any raw state name or variation to the canonical STATE_METADATA key."""
    cleaned = raw_str.strip().upper()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned in STATE_METADATA:
        return cleaned
    # Variations
    if "KUALA LUMPUR" in cleaned:
        return "W.P. KUALA LUMPUR"
    if "LABUAN" in cleaned:
        return "W.P. LABUAN"
    if "PUTRAJAYA" in cleaned:
        return "W.P. PUTRAJAYA"
    if "PINANG" in cleaned or "PENANG" in cleaned:
        return "PULAU PINANG"
    if "SEMBILAN" in cleaned:
        return "NEGERI SEMBILAN"
    if "MELAKA" in cleaned or "MALACCA" in cleaned:
        return "MELAKA"
    for k in STATE_METADATA:
        if k in cleaned:
            return k
    raise ValueError(f"Unable to match state: '{raw_str}'")


def ingest_all_states(state_dir: Path = STATE_DIR) -> pd.DataFrame:
    """
    Ingests all 16 state publications in data/state/ and builds the tidy state_year table.
    """
    state_files = sorted(glob.glob(str(state_dir / "*.xlsx")))
    if len(state_files) != 16:
        raise ValueError(f"Expected 16 state files, found {len(state_files)}")

    records = []
    for filepath in state_files:
        fname = Path(filepath).name
        raw_key = fname.replace("TABLE OF PUBLICATION DTS 2025 ", "").replace(".xlsx", "")
        state_key = match_state_key(raw_key)
        meta = STATE_METADATA[state_key]

        wb = openpyxl.load_workbook(filepath, data_only=True)

        # 1. Jadual 1: Macro Volume, Receipts, ALOS
        ws1 = wb["Jadual 1"]
        receipts_rm_m = float(ws1.cell(6, 8).value or 0.0)  # Row 6, Col 8 is 2025 (RM Million)
        visitors_k = float(ws1.cell(8, 8).value or 0.0)     # Row 8 is 2025 ('000)
        trips_k = float(ws1.cell(10, 8).value or 0.0)       # Row 10 is 2025 ('000)
        alos_days = float(ws1.cell(16, 8).value or 0.0)     # Row 16 is ALOS (days)

        # 2. Jadual 2 & 3: Overnight Tourists vs Same-Day Excursionists
        ws2 = wb["Jadual 2 & 3"]
        excursionists_k = float(ws2.cell(8, 5).value or 0.0) # Row 8, Col 5 ('000)
        tourists_k = float(ws2.cell(9, 5).value or 0.0)      # Row 9, Col 5 ('000)

        # 3. Jadual 7: Detailed Expenditure Components (values in RM '000 -> convert to RM Million)
        ws7 = wb["Jadual 7"]
        shopping_m = float(ws7.cell(8, 3).value or 0.0) / 1000.0
        fuel_m = float(ws7.cell(9, 3).value or 0.0) / 1000.0
        transport_m = float(ws7.cell(10, 3).value or 0.0) / 1000.0
        food_beverage_m = float(ws7.cell(11, 3).value or 0.0) / 1000.0
        accommodation_m = float(ws7.cell(12, 3).value or 0.0) / 1000.0
        pretrip_package_m = float(ws7.cell(13, 3).value or 0.0) / 1000.0
        other_exp_m = float(ws7.cell(14, 3).value or 0.0) / 1000.0
        household_exp_m = float(ws7.cell(15, 3).value or 0.0) / 1000.0
        total_receipts_m = float(ws7.cell(16, 3).value or 0.0) / 1000.0

        wb.close()

        # Derived Accommodation & Economic Yield Metrics (per AGENTS.md Section 3 & 7)
        # Accommodation Share = Accommodation Expenditure / Total Tourism Expenditure
        accom_share = accommodation_m / total_receipts_m if total_receipts_m > 0 else 0.0

        # Spend Per Visitor (RM) = Accommodation Expenditure (RM) / Domestic Visitors
        spend_per_visitor = (accommodation_m * 1e6) / (visitors_k * 1e3) if visitors_k > 0 else 0.0

        # Spend Per Tourist (RM) = Accommodation Expenditure (RM) / Overnight Tourists
        spend_per_tourist = (accommodation_m * 1e6) / (tourists_k * 1e3) if tourists_k > 0 else 0.0

        # Spend Per Tourist Night (RM) = Accommodation Expenditure (RM) / (Tourists * ALOS)
        tourist_nights_k = tourists_k * alos_days
        spend_per_night = (accommodation_m * 1e6) / (tourist_nights_k * 1e3) if tourist_nights_k > 0 else 0.0

        records.append({
            "year": 2025,
            "state": meta["name"],
            "state_code": meta["code"],
            "region": meta["region"],
            "latitude": meta["lat"],
            "longitude": meta["lon"],
            "visitors_thousands": round(visitors_k, 2),
            "tourists_thousands": round(tourists_k, 2),
            "excursionists_thousands": round(excursionists_k, 2),
            "trips_thousands": round(trips_k, 2),
            "alos_days": round(alos_days, 2),
            "total_expenditure_rm_million": round(total_receipts_m, 2),
            "accommodation_expenditure_rm_million": round(accommodation_m, 2),
            "food_expenditure_rm_million": round(food_beverage_m, 2),
            "shopping_expenditure_rm_million": round(shopping_m, 2),
            "transport_expenditure_rm_million": round(transport_m, 2),
            "fuel_expenditure_rm_million": round(fuel_m, 2),
            "pretrip_package_rm_million": round(pretrip_package_m, 2),
            "other_expenditure_rm_million": round(other_exp_m, 2),
            "household_expenditure_rm_million": round(household_exp_m, 2),
            "accommodation_share": round(accom_share, 4),
            "spend_per_visitor_rm": round(spend_per_visitor, 2),
            "spend_per_tourist_rm": round(spend_per_tourist, 2),
            "spend_per_night_rm": round(spend_per_night, 2),
            "tourist_nights_thousands": round(tourist_nights_k, 2),
        })

    df_state = pd.DataFrame(records).sort_values("total_expenditure_rm_million", ascending=False)
    return df_state


def ingest_origin_destination(national_file: Path = NATIONAL_DTS_PATH) -> pd.DataFrame:
    """
    Ingests Sheet 10 from TABLE DTS 2025.xlsx to build the full 16x16 OD tourist flow table.
    """
    wb = openpyxl.load_workbook(national_file, data_only=True)
    ws10 = wb["10"]

    # Extract destination names from Row 7 (Columns 5 to 20 are the 16 states; Col 4 is Malaysia total)
    dest_col_map = {}
    for col in range(5, 21):
        val = ws10.cell(7, col).value
        if val:
            state_key = match_state_key(str(val))
            dest_col_map[col] = STATE_METADATA[state_key]["name"]

    # Extract origin rows from Rows 9 to 24 (Column 3 has origin name; Row 8 is Malaysia total)
    od_records = []
    for r in range(9, 25):
        raw_origin = ws10.cell(r, 3).value or ""
        origin_key = match_state_key(str(raw_origin))
        origin_name = STATE_METADATA[origin_key]["name"]
        origin_code = STATE_METADATA[origin_key]["code"]

        for col, dest_name in dest_col_map.items():
            flow_val = float(ws10.cell(r, col).value or 0.0)
            is_interstate = (origin_name != dest_name)

            dest_meta = next(m for m in STATE_METADATA.values() if m["name"] == dest_name)

            od_records.append({
                "year": 2025,
                "origin": origin_name,
                "origin_code": origin_code,
                "origin_region": STATE_METADATA[origin_key]["region"],
                "origin_lat": STATE_METADATA[origin_key]["lat"],
                "origin_lon": STATE_METADATA[origin_key]["lon"],
                "destination": dest_name,
                "destination_code": dest_meta["code"],
                "destination_region": dest_meta["region"],
                "destination_lat": dest_meta["lat"],
                "destination_lon": dest_meta["lon"],
                "is_interstate": is_interstate,
                "tourist_flow_thousands": round(flow_val, 3),
            })

    wb.close()
    df_od = pd.DataFrame(od_records)
    return df_od


def export_state_and_od():
    """Ingests both state and OD data, then exports to DuckDB and Parquet."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_state = ingest_all_states()
    df_od = ingest_origin_destination()

    state_parquet = PROCESSED_DIR / "state_year.parquet"
    od_parquet = PROCESSED_DIR / "origin_destination.parquet"

    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE state_year AS SELECT * FROM df_state")
    con.execute("CREATE OR REPLACE TABLE origin_destination AS SELECT * FROM df_od")

    con.execute(f"COPY state_year TO '{state_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY origin_destination TO '{od_parquet}' (FORMAT PARQUET)")
    con.close()

    print(f"Ingested {len(df_state)} states and {len(df_od)} OD flow pairs.")
    print(f"Exported to {state_parquet} and {od_parquet}.")
    return df_state, df_od


if __name__ == "__main__":
    df_state, df_od = export_state_and_od()
    print("\n=== TOP 5 STATES BY EXPENDITURE (2025) ===")
    print(df_state[["state", "visitors_thousands", "tourists_thousands", "alos_days", "accommodation_expenditure_rm_million", "spend_per_tourist_rm"]].head())

    print("\n=== TOP 5 INTER-STATE TOURIST CORRIDORS (2025) ===")
    top_interstate = df_od[df_od["is_interstate"]].sort_values("tourist_flow_thousands", ascending=False)
    print(top_interstate[["origin", "destination", "tourist_flow_thousands"]].head())
