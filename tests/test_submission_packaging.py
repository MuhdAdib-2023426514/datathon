"""
Automated Test Suite for Sprint F: Competition Submission Packaging & Pre-Flight Verification.
Covers:
  - Phase 51: Competition Storyline & 10-Slide Pitch Deck
  - Phase 58: Submission Packaging & AGENTS.md Repository Structure
  - CLI Entrypoint: main.py execution and summary output
  - Interactive Notebook Walkthrough: notebooks/tourism_value_optimizer_walkthrough.ipynb
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
NOTEBOOKS_DIR = ROOT_DIR / "notebooks"


class TestCompetitionPresentationDeck:
    """Phase 51: 10-Slide Competition Presentation Deck Completeness."""

    def test_presentation_deck_exists_and_covers_10_slides(self):
        deck_file = DOCS_DIR / "presentation_deck.md"
        assert deck_file.exists(), "docs/presentation_deck.md does not exist"
        content = deck_file.read_text(encoding="utf-8")

        # Must have 10 formal slides following Phase 51 Storyline
        for i in range(1, 11):
            assert f"## Slide {i}:" in content, f"Missing Slide {i} in presentation deck"

        # Verify key slide themes
        assert "Volume Recovery vs. Value Generation" in content
        assert "From Volume to Value" in content
        assert "Accommodation as Malaysia's #1 Value Engine" in content
        assert "4-Quadrant Typology" in content
        assert "Two-Way Fixed Effects" in content
        assert "PPML Gravity Modeling" in content
        assert "58 Non-Dominated Pareto Corridors" in content
        assert "Monte Carlo Uncertainty" in content
        assert "Portfolio Optimization" in content
        assert "Institutional Adoption & SDG Impact" in content


class TestInteractiveNotebookWalkthrough:
    """AGENTS.md Section 17: Interactive Demonstration Notebook."""

    def test_notebook_exists_and_is_valid_json(self):
        nb_file = NOTEBOOKS_DIR / "tourism_value_optimizer_walkthrough.ipynb"
        assert nb_file.exists(), "notebooks/tourism_value_optimizer_walkthrough.ipynb does not exist"

        with open(nb_file, "r", encoding="utf-8") as f:
            nb = json.load(f)

        assert "cells" in nb
        assert len(nb["cells"]) >= 10, "Notebook should have at least 10 markdown and code cells"

        # Check that all 5 core sections are demonstrated
        full_text = " ".join("".join(c.get("source", [])) for c in nb["cells"])
        assert "Product Value-Added Intensity" in full_text
        assert "State Productivity" in full_text
        assert "Pareto Corridors" in full_text
        assert "Scenario Simulation" in full_text
        assert "Portfolio Optimization" in full_text


class TestCLIEntrypoint:
    """Executable CLI entrypoint validation (main.py)."""

    def test_main_cli_summary_runs_successfully(self):
        res = subprocess.run(
            [sys.executable, "main.py", "--summary"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert res.returncode == 0, f"main.py --summary failed with error: {res.stderr}"
        stdout = res.stdout

        # Verify key outputs in executive report
        assert "MYTourism Value Intelligence" in stdout
        assert "Accommodation services" in stdout
        assert "85.8%" in stdout
        assert "0.5890" in stdout
        assert "+0.6628" in stdout
        assert "58 corridors" in stdout

    def test_main_cli_status_runs_successfully(self):
        res = subprocess.run(
            [sys.executable, "main.py", "--status"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert res.returncode == 0, f"main.py --status failed with error: {res.stderr}"
        assert "Pipeline Stage Status" in res.stdout or "pipeline_status" in res.stdout or "stage" in res.stdout.lower()


class TestRepositoryStructureCompliance:
    """AGENTS.md Section 17 Repository Structure Compliance."""

    def test_required_root_directories_and_files_exist(self):
        required_paths = [
            ROOT_DIR / "AGENTS.md",
            ROOT_DIR / "README.md",
            ROOT_DIR / "IMPLEMENTATION_PLAN.md",
            ROOT_DIR / "IMPLEMENTATION_STATUS.md",
            ROOT_DIR / "main.py",
            ROOT_DIR / "pyproject.toml",
            ROOT_DIR / "src",
            ROOT_DIR / "data",
            ROOT_DIR / "dashboard",
            ROOT_DIR / "notebooks",
            ROOT_DIR / "tests",
            ROOT_DIR / "docs",
        ]
        for p in required_paths:
            assert p.exists(), f"Required path {p.name} does not exist in repository root"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
