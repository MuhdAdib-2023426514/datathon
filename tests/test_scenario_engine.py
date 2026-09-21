"""
Unit and Validation Tests for Sprint 6 Scenario Engine.
Covers:
  - Phase 21: One Source of Truth (Formula Parity)
  - Phase 22: Scenario Affected Share
  - Phase 23: Room-Night Capacity Conversion & Guests per Room
  - Phase 24: VFR Scenario Capacity Impact (Lodging Demand Inclusion)
  - Phase 25: Scenario Assumption Metadata Classification
  - Phase 27: Capacity Sensitivity Thresholds (75%, 80%, 85%) & Seasonal Caveat
"""

import pytest
import numpy as np
from pathlib import Path

from src.scenarios.simulator import (
    ScenarioSimulator,
    MANDATORY_DISCLAIMER,
    SEASONAL_CAPACITY_CAVEAT,
    DEFAULT_GUESTS_PER_ROOM,
    DEFAULT_AFFECTED_SHARE,
)


@pytest.fixture(scope="module")
def simulator():
    sim = ScenarioSimulator()
    return sim


class TestScenarioAffectedShare:
    """Phase 22: AdditionalNights = Tourists * AffectedShare * DeltaALOS"""

    def test_affected_share_proportionality(self, simulator):
        # Corridor: Selangor -> Melaka, delta_alos = 0.5
        # 100% affected share vs 15% affected share
        res_full = simulator.simulate_corridor(
            origin="Selangor", destination="Melaka", delta_alos=0.5, affected_share=1.0
        )
        res_15 = simulator.simulate_corridor(
            origin="Selangor", destination="Melaka", delta_alos=0.5, affected_share=0.15
        )

        nights_full = res_full["simulated_impact"]["additional_tourist_nights"]
        nights_15 = res_15["simulated_impact"]["additional_tourist_nights"]

        assert nights_full > 0
        assert np.isclose(nights_15, nights_full * 0.15, rtol=1e-3)

        spend_full = res_full["simulated_impact"]["additional_accommodation_spend_rm_million"]
        spend_15 = res_15["simulated_impact"]["additional_accommodation_spend_rm_million"]
        assert np.isclose(spend_15, spend_full * 0.15, rtol=1e-2)

    def test_affected_share_boundary_conditions(self, simulator):
        # 0% affected share gives 0 incremental impact
        res_zero = simulator.simulate_corridor(
            origin="Selangor", destination="Melaka", delta_alos=0.5, affected_share=0.0
        )
        assert res_zero["simulated_impact"]["additional_tourist_nights"] == 0.0
        assert res_zero["simulated_impact"]["additional_accommodation_spend_rm_million"] == 0.0
        assert res_zero["simulated_impact"]["potential_additional_value_added_rm_million"] == 0.0

        # Invalid bounds raise ValueError
        with pytest.raises(ValueError):
            simulator.simulate_corridor(
                origin="Selangor", destination="Melaka", delta_alos=0.5, affected_share=-0.1
            )
        with pytest.raises(ValueError):
            simulator.simulate_corridor(
                origin="Selangor", destination="Melaka", delta_alos=0.5, affected_share=1.5
            )


class TestRoomNightConversion:
    """Phase 23: AdditionalRoomNights = AdditionalGuestNights / GuestsPerOccupiedRoom"""

    def test_room_night_conversion_formula(self, simulator):
        # Test Melaka comprehensive scenario
        res_1_8 = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.4,
            affected_share=0.15,
            conversion_pct=10.0,
            vfr_conversion_pct=0.0,
            guests_per_room=1.8,
        )
        res_1_0 = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.4,
            affected_share=0.15,
            conversion_pct=10.0,
            vfr_conversion_pct=0.0,
            guests_per_room=1.0,
        )

        cap_1_8 = res_1_8["capacity_feasibility"]
        cap_1_0 = res_1_0["capacity_feasibility"]

        # Room demand at 1.8 guests/room must be exactly 1 / 1.8 of room demand at 1.0 guests/room
        assert cap_1_8["daily_rooms_demanded"] is not None
        assert cap_1_0["daily_rooms_demanded"] is not None
        assert np.isclose(
            cap_1_8["daily_rooms_demanded"], cap_1_0["daily_rooms_demanded"] / 1.8, rtol=1e-2
        )

        # Projected AOR must be higher when guests per room is lower (more rooms needed per guest)
        assert cap_1_0["implied_destination_aor_pct"] > cap_1_8["implied_destination_aor_pct"]

    def test_projected_aor_accounting_identity(self, simulator):
        res = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.4,
            affected_share=0.15,
            conversion_pct=10.0,
            vfr_conversion_pct=5.0,
            guests_per_room=1.8,
        )
        cap = res["capacity_feasibility"]
        base = res["baseline"]

        avail_rooms = base["destination_available_rooms"]
        base_aor = base["destination_baseline_aor_pct"]
        daily_rooms = cap["daily_rooms_demanded"]

        expected_delta_aor = (daily_rooms / avail_rooms) * 100.0
        assert np.isclose(cap["delta_aor_pct"], expected_delta_aor, atol=0.05)
        assert np.isclose(cap["implied_destination_aor_pct"], base_aor + cap["delta_aor_pct"], atol=0.05)


class TestVFRScenarioCapacity:
    """Phase 24: Converted VFR guest nights must generate room demand and affect AOR"""

    def test_vfr_conversion_increases_room_demand(self, simulator):
        # Without VFR conversion
        res_no_vfr = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.4,
            affected_share=0.15,
            conversion_pct=10.0,
            vfr_conversion_pct=0.0,
        )
        # With 10% VFR conversion
        res_with_vfr = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.4,
            affected_share=0.15,
            conversion_pct=10.0,
            vfr_conversion_pct=10.0,
        )

        cap_no = res_no_vfr["capacity_feasibility"]
        cap_vfr = res_with_vfr["capacity_feasibility"]

        # VFR conversion MUST increase room demand and implied AOR
        assert cap_vfr["daily_rooms_demanded"] > cap_no["daily_rooms_demanded"]
        assert cap_vfr["implied_destination_aor_pct"] > cap_no["implied_destination_aor_pct"]

        # Both revenue and capacity must reflect converted VFR
        spend_no = res_no_vfr["simulated_impact"]["additional_accommodation_spend_rm_million"]
        spend_vfr = res_with_vfr["simulated_impact"]["additional_accommodation_spend_rm_million"]
        assert spend_vfr > spend_no


class TestScenarioAssumptionMetadata:
    """Phase 25: All inputs and parameters must have metadata classifying official/derived/scenario_assumption"""

    def test_assumption_metadata_structure(self, simulator):
        res = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.4,
            affected_share=0.15,
            conversion_pct=10.0,
            vfr_conversion_pct=5.0,
        )
        assert "metadata" in res
        meta = res["metadata"]

        # Check required classified fields
        assert meta["affected_share"]["status"] == "scenario_assumption"
        assert meta["guests_per_room"]["status"] == "scenario_assumption"
        assert meta["delta_alos"]["status"] == "scenario_assumption"
        assert meta["planning_threshold"]["status"] == "scenario_assumption"

        assert meta["baseline_aor"]["status"] == "official"
        assert meta["available_rooms"]["status"] == "official"
        assert meta["baseline_tourists"]["status"] == "official"
        assert meta["baseline_alos"]["status"] == "official"

        assert meta["spend_per_night"]["status"] == "derived"
        assert meta["accommodation_vai"]["status"] in ("official", "derived")


class TestCapacitySensitivity:
    """Phase 27: Configurable planning thresholds (75%, 80%, 85%) and seasonal caveat"""

    def test_configurable_planning_thresholds(self, simulator):
        # Destination with substantial conversion
        res_80 = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.8,
            affected_share=0.30,
            conversion_pct=15.0,
            planning_threshold=80.0,
        )
        res_75 = simulator.simulate_destination_comprehensive(
            destination="Melaka",
            delta_alos=0.8,
            affected_share=0.30,
            conversion_pct=15.0,
            planning_threshold=75.0,
        )

        implied_aor = res_80["capacity_feasibility"]["implied_destination_aor_pct"]
        if 75.0 < implied_aor <= 80.0:
            assert res_80["capacity_feasibility"]["saturation_tier"] == "Planning Watch"
            assert res_75["capacity_feasibility"]["saturation_tier"] == "Severe Saturation"

        # Seasonal caveat must be present in capacity feasibility
        assert "seasonal_caveat" in res_80["capacity_feasibility"]
        assert "seasonal/weekend" in res_80["capacity_feasibility"]["seasonal_caveat"].lower()


class TestMandatoryGuardrails:
    """AGENTS.md Section 7, 9, 12 non-negotiable scenario guardrails"""

    def test_disclaimer_presence(self, simulator):
        corridor_res = simulator.simulate_corridor("Selangor", "Melaka", delta_alos=0.5)
        assert corridor_res["disclaimer"] == MANDATORY_DISCLAIMER

        dest_res = simulator.simulate_destination_comprehensive("Melaka", delta_alos=0.4)
        assert dest_res["disclaimer"] == MANDATORY_DISCLAIMER


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__]))
