import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
try:
    from src.config.paths import DUCKDB_PATH
except ImportError:
    DUCKDB_PATH = ROOT_DIR / "data" / "processed" / "tourism_data.duckdb"

db_path = DUCKDB_PATH
db_path.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(db_path))
con.execute("CREATE TABLE IF NOT EXISTS meta (key VARCHAR, value VARCHAR)")
con.execute("INSERT INTO meta VALUES ('initialized', 'true')")
con.close()
print("DuckDB database initialized at:", db_path)
