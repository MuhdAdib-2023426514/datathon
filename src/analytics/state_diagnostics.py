"""
State Econometric Diagnostics & Yield Analysis (Stage C & Advanced Root-Cause Drivers)
Computes:
1. Cross-sectional descriptive statistics, Spearman rank correlations.
2. State Yield Typologies (Volume Trap, Transit Spender, Budget Retreat, High-Yield Destination).
3. SDG 8.9 & 12.b Economic Indicators (TEY, EPR, DVR GVA Retained).
4. Granular DTS Sub-Table Integration (Paid Commercial vs Unpaid VFR, Demographics, Affluence).
5. Cross-Sectional OLS Econometric Driver Regressions (Explaining Spend Per Night & Accom Share).
6. Corridor Opportunity Gap Matrix (Quantifying incremental economic value for +0.5 nights across active corridors).

Exports diagnostic tables to DuckDB and Parquet:
- state_year (enriched with granular structural drivers & typologies)
- state_diagnostics_correlations
- state_driver_regression_summary
- corridor_opportunity_gap
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, List
import duckdb
import numpy as np
import pandas as pd
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scipy import stats
import statsmodels.api as sm
from src.analytics.accounting import calc_sdg_attributable_gva, calc_value_retention_rate

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

MANDATORY_SCENARIO_DISCLAIMER = "Scenario estimate, not a causal forecast."
ACCOMMODATION_VAI = 0.8579


def run_state_diagnostics() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Computes statistical diagnostics, driver regressions, and corridor opportunity gaps
    across all 16 Malaysian states and Federal Territories.
    """
    con = duckdb.connect(str(DUCKDB_PATH))
    existing_tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
    df = con.execute("SELECT * FROM state_year").df()

    # Clean up any existing granular or suffixed columns from previous runs
    cols_to_drop = [c for c in df.columns if c.endswith("_x") or c.endswith("_y")]
    if "state_granular_profile" in existing_tables:
        df_gran = con.execute("SELECT * FROM state_granular_profile").df()
        for c in df_gran.columns:
            if c != "state" and c in df.columns:
                cols_to_drop.append(c)
    if cols_to_drop:
        df = df.drop(columns=list(set(cols_to_drop)))

    # 1. Merge Granular DTS 2025 Sub-Table Profiles (Root Cause Drivers)
    if "state_granular_profile" in existing_tables:
        drop_cols = [c for c in ["state_code", "region"] if c in df_gran.columns]
        df = df.merge(df_gran.drop(columns=drop_cols), on="state", how="left")

    # 2. Spearman Rank Correlations
    # Testing relationship between ALOS, Spend Per Night, Accommodation Share, and Granular Drivers
    corr_records = []
    test_pairs = [
        ("spend_per_tourist_rm", "alos_days"),
        ("spend_per_night_rm", "alos_days"),
        ("accommodation_share", "alos_days"),
        ("accommodation_expenditure_rm_million", "alos_days"),
    ]

    if "paid_commercial_share_pct" in df.columns:
        test_pairs.extend([
            ("spend_per_night_rm", "paid_commercial_share_pct"),
            ("accommodation_share", "paid_commercial_share_pct"),
            ("spend_per_night_rm", "affluence_index"),
            ("spend_per_night_rm", "holiday_leisure_share_pct"),
            ("spend_per_night_rm", "unpaid_vfr_share_pct"),
        ])

    for target, bench in test_pairs:
        if target in df.columns and bench in df.columns:
            rho, p_val = stats.spearmanr(df[bench], df[target])
            corr_records.append({
                "target_metric": target,
                "benchmark_metric": bench,
                "spearman_rho": round(rho, 4),
                "p_value": round(p_val, 4),
                "significance": "p < 0.01" if p_val < 0.01 else ("p < 0.05" if p_val < 0.05 else "Not statistically significant"),
                "interpretation": (
                    "Strong positive association" if rho > 0.5
                    else "Moderate positive association" if rho > 0.2
                    else "Strong negative association" if rho < -0.5
                    else "Moderate negative association" if rho < -0.2
                    else "Weak / Neutral association"
                )
            })

    df_corr = pd.DataFrame(corr_records)

    # 3. Cross-Sectional State Profiles & Yield Typologies
    alos_median = df["alos_days"].median()
    spend_per_tourist_median = df["spend_per_tourist_rm"].median()

    def categorize_state_yield(row):
        high_stay = row["alos_days"] >= alos_median
        high_spend = row["spend_per_tourist_rm"] >= spend_per_tourist_median

        if not high_stay and not high_spend:
            return "Volume Trap (Low ALOS, Low Spend/Tourist)"
        elif not high_stay and high_spend:
            return "Transit Spender (Short Stay, High Spend/Tourist)"
        elif high_stay and not high_spend:
            return "Budget Retreat (Long Stay, Low Spend/Tourist)"
        else:
            return "High-Yield Destination (Long Stay, High Spend/Tourist)"

    df["yield_typology"] = df.apply(categorize_state_yield, axis=1)

    # 4. Sustainable Tourism & SDG 8.9 / 12.b Economic Indicators
    # A. Total Visitor-Days Footprint = (Overnight Tourists * ALOS) + Excursionists
    df["total_visitor_days_thousands"] = (
        (df["tourists_thousands"] * df["alos_days"]) + df["excursionists_thousands"]
    ).round(2)

    # B. Tourism Economic Yield per Visitor-Day (TEY in RM)
    vis_days_denom = df["total_visitor_days_thousands"] * 1e3
    df["tourism_economic_yield_per_day_rm"] = np.where(
        vis_days_denom > 0,
        ((df["total_expenditure_rm_million"] * 1e6) / vis_days_denom).round(2),
        np.nan,
    )

    # C. Excursionist Pressure Ratio (EPR = Excursionists / Overnight Tourists)
    tour_denom = df["tourists_thousands"]
    df["excursionist_pressure_ratio"] = np.where(
        tour_denom > 0,
        (df["excursionists_thousands"] / tour_denom).round(2),
        np.nan,
    )

    # D. Domestic Value Retention Multiplier (DVR GVA proxy using TSA Value-Added Intensities)
    # Using dynamic 2025 empirical TSA VAI: Accommodation = 0.8659, Food = 0.4318, Shopping = 0.7088, Transport = 0.1621
    vai_map_2025 = {
        "accommodation": 0.8659,
        "food_beverage": 0.4318,
        "shopping": 0.7088,
        "transport": 0.1621,
        "other": 0.5000,
    }
    retained_gvas = []
    for _, r in df.iterrows():
        t_exp = r["total_expenditure_rm_million"] or 0.0
        a_exp = r["accommodation_expenditure_rm_million"] or 0.0
        f_exp = r["food_expenditure_rm_million"] or 0.0
        s_exp = r["shopping_expenditure_rm_million"] or 0.0
        tr_exp = r["transport_expenditure_rm_million"] or 0.0
        o_exp = max(0.0, t_exp - (a_exp + f_exp + s_exp + tr_exp))
        retained_gvas.append(
            calc_sdg_attributable_gva(a_exp, f_exp, s_exp, tr_exp, o_exp, vai_map_2025)
        )
    df["estimated_retained_gva_rm_million"] = np.round(retained_gvas, 2)
    tot_exp = df["total_expenditure_rm_million"]
    df["value_retention_rate_pct"] = np.where(
        tot_exp > 0,
        ((df["estimated_retained_gva_rm_million"] / tot_exp) * 100.0).round(2),
        np.nan,
    )

    # 5. Strategic Policy Prescriptions
    def get_policy_prescription(row):
        typology = str(row.get("yield_typology", ""))
        paid_share = row.get("paid_commercial_share_pct", 50.0)
        
        if "Volume Trap" in typology:
            if paid_share < 40.0:
                return "Commercial lodging conversion: Upgrade private VFR lodging into certified homestays; bundle multi-day experiential packages to lift ALOS."
            return "Shift focus from volume to length of stay; bundle evening cultural events, weekend passes, and premium boutique lodging."
        elif "Transit Spender" in typology:
            return "Capture day-trip leakage through night-time economy, cultural evening showcases, and secondary district circuit packaging."
        elif "High-Yield" in typology:
            return "Preserve premium yield; monitor environmental carrying capacity; protect luxury nature and heritage assets."
        elif "Budget Retreat" in typology:
            if paid_share < 40.0:
                return "VFR monetization priority: Deepen commercial accommodation penetration, expand boutique eco-resorts, and monetize local heritage."
            return "Formalize homestays and commercial lodging; monetize culinary and local craft experiences to increase spend per day."
        return "Maintain balanced sustainable growth."

    df["policy_prescription"] = df.apply(get_policy_prescription, axis=1)

    # 6. Merge Historical 2019-2025 Recovery Trajectory from Panel Model
    if "state_recovery_trajectory" in existing_tables:
        df_traj = con.execute("SELECT state, visitor_growth_pct, alos_delta_days, recovery_pattern FROM state_recovery_trajectory").df()
        # Drop if already merged to avoid duplicates
        drop_traj_cols = [c for c in ["visitor_growth_pct", "alos_delta_days", "recovery_pattern"] if c in df.columns]
        if drop_traj_cols:
            df = df.drop(columns=drop_traj_cols)
        df = df.merge(df_traj, on="state", how="left")

    # 7. Econometric Driver OLS Regressions
    regression_records = []

    # Model 1: Spend Per Night Drivers
    # spend_per_night = beta0 + beta1(paid_commercial_share) + beta2(holiday_share) + beta3(affluence_index)
    if all(c in df.columns for c in ["paid_commercial_share_pct", "holiday_leisure_share_pct", "affluence_index", "spend_per_night_rm"]):
        X1 = df[["paid_commercial_share_pct", "holiday_leisure_share_pct", "affluence_index"]]
        X1 = sm.add_constant(X1)
        y1 = df["spend_per_night_rm"]
        ols1 = sm.OLS(y1, X1).fit()

        for var_name in X1.columns:
            coef = ols1.params[var_name]
            se = ols1.bse[var_name]
            t_stat = ols1.tvalues[var_name]
            pval = ols1.pvalues[var_name]
            regression_records.append({
                "model_id": "M1_SpendPerNight",
                "model_description": "Cross-Sectional Drivers of Accommodation Spend Per Night",
                "dependent_variable": "spend_per_night_rm",
                "regressor": var_name,
                "coefficient": round(coef, 4),
                "std_error": round(se, 4),
                "t_statistic": round(t_stat, 4),
                "p_value": round(pval, 4),
                "significance": "p < 0.01" if pval < 0.01 else ("p < 0.05" if pval < 0.05 else ("p < 0.10" if pval < 0.10 else "Not significant")),
                "r_squared": round(ols1.rsquared, 4),
                "adj_r_squared": round(ols1.rsquared_adj, 4),
                "f_statistic": round(ols1.fvalue, 4),
                "f_pvalue": round(ols1.f_pvalue, 4),
                "n_obs": int(ols1.nobs)
            })

    # Model 2: Accommodation Share Drivers
    # accommodation_share = alpha0 + alpha1(paid_commercial_share) + alpha2(holiday_share) + alpha3(alos_days)
    if all(c in df.columns for c in ["paid_commercial_share_pct", "holiday_leisure_share_pct", "alos_days", "accommodation_share"]):
        X2 = df[["paid_commercial_share_pct", "holiday_leisure_share_pct", "alos_days"]]
        X2 = sm.add_constant(X2)
        y2 = df["accommodation_share"]
        ols2 = sm.OLS(y2, X2).fit()

        for var_name in X2.columns:
            coef = ols2.params[var_name]
            se = ols2.bse[var_name]
            t_stat = ols2.tvalues[var_name]
            pval = ols2.pvalues[var_name]
            regression_records.append({
                "model_id": "M2_AccommodationShare",
                "model_description": "Cross-Sectional Drivers of Tourism Accommodation Expenditure Share",
                "dependent_variable": "accommodation_share",
                "regressor": var_name,
                "coefficient": round(coef, 4),
                "std_error": round(se, 4),
                "t_statistic": round(t_stat, 4),
                "p_value": round(pval, 4),
                "significance": "p < 0.01" if pval < 0.01 else ("p < 0.05" if pval < 0.05 else ("p < 0.10" if pval < 0.10 else "Not significant")),
                "r_squared": round(ols2.rsquared, 4),
                "adj_r_squared": round(ols2.rsquared_adj, 4),
                "f_statistic": round(ols2.fvalue, 4),
                "f_pvalue": round(ols2.f_pvalue, 4),
                "n_obs": int(ols2.nobs)
            })

    df_reg = pd.DataFrame(regression_records)

    # 8. Corridor "Value Leakage" & Opportunity Gap Matrix
    # Computes incremental accommodation value if ALOS expands by +0.5 nights across all 240 active corridors
    df_gap = pd.DataFrame()
    if "corridor_classification" in existing_tables:
        df_corr_raw = con.execute("SELECT * FROM corridor_classification WHERE is_interstate = true").df()
        delta_alos = 0.5

        df_corr_raw["delta_alos_scenario_days"] = delta_alos
        df_corr_raw["target_alos_days"] = (df_corr_raw["dest_alos"] + delta_alos).round(2)
        df_corr_raw["additional_tourist_nights_thousands"] = (df_corr_raw["tourist_flow_thousands"] * delta_alos).round(3)
        df_corr_raw["additional_accom_expenditure_rm_million"] = (
            (df_corr_raw["additional_tourist_nights_thousands"] * df_corr_raw["dest_spend_per_night"]) / 1000.0
        ).round(2)
        df_corr_raw["potential_retained_gva_rm_million"] = (
            df_corr_raw["additional_accom_expenditure_rm_million"] * ACCOMMODATION_VAI
        ).round(2)
        df_corr_raw["policy_disclaimer"] = MANDATORY_SCENARIO_DISCLAIMER

        # Merge hotel capacity feasibility metrics if available
        if "accommodation_capacity" in existing_tables:
            df_cap = con.execute(
                "SELECT state AS destination, "
                "COALESCE(aor_2025_pct, aor_2024_pct) AS dest_baseline_aor_pct, "
                "COALESCE(hotel_rooms_2025, dts_rooms_2025, hotel_rooms_2024) AS dest_available_rooms "
                "FROM accommodation_capacity"
            ).df()
            df_corr_raw = df_corr_raw.merge(df_cap, on="destination", how="left")
            daily_rooms_demanded = (df_corr_raw["additional_tourist_nights_thousands"] * 1000.0) / (365.0 * 1.8)
            has_rooms = df_corr_raw["dest_available_rooms"].fillna(0) > 0
            delta_aor = np.where(
                has_rooms,
                (daily_rooms_demanded / df_corr_raw["dest_available_rooms"]) * 100.0,
                np.nan,
            )
            df_corr_raw["implied_dest_aor_pct"] = np.where(
                pd.notnull(delta_aor) & pd.notnull(df_corr_raw["dest_baseline_aor_pct"]),
                (df_corr_raw["dest_baseline_aor_pct"] + delta_aor).round(2),
                np.nan,
            )
            def _capacity_label(val):
                if pd.isna(val):
                    return "Unknown (Capacity Data Unavailable)"
                if val > 100.0:
                    return "Physical Capacity Breach (>100% Saturation)"
                if val > 80.0:
                    return "Capacity Constraint Alert (>80% Saturation)"
                if val >= 70.0:
                    return "Planning Watch (70-80% Saturation)"
                return "Feasible (Within Hotel Capacity)"
            df_corr_raw["capacity_constraint_alert"] = df_corr_raw["implied_dest_aor_pct"].apply(_capacity_label)

        # Merge spatial gravity metrics if available
        if "corridor_gravity_predictions" in existing_tables:
            df_grav = con.execute(
                "SELECT origin, destination, distance_km, gravity_residual, performance_ratio, corridor_gravity_category "
                "FROM corridor_gravity_predictions"
            ).df()
            df_gap = df_corr_raw.merge(df_grav, on=["origin", "destination"], how="left")
        else:
            df_gap = df_corr_raw

        # Sort descending by economic opportunity
        df_gap = df_gap.sort_values(by="additional_accom_expenditure_rm_million", ascending=False).reset_index(drop=True)
        df_gap["opportunity_rank"] = range(1, len(df_gap) + 1)

    # 9. Export All Tables to DuckDB & Parquet
    con.execute("CREATE OR REPLACE TABLE state_year AS SELECT * FROM df")
    con.execute("CREATE OR REPLACE TABLE state_diagnostics_correlations AS SELECT * FROM df_corr")
    
    if not df_reg.empty:
        con.execute("CREATE OR REPLACE TABLE state_driver_regression_summary AS SELECT * FROM df_reg")
        reg_parquet = PROCESSED_DIR / "state_driver_regression_summary.parquet"
        con.execute(f"COPY state_driver_regression_summary TO '{reg_parquet}' (FORMAT PARQUET)")

    if not df_gap.empty:
        con.execute("CREATE OR REPLACE TABLE corridor_opportunity_gap AS SELECT * FROM df_gap")
        gap_parquet = PROCESSED_DIR / "corridor_opportunity_gap.parquet"
        con.execute(f"COPY corridor_opportunity_gap TO '{gap_parquet}' (FORMAT PARQUET)")

    corr_parquet = PROCESSED_DIR / "state_diagnostics_correlations.parquet"
    state_parquet = PROCESSED_DIR / "state_year.parquet"
    con.execute(f"COPY state_diagnostics_correlations TO '{corr_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY state_year TO '{state_parquet}' (FORMAT PARQUET)")
    con.close()

    print("State econometric diagnostics, driver regressions, and corridor opportunity gap complete.")
    return df, df_corr, df_reg, df_gap


if __name__ == "__main__":
    df_state, df_corr, df_reg, df_gap = run_state_diagnostics()
    print("\n=== SPEARMAN RANK CORRELATIONS ===")
    print(df_corr.to_string(index=False))

    print("\n=== ECONOMETRIC DRIVER REGRESSIONS ===")
    if not df_reg.empty:
        print(df_reg[["model_id", "regressor", "coefficient", "t_statistic", "p_value", "r_squared", "significance"]].to_string(index=False))

    print("\n=== TOP 10 CORRIDOR OPPORTUNITY GAPS (+0.5 NIGHTS) ===")
    if not df_gap.empty:
        print(df_gap[[
            "opportunity_rank", "origin", "destination", "tourist_flow_thousands",
            "dest_alos", "dest_spend_per_night", "additional_accom_expenditure_rm_million",
            "potential_retained_gva_rm_million", "corridor_tier"
        ]].head(10).to_string(index=False))
