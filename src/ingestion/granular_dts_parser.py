"""
Granular DTS Sub-Table Parser (2025).
Extracts root-cause structural drivers across all 16 Malaysian States & FTs:
  - Jadual 12: Types of Accommodation (Paid Commercial vs. Unpaid VFR)
  - Jadual 8:  Purpose of Visit (Holiday/Leisure vs. VFR vs. Business)
  - Jadual 11: Mode of Transport (Private Vehicle vs. Air vs. Bus/Train)
  - Jadual 13a: Household Income Demographics (B40, M40, T20, Affluence Index)
  - Jadual 14: Hotel & Room Inventory (Supply Capacity & Star Ratings)

Exports 'state_granular_profile' to DuckDB and Parquet.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import duckdb
import openpyxl
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"
STATE_DIR_2025 = ROOT_DIR / "data/dts/2025/state"

STATE_METADATA: Dict[str, Dict] = {
    "JOHOR": {"name": "Johor", "code": "MY-01", "region": "Southern"},
    "KEDAH": {"name": "Kedah", "code": "MY-02", "region": "Northern"},
    "KELANTAN": {"name": "Kelantan", "code": "MY-03", "region": "East Coast"},
    "MELAKA": {"name": "Melaka", "code": "MY-04", "region": "Southern"},
    "NEGERI SEMBILAN": {"name": "Negeri Sembilan", "code": "MY-05", "region": "Central"},
    "PAHANG": {"name": "Pahang", "code": "MY-06", "region": "East Coast"},
    "PULAU PINANG": {"name": "Pulau Pinang", "code": "MY-07", "region": "Northern"},
    "PERAK": {"name": "Perak", "code": "MY-08", "region": "Northern"},
    "PERLIS": {"name": "Perlis", "code": "MY-09", "region": "Northern"},
    "SELANGOR": {"name": "Selangor", "code": "MY-10", "region": "Central"},
    "TERENGGANU": {"name": "Terengganu", "code": "MY-11", "region": "East Coast"},
    "SABAH": {"name": "Sabah", "code": "MY-12", "region": "East Malaysia"},
    "SARAWAK": {"name": "Sarawak", "code": "MY-13", "region": "East Malaysia"},
    "W.P. KUALA LUMPUR": {"name": "W.P. Kuala Lumpur", "code": "MY-14", "region": "Central"},
    "W.P. LABUAN": {"name": "W.P. Labuan", "code": "MY-15", "region": "East Malaysia"},
    "W.P. PUTRAJAYA": {"name": "W.P. Putrajaya", "code": "MY-16", "region": "Central"},
}


def match_state_from_path(filepath: Path) -> str:
    fname = filepath.name.upper()
    if "KUALA LUMPUR" in fname:
        return "W.P. KUALA LUMPUR"
    if "LABUAN" in fname:
        return "W.P. LABUAN"
    if "PUTRAJAYA" in fname:
        return "W.P. PUTRAJAYA"
    if "PINANG" in fname or "PENANG" in fname:
        return "PULAU PINANG"
    if "SEMBILAN" in fname:
        return "NEGERI SEMBILAN"
    for k in STATE_METADATA:
        if k in fname:
            return k
    raise ValueError(f"Could not identify state from filename: {filepath.name}")


def clean_num(val) -> Optional[float]:
    if val is None:
        return None
    val_str = str(val).replace(",", "").replace("-", "").strip()
    if not val_str:
        return 0.0
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    return float(match.group()) if match else None


def parse_state_granular(filepath: Path) -> Dict:
    state_key = match_state_from_path(filepath)
    meta = STATE_METADATA[state_key]

    wb = openpyxl.load_workbook(filepath, data_only=True)

    # 1. Parse Jadual 11 & 12 (Transport Modes & Accommodation Types)
    ws11_12 = wb["Jadual 11 & 12"]

    # --- Mode of Transport (Jadual 11, top half, col 7 is 2025 Tourists %) ---
    air_share = 0.0
    private_veh_share = 0.0
    bus_share = 0.0
    train_share = 0.0

    for r in range(7, 18):
        lbl = str(ws11_12.cell(r, 1).value or "").lower()
        val = clean_num(ws11_12.cell(r, 7).value)
        if val is not None:
            if "udara" in lbl or "air" in lbl:
                air_share = val
            elif "persendirian" in lbl or "private" in lbl:
                private_veh_share = val
            elif "bas" in lbl or "bus" in lbl:
                bus_share = val
            elif "kereta api" in lbl or "train" in lbl:
                train_share = val

    # --- Type of Accommodation (Jadual 12, bottom half, col 6 is 2025 %) ---
    hotel_share = 0.0
    chalet_share = 0.0
    apt_share = 0.0
    homestay_share = 0.0
    rest_house_share = 0.0
    vfr_accom_share = 0.0

    for r in range(20, min(40, ws11_12.max_row + 1)):
        lbl = str(ws11_12.cell(r, 1).value or "").lower()
        val = clean_num(ws11_12.cell(r, 6).value)
        if val is not None:
            if "saudara" in lbl or "relatives" in lbl:
                vfr_accom_share = val
            elif "hotel" in lbl:
                hotel_share = val
            elif "chalet" in lbl:
                chalet_share = val
            elif "apartmen" in lbl or "apartment" in lbl:
                apt_share = val
            elif "inap desa" in lbl or "homestay" in lbl:
                homestay_share = val
            elif "rumah rehat" in lbl or "rest house" in lbl:
                rest_house_share = val

    paid_commercial_share = hotel_share + chalet_share + apt_share + homestay_share + rest_house_share

    # 2. Parse Jadual 8 (Purpose of Visit)
    ws8 = wb["Jadual 8"]
    holiday_share = 0.0
    vfr_purpose_share = 0.0
    shopping_purpose_share = 0.0
    medical_share = 0.0
    business_share = 0.0

    # In Jadual 8: Col 5 has purpose label for tourists, Col 6 has Percentage share (%)
    for r in range(6, min(17, ws8.max_row + 1)):
        lbl = str(ws8.cell(r, 5).value or "").lower()
        val = clean_num(ws8.cell(r, 6).value)
        if val is not None:
            if "percutian" in lbl or "holiday" in lbl or "leisure" in lbl:
                holiday_share = val
            elif "saudara" in lbl or "relatives" in lbl:
                vfr_purpose_share = val
            elif "membeli-belah" in lbl or "shopping" in lbl:
                shopping_purpose_share = val
            elif "perubatan" in lbl or "medical" in lbl or "wellness" in lbl:
                medical_share = val
            elif "rasmi" in lbl or "perniagaan" in lbl or "business" in lbl or "pendidikan" in lbl:
                business_share = val

    # 3. Parse Jadual 13a (Household Income Demographics)
    b40_share = 0.0
    m40_share = 0.0
    t20_share = 0.0

    if "Jadual 13a" in wb.sheetnames:
        ws13a = wb["Jadual 13a"]
        # Col 2 has income bracket, Col 4 has 2025 (%)
        low_inc = []
        for r in range(7, min(15, ws13a.max_row + 1)):
            lbl = str(ws13a.cell(r, 2).value or "").lower()
            val = clean_num(ws13a.cell(r, 4).value)
            if val is not None:
                if "1,000" in lbl or "3,000" in lbl or "5,000" in lbl:
                    low_inc.append(val)
                elif "10,000" in lbl and "≥" not in lbl and ">" not in lbl:
                    m40_share = val
                elif "≥ 10,001" in lbl or "> 10,000" in lbl or "10,001" in lbl:
                    t20_share = val
        b40_share = sum(low_inc)

    affluence_index = round((m40_share * 1.0) + (t20_share * 2.0), 2)

    # 4. Parse Jadual 14 & 15 (Hotel & Room Inventory)
    total_hotels = 0
    total_rooms = 0
    star_5_rooms = 0
    star_4_rooms = 0
    star_3_rooms = 0

    if "Jadual 14 & 15" in wb.sheetnames:
        ws14 = wb["Jadual 14 & 15"]
        for r in range(5, min(20, ws14.max_row + 1)):
            lbl = str(ws14.cell(r, 1).value or "").lower()
            h_count = clean_num(ws14.cell(r, 3).value) or 0
            r_count = clean_num(ws14.cell(r, 6).value) or 0

            if "5-bintang" in lbl or "5-star" in lbl:
                star_5_rooms = int(r_count)
            elif "4-bintang" in lbl or "4-star" in lbl:
                star_4_rooms = int(r_count)
            elif "3-bintang" in lbl or "3-star" in lbl:
                star_3_rooms = int(r_count)
            elif "jumlah" in lbl or "total" in lbl:
                total_hotels = int(h_count)
                total_rooms = int(r_count)

    wb.close()

    star_rated_rooms = star_5_rooms + star_4_rooms + star_3_rooms
    star_room_share_pct = round((star_rated_rooms / total_rooms * 100.0), 2) if total_rooms > 0 else 0.0

    return {
        "state": meta["name"],
        "state_code": meta["code"],
        "region": meta["region"],
        # Accommodation Structure
        "paid_commercial_share_pct": round(paid_commercial_share, 2),
        "unpaid_vfr_share_pct": round(vfr_accom_share, 2),
        "hotel_share_pct": round(hotel_share, 2),
        "homestay_share_pct": round(homestay_share, 2),
        "apartment_share_pct": round(apt_share, 2),
        # Purpose of Visit
        "holiday_leisure_share_pct": round(holiday_share, 2),
        "vfr_purpose_share_pct": round(vfr_purpose_share, 2),
        "shopping_purpose_share_pct": round(shopping_purpose_share, 2),
        "medical_wellness_share_pct": round(medical_share, 2),
        "business_mice_share_pct": round(business_share, 2),
        # Mode of Transport
        "private_vehicle_share_pct": round(private_veh_share, 2),
        "air_transport_share_pct": round(air_share, 2),
        "bus_transport_share_pct": round(bus_share, 2),
        "train_transport_share_pct": round(train_share, 2),
        # Income & Affluence
        "b40_share_pct": round(b40_share, 2),
        "m40_share_pct": round(m40_share, 2),
        "t20_share_pct": round(t20_share, 2),
        "affluence_index": affluence_index,
        # Hotel Supply Capacity
        "total_hotels": total_hotels,
        "total_rooms": total_rooms,
        "star_rated_rooms": star_rated_rooms,
        "star_room_share_pct": star_room_share_pct,
    }


def run_granular_ingestion() -> pd.DataFrame:
    print("Ingesting Granular DTS Sub-Tables for all 16 Malaysian States...")
    files = sorted(list(STATE_DIR_2025.glob("*.xlsx")))
    if not files:
        raise FileNotFoundError(f"No 2025 state files found in {STATE_DIR_2025}")

    records = []
    for f in files:
        rec = parse_state_granular(f)
        records.append(rec)
        print(f"  Processed {rec['state']:18s} | Paid Accom: {rec['paid_commercial_share_pct']:5.1f}% | Unpaid VFR: {rec['unpaid_vfr_share_pct']:5.1f}% | Holiday: {rec['holiday_leisure_share_pct']:5.1f}%")

    df_granular = pd.DataFrame(records).sort_values("state")

    # Save to DuckDB and Parquet
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE state_granular_profile AS SELECT * FROM df_granular")
    con.execute(f"COPY state_granular_profile TO '{PROCESSED_DIR / 'state_granular_profile.parquet'}' (FORMAT PARQUET)")
    con.close()

    print(f"\nSuccessfully created state_granular_profile with {len(df_granular)} state records.")
    return df_granular


if __name__ == "__main__":
    df = run_granular_ingestion()
