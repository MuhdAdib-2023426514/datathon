"""
Pipeline Orchestrator for Malaysia Tourism Value Optimizer.
Provides a deterministic, phased pipeline runner for:
  Stage 1: Ingestion (DTS, TSA, MOTAC KPI, Demographics)
  Stage 2: Analytics & Models (VAI, Panel FE, Gravity, OD Network, Scenarios)
  Stage 3: Validation (TSA Accounting & Corridor Quality Gates)
  Stage 4: Export (Dashboard JSON serialization)

Can be executed directly via CLI or programmatically called by Pipeline MCP Server.
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent
STATUS_FILE = ROOT_DIR / "data/pipeline_status.json"
DUCKDB_PATH = ROOT_DIR / "data/processed/tourism_data.duckdb"
PYTHON_BIN = sys.executable

STAGES = {
    "ingest": [
        ("tsa", "src/ingestion/tsa_parser.py"),
        ("state", "src/ingestion/state_parser.py"),
        ("multi_year_state", "src/ingestion/multi_year_state_parser.py"),
        ("granular_dts", "src/ingestion/granular_dts_parser.py"),
        ("mytourism_kpi", "src/ingestion/mytourism_kpi_parser.py"),
        ("od_panel", "src/ingestion/od_panel_parser.py"),
    ],
    "analytics": [
        ("product_value", "src/analytics/product_value.py"),
        ("corridor_network", "src/network/corridor_network.py"),
        ("panel_econometrics", "src/analytics/panel_econometrics.py"),
        ("gravity_corridor", "src/analytics/gravity_corridor_model.py"),
        ("sdg_metrics", "src/analytics/sdg_sustainable_metrics.py"),
        ("state_diagnostics", "src/analytics/state_diagnostics.py"),
        ("state_clustering", "src/analytics/state_clustering.py"),
        ("drivers_ml", "src/analytics/accommodation_drivers_ml.py"),
        ("simulator", "src/scenarios/simulator.py"),
    ],
    "validate": [
        ("accounting_fixtures", "tests/test_accounting_fixtures.py"),
        ("scenario_fixtures", "tests/test_scenario_fixtures.py"),
        ("gravity_fixtures", "tests/test_gravity_fixtures.py"),
        ("tsa_accounting", "src/validation/test_tsa_accounting.py"),
        ("state_and_corridors", "src/validation/test_state_and_corridors.py"),
    ],
    "export": [
        ("dashboard_json", "src/analytics/export_dashboard_json.py"),
    ],
}


def load_status() -> Dict:
    """Load pipeline execution status log."""
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"stages": {}, "last_run": None}


def save_status(status: Dict):
    """Save pipeline execution status log."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


def get_table_counts() -> Dict[str, int]:
    """Retrieve row counts for core analytical tables in DuckDB."""
    if not DUCKDB_PATH.exists():
        return {}
    try:
        con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        counts = {}
        for (t_name,) in tables:
            cnt = con.execute(f'SELECT count(*) FROM "{t_name}"').fetchone()[0]
            counts[t_name] = cnt
        con.close()
        return counts
    except Exception as e:
        return {"error": str(e)}


def run_step(step_name: str, script_rel_path: str) -> Tuple[bool, float, str]:
    """Execute a single python script step."""
    script_path = ROOT_DIR / script_rel_path
    if not script_path.exists():
        return False, 0.0, f"Script not found: {script_rel_path}"

    start_time = time.time()
    try:
        res = subprocess.run(
            [PYTHON_BIN, str(script_path)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=300,
        )
        elapsed = time.time() - start_time
        success = (res.returncode == 0)
        output = res.stdout if success else (res.stderr or res.stdout)
        return success, elapsed, output
    except subprocess.TimeoutExpired:
        return False, 300.0, f"Step '{step_name}' timed out after 300s"
    except Exception as e:
        return False, time.time() - start_time, str(e)


def run_stage(stage_name: str, specific_step: Optional[str] = None) -> Dict:
    """Execute a complete stage or a single step within a stage."""
    if stage_name not in STAGES:
        return {
            "success": False,
            "error": f"Unknown stage: '{stage_name}'. Valid stages: {list(STAGES.keys())}",
        }

    steps = STAGES[stage_name]
    if specific_step:
        steps = [s for s in steps if s[0] == specific_step]
        if not steps:
            return {
                "success": False,
                "error": f"Step '{specific_step}' not found in stage '{stage_name}'",
            }

    status = load_status()
    stage_results = []
    overall_success = True

    print(f"\n{'='*70}\n[PIPELINE] Running Stage: {stage_name.upper()}\n{'='*70}")

    for s_name, s_path in steps:
        print(f"  --> Running {s_name} ({s_path})...", end=" ", flush=True)
        ok, dur, out = run_step(s_name, s_path)
        print(f"{'DONE' if ok else 'FAILED'} ({dur:.1f}s)")

        step_info = {
            "step": s_name,
            "path": s_path,
            "success": ok,
            "duration_sec": round(dur, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "log_snippet": out[-500:] if out else "",
        }
        stage_results.append(step_info)
        if not ok:
            overall_success = False
            print(f"\n[ERROR in {s_name}]:\n{out}\n")
            break

    status["stages"][stage_name] = {
        "success": overall_success,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": stage_results,
    }
    status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_status(status)

    return {
        "stage": stage_name,
        "success": overall_success,
        "steps_run": len(stage_results),
        "steps": stage_results,
    }


def get_pipeline_summary() -> str:
    """Return a formatted markdown report of pipeline status and table counts."""
    status = load_status()
    counts = get_table_counts()

    lines = [
        "# Pipeline Status Summary",
        f"Last Run: {status.get('last_run', 'Never')}",
        "",
        "## Stage Status",
        f"{'Stage':<15} {'Status':<12} {'Completed At':<22} {'Steps Passed'}",
        "-" * 65,
    ]

    for st_name in ["ingest", "analytics", "validate", "export"]:
        st_data = status.get("stages", {}).get(st_name)
        if not st_data:
            lines.append(f"{st_name:<15} {'PENDING':<12} {'-':<22} -")
        else:
            ok = st_data.get("success", False)
            status_str = "SUCCESS" if ok else "FAILED"
            ts = st_data.get("completed_at", "-")
            steps = st_data.get("steps", [])
            passed = sum(1 for s in steps if s.get("success"))
            total = len(STAGES.get(st_name, []))
            lines.append(f"{st_name:<15} {status_str:<12} {ts:<22} {passed}/{total}")

    lines.extend(["", "## DuckDB Table Inventory"])
    if not counts or "error" in counts:
        lines.append(f"  DuckDB status: {counts.get('error', 'Database not found')}")
    else:
        lines.append(f"  Total Tables: {len(counts)}")
        core_tables = [
            "tourism_product_year",
            "tsa_macro_year",
            "state_year",
            "state_panel_year",
            "hotel_operations_annual",
            "origin_destination",
            "origin_destination_panel",
            "destination_concentration",
            "corridor_classification",
            "corridor_opportunity_gap",
        ]
        for tbl in core_tables:
            if tbl in counts:
                lines.append(f"  - {tbl:<32}: {counts[tbl]:>6,} rows")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Malaysia Tourism Value Optimizer Pipeline")
    parser.add_argument(
        "--stage",
        choices=["ingest", "analytics", "validate", "export", "all"],
        default="status",
        help="Pipeline stage to execute",
    )
    parser.add_argument("--step", help="Specific step to execute within the stage")
    parser.add_argument("--status", action="store_true", help="Print pipeline status summary")

    args = parser.parse_args()

    if args.status or args.stage == "status":
        print(get_pipeline_summary())
    elif args.stage == "all":
        for s in ["ingest", "analytics", "validate", "export"]:
            res = run_stage(s)
            if not res.get("success"):
                print(f"[PIPELINE STOPPED] Stage '{s}' failed.")
                sys.exit(1)
        print("\nAll pipeline stages completed successfully.")
    else:
        res = run_stage(args.stage, specific_step=args.step)
        if not res.get("success"):
            sys.exit(1)
