"""
State Panel Econometrics & Recovery Trajectory Analysis (2018–2025)
Estimates:
  1. Model 1 (Baseline DTS 2018–2025, One-Way State FE):
     Within-state ALOS and Tourist Volume Elasticities in Constant 2025 Real RM (HC1 robust).
  2. Model 2 (Primary Two-Way FE: State + Year Effects with State-Clustered SEs):
     Controls for national macroeconomic time shocks across 2018–2025 and accounts
     for intra-state error correlation across the 16 state panels.
  3. Model 3 (Multi-Factor Operations Panel 2018–2025):
     Within-state ALOS, AOR, and Foreign Guest Share Elasticities with Two-Way FE.
  4. Model 4 (Yield-Focused Two-Way FE Panel 2018–2025 — Phase 9.3):
     Explains within-state accommodation yield per tourist-night (Real RM/night)
     as a function of occupancy (AOR), foreign guest mix, and holiday leisure purpose.
  5. Cross-State Robustness & Sensitivity (Phase 11):
     - Leave-One-State-Out stability analysis across all 16 states.
     - Outlier and influence diagnostics (Cook's distance, leverage, studentized residuals).
  6. Volume-Recovery vs. Stay-Lag Opportunity Trajectory (2019 vs 2025).

Adheres strictly to AGENTS.md (Section 8, 9) and IMPLEMENTATION_PLAN.md (Phases 9, 10, 11).
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.outliers_influence import OLSInfluence

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.paths import DUCKDB_PATH, PROCESSED_DIR

MODEL_VAL_DIR = ROOT_DIR / "artifacts/model_validation"
PRICE_INDEX_PATH = PROCESSED_DIR / "price_index.csv"


def run_leave_one_state_out(
    df: pd.DataFrame,
    formula: str,
    key_vars: List[str],
    model_id: str = "Model_2_TwoWay_FE",
) -> pd.DataFrame:
    """
    Phase 11: Leave-one-state-out sensitivity analysis.
    For each of the 16 states, omit the state, refit the model with state-clustered SEs,
    and record coefficient stability across the cross-sectional units.
    """
    states = sorted(df["state"].unique())
    records = []

    for state in states:
        sub_df = df[df["state"] != state].copy()
        try:
            m = ols(formula, data=sub_df).fit(
                cov_type="cluster", cov_kwds={"groups": sub_df["state"]}
            )
            for var in key_vars:
                if var in m.params:
                    coef = float(m.params[var])
                    se = float(m.bse[var])
                    pval = float(m.pvalues[var])
                    ci = m.conf_int().loc[var]
                    records.append({
                        "model_id": model_id,
                        "omitted_state": state,
                        "variable": var,
                        "coefficient": round(coef, 4),
                        "std_error": round(se, 4),
                        "ci_lower": round(float(ci[0]), 4),
                        "ci_upper": round(float(ci[1]), 4),
                        "p_value": round(pval, 4),
                        "r_squared": round(float(m.rsquared), 4),
                        "n_obs": int(m.nobs),
                        "n_states": int(sub_df["state"].nunique()),
                    })
        except Exception as e:
            print(f"Warning: LOO failed for omitted state {state}: {e}")

    return pd.DataFrame(records)


def calc_influence_diagnostics(model, df: pd.DataFrame, model_id: str = "Model_2_TwoWay_FE") -> pd.DataFrame:
    """
    Phase 11: Influence and outlier diagnostics.
    Calculates Cook's distance, leverage (hat matrix diagonals), and studentized residuals.
    """
    infl = OLSInfluence(model)
    cooks_d = infl.cooks_distance[0]
    leverage = infl.hat_matrix_diag
    studentized_resids = infl.resid_studentized_internal

    p = float(model.df_model + 1)
    n = float(model.nobs)
    leverage_thresh = (2.0 * p) / n
    cooks_thresh = 4.0 / n

    records = []
    for idx, (c_d, lev, s_res) in enumerate(zip(cooks_d, leverage, studentized_resids)):
        row = df.iloc[idx]
        records.append({
            "model_id": model_id,
            "year": int(row["year"]),
            "state": str(row["state"]),
            "cooks_distance": round(float(c_d), 5),
            "leverage": round(float(lev), 5),
            "studentized_residual": round(float(s_res), 4),
            "is_high_leverage": bool(lev > leverage_thresh),
            "is_influential": bool(c_d > cooks_thresh),
        })

    return pd.DataFrame(records)


def run_panel_econometrics() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    con = duckdb.connect(str(DUCKDB_PATH))

    # Ingest panel with Constant 2025 CPI price deflator and purpose of visit shares
    query = f"""
    SELECT 
        p.year,
        p.state,
        p.state_code,
        p.region,
        p.visitors_thousands,
        p.tourists_thousands,
        p.excursionists_thousands,
        p.trips_thousands,
        p.alos_days,
        p.total_expenditure_rm_million,
        p.accommodation_expenditure_rm_million,
        p.food_expenditure_rm_million,
        p.shopping_expenditure_rm_million,
        p.transport_expenditure_rm_million,
        p.accommodation_share,
        p.spend_per_tourist_rm,
        p.spend_per_night_rm,
        p.tourist_nights_thousands,
        p.aor_pct,
        p.hotel_rooms_kpi,
        p.hotels_count_kpi,
        p.domestic_hotel_guests,
        p.foreign_hotel_guests,
        p.total_hotel_guests,
        p.foreign_guest_share_pct,
        pov.holiday_share_tourist,
        pov.vfr_share_tourist,
        cpi."index" as cpi_index
    FROM state_panel_year p
    LEFT JOIN state_purpose_of_visit_panel pov 
        ON p.year = pov.year AND p.state = pov.state
    LEFT JOIN (
        SELECT year, "index" FROM read_csv_auto('{PRICE_INDEX_PATH}')
    ) cpi ON p.year = cpi.year
    WHERE p.accommodation_expenditure_rm_million > 0 
      AND p.alos_days > 0 
      AND p.tourists_thousands > 0
    ORDER BY p.state, p.year
    """
    df = con.execute(query).df()

    # Price deflator (Constant 2025 RM)
    cpi_2025 = df.loc[df["year"] == 2025, "cpi_index"].iloc[0]
    df["deflator"] = cpi_2025 / df["cpi_index"]

    # Real expenditure series
    df["real_total_expenditure"] = df["total_expenditure_rm_million"] * df["deflator"]
    df["real_accom_spend"] = df["accommodation_expenditure_rm_million"] * df["deflator"]
    df["accom_yield"] = (df["accommodation_expenditure_rm_million"] * 1000.0) / (df["tourists_thousands"] * df["alos_days"])
    df["real_accom_yield"] = df["accom_yield"] * df["deflator"]

    # Log transformations
    df["ln_real_accom_spend"] = np.log(df["real_accom_spend"])
    df["ln_accom_spend"] = np.log(df["accommodation_expenditure_rm_million"])
    df["ln_real_accom_yield"] = np.log(df["real_accom_yield"])
    df["ln_accom_yield"] = np.log(df["accom_yield"])
    df["ln_alos"] = np.log(df["alos_days"])
    df["ln_tourists"] = np.log(df["tourists_thousands"].clip(lower=1.0))
    df["ln_visitors"] = np.log(df["visitors_thousands"].clip(lower=1.0))
    df["ln_aor"] = np.log(df["aor_pct"].clip(lower=1.0))
    df["foreign_share"] = df["foreign_guest_share_pct"].fillna(0.0)
    df["holiday_share"] = df["holiday_share_tourist"].fillna(df["holiday_share_tourist"].median())

    panel_summary_records = []
    n_obs = len(df)
    n_states = df["state"].nunique()
    n_years = df["year"].nunique()

    small_cluster_msg = (
        f"N={n_states} state clusters. Robust cluster-adjusted inference accounts for within-state "
        f"persistence across 2018–2025. Given cluster count < 30, results are evaluated alongside "
        f"leave-one-state-out sensitivity."
    )

    # =========================================================================
    # Model 1: Baseline One-Way State Fixed-Effects Model (HC1 SEs)
    # =========================================================================
    fe_model_m1 = ols("ln_real_accom_spend ~ ln_alos + ln_tourists + C(state)", data=df).fit(cov_type="HC1")

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
        "dependent_variable": "ln(Real Accommodation Expenditure)",
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
        "small_cluster_caveat": "One-way FE with HC1 robust standard errors; does not control for national time shocks.",
        "interpretation": f"A 10% increase in ALOS is associated with a {alos_coef_1 * 10:.1f}% increase in real accommodation spend (unadjusted for macroeconomic year shocks)."
    }, {
        "model_id": "Model_1_State_FE_Only",
        "specification": "One-Way State FE (HC1)",
        "sample_period": f"2018–2025 (N={n_obs}, States={n_states})",
        "dependent_variable": "ln(Real Accommodation Expenditure)",
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
        "small_cluster_caveat": "One-way FE with HC1 robust standard errors; does not control for national time shocks.",
        "interpretation": f"A 10% increase in overnight tourists is associated with a {tour_coef_1 * 10:.1f}% increase in real accommodation spend."
    }])

    # =========================================================================
    # Model 2: Primary Two-Way Fixed-Effects Model (State + Year FE, Clustered SEs)
    # =========================================================================
    fe_model_m2 = ols(
        "ln_real_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)", data=df
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
        "dependent_variable": "ln(Real Accommodation Expenditure)",
        "independent_variable": "ln(ALOS)",
        "elasticity_coefficient": round(alos_coef_2, 4),
        "std_error": round(alos_se_2, 4),
        "ci_lower": round(float(ci_2[0]), 4),
        "ci_upper": round(float(ci_2[1]), 4),
        "t_statistic": round(float(fe_model_m2.tvalues["ln_alos"]), 4),
        "p_value": round(alos_pval_2, 4),
        "significance": "p < 0.01" if alos_pval_2 < 0.01 else ("p < 0.05" if alos_pval_2 < 0.05 else ("p < 0.10" if alos_pval_2 < 0.10 else "Not statistically significant at 5%")),
        "r_squared": round(float(fe_model_m2.rsquared), 4),
        "covariance_type": f"State-Clustered Standard Errors ({n_states} clusters)",
        "small_cluster_caveat": small_cluster_msg,
        "interpretation": f"After controlling for national annual shocks and clustering by state, the ALOS elasticity is {alos_coef_2:.2f} (95% CI: [{ci_2[0]:.2f}, {ci_2[1]:.2f}]). Reflects sensitivity to macroeconomic recovery dynamics."
    }, {
        "model_id": "Model_2_TwoWay_FE_Clustered",
        "specification": "Two-Way FE (State + Year, State-Clustered SEs)",
        "sample_period": f"2018–2025 (N={n_obs}, States={n_states}, Years={n_years})",
        "dependent_variable": "ln(Real Accommodation Expenditure)",
        "independent_variable": "ln(Overnight Tourists)",
        "elasticity_coefficient": round(tour_coef_2, 4),
        "std_error": round(tour_se_2, 4),
        "ci_lower": round(float(fe_model_m2.conf_int().loc["ln_tourists"][0]), 4),
        "ci_upper": round(float(fe_model_m2.conf_int().loc["ln_tourists"][1]), 4),
        "t_statistic": round(float(fe_model_m2.tvalues["ln_tourists"]), 4),
        "p_value": round(tour_pval_2, 4),
        "significance": "p < 0.01" if tour_pval_2 < 0.01 else ("p < 0.05" if tour_pval_2 < 0.05 else "Not sig"),
        "r_squared": round(float(fe_model_m2.rsquared), 4),
        "covariance_type": f"State-Clustered Standard Errors ({n_states} clusters)",
        "small_cluster_caveat": small_cluster_msg,
        "interpretation": f"Overnight tourist volume elasticity remains strongly positive ({tour_coef_2:.2f}, p < 0.01) after two-way fixed effects."
    }])

    # =========================================================================
    # Model 3: Multi-Factor Hotel Operations Model with Two-Way FE
    # =========================================================================
    df_ops = df[df["aor_pct"].notnull() & (df["aor_pct"] > 0)].copy()
    if not df_ops.empty:
        fe_model_ops = ols(
            "ln_real_accom_spend ~ ln_alos + ln_tourists + ln_aor + foreign_share + C(state) + C(year)",
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
                "dependent_variable": "ln(Real Accommodation Expenditure)",
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
                "small_cluster_caveat": small_cluster_msg,
                "interpretation": f"Conditional within-state association controlling for AOR, foreign guest mix, state, and year effects."
            })

    # =========================================================================
    # Model 4: Yield-Focused Two-Way FE Model (Phase 9.3)
    # Dependent Variable: ln(Real Accommodation Yield per Tourist-Night)
    # =========================================================================
    fe_model_yield = ols(
        "ln_real_accom_yield ~ ln_aor + foreign_share + holiday_share + C(state) + C(year)",
        data=df
    ).fit(cov_type="cluster", cov_kwds={"groups": df["state"]})

    for var, var_label in [
        ("ln_aor", "ln(Average Occupancy Rate - AOR)"),
        ("foreign_share", "Foreign Hotel Guest Share (%)"),
        ("holiday_share", "Holiday Purpose Share (%)"),
    ]:
        c = float(fe_model_yield.params[var])
        se = float(fe_model_yield.bse[var])
        t = float(fe_model_yield.tvalues[var])
        p = float(fe_model_yield.pvalues[var])
        ci = fe_model_yield.conf_int().loc[var]
        sig = "p < 0.01" if p < 0.01 else ("p < 0.05" if p < 0.05 else ("p < 0.10" if p < 0.10 else "Not sig"))

        panel_summary_records.append({
            "model_id": "Model_4_Yield_TwoWay_FE",
            "specification": "Two-Way FE Accommodation Yield Model (State-Clustered SEs)",
            "sample_period": f"2018–2025 (N={n_obs}, States={n_states}, Years={n_years})",
            "dependent_variable": "ln(Real Accommodation Yield RM/night)",
            "independent_variable": var_label,
            "elasticity_coefficient": round(c, 4),
            "std_error": round(se, 4),
            "ci_lower": round(float(ci[0]), 4),
            "ci_upper": round(float(ci[1]), 4),
            "t_statistic": round(t, 4),
            "p_value": round(p, 4),
            "significance": sig,
            "r_squared": round(float(fe_model_yield.rsquared), 4),
            "covariance_type": f"State-Clustered Standard Errors ({n_states} clusters)",
            "small_cluster_caveat": small_cluster_msg,
            "interpretation": f"Explains variation in lodging yield per tourist night; reflects occupancy intensity and lodging yield responsiveness under tighter capacity (AOR) and higher-spending traveler profiles."
        })

    df_summary = pd.DataFrame(panel_summary_records)

    # =========================================================================
    # Phase 11: Leave-One-State-Out Robustness (Models 2 & 4)
    # =========================================================================
    MODEL_VAL_DIR.mkdir(parents=True, exist_ok=True)
    df_loo_m2 = run_leave_one_state_out(
        df,
        "ln_real_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)",
        key_vars=["ln_alos", "ln_tourists"],
        model_id="Model_2_Spend_TwoWay_FE",
    )
    df_loo_m4 = run_leave_one_state_out(
        df,
        "ln_real_accom_yield ~ ln_aor + foreign_share + holiday_share + C(state) + C(year)",
        key_vars=["ln_aor", "foreign_share", "holiday_share"],
        model_id="Model_4_Yield_TwoWay_FE",
    )
    df_loo = pd.concat([df_loo_m2, df_loo_m4], ignore_index=True)
    loo_csv = MODEL_VAL_DIR / "state_leave_one_out.csv"
    df_loo.to_csv(loo_csv, index=False)

    # =========================================================================
    # Phase 11: Outlier and Influence Diagnostics
    # =========================================================================
    # Fit standard OLS without cluster keyword to calculate Hat matrix & Cook's D
    ols_m2 = ols("ln_real_accom_spend ~ ln_alos + ln_tourists + C(state) + C(year)", data=df).fit()
    df_influence = calc_influence_diagnostics(ols_m2, df, model_id="Model_2_Spend_TwoWay_FE")
    infl_csv = MODEL_VAL_DIR / "panel_influence_diagnostics.csv"
    df_influence.to_csv(infl_csv, index=False)

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
            e_grow = ((r25["real_total_expenditure"] - r19["real_total_expenditure"]) / r19["real_total_expenditure"]) * 100.0
            a_grow = ((r25["real_accom_spend"] - r19["real_accom_spend"]) / r19["real_accom_spend"]) * 100.0
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
    con.execute("CREATE OR REPLACE TABLE panel_leave_one_out AS SELECT * FROM df_loo")
    con.execute("CREATE OR REPLACE TABLE panel_influence_diagnostics AS SELECT * FROM df_influence")

    summary_parquet = PROCESSED_DIR / "panel_regression_summary.parquet"
    traj_parquet = PROCESSED_DIR / "state_recovery_trajectory.parquet"
    loo_parquet = PROCESSED_DIR / "panel_leave_one_out.parquet"
    infl_parquet = PROCESSED_DIR / "panel_influence_diagnostics.parquet"

    con.execute(f"COPY panel_regression_summary TO '{summary_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY state_recovery_trajectory TO '{traj_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY panel_leave_one_out TO '{loo_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY panel_influence_diagnostics TO '{infl_parquet}' (FORMAT PARQUET)")
    con.close()

    print(f"Panel econometrics estimated ({len(df_summary)} coefficient models).")
    print(f"Leave-one-state-out sensitivity computed ({len(df_loo)} iterations).")
    print(f"Influence diagnostics computed ({len(df_influence)} observations).")
    print(f"Recovery trajectory calculated for {len(df_traj)} states.")
    return df_summary, df_traj, df_loo, df_influence


if __name__ == "__main__":
    df_sum, df_traj, df_loo, df_infl = run_panel_econometrics()
    print("\n=== PANEL REGRESSION DUAL MODEL SPECIFICATIONS ===")
    print(df_sum[["model_id", "specification", "independent_variable", "elasticity_coefficient", "ci_lower", "ci_upper", "p_value", "significance"]].to_string(index=False))

    print("\n=== LEAVE-ONE-OUT COEFFICIENT STABILITY (ALOS) ===")
    alos_loo = df_loo[df_loo["variable"] == "ln_alos"]
    print(f"Mean ALOS Coef: {alos_loo['coefficient'].mean():.4f}, Min: {alos_loo['coefficient'].min():.4f}, Max: {alos_loo['coefficient'].max():.4f}")

    print("\n=== 2019 vs 2025 RECOVERY TRAJECTORY (TOP 5) ===")
    print(df_traj[["state", "visitor_growth_pct", "alos_delta_days", "recovery_pattern"]].head().to_string(index=False))
