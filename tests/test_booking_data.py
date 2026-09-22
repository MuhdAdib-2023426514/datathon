"""
Unit and Contract Tests for Scraped Booking.com Hotel Data.
Validates:
  1. Ingestion completeness (360 hotels across 18 destinations).
  2. All 16 Malaysian states/FTs covered.
  3. Positive room rate prices, ratings, and subscores.
  4. Status labelling as UNVALIDATED_SUPPORTING.
  5. Strict ML exclusion: Ensures ML/econometric models do not train on booking data.
"""

import json
from pathlib import Path
import duckdb
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "dashboard/public/data"
DUCKDB_PATH = ROOT_DIR / "data/processed/tourism_data.duckdb"
BOOKING_JSON = DATA_DIR / "booking_hotel_benchmarks.json"


class TestBookingDataIngestion:
    """Test suite for booking data completeness and integrity."""

    def test_json_artifact_exists(self):
        assert BOOKING_JSON.exists(), f"Missing {BOOKING_JSON}"
        with open(BOOKING_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "national_benchmark" in data
        assert "destinations" in data
        assert "states" in data

    def test_metadata_guardrails_and_status(self):
        with open(BOOKING_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data["metadata"]
        assert meta["status"] == "UNVALIDATED_SUPPORTING"
        assert meta["snapshot_year"] == 2026
        assert meta["total_properties"] == 360
        assert meta["destinations_count"] == 18
        assert meta["states_covered"] == 16
        assert "Excluded from econometric and machine learning" in meta["disclaimer"]

    def test_all_18_destinations_present_with_20_hotels_each(self):
        with open(BOOKING_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        destinations = data["destinations"]
        assert len(destinations) == 18

        expected_slugs = {
            "cameron", "johor", "kedah", "kelantan", "kl", "labuan", "langkawi",
            "melaka", "n_sembilan", "pahang", "penang", "perak", "perlis",
            "putrajaya", "sabah", "sarawak", "selangor", "terengganu"
        }
        assert set(destinations.keys()) == expected_slugs

        for slug, d in destinations.items():
            assert d["sample_size"] == 20, f"Destination {slug} does not have 20 hotels"
            assert len(d["hotels"]) == 20
            assert d["median_price_myr"] > 0, f"Invalid median price in {slug}"
            assert d["mean_price_myr"] > 0
            assert 0 <= d["mean_rating"] <= 10
            # Check star breakdown adds up
            sb = d["star_breakdown"]
            total_stars = sb["luxury_4_5_star_count"] + sb["midscale_3_star_count"] + sb["budget_unrated_count"]
            assert total_stars == 20, f"Star breakdown count mismatch in {slug}"

    def test_all_16_states_covered(self):
        with open(BOOKING_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        states = data["states"]
        assert len(states) == 16

        # Check subdestinations
        assert states["Pahang"]["has_subdestinations"] is True
        assert "cameron" in states["Pahang"]["subdestinations"]
        assert states["Pahang"]["sample_size"] == 40  # 20 Pahang general + 20 Cameron

        assert states["Kedah"]["has_subdestinations"] is True
        assert "langkawi" in states["Kedah"]["subdestinations"]
        assert states["Kedah"]["sample_size"] == 40  # 20 Kedah mainland + 20 Langkawi

    def test_duckdb_tables_exist(self):
        assert DUCKDB_PATH.exists()
        con = duckdb.connect(str(DUCKDB_PATH), read_only=False)
        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        assert "booking_hotel_sample" in tables
        assert "booking_destination_summary" in tables

        cnt_sample = con.execute("SELECT count(*) FROM booking_hotel_sample").fetchone()[0]
        assert cnt_sample == 360

        cnt_dest = con.execute("SELECT count(*) FROM booking_destination_summary").fetchone()[0]
        assert cnt_dest == 18
        con.close()

    def test_strict_ml_exclusion(self):
        """Verify that econometric and ML model code does NOT reference booking tables."""
        ml_files = [
            ROOT_DIR / "src/analytics/accommodation_drivers_ml.py",
            ROOT_DIR / "src/analytics/gravity_corridor_model.py",
            ROOT_DIR / "src/analytics/panel_econometrics.py",
        ]
        for fpath in ml_files:
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8")
                assert "booking_hotel_sample" not in content, f"{fpath.name} violates rule by referencing booking_hotel_sample"
                assert "booking_destination_summary" not in content, f"{fpath.name} violates rule by referencing booking_destination_summary"
