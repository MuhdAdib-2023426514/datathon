"""
Synthetic Accounting Unit Tests (W0 / W2)
Tests pure accounting definitions, VAI calculation, and fixes for the SDG Attributable GVA bug.
"""

import unittest
import numpy as np
import pandas as pd


def calc_vai(gva: float, supply: float) -> float:
    """Calculate Value-Added Intensity: VAI = GVA / Domestic Supply."""
    if supply is None or np.isnan(supply) or supply <= 0:
        return 0.0
    return gva / supply


def calc_tourism_gva_proxy(expenditure: float, vai: float) -> float:
    """Calculate Tourism-Attributable GVA Proxy = Expenditure * VAI."""
    if expenditure is None or np.isnan(expenditure) or vai is None or np.isnan(vai):
        return 0.0
    return expenditure * vai


def calc_total_sdg_attributable_gva(
    accom_spend: float,
    food_spend: float,
    shopping_spend: float,
    transport_spend: float,
    other_spend: float,
    vai_dict: dict,
) -> float:
    """
    Computes total attributable GVA across all components without operator precedence bugs.
    """
    gva_accom = (accom_spend or 0.0) * vai_dict.get("accommodation", 0.0)
    gva_food = (food_spend or 0.0) * vai_dict.get("food_beverage", 0.0)
    gva_shopping = (shopping_spend or 0.0) * vai_dict.get("shopping", 0.0)
    gva_transport = (transport_spend or 0.0) * vai_dict.get("transport", 0.0)
    gva_other = (other_spend or 0.0) * vai_dict.get("other", 0.0)
    return gva_accom + gva_food + gva_shopping + gva_transport + gva_other


class TestAccountingFixtures(unittest.TestCase):
    def setUp(self):
        self.vai = {
            "accommodation": 0.8579,
            "food_beverage": 0.4320,
            "shopping": 0.7090,
            "transport": 0.2850,
            "other": 0.5000,
        }

    def test_vai_calculation(self):
        gva = 1200.0
        supply = 1500.0
        self.assertAlmostEqual(calc_vai(gva, supply), 0.8, places=4)
        # Edge case: zero supply should not raise ZeroDivisionError
        self.assertEqual(calc_vai(100.0, 0.0), 0.0)

    def test_accommodation_gva_proxy_nonzero_when_food_present(self):
        """
        Regression test for Finding 1:
        Verify that accommodation GVA is NOT dropped when calculating GVA proxy.
        In legacy buggy code:
          gva_proxy = (
              accom * vai_accom + food_bev * vai_fb
              if 'food_beverage' in df.columns
              else food * vai_fb
          )
        which evaluated as (accom * vai_accom + food_bev * vai_fb) IF condition ELSE (food * vai_fb).
        This test verifies accommodation is strictly preserved.
        """
        accom_spend = 1945.5  # e.g., KL accommodation expenditure (RM M)
        food_spend = 2500.0
        shopping_spend = 3000.0
        transport_spend = 1200.0
        other_spend = 500.0

        total_gva = calc_total_sdg_attributable_gva(
            accom_spend, food_spend, shopping_spend, transport_spend, other_spend, self.vai
        )

        expected_accom_gva = accom_spend * self.vai["accommodation"]  # ~1669.04
        self.assertGreater(total_gva, expected_accom_gva)
        self.assertAlmostEqual(
            total_gva,
            (1945.5 * 0.8579) + (2500.0 * 0.4320) + (3000.0 * 0.7090) + (1200.0 * 0.2850) + (500.0 * 0.5000),
            places=2,
        )

    def test_accommodation_only_fixture(self):
        """A dataset with only accommodation spending should yield non-zero GVA."""
        total_gva = calc_total_sdg_attributable_gva(1000.0, 0.0, 0.0, 0.0, 0.0, self.vai)
        self.assertAlmostEqual(total_gva, 857.9, places=2)


if __name__ == "__main__":
    unittest.main()
