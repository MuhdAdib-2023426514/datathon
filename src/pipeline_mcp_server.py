"""
Pipeline Runner MCP Server.
Provides tools to trigger, monitor, validate, and inspect pipeline stages
for the Malaysia Tourism Value Optimizer.
"""

import sys
import json
from pathlib import Path
from typing import Optional
from mcp.server.mcpserver import MCPServer

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.pipeline import (
    run_stage as _run_stage,
    get_pipeline_summary,
    load_status,
    get_table_counts,
    DUCKDB_PATH,
)

mcp = MCPServer(
    "pipeline_runner",
    instructions=(
        "Pipeline runner MCP server for Malaysia Tourism Value Optimizer. "
        "Allows triggering stages (ingest, analytics, validate, export), "
        "checking build status, running validation gates, and inspecting database tables."
    ),
)


@mcp.tool()
def pipeline_status() -> str:
    """Show the overall pipeline status, last run timestamps, and DuckDB table row counts."""
    return get_pipeline_summary()


@mcp.tool()
def run_stage(stage_name: str, step: Optional[str] = None) -> str:
    """Execute a specific pipeline stage ('ingest', 'analytics', 'validate', 'export')
    or a single step within that stage.
    """
    valid_stages = ["ingest", "analytics", "validate", "export"]
    if stage_name not in valid_stages:
        return f"Error: Invalid stage '{stage_name}'. Allowed: {', '.join(valid_stages)}"

    res = _run_stage(stage_name, specific_step=step)
    lines = [
        f"Stage Execution: {stage_name.upper()}",
        f"Success: {res.get('success')}",
        f"Steps Run: {res.get('steps_run', 0)}",
        "",
        "Steps Breakdown:",
    ]
    for s in res.get("steps", []):
        st_icon = "✓" if s["success"] else "✗"
        lines.append(f"  [{st_icon}] {s['step']:<20} ({s['duration_sec']}s)")
        if not s["success"] and s.get("log_snippet"):
            lines.append(f"      Error: {s['log_snippet'][-200:]}")

    return "\n".join(lines)


@mcp.tool()
def validate_outputs(stage: str = "all") -> str:
    """Run validation gates and return assertions results.
    'stage' can be 'tsa_accounting', 'state_and_corridors', or 'all'.
    """
    if stage == "all":
        res = _run_stage("validate")
    else:
        res = _run_stage("validate", specific_step=stage)

    lines = [f"Validation Report ({stage}):", f"Passed: {res.get('success')}", ""]
    for s in res.get("steps", []):
        icon = "✓" if s["success"] else "✗"
        lines.append(f"[{icon}] {s['step']} ({s['duration_sec']}s)")
        if s.get("log_snippet"):
            lines.append("--- Log Snippet ---")
            lines.append(s["log_snippet"][-400:])

    return "\n".join(lines)


@mcp.tool()
def diff_outputs(table_name: str) -> str:
    """Inspect the schema and row count of an analytical table in DuckDB."""
    import duckdb

    if not DUCKDB_PATH.exists():
        return f"Error: Database not found at {DUCKDB_PATH}"

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        tables = [
            t[0]
            for t in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
            ).fetchall()
        ]
        if table_name not in tables:
            return f"Table '{table_name}' not found. Available tables:\n" + ", ".join(tables)

        count = con.execute(f'SELECT count(*) FROM "{table_name}"').fetchone()[0]
        schema = con.execute(f'DESCRIBE "{table_name}"').df()

        lines = [
            f"Table: {table_name}",
            f"Row Count: {count:,}",
            "",
            "Schema:",
            schema.to_string(index=False),
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error inspecting table '{table_name}': {e}"
    finally:
        con.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
