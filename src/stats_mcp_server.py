"""
Statistical Testing Engine MCP Server.
Pre-built statistical tests with automatic result interpretation,
proper inference (confidence intervals, effect sizes), and
language guardrails aligned with AGENTS.md.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
import pandas as pd
import numpy as np
from scipy import stats
from mcp.server.mcpserver import MCPServer

try:
    from src.config.paths import DUCKDB_PATH
except ImportError:
    DUCKDB_PATH = ROOT_DIR / "data" / "processed" / "tourism_data.duckdb"

DB_PATH = DUCKDB_PATH

mcp = MCPServer(
    "stats_engine",
    instructions=(
        "Statistical testing engine for the Malaysia Tourism Value Optimizer. "
        "Provides pre-built statistical tests with proper inference, confidence intervals, "
        "effect sizes, and cautious interpretation language. All results use association "
        "language per AGENTS.md — never causal claims."
    )
)


def _load(table_name: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        valid = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        if table_name not in valid:
            raise ValueError(f"Table '{table_name}' not found. Available: {valid}")
        return con.execute(f"SELECT * FROM {table_name}").df()


def _fisher_ci(r: float, n: int, alpha: float = 0.05):
    """Fisher z-transform confidence interval for a correlation coefficient."""
    if n <= 3:
        return (np.nan, np.nan)
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    return (np.tanh(z - z_crit * se), np.tanh(z + z_crit * se))


@mcp.tool()
def correlation_test(
    table: str, col_a: str, col_b: str, method: str = "spearman"
) -> str:
    """
    Test correlation between two columns with proper inference.
    Reports: coefficient, p-value, 95% CI, sample size, effect interpretation.

    Args:
        table: Table name in the tourism database.
        col_a: First column name.
        col_b: Second column name.
        method: 'spearman' (default, robust) or 'pearson'.
    """
    df = _load(table)
    for c in [col_a, col_b]:
        if c not in df.columns:
            return f"Column '{c}' not found. Available: {list(df.columns)}"

    pair = df[[col_a, col_b]].dropna()
    n = len(pair)
    if n < 3:
        return f"Only {n} complete pairs — insufficient for correlation test."

    a, b = pair[col_a].values, pair[col_b].values

    if method == "spearman":
        r, p = stats.spearmanr(a, b)
        label = "Spearman rho"
    else:
        r, p = stats.pearsonr(a, b)
        label = "Pearson r"

    ci_lo, ci_hi = _fisher_ci(r, n)

    # Effect size interpretation
    abs_r = abs(r)
    if abs_r >= 0.7:
        strength = "strong"
    elif abs_r >= 0.4:
        strength = "moderate"
    elif abs_r >= 0.2:
        strength = "weak"
    else:
        strength = "negligible"

    direction = "positive" if r > 0 else "negative"
    sig = "statistically significant" if p < 0.05 else "not statistically significant"

    lines = [
        f"## {method.title()} Correlation Test: {col_a} × {col_b}",
        f"{label} = {r:.4f}",
        f"95% CI: [{ci_lo:.4f}, {ci_hi:.4f}]",
        f"p-value = {p:.4e}",
        f"Sample size: {n}",
        "",
        f"**Interpretation:** {strength.title()} {direction} association, "
        f"{sig} at α = 0.05.",
        "",
        "_Note: Association does not establish causation._"
    ]

    # Small-sample warning
    if n < 20:
        lines.append(
            f"\n⚠️ Small sample (n={n}). Correlation estimates are imprecise; "
            f"the CI width reflects this uncertainty."
        )

    return "\n".join(lines)


@mcp.tool()
def compare_groups(
    table: str, value_col: str, group_col: str
) -> str:
    """
    Compare a numeric variable across groups. Automatically selects:
    - 2 groups: Mann-Whitney U test (non-parametric)
    - 3+ groups: Kruskal-Wallis H test
    Reports: test statistic, p-value, effect size, group medians.

    Args:
        table: Table name.
        value_col: Numeric column to compare.
        group_col: Categorical grouping column.
    """
    df = _load(table)
    for c in [value_col, group_col]:
        if c not in df.columns:
            return f"Column '{c}' not found. Available: {list(df.columns)}"

    clean = df[[value_col, group_col]].dropna()
    groups = clean[group_col].unique()
    k = len(groups)

    if k < 2:
        return f"Only {k} group(s) found in '{group_col}' — need at least 2."

    group_data = [
        clean[clean[group_col] == g][value_col].values for g in groups
    ]

    lines = [
        f"## Group Comparison: {value_col} by {group_col}",
        f"Groups: {k} | Total observations: {len(clean)}",
        ""
    ]

    # Group summaries
    lines.append("### Group Summaries")
    for g, data in zip(groups, group_data):
        lines.append(
            f"  {g}: n={len(data)}, median={np.median(data):.4g}, "
            f"mean={np.mean(data):.4g}, std={np.std(data, ddof=1):.4g}"
        )
    lines.append("")

    if k == 2:
        stat, p = stats.mannwhitneyu(
            group_data[0], group_data[1], alternative='two-sided'
        )
        # Rank-biserial effect size
        n1, n2 = len(group_data[0]), len(group_data[1])
        r_rb = 1 - (2 * stat) / (n1 * n2)

        lines.append("### Mann-Whitney U Test")
        lines.append(f"  U = {stat:.2f}, p = {p:.4e}")
        lines.append(f"  Rank-biserial r = {r_rb:.4f}")

        abs_r = abs(r_rb)
        effect = "large" if abs_r >= 0.5 else "medium" if abs_r >= 0.3 else "small"
        sig = "significant" if p < 0.05 else "not significant"
        lines.append(
            f"\n  **Interpretation:** {effect.title()} effect size, "
            f"{sig} difference at α = 0.05."
        )
    else:
        stat, p = stats.kruskal(*group_data)
        # Epsilon-squared effect size
        n_total = len(clean)
        eps2 = (stat - k + 1) / (n_total - k)

        lines.append("### Kruskal-Wallis H Test")
        lines.append(f"  H = {stat:.2f}, p = {p:.4e}")
        lines.append(f"  ε² (epsilon-squared) = {eps2:.4f}")

        effect = "large" if eps2 >= 0.14 else "medium" if eps2 >= 0.06 else "small"
        sig = "significant" if p < 0.05 else "not significant"
        lines.append(
            f"\n  **Interpretation:** {effect.title()} effect size, "
            f"{sig} at α = 0.05."
        )

    lines.append("\n_Note: Association does not establish causation._")
    return "\n".join(lines)


@mcp.tool()
def trend_test(table: str, value_col: str, time_col: str = "year") -> str:
    """
    Mann-Kendall trend test for a time series.
    Reports: trend direction, Kendall's tau, p-value, Sen's slope.

    Args:
        table: Table name.
        value_col: Numeric column to test for trend.
        time_col: Time/ordering column (default: 'year').
    """
    df = _load(table)
    for c in [value_col, time_col]:
        if c not in df.columns:
            return f"Column '{c}' not found. Available: {list(df.columns)}"

    clean = df[[time_col, value_col]].dropna().sort_values(time_col)
    n = len(clean)
    if n < 4:
        return f"Only {n} observations — need at least 4 for trend test."

    x = clean[time_col].values
    y = clean[value_col].values

    # Kendall's tau as trend measure
    tau, p = stats.kendalltau(x, y)

    # Sen's slope (median of all pairwise slopes)
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            if x[j] != x[i]:
                slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    sen_slope = np.median(slopes) if slopes else np.nan

    direction = "increasing" if tau > 0 else "decreasing" if tau < 0 else "no"
    sig = "significant" if p < 0.05 else "not significant"

    lines = [
        f"## Mann-Kendall Trend Test: {value_col} over {time_col}",
        f"Observations: {n} ({clean[time_col].min()} – {clean[time_col].max()})",
        f"Kendall's τ = {tau:.4f}",
        f"p-value = {p:.4e}",
        f"Sen's slope = {sen_slope:.6g} per unit of {time_col}",
        "",
        f"**Interpretation:** {direction.title()} trend, {sig} at α = 0.05.",
    ]

    return "\n".join(lines)


@mcp.tool()
def normality_test(table: str, column: str) -> str:
    """
    Test whether a column follows a normal distribution.
    Uses Shapiro-Wilk (n < 50) or D'Agostino-Pearson (n >= 50).

    Args:
        table: Table name.
        column: Column to test.
    """
    df = _load(table)
    if column not in df.columns:
        return f"Column '{column}' not found. Available: {list(df.columns)}"

    clean = df[column].dropna()
    n = len(clean)
    if n < 3:
        return f"Only {n} observations — need at least 3."

    lines = [
        f"## Normality Test: {table}.{column}",
        f"Sample size: {n}",
        f"Skewness: {clean.skew():.4f}",
        f"Kurtosis: {clean.kurtosis():.4f}",
        ""
    ]

    if n < 50:
        stat, p = stats.shapiro(clean)
        test_name = "Shapiro-Wilk"
    else:
        stat, p = stats.normaltest(clean)
        test_name = "D'Agostino-Pearson"

    normal = "consistent with" if p >= 0.05 else "not consistent with"

    lines.append(f"### {test_name} Test")
    lines.append(f"  Statistic = {stat:.4f}, p = {p:.4e}")
    lines.append(f"\n  **Interpretation:** Distribution is {normal} normality at α = 0.05.")

    if p < 0.05:
        lines.append(
            "  → Prefer non-parametric methods (Spearman, Mann-Whitney, Kruskal-Wallis)."
        )

    return "\n".join(lines)


@mcp.tool()
def panel_summary(
    table: str, entity_col: str, time_col: str, value_col: str
) -> str:
    """
    Decompose a panel variable into within-entity and between-entity variation.
    Useful for understanding whether variation is cross-sectional or longitudinal.

    Args:
        table: Table name.
        entity_col: Panel entity column (e.g. 'state').
        time_col: Time column (e.g. 'year').
        value_col: Numeric variable to decompose.
    """
    df = _load(table)
    for c in [entity_col, time_col, value_col]:
        if c not in df.columns:
            return f"Column '{c}' not found. Available: {list(df.columns)}"

    clean = df[[entity_col, time_col, value_col]].dropna()
    n = len(clean)
    n_entities = clean[entity_col].nunique()
    n_periods = clean[time_col].nunique()

    overall_mean = clean[value_col].mean()
    overall_var = clean[value_col].var()

    # Between-entity variation (variance of entity means)
    entity_means = clean.groupby(entity_col)[value_col].mean()
    between_var = entity_means.var()

    # Within-entity variation (mean of entity variances)
    entity_vars = clean.groupby(entity_col)[value_col].var()
    within_var = entity_vars.mean()

    between_pct = between_var / overall_var * 100 if overall_var > 0 else 0
    within_pct = within_var / overall_var * 100 if overall_var > 0 else 0

    lines = [
        f"## Panel Decomposition: {value_col}",
        f"Entity: {entity_col} ({n_entities} units)",
        f"Time: {time_col} ({n_periods} periods)",
        f"Observations: {n}",
        "",
        f"Overall mean: {overall_mean:.4g}",
        f"Overall std: {np.sqrt(overall_var):.4g}",
        "",
        f"Between-entity variation: {between_pct:.1f}% of total",
        f"  (entity means range: {entity_means.min():.4g} – {entity_means.max():.4g})",
        f"Within-entity variation: {within_pct:.1f}% of total",
        "",
    ]

    if between_pct > 70:
        lines.append(
            "**Interpretation:** Most variation is between entities. "
            "Cross-sectional differences dominate; fixed effects will absorb this. "
            "Within-entity coefficients rely on relatively little variation."
        )
    elif within_pct > 70:
        lines.append(
            "**Interpretation:** Most variation is within entities over time. "
            "Fixed-effects models have good power to detect within-entity associations."
        )
    else:
        lines.append(
            "**Interpretation:** Substantial variation both between and within entities. "
            "Fixed-effects models will use within-entity variation; random-effects or "
            "pooled models would also capture between-entity differences."
        )

    # Top/bottom entities
    lines.append(f"\n### Highest Mean {value_col}")
    for name, val in entity_means.nlargest(5).items():
        lines.append(f"  {name}: {val:.4g}")
    lines.append(f"\n### Lowest Mean {value_col}")
    for name, val in entity_means.nsmallest(5).items():
        lines.append(f"  {name}: {val:.4g}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
