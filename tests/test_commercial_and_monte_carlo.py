"""
Tests for Sprint 8: Commercial & Wow Factor
Covers:
  1. Phase 26: Monte Carlo Uncertainty Simulation
  2. Phase 36: Tourism Investment Portfolio Optimizer (MILP)
  3. Phase 37: Longitudinal OD Time Animation Data Integrity (2018-2025)
  4. Phase 35 & 38: Commercial Implementation & Grounded Query Contracts
"""

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DATA_DIR = ROOT_DIR / "dashboard/public/data"


class TestMonteCarloUncertainty:
    """Validates Monte Carlo stochastic uncertainty simulation."""

    def test_corridor_monte_carlo_properties(self):
        from src.scenarios.monte_carlo import MonteCarloSimulator

        mc = MonteCarloSimulator()
        res = mc.simulate_corridor_uncertainty(
            origin="Selangor",
            destination="Melaka",
            delta_alos=0.5,
            affected_share=0.15,
            n_simulations=1000,
            seed=42,
        )

        assert "percentiles" in res
        assert "mean" in res
        assert "std" in res
        assert "prob_capacity_breach" in res
        assert "distribution" in res

        # Quantile ordering: P10 <= P50 <= P90
        p = res["percentiles"]
        assert p["additional_nights"]["p10"] <= p["additional_nights"]["p50"] <= p["additional_nights"]["p90"]
        assert p["additional_spend_rm_m"]["p10"] <= p["additional_spend_rm_m"]["p50"] <= p["additional_spend_rm_m"]["p90"]
        assert p["potential_gva_rm_m"]["p10"] <= p["potential_gva_rm_m"]["p50"] <= p["potential_gva_rm_m"]["p90"]

        # Meaningful non-zero variation
        assert res["std"]["potential_gva_rm_m"] > 0.01

        # Probability of breach in [0, 1]
        assert 0.0 <= res["prob_capacity_breach"] <= 1.0

        # Disclaimer presence
        assert "disclaimer" in res
        assert "Scenario estimate" in res["disclaimer"]

    def test_reproducibility_with_seed(self):
        from src.scenarios.monte_carlo import MonteCarloSimulator

        mc = MonteCarloSimulator()
        res1 = mc.simulate_corridor_uncertainty("Johor", "Pahang", n_simulations=500, seed=123)
        res2 = mc.simulate_corridor_uncertainty("Johor", "Pahang", n_simulations=500, seed=123)

        assert res1["percentiles"]["potential_gva_rm_m"]["p50"] == res2["percentiles"]["potential_gva_rm_m"]["p50"]
        assert res1["prob_capacity_breach"] == res2["prob_capacity_breach"]


class TestPortfolioOptimizer:
    """Validates Mixed-Integer Linear Programming (MILP) portfolio optimization."""

    def test_milp_budget_and_capacity_constraints(self):
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        budget_rm_m = 5.0
        planning_threshold = 80.0

        res = opt.optimize_portfolio(
            budget_rm_million=budget_rm_m,
            planning_threshold=planning_threshold,
            max_corridors_per_dest=4,
        )

        assert res["status"] in ["OPTIMAL", "FEASIBLE"]
        assert "selected_corridors" in res
        assert len(res["selected_corridors"]) > 0

        # 1. Budget constraint check
        assert res["summary"]["total_cost_rm_million"] <= budget_rm_m + 1e-5

        # 2. Capacity constraint check across all destinations
        dest_impacts = res["destination_impacts"]
        for dest, imp in dest_impacts.items():
            if imp["implied_aor_pct"] is not None:
                assert imp["implied_aor_pct"] <= planning_threshold + 1e-4

        # 3. Positive expected GVA
        assert res["summary"]["total_expected_gva_rm_million"] > 0.0

        # 4. Positive ROI (GVA / Cost)
        assert res["summary"]["portfolio_roi_multiplier"] > 1.0

    def test_budget_monotonicity(self):
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        res_small = opt.optimize_portfolio(budget_rm_million=2.0)
        res_large = opt.optimize_portfolio(budget_rm_million=10.0)

        # Higher budget allows equal or higher expected GVA
        assert res_large["summary"]["total_expected_gva_rm_million"] >= res_small["summary"]["total_expected_gva_rm_million"] - 1e-5


class TestLongitudinalODAnimation:
    """Validates longitudinal OD data for animation (2018-2025)."""

    def test_all_years_present_in_export(self):
        od_file = DASHBOARD_DATA_DIR / "od_corridors.json"
        assert od_file.exists(), f"Missing {od_file}"

        with open(od_file, "r") as f:
            data = json.load(f)

        assert "corridors_by_year" in data
        years = set(data["corridors_by_year"].keys())
        expected_years = {"2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"}
        assert expected_years.issubset(years), f"Missing years. Found: {years}"

        # Check COVID disruption: 2020 volume should be significantly lower than 2019
        vol_2019 = sum(c["tourist_flow_thousands"] for c in data["corridors_by_year"]["2019"])
        vol_2020 = sum(c["tourist_flow_thousands"] for c in data["corridors_by_year"]["2020"])
        vol_2025 = sum(c["tourist_flow_thousands"] for c in data["corridors_by_year"]["2025"])

        assert vol_2019 > 0
        assert vol_2020 < vol_2019 * 0.6  # Severe COVID contraction (>40% drop)
        assert vol_2025 > vol_2020 * 1.5  # Strong post-COVID recovery


class TestCommercialImplementationContract:
    """Validates commercial framework and grounded query assistant knowledge base."""

    def test_user_personas_and_governance(self):
        from src.scenarios.portfolio_optimizer import get_implementation_metadata

        meta = get_implementation_metadata()
        assert "target_users" in meta
        assert "operating_model" in meta
        assert "refresh_cadence" in meta

        # Key official stakeholders
        user_roles = [u["role"] for u in meta["target_users"]]
        assert "MOTAC" in user_roles
        assert "Tourism Malaysia" in user_roles
        assert "State Tourism Boards" in user_roles
        assert "Local Authorities" in user_roles

        # 8-step operating cycle
        assert len(meta["operating_model"]) >= 7

    def test_grounded_ai_assistant_rules(self):
        from src.scenarios.portfolio_optimizer import query_grounded_assistant

        # Test Melaka capacity question
        q1 = query_grounded_assistant("Why is Melaka classified as capacity constrained?")
        assert "Melaka" in q1["answer"]
        assert "evidence" in q1
        assert "source" in q1
        assert q1["confidence"] in ["High", "Very High"]

        # Test High VAI product question
        q2 = query_grounded_assistant("Which tourism products have the highest Value-Added Intensity?")
        assert "Accommodation" in q2["answer"] or "VAI" in q2["answer"]
        assert "evidence" in q2
