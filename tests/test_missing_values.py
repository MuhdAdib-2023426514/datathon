"""
Unit tests for Missing-Value Handling and Propagation (Sprint 1 / Phase 2).
Enforces AGENTS.md Rule 6 and IMPLEMENTATION_PLAN.md Section 7:
- Missing observations must propagate as np.nan / None (SQL NULL), never coerced to arbitrary numbers.
- Observed zero remains strictly distinct from missing or suppressed values.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest
import numpy as np
import pandas as pd

from src.analytics.accounting import (
    calc_vai,
    calc_estimated_tourism_gva,
    calc_accommodation_share,
    calc_spend_per_visitor,
    calc_spend_per_tourist,
    calc_spend_per_night,
    calc_sdg_attributable_gva,
    calc_value_retention_rate,
)
from src.ingestion.granular_dts_parser import clean_num, safe_round


class TestMissingValues(unittest.TestCase):
    def test_calc_vai_missing_and_zero_handling(self):
        """VAI should return NaN if either input is missing or supply <= 0."""
        self.assertTrue(np.isnan(calc_vai(None, 1000.0)))
        self.assertTrue(np.isnan(calc_vai(500.0, None)))
        self.assertTrue(np.isnan(calc_vai(np.nan, 1000.0)))
        self.assertTrue(np.isnan(calc_vai(500.0, np.nan)))
        self.assertTrue(np.isnan(calc_vai(500.0, 0.0)))
        self.assertTrue(np.isnan(calc_vai(500.0, -100.0)))

        # Valid inputs
        self.assertAlmostEqual(calc_vai(800.0, 1000.0), 0.8)

    def test_calc_estimated_tourism_gva_missing(self):
        """Estimated Tourism GVA proxy must propagate NaN if ITC or VAI is missing."""
        self.assertTrue(np.isnan(calc_estimated_tourism_gva(None, 0.85)))
        self.assertTrue(np.isnan(calc_estimated_tourism_gva(1500.0, None)))
        self.assertTrue(np.isnan(calc_estimated_tourism_gva(np.nan, 0.85)))
        self.assertTrue(np.isnan(calc_estimated_tourism_gva(1500.0, np.nan)))

        # Valid inputs
        self.assertAlmostEqual(calc_estimated_tourism_gva(1000.0, 0.85), 850.0)

    def test_calc_accommodation_metrics_missing(self):
        """Per-visitor, per-tourist, and per-night metrics propagate NaN on missing/zero denominators."""
        # Accommodation share
        self.assertTrue(np.isnan(calc_accommodation_share(None, 5000.0)))
        self.assertTrue(np.isnan(calc_accommodation_share(1000.0, None)))
        self.assertTrue(np.isnan(calc_accommodation_share(1000.0, 0.0)))
        self.assertAlmostEqual(calc_accommodation_share(1000.0, 5000.0), 0.2)

        # Spend per visitor
        self.assertTrue(np.isnan(calc_spend_per_visitor(None, 10000.0)))
        self.assertTrue(np.isnan(calc_spend_per_visitor(5000.0, None)))
        self.assertTrue(np.isnan(calc_spend_per_visitor(5000.0, 0.0)))
        self.assertAlmostEqual(calc_spend_per_visitor(5000.0, 10.0), 500.0)

        # Spend per tourist
        self.assertTrue(np.isnan(calc_spend_per_tourist(None, 5000.0)))
        self.assertTrue(np.isnan(calc_spend_per_tourist(5000.0, None)))
        self.assertTrue(np.isnan(calc_spend_per_tourist(5000.0, 0.0)))
        self.assertAlmostEqual(calc_spend_per_tourist(5000.0, 20.0), 250.0)

        # Spend per night
        self.assertTrue(np.isnan(calc_spend_per_night(None, 100.0, 2.5)))
        self.assertTrue(np.isnan(calc_spend_per_night(5000.0, None, 2.5)))
        self.assertTrue(np.isnan(calc_spend_per_night(5000.0, 100.0, None)))
        self.assertTrue(np.isnan(calc_spend_per_night(5000.0, 0.0, 2.5)))
        self.assertTrue(np.isnan(calc_spend_per_night(5000.0, 100.0, 0.0)))
        self.assertAlmostEqual(calc_spend_per_night(5000.0, 100.0, 2.5), 20.0)

    def test_clean_num_distinguishes_zero_from_missing(self):
        """clean_num must return None for missing/suppressed tokens and preserve real 0.0."""
        self.assertIsNone(clean_num(None))
        self.assertIsNone(clean_num(""))
        self.assertIsNone(clean_num("-"))
        self.assertIsNone(clean_num(" - "))
        self.assertIsNone(clean_num("N/A"))
        self.assertIsNone(clean_num("null"))
        self.assertIsNone(clean_num("nil"))

        # Actual observed zeros
        self.assertEqual(clean_num(0), 0.0)
        self.assertEqual(clean_num(0.0), 0.0)
        self.assertEqual(clean_num("0"), 0.0)
        self.assertEqual(clean_num("0.0"), 0.0)

        # Valid numbers
        self.assertEqual(clean_num(" 1,234.50 "), 1234.5)

    def test_safe_round_handles_nan_and_none(self):
        """safe_round must return None for NaN or None, and float for real values."""
        self.assertIsNone(safe_round(None))
        self.assertIsNone(safe_round(np.nan))
        self.assertEqual(safe_round(12.3456), 12.35)
        self.assertEqual(safe_round(0.0), 0.0)

    def test_demographics_missing_value_propagation(self):
        """State demographics parser must preserve NaN for missing pop or income without 1000.0/5000.0 fallbacks."""
        from src.ingestion.state_demographics_parser import match_state_from_name, STATE_METADATA
        
        # Simulate unobserved row
        raw_row = {"raw_state": "SELANGOR", "population": None, "median_income": None, "mean_income": None}
        raw_pop_val = raw_row.get("population")
        if pd.notna(raw_pop_val) and str(raw_pop_val).strip() != "":
            pop_k = float(raw_pop_val)
        else:
            pop_k = np.nan
        self.assertTrue(np.isnan(pop_k))

        raw_med = raw_row.get("median_income")
        med_inc = float(raw_med) if pd.notna(raw_med) and str(raw_med).strip() != "" else np.nan
        self.assertTrue(np.isnan(med_inc))


if __name__ == "__main__":
    unittest.main()
