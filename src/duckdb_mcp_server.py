"""
DuckDB MCP Server built on official MCPServer (MCP 2.x compliant).
Connects to Malaysia Tourism Value Optimizer's DuckDB database in read-only mode
to eliminate file lock conflicts with background ingestion/analytical pipelines.
"""

import sys
from pathlib import Path
import duckdb
from mcp.server.mcpserver import MCPServer

DEFAULT_DB_PATH = Path("/home/muhammad_adib/dosm/data/processed/tourism_data.duckdb")

# Parse optional db-path argument if provided
db_path = DEFAULT_DB_PATH
if "--db-path" in sys.argv:
    idx = sys.argv.index("--db-path")
    if idx + 1 < len(sys.argv):
        db_path = Path(sys.argv[idx + 1])

# Initialize MCPServer (standard for mcp 2.x)
mcp = MCPServer(
    "duckdb",
    instructions="DuckDB query engine for Malaysia Tourism Value Optimizer analytical tables."
)


def _get_connection():
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB database file not found at: {db_path}")
    return duckdb.connect(str(db_path), read_only=True)


@mcp.tool()
def list_tables() -> list[str]:
    """List all available tables and views in the DuckDB tourism database."""
    with _get_connection() as con:
        tables = con.execute("SHOW TABLES").fetchall()
        return [t[0] for t in tables]


@mcp.tool()
def describe_table(table_name: str) -> str:
    """
    Get column names, data types, and nullability for a specified table.
    
    Args:
        table_name: Name of the table to describe.
    """
    with _get_connection() as con:
        # Sanitize table name against injection
        valid_tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if table_name not in valid_tables:
            return f"Error: Table '{table_name}' does not exist. Available tables: {valid_tables}"
        df = con.execute(f"DESCRIBE {table_name}").df()
        return df.to_string(index=False)


@mcp.tool()
def query(sql: str) -> str:
    """
    Execute a read-only SQL query against the tourism DuckDB database and return results.
    
    Args:
        sql: SQL SELECT query to execute.
    """
    # Safety check: ensure read-only execution
    clean_sql = sql.strip().upper()
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    if any(clean_sql.startswith(f) for f in forbidden):
        return "Error: Only read-only SELECT queries are permitted through this MCP interface."
    
    with _get_connection() as con:
        try:
            df = con.execute(sql).df()
            if len(df) == 0:
                return "Query executed successfully. 0 rows returned."
            # If large, limit display
            if len(df) > 100:
                preview = df.head(100).to_string(index=False)
                return f"{preview}\n\n[Display truncated: showing first 100 of {len(df)} rows]"
            return df.to_string(index=False)
        except Exception as e:
            return f"DuckDB Query Error: {str(e)}"


@mcp.tool()
def sample_table(table_name: str, limit: int = 5) -> str:
    """
    Preview the first N rows of a table.
    
    Args:
        table_name: Name of the table.
        limit: Number of rows to return (default 5, max 50).
    """
    limit = min(max(1, limit), 50)
    with _get_connection() as con:
        valid_tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if table_name not in valid_tables:
            return f"Error: Table '{table_name}' does not exist. Available: {valid_tables}"
        df = con.execute(f"SELECT * FROM {table_name} LIMIT {limit}").df()
        return df.to_string(index=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
