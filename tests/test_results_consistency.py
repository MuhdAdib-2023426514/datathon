"""
Automated Results Consistency & Contract Parity Test Suite.
Per Plan Sections 20, 22, 23, 31, and 32 (Sprint F / Sprint 18):
1. Verifies artifacts/current_results.json authoritative contract structure.
2. Asserts zero analytical drift between README.md and current_results.json.
3. Asserts zero analytical drift between dashboard JSON exports and current_results.json.
4. Asserts zero analytical drift between artifacts/model_metrics.json and current_results.json.
5. Verifies clean architectural separation between snapshot regression checks and scientific tests.
"""

import json
import re
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
CURRENT_RESULTS_PATH = ARTIFACTS_DIR / "current_results.json"
MODEL_METRICS_PATH = ARTIFACTS_DIR / "model_metrics.json"
README_PATH = ROOT_DIR / "README.md"
DASHBOARD_DATA_DIR = ROOT_DIR / "dashboard/public/data"


@pytest.fixture(scope="module")
def current_results():
    assert CURRENT_RESULTS_PATH.exists(), f"Missing current_results.json: {CURRENT_RESULTS_PATH}"
    with open(CURRENT_RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TestCurrentResultsContract:
    """Verifies the schema and completeness of artifacts/current_results.json."""

    def test_current_results_schema(self, current_results):
        assert current_results.get("contract_version") == "1.0.0"
        assert current_results.get("reference_year") == 2025

        # Check required domains
        for domain in ["panel", "gravity", "tsa", "corridors", "scenarios"]:
            assert domain in current_results, f"Domain '{domain}' missing from current_results.json"

        # Check panel domain
        panel = current_results["panel"]
        assert panel["observations"] == 126
        assert panel["states"] == 16
        assert panel["years"] == 8
        assert abs(panel["alos_elasticity"] - 0.6628) < 1e-4
        assert abs(panel["alos_p_value"] - 0.0952) < 1e-4
        assert abs(panel["tourist_elasticity"] - 0.7327) < 1e-4
        assert panel["leave_one_out_stability"] == "16/16"
        assert abs(panel["yield_model"]["r_squared"] - 0.8018) < 1e-4

        # Check gravity domain
        gravity = current_results["gravity"]
        assert gravity["primary_model"] == "PPML"
        assert gravity["total_panel_observations"] == 1920
        assert gravity["train_observations"] == 1680
        assert gravity["test_observations"] == 240
        assert abs(gravity["ppml_oos_r2"] - 0.5890) < 1e-3
        assert abs(gravity["distance_decay_friction"] - (-0.4104)) < 1e-4
        assert abs(gravity["cross_region_barrier"] - (-0.8022)) < 1e-4
        assert abs(gravity["structural_invariance_p_value"] - 0.1198) < 1e-4

        # Check naive baselines
        baselines = gravity["naive_baselines"]
        assert abs(baselines["lag_2024_oos_r2"] - 0.7637) < 1e-3
        assert abs(baselines["historical_mean_oos_r2"] - 0.6732) < 1e-3
        assert abs(baselines["log_ols_oos_r2"] - 0.2936) < 1e-3

        # Check TSA domain
        tsa = current_results["tsa"]
        assert tsa["top_product"] == "Accommodation services"
        assert abs(tsa["accommodation_post_recovery_median_vai"] - 0.8579) < 1e-4
        assert tsa["accommodation_vai_rank"] == 1
        assert tsa["total_product_records"] == 88

        # Check Corridors domain
        corridors = current_results["corridors"]
        assert corridors["total_directional_corridors"] == 240
        assert corridors["total_bilateral_pairs_with_intrastate"] == 256
        assert corridors["pareto_optimal_corridors_count"] == 58
        assert corridors["top_ranked_corridor"]["origin"] == "Selangor"
        assert corridors["top_ranked_corridor"]["destination"] == "W.P. Kuala Lumpur"
        assert corridors["top_ranked_corridor"]["pareto_rank"] == 1
        assert corridors["top_ranked_corridor"]["opportunity_rank"] == 1

        # Check Scenarios domain
        scenarios = current_results["scenarios"]
        assert scenarios["policy_disclaimer"] == "Scenario estimate, not a causal forecast."
        assert scenarios["default_planning_threshold_pct"] == 80.0


class TestReadmeConsistency:
    """Verifies that README.md reports exact values matching the current_results contract."""

    def test_readme_matches_current_results(self, current_results):
        assert README_PATH.exists(), f"README.md not found at {README_PATH}"
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme_text = f.read()

        # 1. Panel ALOS elasticity (0.6628) and Tourist elasticity (0.7327)
        assert "0.6628" in readme_text, "README.md missing ALOS elasticity 0.6628"
        assert "0.7327" in readme_text, "README.md missing Tourist elasticity 0.7327"
        assert "0.0952" in readme_text, "README.md missing ALOS p-value 0.0952"

        # 2. Panel sample observations (126, 2018–2025)
        assert "126" in readme_text, "README.md missing panel N=126"
        assert "2018–2025" in readme_text or "2018-2025" in readme_text

        # 3. Leave-one-out stability (16/16)
        assert "16/16" in readme_text, "README.md missing 16/16 leave-one-out sign stability"

        # 4. Lodging yield model R-squared (0.8018)
        assert "0.8018" in readme_text, "README.md missing Yield model R^2 0.8018"

        # 5. Gravity observation counts (1,920 and 2,048)
        assert "1,920" in readme_text or "1920" in readme_text, "README.md missing 1,920 corridor-years"
        assert "2,048" in readme_text or "2048" in readme_text, "README.md missing 2,048 bilateral observations"

        # 6. Gravity parameters (distance decay -0.4104, cross-region barrier -0.8022)
        assert "-0.4104" in readme_text, "README.md missing distance decay -0.4104"
        assert "-0.8022" in readme_text, "README.md missing cross-region barrier -0.8022"
        assert "0.1198" in readme_text, "README.md missing structural invariance p-value 0.1198"

        # 7. Gravity OOS R-squared (0.5890) and baselines (0.7637, 0.6732, 0.2936)
        assert "0.5890" in readme_text or "0.589" in readme_text, "README.md missing PPML OOS R^2 0.5890"
        assert "0.7637" in readme_text, "README.md missing 2024 lag baseline R^2 0.7637"
        assert "0.6732" in readme_text, "README.md missing historical mean baseline R^2 0.6732"
        assert "0.2936" in readme_text, "README.md missing Log-OLS baseline R^2 0.2936"

        # 8. Pareto optimal corridor count (58)
        assert "58" in readme_text, "README.md missing 58 Pareto corridors"

        # 9. Accommodation VAI (0.8579 / 85.79)
        assert "0.8579" in readme_text or "85.79" in readme_text, "README.md missing Accommodation VAI 0.8579"


class TestDashboardExportsConsistency:
    """Verifies that exported dashboard JSON files match the current_results contract."""

    def test_dashboard_current_results_parity(self, current_results):
        dash_curr = DASHBOARD_DATA_DIR / "current_results.json"
        assert dash_curr.exists(), f"Missing dashboard current_results.json: {dash_curr}"
        with open(dash_curr, "r", encoding="utf-8") as f:
            dash_data = json.load(f)
        assert dash_data == current_results, "Dashboard current_results.json diverged from artifacts/current_results.json"

    def test_drivers_rq3_json_matches_contract(self, current_results):
        drivers_file = DASHBOARD_DATA_DIR / "drivers_rq3.json"
        assert drivers_file.exists(), f"Missing drivers_rq3.json: {drivers_file}"
        with open(drivers_file, "r", encoding="utf-8") as f:
            drivers_data = json.load(f)

        # Verify Two-Way FE Model exists in panel_regressions
        regs = drivers_data.get("panel_regressions", [])
        m2_alos = next((r for r in regs if r.get("model_id") == "Model_2_TwoWay_FE_Clustered" and r.get("independent_variable") == "ln(ALOS)"), None)
        assert m2_alos is not None, "Model_2_TwoWay_FE_Clustered ln(ALOS) missing from drivers_rq3.json"
        assert abs(m2_alos["elasticity_coefficient"] - current_results["panel"]["alos_elasticity"]) < 1e-4

        m2_tourists = next((r for r in regs if r.get("model_id") == "Model_2_TwoWay_FE_Clustered" and r.get("independent_variable") == "ln(Overnight Tourists)"), None)
        assert m2_tourists is not None, "Model_2_TwoWay_FE_Clustered ln(Overnight Tourists) missing from drivers_rq3.json"
        assert abs(m2_tourists["elasticity_coefficient"] - current_results["panel"]["tourist_elasticity"]) < 1e-4

        # Verify leave-one-out stability
        loo = drivers_data.get("leave_one_out_stability", {})
        assert "ln_alos" in loo
        assert loo["ln_alos"]["sign_stability_pct"] == 100.0

    def test_scenario_engine_json_matches_contract(self, current_results):
        scenario_file = DASHBOARD_DATA_DIR / "scenario_engine.json"
        assert scenario_file.exists(), f"Missing scenario_engine.json: {scenario_file}"
        with open(scenario_file, "r", encoding="utf-8") as f:
            scen_data = json.load(f)

        # Verify disclaimer matches contract
        disclaimer = scen_data.get("constants", {}).get("disclaimer")
        assert disclaimer == current_results["scenarios"]["policy_disclaimer"]

        # Verify gravity validation records
        grav_val = scen_data.get("gravity_models", {}).get("validation", [])
        ppml_val = next((v for v in grav_val if v.get("is_primary") is True or "PPML" in v.get("model_specification", "")), None)
        assert ppml_val is not None, "PPML Primary Gravity validation missing from scenario_engine.json"
        assert abs(ppml_val["predictive_r2"] - current_results["gravity"]["ppml_oos_r2"]) < 1e-3


    def test_model_metrics_json_matches_contract(self, current_results):
        assert MODEL_METRICS_PATH.exists(), f"Missing model_metrics.json: {MODEL_METRICS_PATH}"
        with open(MODEL_METRICS_PATH, "r", encoding="utf-8") as f:
            m_metrics = json.load(f)

        # Check parity with current_results
        assert abs(m_metrics["panel"]["alos_elasticity"] - current_results["panel"]["alos_elasticity"]) < 1e-4
        assert abs(m_metrics["panel"]["tourist_elasticity"] - current_results["panel"]["tourist_elasticity"]) < 1e-4
        assert abs(m_metrics["gravity"]["r2_oos"] - current_results["gravity"]["ppml_oos_r2"]) < 1e-3
        assert abs(m_metrics["gravity"]["distance_decay_friction"] - current_results["gravity"]["distance_decay_friction"]) < 1e-4
        assert abs(m_metrics["gravity"]["cross_region_barrier"] - current_results["gravity"]["cross_region_barrier"]) < 1e-4


class TestSnapshotTestSeparation:
    """Verifies that snapshot regression tests are strictly isolated from scientific tests."""

    def test_snapshot_directory_structure(self):
        snapshot_dir = ROOT_DIR / "tests/snapshot"
        assert snapshot_dir.exists(), "tests/snapshot/ directory missing"
        snapshot_files = list(snapshot_dir.glob("test_*.py"))
        assert len(snapshot_files) >= 1, "Expected at least 1 snapshot test file"

        # Check that test_baseline_snapshots.py uses snapshot marker
        baseline_test = snapshot_dir / "test_baseline_snapshots.py"
        assert baseline_test.exists()
        with open(baseline_test, "r", encoding="utf-8") as f:
            content = f.read()
        assert "@pytest.mark.snapshot" in content, "test_baseline_snapshots.py must be marked with @pytest.mark.snapshot"
        assert "snapshot regression checks" in content.lower(), "Snapshot tests must be labeled as regression checks"
        assert "hypothesis confirmed" not in content.lower(), "Snapshot tests must never claim 'hypothesis confirmed'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
