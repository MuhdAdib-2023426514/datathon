import duckdb
from pathlib import Path

db_path = Path("/home/muhammad_adib/dosm/data/processed/tourism_data.duckdb")
db_path.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(db_path))
con.execute("CREATE TABLE IF NOT EXISTS meta (key VARCHAR, value VARCHAR)")
con.execute("INSERT INTO meta VALUES ('initialized', 'true')")
con.close()
print("DuckDB database initialized at:", db_path)
