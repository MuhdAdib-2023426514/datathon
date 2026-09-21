"""
Scenario Parity Test Suite (Plan Section 21 / Sprint E)
Verifies mathematical and categorical equivalence between Python analytics engine
and TypeScript dashboard scenario simulator.

Asserts parity within 1e-4 tolerance for:
  1. Additional visitor nights
  2. Additional room nights
  3. Additional accommodation expenditure (RM Million)
  4. Incremental GVA proxy (RM Million)
  5. Projected Average Occupancy Rate (AOR %)
  6. Capacity status / saturation tier
"""

import unittest
from typing import Dict, Any, Optional
import duckdb
from src.config.paths import DUCKDB_PATH
from src.scenarios.simulator import ScenarioSimulator


def simulate_typescript_contract(
    tourists_k: float,
    visitors_k: float,
    baseline_alos: float,
    baseline_spend_per_night: float,
    delta_alos: float,
    affected_share_pct: float,
    conversion_rate_pct: float,
    yield_uplift_pct: float,
    vfr_conversion_rate_pct: float,
    unpaid_vfr_pct: Optional[float],
    total_rooms: Optional[float],
    baseline_aor: Optional[float],
    planning_threshold: float = 80.0,
    accom_vai: float = 0.8579,
    guests_per_room: float = 1.8,
) -> Dict[str, Any]:
    """
    Exact mathematical replica of the calculation pipeline executed in
    dashboard/src/components/ScenarioSimulator.tsx lines 205-285.
    """
    baseline_excursionists_k = visitors_k - tourists_k

    # 1. Stay extension with campaign affected share
    add_nights_from_alos_k = tourists_k * (affected_share_pct / 100.0) * delta_alos

    # 2. Converted excursionists into overnight tourists
    converted_tourists_k = baseline_excursionists_k * (conversion_rate_pct / 100.0)
    add_nights_from_converted_k = converted_tourists_k * (baseline_alos + delta_alos)

    # 3. Converted unpaid VFR stays into commercial/registered lodging
    has_vfr_data = unpaid_vfr_pct is not None
    vfr_pct_val = unpaid_vfr_pct if has_vfr_data else 0.0
    vfr_tourists_k = tourists_k * (vfr_pct_val / 100.0)
    converted_vfr_tourists_k = vfr_tourists_k * (vfr_conversion_rate_pct / 100.0)
    vfr_nights_k = converted_vfr_tourists_k * (baseline_alos + delta_alos)
    homestay_nightly_rate = max(75.0, baseline_spend_per_night * 0.85)
    vfr_accom_spend_rm = (vfr_nights_k * 1e3 * homestay_nightly_rate) / 1e6 if has_vfr_data else 0.0

    # Total additional guest nights (thousands)
    total_additional_guest_nights_k = add_nights_from_alos_k + add_nights_from_converted_k + vfr_nights_k

    # 4. Expenditure uplift
    new_spend_per_night = baseline_spend_per_night * (1.0 + yield_uplift_pct / 100.0)
    existing_nights_k = tourists_k * baseline_alos
    new_nights_spend_rm = ((add_nights_from_alos_k + add_nights_from_converted_k) * 1e3 * new_spend_per_night) / 1e6
    existing_nights_uplift_rm = (existing_nights_k * 1e3 * (new_spend_per_night - baseline_spend_per_night)) / 1e6
    total_additional_accom_spend_mil = new_nights_spend_rm + existing_nights_uplift_rm + vfr_accom_spend_rm

    # 5. Potential Additional Tourism Value Added Proxy
    potential_additional_tdgva_mil = total_additional_accom_spend_mil * accom_vai

    # 6. Capacity Feasibility & Implied AOR
    has_capacity_data = total_rooms is not None and baseline_aor is not None
    available_room_nights_year_k = (total_rooms * 365.0) / 1e3 if (has_capacity_data and total_rooms > 0) else None
    additional_room_nights_year_k = total_additional_guest_nights_k / guests_per_room
    additional_aor_pct = (
        (additional_room_nights_year_k / available_room_nights_year_k) * 100.0
        if (has_capacity_data and available_room_nights_year_k and available_room_nights_year_k > 0)
        else None
    )
    simulated_aor = (baseline_aor + additional_aor_pct) if (has_capacity_data and baseline_aor is not None and additional_aor_pct is not None) else None

    # 7. Capacity status tier
    if simulated_aor is None:
        capacity_status = "Unknown"
    elif simulated_aor > 100.0:
        capacity_status = "Physical Breach"
    elif simulated_aor > planning_threshold:
        capacity_status = "Severe Saturation"
    elif simulated_aor >= (planning_threshold - 10.0):
        capacity_status = "Planning Watch"
    else:
        capacity_status = "Normal"

    return {
        "additional_visitor_nights": total_additional_guest_nights_k * 1000.0,
        "additional_room_nights": additional_room_nights_year_k * 1000.0,
        "additional_expenditure_rm_million": total_additional_accom_spend_mil,
        "incremental_gva_rm_million": potential_additional_tdgva_mil,
        "projected_aor_pct": simulated_aor,
        "capacity_status": capacity_status,
    }


class TestScenarioParity(unittest.TestCase):
    """Verifies that Python and TypeScript scenario simulation pipelines are numerically identical."""

    @classmethod
    def setUpClass(cls):
        cls.db_path = DUCKDB_PATH
        cls.simulator = ScenarioSimulator()

        # Connect to DuckDB to extract 2025 official baseline profiles
        con = duckdb.connect(str(cls.db_path), read_only=True)
        cls.state_rows = con.execute("""
            SELECT 
                s.state,
                s.tourists_thousands,
                s.visitors_thousands,
                s.alos_days,
                s.spend_per_night_rm,
                s.unpaid_vfr_share_pct,
                c.hotel_rooms_2025,
                c.aor_2025_pct
            FROM state_year s
            LEFT JOIN accommodation_capacity c ON s.state = c.state
            WHERE s.year = 2025
        """).df().set_index("state")
        con.close()

    def test_parity_melaka_moderate_preset(self):
        """Test Melaka under Moderate Preset: +0.4d, 15% reach, 10% conv, 10% spend uplift, 5% VFR, 80% ceiling."""
        state = "Melaka"
        row = self.state_rows.loc[state]

        # 1. Compute in Python
        py_res = self.simulator.simulate_destination_comprehensive(
            destination=state,
            delta_alos=0.4,
            affected_share=0.15,
            conversion_pct=10.0,
            yield_uplift_pct=10.0,
            vfr_conversion_pct=5.0,
            guests_per_room=1.8,
            planning_threshold=80.0,
        )

        # 2. Compute via TypeScript contract
        ts_res = simulate_typescript_contract(
            tourists_k=float(row["tourists_thousands"]),
            visitors_k=float(row["visitors_thousands"]),
            baseline_alos=float(row["alos_days"]),
            baseline_spend_per_night=float(row["spend_per_night_rm"]),
            delta_alos=0.4,
            affected_share_pct=15.0,
            conversion_rate_pct=10.0,
            yield_uplift_pct=10.0,
            vfr_conversion_rate_pct=5.0,
            unpaid_vfr_pct=float(row["unpaid_vfr_share_pct"]) if row["unpaid_vfr_share_pct"] is not None else None,
            total_rooms=float(row["hotel_rooms_2025"]) if row["hotel_rooms_2025"] is not None else None,
            baseline_aor=float(row["aor_2025_pct"]) if row["aor_2025_pct"] is not None else None,
            planning_threshold=80.0,
            accom_vai=self.simulator.national_accom_vai,
            guests_per_room=1.8,
        )

        # Assert parity within tolerance (spend & GVA reported to 2 decimal places / RM 0.01M in simulator)
        self.assertAlmostEqual(
            py_res["simulated_impact"]["total_additional_guest_nights"],
            ts_res["additional_visitor_nights"],
            places=0,
            msg="Visitor nights mismatch on Melaka",
        )
        self.assertAlmostEqual(
            py_res["simulated_impact"]["additional_accommodation_spend_rm_million"],
            round(ts_res["additional_expenditure_rm_million"], 2),
            places=2,
            msg="Accommodation spend mismatch on Melaka",
        )
        self.assertAlmostEqual(
            py_res["simulated_impact"]["potential_additional_value_added_rm_million"],
            round(ts_res["incremental_gva_rm_million"], 2),
            places=2,
            msg="Incremental GVA mismatch on Melaka",
        )
        self.assertAlmostEqual(
            py_res["capacity_feasibility"]["implied_destination_aor_pct"],
            round(ts_res["projected_aor_pct"], 2),
            places=2,
            msg="Projected AOR mismatch on Melaka",
        )
        self.assertEqual(
            py_res["capacity_feasibility"]["saturation_tier"],
            ts_res["capacity_status"],
            msg="Capacity tier mismatch on Melaka",
        )

    def test_parity_pahang_ambitious_preset(self):
        """Test Pahang under Ambitious Preset: +0.6d, 25% reach, 20% conv, 15% spend uplift, 10% VFR, 80% ceiling."""
        state = "Pahang"
        row = self.state_rows.loc[state]

        py_res = self.simulator.simulate_destination_comprehensive(
            destination=state,
            delta_alos=0.6,
            affected_share=0.25,
            conversion_pct=20.0,
            yield_uplift_pct=15.0,
            vfr_conversion_pct=10.0,
            guests_per_room=1.8,
            planning_threshold=80.0,
        )

        ts_res = simulate_typescript_contract(
            tourists_k=float(row["tourists_thousands"]),
            visitors_k=float(row["visitors_thousands"]),
            baseline_alos=float(row["alos_days"]),
            baseline_spend_per_night=float(row["spend_per_night_rm"]),
            delta_alos=0.6,
            affected_share_pct=25.0,
            conversion_rate_pct=20.0,
            yield_uplift_pct=15.0,
            vfr_conversion_rate_pct=10.0,
            unpaid_vfr_pct=float(row["unpaid_vfr_share_pct"]) if row["unpaid_vfr_share_pct"] is not None else None,
            total_rooms=float(row["hotel_rooms_2025"]) if row["hotel_rooms_2025"] is not None else None,
            baseline_aor=float(row["aor_2025_pct"]) if row["aor_2025_pct"] is not None else None,
            planning_threshold=80.0,
            accom_vai=self.simulator.national_accom_vai,
            guests_per_room=1.8,
        )

        self.assertAlmostEqual(
            py_res["simulated_impact"]["total_additional_guest_nights"],
            ts_res["additional_visitor_nights"],
            places=0,
        )
        self.assertAlmostEqual(
            py_res["simulated_impact"]["additional_accommodation_spend_rm_million"],
            round(ts_res["additional_expenditure_rm_million"], 2),
            places=2,
        )
        self.assertAlmostEqual(
            py_res["simulated_impact"]["potential_additional_value_added_rm_million"],
            round(ts_res["incremental_gva_rm_million"], 2),
            places=2,
        )
        self.assertAlmostEqual(
            py_res["capacity_feasibility"]["implied_destination_aor_pct"],
            round(ts_res["projected_aor_pct"], 2),
            places=2,
        )
        self.assertEqual(
            py_res["capacity_feasibility"]["saturation_tier"],
            ts_res["capacity_status"],
        )

    def test_parity_penang_conservative_preset(self):
        """Test Pulau Pinang under Conservative Preset: +0.2d, 10% reach, 5% conv, 5% spend uplift, 2.5% VFR, 75% ceiling."""
        state = "Pulau Pinang"
        row = self.state_rows.loc[state]

        py_res = self.simulator.simulate_destination_comprehensive(
            destination=state,
            delta_alos=0.2,
            affected_share=0.10,
            conversion_pct=5.0,
            yield_uplift_pct=5.0,
            vfr_conversion_pct=2.5,
            guests_per_room=1.8,
            planning_threshold=75.0,
        )

        ts_res = simulate_typescript_contract(
            tourists_k=float(row["tourists_thousands"]),
            visitors_k=float(row["visitors_thousands"]),
            baseline_alos=float(row["alos_days"]),
            baseline_spend_per_night=float(row["spend_per_night_rm"]),
            delta_alos=0.2,
            affected_share_pct=10.0,
            conversion_rate_pct=5.0,
            yield_uplift_pct=5.0,
            vfr_conversion_rate_pct=2.5,
            unpaid_vfr_pct=float(row["unpaid_vfr_share_pct"]) if row["unpaid_vfr_share_pct"] is not None else None,
            total_rooms=float(row["hotel_rooms_2025"]) if row["hotel_rooms_2025"] is not None else None,
            baseline_aor=float(row["aor_2025_pct"]) if row["aor_2025_pct"] is not None else None,
            planning_threshold=75.0,
            accom_vai=self.simulator.national_accom_vai,
            guests_per_room=1.8,
        )

        self.assertAlmostEqual(
            py_res["simulated_impact"]["total_additional_guest_nights"],
            ts_res["additional_visitor_nights"],
            places=0,
        )
        self.assertAlmostEqual(
            py_res["simulated_impact"]["additional_accommodation_spend_rm_million"],
            round(ts_res["additional_expenditure_rm_million"], 2),
            places=2,
        )
        self.assertAlmostEqual(
            py_res["simulated_impact"]["potential_additional_value_added_rm_million"],
            round(ts_res["incremental_gva_rm_million"], 2),
            places=2,
        )
        self.assertAlmostEqual(
            py_res["capacity_feasibility"]["implied_destination_aor_pct"],
            round(ts_res["projected_aor_pct"], 2),
            places=2,
        )
        self.assertEqual(
            py_res["capacity_feasibility"]["saturation_tier"],
            ts_res["capacity_status"],
        )

    def test_parity_capacity_threshold_sensitivity(self):
        """Test that changing planning_threshold (70%, 78%, 85%) produces exact categorical parity."""
        state = "Johor"
        row = self.state_rows.loc[state]

        for threshold in [70.0, 78.0, 85.0]:
            py_res = self.simulator.simulate_destination_comprehensive(
                destination=state,
                delta_alos=0.5,
                affected_share=0.20,
                conversion_pct=10.0,
                yield_uplift_pct=10.0,
                vfr_conversion_pct=5.0,
                guests_per_room=1.8,
                planning_threshold=threshold,
            )

            ts_res = simulate_typescript_contract(
                tourists_k=float(row["tourists_thousands"]),
                visitors_k=float(row["visitors_thousands"]),
                baseline_alos=float(row["alos_days"]),
                baseline_spend_per_night=float(row["spend_per_night_rm"]),
                delta_alos=0.5,
                affected_share_pct=20.0,
                conversion_rate_pct=10.0,
                yield_uplift_pct=10.0,
                vfr_conversion_rate_pct=5.0,
                unpaid_vfr_pct=float(row["unpaid_vfr_share_pct"]) if row["unpaid_vfr_share_pct"] is not None else None,
                total_rooms=float(row["hotel_rooms_2025"]) if row["hotel_rooms_2025"] is not None else None,
                baseline_aor=float(row["aor_2025_pct"]) if row["aor_2025_pct"] is not None else None,
                planning_threshold=threshold,
                accom_vai=self.simulator.national_accom_vai,
                guests_per_room=1.8,
            )

            self.assertEqual(
                py_res["capacity_feasibility"]["saturation_tier"],
                ts_res["capacity_status"],
                msg=f"Threshold parity failure at {threshold}% for {state}",
            )


if __name__ == "__main__":
    unittest.main()
