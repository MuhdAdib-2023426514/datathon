"""
Booking.com Scraped Hotel Data Ingestion & Summarization
Malaysia Tourism Value Optimizer

Processes scraped hotel data from booking.com (18 destinations, 360 hotel listings).
Extracts commercial room rates, star ratings, review scores, subscores, and amenities.
Aggregates state and national market benchmarks.

IMPORTANT CONSTRAINT:
This dataset represents a 2026 cross-sectional scraped market sample.
It is NOT validated by DOSM and MUST NOT be used to train econometric or ML models.
It serves strictly as supporting / auxiliary commercial lodging reference data.
"""

import glob
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import duckdb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BOOKING_DIR = ROOT_DIR / "booking"
PROCESSED_DIR = ROOT_DIR / "data/processed"
DUCKDB_PATH = PROCESSED_DIR / "tourism_data.duckdb"
DASHBOARD_DATA_DIR = ROOT_DIR / "dashboard/public/data"
OUTPUT_JSON = DASHBOARD_DATA_DIR / "booking_hotel_benchmarks.json"
SOURCE_META_FILE = DASHBOARD_DATA_DIR / "source_metadata.json"

# State mapping dictionary
SLUG_TO_DESTINATION = {
    "cameron": {
        "destination_name": "Cameron Highlands",
        "state_name": "Pahang",
        "is_subdestination": True,
        "district": "Cameron Highlands",
    },
    "johor": {
        "destination_name": "Johor",
        "state_name": "Johor",
        "is_subdestination": False,
        "district": None,
    },
    "kedah": {
        "destination_name": "Kedah (Mainland)",
        "state_name": "Kedah",
        "is_subdestination": False,
        "district": None,
    },
    "kelantan": {
        "destination_name": "Kelantan",
        "state_name": "Kelantan",
        "is_subdestination": False,
        "district": None,
    },
    "kl": {
        "destination_name": "W.P. Kuala Lumpur",
        "state_name": "W.P. Kuala Lumpur",
        "is_subdestination": False,
        "district": "Kuala Lumpur",
    },
    "labuan": {
        "destination_name": "W.P. Labuan",
        "state_name": "W.P. Labuan",
        "is_subdestination": False,
        "district": "Labuan",
    },
    "langkawi": {
        "destination_name": "Langkawi Island",
        "state_name": "Kedah",
        "is_subdestination": True,
        "district": "Langkawi",
    },
    "melaka": {
        "destination_name": "Melaka",
        "state_name": "Melaka",
        "is_subdestination": False,
        "district": None,
    },
    "n_sembilan": {
        "destination_name": "Negeri Sembilan",
        "state_name": "Negeri Sembilan",
        "is_subdestination": False,
        "district": None,
    },
    "pahang": {
        "destination_name": "Pahang (General)",
        "state_name": "Pahang",
        "is_subdestination": False,
        "district": None,
    },
    "penang": {
        "destination_name": "Pulau Pinang",
        "state_name": "Pulau Pinang",
        "is_subdestination": False,
        "district": None,
    },
    "perak": {
        "destination_name": "Perak",
        "state_name": "Perak",
        "is_subdestination": False,
        "district": None,
    },
    "perlis": {
        "destination_name": "Perlis",
        "state_name": "Perlis",
        "is_subdestination": False,
        "district": None,
    },
    "putrajaya": {
        "destination_name": "W.P. Putrajaya",
        "state_name": "W.P. Putrajaya",
        "is_subdestination": False,
        "district": "Putrajaya",
    },
    "sabah": {
        "destination_name": "Sabah",
        "state_name": "Sabah",
        "is_subdestination": False,
        "district": None,
    },
    "sarawak": {
        "destination_name": "Sarawak",
        "state_name": "Sarawak",
        "is_subdestination": False,
        "district": None,
    },
    "selangor": {
        "destination_name": "Selangor",
        "state_name": "Selangor",
        "is_subdestination": False,
        "district": None,
    },
    "terengganu": {
        "destination_name": "Terengganu",
        "state_name": "Terengganu",
        "is_subdestination": False,
        "district": None,
    },
}


def parse_numeric_price(price_str: Optional[str]) -> Optional[float]:
    """Parse 'MYR 218' or 'MYR 1,200' to float."""
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", price_str.replace(",", ""))
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def parse_rating_and_reviews(score_raw: Optional[str]) -> tuple[Optional[float], Optional[int]]:
    """Parse '9.5 Exceptional · 388 reviews' into (9.5, 388)."""
    if not score_raw:
        return None, None
    score_match = re.search(r"(\d+\.?\d*)", score_raw)
    score = float(score_match.group(1)) if score_match else None

    rev_match = re.search(r"([\d,]+)\s+reviews", score_raw)
    reviews = int(rev_match.group(1).replace(",", "")) if rev_match else None
    return score, reviews


def clean_nan(obj: Any) -> Any:
    """Recursively clean NaN, Infinity and numpy types for standard JSON serialization."""
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return round(obj, 2)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return round(float(obj), 2)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


def parse_all_booking_data() -> tuple[List[Dict[str, Any]], pd.DataFrame]:
    """Parse all 18 JSON files into individual hotel records and a DataFrame."""
    json_files = sorted(glob.glob(str(BOOKING_DIR / "*.json")))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {BOOKING_DIR}")

    records = []

    for fpath in json_files:
        fname = Path(fpath).name
        slug = fname.replace(".json", "")
        dest_meta = SLUG_TO_DESTINATION.get(slug, {
            "destination_name": slug.title(),
            "state_name": slug.title(),
            "is_subdestination": False,
            "district": None,
        })

        with open(fpath, "r", encoding="utf-8") as fp:
            items = json.load(fp)

        for idx, item in enumerate(items, start=1):
            sl = item.get("search_listing") or {}

            # Price extraction
            price_raw = sl.get("price_raw")
            price_myr = parse_numeric_price(price_raw)

            # Rating and review count
            score_raw = item.get("score_raw") or sl.get("score_raw")
            rating_score, review_count = parse_rating_and_reviews(score_raw)

            # Subscores
            sub = item.get("subscores") or {}
            sub_staff = float(sub.get("staff")) if sub.get("staff") is not None else None
            sub_facilities = float(sub.get("facilities")) if sub.get("facilities") is not None else None
            sub_cleanliness = float(sub.get("cleanliness")) if sub.get("cleanliness") is not None else None
            sub_comfort = float(sub.get("comfort")) if sub.get("comfort") is not None else None
            sub_value_for_money = float(sub.get("value_for_money")) if sub.get("value_for_money") is not None else None
            sub_location = float(sub.get("location")) if sub.get("location") is not None else None
            sub_wifi = float(sub.get("free_wifi")) if sub.get("free_wifi") is not None else None

            # Popular facilities (deduplicate while preserving order)
            raw_facs = item.get("popular_facilities") or []
            seen_facs = set()
            clean_facs = []
            for fac in raw_facs:
                fac_clean = fac.strip()
                if fac_clean and fac_clean not in seen_facs:
                    seen_facs.add(fac_clean)
                    clean_facs.append(fac_clean)

            # Stars
            stars = int(item.get("stars", 0))

            hotel_record = {
                "hotel_id": f"{slug}_{idx:02d}",
                "destination_slug": slug,
                "destination_name": dest_meta["destination_name"],
                "state_name": dest_meta["state_name"],
                "is_subdestination": dest_meta["is_subdestination"],
                "district": dest_meta["district"],
                "hotel_name": item.get("title", "").strip(),
                "price_myr": price_myr,
                "stars": stars,
                "rating_score": rating_score,
                "review_count": review_count,
                "sub_cleanliness": sub_cleanliness,
                "sub_comfort": sub_comfort,
                "sub_location": sub_location,
                "sub_value_for_money": sub_value_for_money,
                "sub_facilities": sub_facilities,
                "sub_staff": sub_staff,
                "sub_wifi": sub_wifi,
                "distance_downtown": sl.get("distance"),
                "address": (item.get("address") or "").strip(),
                "booking_url": item.get("url") or sl.get("url"),
                "property_type": item.get("property_type") or "Hotel",
                "sustainable_badge": bool(item.get("travel_sustainable_badge")),
                "popular_facilities": clean_facs[:8],  # top 8 facilities
                "data_status": "UNVALIDATED_SUPPORTING_2026",
            }
            records.append(hotel_record)

    df = pd.DataFrame(records)
    return records, df


def compute_group_metrics(group_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute summary statistics for a destination or state group."""
    prices = group_df["price_myr"].dropna()
    ratings = group_df["rating_score"].dropna()
    reviews = group_df["review_count"].dropna()

    # Star distribution
    star_counts = group_df["stars"].value_counts().to_dict()
    total_props = len(group_df)
    luxury_count = star_counts.get(5, 0) + star_counts.get(4, 0)
    mid_count = star_counts.get(3, 0)
    budget_unrated_count = total_props - (luxury_count + mid_count)

    # Subscores
    sub_metrics = {
        "cleanliness": float(group_df["sub_cleanliness"].mean()) if group_df["sub_cleanliness"].notna().any() else None,
        "comfort": float(group_df["sub_comfort"].mean()) if group_df["sub_comfort"].notna().any() else None,
        "location": float(group_df["sub_location"].mean()) if group_df["sub_location"].notna().any() else None,
        "value_for_money": float(group_df["sub_value_for_money"].mean()) if group_df["sub_value_for_money"].notna().any() else None,
        "facilities": float(group_df["sub_facilities"].mean()) if group_df["sub_facilities"].notna().any() else None,
        "staff": float(group_df["sub_staff"].mean()) if group_df["sub_staff"].notna().any() else None,
    }

    # Top amenities
    all_facs = [fac for sublist in group_df["popular_facilities"] for fac in sublist]
    fac_series = pd.Series(all_facs)
    top_facs = fac_series.value_counts().head(6).to_dict() if not fac_series.empty else {}

    return {
        "sample_size": total_props,
        "median_price_myr": float(prices.median()) if not prices.empty else None,
        "mean_price_myr": float(prices.mean()) if not prices.empty else None,
        "min_price_myr": float(prices.min()) if not prices.empty else None,
        "max_price_myr": float(prices.max()) if not prices.empty else None,
        "p25_price_myr": float(prices.quantile(0.25)) if not prices.empty else None,
        "p75_price_myr": float(prices.quantile(0.75)) if not prices.empty else None,
        "mean_rating": float(ratings.mean()) if not ratings.empty else None,
        "median_rating": float(ratings.median()) if not ratings.empty else None,
        "total_reviews_sample": int(reviews.sum()) if not reviews.empty else 0,
        "star_breakdown": {
            "luxury_4_5_star_count": luxury_count,
            "luxury_4_5_star_pct": round((luxury_count / total_props) * 100, 1) if total_props else 0,
            "midscale_3_star_count": mid_count,
            "midscale_3_star_pct": round((mid_count / total_props) * 100, 1) if total_props else 0,
            "budget_unrated_count": budget_unrated_count,
            "budget_unrated_pct": round((budget_unrated_count / total_props) * 100, 1) if total_props else 0,
        },
        "subscores_avg": sub_metrics,
        "top_amenities": top_facs,
    }


def build_benchmarks_payload(records: List[Dict[str, Any]], df: pd.DataFrame) -> Dict[str, Any]:
    """Construct full structured JSON output for dashboard consumption."""
    # National overall benchmark
    national_metrics = compute_group_metrics(df)

    # Destination-level summaries (18 destinations)
    destinations = {}
    for slug, group in df.groupby("destination_slug"):
        meta = SLUG_TO_DESTINATION[slug]
        metrics = compute_group_metrics(group)
        metrics["destination_slug"] = slug
        metrics["destination_name"] = meta["destination_name"]
        metrics["state_name"] = meta["state_name"]
        metrics["is_subdestination"] = meta["is_subdestination"]
        metrics["district"] = meta["district"]
        # Attach hotels list sorted by rating desc, price asc
        hotel_items = group.sort_values(
            by=["rating_score", "price_myr"], ascending=[False, True]
        ).to_dict(orient="records")
        metrics["hotels"] = hotel_items
        destinations[slug] = metrics

    # State-level summaries (16 official states)
    state_summaries = {}
    for state_name, group in df.groupby("state_name"):
        metrics = compute_group_metrics(group)
        metrics["state_name"] = state_name

        # Identify subdestinations for this state
        sub_slugs = [
            slug for slug, m in SLUG_TO_DESTINATION.items()
            if m["state_name"] == state_name and m["is_subdestination"]
        ]
        metrics["has_subdestinations"] = len(sub_slugs) > 0
        metrics["subdestinations"] = sub_slugs

        # Hotels in this state
        hotel_items = group.sort_values(
            by=["rating_score", "price_myr"], ascending=[False, True]
        ).to_dict(orient="records")
        metrics["hotels"] = hotel_items
        state_summaries[state_name] = metrics

    payload = {
        "metadata": {
            "source": "Scraped from Booking.com",
            "snapshot_year": 2026,
            "total_properties": len(df),
            "destinations_count": len(destinations),
            "states_covered": len(state_summaries),
            "status": "UNVALIDATED_SUPPORTING",
            "disclaimer": (
                "Supporting market data only. Scraped in 2026 for 20 hotels per destination. "
                "Not officially validated by DOSM. Excluded from econometric and machine learning model training."
            ),
        },
        "national_benchmark": national_metrics,
        "destinations": destinations,
        "states": state_summaries,
    }

    return clean_nan(payload)


def persist_to_duckdb(df: pd.DataFrame, payload: Dict[str, Any]) -> None:
    """Store raw hotel records and summary tables in DuckDB."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DUCKDB_PATH))

    # Flatten popular_facilities to JSON string for DuckDB storage
    df_db = df.copy()
    df_db["popular_facilities"] = df_db["popular_facilities"].apply(json.dumps)

    con.execute("DROP TABLE IF EXISTS booking_hotel_sample")
    con.execute("CREATE TABLE booking_hotel_sample AS SELECT * FROM df_db")

    # Destination summary table
    summary_rows = []
    for slug, d in payload["destinations"].items():
        summary_rows.append({
            "destination_slug": slug,
            "destination_name": d["destination_name"],
            "state_name": d["state_name"],
            "is_subdestination": d["is_subdestination"],
            "sample_size": d["sample_size"],
            "median_price_myr": d["median_price_myr"],
            "mean_price_myr": d["mean_price_myr"],
            "min_price_myr": d["min_price_myr"],
            "max_price_myr": d["max_price_myr"],
            "mean_rating": d["mean_rating"],
            "total_reviews_sample": d["total_reviews_sample"],
            "luxury_4_5_star_pct": d["star_breakdown"]["luxury_4_5_star_pct"],
            "midscale_3_star_pct": d["star_breakdown"]["midscale_3_star_pct"],
            "budget_unrated_pct": d["star_breakdown"]["budget_unrated_pct"],
            "data_status": "UNVALIDATED_SUPPORTING_2026",
        })
    df_summary = pd.DataFrame(summary_rows)
    con.execute("DROP TABLE IF EXISTS booking_destination_summary")
    con.execute("CREATE TABLE booking_destination_summary AS SELECT * FROM df_summary")

    con.close()
    print(f"Persisted booking data to DuckDB at {DUCKDB_PATH}")


def update_source_metadata():
    """Register booking dataset in source_metadata.json with strict supporting status."""
    if not SOURCE_META_FILE.exists():
        return

    with open(SOURCE_META_FILE, "r", encoding="utf-8") as fp:
        meta = json.load(fp)

    sources = meta.get("sources", {})
    sources["booking_hotel_sample_2026"] = {
        "title": "Booking.com Malaysian Hotel Market Sample 2026",
        "organization": "Commercial OTA Scraped Sample (Booking.com)",
        "frequency": "One-time Cross-Sectional Snapshot (2026)",
        "sample_size": "360 hotels across 18 destinations (20 per destination)",
        "data_status": "UNVALIDATED_SUPPORTING",
        "ml_eligible": False,
        "purpose": "Supporting commercial room-rate benchmark and private lodging quality reference.",
        "limitations": (
            "Not an official DOSM dataset. Covers commercial online booking listings only, "
            "which over-indexes on commercial hotels vs informal or VFR accommodation. "
            "Strictly excluded from ML model training."
        ),
    }
    meta["sources"] = sources

    with open(SOURCE_META_FILE, "w", encoding="utf-8") as fp:
        json.dump(meta, fp, indent=2)
    print(f"Updated source metadata at {SOURCE_META_FILE}")


def run_ingestion():
    print("=" * 70)
    print("Ingesting Booking.com Scraped Hotel Data")
    print("=" * 70)

    records, df = parse_all_booking_data()
    print(f"Parsed {len(records)} hotels across {df['destination_slug'].nunique()} destinations.")
    print(f"States represented: {df['state_name'].nunique()} (Coverage: 100% of 16 states/FTs)")

    payload = build_benchmarks_payload(records, df)

    # Ensure output directory exists
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)
    print(f"Exported dashboard JSON to {OUTPUT_JSON} ({OUTPUT_JSON.stat().st_size} bytes)")

    # Save to DuckDB
    persist_to_duckdb(df, payload)

    # Update provenance metadata
    update_source_metadata()

    print("Booking.com ingestion complete successfully.")


if __name__ == "__main__":
    run_ingestion()
