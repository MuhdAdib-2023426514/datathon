"""
Python Data Science Sandbox MCP Server.
Provides a persistent Python REPL session pre-loaded with data science
libraries and the tourism database, enabling interactive exploration,
statistical testing, and chart generation.
"""

import sys
import io
import os
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp.server.mcpserver import MCPServer

try:
    from src.config.paths import DUCKDB_PATH, CHARTS_DIR
except ImportError:
    DUCKDB_PATH = ROOT_DIR / "data" / "processed" / "tourism_data.duckdb"
    CHARTS_DIR = ROOT_DIR / "data" / "charts"

DB_PATH = DUCKDB_PATH
CHART_DIR = CHARTS_DIR

mcp = MCPServer(
    "datasci",
    instructions=(
        "Interactive Python data science sandbox with persistent state. "
        "Pre-loaded with pandas, numpy, scipy, statsmodels, matplotlib, "
        "scikit-learn, and a read-only connection to the tourism DuckDB database. "
        "Core tables (state_year, tourism_product_year, origin_destination) "
        "are available as DataFrames. Use sql('SELECT ...') for custom queries."
    )
)

# Persistent execution namespace — survives between tool calls
_session: dict = {}
_initialized: bool = False


def _init_session():
    """Initialize the persistent session with libraries and data."""
    global _initialized
    if _initialized:
        return

    # Use Agg backend so matplotlib never tries to open a GUI window
    os.environ.setdefault("MPLBACKEND", "Agg")

    init_code = f"""
import pandas as pd
import numpy as np
import duckdb
from scipy import stats as scipy_stats
from scipy.stats import spearmanr, pearsonr, mannwhitneyu, kruskal
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

def sql(query):
    \"\"\"Execute a SQL query against the tourism database and return a DataFrame.\"\"\"
    with duckdb.connect(f'{DB_PATH}', read_only=True) as con:
        return con.execute(query).df()

def tables():
    \"\"\"List all tables in the tourism database.\"\"\"
    with duckdb.connect(f'{DB_PATH}', read_only=True) as con:
        return [t[0] for t in con.execute("SHOW TABLES").fetchall()]

# Pre-load core analytical tables
_available_tables = tables()
_loaded = []

if 'state_year' in _available_tables:
    state_year = sql("SELECT * FROM state_year")
    _loaded.append(f"  state_year: {{state_year.shape}}")

if 'tourism_product_year' in _available_tables:
    tourism_product = sql("SELECT * FROM tourism_product_year")
    _loaded.append(f"  tourism_product: {{tourism_product.shape}}")

if 'origin_destination' in _available_tables:
    od = sql("SELECT * FROM origin_destination")
    _loaded.append(f"  od: {{od.shape}}")

if 'state_panel_year' in _available_tables:
    state_panel = sql("SELECT * FROM state_panel_year")
    _loaded.append(f"  state_panel: {{state_panel.shape}}")

if 'tsa_macro_year' in _available_tables:
    tsa_macro = sql("SELECT * FROM tsa_macro_year")
    _loaded.append(f"  tsa_macro: {{tsa_macro.shape}}")

if 'origin_destination_panel' in _available_tables:
    od_panel = sql("SELECT * FROM origin_destination_panel")
    _loaded.append(f"  od_panel: {{od_panel.shape}}")

print("Session ready. Pre-loaded tables:")
for line in _loaded:
    print(line)
print(f"\\nAll tables: {{_available_tables}}")
print("Use sql('SELECT ...') for custom queries, tables() to list tables.")
"""
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        exec(init_code, _session)
        _initialized = True
        output = buffer.getvalue()
        # Store init output for reference but don't return it every time
        _session["_init_output"] = output
    except Exception as e:
        raise RuntimeError(f"Session initialization failed: {e}")
    finally:
        sys.stdout = old_stdout


def _capture_output(code: str, save_chart: str = "") -> str:
    """Execute code in the persistent session, capturing stdout and optional charts."""
    _init_session()

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        # Try eval first (for expressions like df.head(), x + y)
        try:
            result = eval(code, _session)
            if result is not None:
                # Pretty-print DataFrames and Series
                if hasattr(result, 'to_string'):
                    print(result.to_string())
                else:
                    print(repr(result))
        except SyntaxError:
            # Fall back to exec for statements (assignments, loops, etc.)
            exec(code, _session)

        output = buffer.getvalue()

        # Capture chart if requested
        if save_chart:
            plt = _session.get("plt")
            if plt and plt.get_fignums():
                CHART_DIR.mkdir(parents=True, exist_ok=True)
                chart_path = CHART_DIR / save_chart
                plt.savefig(str(chart_path), dpi=150, bbox_inches='tight',
                            facecolor='white', edgecolor='none')
                plt.close('all')
                output += f"\n[Chart saved: {chart_path}]"
            elif plt:
                output += "\n[No active matplotlib figure to save]"

        return output.strip() if output.strip() else "(executed successfully, no output)"

    except Exception:
        return f"Error:\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout


@mcp.tool()
def execute(code: str, save_chart: str = "") -> str:
    """
    Execute Python code in a persistent data science session.

    Variables persist between calls. The following are pre-imported:
    pandas (pd), numpy (np), scipy.stats, statsmodels, matplotlib.pyplot (plt),
    scikit-learn, duckdb. Core tourism tables are loaded as DataFrames:
    state_year, tourism_product, od, state_panel, tsa_macro, od_panel.

    Use sql('SELECT ...') for custom queries. Use tables() to list all tables.

    Args:
        code: Python code to execute. Can be an expression (returns value)
              or statements (prints output).
        save_chart: Optional filename (e.g. 'scatter.png') to save the current
                    matplotlib figure. Saved to data/charts/.
    """
    return _capture_output(code, save_chart)


@mcp.tool()
def get_variables() -> str:
    """List all user-defined variables in the current session with types and shapes."""
    _init_session()

    skip = {
        '__builtins__', '_db', '_available_tables', '_loaded',
        '_init_output', 'warnings'
    }
    # Standard library/module names to skip
    module_types = type(sys)

    result = []
    for name, val in sorted(_session.items()):
        if name.startswith('_') or name in skip:
            continue
        if isinstance(val, (module_types, type)):
            continue
        if callable(val) and not hasattr(val, 'shape'):
            continue

        info = f"  {name}: {type(val).__name__}"
        if hasattr(val, 'shape'):
            info += f"  shape={val.shape}"
        elif hasattr(val, '__len__') and not isinstance(val, str):
            info += f"  len={len(val)}"
        result.append(info)

    return "\n".join(result) if result else "(no user variables in session)"


@mcp.tool()
def reset_session() -> str:
    """Clear all variables and restart the session with fresh imports and data."""
    global _session, _initialized
    _session = {}
    _initialized = False
    _init_session()
    return "Session reset and re-initialized.\n" + _session.get("_init_output", "")


if __name__ == "__main__":
    mcp.run(transport="stdio")
