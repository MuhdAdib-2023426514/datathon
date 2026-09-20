"""
Unit Test Suite for Sprint 3: Econometric Panel Modeling & Robustness.
Enforces econometric principles from:
- AGENTS.md (Section 8, 9)
- IMPLEMENTATION_PLAN.md (Phases 9, 10, 11)
- .agents/skills/tourism-econometrics-ml/SKILL.md
- .agents/skills/hypothesis-testing-playbook/SKILL.md
"""

from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from statsmodels.formula.api import ols

from src.analytics.panel_econometrics import (
    run_panel_econometrics,
    run_leave_one_state_out,
    calc_influence_diagnostics,
    DUCKDB_PATH,
    ROOT_DIR,
)


@pytest.fixture(scope="module")
def panel_data():
    """Load the state panel dataset with Constant 2025 RM series and purpose shares."""
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("""
        SELECT 
            p.year,
            p.state,
            p.state_code,
            p.region,
            p.visitors_thousands,
            p.tourists_thousands,
            p.excursionists_thousands,
            p.alos_days,
            p.total_expenditure_rm_million,
            p.accommodation_expenditure_rm_million,
            p.aor_pct,
            p.foreign_guest_share_pct,
            pov.holiday_share_tourist,
            cpi."index" as cpi_index
        FROM state_panel_year p
        LEFT JOIN state_purpose_of_visit_panel pov 
            ON p.year = pov.year AND p.state = pov.state
        LEFT JOIN (
            SELECT year, "index" FROM read_csv_auto('data/processed/price_index.csv')
        ) cpi ON p.year = cpi.year
        WHERE p.accommodation_expenditure_rm_million > 0 
          AND p.alos_days > 0 
          AND p.tourists_thousands > 0
    """).df()
    con.close()

    # Base year 2025 CPI index
    cpi_2025 = df.loc[df["year"] == 2025, "cpi_index"].iloc[0]
    df["deflator"] = cpi_2025 / df["cpi_index"]

    # Real accommodation spend & log
    df["real_accom_spend"] = df["accommodation_expenditure_rm_million"] * df["deflator"]
    df["ln_real_accom_spend"] = np.log(df["real_accom_spend"])
    df["ln_accom_spend"] = np.log(df["accommodation_expenditure_rm_million"])

    # Real accommodation yield per tourist night & log
    df["accom_yield"] = (df["accommodation_expenditure_rm_million"] * 1000.0) / (df["tourists_thousands"] * df["alos_days"])
    df["real_accom_yield"] = df["accom_yield"] * df["deflator"]
    df["ln_real_accom_yield"] = np.log(df["real_accom_yield"])
    df["ln_accom_yield"] = np.log(df["accom_yield"])

    # Regressors
    df["ln_alos"] = np.log(df["alos_days"])
    df["ln_tourists"] = np.log(df["tourists_thousands"])
    df["ln_aor"] = np.log(df["aor_pct"].clip(lower=1.0))
    df["foreign_share"] = df["foreign_guest_share_pct"].fillna(0.0)
    df["holiday_share"] = df["holiday_share_tourist"].fillna(df["holiday_share_tourist"].median())

    return df


class TestTwoWayFixedEffects:
    """Phase 9.1 & 9.2: Two-way fixed effects and state-clustered SEs."""

    def test_two_way_fe_absorbs_year_shocks(self, panel_data):
        df = panel_data
        # Estimate two-way FE with state-clustered SEs
        m2 = ols("ln_real_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["state"]}
        )

        assert m2.rsquared > 0.95, "Two-way FE model should explain over 95% of variation"
        assert "C(year)[T.2020]" in m2.params, "Year dummies must be present in model"
        assert "C(state)[T.Kedah]" in m2.params, "State dummies must be present in model"

        # Check that tourist volume elasticity is positive and statistically significant
        tour_coef = m2.params["ln_tourists"]
        tour_pval = m2.pvalues["ln_tourists"]
        assert tour_coef > 0.4, f"Tourist elasticity {tour_coef} should be strongly positive"
        assert tour_pval < 0.05, f"Tourist elasticity p-value {tour_pval} should be significant"

    def test_state_clustered_standard_errors(self, panel_data):
        df = panel_data
        m_clust = ols("ln_real_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["state"]}
        )

        # Clustered SEs should reflect within-state correlation across time
        assert m_clust.bse["ln_alos"] > 0
        assert m_clust.bse["ln_tourists"] > 0
        assert np.isfinite(m_clust.bse["ln_alos"])


class TestYieldFocusedModel:
    """Phase 9.3: Yield-focused two-way FE model."""

    def test_accommodation_yield_model_estimation(self, panel_data):
        df = panel_data
        m_yield = ols(
            "ln_real_accom_yield ~ ln_aor + foreign_share + holiday_share + C(state) + C(year)",
            data=df
        ).fit(cov_type="cluster", cov_kwds={"groups": df["state"]})

        assert m_yield.nobs == 126, f"Expected 126 observations, got {m_yield.nobs}"
        assert m_yield.rsquared > 0.75, "Yield model should explain >75% of panel variation"

        # ln(AOR) is expected to have a positive association with yield (pricing power under tighter capacity)
        aor_coef = m_yield.params["ln_aor"]
        assert aor_coef > 0, f"AOR elasticity on accommodation yield should be positive, got {aor_coef}"


class TestLeaveOneStateOut:
    """Phase 11: Leave-one-state-out stability analysis."""

    def test_leave_one_state_out_completeness(self, panel_data):
        df = panel_data
        formula = "ln_real_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)"
        df_loo = run_leave_one_state_out(df, formula, key_vars=["ln_alos", "ln_tourists"])

        # 16 states left out
        assert len(df_loo["omitted_state"].unique()) == 16
        assert len(df_loo) == 16 * 2  # 2 key variables evaluated

        # Check tourist elasticity stability across all 16 iterations
        tour_coefs = df_loo[df_loo["variable"] == "ln_tourists"]["coefficient"]
        assert (tour_coefs > 0).all(), "Tourist elasticity must remain positive across all 16 leave-one-out iterations"


class TestInfluenceDiagnostics:
    """Phase 11: Outlier and influence diagnostics."""

    def test_influence_diagnostics_calculation(self, panel_data):
        df = panel_data
        model = ols("ln_real_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)", data=df).fit()
        df_diag = calc_influence_diagnostics(model, df)

        assert "cooks_distance" in df_diag.columns
        assert "leverage" in df_diag.columns
        assert "studentized_residual" in df_diag.columns
        assert (df_diag["cooks_distance"] >= 0).all()
        assert (df_diag["leverage"] >= 0).all()
        assert len(df_diag) == len(df)


class TestCausalHumilityAndLanguage:
    """Phase 10: Prohibition of 'root cause' and enforcement of causal humility."""

    def test_no_root_cause_in_panel_summary(self):
        df_sum, df_traj, _, _ = run_panel_econometrics()

        # Check summary interpretations
        for interp in df_sum["interpretation"]:
            assert "root cause" not in interp.lower()
            assert "proves" not in interp.lower()
            assert "guarantees" not in interp.lower()

        # Check that caveated language is present
        assert any("small-cluster" in str(row.get("small_cluster_caveat", "")).lower() or
                   "cluster" in str(row.get("covariance_type", "")).lower()
                   for _, row in df_sum.iterrows())
