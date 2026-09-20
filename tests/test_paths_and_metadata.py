"""
Unit tests for Path Configuration, Zero-Absolute-Path Enforcement, and Source Registry (Sprint 1).
Verifies:
1. All path constants in src.config.paths resolve valid local project directories.
2. No absolute hardcoded paths (/home/muhammad_adib or C:\) exist in python modules under src/.
3. data/metadata/source_registry.yaml adheres to schema and exports valid JSON.
"""

import os
import sys
import json
import unittest
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.paths import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DUCKDB_PATH,
    ARTIFACTS_DIR,
    BASELINE_DIR,
    DASHBOARD_DIR,
    DASHBOARD_DATA_DIR,
    METADATA_DIR,
    DOCS_DIR,
)


class TestPathsAndMetadata(unittest.TestCase):
    def test_paths_resolve_under_project_root(self):
        """All configured path variables must be relative subpaths of PROJECT_ROOT."""
        self.assertTrue(PROJECT_ROOT.exists(), f"PROJECT_ROOT does not exist: {PROJECT_ROOT}")
        self.assertTrue(DATA_DIR.exists())
        self.assertTrue(PROCESSED_DATA_DIR.exists())
        self.assertTrue(DUCKDB_PATH.exists(), f"DuckDB database missing at {DUCKDB_PATH}")
        self.assertTrue(ARTIFACTS_DIR.exists())
        self.assertTrue(BASELINE_DIR.exists())
        self.assertTrue(DASHBOARD_DIR.exists())
        self.assertTrue(DASHBOARD_DATA_DIR.exists())
        self.assertTrue(METADATA_DIR.exists())
        self.assertTrue(DOCS_DIR.exists())

        # Verify ancestry
        self.assertTrue(DATA_DIR.is_relative_to(PROJECT_ROOT))
        self.assertTrue(DASHBOARD_DATA_DIR.is_relative_to(PROJECT_ROOT))

    def test_zero_hardcoded_absolute_paths_in_src(self):
        """No Python file in src/ should contain '/home/muhammad_adib' or 'C:\\'."""
        src_dir = PROJECT_ROOT / "src"
        violations = []

        for root, _, files in os.walk(src_dir):
            for f in files:
                if f.endswith(".py"):
                    full_path = Path(root) / f
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                        if "/home/muhammad_adib" in content:
                            violations.append(f"{full_path.relative_to(PROJECT_ROOT)} contains '/home/muhammad_adib'")
                        if "C:\\" in content or "C:/" in content:
                            violations.append(f"{full_path.relative_to(PROJECT_ROOT)} contains Windows drive letter")

        self.assertEqual(len(violations), 0, f"Found hardcoded absolute paths in src/:\n" + "\n".join(violations))

    def test_source_registry_schema_and_export(self):
        """data/metadata/source_registry.yaml must be valid YAML and compile to source_metadata.json."""
        yaml_file = METADATA_DIR / "source_registry.yaml"
        self.assertTrue(yaml_file.exists(), f"Missing {yaml_file}")

        with open(yaml_file, "r") as f:
            registry = yaml.safe_load(f)

        self.assertIn("sources", registry)
        self.assertIn("derived_models", registry)

        sources = registry["sources"]
        self.assertIn("tsa_macro_and_products", sources)
        self.assertIn("state_domestic_tourism_2025", sources)
        self.assertIn("motac_hotel_kpi", sources)

        # Verify compiled JSON
        json_file = DASHBOARD_DATA_DIR / "source_metadata.json"
        self.assertTrue(json_file.exists(), f"Compiled JSON missing at {json_file}")
        with open(json_file, "r") as f:
            data = json.load(f)
        self.assertEqual(len(data.get("sources", {})), len(sources))


if __name__ == "__main__":
    unittest.main()
