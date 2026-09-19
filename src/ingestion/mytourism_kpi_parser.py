"""
MyTourism KPI Ingestion Parser (2016–2025)
Extracts official operational indicators from /home/muhammad_adib/dosm/mytourism_kpi/:
  1. Average Occupancy Rates (AOR %) by State (2016–2025)
  2. Hotel & Room Supply by State (2016–2025)
  3. Hotel Guests (Domestic vs. Foreign) by State (2016–2025)
  4. Homestay Sector (Operators, Villages, Rooms, Income, Guest pax) (2023–2024)

Materializes in DuckDB & Parquet:
  - hotel_operations_annual (2016–2025, 160 records)
  - homestay_operations_annual (2023–2024, 28 records)
  - accommodation_capacity (2025 actual operations + 2024 homestays + DTS room supply)
  - enriches state_panel_year (2018–2025 fully populated with operations)
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import duckdb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"
KPI_DIR = ROOT_DIR / "mytourism_kpi"

STATE_LOOKUP: Dict[str, Tuple[str, str, str]] = {
    "JOHOR": ("Johor", "MY-01", "Southern"),
    "KEDAH": ("Kedah", "MY-02", "Northern"),
    "KEDAH & LANGKAWI": ("Kedah", "MY-02", "Northern"),
    "KELANTAN": ("Kelantan", "MY-03", "East Coast"),
    "MELAKA": ("Melaka", "MY-04", "Southern"),
    "NEGERI SEMBILAN": ("Negeri Sembilan", "MY-05", "Central"),
    "N.SEMBILAN": ("Negeri Sembilan", "MY-05", "Central"),
    "PAHANG": ("Pahang", "MY-06", "East Coast"),
    "PULAU PINANG": ("Pulau Pinang", "MY-07", "Northern"),
    "PENANG": ("Pulau Pinang", "MY-07", "Northern"),
    "PERAK": ("Perak", "MY-08", "Northern"),
    "PERLIS": ("Perlis", "MY-09", "Northern"),
    "SELANGOR": ("Selangor", "MY-10", "Central"),
    "TERENGGANU": ("Terengganu", "MY-11", "East Coast"),
    "SABAH": ("Sabah", "MY-12", "Sabah"),
    "SARAWAK": ("Sarawak", "MY-13", "Sarawak"),
    "KUALA LUMPUR": ("W.P. Kuala Lumpur", "MY-14", "Central"),
    "W.P. KUALA LUMPUR": ("W.P. Kuala Lumpur", "MY-14", "Central"),
    "LABUAN": ("W.P. Labuan", "MY-15", "Sabah"),
    "W.P. LABUAN": ("W.P. Labuan", "MY-15", "Sabah"),
    "PUTRAJAYA": ("W.P. Putrajaya", "MY-16", "Central"),
    "W.P. PUTRAJAYA": ("W.P. Putrajaya", "MY-16", "Central"),
}

IGNORE_STATE_KEYWORDS = [
    "PENINSULAR", "MALAYSIA", "GRAND TOTAL", "TOTAL", "DIFFERENCE", "CHANGE", "DIFF", "BY LOCALITY"
]


def normalize_state_name(raw: str) -> Optional[Tuple[str, str, str]]:
    """Standardizes raw state string to (name, code, region) or None if total/subtotal."""
    if not isinstance(raw, str):
        return None
    cleaned = re.sub(r"[\*\d\(\)\%]", "", raw).strip().upper()
    cleaned = re.sub(r"\s+", " ", cleaned)

    for kw in IGNORE_STATE_KEYWORDS:
        if kw == cleaned or cleaned.startswith("MALAYSIA") or cleaned.startswith("TOTAL") or cleaned.startswith("GRAND TOTAL") or cleaned.startswith("PENINSULAR"):
            return None

    if cleaned in STATE_LOOKUP:
        return STATE_LOOKUP[cleaned]

    for k, v in STATE_LOOKUP.items():
        if k in cleaned or cleaned in k:
            return v

    return None


def clean_numeric(val) -> Optional[float]:
    """Cleans numeric values, stripping commas, asterisks, spaces, and %."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace(",", "").replace("%", "").replace("*", "").replace('"', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return None


def parse_hotel_operations() -> pd.DataFrame:
    """Parses AOR, hotel/room supply, and domestic/foreign hotel guests for 2016–2025."""
    years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    state_year_records = {}

    for y in years:
        ydir = KPI_DIR / str(y)
        if not ydir.exists():
            continue

        # 1. Parse AOR
        aor_files = list(ydir.glob("*occupancy*.csv")) + list(ydir.glob("*aor*.csv"))
        if aor_files:
            df_aor = pd.read_csv(aor_files[0])
            # Determine state column (usually 'State' or first column)
            state_col = None
            for col in df_aor.columns:
                if "state" in col.lower() or "locality" in col.lower():
                    state_col = col
                    break
            if not state_col:
                state_col = df_aor.columns[0]

            # Target column for full-year AOR
            target_col = None
            for col in df_aor.columns:
                col_clean = col.lower().replace(" ", "").replace("_", "")
                if "january-december" in col_clean or "jan-dec" in col_clean:
                    target_col = col
                    break
                if ("diff" not in col_clean and "pct_diff" not in col_clean and "change" not in col_clean and "q4" not in col_clean and "oct" not in col_clean and "nov" not in col_clean and col_clean != "dec"):
                    if str(y) in col_clean:
                        target_col = col
                        break

            if target_col:
                for _, row in df_aor.iterrows():
                    match = normalize_state_name(str(row[state_col]))
                    if match:
                        std_name, code, reg = match
                        val = clean_numeric(row[target_col])
                        key = (std_name, y)
                        if key not in state_year_records:
                            state_year_records[key] = {
                                "state": std_name, "state_code": code, "region": reg, "year": y
                            }
                        state_year_records[key]["aor_pct"] = val

        # 2. Parse Hotel & Room Supply
        supply_files = (
            list(ydir.glob("*inventory*.csv"))
            + list(ydir.glob("*room_supply*.csv"))
            + list(ydir.glob("*accommodation_supply*.csv"))
        )
        if supply_files:
            df_sup = pd.read_csv(supply_files[0])
            state_col = None
            for col in df_sup.columns:
                if "state" in col.lower() or "locality" in col.lower():
                    state_col = col
                    break
            if not state_col:
                state_col = df_sup.columns[0]

            hotel_col = None
            room_col = None
            for col in df_sup.columns:
                col_clean = col.lower().replace(" ", "").replace("_", "")
                if ("comp" not in col_clean and "diff" not in col_clean and "change" not in col_clean):
                    if str(y) in col_clean:
                        if "hotel" in col_clean:
                            hotel_col = col
                        elif "room" in col_clean:
                            room_col = col
                    elif hotel_col is None and "hotel" in col_clean:
                        hotel_col = col
                    elif room_col is None and "room" in col_clean:
                        room_col = col

            for _, row in df_sup.iterrows():
                match = normalize_state_name(str(row[state_col]))
                if match:
                    std_name, code, reg = match
                    key = (std_name, y)
                    if key not in state_year_records:
                        state_year_records[key] = {
                            "state": std_name, "state_code": code, "region": reg, "year": y
                        }
                    if hotel_col and hotel_col in row:
                        state_year_records[key]["hotels_count"] = clean_numeric(row[hotel_col])
                    if room_col and room_col in row:
                        state_year_records[key]["rooms_count"] = clean_numeric(row[room_col])

        # 3. Parse Hotel Guests (Domestic vs Foreign)
        guest_files = list(ydir.glob("*hotel_guests*.csv")) + list(ydir.glob("*hotel-guest*.csv"))
        if guest_files:
            df_gst = pd.read_csv(guest_files[0])
            state_col = None
            for col in df_gst.columns:
                if "state" in col.lower() or "locality" in col.lower():
                    state_col = col
                    break
            if not state_col:
                state_col = df_gst.columns[0]

            dom_col = None
            for_col = None
            tot_col = None

            for col in df_gst.columns:
                col_clean = col.lower().replace(" ", "").replace("_", "")
                if ("change" not in col_clean and "pct" not in col_clean and "diff" not in col_clean):
                    if str(y) in col_clean:
                        if "dom" in col_clean:
                            dom_col = col
                        elif "for" in col_clean:
                            for_col = col
                        elif "tot" in col_clean:
                            tot_col = col
                    elif dom_col is None and "dom" in col_clean:
                        dom_col = col
                    elif for_col is None and "for" in col_clean:
                        for_col = col
                    elif tot_col is None and "tot" in col_clean:
                        tot_col = col

            for _, row in df_gst.iterrows():
                match = normalize_state_name(str(row[state_col]))
                if match:
                    std_name, code, reg = match
                    key = (std_name, y)
                    if key not in state_year_records:
                        state_year_records[key] = {
                            "state": std_name, "state_code": code, "region": reg, "year": y
                        }
                    d_val = clean_numeric(row[dom_col]) if dom_col and dom_col in row else None
                    f_val = clean_numeric(row[for_col]) if for_col and for_col in row else None
                    t_val = clean_numeric(row[tot_col]) if tot_col and tot_col in row else None

                    state_year_records[key]["domestic_hotel_guests"] = d_val
                    state_year_records[key]["foreign_hotel_guests"] = f_val
                    state_year_records[key]["total_hotel_guests"] = t_val

                    if t_val and t_val > 0 and f_val is not None:
                        state_year_records[key]["foreign_guest_share_pct"] = round((f_val / t_val) * 100.0, 2)
                    elif d_val is not None and f_val is not None and (d_val + f_val) > 0:
                        state_year_records[key]["foreign_guest_share_pct"] = round((f_val / (d_val + f_val)) * 100.0, 2)
                        state_year_records[key]["total_hotel_guests"] = d_val + f_val

    df_res = pd.DataFrame(list(state_year_records.values()))
    df_res = df_res.sort_values(by=["year", "state_code"]).reset_index(drop=True)
    return df_res


def parse_homestay_operations() -> pd.DataFrame:
    """Parses Homestay operators, villages, rooms, income, and guest pax for 2023–2024."""
    years = [2023, 2024]
    records = []

    for y in years:
        ydir = KPI_DIR / str(y)
        op_files = list(ydir.glob("*homestay_operators*.csv"))
        gst_files = list(ydir.glob("*homestay_guests*.csv"))

        if not op_files or not gst_files:
            continue

        df_op = pd.read_csv(op_files[0])
        df_gst = pd.read_csv(gst_files[0])

        op_dict = {}
        for _, row in df_op.iterrows():
            match = normalize_state_name(str(row.iloc[0]))
            if match:
                std_name, code, reg = match
                op_dict[std_name] = {
                    "no_of_homestays": clean_numeric(row.get("no_of_homestays", row.get("NO. OF HOMESTAYS"))),
                    "no_of_villages": clean_numeric(row.get("no_of_villages", row.get("NO. OF VILLAGES"))),
                    "no_of_operators": clean_numeric(row.get("no_of_operators", row.get("NO. OF OPERATORS"))),
                    "no_of_rooms": clean_numeric(row.get("no_of_rooms", row.get("NO. OF ROOMS"))),
                }

        for _, row in df_gst.iterrows():
            match = normalize_state_name(str(row.iloc[0]))
            if match:
                std_name, code, reg = match
                inc = clean_numeric(row.get("total_income_rm", row.get("TOTAL INCOME (RM)")))
                dom = clean_numeric(row.get("domestic_pax", row.get("TOURIST ARRIVALS DOMESTIC")))
                fore = clean_numeric(row.get("foreigner_pax", row.get("TOURIST ARRIVALS FOREIGNER")))
                tot = clean_numeric(row.get("total_pax", row.get("TOURIST ARRIVALS TOTAL")))

                rec = {
                    "year": y,
                    "state": std_name,
                    "state_code": code,
                    "region": reg,
                    "total_income_rm": inc,
                    "domestic_homestay_guests": dom,
                    "foreign_homestay_guests": fore,
                    "total_homestay_guests": tot,
                    "income_per_guest_rm": round(inc / tot, 2) if inc and tot and tot > 0 else None,
                }
                if std_name in op_dict:
                    rec.update(op_dict[std_name])
                records.append(rec)

    df_homestay = pd.DataFrame(records)
    if not df_homestay.empty:
        df_homestay = df_homestay.sort_values(by=["year", "state_code"]).reset_index(drop=True)
    return df_homestay


def build_accommodation_capacity_table(df_hotel: pd.DataFrame, df_homestay: pd.DataFrame) -> pd.DataFrame:
    """Builds unified accommodation_capacity table linking 2025 operations, 2024 homestay, and DTS 2025 supply."""
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df_state_2025 = con.execute("SELECT state, total_rooms AS dts_rooms_2025, total_hotels AS dts_hotels_2025, star_room_share_pct FROM state_year").df()
    con.close()

    # 2025 actual operations
    hotel_2025 = df_hotel[df_hotel["year"] == 2025].copy()
    hotel_2025 = hotel_2025.rename(columns={
        "aor_pct": "aor_2025_pct",
        "rooms_count": "hotel_rooms_2025",
        "hotels_count": "hotels_count_2025",
        "domestic_hotel_guests": "domestic_guests_2025",
        "foreign_hotel_guests": "foreign_guests_2025",
        "total_hotel_guests": "total_hotel_guests_2025",
        "foreign_guest_share_pct": "foreign_guest_share_2025_pct",
    }).drop(columns=["year"], errors="ignore")

    # 2024 operations for reference
    hotel_2024 = df_hotel[df_hotel["year"] == 2024].copy()
    hotel_2024 = hotel_2024[["state", "aor_pct", "rooms_count"]].rename(columns={
        "aor_pct": "aor_2024_pct",
        "rooms_count": "hotel_rooms_2024"
    })

    # Homestay 2024
    homestay_2024 = df_homestay[df_homestay["year"] == 2024].copy()
    homestay_2024 = homestay_2024[[
        "state", "no_of_homestays", "no_of_operators", "no_of_rooms", "total_income_rm", "total_homestay_guests"
    ]].rename(columns={
        "no_of_homestays": "homestays_2024",
        "no_of_operators": "homestay_operators_2024",
        "no_of_rooms": "homestay_rooms_2024",
        "total_income_rm": "homestay_income_2024_rm",
        "total_homestay_guests": "homestay_guests_2024"
    })

    cap = hotel_2025.merge(hotel_2024, on="state", how="left")
    cap = cap.merge(homestay_2024, on="state", how="left")
    cap = cap.merge(df_state_2025, on="state", how="left")

    cap["homestays_2024"] = cap["homestays_2024"].fillna(0)
    cap["homestay_rooms_2024"] = cap["homestay_rooms_2024"].fillna(0)
    cap["homestay_operators_2024"] = cap["homestay_operators_2024"].fillna(0)
    return cap


def enrich_state_panel_year(df_hotel: pd.DataFrame, df_homestay: pd.DataFrame):
    """Enriches state_panel_year (2018–2025 fully populated with operations data)."""
    con = duckdb.connect(str(DUCKDB_PATH))
    panel = con.execute("SELECT * FROM state_panel_year").df()

    # Drop old operational columns if present
    clean_cols = [
        "aor_pct", "domestic_hotel_guests", "foreign_hotel_guests", "total_hotel_guests",
        "foreign_guest_share_pct", "hotel_rooms_kpi", "hotels_count_kpi",
        "homestay_rooms", "homestay_operators"
    ]
    panel = panel.drop(columns=[c for c in clean_cols if c in panel.columns], errors="ignore")

    # Hotel ops merge columns
    h_merge = df_hotel[[
        "state", "year", "aor_pct", "rooms_count", "hotels_count",
        "domestic_hotel_guests", "foreign_hotel_guests", "total_hotel_guests", "foreign_guest_share_pct"
    ]].rename(columns={"rooms_count": "hotel_rooms_kpi", "hotels_count": "hotels_count_kpi"})

    panel = panel.merge(h_merge, on=["state", "year"], how="left")

    # Homestay merge columns (2023-2024)
    if not df_homestay.empty:
        hs_merge = df_homestay[["state", "year", "no_of_rooms", "no_of_operators"]].rename(
            columns={"no_of_rooms": "homestay_rooms", "no_of_operators": "homestay_operators"}
        )
        panel = panel.merge(hs_merge, on=["state", "year"], how="left")
    else:
        panel["homestay_rooms"] = None
        panel["homestay_operators"] = None

    # Write back to DuckDB & Parquet
    con.execute("CREATE OR REPLACE TABLE state_panel_year AS SELECT * FROM panel")
    panel_parquet = PROCESSED_DIR / "state_panel_year.parquet"
    con.execute(f"COPY state_panel_year TO '{panel_parquet}' (FORMAT PARQUET)")
    con.close()
    print("Successfully enriched state_panel_year (2018–2025) with hotel operations.")


def run_mytourism_kpi_ingestion():
    """Main execution function."""
    print("Starting MyTourism KPI Ingestion (2016–2025)...")
    df_hotel = parse_hotel_operations()
    print(f"  Parsed {len(df_hotel)} hotel operations records across years {df_hotel['year'].min()} to {df_hotel['year'].max()}.")

    df_homestay = parse_homestay_operations()
    print(f"  Parsed {len(df_homestay)} homestay records across years {df_homestay['year'].min()} to {df_homestay['year'].max()}.")

    df_capacity = build_accommodation_capacity_table(df_hotel, df_homestay)
    print(f"  Constructed accommodation_capacity table with {len(df_capacity)} state records.")

    # Export to DuckDB & Parquet
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE hotel_operations_annual AS SELECT * FROM df_hotel")
    con.execute("CREATE OR REPLACE TABLE homestay_operations_annual AS SELECT * FROM df_homestay")
    con.execute("CREATE OR REPLACE TABLE accommodation_capacity AS SELECT * FROM df_capacity")

    con.execute(f"COPY hotel_operations_annual TO '{PROCESSED_DIR / 'hotel_operations_annual.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY homestay_operations_annual TO '{PROCESSED_DIR / 'homestay_operations_annual.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY accommodation_capacity TO '{PROCESSED_DIR / 'accommodation_capacity.parquet'}' (FORMAT PARQUET)")
    con.close()

    enrich_state_panel_year(df_hotel, df_homestay)
    print("MyTourism KPI Ingestion (2016–2025) successfully complete.")


if __name__ == "__main__":
    run_mytourism_kpi_ingestion()
