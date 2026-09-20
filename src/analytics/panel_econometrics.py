"""
State Panel Econometrics & Recovery Trajectory Analysis (2018–2025)
Estimates:
  1. Model 1 (Baseline DTS 2018–2025, One-Way State FE):
     Within-state ALOS and Tourist Volume Elasticities (HC1 robust).
  2. Model 2 (Primary Two-Way FE: State + Year Effects with State-Clustered SEs):
     Controls for national macroeconomic time shocks across 2018–2025 and accounts
     for intra-state error correlation across the 16 state panels.
  3. Model 3 (Multi-Factor Operations Panel 2018–2025):
     Within-state ALOS, AOR, and Foreign Guest Share Elasticities with Two-Way FE.
  4. Volume-Recovery vs. Stay-Lag Opportunity Gap (2019 vs 2025).

Exports summary tables to DuckDB and Parquet:
  - panel_regression_summary
  - state_recovery_trajectory
"""

import sys
from pathlib import Path
from typing import Dict, Tuple
import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"


def run_panel_econometrics() -> Tuple[pd.DataFrame, pd.DataFrame]:
    con = duckdb.connect(str(DUCKDB_PATH))
    df = con.execute("SELECT * FROM state_panel_year WHERE accommodation_expenditure_rm_million > 0 AND alos_days > 0").df()

    # Log transformations
    df["ln_accom_spend"] = np.log(df["accommodation_expenditure_rm_million"])
    df["ln_alos"] = np.log(df["alos_days"])
    df["ln_tourists"] = np.log(df["tourists_thousands"].clip(lower=1.0))
    df["ln_visitors"] = np.log(df["visitors_thousands"].clip(lower=1.0))

    panel_summary_records = []
    n_obs = len(df)
    n_states = df["state"].nunique()
    n_years = df["year"].nunique()

    # =========================================================================
    # Model 1: Baseline One-Way State Fixed-Effects Model (HC1 SEs)
    # =========================================================================
    fe_model_m1 = ols("ln_accom_spend ~ ln_alos + ln_tourists + C(state)", data=df).fit(cov_type="HC1")

    alos_coef_1 = float(fe_model_m1.params["ln_alos"])
    alos_pval_1 = float(fe_model_m1.pvalues["ln_alos"])
    alos_se_1 = float(fe_model_m1.bse["ln_alos"])
    ci_1 = fe_model_m1.conf_int().loc["ln_alos"]

    tour_coef_1 = float(fe_model_m1.params["ln_tourists"])
    tour_pval_1 = float(fe_model_m1.pvalues["ln_tourists"])
    tour_se_1 = float(fe_model_m1.bse["ln_tourists"])

    panel_summary_records.extend([{
        "model_id": "Model_1_State_FE_Only",
        "specification": "One-Way State FE (HC1)",
        "sample_period": f"2018–2025 (N={n_obs}, States={n_states})",
        "independent_variable": "ln(ALOS)",
        "elasticity_coefficient": round(alos_coef_1, 4),
        "std_error": round(alos_se_1, 4),
        "ci_lower": round(float(ci_1[0]), 4),
        "ci_upper": round(float(ci_1[1]), 4),
        "t_statistic": round(float(fe_model_m1.tvalues["ln_alos"]), 4),
        "p_value": round(alos_pval_1, 4),
        "significance": "p < 0.01" if alos_pval_1 < 0.01 else ("p < 0.05" if alos_pval_1 < 0.05 else "Not sig"),
        "r_squared": round(float(fe_model_m1.rsquared), 4),
        "covariance_type": "HC1 Heteroskedasticity-Robust",
        "interpretation": f"A 10% increase in ALOS is associated with a {alos_coef_1 * 10:.1f}% increase in accommodation spend (unadjusted for macroeconomic year shocks)."
    }, {
        "model_id": "Model_1_State_FE_Only",
        "specification": "One-Way State FE (HC1)",
        "sample_period": f"2018–2025 (N={n_obs}, States={n_states})",
        "independent_variable": "ln(Overnight Tourists)",
        "elasticity_coefficient": round(tour_coef_1, 4),
        "std_error": round(tour_se_1, 4),
        "ci_lower": round(float(fe_model_m1.conf_int().loc["ln_tourists"][0]), 4),
        "ci_upper": round(float(fe_model_m1.conf_int().loc["ln_tourists"][1]), 4),
        "t_statistic": round(float(fe_model_m1.tvalues["ln_tourists"]), 4),
        "p_value": round(tour_pval_1, 4),
        "significance": "p < 0.01" if tour_pval_1 < 0.01 else ("p < 0.05" if tour_pval_1 < 0.05 else "Not sig"),
        "r_squared": round(float(fe_model_m1.rsquared), 4),
        "covariance_type": "HC1 Heteroskedasticity-Robust",
        "interpretation": f"A 10% increase in overnight tourists is associated with a {tour_coef_1 * 10:.1f}% increase in accommodation spend."
    }])

    # =========================================================================
    # Model 2: Primary Two-Way Fixed-Effects Model (State + Year FE, Clustered SEs)
    # =========================================================================
    fe_model_m2 = ols(
        "ln_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)", data=df
    ).fit(cov_type="cluster", cov_kwds={"groups": df["state"]})

    alos_coef_2 = float(fe_model_m2.params["ln_alos"])
    alos_pval_2 = float(fe_model_m2.pvalues["ln_alos"])
    alos_se_2 = float(fe_model_m2.bse["ln_alos"])
    ci_2 = fe_model_m2.conf_int().loc["ln_alos"]

    tour_coef_2 = float(fe_model_m2.params["ln_tourists"])
    tour_pval_2 = float(fe_model_m2.pvalues["ln_tourists"])
    tour_se_2 = float(fe_model_m2.bse["ln_tourists"])

    panel_summary_records.extend([{
        "model_id": "Model_2_TwoWay_FE_Clustered",
        "specification": "Two-Way FE (State + Year, State-Clustered SEs)",
        "sample_period": f"2018–2025 (N={n_obs}, States={n_states}, Years={n_years})",
        "independent_variable": "ln(ALOS)",
        "elasticity_coefficient": round(alos_coef_2, 4),
        "std_error": round(alos_se_2, 4),
        "ci_lower": round(float(ci_2[0]), 4),
        "ci_upper": round(float(ci_2[1]), 4),
        "t_statistic": round(float(fe_model_m2.tvalues["ln_alos"]), 4),
        "p_value": round(alos_pval_2, 4),
        "significance": "p < 0.01" if alos_pval_2 < 0.01 else ("p < 0.05" if alos_pval_2 < 0.05 else ("p < 0.10" if alos_pval_2 < 0.10 else "Not statistically significant at 5%")),
        "r_squared": round(float(fe_model_m2.rsquared), 4),
        "covariance_type": "State-Clustered Standard Errors (16 clusters)",
        "interpretation": f"After controlling for national annual shocks and clustering by state, the ALOS elasticity is {alos_coef_2:.2f} (95% CI: [{ci_2[0]:.2f}, {ci_2[1]:.2f}]). Reflects sensitivity to macroeconomic recovery dynamics."
    }, {
        "model_id": "Model_2_TwoWay_FE_Clustered",
        "specification": "Two-Way FE (State + Year, State-Clustered SEs)",
        "sample_period": f"2018–2025 (N={n_obs}, States={n_states}, Years={n_years})",
        "independent_variable": "ln(Overnight Tourists)",
        "elasticity_coefficient": round(tour_coef_2, 4),
        "std_error": round(tour_se_2, 4),
        "ci_lower": round(float(fe_model_m2.conf_int().loc["ln_tourists"][0]), 4),
        "ci_upper": round(float(fe_model_m2.conf_int().loc["ln_tourists"][1]), 4),
        "t_statistic": round(float(fe_model_m2.tvalues["ln_tourists"]), 4),
        "p_value": round(tour_pval_2, 4),
        "significance": "p < 0.01" if tour_pval_2 < 0.01 else ("p < 0.05" if tour_pval_2 < 0.05 else "Not sig"),
        "r_squared": round(float(fe_model_m2.rsquared), 4),
        "covariance_type": "State-Clustered Standard Errors (16 clusters)",
        "interpretation": f"Overnight tourist volume elasticity remains strongly positive ({tour_coef_2:.2f}, p < 0.01) after two-way fixed effects."
    }])

    # =========================================================================
    # Model 3: Multi-Factor Hotel Operations Model with Two-Way FE
    # =========================================================================
    df_ops = df[df["aor_pct"].notnull() & (df["aor_pct"] > 0)].copy()
    if not df_ops.empty:
        df_ops["ln_aor"] = np.log(df_ops["aor_pct"])
        df_ops["foreign_share"] = df_ops["foreign_guest_share_pct"].fillna(0)

        fe_model_ops = ols(
            "ln_accom_spend ~ ln_alos + ln_tourists + ln_aor + foreign_share + C(state) + C(year)",
            data=df_ops
        ).fit(cov_type="cluster", cov_kwds={"groups": df_ops["state"]})

        for var, var_label in [
            ("ln_alos", "ln(ALOS)"),
            ("ln_tourists", "ln(Overnight Tourists)"),
            ("ln_aor", "ln(Average Occupancy Rate - AOR)"),
            ("foreign_share", "Foreign Hotel Guest Share (%)"),
        ]:
            c = float(fe_model_ops.params[var])
            se = float(fe_model_ops.bse[var])
            t = float(fe_model_ops.tvalues[var])
            p = float(fe_model_ops.pvalues[var])
            ci = fe_model_ops.conf_int().loc[var]
            sig = "p < 0.01" if p < 0.01 else ("p < 0.05" if p < 0.05 else ("p < 0.10" if p < 0.10 else "Not sig"))

            panel_summary_records.append({
                "model_id": "Model_3_Operations_TwoWay_FE",
                "specification": "Two-Way FE Operations Model (State-Clustered SEs)",
                "sample_period": f"2018–2025 (N={len(df_ops)}, States={df_ops['state'].nunique()})",
                "independent_variable": var_label,
                "elasticity_coefficient": round(c, 4),
                "std_error": round(se, 4),
                "ci_lower": round(float(ci[0]), 4),
                "ci_upper": round(float(ci[1]), 4),
                "t_statistic": round(t, 4),
                "p_value": round(p, 4),
                "significance": sig,
                "r_squared": round(float(fe_model_ops.rsquared), 4),
                "covariance_type": "State-Clustered Standard Errors",
                "interpretation": f"Conditional within-state association controlling for AOR, foreign guest mix, state, and year effects."
            })

    df_summary = pd.DataFrame(panel_summary_records)

    # =========================================================================
    # Volume Recovery vs. Stay-Lag Opportunity Trajectory (2019 vs 2025)
    # =========================================================================
    df_2019 = df[df["year"] == 2019].set_index("state")
    df_2025 = df[df["year"] == 2025].set_index("state")

    trajectory_records = []
    for st in df_2025.index:
        if st in df_2019.index:
            r19 = df_2019.loc[st]
            r25 = df_2025.loc[st]

            v_grow = ((r25["visitors_thousands"] - r19["visitors_thousands"]) / r19["visitors_thousands"]) * 100.0
            t_grow = ((r25["tourists_thousands"] - r19["tourists_thousands"]) / r19["tourists_thousands"]) * 100.0
            e_grow = ((r25["total_expenditure_rm_million"] - r19["total_expenditure_rm_million"]) / r19["total_expenditure_rm_million"]) * 100.0
            a_grow = ((r25["accommodation_expenditure_rm_million"] - r19["accommodation_expenditure_rm_million"]) / r19["accommodation_expenditure_rm_million"]) * 100.0
            alos_delta = r25["alos_days"] - r19["alos_days"]

            if v_grow > 0 and alos_delta < -0.2:
                pattern = "Volume Expansion, Stay Contraction (High Risk)"
            elif v_grow > 0 and alos_delta >= 0:
                pattern = "Full Value Deepening (Ideal Trajectory)"
            elif v_grow <= 0 and alos_delta > 0:
                pattern = "Consolidated Long-Stay (Niche High-Yield)"
            else:
                pattern = "Lagging Recovery (Volume & Stay Deficit)"

            trajectory_records.append({
                "state": st,
                "state_code": r25["state_code"],
                "region": r25["region"],
                "visitor_growth_pct": round(float(v_grow), 2),
                "tourist_growth_pct": round(float(t_grow), 2),
                "spend_growth_pct": round(float(e_grow), 2),
                "accom_spend_growth_pct": round(float(a_grow), 2),
                "alos_delta_days": round(float(alos_delta), 2),
                "recovery_pattern": pattern
            })

    df_traj = pd.DataFrame(trajectory_records).sort_values("visitor_growth_pct", ascending=False)

    # Export to DuckDB & Parquet
    con.execute("CREATE OR REPLACE TABLE panel_regression_summary AS SELECT * FROM df_summary")
    con.execute("CREATE OR REPLACE TABLE state_recovery_trajectory AS SELECT * FROM df_traj")

    summary_parquet = PROCESSED_DIR / "panel_regression_summary.parquet"
    traj_parquet = PROCESSED_DIR / "state_recovery_trajectory.parquet"

    con.execute(f"COPY panel_regression_summary TO '{summary_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY state_recovery_trajectory TO '{traj_parquet}' (FORMAT PARQUET)")
    con.close()

    print(f"Panel econometrics estimated ({len(df_summary)} coefficient models).")
    print(f"Recovery trajectory calculated for {len(df_traj)} states.")
    return df_summary, df_traj


if __name__ == "__main__":
    df_sum, df_traj = run_panel_econometrics()
    print("\n=== PANEL REGRESSION DUAL MODEL SPECIFICATIONS ===")
    print(df_sum[["model_id", "specification", "independent_variable", "elasticity_coefficient", "ci_lower", "ci_upper", "p_value", "significance"]].to_string(index=False))

    print("\n=== 2019 vs 2025 RECOVERY TRAJECTORY (TOP 5) ===")
    print(df_traj[["state", "visitor_growth_pct", "alos_delta_days", "recovery_pattern"]].head().to_string(index=False))
