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
        # Ensure no unsupported localized sub-state claims
        assert "Bandar Hilir" not in q1["limitation"], "Localized sub-state claim found in limitation"
        assert "Bandar Hilir" not in q1["answer"], "Localized sub-state claim found in answer"

        # Test High VAI product question
        q2 = query_grounded_assistant("Which tourism products have the highest Value-Added Intensity?")
        assert "Accommodation" in q2["answer"] or "VAI" in q2["answer"]
        assert "evidence" in q2

    def test_monte_carlo_missing_data_handling(self):
        """Sprint A: Monte Carlo returns UNAVAILABLE when baseline empirical data is missing."""
        from src.scenarios.monte_carlo import MonteCarloSimulator

        mc = MonteCarloSimulator()
        # Mock a destination with missing alos/spend
        mc.df_state.loc["MockState"] = pd.Series({"alos": np.nan, "spend_per_night": np.nan})
        # Add mock row in df_od
        mc.df_od = pd.concat([mc.df_od, pd.DataFrame([{
            "origin": "Selangor", "destination": "MockState", "tourist_flow_thousands": 100.0
        }])], ignore_index=True)

        res = mc.simulate_corridor_uncertainty("Selangor", "MockState")
        assert res["status"] == "UNAVAILABLE"
        assert "missing baseline empirical data" in res["error"]
        assert res["evidence_status"] == "insufficient_data"

    def test_portfolio_optimizer_eligibility_filtering(self):
        """Sprint A: Corridors with missing empirical data are marked ineligible."""
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        assert "eligible" in opt.df_candidates.columns
        assert "evidence_status" in opt.df_candidates.columns

        # Verify eligible candidates all have positive spend and room demand
        eligible = opt.df_candidates[opt.df_candidates["eligible"] == True]
        assert (eligible["expected_gva_rm_million"] > 0).all()
        assert (eligible["daily_rooms_demanded"] > 0).all()

    def test_no_zero_hallucination_or_pricing_power_claims(self):
        """Sprint A: Enforce elimination of 'zero hallucination' and 'pricing power'."""
        opt_py = (ROOT_DIR / "src/scenarios/portfolio_optimizer.py").read_text(encoding="utf-8")
        roadmap_tsx = (ROOT_DIR / "dashboard/src/components/ImplementationRoadmap.tsx").read_text(encoding="utf-8")
        econometrics_py = (ROOT_DIR / "src/analytics/panel_econometrics.py").read_text(encoding="utf-8")

        assert "zero hallucination" not in opt_py.lower()
        assert "zero-hallucination" not in opt_py.lower()
        assert "zero hallucination" not in roadmap_tsx.lower()
        assert "zero-hallucination" not in roadmap_tsx.lower()
        assert "pricing power" not in econometrics_py.lower()

    def test_grounded_assistant_truthful_metrics(self):
        """Sprint D: Verify all facts in Grounded Query Assistant match official 2025 data."""
        from src.scenarios.portfolio_optimizer import query_grounded_assistant

        # 1. Melaka capacity facts
        q_melaka = query_grounded_assistant("melaka capacity")
        assert q_melaka["metrics"]["alos_days"] == 2.11
        assert q_melaka["metrics"]["national_median_alos"] == 2.47
        assert q_melaka["metrics"]["spend_per_night_rm"] == 63.00

        # 2. VAI product ranking facts
        q_vai = query_grounded_assistant("highest value products")
        assert q_vai["metrics"]["accommodation_vai_pct"] == 85.8
        assert q_vai["metrics"]["food_beverage_vai_pct"] == 65.5
        assert q_vai["metrics"]["recreation_vai_pct"] == 60.4

        # 3. Pareto frontier size
        q_default = query_grounded_assistant("overview")
        assert q_default["metrics"]["pareto_optimal_corridors"] == 58
        assert q_default["metrics"]["national_median_alos"] == 2.47

        # 4. Header headline verification
        header_tsx = (ROOT_DIR / "dashboard/src/components/Header.tsx").read_text(encoding="utf-8")
        assert "From More Tourists to" in header_tsx
        assert "More Value" in header_tsx
        assert "Monitor · Diagnose · Target · Simulate · Optimize" in header_tsx

        # 5. Dynamic state resolution (Sprint E Plan Section 13.2)
        q_pahang = query_grounded_assistant("Pahang capacity and yield")
        assert q_pahang["metrics"]["state"] == "Pahang"
        assert q_pahang["metrics"]["alos_days"] == 2.21
        assert q_pahang["metrics"]["baseline_aor_pct"] == 76.3
        assert "Pahang" in q_pahang["answer"]

        q_penang = query_grounded_assistant("penang")
        assert q_penang["metrics"]["state"] == "Pulau Pinang"
        assert q_penang["metrics"]["alos_days"] == 2.65
        assert "Pulau Pinang" in q_penang["answer"]


class TestSprintCCommercialCredibility:
    """Validates Sprint C: Commercial Credibility, Illustrative Cost Assumptions, Custom Costs & Pilot Operating Model."""

    def test_custom_cost_overrides_in_portfolio_optimizer(self):
        """Verify custom_costs parameter overrides default illustrative candidate costs."""
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        test_corridor = "Selangor -> W.P. Kuala Lumpur"
        default_candidate = opt.df_candidates[opt.df_candidates["corridor_id"] == test_corridor].iloc[0]
        default_cost = default_candidate["cost_rm_million"]

        # Run with default costs
        res_default = opt.optimize_portfolio(budget_rm_million=5.0)

        # Override test corridor with custom cost (e.g. 5x higher)
        custom_cost = default_cost * 5.0
        res_custom = opt.optimize_portfolio(
            budget_rm_million=5.0,
            custom_costs={test_corridor: custom_cost}
        )

        assert res_custom["status"] in ["OPTIMAL", "FEASIBLE"]
        for c in res_custom["selected_corridors"]:
            if c["corridor_id"] == test_corridor:
                assert np.isclose(c["cost_rm_million"], custom_cost, atol=1e-4)
                assert c["cost_status"] in ["CUSTOM USER COST", "USER-SUPPLIED INTERVENTION COST"]
                assert c["cost_type"] == "user_supplied"

    def test_illustrative_cost_labeling_and_no_naked_roi(self):
        """Verify illustrative cost assumption labeling and absence of unsupported ROI wording."""
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        res = opt.optimize_portfolio(budget_rm_million=5.0)

        # Check summary contract
        assert "value_to_cost_multiple" in res["summary"]
        assert "cost_status" in res["summary"]
        assert "ILLUSTRATIVE" in res["summary"]["cost_status"]

        # Check candidate corridors have intervention_type and illustrative cost status
        for c in res["selected_corridors"]:
            assert "intervention_type" in c
            assert any(t in c["intervention_type"] for t in ["Stay-Extension", "Overnight Conversion", "Midweek Heritage"])
            assert "cost_status" in c
            assert c["cost_status"] in ["ILLUSTRATIVE COST ASSUMPTION", "CUSTOM USER COST", "USER-SUPPLIED INTERVENTION COST"]

    def test_melaka_pilot_operating_model_contract(self):
        """Verify Melaka 8-12 week pilot deployment protocol contract and official baselines."""
        from src.scenarios.portfolio_optimizer import get_implementation_metadata

        meta = get_implementation_metadata()
        assert "pilot_operating_model" in meta
        pilot = meta["pilot_operating_model"]

        assert pilot["destination"] == "Melaka"
        assert "baseline_quarter" in pilot
        assert pilot["baseline_quarter"]["destination_alos_days"] == 2.11
        assert pilot["baseline_quarter"]["spend_per_night_rm"] == 63.00
        assert pilot["baseline_quarter"]["baseline_aor_pct"] == 63.8
        assert pilot["baseline_quarter"]["available_hotel_rooms"] == 14782

        assert "intervention_design" in pilot
        assert len(pilot["intervention_design"]["target_corridors"]) >= 3
        assert "8–12 weeks" in pilot["intervention_design"]["duration_weeks"]

        assert "outcome_tracking" in pilot
        assert len(pilot["outcome_tracking"]) >= 4

        assert "evaluation_framework" in pilot
        assert "Difference-in-Differences" in pilot["evaluation_framework"]["methodology"]
        assert len(pilot["evaluation_framework"]["treatment_corridors"]) >= 2
        assert len(pilot["evaluation_framework"]["matched_control_corridors"]) >= 2

    def test_institutional_raci_governance_matrix(self):
        """Verify institutional roles and RACI governance matrix across 5 core functions."""
        from src.scenarios.portfolio_optimizer import get_implementation_metadata

        meta = get_implementation_metadata()
        assert "institutional_raci" in meta
        raci = meta["institutional_raci"]

        assert len(raci) == 5
        required_keys = {"function", "decision_owner", "data_owner", "implementation_owner", "review_cadence"}
        for item in raci:
            assert required_keys.issubset(item.keys())

        functions = [r["function"] for r in raci]
        assert "TSA National Supply & VAI Accounts" in functions
        assert "State Campaign Selection & Budget Sizing" in functions
        assert "Corridor Packaging & Hotel Booking Bundles" in functions
        assert "Carrying Capacity & Municipal Licensing" in functions
        assert "Econometric Recalibration & Optimization" in functions

    def test_implementation_model_doc_truthfulness(self):
        """Verify docs/implementation_model.md contains Sections 6 and 7."""
        doc_path = ROOT_DIR / "docs/implementation_model.md"
        assert doc_path.exists()
        doc_text = doc_path.read_text(encoding="utf-8")

        assert "## 6. Concrete Pilot Operating Model: Melaka 8–12 Week Protocol" in doc_text
        assert "## 7. Institutional Roles & RACI Governance Matrix" in doc_text
        assert "Difference-in-Differences" in doc_text
        assert "ILLUSTRATIVE COST ASSUMPTIONS" in doc_text


class TestSprintDUncertaintyAndOptimization:
    """Validates Sprint D: Empirical Monte Carlo Calibration, Uncertainty Provenance & Risk-Adjusted Optimization."""

    def test_monte_carlo_historical_calibration(self):
        """Verify Monte Carlo simulation derives variation parameters from historical panels."""
        from src.scenarios.monte_carlo import MonteCarloSimulator

        mc = MonteCarloSimulator()
        assert hasattr(mc, "state_historical_vars")
        assert len(mc.state_historical_vars) >= 14, "Historical state panel variables missing"
        
        # Check Melaka calibration
        melaka_var = mc.state_historical_vars.get("Melaka")
        assert melaka_var is not None
        assert 0.08 <= melaka_var["spend_cv"] <= 0.40
        assert melaka_var["sample_count"] >= 3

        # Check National TSA VAI standard deviation
        assert hasattr(mc, "national_vai_sd")
        assert 0.03 <= mc.national_vai_sd <= 0.15

    def test_monte_carlo_uncertainty_provenance_separation(self):
        """Verify Monte Carlo output strictly separates data uncertainty from policy assumptions."""
        from src.scenarios.monte_carlo import MonteCarloSimulator

        mc = MonteCarloSimulator()
        res = mc.simulate_corridor_uncertainty("Selangor", "Melaka", n_simulations=100)

        assert "uncertainty_provenance" in res
        prov = res["uncertainty_provenance"]
        assert "data_uncertainty" in prov
        assert "policy_uncertainty" in prov

        # Data uncertainty checks
        data_unc = prov["data_uncertainty"]
        assert data_unc["status"] == "data_calibrated"
        assert "spend_per_night_cv" in data_unc
        assert "vai_historical_sd" in data_unc
        assert "DOSM State Panel" in data_unc["calibration_source"]

        # Policy uncertainty checks
        policy_unc = prov["policy_uncertainty"]
        assert policy_unc["affected_share"]["status"] == "policy_assumption"
        assert policy_unc["delta_alos"]["status"] == "policy_target"
        assert policy_unc["guests_per_room"]["status"] == "scenario_assumption"

    def test_portfolio_optimizer_risk_adjusted_modes(self):
        """Verify PortfolioOptimizer supports expected, conservative_p10, and risk_adjusted objective modes."""
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()

        for mode in ["expected", "conservative_p10", "risk_adjusted"]:
            sol = opt.optimize_portfolio(budget_rm_million=5.0, planning_threshold=80.0, objective_mode=mode)
            assert sol["status"] in ["OPTIMAL", "FEASIBLE"]
            assert sol["summary"]["objective_mode"] == mode
            assert sol["summary"]["total_expected_gva_rm_million"] > 0
            assert sol["summary"]["total_p10_gva_rm_million"] > 0
            assert sol["summary"]["total_risk_adjusted_gva_rm_million"] > 0
            assert len(sol["selected_corridors"]) > 0

    def test_portfolio_corridor_uncertainty_monotonicity(self):
        """Verify that for all eligible candidate corridors: P10(GVA) <= RiskAdjusted(GVA) <= Expected(GVA)."""
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        eligible = opt.df_candidates[opt.df_candidates["eligible"] == True]
        assert len(eligible) > 50

        # Monotonicity checks
        p10_le_risk = eligible["p10_gva_rm_million"] <= (eligible["risk_adjusted_gva_rm_million"] + 1e-4)
        risk_le_exp = eligible["risk_adjusted_gva_rm_million"] <= (eligible["expected_gva_rm_million"] + 1e-4)

        assert p10_le_risk.all(), f"P10 > RiskAdjusted violations: {(~p10_le_risk).sum()}"
        assert risk_le_exp.all(), f"RiskAdjusted > Expected violations: {(~risk_le_exp).sum()}"


