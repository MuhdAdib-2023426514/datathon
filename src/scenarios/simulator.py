"""
Tourism Policy Scenario Simulator Engine (Stage F & Capacity-Constrained Feasibility)
Simulates the economic potential of converting visitor demand into longer stays
and overnight accommodation value under transparent, deterministic equations.

Sprint 6 Upgrades:
  1. Phase 21: One Source of Truth (deterministic Python engine providing single source)
  2. Phase 22: Scenario Affected Share (campaign reach scaling: AdditionalNights = Flow * AffectedShare * DeltaALOS)
  3. Phase 23: Correct Room-Night Capacity Conversion (AdditionalRoomNights = GuestNights / GuestsPerOccupiedRoom)
  4. Phase 24: Correct VFR Scenario Capacity (converted VFR stays generate commercial room demand & impact AOR)
  5. Phase 25: Scenario Assumption Metadata (official, derived, scenario_assumption classification)
  6. Phase 27: Capacity Sensitivity Analysis (75%, 80%, 85% planning thresholds with seasonal caveat)

Mandatory Policy Guardrail (AGENTS.md Section 7, 9, 12):
Every scenario card, report, and visualization output must display:
"Scenario estimate, not a causal forecast."
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import duckdb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"

MANDATORY_DISCLAIMER = "Scenario estimate, not a causal forecast."
SEASONAL_CAPACITY_CAVEAT = "Annual occupancy may hide seasonal/weekend capacity pressure."
DEFAULT_ACCOMMODATION_VAI = 0.8579
DEFAULT_GUESTS_PER_ROOM = 1.8
DEFAULT_AFFECTED_SHARE = 0.15
DEFAULT_HOMESTAY_DISCOUNT_FACTOR = 0.85
DEFAULT_PLANNING_THRESHOLD = 80.0


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

    def _evaluate_capacity_status(
        self, implied_aor: Optional[float], planning_threshold: float = DEFAULT_PLANNING_THRESHOLD
    ) -> Tuple[bool, str, str]:
        """Classifies saturation status into transparent planning tiers based on configurable planning threshold."""
        if implied_aor is None or np.isnan(implied_aor):
            return False, "Unknown", "Unknown (Hotel Capacity Data Unavailable)"
        if implied_aor > 100.0:
            return (
                True,
                "Physical Breach",
                f"Physical Capacity Breach ({implied_aor:.1f}% AOR > 100% Ceiling) — Exceeds total available hotel room inventory",
            )
        elif implied_aor > planning_threshold:
            return (
                True,
                "Severe Saturation",
                f"Severe Capacity Saturation ({implied_aor:.1f}% AOR > {planning_threshold:.0f}% Threshold) — Requires room supply expansion or off-peak weekday redistribution",
            )
        elif implied_aor >= (planning_threshold - 10.0):
            return (
                False,
                "Planning Watch",
                f"Planning Watch ({implied_aor:.1f}% AOR in {planning_threshold - 10.0:.0f}-{planning_threshold:.0f}% range) — Tightening headroom during peak periods",
            )
        else:
            return (
                False,
                "Normal",
                f"Feasible ({implied_aor:.1f}% AOR within sustainable hotel capacity)",
            )

    def simulate_corridor(
        self,
        origin: str,
        destination: str,
        delta_alos: float = 0.5,
        affected_share: float = 1.0,
        guests_per_room: float = DEFAULT_GUESTS_PER_ROOM,
        planning_threshold: float = DEFAULT_PLANNING_THRESHOLD,
    ) -> Dict[str, Any]:
        """
        Simulates the economic opportunity and capacity feasibility for a specific origin-destination corridor.
        Includes campaign affected share and room-night capacity conversion.
        """
        if origin not in self.valid_states:
            raise ValueError(f"Invalid origin state: '{origin}'. Must be one of 16 Malaysian states.")
        if destination not in self.valid_states:
            raise ValueError(f"Invalid destination state: '{destination}'. Must be one of 16 Malaysian states.")
        if delta_alos < 0 or delta_alos > 3.0:
            raise ValueError("delta_alos must be between 0.0 and 3.0 nights.")
        if affected_share < 0.0 or affected_share > 1.0:
            raise ValueError("affected_share must be between 0.0 and 1.0 (0% to 100%).")
        if guests_per_room <= 0:
            raise ValueError("guests_per_room must be positive.")

        # Destination baseline
        dest_rows = self.df_state[(self.df_state["state"] == destination) & (self.df_state["year"] == 2025)]
        if dest_rows.empty:
            dest_rows = self.df_state[self.df_state["state"] == destination]
        if dest_rows.empty:
            raise ValueError(f"Destination state '{destination}' not found in state baseline.")
        dest_data = dest_rows.iloc[-1]

        # Corridor flow baseline
        flow_rows = self.df_od[(self.df_od["origin"] == origin) & (self.df_od["destination"] == destination)]
        flow_k = float(flow_rows["tourist_flow_thousands"].values[0]) if not flow_rows.empty else 0.0

        baseline_tourists = flow_k * 1000.0
        baseline_alos = float(dest_data["alos_days"])
        spend_per_night = float(dest_data["spend_per_night_rm"])

        # 1. ALOS Extension Simulation with Affected Share
        # Additional Tourist Nights = TouristFlow * AffectedShare * DeltaALOS
        total_additional_nights = baseline_tourists * affected_share * delta_alos
        total_additional_spend_rm = total_additional_nights * spend_per_night
        total_additional_spend_m = total_additional_spend_rm / 1e6
        potential_value_added_rm = total_additional_spend_rm * self.national_accom_vai
        potential_value_added_m = potential_value_added_rm / 1e6

        # 2. Hotel Room Capacity Check
        base_aor, avail_rooms = self._get_capacity_metrics(destination)
        if avail_rooms and avail_rooms > 0 and base_aor is not None:
            daily_room_demand = total_additional_nights / (365.0 * guests_per_room)
            delta_aor_pct = (daily_room_demand / avail_rooms) * 100.0
            implied_aor = round(base_aor + delta_aor_pct, 2)
        else:
            daily_room_demand = None
            delta_aor_pct = None
            implied_aor = None

        is_constrained, tier, status_msg = self._evaluate_capacity_status(implied_aor, planning_threshold)

        metadata = {
            "affected_share": {"value": affected_share, "status": "scenario_assumption"},
            "guests_per_room": {"value": guests_per_room, "status": "scenario_assumption"},
            "delta_alos": {"value": delta_alos, "status": "scenario_assumption"},
            "planning_threshold": {"value": planning_threshold, "status": "scenario_assumption"},
            "baseline_tourists": {"value": round(baseline_tourists, 0), "status": "official"},
            "baseline_alos": {"value": round(baseline_alos, 2), "status": "official"},
            "baseline_aor": {"value": round(base_aor, 1) if base_aor else None, "status": "official"},
            "available_rooms": {"value": int(avail_rooms) if avail_rooms else None, "status": "official"},
            "spend_per_night": {"value": round(spend_per_night, 2), "status": "derived"},
            "accommodation_vai": {"value": round(self.national_accom_vai, 4), "status": "official"},
        }

        return {
            "origin": origin,
            "destination": destination,
            "inputs": {
                "delta_alos_nights": delta_alos,
                "affected_share": affected_share,
                "guests_per_room": guests_per_room,
                "planning_threshold": planning_threshold,
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
                "seasonal_caveat": SEASONAL_CAPACITY_CAVEAT,
            },
            "metadata": metadata,
            "disclaimer": MANDATORY_DISCLAIMER,
        }

    def simulate_destination_comprehensive(
        self,
        destination: str,
        delta_alos: float = 0.4,
        affected_share: float = DEFAULT_AFFECTED_SHARE,
        conversion_pct: float = 10.0,
        yield_uplift_pct: float = 10.0,
        vfr_conversion_pct: float = 5.0,
        guests_per_room: float = DEFAULT_GUESTS_PER_ROOM,
        planning_threshold: float = DEFAULT_PLANNING_THRESHOLD,
    ) -> Dict[str, Any]:
        """
        Comprehensive multi-lever scenario simulator at destination state level:
          1. Stay extension of existing tourists (with campaign affected share)
          2. Converted excursionists to overnight tourists
          3. Converted unpaid VFR stays into commercial paid/homestay lodging (with room night capacity impact)
          4. Room-night capacity constraint and sensitivity analysis
        """
        if destination not in self.valid_states:
            raise ValueError(f"Invalid destination state: '{destination}'.")
        if delta_alos < 0 or delta_alos > 3.0:
            raise ValueError("delta_alos must be between 0.0 and 3.0 nights.")
        if affected_share < 0.0 or affected_share > 1.0:
            raise ValueError("affected_share must be between 0.0 and 1.0.")
        if conversion_pct < 0 or conversion_pct > 100.0:
            raise ValueError("conversion_pct must be between 0.0% and 100.0%.")
        if vfr_conversion_pct < 0 or vfr_conversion_pct > 100.0:
            raise ValueError("vfr_conversion_pct must be between 0.0% and 100.0%.")
        if guests_per_room <= 0:
            raise ValueError("guests_per_room must be positive.")

        dest_rows = self.df_state[(self.df_state["state"] == destination) & (self.df_state["year"] == 2025)]
        if dest_rows.empty:
            dest_rows = self.df_state[self.df_state["state"] == destination]
        if dest_rows.empty:
            raise ValueError(f"Destination state '{destination}' not found.")
        dest_data = dest_rows.iloc[-1]

        baseline_tourists = float(dest_data["tourists_thousands"]) * 1000.0
        baseline_excursionists = (float(dest_data["visitors_thousands"]) - float(dest_data["tourists_thousands"])) * 1000.0
        baseline_alos = float(dest_data["alos_days"])
        spend_per_night = float(dest_data["spend_per_night_rm"])
        base_aor, avail_rooms = self._get_capacity_metrics(destination)

        # 1. Stay extension of existing tourists (Phase 22)
        add_nights_alos = baseline_tourists * affected_share * delta_alos

        # 2. Converted excursionists into overnight tourists
        converted_tourists = baseline_excursionists * (conversion_pct / 100.0)
        add_nights_daytrip = converted_tourists * (baseline_alos + delta_alos)

        # 3. Converted unpaid VFR stays into commercial/homestay accommodation (Phase 24)
        has_vfr_data = "unpaid_vfr_share_pct" in dest_data and pd.notnull(dest_data["unpaid_vfr_share_pct"])
        unpaid_vfr_pct = float(dest_data["unpaid_vfr_share_pct"]) if has_vfr_data else None

        if has_vfr_data and unpaid_vfr_pct is not None:
            vfr_tourists = baseline_tourists * (unpaid_vfr_pct / 100.0)
            converted_vfr_tourists = vfr_tourists * (vfr_conversion_pct / 100.0)
            vfr_guest_nights = converted_vfr_tourists * (baseline_alos + delta_alos)
            homestay_nightly_rate = max(75.0, spend_per_night * DEFAULT_HOMESTAY_DISCOUNT_FACTOR)
            vfr_accom_spend_rm = vfr_guest_nights * homestay_nightly_rate
        else:
            vfr_tourists = 0.0
            converted_vfr_tourists = 0.0
            vfr_guest_nights = 0.0
            vfr_accom_spend_rm = 0.0

        # Total additional guest nights across all levers (Phase 24: includes VFR guest nights!)
        total_additional_guest_nights = add_nights_alos + add_nights_daytrip + vfr_guest_nights

        # Pricing yield uplift
        new_spend_per_night = spend_per_night * (1.0 + yield_uplift_pct / 100.0)

        # Additional accommodation expenditure
        existing_nights = baseline_tourists * baseline_alos
        existing_nights_uplift_rm = existing_nights * (new_spend_per_night - spend_per_night)
        new_nights_spend_rm = (add_nights_alos + add_nights_daytrip) * new_spend_per_night
        total_additional_spend_rm = new_nights_spend_rm + existing_nights_uplift_rm + vfr_accom_spend_rm
        total_additional_spend_m = total_additional_spend_rm / 1e6
        potential_gva_m = (total_additional_spend_rm * self.national_accom_vai) / 1e6

        # Capacity feasibility (Phase 23 & 24)
        if avail_rooms and avail_rooms > 0 and base_aor is not None:
            daily_rooms_demanded = total_additional_guest_nights / (365.0 * guests_per_room)
            delta_aor_pct = (daily_rooms_demanded / avail_rooms) * 100.0
            implied_aor = round(base_aor + delta_aor_pct, 2)
        else:
            daily_rooms_demanded = None
            delta_aor_pct = None
            implied_aor = None

        is_constrained, tier, status_msg = self._evaluate_capacity_status(implied_aor, planning_threshold)

        metadata = {
            "affected_share": {"value": affected_share, "status": "scenario_assumption"},
            "guests_per_room": {"value": guests_per_room, "status": "scenario_assumption"},
            "delta_alos": {"value": delta_alos, "status": "scenario_assumption"},
            "conversion_pct": {"value": conversion_pct, "status": "scenario_assumption"},
            "yield_uplift_pct": {"value": yield_uplift_pct, "status": "scenario_assumption"},
            "vfr_conversion_pct": {"value": vfr_conversion_pct, "status": "scenario_assumption"},
            "planning_threshold": {"value": planning_threshold, "status": "scenario_assumption"},
            "baseline_tourists": {"value": round(baseline_tourists, 0), "status": "official"},
            "baseline_excursionists": {"value": round(baseline_excursionists, 0), "status": "official"},
            "baseline_alos": {"value": round(baseline_alos, 2), "status": "official"},
            "baseline_aor": {"value": round(base_aor, 1) if base_aor else None, "status": "official"},
            "available_rooms": {"value": int(avail_rooms) if avail_rooms else None, "status": "official"},
            "unpaid_vfr_pct": {"value": round(unpaid_vfr_pct, 1) if unpaid_vfr_pct is not None else None, "status": "official"},
            "spend_per_night": {"value": round(spend_per_night, 2), "status": "derived"},
            "accommodation_vai": {"value": round(self.national_accom_vai, 4), "status": "official"},
        }

        return {
            "destination": destination,
            "inputs": {
                "delta_alos_nights": delta_alos,
                "affected_share": affected_share,
                "conversion_pct": conversion_pct,
                "yield_uplift_pct": yield_uplift_pct,
                "vfr_conversion_pct": vfr_conversion_pct,
                "guests_per_room": guests_per_room,
                "planning_threshold": planning_threshold,
                "accommodation_vai_used": self.national_accom_vai,
            },
            "baseline": {
                "total_tourists": round(baseline_tourists, 0),
                "total_excursionists": round(baseline_excursionists, 0),
                "alos_days": round(baseline_alos, 2),
                "spend_per_night_rm": round(spend_per_night, 2),
                "destination_baseline_aor_pct": round(base_aor, 1) if base_aor else None,
                "destination_available_rooms": int(avail_rooms) if avail_rooms else None,
                "unpaid_vfr_pct": round(unpaid_vfr_pct, 1) if unpaid_vfr_pct is not None else None,
            },
            "simulated_impact": {
                "stay_extension_nights": round(add_nights_alos, 0),
                "daytrip_converted_tourists": round(converted_tourists, 0),
                "daytrip_converted_nights": round(add_nights_daytrip, 0),
                "vfr_converted_tourists": round(converted_vfr_tourists, 0),
                "vfr_converted_nights": round(vfr_guest_nights, 0),
                "total_additional_guest_nights": round(total_additional_guest_nights, 0),
                "additional_accommodation_spend_rm_million": round(total_additional_spend_m, 2),
                "potential_additional_value_added_rm_million": round(potential_gva_m, 2),
            },
            "capacity_feasibility": {
                "daily_rooms_demanded": round(daily_rooms_demanded, 1) if daily_rooms_demanded else None,
                "delta_aor_pct": round(delta_aor_pct, 2) if delta_aor_pct else None,
                "implied_destination_aor_pct": implied_aor,
                "saturation_tier": tier,
                "is_capacity_constrained": is_constrained,
                "status": status_msg,
                "seasonal_caveat": SEASONAL_CAPACITY_CAVEAT,
            },
            "metadata": metadata,
            "disclaimer": MANDATORY_DISCLAIMER,
        }

    def simulate_destination_daytrip(
        self,
        destination: str,
        conversion_pct: float = 1.0,
        converted_alos: Optional[float] = None,
        guests_per_room: float = DEFAULT_GUESTS_PER_ROOM,
        planning_threshold: float = DEFAULT_PLANNING_THRESHOLD,
    ) -> Dict[str, Any]:
        """
        Simulates converting a percentage of destination-level excursionists into overnight tourists.
        Operates on the destination excursionist pool once (strictly conserving volume).
        """
        if destination not in self.valid_states:
            raise ValueError(f"Invalid destination state: '{destination}'.")
        if conversion_pct < 0 or conversion_pct > 100.0:
            raise ValueError("conversion_pct must be between 0.0% and 100.0%.")

        dest_rows = self.df_state[(self.df_state["state"] == destination) & (self.df_state["year"] == 2025)]
        if dest_rows.empty:
            dest_rows = self.df_state[self.df_state["state"] == destination]
        if dest_rows.empty:
            raise ValueError(f"Destination state '{destination}' not found.")
        dest_data = dest_rows.iloc[-1]

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
            daily_room_demand = new_nights / (365.0 * guests_per_room)
            delta_aor_pct = (daily_room_demand / avail_rooms) * 100.0
            implied_aor = round(base_aor + delta_aor_pct, 2)
        else:
            daily_room_demand = None
            delta_aor_pct = None
            implied_aor = None

        is_constrained, tier, status_msg = self._evaluate_capacity_status(implied_aor, planning_threshold)

        metadata = {
            "conversion_pct": {"value": conversion_pct, "status": "scenario_assumption"},
            "target_stay_duration_nights": {"value": target_alos, "status": "scenario_assumption"},
            "guests_per_room": {"value": guests_per_room, "status": "scenario_assumption"},
            "planning_threshold": {"value": planning_threshold, "status": "scenario_assumption"},
            "total_excursionists": {"value": round(dest_excursionists, 0), "status": "official"},
            "spend_per_night": {"value": round(spend_per_night, 2), "status": "derived"},
            "baseline_aor": {"value": round(base_aor, 1) if base_aor else None, "status": "official"},
            "available_rooms": {"value": int(avail_rooms) if avail_rooms else None, "status": "official"},
        }

        return {
            "destination": destination,
            "inputs": {
                "conversion_pct": conversion_pct,
                "target_stay_duration_nights": target_alos,
                "guests_per_room": guests_per_room,
                "planning_threshold": planning_threshold,
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
                "seasonal_caveat": SEASONAL_CAPACITY_CAVEAT,
            },
            "metadata": metadata,
            "disclaimer": MANDATORY_DISCLAIMER,
        }

    def simulate_state_priority_portfolio(
        self,
        destination: str,
        delta_alos: float = 0.5,
        affected_share: float = DEFAULT_AFFECTED_SHARE,
        guests_per_room: float = DEFAULT_GUESTS_PER_ROOM,
        planning_threshold: float = DEFAULT_PLANNING_THRESHOLD,
    ) -> Dict[str, Any]:
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
                affected_share=affected_share,
                guests_per_room=guests_per_room,
                planning_threshold=planning_threshold,
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
                "affected_share": affected_share,
                "additional_nights": add_nights,
                "additional_spend_rm_m": add_spend_m,
                "potential_value_added_rm_m": pot_gva_m,
            })

        df_corridors = pd.DataFrame(corridor_results).sort_values("additional_spend_rm_m", ascending=False)

        # Portfolio aggregate capacity assessment
        base_aor, avail_rooms = self._get_capacity_metrics(destination)
        if avail_rooms and avail_rooms > 0 and base_aor is not None:
            portfolio_daily_room_demand = total_portfolio_nights / (365.0 * guests_per_room)
            portfolio_delta_aor = (portfolio_daily_room_demand / avail_rooms) * 100.0
            portfolio_implied_aor = round(base_aor + portfolio_delta_aor, 2)
        else:
            portfolio_daily_room_demand = None
            portfolio_delta_aor = None
            portfolio_implied_aor = None

        is_constrained, tier, status_msg = self._evaluate_capacity_status(portfolio_implied_aor, planning_threshold)

        portfolio_summary = {
            "destination": destination,
            "total_active_feeders": len(dest_od),
            "affected_share": affected_share,
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
            "seasonal_caveat": SEASONAL_CAPACITY_CAVEAT,
            "disclaimer": MANDATORY_DISCLAIMER,
        }

        return {
            "corridors": df_corridors,
            "portfolio_summary": portfolio_summary,
        }

    def simulate_corridor_monte_carlo(
        self,
        origin: str,
        destination: str,
        delta_alos: float = 0.5,
        affected_share: float = DEFAULT_AFFECTED_SHARE,
        guests_per_room: float = DEFAULT_GUESTS_PER_ROOM,
        planning_threshold: float = DEFAULT_PLANNING_THRESHOLD,
        n_simulations: int = 2000,
        seed: Optional[int] = 42,
    ) -> Dict[str, Any]:
        """Runs stochastic Monte Carlo simulation across policy intervention parameters (Phase 26)."""
        from src.scenarios.monte_carlo import MonteCarloSimulator
        mc = MonteCarloSimulator(duckdb_path=self.duckdb_path)
        return mc.simulate_corridor_uncertainty(
            origin=origin,
            destination=destination,
            delta_alos=delta_alos,
            affected_share=affected_share,
            guests_per_room=guests_per_room,
            planning_threshold=planning_threshold,
            n_simulations=n_simulations,
            seed=seed,
        )

    def optimize_investment_portfolio(
        self,
        budget_rm_million: float = 5.0,
        planning_threshold: float = DEFAULT_PLANNING_THRESHOLD,
        max_corridors_per_dest: int = 4,
        preferred_tier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Solves optimal corridor investment allocation via Mixed-Integer Linear Programming (Phase 36)."""
        from src.scenarios.portfolio_optimizer import PortfolioOptimizer
        opt = PortfolioOptimizer(duckdb_path=self.duckdb_path)
        return opt.optimize_portfolio(
            budget_rm_million=budget_rm_million,
            planning_threshold=planning_threshold,
            max_corridors_per_dest=max_corridors_per_dest,
            preferred_tier=preferred_tier,
        )


if __name__ == "__main__":
    sim = ScenarioSimulator()

    # Test Scenario 1: Corridor ALOS (Selangor -> Melaka, +0.5 nights, 15% affected share)
    s1 = sim.simulate_corridor("Selangor", "Melaka", delta_alos=0.5, affected_share=0.15)
    print("\n" + "=" * 80)
    print("SCENARIO SIMULATION 1: Corridor ALOS Extension (Selangor -> Melaka +0.5 Nights, 15% Reach)")
    print("=" * 80)
    print(f"Origin: {s1['origin']} -> Destination: {s1['destination']}")
    print(f"Additional Nights: +{s1['simulated_impact']['additional_tourist_nights']:,.0f}")
    print(f"Additional Spend:  +RM {s1['simulated_impact']['additional_accommodation_spend_rm_million']:.2f} Million")
    print(f"Potential GVA:     +RM {s1['simulated_impact']['potential_additional_value_added_rm_million']:.2f} Million")
    print(f"Capacity Status:   {s1['capacity_feasibility']['status']}")

    # Test Scenario 2: Comprehensive Destination (Melaka)
    s2 = sim.simulate_destination_comprehensive("Melaka", delta_alos=0.4, affected_share=0.15, conversion_pct=10.0, vfr_conversion_pct=5.0)
    print("\n" + "=" * 80)
    print("SCENARIO SIMULATION 2: Melaka Comprehensive Multi-Lever Simulation")
    print("=" * 80)
    print(f"Destination: {s2['destination']}")
    print(f"Additional Guest Nights: +{s2['simulated_impact']['total_additional_guest_nights']:,.0f}")
    print(f"Additional Spend:        +RM {s2['simulated_impact']['additional_accommodation_spend_rm_million']:.2f} Million")
    print(f"Potential GVA:           +RM {s2['simulated_impact']['potential_additional_value_added_rm_million']:.2f} Million")
    print(f"Capacity Status:         {s2['capacity_feasibility']['status']}")
    print(f"Caveat:                  {s2['capacity_feasibility']['seasonal_caveat']}")
    print(f"Disclaimer:              {s2['disclaimer']}")
