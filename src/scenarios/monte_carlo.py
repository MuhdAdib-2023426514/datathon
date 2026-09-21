"""
Monte Carlo Stochastic Uncertainty Simulator for Tourism Policy Scenarios
Simulates probability distributions of economic yield, tourist nights, and room capacity
stress under stochastic campaign reach, stay extension, spend velocity, and guest density.

Phase 26 Implementation (AGENTS.md Section 7, 8, 9)
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import duckdb
import numpy as np
import pandas as pd
from scipy import stats

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

MANDATORY_DISCLAIMER = "Scenario estimate with stochastic uncertainty distribution, not a causal forecast."
SEASONAL_CAPACITY_CAVEAT = "Annual occupancy may hide seasonal/weekend capacity pressure."
DEFAULT_GUESTS_PER_ROOM = 1.8
DEFAULT_AFFECTED_SHARE = 0.15
DEFAULT_PLANNING_THRESHOLD = 80.0


class MonteCarloSimulator:
    def __init__(self, duckdb_path: Path = DUCKDB_PATH):
        self.duckdb_path = duckdb_path
        self._load_data()

    def _load_data(self):
        con = duckdb.connect(str(self.duckdb_path), read_only=True)
        self.df_state = con.execute("SELECT * FROM state_year WHERE year = 2025").df().set_index("state")
        self.df_od = con.execute("SELECT * FROM origin_destination WHERE year = 2025").df()

        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if "product_value_summary" in tables:
            vai_res = con.execute(
                "SELECT post_recovery_median_vai FROM product_value_summary WHERE product_id = 'accommodation'"
            ).fetchone()
            self.national_accom_vai = float(vai_res[0]) if (vai_res and vai_res[0]) else None
        else:
            self.national_accom_vai = None

        if "accommodation_capacity" in tables:
            self.df_cap = con.execute("SELECT * FROM accommodation_capacity").df().set_index("state")
        else:
            self.df_cap = pd.DataFrame()

        # Sprint D / Plan Section 17.1: Calibrate data-derived empirical uncertainty from historical panels
        if "state_panel_year" in tables:
            df_sp = con.execute("""
                SELECT state, year, alos_days, spend_per_night_rm, aor_pct
                FROM state_panel_year
                WHERE year NOT IN (2020, 2021)
            """).df()
            state_vars = {}
            for st, grp in df_sp.groupby("state"):
                values = grp["spend_per_night_rm"].replace([np.inf, -np.inf], np.nan).dropna()
                values = values[values > 0]
                state_vars[st] = {
                    "spend_cv": float(values.std() / values.mean()) if len(values) >= 3 else None,
                    "sample_count": len(values),
                }
            self.state_historical_vars = state_vars
        else:
            self.state_historical_vars = {}

        if "tourism_product_year" in tables:
            df_vai = con.execute("""
                SELECT year, vai FROM tourism_product_year
                WHERE product = 'Accommodation services' AND year != 2021
            """).df()
            if not df_vai.empty and len(df_vai) > 2:
                self.national_vai_sd = float(df_vai["vai"].std())
            else:
                self.national_vai_sd = None
        else:
            self.national_vai_sd = None

        con.close()

    def _get_destination_baseline(self, destination: str) -> Dict[str, Any]:
        if destination not in self.df_state.index:
            raise ValueError(f"Destination '{destination}' not found in state data.")
        row = self.df_state.loc[destination]

        alos = None
        for c in ["alos_days", "alos"]:
            if c in row and pd.notnull(row[c]) and float(row[c]) > 0:
                alos = float(row[c])
                break

        spend_night = None
        for c in ["spend_per_night_rm", "spend_per_night"]:
            if c in row and pd.notnull(row[c]) and float(row[c]) > 0:
                spend_night = float(row[c])
                break

        base_aor, avail_rooms = None, None
        if not self.df_cap.empty and destination in self.df_cap.index:
            cap_row = self.df_cap.loc[destination]
            for c in ["aor_2025_pct", "aor_2024_pct"]:
                if c in cap_row and pd.notnull(cap_row[c]) and 0 <= float(cap_row[c]) <= 100:
                    base_aor = float(cap_row[c])
                    break
            for c in ["hotel_rooms_2025", "dts_rooms_2025", "hotel_rooms_2024"]:
                if c in cap_row and pd.notnull(cap_row[c]) and float(cap_row[c]) > 0:
                    avail_rooms = float(cap_row[c])
                    break

        var_info = self.state_historical_vars.get(destination, {})
        return {
            "alos": alos, "spend_per_night": spend_night,
            "base_aor": base_aor, "avail_rooms": avail_rooms,
            "spend_cv": var_info.get("spend_cv"),
            "sample_count": var_info.get("sample_count", 0),
        }

    def simulate_corridor_uncertainty(
        self,
        origin: str,
        destination: str,
        delta_alos: float = 0.5,
        affected_share: float = DEFAULT_AFFECTED_SHARE,
        guests_per_room: float = DEFAULT_GUESTS_PER_ROOM,
        planning_threshold: float = DEFAULT_PLANNING_THRESHOLD,
        n_simulations: int = 10000,
        seed: Optional[int] = 42,
    ) -> Dict[str, Any]:
        """Runs Monte Carlo simulation for an origin-destination corridor stay-extension policy."""
        limits = {"delta_alos": (delta_alos, 0, 2.5), "affected_share": (affected_share, 0, 1),
                  "guests_per_room": (guests_per_room, 0.1, 10), "planning_threshold": (planning_threshold, 0.1, 100)}
        for name, (value, lower, upper) in limits.items():
            if not np.isfinite(value) or not lower <= value <= upper:
                raise ValueError(f"{name} must be finite and between {lower} and {upper}")
        if isinstance(n_simulations, bool) or not isinstance(n_simulations, int) or n_simulations <= 0:
            raise ValueError("n_simulations must be a positive integer")
        rng = np.random.default_rng(seed)

        dest_meta = self._get_destination_baseline(destination)
        base_spend = dest_meta["spend_per_night"]
        base_alos = dest_meta["alos"]
        base_aor = dest_meta["base_aor"]
        avail_rooms = dest_meta["avail_rooms"]

        if base_spend is None or base_alos is None or self.national_accom_vai is None or dest_meta["spend_cv"] is None or self.national_vai_sd is None:
            return {
                "status": "UNAVAILABLE",
                "error": "missing baseline empirical data",
                "reason": f"Destination '{destination}' lacks baseline ALOS, spend, VAI, or at least three historical calibration observations.",
                "disclaimer": MANDATORY_DISCLAIMER,
                "evidence_status": "insufficient_data"
            }

        # Fetch corridor flow
        match = self.df_od[(self.df_od["origin"] == origin) & (self.df_od["destination"] == destination)]
        if match.empty:
            raise ValueError(f"Corridor '{origin}' -> '{destination}' not found in 2025 DTS flow matrix.")
        flow_thousands = float(match.iloc[0]["tourist_flow_thousands"])
        tourist_flow = flow_thousands * 1000.0

        if not np.isfinite(tourist_flow) or tourist_flow < 0:
            raise ValueError("Corridor flow must be finite and non-negative")

        def truncated(location, scale, lower, upper):
            if scale == 0:
                return np.full(n_simulations, location)
            return stats.truncnorm.rvs((lower-location)/scale, (upper-location)/scale,
                                      loc=location, scale=scale, size=n_simulations, random_state=rng)

        # Policy distributions are sensitivity assumptions; zero means no intervention.
        draws_affected_share = (np.zeros(n_simulations) if affected_share == 0 else
                                truncated(affected_share, 0.04, 0, 1))
        scale_alos = delta_alos * 0.15
        draws_delta_alos = (np.zeros(n_simulations) if delta_alos == 0 else
                           truncated(delta_alos, scale_alos, 0, 2.5))
        # Convert observed coefficient of variation into log-normal sigma exactly.
        spend_cv = float(dest_meta["spend_cv"])
        sigma_spend = float(np.sqrt(np.log1p(spend_cv ** 2)))
        mu_ln = np.log(base_spend) - 0.5 * sigma_spend ** 2
        draws_spend = rng.lognormal(mu_ln, sigma_spend, n_simulations)
        draws_guests_per_room = truncated(guests_per_room, 0.12, 0.1, 10)
        scale_vai = float(self.national_vai_sd)
        draws_vai = truncated(self.national_accom_vai, scale_vai, 0, 1)

        # Calculations across draws
        draws_nights = tourist_flow * draws_affected_share * draws_delta_alos
        draws_spend_m = (draws_nights * draws_spend) / 1_000_000.0
        draws_gva_m = draws_spend_m * draws_vai

        # Capacity calculations
        if avail_rooms and avail_rooms > 0 and base_aor is not None:
            draws_room_nights = draws_nights / draws_guests_per_room
            draws_delta_aor = (draws_room_nights / (365.0 * avail_rooms)) * 100.0
            draws_implied_aor = base_aor + draws_delta_aor
            prob_breach = float(np.mean(draws_implied_aor > planning_threshold))
        else:
            draws_implied_aor = None
            prob_breach = None

        def calc_quantiles(arr: np.ndarray) -> Dict[str, float]:
            return {
                "p10": round(float(np.percentile(arr, 10)), 2),
                "p25": round(float(np.percentile(arr, 25)), 2),
                "p50": round(float(np.percentile(arr, 50)), 2),
                "p75": round(float(np.percentile(arr, 75)), 2),
                "p90": round(float(np.percentile(arr, 90)), 2),
            }

        # Distribution histogram for charting (20 bins)
        hist_gva, edges_gva = np.histogram(draws_gva_m, bins=20)
        distribution_gva = [
            {"bin_mid": round(float((edges_gva[i] + edges_gva[i + 1]) / 2.0), 2), "frequency": int(hist_gva[i])}
            for i in range(len(hist_gva))
        ]

        uncertainty_provenance = {
            "data_uncertainty": {
                "spend_per_night_cv": round(spend_cv, 4),
                "vai_historical_sd": round(scale_vai, 4),
                "spend_sample_count": dest_meta["sample_count"],
                "dispersion_estimator": "sample standard deviation / mean (ddof=1); no clipping",
                "price_basis": "nominal RM; includes historical price changes",
                "capacity_uncertainty": "baseline occupancy fixed, not sampled",
                "interpretation": "Historical variability sensitivity, not campaign effectiveness or a confidence interval",
                "dependence_assumption": "Independent parameter draws",
                "minimum_observations": 3,
                "calibration_source": "DOSM State Panel (state_panel_year 2018-2025) & National TSA (tourism_product_year 2015-2025 excl. 2021 lockdown anomaly)",
                "status": "data_calibrated"
            },
            "policy_uncertainty": {
                "affected_share": {
                    "distribution": "truncated_normal",
                    "location": affected_share,
                    "sd": 0.04,
                    "bounds": [0, 1],
                    "status": "policy_assumption"
                },
                "delta_alos": {
                    "distribution": "truncated_normal",
                    "location": delta_alos,
                    "sd": round(scale_alos, 4),
                    "bounds": [0, 2.5],
                    "status": "policy_target"
                },
                "guests_per_room": {
                    "distribution": "truncated_normal",
                    "location": guests_per_room,
                    "sd": 0.12,
                    "bounds": [0.1, 10],
                    "status": "scenario_assumption"
                }
            }
        }

        return {
            "origin": origin,
            "destination": destination,
            "n_simulations": n_simulations,
            "seed": seed,
            "baseline_year": 2025,
            "parameters": {
                "tourist_flow_thousands": flow_thousands,
                "input_delta_alos": delta_alos,
                "input_affected_share": affected_share,
                "input_guests_per_room": guests_per_room,
                "planning_threshold_pct": planning_threshold,
            },
            "percentiles": {
                "additional_nights": {
                    "p10": round(float(np.percentile(draws_nights, 10)), 0),
                    "p50": round(float(np.percentile(draws_nights, 50)), 0),
                    "p90": round(float(np.percentile(draws_nights, 90)), 0),
                },
                "additional_spend_rm_m": calc_quantiles(draws_spend_m),
                "potential_gva_rm_m": calc_quantiles(draws_gva_m),
                "projected_aor_pct": calc_quantiles(draws_implied_aor) if draws_implied_aor is not None else None,
            },
            "mean": {
                "additional_nights": round(float(np.mean(draws_nights)), 0),
                "additional_spend_rm_m": round(float(np.mean(draws_spend_m)), 2),
                "potential_gva_rm_m": round(float(np.mean(draws_gva_m)), 2),
                "projected_aor_pct": round(float(np.mean(draws_implied_aor)), 2) if draws_implied_aor is not None else None,
            },
            "std": {
                "additional_spend_rm_m": round(float(np.std(draws_spend_m)), 2),
                "potential_gva_rm_m": round(float(np.std(draws_gva_m)), 2),
                "projected_aor_pct": round(float(np.std(draws_implied_aor)), 2) if draws_implied_aor is not None else None,
            },
            "prob_capacity_breach": round(prob_breach, 4) if prob_breach is not None else None,
            "capacity_status": "observed" if prob_breach is not None else "unavailable",
            "distribution": {
                "gva_density": distribution_gva,
            },
            "uncertainty_provenance": uncertainty_provenance,
            "disclaimer": MANDATORY_DISCLAIMER,
            "seasonal_caveat": SEASONAL_CAPACITY_CAVEAT,
        }
