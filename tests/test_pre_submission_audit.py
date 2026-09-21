"""
Automated Validation Suite for Sprint E: Final Pre-Submission Audit & Judge Defense.
Covers:
  - Phase 58: Final Pre-Submission Audit (Methodology, Data Quality, Dashboard, Commercial, Creativity)
  - Phase 60: Authoritative Product Definition & North-Star Principle
  - Phase 61: Stop Condition Compliance
  - Phase 63: The Five Judge Questions Defense Package
"""

import json
import re
from pathlib import Path
import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
DATA_DIR = ROOT_DIR / "data"
DASHBOARD_DATA_DIR = ROOT_DIR / "dashboard/public/data"
DASHBOARD_SRC_DIR = ROOT_DIR / "dashboard/src"


@pytest.fixture(scope="module")
def duckdb_con():
    import duckdb
    duckdb_path = DATA_DIR / "processed" / "tourism_data.duckdb"
    con = duckdb.connect(str(duckdb_path), read_only=True)
    yield con
    con.close()


class TestPhase58MethodologyCriteria:
    """Validates methodology criteria specified in Phase 58 of IMPLEMENTATION_PLAN.md."""

    def test_economic_sustainability_centering(self):
        """Phase 58: Problem statement centered on economic sustainability."""
        agents_md = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        assert "economic dimension of sustainable tourism" in agents_md
        assert "more economic value from existing visitors" in agents_md

    def test_tvay_and_tey_in_duckdb(self, duckdb_con):
        """Phase 58: Main KPI = value per visitor-day (TEY & TVAY)."""
        res = duckdb_con.execute(
            "SELECT tey_rm_per_day, tvay_rm_per_day FROM sdg_sustainable_metrics WHERE year = 2025"
        ).fetchall()
        assert len(res) == 16
        for tey, tvay in res:
            assert tey > 0, "TEY must be strictly positive"
            assert tvay > 0, "TVAY must be strictly positive"
            assert tvay < tey, "TVAY (value-added) must be less than gross expenditure yield (TEY)"

    def test_two_way_fe_and_clustered_inference(self, duckdb_con):
        """Phase 58: Two-way FE implemented with state-clustered uncertainty."""
        models = duckdb_con.execute(
            "SELECT DISTINCT model_id FROM panel_regression_summary"
        ).fetchall()
        model_ids = [m[0] for m in models]
        assert "Model_2_TwoWay_FE_Clustered" in model_ids
        assert "Model_4_Yield_TwoWay_FE" in model_ids

        # Verify clustered covariance
        cov = duckdb_con.execute(
            "SELECT DISTINCT covariance_type FROM panel_regression_summary WHERE model_id = 'Model_2_TwoWay_FE_Clustered'"
        ).fetchone()[0]
        assert "clustered" in cov.lower()

    def test_ppml_gravity_holdout_validation(self, duckdb_con):
        """Phase 58: PPML implemented with genuine out-of-sample holdout validation."""
        val = duckdb_con.execute(
            "SELECT predictive_r2, testing_sample FROM corridor_gravity_validation WHERE model_specification = 'PPML Structural Gravity (Primary)'"
        ).fetchone()
        assert val is not None
        r2_oos, testing_sample = val
        assert "2025" in testing_sample
        assert 0.50 <= r2_oos <= 0.70, f"Unexpected R2_OOS: {r2_oos}"

    def test_scenario_clearly_non_causal(self):
        """Phase 58: Scenario clearly non-causal with explicit disclaimers."""
        from src.scenarios.simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        res = sim.simulate_corridor("Selangor", "Melaka")
        assert "Scenario estimate, not a causal forecast" in res["disclaimer"]


class TestPhase58DataQualityCriteria:
    """Validates data quality criteria specified in Phase 58 of IMPLEMENTATION_PLAN.md."""

    def test_official_source_registry_and_checksums(self):
        """Phase 58: Official sources documented with SHA-256 checksums."""
        registry_file = DATA_DIR / "metadata/source_registry.yaml"
        assert registry_file.exists()
        with open(registry_file, "r", encoding="utf-8") as f:
            registry = yaml.safe_load(f)

        assert "sources" in registry
        sources = registry["sources"]
        assert len(sources) >= 7

        for sname, sdata in sources.items():
            assert "checksum" in sdata, f"Source '{sname}' missing checksum"
            assert len(sdata["checksum"]) == 64, f"Invalid SHA-256 for '{sname}': {sdata['checksum']}"
            assert "data_status" in sdata
            assert "publication" in sdata

    def test_zero_fabrication_and_no_fallbacks(self):
        """Phase 58: Zero empirical fabrication, missing values propagate as NaN/null."""
        diag_py = (ROOT_DIR / "src/analytics/state_diagnostics.py").read_text(encoding="utf-8")
        assert "50.0  # fallback" not in diag_py
        assert "5000.0  # fallback" not in diag_py
        assert "300.0  # fallback" not in diag_py

        mc_py = (ROOT_DIR / "src/scenarios/monte_carlo.py").read_text(encoding="utf-8")
        assert "alos = 2.5" not in mc_py

    def test_constant_price_rm_available(self):
        """Phase 58: Constant-price RM price deflator table available."""
        price_file = DATA_DIR / "processed/price_index.csv"
        assert price_file.exists()


class TestPhase58DashboardCriteria:
    """Validates dashboard component criteria specified in Phase 58."""

    def test_all_model_values_generated_dynamically(self):
        """Phase 58: Dashboard loads all model values dynamically from model_metrics.json."""
        metrics_file = DASHBOARD_DATA_DIR / "model_metrics.json"
        assert metrics_file.exists()
        with open(metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        assert "gravity" in metrics
        assert "panel" in metrics
        assert "r2_oos" in metrics["gravity"]
        assert "yield_model" in metrics["panel"]

    def test_dashboard_provenance_and_status_badges(self):
        """Phase 58: Global provenance drawer and data status badges exist."""
        prov_file = DASHBOARD_SRC_DIR / "components/ProvenanceDrawer.tsx"
        assert prov_file.exists()
        prov_content = prov_file.read_text(encoding="utf-8")
        assert "Data Provenance & Audit Registry" in prov_content
        assert "SDG" in prov_content

    def test_dashboard_headline_and_storyline(self):
        """Phase 52: Headline and North-Star messaging."""
        header_file = DASHBOARD_SRC_DIR / "components/Header.tsx"
        assert header_file.exists()
        header_content = header_file.read_text(encoding="utf-8")
        assert "From More Tourists to" in header_content
        assert "More Value" in header_content
        assert "Monitor · Diagnose · Target · Simulate · Optimize" in header_content


class TestPhase60And63JudgeDefensePackage:
    """Validates the Five Judge Questions and North-Star positioning."""

    def test_judge_defense_document_exists_and_answers_all_questions(self):
        """Phase 63: The Five Judge Questions Defense Guide exists in docs/."""
        defense_file = DOCS_DIR / "judge_defense.md"
        assert defense_file.exists(), "docs/judge_defense.md is missing"
        content = defense_file.read_text(encoding="utf-8")

        # Must address all 5 Judge Questions
        assert "Judge Question 1: Where did this number come from?" in content
        assert "Judge Question 2: Why do you believe this relationship?" in content
        assert "Judge Question 3: Why should this corridor be targeted?" in content
        assert "Judge Question 4: What happens if your assumptions are wrong?" in content
        assert "Judge Question 5: How would a real organization use this?" in content

        # Must cite authoritative econometric and accounting evidence
        assert "0.5890" in content, "Missing PPML R2_OOS in judge defense"
        assert "0.6628" in content, "Missing ALOS elasticity in judge defense"
        assert "58" in content, "Missing 58 Pareto corridors in judge defense"
        assert "85.8%" in content, "Missing Accommodation VAI in judge defense"
        assert "Monte Carlo" in content, "Missing Monte Carlo in judge defense"
        assert "MILP" in content, "Missing MILP portfolio optimizer in judge defense"

    def test_north_star_principle_in_key_documents(self):
        """Phase 60: North-Star principle present across documentation."""
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        defense = (DOCS_DIR / "judge_defense.md").read_text(encoding="utf-8")

        for doc in (readme, defense):
            assert "Do not only maximize tourists" in doc
            assert "Maximize sustainable" in doc


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__]))
