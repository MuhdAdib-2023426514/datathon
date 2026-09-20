"""
Data Profiler MCP Server.
Automated dataset profiling — the "first 5 minutes" of any data scientist's
workflow, done in one tool call. Profiles tables from the tourism DuckDB
database with nulls, distributions, outliers, correlations, and anomalies.
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from mcp.server.mcpserver import MCPServer

DB_PATH = Path("/home/muhammad_adib/dosm/data/processed/tourism_data.duckdb")

mcp = MCPServer(
    "profiler",
    instructions=(
        "Data profiling engine for the Malaysia Tourism Value Optimizer. "
        "Generates automated dataset profiles including distributions, "
        "null rates, outliers, correlations, and anomaly detection."
    )
)


def _get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB database not found at: {DB_PATH}")
    return duckdb.connect(str(DB_PATH), read_only=True)


def _load_table(table_name: str) -> pd.DataFrame:
    with _get_connection() as con:
        valid = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if table_name not in valid:
            raise ValueError(
                f"Table '{table_name}' not found. Available: {valid}"
            )
        return con.execute(f"SELECT * FROM {table_name}").df()


@mcp.tool()
def profile_table(table_name: str) -> str:
    """
    Generate a comprehensive profile of a DuckDB table.
    Reports: row/column counts, per-column types, null rates, unique counts,
    numeric statistics (mean, median, std, skew, kurtosis, outliers),
    and categorical top values.

    Args:
        table_name: Name of the table to profile.
    """
    try:
        df = _load_table(table_name)
    except ValueError as e:
        return str(e)

    lines = [
        f"# Profile: {table_name}",
        f"Rows: {len(df):,} | Columns: {len(df.columns)}",
        ""
    ]

    numeric_cols = []
    for col in df.columns:
        s = df[col]
        null_count = int(s.isna().sum())
        null_pct = s.isna().mean() * 100
        unique_count = int(s.nunique())

        lines.append(f"## {col}  ({s.dtype})")
        lines.append(f"  Nulls: {null_count} ({null_pct:.1f}%)")
        lines.append(f"  Unique: {unique_count}")

        if pd.api.types.is_numeric_dtype(s):
            numeric_cols.append(col)
            clean = s.dropna()
            if len(clean) > 0:
                lines.append(
                    f"  Range: [{clean.min():.4g}, {clean.max():.4g}]"
                )
                lines.append(
                    f"  Mean: {clean.mean():.4g} | Median: {clean.median():.4g} | "
                    f"Std: {clean.std():.4g}"
                )
                if len(clean) >= 3:
                    lines.append(
                        f"  Skew: {clean.skew():.3f} | Kurtosis: {clean.kurtosis():.3f}"
                    )
                # IQR outlier detection
                q1 = clean.quantile(0.25)
                q3 = clean.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    outlier_count = int(
                        ((clean < q1 - 1.5 * iqr) | (clean > q3 + 1.5 * iqr)).sum()
                    )
                    if outlier_count > 0:
                        lines.append(f"  ⚠️ Outliers (IQR method): {outlier_count}")
                # Percentiles
                pcts = clean.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
                lines.append(
                    f"  Percentiles: p5={pcts.iloc[0]:.4g} p25={pcts.iloc[1]:.4g} "
                    f"p50={pcts.iloc[2]:.4g} p75={pcts.iloc[3]:.4g} p95={pcts.iloc[4]:.4g}"
                )
            else:
                lines.append("  (all null)")
        else:
            # Categorical / string column
            top = s.value_counts().head(5)
            if len(top) > 0:
                top_str = ", ".join(
                    f"{k} ({v})" for k, v in top.items()
                )
                lines.append(f"  Top values: {top_str}")

        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def profile_column(table_name: str, column: str) -> str:
    """
    Deep-dive profile on a single column: full distribution, histogram bins,
    percentiles, and top values.

    Args:
        table_name: Name of the table.
        column: Column name to profile.
    """
    try:
        df = _load_table(table_name)
    except ValueError as e:
        return str(e)

    if column not in df.columns:
        return f"Column '{column}' not found. Available: {list(df.columns)}"

    s = df[column]
    lines = [
        f"# Column Profile: {table_name}.{column}",
        f"Type: {s.dtype}",
        f"Total: {len(s):,} | Nulls: {s.isna().sum()} ({s.isna().mean()*100:.1f}%)",
        f"Unique: {s.nunique()}",
        ""
    ]

    if pd.api.types.is_numeric_dtype(s):
        clean = s.dropna()
        if len(clean) == 0:
            lines.append("(all null)")
            return "\n".join(lines)

        lines.append("## Statistics")
        lines.append(f"  Min: {clean.min():.6g}")
        lines.append(f"  Max: {clean.max():.6g}")
        lines.append(f"  Mean: {clean.mean():.6g}")
        lines.append(f"  Median: {clean.median():.6g}")
        lines.append(f"  Std Dev: {clean.std():.6g}")
        lines.append(f"  Variance: {clean.var():.6g}")
        if len(clean) >= 3:
            lines.append(f"  Skewness: {clean.skew():.4f}")
            lines.append(f"  Kurtosis: {clean.kurtosis():.4f}")

        lines.append("")
        lines.append("## Percentiles")
        for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            val = clean.quantile(p / 100)
            lines.append(f"  p{p}: {val:.6g}")

        lines.append("")
        lines.append("## Distribution (10 bins)")
        counts, bin_edges = np.histogram(clean, bins=10)
        for i, count in enumerate(counts):
            lo = bin_edges[i]
            hi = bin_edges[i + 1]
            bar = "█" * max(1, int(count / max(counts) * 30))
            lines.append(f"  [{lo:>10.4g}, {hi:>10.4g}): {count:>5d} {bar}")

        # Zeros
        zero_count = int((clean == 0).sum())
        if zero_count > 0:
            lines.append(f"\n  Exact zeros: {zero_count}")

    else:
        lines.append("## Value Counts (all)")
        vc = s.value_counts()
        for val, count in vc.items():
            pct = count / len(s) * 100
            lines.append(f"  {val}: {count} ({pct:.1f}%)")

    return "\n".join(lines)


@mcp.tool()
def compare_columns(table_name: str, col_a: str, col_b: str) -> str:
    """
    Compare two numeric columns: correlation (Pearson & Spearman),
    complete-pair count, and basic joint statistics.

    Args:
        table_name: Name of the table.
        col_a: First column name.
        col_b: Second column name.
    """
    from scipy import stats

    try:
        df = _load_table(table_name)
    except ValueError as e:
        return str(e)

    for c in [col_a, col_b]:
        if c not in df.columns:
            return f"Column '{c}' not found. Available: {list(df.columns)}"

    pair = df[[col_a, col_b]].dropna()
    n = len(pair)

    if n < 3:
        return f"Only {n} complete pairs available — insufficient for correlation."

    a, b = pair[col_a], pair[col_b]

    lines = [
        f"# Comparison: {col_a} vs {col_b}",
        f"Complete pairs: {n}",
        ""
    ]

    # Pearson
    r_p, p_p = stats.pearsonr(a, b)
    lines.append(f"## Pearson Correlation")
    lines.append(f"  r = {r_p:.4f}, p = {p_p:.4e}")

    # Spearman
    r_s, p_s = stats.spearmanr(a, b)
    lines.append(f"## Spearman Correlation")
    lines.append(f"  rho = {r_s:.4f}, p = {p_s:.4e}")

    # Fisher CI for Spearman
    if n > 3:
        z = np.arctanh(r_s)
        se = 1.0 / np.sqrt(n - 3)
        ci_lo = np.tanh(z - 1.96 * se)
        ci_hi = np.tanh(z + 1.96 * se)
        lines.append(f"  95% CI: [{ci_lo:.4f}, {ci_hi:.4f}]")

    # Interpretation
    strength = "strong" if abs(r_s) > 0.7 else "moderate" if abs(r_s) > 0.4 else "weak"
    direction = "positive" if r_s > 0 else "negative"
    sig = "significant" if p_s < 0.05 else "not significant"
    lines.append("")
    lines.append(
        f"Interpretation: {strength} {direction} association, "
        f"{sig} at α=0.05 (n={n})."
    )
    lines.append("Note: Association does not establish causation.")

    return "\n".join(lines)


@mcp.tool()
def detect_anomalies(table_name: str) -> str:
    """
    Scan a table for data quality anomalies:
    - High null rates (>20%)
    - Constant columns (0 variance)
    - Extreme skew (|skew| > 3)
    - Duplicate rows
    - Suspicious patterns (negative values in non-negative fields)

    Args:
        table_name: Name of the table to scan.
    """
    try:
        df = _load_table(table_name)
    except ValueError as e:
        return str(e)

    lines = [f"# Anomaly Scan: {table_name}", ""]
    issues_found = 0

    # Duplicate rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        lines.append(f"⚠️ Duplicate rows: {dup_count}")
        issues_found += 1

    for col in df.columns:
        s = df[col]
        col_issues = []

        # High nulls
        null_pct = s.isna().mean() * 100
        if null_pct > 20:
            col_issues.append(f"High nulls: {null_pct:.1f}%")

        if pd.api.types.is_numeric_dtype(s):
            clean = s.dropna()
            if len(clean) > 0:
                # Constant
                if clean.std() == 0:
                    col_issues.append("Constant (zero variance)")

                # Extreme skew
                if len(clean) >= 3:
                    skew = clean.skew()
                    if abs(skew) > 3:
                        col_issues.append(f"Extreme skew: {skew:.2f}")

                # Negative values in likely non-negative fields
                non_neg_hints = [
                    'expenditure', 'visitors', 'tourists', 'trips',
                    'flow', 'population', 'rooms', 'supply', 'gva',
                    'itc', 'employment', 'alos', 'occupancy'
                ]
                if any(h in col.lower() for h in non_neg_hints):
                    neg_count = int((clean < 0).sum())
                    if neg_count > 0:
                        col_issues.append(f"Negative values: {neg_count}")

        if col_issues:
            issues_found += len(col_issues)
            lines.append(f"## {col}")
            for issue in col_issues:
                lines.append(f"  ⚠️ {issue}")

    if issues_found == 0:
        lines.append("✅ No anomalies detected.")
    else:
        lines.append(f"\nTotal issues found: {issues_found}")

    return "\n".join(lines)


@mcp.tool()
def correlation_matrix(table_name: str, method: str = "spearman", min_periods: int = 5) -> str:
    """
    Compute a correlation matrix for all numeric columns in a table.

    Args:
        table_name: Name of the table.
        method: Correlation method ('pearson' or 'spearman').
        min_periods: Minimum number of non-null pairs required.
    """
    try:
        df = _load_table(table_name)
    except ValueError as e:
        return str(e)

    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return "Fewer than 2 numeric columns — cannot compute correlation matrix."

    corr = numeric.corr(method=method, min_periods=min_periods)

    lines = [
        f"# {method.title()} Correlation Matrix: {table_name}",
        f"Numeric columns: {corr.shape[0]}",
        ""
    ]

    # Format as aligned table
    lines.append(corr.round(3).to_string())

    # Highlight strong correlations (excluding diagonal)
    lines.append("\n## Notable Correlations (|r| > 0.6)")
    pairs_seen = set()
    for i, row_name in enumerate(corr.index):
        for j, col_name in enumerate(corr.columns):
            if i >= j:
                continue
            r = corr.iloc[i, j]
            if abs(r) > 0.6 and not np.isnan(r):
                pair_key = tuple(sorted([row_name, col_name]))
                if pair_key not in pairs_seen:
                    pairs_seen.add(pair_key)
                    direction = "+" if r > 0 else "-"
                    lines.append(f"  {direction} {row_name} × {col_name}: {r:.3f}")

    if not pairs_seen:
        lines.append("  (none found)")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
