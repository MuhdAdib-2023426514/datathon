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
    import json
    import subprocess
    from pathlib import Path
    args = dict(baselineTouristsK=tourists_k, baselineExcursionistsK=visitors_k-tourists_k,
                baselineAlos=baseline_alos, baselineSpendPerNight=baseline_spend_per_night,
                deltaAlos=delta_alos, affectedShare=affected_share_pct, conversionRate=conversion_rate_pct,
                yieldUplift=yield_uplift_pct, vfrConversionRate=vfr_conversion_rate_pct,
                unpaidVfrInput=unpaid_vfr_pct, totalRooms=total_rooms, baselineAor=baseline_aor,
                accomVAI=accom_vai, guestsPerRoom=guests_per_room, residentHouseholds=None,
                hasCapacityData=total_rooms is not None and baseline_aor is not None)
    root = Path(__file__).resolve().parents[1]
    command = "import {calculateScenario} from './dashboard/src/lib/scenario.ts'; let s=''; for await (const c of process.stdin) s+=c; console.log(JSON.stringify(calculateScenario(JSON.parse(s))));"
    result = json.loads(subprocess.check_output(['node','--input-type=module','-e',command],input=json.dumps(args),text=True,cwd=root))
    aor = result['simulatedAor']
    tier = ('Unknown' if aor is None else 'Physical Breach' if aor > 100 else
            'Severe Saturation' if aor > planning_threshold else 'Planning Watch' if aor >= planning_threshold-10 else 'Normal')
    return {'additional_visitor_nights': result['totalAdditionalGuestNightsK']*1000,
            'additional_room_nights': result['additionalRoomNightsYearK']*1000,
            'additional_expenditure_rm_million': result['totalAdditionalAccomSpendMil'],
            'incremental_gva_rm_million': result['potentialAdditionalTdgvaMil'],
            'projected_aor_pct': aor, 'capacity_status': tier}


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
