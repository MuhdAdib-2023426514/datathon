"""
Tourism Policy Scenario Simulator Engine (Stage F & Capacity-Constrained Feasibility)
Simulates the economic potential of converting visitor demand into longer stays
and overnight accommodation value under transparent, deterministic equations.

Includes:
  1. Incremental Tourist Nights & Accommodation Expenditure.
  2. Potential Attributable Value Added (TSA VAI proxy: 0.8579).
  3. Hotel Room Capacity Feasibility & Saturation Check (Implied AOR > 80% threshold).

Mandatory Policy Guardrail:
Every scenario card, report, and visualization output must display:
"Scenario estimate, not a causal forecast."
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
import duckdb
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

MANDATORY_DISCLAIMER = "Scenario estimate, not a causal forecast."
ACCOMMODATION_VAI = 0.8579
CAPACITY_SATURATION_THRESHOLD_AOR = 80.0
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

        # Fetch national accommodation VAI
        vai_res = con.execute(
            "SELECT post_recovery_median_vai FROM product_value_summary WHERE product_id = 'accommodation'"
        ).fetchone()
        self.national_accom_vai = float(vai_res[0]) if vai_res else ACCOMMODATION_VAI

        # Fetch hotel capacity metrics if table exists
        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if "accommodation_capacity" in tables:
            self.df_cap = con.execute("SELECT * FROM accommodation_capacity").df().set_index("state")
        else:
            self.df_cap = pd.DataFrame()
        con.close()

    def simulate_corridor(
        self,
        origin: str,
        destination: str,
        delta_alos: float = 0.5,
        day_trip_conversion_pct: float = 0.0,
    ) -> Dict[str, Union[str, float, Dict]]:
        """
        Simulates the economic opportunity and capacity feasibility for a specific corridor.
        
        Parameters:
            origin: Name of the origin feeder state.
            destination: Name of the destination state.
            delta_alos: Incremental increase in length of stay (0.0 to 3.0 nights).
            day_trip_conversion_pct: Percentage of excursionists converted to overnight (0 to 100%).
            
        Returns:
            Dictionary with baseline metrics, simulated gains, capacity check, and mandatory disclaimer.
        """
        if delta_alos < 0 or delta_alos > 3.0:
            raise ValueError("delta_alos must be between 0.0 and 3.0 nights.")
        if day_trip_conversion_pct < 0 or day_trip_conversion_pct > 100.0:
            raise ValueError("day_trip_conversion_pct must be between 0.0% and 100.0%.")

        # Destination baseline
        dest_rows = self.df_state[self.df_state["state"] == destination]
        if dest_rows.empty:
            raise ValueError(f"Destination state '{destination}' not found.")
        dest_data = dest_rows.iloc[0]

        # Corridor flow baseline
        flow_rows = self.df_od[(self.df_od["origin"] == origin) & (self.df_od["destination"] == destination)]
        flow_k = flow_rows["tourist_flow_thousands"].values[0] if not flow_rows.empty else 0.0

        # Baseline parameters
        baseline_tourists = flow_k * 1000.0
        baseline_alos = float(dest_data["alos_days"])
        spend_per_night = float(dest_data["spend_per_night_rm"])
        dest_excursionists = float(dest_data["excursionists_thousands"]) * 1000.0

        # 1. ALOS Extension Simulation
        # Additional Tourist Nights = TouristFlow * DeltaALOS
        add_nights_alos = baseline_tourists * delta_alos
        add_spend_alos = add_nights_alos * spend_per_night

        # 2. Day-Trip to Overnight Conversion Simulation
        converted_tourists = dest_excursionists * (day_trip_conversion_pct / 100.0)
        new_nights_converted = converted_tourists * (baseline_alos + delta_alos)
        add_spend_converted = new_nights_converted * spend_per_night

        # Total additions
        total_additional_nights = add_nights_alos + new_nights_converted
        total_additional_spend_rm = add_spend_alos + add_spend_converted
        total_additional_spend_m = total_additional_spend_rm / 1e6

        # Potential Additional Value Added (Analytical Proxy)
        potential_value_added_rm = total_additional_spend_rm * self.national_accom_vai
        potential_value_added_m = potential_value_added_rm / 1e6

        # 3. Hotel Room Capacity Saturation & Feasibility Check
        dest_cap_row = self.df_cap.loc[destination] if not self.df_cap.empty and destination in self.df_cap.index else None
        
        base_aor = (
            float(dest_cap_row["aor_2025_pct"])
            if dest_cap_row is not None and "aor_2025_pct" in dest_cap_row and pd.notnull(dest_cap_row["aor_2025_pct"])
            else (float(dest_cap_row["aor_2024_pct"]) if dest_cap_row is not None and pd.notnull(dest_cap_row.get("aor_2024_pct")) else 50.0)
        )
        avail_rooms = (
            float(dest_cap_row["dts_rooms_2025"])
            if dest_cap_row is not None and pd.notnull(dest_cap_row.get("dts_rooms_2025"))
            else (float(dest_cap_row["hotel_rooms_2025"]) if dest_cap_row is not None and "hotel_rooms_2025" in dest_cap_row and pd.notnull(dest_cap_row["hotel_rooms_2025"]) else 15000.0)
        )

        daily_additional_room_demand = total_additional_nights / (365.0 * AVERAGE_GUESTS_PER_ROOM)
        delta_aor_pct = (daily_additional_room_demand / avail_rooms) * 100.0 if avail_rooms > 0 else 0.0
        implied_aor = round(base_aor + delta_aor_pct, 2)

        if implied_aor > CAPACITY_SATURATION_THRESHOLD_AOR:
            capacity_status = "Capacity Constraint Alert (>80% Saturation) — Requires supply expansion or off-peak weekday shifting"
            is_capacity_constrained = True
        else:
            capacity_status = "Feasible (Within existing hotel capacity)"
            is_capacity_constrained = False

        return {
            "origin": origin,
            "destination": destination,
            "inputs": {
                "delta_alos_nights": delta_alos,
                "day_trip_conversion_pct": day_trip_conversion_pct,
                "accommodation_vai_used": self.national_accom_vai,
            },
            "baseline": {
                "corridor_tourists": round(baseline_tourists, 0),
                "destination_alos_days": round(baseline_alos, 2),
                "spend_per_night_rm": round(spend_per_night, 2),
                "destination_total_accom_expenditure_rm_m": float(dest_data["accommodation_expenditure_rm_million"]),
                "destination_baseline_aor_pct": round(base_aor, 1),
                "destination_available_rooms": int(avail_rooms),
            },
            "simulated_impact": {
                "additional_tourist_nights": round(total_additional_nights, 0),
                "additional_accommodation_spend_rm_million": round(total_additional_spend_m, 2),
                "potential_additional_value_added_rm_million": round(potential_value_added_m, 2),
            },
            "capacity_feasibility": {
                "daily_rooms_demanded": round(daily_additional_room_demand, 1),
                "delta_aor_pct": round(delta_aor_pct, 2),
                "implied_destination_aor_pct": implied_aor,
                "saturation_threshold_pct": CAPACITY_SATURATION_THRESHOLD_AOR,
                "is_capacity_constrained": is_capacity_constrained,
                "status": capacity_status,
            },
            "disclaimer": MANDATORY_DISCLAIMER,
        }

    def simulate_state_priority_portfolio(
        self, destination: str, delta_alos: float = 0.3
    ) -> pd.DataFrame:
        """
        Simulates impact across all inter-state feeder origins for a given destination.
        """
        dest_od = self.df_od[(self.df_od["destination"] == destination) & (self.df_od["is_interstate"])].copy()
        results = []

        for _, row in dest_od.iterrows():
            sim = self.simulate_corridor(
                origin=row["origin"],
                destination=destination,
                delta_alos=delta_alos,
            )
            results.append({
                "origin": row["origin"],
                "destination": destination,
                "tourist_flow_thousands": row["tourist_flow_thousands"],
                "delta_alos": delta_alos,
                "additional_nights": sim["simulated_impact"]["additional_tourist_nights"],
                "additional_spend_rm_m": sim["simulated_impact"]["additional_accommodation_spend_rm_million"],
                "potential_value_added_rm_m": sim["simulated_impact"]["potential_additional_value_added_rm_million"],
                "implied_aor_pct": sim["capacity_feasibility"]["implied_destination_aor_pct"],
                "capacity_alert": sim["capacity_feasibility"]["is_capacity_constrained"],
            })

        df_res = pd.DataFrame(results).sort_values("additional_spend_rm_m", ascending=False)
        return df_res


if __name__ == "__main__":
    sim = ScenarioSimulator()

    # Test Scenario 1: Selangor -> Melaka (+0.5 nights)
    s1 = sim.simulate_corridor("Selangor", "Melaka", delta_alos=0.5)
    print("\n" + "=" * 80)
    print("SCENARIO SIMULATION: Selangor -> Melaka (+0.5 Nights ALOS)")
    print("=" * 80)
    print(f"Origin Feeder: {s1['origin']} | Destination: {s1['destination']}")
    print(f"Baseline Tourists: {s1['baseline']['corridor_tourists']:,.0f} | Spend/Night: RM {s1['baseline']['spend_per_night_rm']:.2f}")
    print(f"Additional Nights: +{s1['simulated_impact']['additional_tourist_nights']:,.0f} nights")
    print(f"Additional Spend:  +RM {s1['simulated_impact']['additional_accommodation_spend_rm_million']:.2f} Million")
    print(f"Potential GVA:     +RM {s1['simulated_impact']['potential_additional_value_added_rm_million']:.2f} Million")
    print(f"Baseline AOR:      {s1['baseline']['destination_baseline_aor_pct']}% | Implied AOR: {s1['capacity_feasibility']['implied_destination_aor_pct']}%")
    print(f"Capacity Status:   {s1['capacity_feasibility']['status']}")
    print(f"Notice:            {s1['disclaimer']}")
