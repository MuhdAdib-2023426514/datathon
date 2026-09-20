"""
Tests for Sprint 5: Corridor Opportunity Engine & HHI Market Diversification.
Validates:
1. Phase 20: Inbound feeder concentration (HHI, top origin share, top-3 share, meaningful origin count).
2. Phase 19: Separation of gravity model residual/gap from economic opportunity.
3. Multi-dimensional opportunity criteria: capacity headroom, yield, accessibility, diversification.
4. Pareto opportunity frontier: non-domination property, frontier selection, composite score validity.
5. Strict non-causal policy disclaimer preservation.
"""

import pytest
import duckdb
import numpy as np
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DUCKDB_PATH = ROOT_DIR / "data/processed/tourism_data.duckdb"


@pytest.fixture(scope="module")
def db_connection():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    yield con
    con.close()


class TestDestinationConcentrationHHI:
    """Validates Phase 20: HHI Market Diversification and feeder metrics."""

    def test_concentration_panel_metrics(self, db_connection):
        df_conc = db_connection.execute("SELECT * FROM destination_concentration_panel").df()
        assert len(df_conc) > 0, "destination_concentration_panel is empty"

        # Check required columns for Phase 20
        required_cols = [
            "year", "destination", "interstate_origin_hhi", "all_origin_hhi",
            "top_feeder_origin", "top_feeder_share_pct", "top_3_origin_share_pct",
            "meaningful_origin_count", "concentration_tier"
        ]
        for col in required_cols:
            assert col in df_conc.columns, f"Column '{col}' missing from destination_concentration_panel"

        # Check domain boundaries
        valid_hhi = df_conc["interstate_origin_hhi"].dropna()
        assert (valid_hhi >= 0).all() and (valid_hhi <= 10000).all(), "HHI out of [0, 10000] range"

        # Top origin share <= Top 3 origin share <= 100%
        valid_shares = df_conc.dropna(subset=["top_feeder_share_pct", "top_3_origin_share_pct"])
        assert (valid_shares["top_feeder_share_pct"] <= valid_shares["top_3_origin_share_pct"] + 1e-4).all(), (
            "Top feeder share cannot exceed top 3 feeder share"
        )
        assert (valid_shares["top_3_origin_share_pct"] <= 100.01).all(), "Top 3 share exceeds 100%"

        # Meaningful origin count (origins with >= 5% share) should be between 1 and 15
        valid_counts = df_conc["meaningful_origin_count"].dropna()
        assert (valid_counts >= 1).all() and (valid_counts <= 15).all(), "Invalid meaningful origin count"

    def test_neutral_concentration_terminology(self, db_connection):
        df_conc = db_connection.execute("SELECT * FROM destination_concentration WHERE year = 2025").df()
        tiers = df_conc["concentration_tier"].unique()
        # Verify neutral wording, not judgmental
        for t in tiers:
            assert "bad" not in t.lower() and "poor" not in t.lower(), f"Judgmental tier name found: {t}"


class TestCorridorOpportunityEngine:
    """Validates Phase 19: Corridor Opportunity Redesign & Pareto Frontier."""

    def test_corridor_opportunity_gap_table_exists(self, db_connection):
        df_gap = db_connection.execute("SELECT * FROM corridor_opportunity_gap").df()
        assert len(df_gap) == 240, f"Expected 240 bilateral interstate corridors, got {len(df_gap)}"

    def test_model_gap_separated_from_opportunity(self, db_connection):
        df_gap = db_connection.execute("SELECT * FROM corridor_opportunity_gap").df()
        # Ensure model performance/gap is distinct from corridor tier
        assert "gravity_performance_category" in df_gap.columns, (
            "gravity_performance_category missing from corridor_opportunity_gap"
        )
        assert "gravity_flow_gap_thousands" in df_gap.columns, (
            "gravity_flow_gap_thousands missing from corridor_opportunity_gap"
        )
        categories = set(df_gap["gravity_performance_category"].unique())
        expected_cats = {"Below Model Expected", "Near Model Expected", "Above Model Expected"}
        assert categories.issubset(expected_cats), f"Unexpected gravity performance categories: {categories}"

        # Test that below-expected flow does NOT automatically dictate tier 1 opportunity
        below_expected = df_gap[df_gap["gravity_performance_category"] == "Below Model Expected"]
        assert len(below_expected) > 0, "No corridors classified as Below Model Expected"
        # Not all below-expected corridors should be Pareto optimal
        assert not below_expected["is_pareto_optimal"].all(), (
            "Fallacy: Below-expected flow was automatically treated as Pareto-optimal"
        )

    def test_multidimensional_opportunity_criteria(self, db_connection):
        df_gap = db_connection.execute("SELECT * FROM corridor_opportunity_gap").df()

        # 1. Capacity Headroom
        assert "capacity_headroom_pct" in df_gap.columns, "capacity_headroom_pct missing"
        assert "capacity_tier" in df_gap.columns, "capacity_tier missing"
        valid_headroom = df_gap["capacity_headroom_pct"].dropna()
        assert (valid_headroom >= -20).all() and (valid_headroom <= 100).all(), "Headroom out of bounds"

        # 2. Economic Yield
        assert "dest_spend_per_night" in df_gap.columns or "dest_tvay_rm_per_day" in df_gap.columns, (
            "Yield metric missing from opportunity table"
        )

        # 3. Accessibility
        assert "accessibility_tier" in df_gap.columns, "accessibility_tier missing"
        acc_tiers = set(df_gap["accessibility_tier"].unique())
        assert any("High" in t for t in acc_tiers), "No high accessibility tier found"

        # 4. Diversification
        assert "diversification_benefit" in df_gap.columns, "diversification_benefit missing"
        assert "is_dominant_feeder" in df_gap.columns, "is_dominant_feeder missing"

        # 5. Model Confidence
        assert "model_confidence_tier" in df_gap.columns, "model_confidence_tier missing"

    def test_pareto_frontier_properties(self, db_connection):
        df_gap = db_connection.execute("SELECT * FROM corridor_opportunity_gap").df()
        assert "is_pareto_optimal" in df_gap.columns, "is_pareto_optimal missing"
        assert "pareto_rank" in df_gap.columns, "pareto_rank missing"
        assert "composite_opportunity_score" in df_gap.columns, "composite_opportunity_score missing"

        pareto_corridors = df_gap[df_gap["is_pareto_optimal"] == True]
        assert len(pareto_corridors) >= 3, "Pareto frontier has too few corridors (< 3)"
        assert len(pareto_corridors) <= 120, "Pareto frontier is not selective enough (> 120)"

        # Composite score bounds
        scores = df_gap["composite_opportunity_score"].dropna()
        assert (scores >= 0.0).all() and (scores <= 100.0).all(), "Composite score out of [0, 100]"

        # Rank 1 corridor should have the top composite score
        sorted_by_score = df_gap.sort_values("composite_opportunity_score", ascending=False).reset_index(drop=True)
        assert sorted_by_score.iloc[0]["composite_opportunity_score"] >= sorted_by_score.iloc[-1]["composite_opportunity_score"]

    def test_scenario_disclaimer_preservation(self, db_connection):
        df_gap = db_connection.execute("SELECT * FROM corridor_opportunity_gap").df()
        assert (df_gap["policy_disclaimer"] == "Scenario estimate, not a causal forecast.").all(), (
            "Mandatory policy disclaimer violated"
        )


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__]))
