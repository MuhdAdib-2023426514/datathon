"""
State Econometric Diagnostics & Yield Analysis (Stage C & Structural Diagnostic Drivers)
Computes:
1. Cross-sectional descriptive statistics, Spearman rank correlations.
2. State Yield Typologies (Short Stay / Low Yield, Short Stay / High Yield, Long Stay / Low Yield, Long Stay / High Yield).
3. SDG 8.9 & 12.b Economic Indicators (TEY, TVAY, Tourism GVA Intensity, Mapping Coverage, EPR).
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
from src.analytics.accounting import (
    calc_visitor_days,
    calc_tey,
    calc_accommodation_yield,
    calc_estimated_tourism_gva_state,
    calc_mapping_coverage,
    calc_tourism_gva_intensity,
    calc_tvay,
    classify_state_yield_typology,
    calc_sdg_attributable_gva,
    calc_value_retention_rate,
)

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

    # Load 2025 cross-sectional baseline from state_year table
    df = con.execute("SELECT * FROM state_year").df()

    # Drop columns that will be re-merged or recalculated
    cols_to_drop = []
    if "state_granular_profile" in existing_tables:
        df_gran = con.execute("SELECT * FROM state_granular_profile").df()
        for c in df_gran.columns:
            if c != "state" and c in df.columns:
                cols_to_drop.append(c)
    if cols_to_drop:
        df = df.drop(columns=list(set(cols_to_drop)))

    # 1. Merge Granular DTS 2025 Sub-Table Profiles (Exploratory Driver Analysis)
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

    # 3. Sustainable Tourism & SDG 8.9 / 12.b Economic Indicators
    # A. Total Visitor-Days Footprint = (Overnight Tourists * ALOS) + Excursionists
    df["total_visitor_days_thousands"] = [
        calc_visitor_days(t, alos, exc)
        for t, alos, exc in zip(df["tourists_thousands"], df["alos_days"], df["excursionists_thousands"])
    ]

    # B. Tourism Economic Yield per Visitor-Day (TEY in RM)
    df["tourism_economic_yield_per_day_rm"] = [
        np.round(calc_tey(tot_exp * 1e6, vis_days * 1e3), 2)
        for tot_exp, vis_days in zip(df["total_expenditure_rm_million"], df["total_visitor_days_thousands"])
    ]

    # C. Accommodation Yield per Overnight Night (RM/night)
    df["accommodation_yield_per_night_rm"] = [
        np.round(calc_accommodation_yield(accom_exp * 1e6, t * 1e3, alos), 2)
        for accom_exp, t, alos in zip(
            df["accommodation_expenditure_rm_million"], df["tourists_thousands"], df["alos_days"]
        )
    ]

    # D. Excursionist Pressure Ratio (EPR = Excursionists / Overnight Tourists)
    tour_denom = df["tourists_thousands"]
    df["excursionist_pressure_ratio"] = np.where(
        tour_denom > 0,
        (df["excursionists_thousands"] / tour_denom).round(2),
        np.nan,
    )

    # E. Tourism GVA Intensity (%) & Mapping Coverage (%) — Phase 6 & 6.1 (No 0.50 fallback)
    vai_map_2025 = {
        "accommodation": 0.8579,
        "food_beverage": 0.4318,
        "shopping": 0.7088,
        "transport": 0.1627,
    }

    gvas, mapped_exps, coverages, intensities, tvays = [], [], [], [], []
    for _, r in df.iterrows():
        t_exp = r["total_expenditure_rm_million"] or 0.0
        exp_dict = {
            "accommodation": r["accommodation_expenditure_rm_million"],
            "food_beverage": r["food_expenditure_rm_million"],
            "shopping": r["shopping_expenditure_rm_million"],
            "transport": r["transport_expenditure_rm_million"],
        }
        gva, mapped = calc_estimated_tourism_gva_state(exp_dict, vai_map_2025)
        cov = calc_mapping_coverage(mapped, t_exp)
        intensity = calc_tourism_gva_intensity(gva, mapped)

        vis_days_k = r["total_visitor_days_thousands"]
        tvay = calc_tvay(gva * 1e6, vis_days_k * 1e3) if vis_days_k and vis_days_k > 0 else np.nan

        gvas.append(gva)
        mapped_exps.append(mapped)
        coverages.append(cov)
        intensities.append(intensity)
        tvays.append(tvay)

    df["estimated_tourism_gva_rm_million"] = np.round(gvas, 2)
    df["mapped_expenditure_rm_million"] = np.round(mapped_exps, 2)
    df["mapping_coverage_pct"] = np.round(coverages, 1)
    df["tourism_gva_intensity_pct"] = np.round(intensities, 1)
    df["tourism_value_added_yield_per_day_rm"] = np.round(tvays, 2)

    # Backward compatibility aliases
    df["estimated_retained_gva_rm_million"] = df["estimated_tourism_gva_rm_million"]
    df["value_retention_rate_pct"] = df["tourism_gva_intensity_pct"]

    # 4. Cross-Sectional State Profiles & Yield Typologies (Phase 8: ALOS vs TVAY)
    alos_median = df["alos_days"].median()
    tvay_median = df["tourism_value_added_yield_per_day_rm"].median()

    df["yield_typology"] = [
        classify_state_yield_typology(alos, tvay, alos_median, tvay_median)
        for alos, tvay in zip(df["alos_days"], df["tourism_value_added_yield_per_day_rm"])
    ]

    # 5. Strategic Policy Prescriptions
    def get_policy_prescription(row):
        typology = str(row.get("yield_typology", ""))
        paid_share = row.get("paid_commercial_share_pct")

        if "Short Stay / Low Yield" in typology:
            if pd.notnull(paid_share) and paid_share < 40.0:
                return "Commercial lodging conversion: Upgrade private VFR lodging into certified homestays; bundle multi-day experiential packages to lift ALOS."
            return "Shift focus from volume to length of stay; bundle evening cultural events, weekend passes, and premium boutique lodging."
        elif "Short Stay / High Yield" in typology:
            return "High day-trip and short-stay spend capture; develop evening cultural circuits and overnight incentive packaging to deepen stay."
        elif "Long Stay / Low Yield" in typology:
            if pd.notnull(paid_share) and paid_share < 40.0:
                return "Commercial accommodation capture opportunity: Deepen commercial accommodation penetration, expand boutique eco-resorts, and monetize local heritage."
            return "Formalize homestays and commercial lodging; monetize culinary and local craft experiences to increase spend per day."
        elif "Long Stay / High Yield" in typology:
            return "Preserve premium yield; monitor environmental carrying capacity; protect luxury nature and heritage assets."
        return "Maintain balanced sustainable growth."

    df["policy_prescription"] = df.apply(get_policy_prescription, axis=1)

    # 6. Merge Historical 2019-2025 Recovery Trajectory from Panel Model
    if "state_recovery_trajectory" in existing_tables:
        df_traj = con.execute("SELECT state, visitor_growth_pct, alos_delta_days, recovery_pattern FROM state_recovery_trajectory").df()
        drop_traj_cols = [c for c in ["visitor_growth_pct", "alos_delta_days", "recovery_pattern"] if c in df.columns]
        if drop_traj_cols:
            df = df.drop(columns=drop_traj_cols)
        df = df.merge(df_traj, on="state", how="left")

    # 7. Econometric Driver OLS Regressions
    regression_records = []

    # Model 1: Spend Per Night Drivers
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
                "t_statistic": round(t_stat, 3),
                "p_value": round(pval, 4),
                "significance": "p < 0.01" if pval < 0.01 else ("p < 0.05" if pval < 0.05 else "Not significant"),
                "r_squared": round(ols1.rsquared, 4),
                "adj_r_squared": round(ols1.rsquared_adj, 4),
                "f_statistic": round(ols1.fvalue, 3),
                "f_pvalue": round(ols1.f_pvalue, 4),
                "n_obs": int(ols1.nobs),
                "causal_disclaimer": "This exploratory driver analysis identifies associations and should not be interpreted as causal evidence."
            })

    # Model 2: Accommodation Share Drivers
    if all(c in df.columns for c in ["alos_days", "paid_commercial_share_pct", "holiday_leisure_share_pct", "accommodation_share"]):
        X2 = df[["alos_days", "paid_commercial_share_pct", "holiday_leisure_share_pct"]]
        X2 = sm.add_constant(X2)
        y2 = df["accommodation_share"] * 100.0
        ols2 = sm.OLS(y2, X2).fit()

        for var_name in X2.columns:
            coef = ols2.params[var_name]
            se = ols2.bse[var_name]
            t_stat = ols2.tvalues[var_name]
            pval = ols2.pvalues[var_name]
            regression_records.append({
                "model_id": "M2_AccommodationShare",
                "model_description": "Cross-Sectional Drivers of Accommodation Expenditure Share (%)",
                "dependent_variable": "accommodation_share_pct",
                "regressor": var_name,
                "coefficient": round(coef, 4),
                "std_error": round(se, 4),
                "t_statistic": round(t_stat, 3),
                "p_value": round(pval, 4),
                "significance": "p < 0.01" if pval < 0.01 else ("p < 0.05" if pval < 0.05 else "Not significant"),
                "r_squared": round(ols2.rsquared, 4),
                "adj_r_squared": round(ols2.rsquared_adj, 4),
                "f_statistic": round(ols2.fvalue, 3),
                "f_pvalue": round(ols2.f_pvalue, 4),
                "n_obs": int(ols2.nobs),
                "causal_disclaimer": "This exploratory driver analysis identifies associations and should not be interpreted as causal evidence."
            })

    df_reg = pd.DataFrame(regression_records)

    # 8. Corridor Economic Yield & Opportunity Gap Matrix (Phases 19 & 20)
    df_gap = pd.DataFrame()
    if "corridor_classification" in existing_tables:
        df_corr_raw = con.execute("SELECT * FROM corridor_classification WHERE is_interstate = true").df()

        # Merge Destination Concentration (Phase 20)
        if "destination_concentration" in existing_tables:
            df_conc = con.execute(
                "SELECT destination, interstate_origin_hhi AS dest_interstate_hhi, "
                "top_feeder_origin, top_feeder_share_pct, top_3_origin_share_pct, "
                "meaningful_origin_count, concentration_tier AS dest_concentration_tier "
                "FROM destination_concentration"
            ).df()
            df_corr_raw = df_corr_raw.merge(df_conc, on="destination", how="left")
        else:
            df_corr_raw["dest_interstate_hhi"] = np.nan
            df_corr_raw["top_feeder_origin"] = "None"
            df_corr_raw["top_feeder_share_pct"] = np.nan
            df_corr_raw["top_3_origin_share_pct"] = np.nan
            df_corr_raw["meaningful_origin_count"] = np.nan
            df_corr_raw["dest_concentration_tier"] = "Unknown (Concentration Data Unavailable)"

        # Merge SDG Yield Metrics (Sprint 2)
        if "sdg_sustainable_metrics" in existing_tables:
            df_sdg = con.execute(
                "SELECT state AS destination, "
                "tvay_rm_per_day AS dest_tvay_rm_per_day, "
                "real_tey_rm_per_day AS dest_real_tey_rm_per_day, "
                "tir_visitors_per_resident AS dest_tir_ratio "
                "FROM sdg_sustainable_metrics WHERE year = 2025"
            ).df()
            df_corr_raw = df_corr_raw.merge(df_sdg, on="destination", how="left")
        else:
            df_corr_raw["dest_tvay_rm_per_day"] = np.nan
            df_corr_raw["dest_real_tey_rm_per_day"] = np.nan
            df_corr_raw["dest_tir_ratio"] = np.nan

        # Merge hotel capacity feasibility metrics
        if "accommodation_capacity" in existing_tables:
            df_cap = con.execute(
                "SELECT state AS destination, "
                "COALESCE(aor_2025_pct, aor_2024_pct) AS dest_baseline_aor_pct, "
                "COALESCE(hotel_rooms_2025, dts_rooms_2025, hotel_rooms_2024) AS dest_available_rooms "
                "FROM accommodation_capacity"
            ).df()
            df_corr_raw = df_corr_raw.merge(df_cap, on="destination", how="left")
        else:
            df_corr_raw["dest_baseline_aor_pct"] = np.nan
            df_corr_raw["dest_available_rooms"] = np.nan

        # Capacity Headroom - preserve NaN without 50.0 substitution
        df_corr_raw["capacity_headroom_pct"] = np.where(
            pd.notnull(df_corr_raw["dest_baseline_aor_pct"]),
            (100.0 - df_corr_raw["dest_baseline_aor_pct"]).round(2),
            np.nan
        )
        df_corr_raw["capacity_tier"] = np.where(
            pd.isna(df_corr_raw["dest_baseline_aor_pct"]), "Unknown (Capacity Data Unavailable)",
            np.where(
                df_corr_raw["dest_baseline_aor_pct"] < 60.0, "Substantial Headroom (<60% AOR)",
                np.where(
                    df_corr_raw["dest_baseline_aor_pct"] < 75.0, "Moderate Headroom (60-75% AOR)",
                    np.where(
                        df_corr_raw["dest_baseline_aor_pct"] <= 85.0, "Constrained (75-85% AOR)",
                        "Saturated (>85% AOR)"
                    )
                )
            )
        )

        # Merge spatial gravity metrics
        if "corridor_gravity_predictions" in existing_tables:
            df_grav = con.execute(
                "SELECT origin, destination, distance_km, is_cross_region, gravity_residual, performance_ratio, "
                "expected_flow_thousands, corridor_gravity_category "
                "FROM corridor_gravity_predictions"
            ).df()
            # Avoid duplicate distance_km and is_cross_region columns if already present
            grav_cols = ["origin", "destination", "gravity_residual", "performance_ratio", "expected_flow_thousands", "corridor_gravity_category"]
            for col in ["distance_km", "is_cross_region"]:
                if col in df_grav.columns and col not in df_corr_raw.columns:
                    grav_cols.append(col)
            df_gap = df_corr_raw.merge(df_grav[grav_cols], on=["origin", "destination"], how="left")
        else:
            df_gap = df_corr_raw
            df_gap["expected_flow_thousands"] = df_gap["tourist_flow_thousands"]
            df_gap["performance_ratio"] = 1.0
            df_gap["gravity_residual"] = 0.0
            df_gap["corridor_gravity_category"] = "Near Model Expected"

        # Separate Model Gap from Opportunity (Phase 19.1)
        df_gap["expected_flow_thousands"] = df_gap["expected_flow_thousands"].fillna(df_gap["tourist_flow_thousands"])
        df_gap["performance_ratio"] = df_gap["performance_ratio"].fillna(1.0)
        df_gap["gravity_flow_gap_thousands"] = (df_gap["expected_flow_thousands"] - df_gap["tourist_flow_thousands"]).round(2)
        df_gap["gravity_performance_category"] = np.where(
            df_gap["performance_ratio"] < 0.85, "Below Model Expected",
            np.where(df_gap["performance_ratio"] > 1.15, "Above Model Expected", "Near Model Expected")
        )

        # Accessibility - preserve NaN without 300.0 substitution
        is_cross = df_gap["is_cross_region"].fillna(False) if "is_cross_region" in df_gap.columns else pd.Series(False, index=df_gap.index)
        dist = df_gap["distance_km"] if "distance_km" in df_gap.columns else pd.Series(np.nan, index=df_gap.index)
        df_gap["accessibility_tier"] = np.where(
            pd.isna(dist), "Unknown Accessibility (Distance Unavailable)",
            np.where(
                ~is_cross & (dist < 250), "High Accessibility (<250km Road/Rail)",
                np.where(~is_cross & (dist <= 500), "Moderate Accessibility (250-500km Road/Rail)",
                         "Lower Accessibility (>500km or Flight Barrier)")
            )
        )

        # Diversification Benefit - preserve NaN without 1500.0 substitution
        top_origin = df_gap["top_feeder_origin"] if "top_feeder_origin" in df_gap.columns else pd.Series("None", index=df_gap.index)
        df_gap["is_dominant_feeder"] = (df_gap["origin"] == top_origin)
        hhi_val = df_gap["dest_interstate_hhi"] if "dest_interstate_hhi" in df_gap.columns else pd.Series(np.nan, index=df_gap.index)
        df_gap["diversification_benefit"] = np.where(
            pd.isna(hhi_val), "Unknown Diversification (HHI Unavailable)",
            np.where(
                (hhi_val > 2000) & ~df_gap["is_dominant_feeder"], "High Diversification (Reduces Feeder Concentration)",
                np.where(~df_gap["is_dominant_feeder"], "Moderate Diversification", "Consolidating Existing Dominance")
            )
        )

        # Model Confidence
        flows = df_gap["tourist_flow_thousands"]
        df_gap["model_confidence_tier"] = np.where(
            pd.isna(flows), "Unknown Confidence (Flow Unavailable)",
            np.where(
                flows >= 50.0, "High Confidence (Robust Historical Flow)",
                np.where(flows >= 10.0, "Moderate Confidence (Moderate Flow)", "Exploratory (Sparse Flow)")
            )
        )

        # Economic Yield Tiers - preserve NaN without 120.0 substitution
        spend_nt = df_gap["dest_spend_per_night"] if "dest_spend_per_night" in df_gap.columns else pd.Series(np.nan, index=df_gap.index)
        df_gap["yield_tier"] = np.where(
            pd.isna(spend_nt), "Unknown Yield (Spend Data Unavailable)",
            np.where(
                spend_nt >= 160.0, "High Yield (>= RM160/night)",
                np.where(spend_nt >= 100.0, "Moderate Yield (RM100-160/night)", "Lower Yield (< RM100/night)")
            )
        )

        # Scenario metrics (Stay extension delta_alos = 0.5 - illustrative benchmark, not ranking basis)
        delta_alos = 0.5
        df_gap["delta_alos_scenario_days"] = delta_alos
        df_gap["target_alos_days"] = np.where(
            pd.notnull(df_gap["dest_alos"]),
            (df_gap["dest_alos"] + delta_alos).round(2),
            np.nan
        )
        df_gap["additional_tourist_nights_thousands"] = np.where(
            pd.notnull(df_gap["tourist_flow_thousands"]),
            (df_gap["tourist_flow_thousands"] * delta_alos).round(3),
            np.nan
        )
        df_gap["additional_accom_expenditure_rm_million"] = np.where(
            pd.notnull(df_gap["additional_tourist_nights_thousands"]) & pd.notnull(df_gap["dest_spend_per_night"]),
            ((df_gap["additional_tourist_nights_thousands"] * df_gap["dest_spend_per_night"]) / 1000.0).round(2),
            np.nan
        )
        df_gap["potential_additional_value_added_rm_million"] = np.where(
            pd.notnull(df_gap["additional_accom_expenditure_rm_million"]),
            (df_gap["additional_accom_expenditure_rm_million"] * ACCOMMODATION_VAI).round(2),
            np.nan
        )
        df_gap["potential_retained_gva_rm_million"] = df_gap["potential_additional_value_added_rm_million"]
        df_gap["policy_disclaimer"] = MANDATORY_SCENARIO_DISCLAIMER

        # Hotel room demand and implied AOR
        daily_rooms_demanded = np.where(
            pd.notnull(df_gap["additional_tourist_nights_thousands"]),
            (df_gap["additional_tourist_nights_thousands"] * 1000.0) / (365.0 * 1.8),
            np.nan
        )
        has_rooms = (df_gap["dest_available_rooms"].fillna(0) > 0)
        delta_aor = np.where(
            has_rooms & pd.notnull(daily_rooms_demanded),
            (daily_rooms_demanded / df_gap["dest_available_rooms"]) * 100.0,
            np.nan,
        )
        df_gap["implied_dest_aor_pct"] = np.where(
            pd.notnull(delta_aor) & pd.notnull(df_gap["dest_baseline_aor_pct"]),
            (df_gap["dest_baseline_aor_pct"] + delta_aor).round(2),
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
        df_gap["capacity_constraint_alert"] = df_gap["implied_dest_aor_pct"].apply(_capacity_label)

        # Pareto Opportunity Framework (Phase 19.3 & Sprint A)
        # O1: Demand gap / room to model expected (Clean: no arbitrary +0.5 * flow)
        c1 = np.maximum(0.0, df_gap["gravity_flow_gap_thousands"].fillna(0.0))
        # O2: Destination economic yield
        c2 = spend_nt.fillna(0.0)
        # O3: Destination capacity headroom (unobserved capacity -> 0 headroom in sorting)
        c3 = df_gap["capacity_headroom_pct"].fillna(0.0)
        # O4: Overland accessibility (penalize cross-region flight barrier and distance)
        c4 = -dist.fillna(1000.0) - (500.0 * is_cross.astype(float))
        # O5: Market diversification benefit
        orig_share = df_gap["origin_share_of_dest_pct"].fillna(0.0) if "origin_share_of_dest_pct" in df_gap.columns else pd.Series(0.0, index=df_gap.index)
        c5 = (100.0 - orig_share) * (hhi_val.fillna(1000.0) / 2500.0)

        # Flag evidence completeness
        has_critical_evidence = (
            pd.notnull(df_gap["tourist_flow_thousands"]) &
            pd.notnull(df_gap["dest_spend_per_night"]) &
            pd.notnull(df_gap["dest_baseline_aor_pct"])
        )
        df_gap["evidence_status"] = np.where(has_critical_evidence, "complete", "insufficient_data")

        M = np.column_stack([c1, c2, c3, c4, c5])
        N_corrs = len(df_gap)
        dom_count = np.zeros(N_corrs, dtype=int)
        for i in range(N_corrs):
            if not has_critical_evidence.iloc[i]:
                dom_count[i] = 998  # Demote corridors with insufficient evidence
                continue
            for j in range(N_corrs):
                if i == j or not has_critical_evidence.iloc[j]:
                    continue
                if np.all(M[j] >= M[i]) and np.any(M[j] > M[i]):
                    dom_count[i] += 1

        df_gap["is_pareto_optimal"] = (dom_count == 0) & has_critical_evidence
        df_gap["pareto_rank"] = np.where(has_critical_evidence, dom_count + 1, 999)

        # Normalized Composite Opportunity Score [0, 100]
        def _minmax(arr):
            valid_mask = has_critical_evidence.to_numpy()
            if not np.any(valid_mask):
                return np.zeros_like(arr)
            mn = np.min(arr[valid_mask])
            mx = np.max(arr[valid_mask])
            if mx - mn < 1e-9:
                return np.zeros_like(arr)
            res = (arr - mn) / (mx - mn)
            return np.where(valid_mask, np.clip(res, 0.0, 1.0), 0.0)

        comp_score = 100.0 * (
            0.25 * _minmax(c2.to_numpy()) +
            0.20 * _minmax(c3.to_numpy()) +
            0.20 * _minmax(c1.to_numpy()) +
            0.20 * _minmax(c4.to_numpy()) +
            0.15 * _minmax(c5.to_numpy())
        )
        df_gap["composite_opportunity_score"] = np.where(has_critical_evidence, comp_score.round(2), 0.0)

        # Strict Multi-Objective Ranking Hierarchy (Plan Section 8):
        # Primary: Pareto Rank ascending (Non-dominated Frontier 1 first)
        # Secondary: Composite Opportunity Score descending
        df_gap = df_gap.sort_values(
            by=["pareto_rank", "composite_opportunity_score"],
            ascending=[True, False]
        ).reset_index(drop=True)
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
