"""
State Demographics & Household Income Ingestion Parser
Loads state population and median/mean household income from data/raw/
Standardizes state names to official 16 states and Federal Territories.
Exports to DuckDB table `state_demographics` and Parquet.
"""

import glob
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import duckdb
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

RAW_DIR = ROOT_DIR / "data/raw"
PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

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


def match_state_from_name(raw_str: str) -> Optional[str]:
    cleaned = str(raw_str).strip().upper().replace("_", " ").replace(".", "")
    if "PULAU PINANG" in cleaned or "PENANG" in cleaned or "P PINANG" in cleaned:
        return "PULAU PINANG"
    if "KUALA LUMPUR" in cleaned or "KL" in cleaned:
        return "W.P. KUALA LUMPUR"
    if "PUTRAJAYA" in cleaned:
        return "W.P. PUTRAJAYA"
    if "LABUAN" in cleaned:
        return "W.P. LABUAN"
    if "NEGERI SEMBILAN" in cleaned or "N SEMBILAN" in cleaned:
        return "NEGERI SEMBILAN"
    for k in STATE_METADATA:
        if k.replace(".", "") in cleaned:
            return k
    return None


def find_demographics_file() -> Optional[Path]:
    """Find user uploaded demographics file or fallback to template."""
    candidates = []
    for ext in ["*.csv", "*.xlsx", "*.xls"]:
        candidates.extend(list(RAW_DIR.glob(ext)))
    
    # Priority: user file with 'pop' or 'income' or 'demograph'
    for c in candidates:
        name = c.name.lower()
        if "template" not in name and any(k in name for k in ["pop", "income", "demograph", "penduduk", "pendapatan", "hies"]):
            return c
            
    # Priority 2: state_demographics.csv
    exact = RAW_DIR / "state_demographics.csv"
    if exact.exists():
        return exact

    # Priority 3: template
    tmpl = RAW_DIR / "state_demographics_template.csv"
    if tmpl.exists():
        return tmpl

    return None


def run_pipeline():
    print("=" * 70)
    print("Ingesting State Demographics & Household Income Data")
    print("=" * 70)

    fpath = find_demographics_file()
    if not fpath:
        print("  [Warning] No demographics file found in data/raw/")
        return

    print(f"Reading demographics from: {fpath.name}")
    if fpath.suffix == ".csv":
        df_raw = pd.read_csv(fpath)
    else:
        df_raw = pd.read_excel(fpath)

    # Clean columns
    col_map = {}
    for c in df_raw.columns:
        cl = str(c).lower().strip()
        if "state" in cl or "negeri" in cl:
            col_map[c] = "raw_state"
        elif "year" in cl or "tahun" in cl:
            col_map[c] = "year"
        elif "pop" in cl or "penduduk" in cl:
            col_map[c] = "population"
        elif "median" in cl or "penengah" in cl:
            col_map[c] = "median_income"
        elif "mean" in cl or "purata" in cl:
            col_map[c] = "mean_income"

    df_clean = df_raw.rename(columns=col_map)
    records = []

    for _, row in df_clean.iterrows():
        raw_st = row.get("raw_state")
        m_key = match_state_from_name(raw_st)
        if m_key:
            meta = STATE_METADATA[m_key]
            
            # Pop normalization (standardize to thousands)
            raw_pop = float(row.get("population", 1000.0))
            pop_k = raw_pop if raw_pop < 50000 else raw_pop / 1000.0
            
            med_inc = float(row.get("median_income", 5000.0))
            mean_inc = float(row.get("mean_income", med_inc * 1.25))
            yr = int(row.get("year", 2024))

            records.append({
                "year": yr,
                "state": meta["name"],
                "state_code": meta["code"],
                "region": meta["region"],
                "population_thousands": round(pop_k, 2),
                "population_millions": round(pop_k / 1000.0, 4),
                "median_household_income_rm": round(med_inc, 0),
                "mean_household_income_rm": round(mean_inc, 0),
            })

    df_final = pd.DataFrame(records).drop_duplicates(subset=["state", "year"])
    print(f"Extracted {len(df_final)} demographic records across {df_final['state'].nunique()} states.")

    # Export to processed and DuckDB
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(PROCESSED_DIR / "state_demographics.csv", index=False)

    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE state_demographics AS SELECT * FROM df_final")
    con.execute(f"COPY state_demographics TO '{PROCESSED_DIR}/state_demographics.parquet' (FORMAT PARQUET)")
    n = con.execute("SELECT COUNT(*) FROM state_demographics").fetchone()[0]
    print(f"DuckDB table `state_demographics` updated: {n} rows.")
    con.close()
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
