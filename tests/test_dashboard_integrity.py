"""
Unit and Validation Tests for Sprint 7 Dashboard Integrity.
Covers:
  - Phase 28: Corridor -> Simulator Pre-population Data Contracts
  - Phase 29: Dashboard Provenance Registry & Source Metadata
  - Phase 30: Visible Data Status Tags & Preliminary/Official Distinctions
  - Phase 31: Elimination of "Official Brief" Language & Causal Humility
  - Phase 32: State Decision Summary Completeness & Metrics Availability
  - Phase 34: Product Value Frontier (VAI vs ITC vs Estimated GVA)
"""

import json
import re
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "dashboard/public/data"
SRC_DASHBOARD = ROOT_DIR / "dashboard/src"


class TestModelMetricsAndProvenance:
    """Sprint 7: Verification of model_metrics.json and source_metadata.json feeds"""

    def test_model_metrics_json_integrity(self):
        metrics_file = DATA_DIR / "model_metrics.json"
        assert metrics_file.exists(), "dashboard/public/data/model_metrics.json does not exist"
        with open(metrics_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "gravity" in data, "Missing 'gravity' in model_metrics.json"
        assert "r2_oos" in data["gravity"], "Missing 'r2_oos' in gravity metrics"
        assert 0.5 <= data["gravity"]["r2_oos"] <= 0.7, f"Unexpected r2_oos: {data['gravity']['r2_oos']}"
        assert "distance_decay_friction" in data["gravity"]

    def test_source_metadata_json_integrity(self):
        source_file = DATA_DIR / "source_metadata.json"
        assert source_file.exists(), "dashboard/public/data/source_metadata.json does not exist"
        with open(source_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "sources" in data
        sources = data["sources"]
        assert "tsa_macro_and_products" in sources
        assert "state_domestic_tourism_2025" in sources
        assert "multi_year_state_panel" in sources

        # Verify data status is explicitly documented
        for sname, sinfo in sources.items():
            assert "data_status" in sinfo, f"Source '{sname}' missing 'data_status'"
            assert "organization" in sinfo, f"Source '{sname}' missing 'organization'"


class TestNoOfficialBriefLanguage:
    """Phase 31: Verification that 'Official Decision-Support Brief' language has been removed"""

    def test_no_official_brief_in_dashboard_source(self):
        forbidden_patterns = [
            re.compile(r"Official\s+Decision-Support\s+Brief", re.IGNORECASE),
            re.compile(r"Official\s+Policy\s+Briefing", re.IGNORECASE),
        ]

        offending_lines = []
        for ext in ("*.ts", "*.tsx"):
            for filepath in SRC_DASHBOARD.rglob(ext):
                with open(filepath, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        for pat in forbidden_patterns:
                            if pat.search(line):
                                offending_lines.append(f"{filepath.name}:{line_num}: {line.strip()}")

        assert not offending_lines, (
            "Found forbidden 'Official Brief' language in dashboard components:\n"
            + "\n".join(offending_lines)
        )


class TestStateDecisionSummaryCompleteness:
    """Phase 32 & 33: State Decision Summary metrics completeness across all 16 states"""

    def test_state_decision_summary_data_present(self):
        profiles_file = DATA_DIR / "state_profiles.json"
        assert profiles_file.exists()
        with open(profiles_file, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        assert len(profiles) == 16, f"Expected 16 states, found {len(profiles)}"

        for state_name, profile in profiles.items():
            b = profile.get("baseline_2025", {})
            sdg = profile.get("sdg_metrics", {})

            assert "alos_days" in b, f"Missing alos_days for {state_name}"
            assert b["alos_days"] > 0, f"Invalid alos_days for {state_name}"
            assert "spend_per_night_rm" in b, f"Missing spend_per_night_rm for {state_name}"
            assert "tourists_thousands" in b, f"Missing tourists_thousands for {state_name}"

            # Capacity metrics must be either float or None (not missing from dictionary)
            assert "hotel_rooms" in b
            assert "aor_pct" in b

            # Typology and coverage
            assert "yield_typology" in b or "yield_typology" in sdg, f"Missing yield_typology for {state_name}"
            assert "mapping_coverage_pct" in sdg, f"Missing mapping_coverage_pct for {state_name}"


class TestProductValueFrontier:
    """Phase 34: Product Value Frontier (VAI vs ITC vs Estimated GVA) data contracts"""

    def test_product_summary_frontier_fields(self):
        tsa_file = DATA_DIR / "tsa_macro.json"
        assert tsa_file.exists()
        with open(tsa_file, "r", encoding="utf-8") as f:
            tsa = json.load(f)

        assert "product_summary" in tsa
        products = tsa["product_summary"]
        assert len(products) == 8, f"Expected 8 TSA products, found {len(products)}"

        for p in products:
            assert "product" in p
            assert "vai_2025" in p
            assert 0.0 <= p["vai_2025"] <= 1.0, f"Invalid VAI for {p['product']}"
            assert "itc_2025" in p
            assert p["itc_2025"] >= 0
            assert "strategic_quadrant" in p
            assert any(
                p["strategic_quadrant"].startswith(prefix)
                for prefix in (
                    "High-Value Core",
                    "Growth Opportunity",
                    "Efficiency",
                    "Lower",
                )
            ), f"Unexpected quadrant: {p['strategic_quadrant']}"


class TestCorridorToSimulatorContract:
    """Phase 28: Corridor to Simulator pre-population contracts"""

    def test_all_corridors_have_valid_destinations_in_scenario_engine(self):
        od_file = DATA_DIR / "od_corridors.json"
        scenario_file = DATA_DIR / "scenario_engine.json"
        assert od_file.exists() and scenario_file.exists()

        with open(od_file, "r", encoding="utf-8") as f:
            od = json.load(f)
        with open(scenario_file, "r", encoding="utf-8") as f:
            scen = json.load(f)

        destinations_in_corridors = set(c["destination"] for c in od["corridors_2025"])
        destinations_in_simulator = set(scen["state_baselines"].keys())

        missing = destinations_in_corridors - destinations_in_simulator
        assert not missing, f"Destinations in corridors missing from scenario baselines: {missing}"


class TestNoHardcodedModelFallbacks:
    """Phase 26 / Sprint 7: Ensure dynamic consumption of model_metrics without fallback constants"""

    def test_corridor_network_no_hardcoded_gravity_fallbacks(self):
        corridor_ts = SRC_DASHBOARD / "components" / "CorridorNetwork.tsx"
        assert corridor_ts.exists()
        content = corridor_ts.read_text(encoding="utf-8")
        assert "|| '0.5890'" not in content, "Found hardcoded '0.5890' fallback in CorridorNetwork.tsx"
        assert "|| '-0.410'" not in content, "Found hardcoded '-0.410' fallback in CorridorNetwork.tsx"


@pytest.fixture(scope="module")
def duckdb_con():
    import duckdb
    duckdb_path = ROOT_DIR / "data/processed/tourism_data.duckdb"
    con = duckdb.connect(str(duckdb_path), read_only=True)
    yield con
    con.close()


class TestDashboardAnalyticalContracts:
    """
    Phase 41: Dashboard Analytical Contract Tests.
    Mandates exact numerical parity between Python model outputs in DuckDB and dashboard JSON feeds:
      1. Dashboard R² == Python / Model R²
      2. Dashboard coefficients == Python / Model coefficients
      3. Dashboard scenario GVA == Python scenario engine output
      4. Dashboard HHI == Python analytical output
      5. Dashboard state KPI == Pipeline output
    """

    def test_dashboard_r2_parity_with_python(self, duckdb_con):
        """Phase 41.1: Assert dashboard R² == Python R² across Gravity and Panel models."""
        metrics_file = DATA_DIR / "model_metrics.json"
        with open(metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        # 1. Gravity Out-of-Sample R²
        db_grav_r2 = duckdb_con.execute(
            "SELECT predictive_r2 FROM corridor_gravity_validation WHERE model_specification = 'PPML Structural Gravity (Primary)'"
        ).fetchone()[0]
        dash_grav_r2 = metrics["gravity"]["r2_oos"]
        assert abs(dash_grav_r2 - db_grav_r2) < 1e-4, f"Gravity R² mismatch: Dash={dash_grav_r2}, DB={db_grav_r2}"

        # 2. Panel Yield Model R²
        db_yield_r2 = duckdb_con.execute(
            "SELECT r_squared FROM panel_regression_summary WHERE model_id = 'Model_4_Yield_TwoWay_FE' LIMIT 1"
        ).fetchone()[0]
        dash_yield_r2 = metrics["panel"]["yield_model"]["r_squared"]
        assert abs(dash_yield_r2 - db_yield_r2) < 1e-4, f"Yield Model R² mismatch: Dash={dash_yield_r2}, DB={db_yield_r2}"

    def test_dashboard_coefficients_parity_with_model_output(self, duckdb_con):
        """Phase 41.2: Assert dashboard coefficients == model output."""
        metrics_file = DATA_DIR / "model_metrics.json"
        with open(metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        # 1. Gravity Distance Decay & Cross-Region Coefficients
        grav_rows = duckdb_con.execute(
            "SELECT variable, coefficient FROM corridor_gravity_model_summary WHERE model_type LIKE 'PPML%'"
        ).fetchall()
        grav_dict = {r[0]: r[1] for r in grav_rows}

        db_dist = grav_dict["Distance Decay Friction (PPML)"]
        db_cross = grav_dict["Cross-Region Flight Barrier (Peninsula <-> Borneo)"]
        assert abs(metrics["gravity"]["distance_decay_friction"] - db_dist) < 1e-4
        assert abs(metrics["gravity"]["cross_region_barrier"] - db_cross) < 1e-4

        # 2. Panel Two-Way FE Elasticities
        panel_rows = duckdb_con.execute(
            "SELECT independent_variable, elasticity_coefficient FROM panel_regression_summary WHERE model_id = 'Model_2_TwoWay_FE_Clustered'"
        ).fetchall()
        panel_dict = {r[0]: r[1] for r in panel_rows}

        assert abs(metrics["panel"]["alos_elasticity"] - panel_dict["ln(ALOS)"]) < 1e-4
        assert abs(metrics["panel"]["tourist_elasticity"] - panel_dict["ln(Overnight Tourists)"]) < 1e-4

    def test_dashboard_scenario_gva_parity_with_scenario_engine(self):
        """Phase 41.3: Assert dashboard scenario GVA proxy == Python scenario engine output."""
        from src.scenarios.simulator import ScenarioSimulator
        simulator = ScenarioSimulator()

        # Test corridor simulation parity
        res = simulator.simulate_corridor("Selangor", "Melaka", delta_alos=0.5, affected_share=0.15)
        spend = res["simulated_impact"]["additional_accommodation_spend_rm_million"]
        gva = res["simulated_impact"]["potential_additional_value_added_rm_million"]
        vai = res["inputs"]["accommodation_vai_used"]
        expected_gva_proxy = round(spend * vai, 2)
        assert abs(gva - expected_gva_proxy) < 1e-2, f"Corridor GVA proxy mismatch: {gva} vs {expected_gva_proxy}"

        # Test state benchmark JSON scenario GVA formula consistency
        scen_file = DATA_DIR / "scenario_engine.json"
        with open(scen_file, "r", encoding="utf-8") as f:
            scen = json.load(f)

        for state, benchmarks in scen.get("benchmarks", {}).items():
            for bname, bdata in benchmarks.items():
                impact = bdata["simulated_impact"]
                inputs = bdata["inputs"]
                b_spend = impact["additional_accommodation_spend_rm_million"]
                b_gva = impact["potential_additional_value_added_rm_million"]
                b_vai = inputs["accommodation_vai_used"]
                b_expected_gva = round(b_spend * b_vai, 2)
                assert abs(b_gva - b_expected_gva) <= 0.05, f"Scenario GVA mismatch for {state} ({bname}): {b_gva} vs {b_expected_gva}"

    def test_dashboard_hhi_parity_with_analytical_output(self, duckdb_con):
        """Phase 41.4: Assert dashboard destination feeder HHI == analytical output."""
        db_hhi_rows = duckdb_con.execute(
            "SELECT destination, interstate_origin_hhi, top_feeder_origin FROM destination_concentration WHERE year = 2025"
        ).fetchall()
        db_hhi = {r[0]: (round(r[1], 2), r[2]) for r in db_hhi_rows}

        profiles_file = DATA_DIR / "state_profiles.json"
        with open(profiles_file, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        for state, (expected_hhi, expected_feeder) in db_hhi.items():
            if state in profiles and "sdg_metrics" in profiles[state]:
                state_sdg = profiles[state]["sdg_metrics"]
                if "hhi_interstate" in state_sdg:
                    assert abs(state_sdg["hhi_interstate"] - expected_hhi) < 0.1, (
                        f"HHI mismatch for {state}: Dash={state_sdg['hhi_interstate']}, DB={expected_hhi}"
                    )

    def test_dashboard_state_kpi_parity_with_pipeline_output(self, duckdb_con):
        """Phase 41.5: Assert dashboard state KPIs == pipeline state_year output."""
        db_state_rows = duckdb_con.execute(
            "SELECT state, alos_days, tourists_thousands, spend_per_night_rm FROM state_year WHERE year = 2025"
        ).fetchall()
        db_states = {r[0]: {"alos": r[1], "tourists": r[2], "spend": r[3]} for r in db_state_rows}

        profiles_file = DATA_DIR / "state_profiles.json"
        with open(profiles_file, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        assert len(profiles) == 16
        for state, exp in db_states.items():
            assert state in profiles, f"State {state} missing from state_profiles.json"
            b = profiles[state]["baseline_2025"]
            assert abs(b["alos_days"] - exp["alos"]) < 1e-2, f"ALOS mismatch for {state}"
            assert abs(b["tourists_thousands"] - exp["tourists"]) < 0.1, f"Tourists mismatch for {state}"
            assert abs(b["spend_per_night_rm"] - exp["spend"]) < 1e-2, f"Spend per night mismatch for {state}"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__]))
