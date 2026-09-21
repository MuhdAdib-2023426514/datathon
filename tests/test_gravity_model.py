"""
Unit Test Suite for Sprint 4: Gravity Model & PPML Estimation.
Enforces econometric principles from:
- AGENTS.md (Section 7 Stage D, Section 8, 9)
- IMPLEMENTATION_PLAN.md (Phases 14, 15, 16, 17, 18)
- .agents/skills/tourism-corridor-scenarios/SKILL.md
- .agents/skills/tourism-econometrics-ml/SKILL.md
"""

import json
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import pytest

from src.analytics.gravity_corridor_model import (
    run_gravity_corridor_model,
    estimate_ppml_gravity,
    calc_oos_metrics,
    evaluate_distance_structural_change,
)
from src.config.paths import DUCKDB_PATH, DASHBOARD_DATA_DIR, ROOT_DIR


@pytest.fixture(scope="module")
def gravity_data():
    """Load the interstate origin-destination panel data."""
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("""
        SELECT 
            year,
            origin,
            destination,
            distance_km,
            is_cross_region,
            tourist_flow_thousands
        FROM origin_destination_panel
        WHERE is_interstate = TRUE
    """).df()
    con.close()

    df["ln_dist"] = np.log(df["distance_km"].clip(lower=40.0))
    df["cross_region_int"] = df["is_cross_region"].astype(int)
    df["year_factor"] = df["year"].astype(str)
    return df


class TestPPMLGravitySpecification:
    """Phase 14 & 15: PPML estimation, fixed effects, and target leakage elimination."""

    def test_ppml_convergence_and_negative_distance_friction(self, gravity_data):
        df = gravity_data
        model = estimate_ppml_gravity(df)

        assert model.converged, "PPML model must converge"
        assert "ln_dist" in model.params, "ln_dist must be present in model"
        assert model.params["ln_dist"] < 0, "Distance decay coefficient must be negative"
        assert model.pvalues["ln_dist"] < 0.01, "Distance decay friction must be statistically significant (p < 0.01)"
        assert model.params["cross_region_int"] < 0, "Cross-region flight penalty must be negative"

    def test_zero_target_leakage(self, gravity_data):
        df = gravity_data
        model = estimate_ppml_gravity(df)

        # Ensure destination total tourists is not used as an explanatory regressor
        regressors = list(model.params.keys())
        assert "dest_total_tourists_thousands" not in regressors, "Target leakage detected: dest_total_tourists must not be a regressor"
        assert "ln_dest_pull" not in regressors, "Target leakage detected: ln_dest_pull must not be a regressor"


class TestOOSValidationAndBaselines:
    """Phase 16: Proper out-of-sample holdout, true R², and naive baselines."""

    def test_true_oos_r2_and_metrics(self, gravity_data):
        df = gravity_data
        train = df[df["year"] < 2025].copy()
        test = df[df["year"] == 2025].copy()

        assert len(train) == 1680, f"Expected 1680 training corridor-years, got {len(train)}"
        assert len(test) == 240, f"Expected 240 holdout testing corridors, got {len(test)}"

        model = estimate_ppml_gravity(train, include_year_fe=False)
        test["pred_flow"] = model.predict(test)

        metrics = calc_oos_metrics(test["tourist_flow_thousands"].values, test["pred_flow"].values)

        assert "r2_oos" in metrics
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "rmsle" in metrics
        assert "smape" in metrics

        # True predictive R2 must exceed 0.40 on 2025 holdout
        assert metrics["r2_oos"] > 0.40, f"Expected R2_OOS > 0.40, got {metrics['r2_oos']}"
        assert metrics["mae"] > 0
        assert metrics["rmse"] > 0

    def test_baselines_comparison(self, gravity_data):
        df_sum, df_pred, df_val = run_gravity_corridor_model()

        specs = df_val["model_specification"].tolist()
        assert any("PPML" in s for s in specs), "PPML must be included in validation summary"
        assert any("Log-OLS" in s for s in specs), "Log-OLS must be included for comparison"
        assert any("Baseline 1" in s or "Lag" in s for s in specs), "Naive lag baseline must be reported"
        assert any("Baseline 2" in s or "Mean" in s for s in specs), "Historical mean baseline must be reported"


class TestStructuralChange:
    """Phase 18: Distance friction structural change test."""

    def test_distance_post_recovery_interaction(self, gravity_data):
        df = gravity_data
        result = evaluate_distance_structural_change(df)

        assert "interaction_coef" in result
        assert "std_error" in result
        assert "p_value" in result
        assert "h0_rejected_5pct" in result
        assert np.isfinite(result["interaction_coef"])
        assert np.isfinite(result["p_value"])


class TestModelMetricsSerialization:
    """Phase 17: Single model metrics JSON serialization."""

    def test_model_metrics_json_schema(self):
        metrics_path = DASHBOARD_DATA_DIR / "model_metrics.json"
        assert metrics_path.exists(), "dashboard/public/data/model_metrics.json must be generated"

        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "gravity" in data
        grav = data["gravity"]
        assert grav["model"] == "PPML"
        assert "r2_oos" in grav
        assert "mae" in grav
        assert "rmse" in grav
        assert "smape" in grav
        assert "naive_baselines" in grav
        assert "baseline_comparison_note" in grav, "Sprint B: baseline_comparison_note must explain persistence vs PPML"
        assert "inertia" in grav["baseline_comparison_note"].lower() or "persistence" in grav["baseline_comparison_note"].lower()

        # Sprint B: Dynamic panel metrics validation
        assert "panel" in data
        panel = data["panel"]
        assert "alos_elasticity" in panel
        assert "tourist_elasticity" in panel
        assert "yield_model" in panel
        assert panel["yield_model"]["r_squared"] > 0.70

        # Verify DuckDB parity
        con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        m2_row = con.execute("SELECT elasticity_coefficient FROM panel_regression_summary WHERE model_id='Model_2_TwoWay_FE_Clustered' AND independent_variable='ln(ALOS)'").fetchone()
        con.close()
        if m2_row:
            assert abs(panel["alos_elasticity"] - float(m2_row[0])) < 1e-4, "Parity mismatch between JSON panel metrics and DuckDB"
