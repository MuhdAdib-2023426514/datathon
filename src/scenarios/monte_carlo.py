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
DEFAULT_ACCOM_VAI = 0.8579
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
            self.national_accom_vai = float(vai_res[0]) if (vai_res and vai_res[0]) else DEFAULT_ACCOM_VAI
        else:
            self.national_accom_vai = DEFAULT_ACCOM_VAI

        if "accommodation_capacity" in tables:
            self.df_cap = con.execute("SELECT * FROM accommodation_capacity").df().set_index("state")
        else:
            self.df_cap = pd.DataFrame()
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
                if c in cap_row and pd.notnull(cap_row[c]) and float(cap_row[c]) > 0:
                    base_aor = float(cap_row[c])
                    break
            for c in ["hotel_rooms_2025", "dts_rooms_2025", "hotel_rooms_2024"]:
                if c in cap_row and pd.notnull(cap_row[c]) and float(cap_row[c]) > 0:
                    avail_rooms = float(cap_row[c])
                    break

        return {
            "alos": alos,
            "spend_per_night": spend_night,
            "base_aor": base_aor,
            "avail_rooms": avail_rooms,
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
        if seed is not None:
            np.random.seed(seed)

        dest_meta = self._get_destination_baseline(destination)
        base_spend = dest_meta["spend_per_night"]
        base_alos = dest_meta["alos"]
        base_aor = dest_meta["base_aor"]
        avail_rooms = dest_meta["avail_rooms"]

        if base_spend is None or base_alos is None:
            return {
                "status": "UNAVAILABLE",
                "error": "missing baseline empirical data",
                "reason": f"Destination '{destination}' lacks empirical ALOS or spend per night observation in official tables.",
                "disclaimer": MANDATORY_DISCLAIMER,
                "evidence_status": "insufficient_data"
            }

        # Fetch corridor flow
        match = self.df_od[(self.df_od["origin"] == origin) & (self.df_od["destination"] == destination)]
        if match.empty:
            raise ValueError(f"Corridor '{origin}' -> '{destination}' not found in 2025 DTS flow matrix.")
        flow_thousands = float(match.iloc[0]["tourist_flow_thousands"])
        tourist_flow = flow_thousands * 1000.0

        # Stochastic parameter sampling
        # 1. Affected share: Truncated normal around affected_share (bounds: [0.05, 0.40])
        a_share, b_share = (0.05 - affected_share) / 0.04, (0.40 - affected_share) / 0.04
        draws_affected_share = stats.truncnorm.rvs(a_share, b_share, loc=affected_share, scale=0.04, size=n_simulations)

        # 2. Delta ALOS: Truncated normal around delta_alos (bounds: [0.05, 2.5])
        scale_alos = max(0.05, delta_alos * 0.15)
        a_alos, b_alos = (0.05 - delta_alos) / scale_alos, (2.5 - delta_alos) / scale_alos
        draws_delta_alos = stats.truncnorm.rvs(a_alos, b_alos, loc=delta_alos, scale=scale_alos, size=n_simulations)

        # 3. Spend per night: Log-normal with mean equal to base_spend and CV=0.15
        mu_ln = np.log(base_spend) - 0.5 * (0.15 ** 2)
        draws_spend = np.random.lognormal(mean=mu_ln, sigma=0.15, size=n_simulations)

        # 4. Guests per room: Truncated normal around guests_per_room (bounds: [1.3, 2.4])
        a_g, b_g = (1.3 - guests_per_room) / 0.12, (2.4 - guests_per_room) / 0.12
        draws_guests_per_room = stats.truncnorm.rvs(a_g, b_g, loc=guests_per_room, scale=0.12, size=n_simulations)

        # 5. Accommodation VAI: Truncated normal around national VAI (bounds: [0.70, 0.95])
        a_v, b_v = (0.70 - self.national_accom_vai) / 0.025, (0.95 - self.national_accom_vai) / 0.025
        draws_vai = stats.truncnorm.rvs(a_v, b_v, loc=self.national_accom_vai, scale=0.025, size=n_simulations)

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
            prob_breach = 0.0

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

        return {
            "origin": origin,
            "destination": destination,
            "n_simulations": n_simulations,
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
            "prob_capacity_breach": round(prob_breach, 4),
            "distribution": {
                "gva_density": distribution_gva,
            },
            "disclaimer": MANDATORY_DISCLAIMER,
            "seasonal_caveat": SEASONAL_CAPACITY_CAVEAT,
        }
