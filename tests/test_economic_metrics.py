"""
Unit Test Suite for Sprint 2: Economic Metrics & Accounting Standards.
Enforces non-negotiable accounting rules and formulas from:
- AGENTS.md (Section 3, 7, 8, 9, 11)
- IMPLEMENTATION_PLAN.md (Phases 5, 6, 6.1, 7, 8, 13)
- .agents/skills/tsa-tourism-economics/SKILL.md
- .agents/skills/sustainable-tourism-sdg-metrics/SKILL.md
"""

import math
import numpy as np
import pandas as pd
import pytest

from src.analytics.accounting import (
    calc_real_value,
    calc_visitor_days,
    calc_tey,
    calc_accommodation_yield,
    calc_tourism_gva_intensity,
    calc_estimated_tourism_gva_state,
    calc_mapping_coverage,
    calc_tvay,
)


class TestPriceIndexAndRealRM:
    """Phase 5: Real RM inflation adjustment tests."""

    @pytest.fixture
    def cpi_map(self):
        # Official DOSM CPI series 2010=100
        return {
            2015: 112.5,
            2018: 120.1,
            2019: 120.9,
            2020: 120.0,
            2024: 132.8,
            2025: 134.6,
        }

    def test_2025_nominal_equals_real(self, cpi_map):
        # For base year 2025, RealValue == NominalValue
        nom = 1500.0
        real = calc_real_value(nom, 2025, cpi_map, base_year=2025)
        assert pytest.approx(real, rel=1e-5) == 1500.0

    def test_2015_deflation_increases_nominal_spend(self, cpi_map):
        # In 2015, CPI was 112.5 vs 134.6 in 2025. Constant 2025 RM must be higher than nominal.
        nom = 1000.0
        expected_real = 1000.0 * (134.6 / 112.5)  # ~ 1196.44
        real = calc_real_value(nom, 2015, cpi_map, base_year=2025)
        assert pytest.approx(real, rel=1e-4) == expected_real
        assert real > nom

    def test_missing_and_invalid_inputs_propagate_nan(self, cpi_map):
        assert np.isnan(calc_real_value(None, 2020, cpi_map))
        assert np.isnan(calc_real_value(np.nan, 2020, cpi_map))
        assert np.isnan(calc_real_value(100.0, 1999, cpi_map))  # missing year
        assert np.isnan(calc_real_value(100.0, 2020, {}))  # empty cpi map


class TestVisitorDaysAndYields:
    """Phase 7: Visitor-Days, TEY, Accommodation Yield, and TVAY tests."""

    def test_calc_visitor_days(self):
        # 100k tourists * 2.5 days ALOS + 50k excursionists = 250k + 50k = 300k visitor days
        days = calc_visitor_days(tourists_count=100.0, alos_days=2.5, excursionists_count=50.0)
        assert pytest.approx(days) == 300.0

    def test_calc_visitor_days_missing_inputs(self):
        assert np.isnan(calc_visitor_days(None, 2.5, 50.0))
        assert np.isnan(calc_visitor_days(100.0, None, 50.0))
        assert np.isnan(calc_visitor_days(100.0, 2.5, None))
        assert np.isnan(calc_visitor_days(100.0, -1.0, 50.0))

    def test_calc_tey(self):
        # Total Expenditure RM 60M / 300k visitor days = RM 200 / day
        # In consistent currency units: e.g. RM 60,000,000 / 300,000 days = 200.0
        tey = calc_tey(total_expenditure_rm=60_000_000.0, visitor_days=300_000.0)
        assert pytest.approx(tey) == 200.0

    def test_calc_tey_non_positive_days(self):
        assert np.isnan(calc_tey(60_000_000.0, 0.0))
        assert np.isnan(calc_tey(60_000_000.0, -100.0))
        assert np.isnan(calc_tey(None, 300_000.0))

    def test_calc_accommodation_yield(self):
        # Accommodation Spend RM 20M / (100k tourists * 2.5 days = 250k nights) = RM 80 / night
        accom_yield = calc_accommodation_yield(
            accommodation_expenditure_rm=20_000_000.0,
            tourists_count=100_000.0,
            alos_days=2.5,
        )
        assert pytest.approx(accom_yield) == 80.0

    def test_calc_accommodation_yield_invalid(self):
        assert np.isnan(calc_accommodation_yield(20_000_000.0, 0, 2.5))
        assert np.isnan(calc_accommodation_yield(20_000_000.0, 100_000.0, 0))
        assert np.isnan(calc_accommodation_yield(None, 100_000.0, 2.5))


class TestTourismGVAIntensityAndNoArbitraryFallback:
    """Phase 6 & 6.1: GVA Intensity, Mapping Coverage, and Zero Arbitrary 0.50 Fallback."""

    @pytest.fixture
    def empirical_vai(self):
        return {
            "accommodation": 0.8579,
            "food_beverage": 0.4318,
            "shopping": 0.7088,
            "transport": 0.1627,
        }

    def test_no_arbitrary_050_fallback(self, empirical_vai):
        """
        Phase 6.1 requirement:
        Remove 'other': 0.50 as a default for unmapped categories.
        Do not assume VAI for unknown expenditure.
        Only mapped categories contribute to Estimated Tourism GVA.
        """
        # Mapped categories:
        # accom = 100, food = 100, shop = 100, trans = 100
        # other (unmapped) = 100
        gva, mapped_exp = calc_estimated_tourism_gva_state(
            expenditure_by_category={
                "accommodation": 100.0,
                "food_beverage": 100.0,
                "shopping": 100.0,
                "transport": 100.0,
                "other": 100.0,
            },
            vai_map=empirical_vai,
        )
        # Expected GVA = 100*0.8579 + 100*0.4318 + 100*0.7088 + 100*0.1627 = 216.12
        # 'other' MUST NOT be multiplied by 0.50!
        expected_gva = 100 * (0.8579 + 0.4318 + 0.7088 + 0.1627)
        assert pytest.approx(gva, rel=1e-4) == expected_gva
        assert pytest.approx(mapped_exp, rel=1e-4) == 400.0

    def test_mapping_coverage(self):
        # Mapped = 400M, Total = 500M -> Coverage = 80.0%
        coverage = calc_mapping_coverage(mapped_expenditure=400.0, total_expenditure=500.0)
        assert pytest.approx(coverage) == 80.0

        # Total is 0 or NaN -> NaN
        assert np.isnan(calc_mapping_coverage(400.0, 0.0))
        assert np.isnan(calc_mapping_coverage(None, 500.0))

    def test_tourism_gva_intensity(self, empirical_vai):
        """
        Formula:
        TourismGVAIntensity = sum_k (Exp_k * VAI_k) / sum_k (MappedExp_k) * 100%
        """
        # GVA = 216.12, Mapped = 400.0 -> Intensity = 54.03%
        gva, mapped_exp = calc_estimated_tourism_gva_state(
            expenditure_by_category={
                "accommodation": 100.0,
                "food_beverage": 100.0,
                "shopping": 100.0,
                "transport": 100.0,
            },
            vai_map=empirical_vai,
        )
        intensity = calc_tourism_gva_intensity(estimated_gva=gva, mapped_expenditure=mapped_exp)
        expected_intensity = (216.12 / 400.0) * 100.0
        assert pytest.approx(intensity, rel=1e-4) == expected_intensity

    def test_calc_tvay(self):
        # Estimated GVA RM 30M / 300k visitor days = RM 100 / visitor-day
        tvay = calc_tvay(estimated_tourism_gva_rm=30_000_000.0, visitor_days=300_000.0)
        assert pytest.approx(tvay) == 100.0


class TestStateTypologyQuadrants:
    """Phase 8: Typology based on ALOS vs TVAY/TEY, not spend-per-tourist."""

    def test_quadrant_labels(self):
        # Test that helper classifies correctly into 4 required quadrants:
        # 'Short Stay / Low Yield', 'Short Stay / High Yield', 'Long Stay / Low Yield', 'Long Stay / High Yield'
        from src.analytics.accounting import classify_state_yield_typology

        assert classify_state_yield_typology(alos=2.0, yield_val=80.0, alos_median=2.5, yield_median=120.0) == "Short Stay / Low Yield"
        assert classify_state_yield_typology(alos=2.0, yield_val=150.0, alos_median=2.5, yield_median=120.0) == "Short Stay / High Yield"
        assert classify_state_yield_typology(alos=3.0, yield_val=80.0, alos_median=2.5, yield_median=120.0) == "Long Stay / Low Yield"
        assert classify_state_yield_typology(alos=3.0, yield_val=150.0, alos_median=2.5, yield_median=120.0) == "Long Stay / High Yield"
