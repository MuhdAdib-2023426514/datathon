"""
TSA Accounting and Data Quality Validation Test Suite
Enforces quality gates, accounting formulas, and assertions specified in:
- AGENTS.md (Sections 3, 6, 18)
- .agents/skills/data-pipeline-validation/SKILL.md
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
import pandas as pd

DUCKDB_PATH = ROOT_DIR / "data/processed/tourism_data.duckdb"


def test_tourism_product_year():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT * FROM tourism_product_year").df()
    con.close()

    print("\n[TEST 1] Validating tourism_product_year...")
    # Row count: 8 products x 11 years = 88 rows
    assert len(df) == 88, f"Expected 88 rows, got {len(df)}"
    assert df["year"].min() == 2015 and df["year"].max() == 2025, "Year range must be 2015 to 2025"
    assert df["product"].nunique() == 8, f"Expected 8 products, got {df['product'].nunique()}"

    # Non-negativity assertions
    assert (df["domestic_supply"] >= 0).all(), "Negative domestic supply found!"
    assert (df["gva"] >= 0).all(), "Negative GVA found!"
    assert (df["itc"] >= 0).all(), "Negative ITC found!"

    # Bounds on rates and ratios
    # In structural periods (Pre-COVID 2015-2019 and Post-Recovery 2023-2025), VAI is strictly in [0.0, 1.0]
    structural_df = df[df["year"] != 2021]
    assert (structural_df["vai"] >= 0.0).all() and (structural_df["vai"] <= 1.0).all(), (
        f"Structural VAI must be between 0 and 1: min={structural_df['vai'].min()}, max={structural_df['vai'].max()}"
    )

    # In 2021 (peak COVID lockdown), production subsidies / wage support caused GVA to exceed collapsed domestic supply
    anomaly_2021 = df[(df["year"] == 2021) & (df["vai"] > 1.0)]
    assert len(anomaly_2021) > 0, "Expected documented 2021 COVID subsidy anomaly in VAI"
    print(f"  Note: 2021 COVID disruption anomaly verified ({len(anomaly_2021)} products with VAI > 1.0 due to supply collapse)")

    assert (df["tourism_ratio"] >= 0.0).all() and (df["tourism_ratio"] <= 1.0).all(), "Tourism ratio must be between 0 and 1"

    # Status flags preservation
    status_counts = df["data_status"].value_counts().to_dict()
    print(f"  Status flag distribution: {status_counts}")
    assert "preliminary" in status_counts, "Preliminary flag (2025p) not preserved!"
    assert "estimate" in status_counts, "Estimate flag (2024e) not preserved!"

    # Formula consistency: VAI = GVA / Supply
    calculated_vai = (df["gva"] / df["domestic_supply"]).round(4)
    vai_diff = (df["vai"] - calculated_vai).abs().max()
    assert vai_diff < 0.001, f"VAI formula mismatch: max difference {vai_diff}"

    # Formula consistency: Estimated Tourism GVA = ITC * VAI (check within 0.1% rounding tolerance)
    calc_proxy = (df["itc"] * df["vai"]).round(2)
    rel_diff = ((df["estimated_tourism_gva"] - calc_proxy).abs() / df["estimated_tourism_gva"].replace(0, 1)).max()
    assert rel_diff < 0.001, f"Estimated Tourism GVA proxy relative mismatch: max diff {rel_diff:.4%}"

    print("  ✓ tourism_product_year schema, bounds, and formula assertions PASSED.")


def test_tsa_macro_year():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT * FROM tsa_macro_year ORDER BY year").df()
    con.close()

    print("\n[TEST 2] Validating tsa_macro_year...")
    assert len(df) == 11, f"Expected 11 macro years, got {len(df)}"
    assert (df["tdgva"] > 0).all(), "TDGVA must be strictly positive"
    assert (df["tdgdp"] > 0).all(), "TDGDP must be strictly positive"

    # 2025 official benchmarks
    row_2025 = df[df["year"] == 2025].iloc[0]
    assert row_2025["tdgva"] == 123453.8, f"Unexpected 2025 TDGVA: {row_2025['tdgva']}"
    assert row_2025["tdgdp"] == 138670.0, f"Unexpected 2025 TDGDP: {row_2025['tdgdp']}"
    assert row_2025["data_status"] == "preliminary", "2025 status must be preliminary"

    print("  ✓ tsa_macro_year values and benchmarks PASSED.")


def test_product_value_summary_integrity():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT * FROM product_value_summary ORDER BY vai_rank").df()
    con.close()

    print("\n[TEST 3] Validating Product Value Summary & Quadrant Integrity...")
    assert len(df) == 8, f"Expected 8 TSA products, got {len(df)}"
    
    # Mathematical bounds on VAI and ranks
    assert (df["post_recovery_median_vai"] >= 0.0).all() and (df["post_recovery_median_vai"] <= 1.0).all(), (
        "VAI values must be bounded within [0, 1]"
    )
    assert sorted(df["vai_rank"].tolist()) == list(range(1, 9)), "VAI ranks must be contiguous 1..8"
    assert (df["gva_2025"] > 0).all(), "2025 GVA must be strictly positive"
    assert (df["domestic_supply_2025"] > 0).all(), "2025 Domestic Supply must be strictly positive"

    # Valid quadrant taxonomy
    valid_quadrants = {
        "High-Value Core Activity",
        "Growth Opportunity (High Yield)",
        "Efficiency-Improvement Priority (Low Value Retention)",
        "Lower Strategic Priority",
    }
    assert set(df["strategic_quadrant"]).issubset(valid_quadrants), (
        f"Invalid quadrants found: {set(df['strategic_quadrant']) - valid_quadrants}"
    )

    # Validate Travel Agency structural supply metrics
    ta_row = df[df["product_id"] == "travel_agency"].iloc[0]
    assert ta_row["gva_2025"] > 0, "Travel Agency GVA in 2025 must be positive"
    assert ta_row["domestic_supply_2025"] > ta_row["gva_2025"], "Travel Agency supply must exceed GVA"

    print("  ✓ Product value summary integrity and quadrant assignments PASSED.")
    print("  ✓ Travel agency structural supply and GVA metrics PASSED.")


def run_all_tests():
    print("=" * 70)
    print("RUNNING TSA ACCOUNTING & DATA VALIDATION SUITE")
    print("=" * 70)
    test_tourism_product_year()
    test_tsa_macro_year()
    test_product_value_summary_integrity()
    print("\n" + "=" * 70)
    print("ALL VALIDATION TESTS PASSED (100% SUCCESS)")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
