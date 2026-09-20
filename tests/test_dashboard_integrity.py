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


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__]))
