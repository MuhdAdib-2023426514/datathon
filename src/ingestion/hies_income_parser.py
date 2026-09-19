"""
HIES Income & Household Time Series Parser
Ingests official DOSM Household Income & Basic Amenities Survey (HIES) Table 6:
- Sheet 6.1: Number of households ('000) (1995-2024)
- Sheet 6.2: Median monthly household income (RM) (1995-2024)
- Sheet 6.3: Mean monthly household income (RM) (1970-2024)
- Sheet 6.4: Mean monthly household income by income deciles (B40, M40, T20)
- Sheet 6.5: Gross income share of household groups (B40, M40, T20)

Follows AGENTS.md standards:
- Standardize state names against canonical 16 states & Federal Territories
- Preserve status flags: 'official' for survey years (2019, 2022, 2024), 'e' for interpolated years
- Reconcile state totals against national totals
- Materialize to DuckDB and Parquet
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import duckdb
import numpy as np
import openpyxl
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

RAW_FILE = ROOT_DIR / "data/raw/TABLE 6_ TIME SERIES FOR SELECTED STATISTICS ON INCOME.xlsx"
PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

# Canonical state reference table
STATE_MAP = {
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


def clean_state_name(raw_name: str) -> str:
    cleaned = str(raw_name).strip()
    if "Labuan" in cleaned:
        return "W.P. Labuan"
    if "Kuala Lumpur" in cleaned:
        return "W.P. Kuala Lumpur"
    if "Putrajaya" in cleaned:
        return "W.P. Putrajaya"
    if "Penang" in cleaned:
        return "Pulau Pinang"
    return cleaned


def parse_numeric(val) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip().replace("*", "").replace(",", "")
    if s.lower() in ["n.a.", "-", "", "none"]:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def get_year_columns(sheet, header_row: int = 4) -> Tuple[Dict[int, int], List[tuple]]:
    rows = list(sheet.iter_rows(values_only=True))
    header = rows[header_row - 1]
    col_map = {}
    for idx, val in enumerate(header):
        if val is not None:
            s = str(val).strip().replace("*", "")
            if s.isdigit():
                col_map[int(s)] = idx
    return col_map, rows


def extract_state_survey_panel(wb) -> pd.DataFrame:
    """Extract official triennial survey data for all 16 states (1995-2024)."""
    col61, rows61 = get_year_columns(wb["6.1"])
    col62, rows62 = get_year_columns(wb["6.2"])
    col63, rows63 = get_year_columns(wb["6.3"])

    common_years = sorted(list(set(col61.keys()) & set(col62.keys()) & set(col63.keys())))
    records = []

    # State rows are 15 to 30 (0-indexed 14 to 29)
    for r_idx in range(14, 30):
        raw_name = rows61[r_idx][0]
        st_clean = clean_state_name(raw_name)
        if st_clean not in STATE_MAP:
            continue
        meta = STATE_MAP[st_clean]

        for yr in common_years:
            hh_k = parse_numeric(rows61[r_idx][col61[yr]])
            med = parse_numeric(rows62[r_idx][col62[yr]])
            mean = parse_numeric(rows63[r_idx][col63[yr]])

            skewness = round(mean / med, 3) if (mean and med and med > 0) else None

            records.append({
                "year": yr,
                "state": st_clean,
                "state_code": meta["code"],
                "region": meta["region"],
                "households_thousands": round(hh_k, 3) if hh_k is not None else None,
                "households_count": int(round(hh_k * 1000)) if hh_k is not None else None,
                "median_income_rm": round(med, 1) if med is not None else None,
                "mean_income_rm": round(mean, 1) if mean is not None else None,
                "income_skewness_ratio": skewness,
                "data_status": "official_survey",
                "source": "DOSM HIES Table 6",
            })

    df = pd.DataFrame(records).sort_values(["state", "year"]).reset_index(drop=True)
    return df


def interpolate_annual_state_series(df_survey: pd.DataFrame) -> pd.DataFrame:
    """
    Interpolate annual household income series (2018-2025) matching the tourism panel.
    - 2019, 2022, 2024: Official HIES survey values ('official')
    - 2018, 2020, 2021, 2023, 2025: CAGR geometric interpolation/projection ('e')
    """
    all_states = sorted(list(STATE_MAP.keys()))
    annual_records = []

    for st in all_states:
        meta = STATE_MAP[st]
        st_sub = df_survey[df_survey["state"] == st].set_index("year")

        def get_val(yr, col):
            if yr in st_sub.index and pd.notnull(st_sub.loc[yr, col]):
                return float(st_sub.loc[yr, col])
            return None

        # Determine CAGR rates for interpolation
        metrics = ["households_thousands", "median_income_rm", "mean_income_rm"]
        state_cagr = {}
        for m in metrics:
            v16 = get_val(2016, m)
            v19 = get_val(2019, m)
            v22 = get_val(2022, m)
            v24 = get_val(2024, m)

            cagr_16_19 = ((v19 / v16) ** (1 / 3) - 1) if (v16 and v19 and v16 > 0) else 0.03
            cagr_19_22 = ((v22 / v19) ** (1 / 3) - 1) if (v19 and v22 and v19 > 0) else 0.02
            cagr_22_24 = ((v24 / v22) ** (1 / 2) - 1) if (v22 and v24 and v22 > 0) else 0.03

            state_cagr[m] = {
                "16_19": cagr_16_19,
                "19_22": cagr_19_22,
                "22_24": cagr_22_24,
                "v19": v19,
                "v22": v22,
                "v24": v24,
            }

        for yr in range(2018, 2026):
            row_dict = {
                "year": yr,
                "state": st,
                "state_code": meta["code"],
                "region": meta["region"],
            }

            if yr in [2019, 2022, 2024]:
                row_dict["status"] = "official"
                for m in metrics:
                    row_dict[m] = get_val(yr, m)
            else:
                row_dict["status"] = "e"
                for m in metrics:
                    cinfo = state_cagr[m]
                    if yr == 2018:
                        row_dict[m] = cinfo["v19"] / (1 + cinfo["16_19"]) if cinfo["v19"] else None
                    elif yr == 2020:
                        row_dict[m] = cinfo["v19"] * (1 + cinfo["19_22"]) if cinfo["v19"] else None
                    elif yr == 2021:
                        row_dict[m] = cinfo["v19"] * ((1 + cinfo["19_22"]) ** 2) if cinfo["v19"] else None
                    elif yr == 2023:
                        row_dict[m] = cinfo["v22"] * (1 + cinfo["22_24"]) if cinfo["v22"] else None
                    elif yr == 2025:
                        row_dict[m] = cinfo["v24"] * (1 + cinfo["22_24"]) if cinfo["v24"] else None

            # Derived attributes
            if row_dict["households_thousands"]:
                row_dict["households_thousands"] = round(row_dict["households_thousands"], 3)
                row_dict["households_count"] = int(round(row_dict["households_thousands"] * 1000))
            else:
                row_dict["households_count"] = None

            if row_dict["median_income_rm"]:
                row_dict["median_income_rm"] = round(row_dict["median_income_rm"], 1)
            if row_dict["mean_income_rm"]:
                row_dict["mean_income_rm"] = round(row_dict["mean_income_rm"], 1)

            if row_dict["mean_income_rm"] and row_dict["median_income_rm"] and row_dict["median_income_rm"] > 0:
                row_dict["income_skewness_ratio"] = round(row_dict["mean_income_rm"] / row_dict["median_income_rm"], 3)
            else:
                row_dict["income_skewness_ratio"] = None

            annual_records.append(row_dict)

    df_annual = pd.DataFrame(annual_records).sort_values(["state", "year"]).reset_index(drop=True)
    return df_annual


def extract_national_benchmarks(wb) -> pd.DataFrame:
    """Extract National, Strata (Urban/Rural), and Ethnic breakdowns (1995-2024)."""
    col61, rows61 = get_year_columns(wb["6.1"])
    col62, rows62 = get_year_columns(wb["6.2"])
    col63, rows63 = get_year_columns(wb["6.3"])

    common_years = sorted(list(set(col61.keys()) & set(col62.keys()) & set(col63.keys())))

    # Category mappings: row index in Sheet 6.1/6.2/6.3
    categories = [
        (4, "National Total", "Malaysia"),
        (6, "Ethnic Group", "Bumiputera"),
        (7, "Ethnic Group", "Cina/ Chinese"),
        (8, "Ethnic Group", "India/ Indians"),
        (9, "Ethnic Group", "Lain-lain/ Others"),
        (11, "Strata", "Bandar/ Urban"),
        (12, "Strata", "Luar bandar/ Rural"),
    ]

    records = []
    for r_idx, ctype, cname in categories:
        for yr in common_years:
            hh_k = parse_numeric(rows61[r_idx][col61[yr]])
            med = parse_numeric(rows62[r_idx][col62[yr]])
            mean = parse_numeric(rows63[r_idx][col63[yr]])

            records.append({
                "year": yr,
                "category_type": ctype,
                "category_name": cname,
                "households_thousands": round(hh_k, 3) if hh_k is not None else None,
                "median_income_rm": round(med, 1) if med is not None else None,
                "mean_income_rm": round(mean, 1) if mean is not None else None,
                "income_skewness_ratio": round(mean / med, 3) if (mean and med and med > 0) else None,
                "data_status": "official_survey",
            })

    df = pd.DataFrame(records).sort_values(["category_type", "category_name", "year"]).reset_index(drop=True)
    return df


def extract_national_income_classes(wb) -> pd.DataFrame:
    """Extract B40 (D1-D4), M40 (D5-D8), and T20 (D9-D10) mean income and shares from Sheets 6.4 & 6.5."""
    col64, rows64 = get_year_columns(wb["6.4"], header_row=5)
    col65, rows65 = get_year_columns(wb["6.5"], header_row=5)

    common_years = sorted(list(set(col64.keys()) & set(col65.keys())))

    # Sections in 6.4 & 6.5
    sections = [
        ("B40 (D1-D4)", 5),   # Malaysia row 6 (index 5)
        ("M40 (D5-D8)", 17),  # Malaysia row 18 (index 17)
        ("T20 (D9-D10)", 29), # Malaysia row 30 (index 29)
    ]

    records = []
    for iclass, r_idx in sections:
        for yr in common_years:
            mean_inc = parse_numeric(rows64[r_idx][col64[yr]]) if yr in col64 else None
            inc_share = parse_numeric(rows65[r_idx][col65[yr]]) if yr in col65 else None

            records.append({
                "year": yr,
                "income_class": iclass,
                "group_name": "Malaysia",
                "mean_income_rm": round(mean_inc, 1) if mean_inc is not None else None,
                "income_share_pct": round(inc_share, 2) if inc_share is not None else None,
                "data_status": "official_survey",
            })

    df = pd.DataFrame(records).sort_values(["income_class", "year"]).reset_index(drop=True)
    return df


def run_pipeline():
    print("=" * 70)
    print("HIES Official Income & Household Time Series Ingestion")
    print("=" * 70)

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"File not found: {RAW_FILE}")

    print(f"Reading workbook: {RAW_FILE.name}")
    wb = openpyxl.load_workbook(RAW_FILE, read_only=True, data_only=True)

    # 1. State Survey Panel (1995-2024)
    df_state_survey = extract_state_survey_panel(wb)
    print(f"  [1/4] Extracted State Survey Panel: {len(df_state_survey)} records (16 states x {df_state_survey['year'].nunique()} survey years)")

    # 2. State Annual Interpolated Series (2018-2025)
    df_state_annual = interpolate_annual_state_series(df_state_survey)
    print(f"  [2/4] Generated State Annual Panel: {len(df_state_annual)} records (16 states x 8 years: 2018-2025)")

    # 3. National Strata & Ethnicity Benchmarks
    df_national = extract_national_benchmarks(wb)
    print(f"  [3/4] Extracted National Benchmarks: {len(df_national)} records")

    # 4. National Income Classes (B40, M40, T20)
    df_classes = extract_national_income_classes(wb)
    print(f"  [4/4] Extracted B40/M40/T20 Income Classes: {len(df_classes)} records")

    # Reconciliations and validation checks
    print("\nValidating Data Quality:")
    for yr in [2019, 2022, 2024]:
        nat_hh = df_national[(df_national["category_name"] == "Malaysia") & (df_national["year"] == yr)]["households_thousands"].values[0]
        st_sum = df_state_survey[df_state_survey["year"] == yr]["households_thousands"].sum()
        pct_diff = abs(st_sum - nat_hh) / nat_hh * 100
        print(f"  - Year {yr}: National = {nat_hh:.1f}k, Sum of 16 States = {st_sum:.1f}k, Diff = {abs(st_sum - nat_hh):.2f}k ({pct_diff:.4f}%)")
        assert pct_diff < 0.01, f"Household sum discrepancy > 0.01% in {yr}"

    # Export to CSV first
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_state_survey.to_csv(PROCESSED_DIR / "state_household_income_panel.csv", index=False)
    df_state_annual.to_csv(PROCESSED_DIR / "state_household_income_annual.csv", index=False)
    df_national.to_csv(PROCESSED_DIR / "national_household_income_panel.csv", index=False)
    df_classes.to_csv(PROCESSED_DIR / "national_income_class_panel.csv", index=False)

    # Ingest into DuckDB
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE state_household_income_panel AS SELECT * FROM df_state_survey")
    con.execute("CREATE OR REPLACE TABLE state_household_income_annual AS SELECT * FROM df_state_annual")
    con.execute("CREATE OR REPLACE TABLE national_household_income_panel AS SELECT * FROM df_national")
    con.execute("CREATE OR REPLACE TABLE national_income_class_panel AS SELECT * FROM df_classes")

    # Native Parquet export via DuckDB
    con.execute(f"COPY state_household_income_panel TO '{PROCESSED_DIR}/state_household_income_panel.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY state_household_income_annual TO '{PROCESSED_DIR}/state_household_income_annual.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY national_household_income_panel TO '{PROCESSED_DIR}/national_household_income_panel.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY national_income_class_panel TO '{PROCESSED_DIR}/national_income_class_panel.parquet' (FORMAT PARQUET)")

    # Update state_demographics with latest official 2024 HIES data
    df_demog_2024 = df_state_survey[df_state_survey["year"] == 2024].copy()
    con.execute("""
        CREATE OR REPLACE TABLE state_demographics AS
        SELECT 
            inc.year,
            inc.state,
            inc.state_code,
            inc.region,
            COALESCE(d.population_thousands, inc.households_thousands * 3.9) AS population_thousands,
            ROUND(COALESCE(d.population_thousands, inc.households_thousands * 3.9) / 1000.0, 4) AS population_millions,
            inc.households_thousands,
            inc.households_count,
            inc.median_income_rm,
            inc.mean_income_rm,
            inc.income_skewness_ratio,
            'official_survey_2024' AS data_status
        FROM df_demog_2024 inc
        LEFT JOIN (
            SELECT state, population_thousands FROM state_demographics
        ) d ON inc.state = d.state
    """)

    # Enrich state_panel_year with annual income and households
    con.execute("""
        CREATE OR REPLACE TABLE state_panel_year AS
        SELECT 
            p.*,
            h.households_thousands,
            h.households_count,
            h.median_income_rm AS median_household_income_rm,
            h.mean_income_rm AS mean_household_income_rm,
            h.income_skewness_ratio,
            h.status AS income_data_status
        FROM state_panel_year p
        LEFT JOIN state_household_income_annual h
            ON p.state = h.state AND p.year = h.year
    """)

    print("\nDuckDB Tables Updated:")
    for tname in [
        "state_household_income_panel",
        "state_household_income_annual",
        "national_household_income_panel",
        "national_income_class_panel",
        "state_demographics",
        "state_panel_year",
    ]:
        cnt = con.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
        print(f"  - {tname}: {cnt} rows")

    con.close()
    print("=" * 70)
    print("HIES Ingestion Completed Successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
