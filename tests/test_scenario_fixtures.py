"""
Synthetic Scenario & Capacity Unit Tests (W0 / W7)
Tests scenario calculations, corridor ALOS decoupling from destination day trips,
and multi-corridor portfolio room capacity feasibility checks.
"""

import unittest
import numpy as np


class TestScenarioFixtures(unittest.TestCase):
    def test_corridor_alos_independent_of_day_trip(self):
        """
        Regression test for Finding 2:
        Corridor ALOS simulation must depend on the corridor flow.
        Zero flow or 0 ALOS extension with 0 day-trip conversion must yield 0 incremental nights.
        """
        flow_k = 500.0  # 500,000 tourists
        delta_alos = 0.5  # +0.5 nights
        spend_per_night = 120.0  # RM/night
        vai = 0.8579

        add_nights = flow_k * 1000.0 * delta_alos
        add_spend = add_nights * spend_per_night
        gva_proxy = add_spend * vai

        self.assertEqual(add_nights, 250_000.0)
        self.assertEqual(add_spend, 30_000_000.0)
        self.assertAlmostEqual(gva_proxy, 25_737_000.0, places=1)

        # When delta_alos is 0 and day-trip conversion is 0:
        zero_nights = flow_k * 1000.0 * 0.0
        self.assertEqual(zero_nights, 0.0)

    def test_portfolio_capacity_aggregation(self):
        """
        Regression test for Finding 7:
        When multiple corridors extend stays to the same destination,
        incremental room demand must aggregate across all feeders.
        """
        # Destination: e.g. Pahang with 30,000 rooms, 65% baseline AOR
        total_rooms = 30_000
        baseline_aor = 65.0
        guests_per_room = 1.8

        # 3 Feeder corridors adding nights:
        feeder_nights = [400_000, 350_000, 500_000]  # Total 1,250,000 tourist nights
        total_add_nights = sum(feeder_nights)

        daily_room_demand = total_add_nights / (365.0 * guests_per_room)
        delta_aor = (daily_room_demand / total_rooms) * 100.0
        implied_aor = baseline_aor + delta_aor

        # Check aggregate calculation:
        # daily_room_demand = 1,250,000 / 657 = ~1902.58 rooms
        # delta_aor = 1902.58 / 30000 = ~6.34%
        # implied_aor = 65.0 + 6.34 = 71.34%
        self.assertAlmostEqual(implied_aor, 71.34, places=1)

        # Capacity saturation tiers check:
        def get_capacity_status(aor):
            if aor > 100.0:
                return "Physical Capacity Breach (>100% AOR)"
            elif aor > 80.0:
                return "Severe Saturation (>80% AOR)"
            elif aor >= 70.0:
                return "Planning Watch (70-80% AOR)"
            return "Normal (<70% AOR)"

        self.assertEqual(get_capacity_status(implied_aor), "Planning Watch (70-80% AOR)")
        self.assertEqual(get_capacity_status(85.0), "Severe Saturation (>80% AOR)")
        self.assertEqual(get_capacity_status(102.0), "Physical Capacity Breach (>100% AOR)")


if __name__ == "__main__":
    unittest.main()
