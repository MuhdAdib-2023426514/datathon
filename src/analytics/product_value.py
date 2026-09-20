"""
Product Value Analytics & Strategic Classification (Stage A & B)
Implements Value-Added Intensity (VAI) calculations, period-split analyses,
accommodation validation, and 2x2 strategic quadrant classification.
Saves analytical outputs to Parquet and DuckDB.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
import numpy as np
import pandas as pd
from src.ingestion.tsa_parser import ingest_tsa_tables

from src.config.paths import PROCESSED_DATA_DIR, DUCKDB_PATH

PROCESSED_DIR = PROCESSED_DATA_DIR


def compute_period_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes summary metrics (mean, median, std, CV, trend) for each product
    across the three defined analytical periods:
    - Pre-COVID (2015-2019)
    - Disruption (2020-2022)
    - Post-Recovery (2023-2025)
    """
    summary_rows = []
    products = df["product"].unique()

    for prod in products:
        p_df = df[df["product"] == prod].sort_values("year")

        pre_df = p_df[p_df["year"].between(2015, 2019)]
        disrupt_df = p_df[p_df["year"].between(2020, 2022)]
        post_df = p_df[p_df["year"].between(2023, 2025)]

        # Post-recovery 2025 baseline
        row_2025 = p_df[p_df["year"] == 2025].iloc[0]

        # Overall 2015-2025 metrics
        overall_vai_mean = p_df["vai"].mean()
        overall_vai_std = p_df["vai"].std()
        overall_vai_cv = (overall_vai_std / overall_vai_mean) if overall_vai_mean > 0 else 0.0

        # Pre-COVID metrics
        pre_vai_median = pre_df["vai"].median()
        pre_vai_mean = pre_df["vai"].mean()

        # Post-recovery metrics
        post_vai_median = post_df["vai"].median()
        post_vai_mean = post_df["vai"].mean()
        post_vai_std = post_df["vai"].std()
        post_vai_cv = (post_vai_std / post_vai_mean) if post_vai_mean > 0 else 0.0

        # Trend (VAI change: 2025 vs 2019 pre-COVID baseline)
        vai_2019 = pre_df[pre_df["year"] == 2019]["vai"].values[0]
        vai_2025 = row_2025["vai"]
        delta_vai_structural = vai_2025 - vai_2019

        summary_rows.append({
            "product_id": row_2025["product_id"],
            "product": prod,
            "industry": row_2025["industry"],
            "itc_2025": row_2025["itc"],
            "domestic_supply_2025": row_2025["domestic_supply"],
            "gva_2025": row_2025["gva"],
            "tourism_ratio_2025": row_2025["tourism_ratio"],
            "vai_2025": vai_2025,
            "pre_covid_median_vai": round(pre_vai_median, 4),
            "disruption_median_vai": round(disrupt_df["vai"].median(), 4),
            "post_recovery_median_vai": round(post_vai_median, 4),
            "post_recovery_cv": round(post_vai_cv, 4),
            "delta_vai_vs_2019": round(delta_vai_structural, 4),
            "estimated_tourism_gva_2025": row_2025["estimated_tourism_gva"],
            "employment_2025_thousands": row_2025["employment_thousands"],
        })

    summary_df = pd.DataFrame(summary_rows)

    # Strategic Quadrant Classification based on post-recovery median VAI and 2025 ITC scale
    median_vai_benchmark = summary_df["post_recovery_median_vai"].median()
    median_itc_benchmark = summary_df["itc_2025"].median()

    def classify_quadrant(row):
        high_vai = row["post_recovery_median_vai"] >= median_vai_benchmark
        high_itc = row["itc_2025"] >= median_itc_benchmark

        if high_vai and high_itc:
            return "High-Value Core Activity"
        elif high_vai and not high_itc:
            return "Growth Opportunity (High Yield)"
        elif not high_vai and high_itc:
            return "Efficiency-Improvement Priority (High Leakage)"
        else:
            return "Lower Strategic Priority"

    summary_df["strategic_quadrant"] = summary_df.apply(classify_quadrant, axis=1)

    # Rank products by post-recovery VAI
    summary_df["vai_rank"] = summary_df["post_recovery_median_vai"].rank(ascending=False).astype(int)

    return summary_df.sort_values("vai_rank")


def export_to_duckdb(df_prod: pd.DataFrame, df_macro: pd.DataFrame, df_summary: pd.DataFrame):
    """
    Exports clean analytical tables to Parquet and registers them in DuckDB
    using DuckDB's native high-performance Parquet engine.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    prod_parquet = PROCESSED_DIR / "tourism_product_year.parquet"
    macro_parquet = PROCESSED_DIR / "tsa_macro_year.parquet"
    summary_parquet = PROCESSED_DIR / "product_value_summary.parquet"

    # Connect to DuckDB and register tables from DataFrames
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE tourism_product_year AS SELECT * FROM df_prod")
    con.execute("CREATE OR REPLACE TABLE tsa_macro_year AS SELECT * FROM df_macro")
    con.execute("CREATE OR REPLACE TABLE product_value_summary AS SELECT * FROM df_summary")

    # Export to Parquet using DuckDB native COPY
    con.execute(f"COPY tourism_product_year TO '{prod_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY tsa_macro_year TO '{macro_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY product_value_summary TO '{summary_parquet}' (FORMAT PARQUET)")
    con.close()

    print(f"Tables successfully registered in DuckDB: {DUCKDB_PATH}")
    print(f"Parquet files saved to: {PROCESSED_DIR}")


def run_stage_a_analysis() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Orchestrates Stage A analysis: Ingestion, Period Metrics, Quadrant Classification, and Export.
    """
    df_prod, df_macro = ingest_tsa_tables()
    df_summary = compute_period_metrics(df_prod)
    export_to_duckdb(df_prod, df_macro, df_summary)
    return df_prod, df_macro, df_summary


if __name__ == "__main__":
    df_prod, df_macro, df_summary = run_stage_a_analysis()
    print("\n" + "=" * 100)
    print("STAGE A: STRATEGIC PRODUCT VALUE MATRIX (Post-Recovery 2023-2025)")
    print("=" * 100)
    display_cols = [
        "vai_rank",
        "product",
        "post_recovery_median_vai",
        "post_recovery_cv",
        "itc_2025",
        "gva_2025",
        "strategic_quadrant"
    ]
    print(df_summary[display_cols].to_string(index=False))
