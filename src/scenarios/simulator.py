"""
Tourism Policy Scenario Simulator Engine (Stage F & Capacity-Constrained Feasibility)
Simulates the economic potential of converting visitor demand into longer stays
and overnight accommodation value under transparent, deterministic equations.

Includes:
  1. Decoupled Corridor ALOS Extension:
     Operates at origin-destination level using verified corridor flows.
  2. Decoupled Destination Day-Trip Conversion:
     Operates at destination level on verified excursionist pools without double counting.
  3. Multi-Corridor Portfolio Aggregation:
     Sums incremental daily room demand across all feeder corridors to evaluate true
     aggregate destination hotel occupancy and physical capacity saturation.
  4. Saturation Tiers:
     - Normal (< 70% AOR)
     - Planning Watch (70% - 80% AOR)
     - Severe Saturation (> 80% AOR)
     - Physical Capacity Breach (> 100% AOR)

Mandatory Policy Guardrail (AGENTS.md Section 7, 9, 12):
Every scenario card, report, and visualization output must display:
"Scenario estimate, not a causal forecast."
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
import duckdb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

MANDATORY_DISCLAIMER = "Scenario estimate, not a causal forecast."
DEFAULT_ACCOMMODATION_VAI = 0.8579
AVERAGE_GUESTS_PER_ROOM = 1.8


class ScenarioSimulator:
    def __init__(self, duckdb_path: Path = DUCKDB_PATH):
        self.duckdb_path = duckdb_path
        self._load_baseline_data()

    def _load_baseline_data(self):
        """Loads clean baseline data from DuckDB."""
        con = duckdb.connect(str(self.duckdb_path), read_only=True)
        self.df_state = con.execute("SELECT * FROM state_year").df()
        self.df_od = con.execute("SELECT * FROM origin_destination").df()

        # Valid states
        self.valid_states = set(self.df_state["state"].unique())

        # Fetch national accommodation VAI
        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if "product_value_summary" in tables:
            vai_res = con.execute(
                "SELECT post_recovery_median_vai FROM product_value_summary WHERE product_id = 'accommodation'"
            ).fetchone()
            self.national_accom_vai = float(vai_res[0]) if (vai_res and vai_res[0]) else DEFAULT_ACCOMMODATION_VAI
        else:
            self.national_accom_vai = DEFAULT_ACCOMMODATION_VAI

        # Fetch hotel capacity metrics
        if "accommodation_capacity" in tables:
            self.df_cap = con.execute("SELECT * FROM accommodation_capacity").df().set_index("state")
        else:
            self.df_cap = pd.DataFrame()
        con.close()

    def _get_capacity_metrics(self, destination: str) -> Tuple[Optional[float], Optional[float]]:
        """Retrieves verified baseline AOR (%) and available rooms count without invented fallbacks."""
        if self.df_cap.empty or destination not in self.df_cap.index:
            return None, None

        row = self.df_cap.loc[destination]
        # Base AOR precedence
        base_aor = None
        for col in ["aor_2025_pct", "aor_2024_pct"]:
            if col in row and pd.notnull(row[col]) and float(row[col]) > 0:
                base_aor = float(row[col])
                break

        # Available rooms precedence
        avail_rooms = None
        for col in ["hotel_rooms_2025", "dts_rooms_2025", "hotel_rooms_2024"]:
            if col in row and pd.notnull(row[col]) and float(row[col]) > 0:
                avail_rooms = float(row[col])
                break

        return base_aor, avail_rooms

    def _evaluate_capacity_status(self, implied_aor: Optional[float]) -> Tuple[bool, str, str]:
        """Classifies saturation status into 4 transparent planning tiers."""
        if implied_aor is None or np.isnan(implied_aor):
            return False, "Unknown", "Unknown (Hotel Capacity Data Unavailable)"
        if implied_aor > 100.0:
            return True, "Physical Breach", f"Physical Capacity Breach ({implied_aor:.1f}% AOR > 100% Ceiling) — Exceeds total available hotel room inventory"
        elif implied_aor > 80.0:
            return True, "Severe Saturation", f"Severe Capacity Saturation ({implied_aor:.1f}% AOR > 80% Threshold) — Requires room supply expansion or off-peak weekday redistribution"
        elif implied_aor >= 70.0:
            return False, "Planning Watch", f"Planning Watch ({implied_aor:.1f}% AOR in 70-80% range) — Tightening headroom during peak periods"
        else:
            return False, "Normal", f"Feasible ({implied_aor:.1f}% AOR within sustainable hotel capacity)"

    def simulate_corridor(
        self,
        origin: str,
        destination: str,
        delta_alos: float = 0.5,
    ) -> Dict[str, Union[str, float, Dict]]:
        """
        Simulates the economic opportunity and capacity feasibility for a specific origin-destination corridor.
        Strictly decoupled from destination day-trip pools to prevent double counting.
        """
        if origin not in self.valid_states:
            raise ValueError(f"Invalid origin state: '{origin}'. Must be one of 16 Malaysian states.")
        if destination not in self.valid_states:
            raise ValueError(f"Invalid destination state: '{destination}'. Must be one of 16 Malaysian states.")
        if delta_alos < 0 or delta_alos > 3.0:
            raise ValueError("delta_alos must be between 0.0 and 3.0 nights.")

        # Destination baseline
        dest_rows = self.df_state[self.df_state["state"] == destination]
        if dest_rows.empty:
            raise ValueError(f"Destination state '{destination}' not found in state baseline.")
        dest_data = dest_rows.iloc[0]

        # Corridor flow baseline
        flow_rows = self.df_od[(self.df_od["origin"] == origin) & (self.df_od["destination"] == destination)]
        flow_k = float(flow_rows["tourist_flow_thousands"].values[0]) if not flow_rows.empty else 0.0

        baseline_tourists = flow_k * 1000.0
        baseline_alos = float(dest_data["alos_days"])
        spend_per_night = float(dest_data["spend_per_night_rm"])

        # 1. ALOS Extension Simulation
        # Additional Tourist Nights = TouristFlow * DeltaALOS
        total_additional_nights = baseline_tourists * delta_alos
        total_additional_spend_rm = total_additional_nights * spend_per_night
        total_additional_spend_m = total_additional_spend_rm / 1e6
        potential_value_added_rm = total_additional_spend_rm * self.national_accom_vai
        potential_value_added_m = potential_value_added_rm / 1e6

        # 2. Hotel Room Capacity Check
        base_aor, avail_rooms = self._get_capacity_metrics(destination)
        if avail_rooms and avail_rooms > 0 and base_aor is not None:
            daily_room_demand = total_additional_nights / (365.0 * AVERAGE_GUESTS_PER_ROOM)
            delta_aor_pct = (daily_room_demand / avail_rooms) * 100.0
            implied_aor = round(base_aor + delta_aor_pct, 2)
        else:
            daily_room_demand = None
            delta_aor_pct = None
            implied_aor = None

        is_constrained, tier, status_msg = self._evaluate_capacity_status(implied_aor)

        return {
            "origin": origin,
            "destination": destination,
            "inputs": {
                "delta_alos_nights": delta_alos,
                "accommodation_vai_used": self.national_accom_vai,
            },
            "baseline": {
                "corridor_tourists": round(baseline_tourists, 0),
                "destination_alos_days": round(baseline_alos, 2),
                "spend_per_night_rm": round(spend_per_night, 2),
                "destination_total_accom_expenditure_rm_m": float(dest_data["accommodation_expenditure_rm_million"]),
                "destination_baseline_aor_pct": round(base_aor, 1) if base_aor else None,
                "destination_available_rooms": int(avail_rooms) if avail_rooms else None,
            },
            "simulated_impact": {
                "additional_tourist_nights": round(total_additional_nights, 0),
                "additional_accommodation_spend_rm_million": round(total_additional_spend_m, 2),
                "potential_additional_value_added_rm_million": round(potential_value_added_m, 2),
            },
            "capacity_feasibility": {
                "daily_rooms_demanded": round(daily_room_demand, 1) if daily_room_demand else None,
                "delta_aor_pct": round(delta_aor_pct, 2) if delta_aor_pct else None,
                "implied_destination_aor_pct": implied_aor,
                "saturation_tier": tier,
                "is_capacity_constrained": is_constrained,
                "status": status_msg,
            },
            "disclaimer": MANDATORY_DISCLAIMER,
        }

    def simulate_destination_daytrip(
        self,
        destination: str,
        conversion_pct: float = 1.0,
        converted_alos: Optional[float] = None,
    ) -> Dict[str, Union[str, float, Dict]]:
        """
        Simulates converting a percentage of destination-level excursionists into overnight tourists.
        Operates on the destination excursionist pool once (strictly conserving volume).
        """
        if destination not in self.valid_states:
            raise ValueError(f"Invalid destination state: '{destination}'.")
        if conversion_pct < 0 or conversion_pct > 100.0:
            raise ValueError("conversion_pct must be between 0.0% and 100.0%.")

        dest_rows = self.df_state[self.df_state["state"] == destination]
        if dest_rows.empty:
            raise ValueError(f"Destination state '{destination}' not found.")
        dest_data = dest_rows.iloc[0]

        dest_excursionists = float(dest_data["excursionists_thousands"]) * 1000.0
        spend_per_night = float(dest_data["spend_per_night_rm"])
        target_alos = converted_alos if converted_alos else float(dest_data["alos_days"])

        converted_tourists = dest_excursionists * (conversion_pct / 100.0)
        new_nights = converted_tourists * target_alos
        add_spend_rm = new_nights * spend_per_night
        add_spend_m = add_spend_rm / 1e6
        potential_gva_m = (add_spend_rm * self.national_accom_vai) / 1e6

        base_aor, avail_rooms = self._get_capacity_metrics(destination)
        if avail_rooms and avail_rooms > 0 and base_aor is not None:
            daily_room_demand = new_nights / (365.0 * AVERAGE_GUESTS_PER_ROOM)
            delta_aor_pct = (daily_room_demand / avail_rooms) * 100.0
            implied_aor = round(base_aor + delta_aor_pct, 2)
        else:
            daily_room_demand = None
            delta_aor_pct = None
            implied_aor = None

        is_constrained, tier, status_msg = self._evaluate_capacity_status(implied_aor)

        return {
            "destination": destination,
            "inputs": {
                "conversion_pct": conversion_pct,
                "target_stay_duration_nights": target_alos,
            },
            "baseline": {
                "total_excursionists": round(dest_excursionists, 0),
                "spend_per_night_rm": round(spend_per_night, 2),
                "destination_baseline_aor_pct": round(base_aor, 1) if base_aor else None,
                "destination_available_rooms": int(avail_rooms) if avail_rooms else None,
            },
            "simulated_impact": {
                "newly_converted_tourists": round(converted_tourists, 0),
                "additional_tourist_nights": round(new_nights, 0),
                "additional_accommodation_spend_rm_million": round(add_spend_m, 2),
                "potential_additional_value_added_rm_million": round(potential_gva_m, 2),
            },
            "capacity_feasibility": {
                "daily_rooms_demanded": round(daily_room_demand, 1) if daily_room_demand else None,
                "delta_aor_pct": round(delta_aor_pct, 2) if delta_aor_pct else None,
                "implied_destination_aor_pct": implied_aor,
                "saturation_tier": tier,
                "is_capacity_constrained": is_constrained,
                "status": status_msg,
            },
            "disclaimer": MANDATORY_DISCLAIMER,
        }

    def simulate_state_priority_portfolio(
        self, destination: str, delta_alos: float = 0.5
    ) -> Dict[str, Union[pd.DataFrame, Dict]]:
        """
        Simulates impact across all inter-state feeder corridors to a destination,
        aggregating incremental room demand across all corridors to assess destination portfolio capacity.
        """
        dest_od = self.df_od[(self.df_od["destination"] == destination) & (self.df_od["is_interstate"])].copy()
        corridor_results = []
        total_portfolio_nights = 0.0
        total_portfolio_spend_m = 0.0
        total_portfolio_gva_m = 0.0

        for _, row in dest_od.iterrows():
            sim = self.simulate_corridor(
                origin=row["origin"],
                destination=destination,
                delta_alos=delta_alos,
            )
            add_nights = sim["simulated_impact"]["additional_tourist_nights"]
            add_spend_m = sim["simulated_impact"]["additional_accommodation_spend_rm_million"]
            pot_gva_m = sim["simulated_impact"]["potential_additional_value_added_rm_million"]

            total_portfolio_nights += add_nights
            total_portfolio_spend_m += add_spend_m
            total_portfolio_gva_m += pot_gva_m

            corridor_results.append({
                "origin": row["origin"],
                "destination": destination,
                "tourist_flow_thousands": row["tourist_flow_thousands"],
                "delta_alos": delta_alos,
                "additional_nights": add_nights,
                "additional_spend_rm_m": add_spend_m,
                "potential_value_added_rm_m": pot_gva_m,
            })

        df_corridors = pd.DataFrame(corridor_results).sort_values("additional_spend_rm_m", ascending=False)

        # Portfolio aggregate capacity assessment
        base_aor, avail_rooms = self._get_capacity_metrics(destination)
        if avail_rooms and avail_rooms > 0 and base_aor is not None:
            portfolio_daily_room_demand = total_portfolio_nights / (365.0 * AVERAGE_GUESTS_PER_ROOM)
            portfolio_delta_aor = (portfolio_daily_room_demand / avail_rooms) * 100.0
            portfolio_implied_aor = round(base_aor + portfolio_delta_aor, 2)
        else:
            portfolio_daily_room_demand = None
            portfolio_delta_aor = None
            portfolio_implied_aor = None

        is_constrained, tier, status_msg = self._evaluate_capacity_status(portfolio_implied_aor)

        portfolio_summary = {
            "destination": destination,
            "total_active_feeders": len(dest_od),
            "total_additional_nights": round(total_portfolio_nights, 0),
            "total_additional_spend_rm_million": round(total_portfolio_spend_m, 2),
            "total_potential_value_added_rm_million": round(total_portfolio_gva_m, 2),
            "portfolio_daily_rooms_demanded": round(portfolio_daily_room_demand, 1) if portfolio_daily_room_demand else None,
            "portfolio_delta_aor_pct": round(portfolio_delta_aor, 2) if portfolio_delta_aor else None,
            "destination_baseline_aor_pct": round(base_aor, 1) if base_aor else None,
            "destination_implied_portfolio_aor_pct": portfolio_implied_aor,
            "destination_available_rooms": int(avail_rooms) if avail_rooms else None,
            "saturation_tier": tier,
            "is_capacity_constrained": is_constrained,
            "status": status_msg,
            "disclaimer": MANDATORY_DISCLAIMER,
        }

        return {
            "corridors": df_corridors,
            "portfolio_summary": portfolio_summary,
        }


if __name__ == "__main__":
    sim = ScenarioSimulator()

    # Test Scenario 1: Corridor ALOS (Selangor -> Melaka, +0.5 nights)
    s1 = sim.simulate_corridor("Selangor", "Melaka", delta_alos=0.5)
    print("\n" + "=" * 80)
    print("SCENARIO SIMULATION 1: Corridor ALOS Extension (Selangor -> Melaka +0.5 Nights)")
    print("=" * 80)
    print(f"Origin: {s1['origin']} -> Destination: {s1['destination']}")
    print(f"Additional Nights: +{s1['simulated_impact']['additional_tourist_nights']:,.0f}")
    print(f"Additional Spend:  +RM {s1['simulated_impact']['additional_accommodation_spend_rm_million']:.2f} Million")
    print(f"Potential GVA:     +RM {s1['simulated_impact']['potential_additional_value_added_rm_million']:.2f} Million")
    print(f"Capacity Status:   {s1['capacity_feasibility']['status']}")

    # Test Scenario 2: Destination Day-Trip Conversion (Melaka 1% Conversion)
    s2 = sim.simulate_destination_daytrip("Melaka", conversion_pct=1.0)
    print("\n" + "=" * 80)
    print("SCENARIO SIMULATION 2: Destination Day-Trip Conversion (Melaka 1% Conversion)")
    print("=" * 80)
    print(f"Destination: {s2['destination']} | Excursionists: {s2['baseline']['total_excursionists']:,.0f}")
    print(f"Converted Tourists: +{s2['simulated_impact']['newly_converted_tourists']:,.0f}")
    print(f"Additional Spend:   +RM {s2['simulated_impact']['additional_accommodation_spend_rm_million']:.2f} Million")
    print(f"Capacity Status:    {s2['capacity_feasibility']['status']}")

    # Test Scenario 3: Destination Portfolio Assessment (Pahang all feeders +0.5 nights)
    port = sim.simulate_state_priority_portfolio("Pahang", delta_alos=0.5)
    print("\n" + "=" * 80)
    print("SCENARIO SIMULATION 3: Pahang Multi-Feeder Portfolio Aggregation (+0.5 Nights)")
    print("=" * 80)
    psum = port["portfolio_summary"]
    print(f"Destination: {psum['destination']} across {psum['total_active_feeders']} feeders")
    print(f"Total Portfolio Add Nights: +{psum['total_additional_nights']:,.0f}")
    print(f"Total Portfolio Add Spend:  +RM {psum['total_additional_spend_rm_million']:.2f} Million")
    print(f"Baseline AOR: {psum['destination_baseline_aor_pct']}% -> Implied Portfolio AOR: {psum['destination_implied_portfolio_aor_pct']}%")
    print(f"Saturation Tier: {psum['saturation_tier']}")
    print(f"Status: {psum['status']}")
    print(f"Disclaimer: {psum['disclaimer']}")
