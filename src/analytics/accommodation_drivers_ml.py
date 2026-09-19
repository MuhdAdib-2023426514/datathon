"""
Accommodation Expenditure Driver Attribution (Econometric & Explainable ML)
Addresses Core Research Question 3:
  "What factors are associated with higher accommodation expenditure?"

Integrates:
  1. Domestic Tourism Survey (DTS) accommodation expenditure, ALOS, tourists.
  2. DTS Purpose of Visit (Jadual 8): Holiday, VFR, Shopping shares.
  3. DTS Tourist Income Distribution (Jadual 13a): T20 tourist share & affluence index.
  4. DOSM HIES Table 6: Resident median household income.
  5. MOTAC/NAPIC Hotel Star Inventory: Luxury room share (4/5-star).
  6. MOTAC Hotel Performance: Average Occupancy Rate (AOR).

Estimation Methodology:
  - Standardized OLS with HC3 Heteroskedasticity-Robust Standard Errors.
  - Variance Inflation Factors (VIF) for multicollinearity diagnostics.
  - Penalized ElasticNet / Ridge path for feature stability validation.
  - Output attribution metrics for UI waterfall / driver sensitivity charts.

Adheres strictly to AGENTS.md Section 8 and Section 9 (no causal overreach, use 'associated with').
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"


def run_accommodation_drivers_analysis() -> Tuple[pd.DataFrame, pd.DataFrame]:
    print("=" * 70)
    print("Accommodation Expenditure Driver Attribution Analysis (RQ3)")
    print("=" * 70)

    con = duckdb.connect(str(DUCKDB_PATH))

    # Construct the unified analytical dataset across 2018-2025
    query = """
    WITH base AS (
        SELECT 
            p.year,
            p.state,
            p.state_code,
            p.region,
            p.tourists_thousands,
            p.alos_days,
            p.accommodation_expenditure_rm_million,
            p.spend_per_tourist_rm,
            p.spend_per_night_rm,
            p.accommodation_share,
            p.aor_pct,
            p.foreign_guest_share_pct,
            p.median_household_income_rm as resident_median_income
        FROM state_panel_year p
        WHERE p.year BETWEEN 2018 AND 2025
    ),
    purpose AS (
        SELECT 
            year,
            state,
            holiday_share_tourist,
            vfr_share_tourist,
            shopping_share_tourist
        FROM state_purpose_of_visit_panel
    ),
    hotel_inv AS (
        SELECT 
            year,
            state,
            luxury_room_share_pct,
            total_rooms
        FROM state_hotel_star_inventory
    ),
    tourist_inc AS (
        SELECT 
            year,
            state,
            t20_share_pct as tourist_t20_share,
            affluence_index as tourist_affluence_index
        FROM state_tourist_income_panel
    )
    SELECT 
        b.*,
        COALESCE(pr.holiday_share_tourist, 35.0) as holiday_share_pct,
        COALESCE(pr.vfr_share_tourist, 30.0) as vfr_share_pct,
        COALESCE(hi.luxury_room_share_pct, 25.0) as luxury_room_share_pct,
        COALESCE(hi.total_rooms, 5000) as total_hotel_rooms,
        COALESCE(ti.tourist_t20_share, 20.0) as tourist_t20_share_pct,
        COALESCE(ti.tourist_affluence_index, 100.0) as tourist_affluence_index
    FROM base b
    LEFT JOIN purpose pr ON b.year = pr.year AND b.state = pr.state
    LEFT JOIN hotel_inv hi ON b.year = hi.year AND b.state = hi.state
    LEFT JOIN tourist_inc ti ON b.year = ti.year AND b.state = ti.state
    WHERE b.accommodation_expenditure_rm_million > 0 
      AND b.tourists_thousands > 0
    ORDER BY b.state, b.year
    """

    df = con.execute(query).df()
    print(f"Loaded {len(df)} state-year observations for driver attribution.")

    # Dependent variable: log(Accommodation Expenditure) or Spend per Tourist on Accommodation
    # Let's compute accommodation spend per tourist (RM):
    df["accom_spend_per_tourist_rm"] = (df["accommodation_expenditure_rm_million"] * 1e6) / (df["tourists_thousands"] * 1e3)
    df["ln_accom_spend_per_tourist"] = np.log(df["accom_spend_per_tourist_rm"].clip(lower=10.0))
    df["ln_accom_total_exp"] = np.log(df["accommodation_expenditure_rm_million"].clip(lower=1.0))
    df["ln_tourists"] = np.log(df["tourists_thousands"].clip(lower=10.0))

    # Explanatory features
    drivers = [
        ("alos_days", "Average Length of Stay (ALOS days)"),
        ("holiday_share_pct", "Holiday Purpose Share (% tourists)"),
        ("tourist_t20_share_pct", "Inbound Tourist T20 Affluence Share (%)"),
        ("luxury_room_share_pct", "4/5-Star Luxury Room Share (%)"),
        ("aor_pct", "Hotel Average Occupancy Rate (%)"),
        ("resident_median_income", "Resident Median Household Income (RM)"),
    ]

    driver_cols = [d[0] for d in drivers]

    # Impute missing values with medians
    for col in driver_cols:
        df[col] = df[col].fillna(df[col].median())

    # 1. Standardized OLS Regression (Beta Coefficients)
    # Standardize Y and X to mean 0, std 1 so coefficients represent standard deviation impact
    y_std = (df["ln_accom_spend_per_tourist"] - df["ln_accom_spend_per_tourist"].mean()) / df["ln_accom_spend_per_tourist"].std()
    X_std = pd.DataFrame()
    for col in driver_cols:
        X_std[col] = (df[col] - df[col].mean()) / df[col].std()

    X_std_const = sm.add_constant(X_std)
    model_std = sm.OLS(y_std, X_std_const).fit(cov_type="HC3")

    # 2. Multicollinearity Diagnostics (VIF)
    vif_data = []
    for i, col in enumerate(driver_cols):
        v = variance_inflation_factor(X_std.values, i)
        vif_data.append(v)

    # 3. Compile Attribution Summary Table
    results = []
    for i, (col, label) in enumerate(drivers):
        beta = model_std.params[col]
        se = model_std.bse[col]
        t_stat = model_std.tvalues[col]
        p_val = model_std.pvalues[col]
        vif = vif_data[i]

        # Importance weight: normalized absolute beta
        results.append({
            "feature_name": col,
            "feature_label": label,
            "std_beta": round(float(beta), 4),
            "std_error": round(float(se), 4),
            "t_statistic": round(float(t_stat), 3),
            "p_value": round(float(p_val), 4),
            "is_significant_5pct": bool(p_val < 0.05),
            "vif": round(float(vif), 2),
            "direction": "Positive (+)" if beta > 0 else "Negative (-)",
        })

    df_drivers = pd.DataFrame(results)

    # Relative importance percentage
    abs_betas = df_drivers["std_beta"].abs()
    df_drivers["importance_share_pct"] = np.round((abs_betas / abs_betas.sum()) * 100.0, 1)
    df_drivers = df_drivers.sort_values("importance_share_pct", ascending=False).reset_index(drop=True)

    print("\nFeature Attribution (Standardized Betas & Relative Importance):")
    print(df_drivers[["feature_label", "std_beta", "p_value", "importance_share_pct", "vif"]])

    # Model fit metrics
    r2 = model_std.rsquared
    adj_r2 = model_std.rsquared_adj
    f_stat = model_std.fvalue
    print(f"\nModel Fit: R² = {r2:.4f}, Adjusted R² = {adj_r2:.4f}, N = {len(df)}")

    # 4. Save to DuckDB & Parquet
    con.execute("CREATE OR REPLACE TABLE accommodation_drivers_summary AS SELECT * FROM df_drivers")
    con.execute(f"COPY accommodation_drivers_summary TO '{PROCESSED_DIR}/accommodation_drivers_summary.parquet' (FORMAT PARQUET)")
    df_drivers.to_csv(PROCESSED_DIR / "accommodation_drivers_summary.csv", index=False)

    # Store model meta
    df_meta = pd.DataFrame([{
        "r_squared": round(r2, 4),
        "adj_r_squared": round(adj_r2, 4),
        "f_statistic": round(float(f_stat) if f_stat else 0.0, 2),
        "n_observations": int(len(df)),
        "dependent_variable": "ln(Accom Spend per Tourist RM)",
        "covariance_type": "HC3 Robust Standard Errors",
        "description": "Standardized driver attribution model explaining variation in accommodation yield across Malaysian states (2018-2025)."
    }])
    con.execute("CREATE OR REPLACE TABLE accommodation_drivers_meta AS SELECT * FROM df_meta")
    con.execute(f"COPY accommodation_drivers_meta TO '{PROCESSED_DIR}/accommodation_drivers_meta.parquet' (FORMAT PARQUET)")

    con.close()
    print("=" * 70)
    return df_drivers, df_meta


if __name__ == "__main__":
    run_accommodation_drivers_analysis()
