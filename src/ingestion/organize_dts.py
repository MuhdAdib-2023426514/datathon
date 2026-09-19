"""
Organize DTS Files into Canonical Hierarchy:
data/dts/<YEAR>/national/
data/dts/<YEAR>/state/
"""

import re
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DTS_SOURCE_DIR = ROOT_DIR / "dts"
DATA_DIR = ROOT_DIR / "data"
TARGET_DTS_DIR = DATA_DIR / "dts"

STATE_NAME_MAPPINGS = {
    "JOHOR": "JOHOR",
    "KEDAH": "KEDAH",
    "KELANTAN": "KELANTAN",
    "MELAKA": "MELAKA",
    "MALACCA": "MELAKA",
    "NEGERI_SEMBILAN": "NEGERI SEMBILAN",
    "NEGERI SEMBILAN": "NEGERI SEMBILAN",
    "PAHANG": "PAHANG",
    "PERAK": "PERAK",
    "PERLIS": "PERLIS",
    "PULAU_PINANG": "PULAU PINANG",
    "PULAU PINANG": "PULAU PINANG",
    "PENANG": "PULAU PINANG",
    "SABAH": "SABAH",
    "SARAWAK": "SARAWAK",
    "SELANGOR": "SELANGOR",
    "TERENGGANU": "TERENGGANU",
    "WP_KUALA_LUMPUR": "W.P. KUALA LUMPUR",
    "W.P. KUALA LUMPUR": "W.P. KUALA LUMPUR",
    "KUALA_LUMPUR": "W.P. KUALA LUMPUR",
    "KUALA LUMPUR": "W.P. KUALA LUMPUR",
    "WP_LABUAN": "W.P. LABUAN",
    "W.P. LABUAN": "W.P. LABUAN",
    "LABUAN": "W.P. LABUAN",
    "WP_PUTRAJAYA": "W.P. PUTRAJAYA",
    "W.P. PUTRAJAYA": "W.P. PUTRAJAYA",
    "PUTRAJAYA": "W.P. PUTRAJAYA",
}


def resolve_canonical_state(text: str) -> str:
    cleaned = text.upper().replace("-", "_").replace(" ", "_")
    for pattern, canonical in STATE_NAME_MAPPINGS.items():
        if pattern.replace(" ", "_") in cleaned:
            return canonical
    raise ValueError(f"Could not identify state from: '{text}'")


def organize_all():
    print("Starting automated organization of DTS files...")
    TARGET_DTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Process files in dts/ (2018 - 2024)
    if DTS_SOURCE_DIR.exists():
        all_dts_files = list(DTS_SOURCE_DIR.rglob("*.xlsx"))
        for src_path in all_dts_files:
            fname = src_path.name
            parent_name = src_path.parent.name
            full_str = f"{parent_name}_{fname}".upper()

            # Identify year
            year_match = re.search(r"20\d{2}", full_str)
            if not year_match:
                continue
            year = int(year_match.group())

            # Check if National
            if "TABLE DTS" in fname.upper():
                dest_dir = TARGET_DTS_DIR / str(year) / "national"
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / f"TABLE DTS {year}.xlsx"
                shutil.copy2(src_path, dest_file)
            else:
                # State file
                try:
                    state_canonical = resolve_canonical_state(full_str)
                    dest_dir = TARGET_DTS_DIR / str(year) / "state"
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest_file = dest_dir / f"TABLE OF PUBLICATION DTS {year} {state_canonical}.xlsx"
                    shutil.copy2(src_path, dest_file)
                except ValueError as e:
                    print(f"  [WARN] Skipping unrecognized file: {src_path} ({e})")

    # 2. Process existing 2025 files in data/malaysia/ and data/state/
    nat_2025 = DATA_DIR / "malaysia" / "TABLE DTS 2025.xlsx"
    if nat_2025.exists():
        dest_dir = TARGET_DTS_DIR / "2025" / "national"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(nat_2025, dest_dir / "TABLE DTS 2025.xlsx")

    state_2025_files = list((DATA_DIR / "state").glob("*.xlsx"))
    for src_path in state_2025_files:
        dest_dir = TARGET_DTS_DIR / "2025" / "state"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / src_path.name
        shutil.copy2(src_path, dest_file)

    # 3. Print verification summary
    print("\n" + "=" * 60)
    print("ORGANIZATION COMPLETE: INVENTORY OF data/dts/")
    print("=" * 60)
    for year_dir in sorted(TARGET_DTS_DIR.iterdir()):
        if year_dir.is_dir() and re.match(r"20\d{2}", year_dir.name):
            nat_count = len(list((year_dir / "national").glob("*.xlsx"))) if (year_dir / "national").exists() else 0
            state_count = len(list((year_dir / "state").glob("*.xlsx"))) if (year_dir / "state").exists() else 0
            print(f"Year {year_dir.name}: National={nat_count} file(s), State={state_count} state file(s)")


if __name__ == "__main__":
    organize_all()
