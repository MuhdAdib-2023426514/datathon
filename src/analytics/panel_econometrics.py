"""
State Panel Econometrics & Recovery Trajectory Analysis (2018–2025)
Estimates:
  1. Model 1 (Baseline DTS 2018–2025): Within-state ALOS and Tourist Volume Elasticities.
  2. Model 2 (Multi-Factor Operations 2018–2024): Within-state ALOS, AOR, and Foreign Guest Share Elasticities.
  3. Volume-Recovery vs. Stay-Lag Opportunity Gap (2019 vs 2025).

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
    df["ln_tourists"] = np.log(df["tourists_thousands"].replace(0, 1))
    df["ln_visitors"] = np.log(df["visitors_thousands"].replace(0, 1))

    panel_summary_records = []

    # =========================================================================
    # Model 1: Baseline State Fixed-Effects Model (2018–2025, N = 126)
    # =========================================================================
    fe_model_base = ols("ln_accom_spend ~ ln_alos + ln_tourists + C(state)", data=df).fit(cov_type="HC1")

    alos_coef_1 = fe_model_base.params["ln_alos"]
    alos_pval_1 = fe_model_base.pvalues["ln_alos"]
    tour_coef_1 = fe_model_base.params["ln_tourists"]
    tour_pval_1 = fe_model_base.pvalues["ln_tourists"]

    panel_summary_records.extend([{
        "model_id": "Model_1_Baseline_DTS",
        "sample_period": "2018–2025 (N=126)",
        "independent_variable": "ln(ALOS)",
        "elasticity_coefficient": round(alos_coef_1, 4),
        "std_error": round(fe_model_base.bse["ln_alos"], 4),
        "t_statistic": round(fe_model_base.tvalues["ln_alos"], 4),
        "p_value": round(alos_pval_1, 4),
        "significance": "p < 0.01" if alos_pval_1 < 0.01 else ("p < 0.05" if alos_pval_1 < 0.05 else "Not sig"),
        "r_squared": round(fe_model_base.rsquared, 4),
        "interpretation": f"A 10% increase in ALOS is associated with a {alos_coef_1 * 10:.1f}% increase in accommodation spend."
    }, {
        "model_id": "Model_1_Baseline_DTS",
        "sample_period": "2018–2025 (N=126)",
        "independent_variable": "ln(Overnight Tourists)",
        "elasticity_coefficient": round(tour_coef_1, 4),
        "std_error": round(fe_model_base.bse["ln_tourists"], 4),
        "t_statistic": round(fe_model_base.tvalues["ln_tourists"], 4),
        "p_value": round(tour_pval_1, 4),
        "significance": "p < 0.01" if tour_pval_1 < 0.01 else ("p < 0.05" if tour_pval_1 < 0.05 else "Not sig"),
        "r_squared": round(fe_model_base.rsquared, 4),
        "interpretation": f"A 10% increase in overnight tourists is associated with a {tour_coef_1 * 10:.1f}% increase in accommodation spend."
    }])

    # =========================================================================
    # Model 2: Multi-Factor Hotel Operations Model (2018–2025, N = 126)
    # =========================================================================
    df_ops = df[df["aor_pct"].notnull() & (df["aor_pct"] > 0)].copy()
    if not df_ops.empty:
        df_ops["ln_aor"] = np.log(df_ops["aor_pct"])
        df_ops["foreign_share"] = df_ops["foreign_guest_share_pct"].fillna(0)

        fe_model_ops = ols(
            "ln_accom_spend ~ ln_alos + ln_tourists + ln_aor + foreign_share + C(state)",
            data=df_ops
        ).fit(cov_type="HC1")

        for var, var_label in [
            ("ln_alos", "ln(ALOS)"),
            ("ln_tourists", "ln(Overnight Tourists)"),
            ("ln_aor", "ln(Average Occupancy Rate - AOR)"),
            ("foreign_share", "Foreign Hotel Guest Share (%)"),
        ]:
            c = fe_model_ops.params[var]
            se = fe_model_ops.bse[var]
            t = fe_model_ops.tvalues[var]
            p = fe_model_ops.pvalues[var]
            sig = "p < 0.01" if p < 0.01 else ("p < 0.05" if p < 0.05 else ("p < 0.10" if p < 0.10 else "Not sig"))

            if "ln" in var:
                interp = f"A 10% increase in {var_label} is associated with a {c * 10:.1f}% change in accommodation spend."
            else:
                interp = f"A 1 percentage point increase in foreign guest share is associated with a {c * 100:.2f}% change in accommodation spend."

            panel_summary_records.append({
                "model_id": "Model_2_MultiFactor_Operations",
                "sample_period": f"2018–2025 (N={int(fe_model_ops.nobs)})",
                "independent_variable": var_label,
                "elasticity_coefficient": round(c, 4),
                "std_error": round(se, 4),
                "t_statistic": round(t, 4),
                "p_value": round(p, 4),
                "significance": sig,
                "r_squared": round(fe_model_ops.rsquared, 4),
                "interpretation": interp
            })

    df_panel_summary = pd.DataFrame(panel_summary_records)

    # =========================================================================
    # 3. Volume-Recovery vs. Stay-Lag Analysis (2019 vs 2025)
    # =========================================================================
    df_2019 = df[df["year"] == 2019].set_index("state")
    df_2025 = df[df["year"] == 2025].set_index("state")

    common_states = df_2019.index.intersection(df_2025.index)
    traj_records = []

    for state in common_states:
        vis_19 = df_2019.loc[state, "visitors_thousands"]
        vis_25 = df_2025.loc[state, "visitors_thousands"]
        alos_19 = df_2019.loc[state, "alos_days"]
        alos_25 = df_2025.loc[state, "alos_days"]
        accom_19 = df_2019.loc[state, "accommodation_expenditure_rm_million"]
        accom_25 = df_2025.loc[state, "accommodation_expenditure_rm_million"]

        vis_growth_pct = ((vis_25 - vis_19) / vis_19) * 100.0 if vis_19 > 0 else 0.0
        alos_delta_days = alos_25 - alos_19
        alos_growth_pct = (alos_delta_days / alos_19) * 100.0 if alos_19 > 0 else 0.0
        accom_growth_pct = ((accom_25 - accom_19) / accom_19) * 100.0 if accom_19 > 0 else 0.0

        if vis_growth_pct > 0 and alos_delta_days < 0:
            category = "Volume Recovered, Stay Lagging (Opportunity Gap)"
        elif vis_growth_pct > 0 and alos_delta_days >= 0:
            category = "Balanced Expansion (Volume & Stay Expanded)"
        elif vis_growth_pct <= 0 and alos_delta_days >= 0:
            category = "Deepened Niche (Fewer Visitors, Longer Stay)"
        else:
            category = "Contracting Volume & Stay"

        traj_records.append({
            "state": state,
            "visitors_2019_k": round(vis_19, 1),
            "visitors_2025_k": round(vis_25, 1),
            "visitor_growth_pct": round(vis_growth_pct, 1),
            "alos_2019_days": round(alos_19, 2),
            "alos_2025_days": round(alos_25, 2),
            "alos_delta_days": round(alos_delta_days, 2),
            "alos_growth_pct": round(alos_growth_pct, 1),
            "accom_spend_2019_m": round(accom_19, 1),
            "accom_spend_2025_m": round(accom_25, 1),
            "accom_growth_pct": round(accom_growth_pct, 1),
            "recovery_pattern": category,
        })

    df_traj = pd.DataFrame(traj_records).sort_values("visitor_growth_pct", ascending=False)

    # Export to DuckDB and Parquet
    con.execute("CREATE OR REPLACE TABLE panel_regression_summary AS SELECT * FROM df_panel_summary")
    con.execute("CREATE OR REPLACE TABLE state_recovery_trajectory AS SELECT * FROM df_traj")

    con.execute(f"COPY panel_regression_summary TO '{PROCESSED_DIR / 'panel_regression_summary.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY state_recovery_trajectory TO '{PROCESSED_DIR / 'state_recovery_trajectory.parquet'}' (FORMAT PARQUET)")
    con.close()

    print("Panel econometrics (Model 1 Baseline & Model 2 Operations) complete.")
    return df_panel_summary, df_traj


if __name__ == "__main__":
    df_sum, df_traj = run_panel_econometrics()
    print("\n=== MULTI-FACTOR PANEL REGRESSION SUMMARY ===")
    print(df_sum[["model_id", "sample_period", "independent_variable", "elasticity_coefficient", "t_statistic", "p_value", "r_squared", "significance"]].to_string(index=False))

    print("\n=== TOP STATES WITH 'VOLUME RECOVERED, STAY LAGGING' GAP ===")
    lagging = df_traj[df_traj["recovery_pattern"].str.contains("Stay Lagging")]
    cols = ["state", "visitor_growth_pct", "alos_2019_days", "alos_2025_days", "alos_delta_days", "recovery_pattern"]
    print(lagging[cols].to_string(index=False))
