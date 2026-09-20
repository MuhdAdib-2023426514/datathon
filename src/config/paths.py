"""
Centralized, cross-platform path management for Malaysia Tourism Value Optimizer.
Eliminates all hardcoded user or machine-specific absolute paths across the codebase.
"""

import os
from pathlib import Path

# Project root directory (dosm/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DUCKDB_PATH = PROCESSED_DATA_DIR / "tourism_data.duckdb"
METADATA_DIR = DATA_DIR / "metadata"
CHARTS_DIR = DATA_DIR / "charts"
GEO_DIR = DATA_DIR / "geo"
TSA_DIR = DATA_DIR / "tsa"

# Artifact and documentation directories
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
BASELINE_DIR = ARTIFACTS_DIR / "baseline"
DOCS_DIR = PROJECT_ROOT / "docs"

# Dashboard directories
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DASHBOARD_DATA_DIR = DASHBOARD_DIR / "public" / "data"

# Convenience aliases
ROOT_DIR = PROJECT_ROOT
PROCESSED_DIR = PROCESSED_DATA_DIR

# Ensure runtime directories exist
for _dir in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, ARTIFACTS_DIR, BASELINE_DIR, METADATA_DIR, CHARTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
