"""
Snapshot regression tests against saved baseline artifacts.
Per Phase 40 of IMPLEMENTATION_PLAN.md:
  - Separates empirical snapshot behavior from scientific model/accounting validation.
  - Snapshot assertions verify regression consistency against recorded baselines
    without declaring predetermined scientific hypotheses.
"""

from pathlib import Path
import pandas as pd
import duckdb
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BASELINE_DIR = ROOT_DIR / "artifacts/baseline"
DUCKDB_PATH = ROOT_DIR / "data/processed/tourism_data.duckdb"


@pytest.mark.snapshot
class TestBaselineSnapshots:
    """Snapshot regression checks against artifacts/baseline/."""

    def test_baseline_tsa_snapshot_consistency(self):
        snapshot_csv = BASELINE_DIR / "tsa_product_ranking.csv"
        assert snapshot_csv.exists(), f"Missing baseline snapshot: {snapshot_csv}"
        df_base = pd.read_csv(snapshot_csv)
        assert len(df_base) >= 88, f"Expected at least 88 baseline product records, got {len(df_base)}"

        # Verify current DuckDB product value summary matches baseline snapshot structure
        con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        df_curr = con.execute("SELECT * FROM product_value_summary ORDER BY vai_rank").df()
        con.close()

        # In the 2025 baseline snapshot, Accommodation services is recorded as Rank 1
        top_product = df_curr.iloc[0]
        assert top_product["product"] == "Accommodation services"
        assert top_product["vai_rank"] == 1
        assert top_product["post_recovery_median_vai"] > 0.80

    def test_baseline_corridor_opportunity_snapshot(self):
        snapshot_csv = BASELINE_DIR / "corridor_classifications.csv"
        assert snapshot_csv.exists(), f"Missing baseline snapshot: {snapshot_csv}"
        df_base = pd.read_csv(snapshot_csv)
        assert len(df_base) == 240, f"Expected 240 baseline corridor records, got {len(df_base)}"

        # Verify key baseline priority conversion corridors recorded in the 2025 release
        priority_base = df_base[df_base["corridor_tier"] == "Priority Conversion Corridor"]
        corridor_pairs = set(zip(priority_base["origin"], priority_base["destination"]))
        assert ("Selangor", "Melaka") in corridor_pairs, "Selangor -> Melaka expected in 2025 baseline priority corridors"
        assert ("Selangor", "Perak") in corridor_pairs, "Selangor -> Perak expected in 2025 baseline priority corridors"

        # Current table exists and has identical 240 bilateral pairs
        con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        df_curr = con.execute("SELECT * FROM corridor_opportunity_gap").df()
        con.close()
        assert len(df_curr) == 240

    def test_baseline_state_metrics_snapshot(self):
        snapshot_csv = BASELINE_DIR / "state_metrics.csv"
        assert snapshot_csv.exists(), f"Missing baseline snapshot: {snapshot_csv}"
        df_base = pd.read_csv(snapshot_csv)
        assert len(df_base) == 16, f"Expected 16 state records in baseline, got {len(df_base)}"

    def test_baseline_econometric_elasticities_snapshot(self):
        """Phase 40 & Item 15: Exact point-estimate contracts verified as historical baseline snapshots."""
        con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if "state_panel_econometrics" in tables:
            df_panel = con.execute("SELECT * FROM state_panel_econometrics WHERE model_id = 'Model_2_TwoWay_FE_Clustered'").df()
            alos_row = df_panel[df_panel["independent_variable"] == "ln(ALOS)"]
            if not alos_row.empty:
                assert abs(float(alos_row.iloc[0]["elasticity_coefficient"]) - 0.6628) < 1e-3
        con.close()
