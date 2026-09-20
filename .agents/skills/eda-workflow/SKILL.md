---
name: eda-workflow
description: >-
  Structured EDA workflow for Malaysia Tourism data.
  Guides the agent through systematic data exploration,
  hypothesis formation, and statistical validation.
---

# Exploratory Data Analysis Workflow for Tourism Data

This skill defines the systematic approach the agent must follow when
exploring data interactively. It transforms ad-hoc code writing into a
methodical data science workflow.

## Available Tools

Use these MCP tools for exploration:

| Tool | Server | When to Use |
|---|---|---|
| `execute(code)` | `datasci` | Interactive Python: quick stats, transforms, custom analysis |
| `execute(code, save_chart='name.png')` | `datasci` | Generate and save matplotlib charts |
| `get_variables()` | `datasci` | Check what's loaded in the session |
| `profile_table(table)` | `profiler` | First look at any table: types, nulls, distributions |
| `profile_column(table, col)` | `profiler` | Deep dive on a single column |
| `compare_columns(table, a, b)` | `profiler` | Bivariate correlation with CI |
| `detect_anomalies(table)` | `profiler` | Automated data quality scan |
| `correlation_matrix(table)` | `profiler` | Full correlation heatmap |
| `correlation_test(table, a, b)` | `stats_engine` | Formal hypothesis test with proper inference |
| `compare_groups(table, val, group)` | `stats_engine` | Group comparison with effect sizes |
| `trend_test(table, val, time)` | `stats_engine` | Mann-Kendall trend detection |
| `normality_test(table, col)` | `stats_engine` | Distribution shape test → method selection |
| `panel_summary(table, entity, time, val)` | `stats_engine` | Within vs between variation decomposition |
| `query(sql)` | `duckdb` | Custom SQL queries on the tourism database |

---

## Step 1: Profile Before You Model

Before any analysis, always run these checks:

```
profiler → profile_table('state_year')
profiler → detect_anomalies('state_year')
```

Check for:
- Row counts: Does it match expectations? (16 states × N years)
- Null rates: Which columns have missing data? Is it MCAR/MAR/MNAR?
- Value distributions: Are numeric columns bounded correctly?
- Key alignment: Do state names match between tables?

**Rule:** Never start modelling until you understand the data.

---

## Step 2: Explore Univariate Distributions

For each key metric, understand its distribution shape:

| Metric | Expected Shape | Watch For |
|---|---|---|
| VAI | Bounded [0, 1] | Values near 0 or 1 may need investigation |
| ALOS | Right-skewed, positive | Zero or negative = data error |
| accommodation_expenditure | Right-skewed | Extreme outliers (KL, Selangor?) |
| tourist_flow | Highly skewed | Many small flows, few large ones |
| tourism_ratio | Bounded [0, 1] | Values > 1 = accounting anomaly |

```
profiler → profile_column('state_year', 'alos')
stats_engine → normality_test('state_year', 'accommodation_expenditure')
```

**Decision point:** If distribution is non-normal (most tourism variables are),
prefer non-parametric methods: Spearman over Pearson, Mann-Whitney over t-test.

---

## Step 3: Explore Bivariate Relationships

Priority pairs for this project (per AGENTS.md research questions):

1. **ALOS × accommodation_expenditure** — core project hypothesis
2. **tourists × total_expenditure** — volume vs value relationship
3. **VAI × ITC** — efficiency vs scale quadrant (Stage B classification)
4. **tourist_flow × destination ALOS** — corridor opportunity identification

```
stats_engine → correlation_test('state_year', 'alos', 'accommodation_expenditure')
profiler → compare_columns('state_year', 'tourists', 'total_expenditure')
```

**Always report:** method, sample size, confidence interval, p-value, effect size.
**Always use:** "associated with" language, never causal claims.

---

## Step 4: Temporal Patterns

The 2015–2025 period has a massive structural break (COVID).

**Use these periods:**
- Pre-COVID: 2015–2019 (structural baseline)
- Disruption/recovery: 2020–2022 (anomaly — do NOT let this dominate conclusions)
- Post-recovery: 2023–2025 (current reality)

```python
# In datasci session:
pre = state_panel[state_panel['year'].between(2015, 2019)]
post = state_panel[state_panel['year'].between(2023, 2025)]
# Compare distributions, not just means
```

**Critical rule:** A trend that only holds because of COVID-year values is not
a structural trend. Always check with 2020–2022 excluded.

---

## Step 5: State-Level Heterogeneity

Malaysia has extreme heterogeneity across its 16 states/FTs:

| State Type | Example | Characteristic |
|---|---|---|
| Urban mega-destinations | KL, Selangor | Huge volume, may dominate aggregates |
| Tourism-driven states | Sabah, Sarawak, Penang | Long ALOS, high spend per night |
| Transit/day-trip states | Melaka, Perak | High excursionist ratio |
| Small FTs | Putrajaya, Labuan, Perlis | Tiny sample, extreme values |

**Analysis checklist:**
- Are results driven by 1–2 outlier states? (Leave-one-out check)
- Does the relationship hold within regions? (Northern, East Coast, etc.)
- Are Federal Territories distorting state-level patterns?

```python
# Leave-one-out sensitivity
for drop_state in state_year['state'].unique():
    subset = state_year[state_year['state'] != drop_state]
    r, p = spearmanr(subset['alos'], subset['accommodation_expenditure'])
    print(f"Excluding {drop_state}: r={r:.3f}, p={p:.3f}")
```

---

## Step 6: Form Testable Hypotheses

Before modelling, write down explicit hypotheses:

**Template:**
```
H0: [null — no relationship / no difference]
H1: [alternative — specific direction if theory supports it]
Test: [statistical method, with justification]
Assumptions: [what must hold for the test to be valid]
Sample: [exact N, exclusions, period]
α: 0.05 (state if different)
```

**Example for this project:**
```
H0: Within-state changes in ALOS are not associated with changes
    in accommodation expenditure, controlling for year effects.
H1: Positive within-state association (longer stays → higher spend).
Test: Panel fixed-effects regression with state and year effects,
      state-clustered standard errors.
Assumptions: Within-state linearity, no severe serial correlation.
Sample: 16 states × 8 years = 126 state-year observations (after
        excluding unavailable years). Only 16 clusters for SE.
α: 0.05
```

---

## Step 7: Document and Iterate

After each exploration round, record in the session or a markdown artifact:

1. **What was tested** — exact variables, methods, sample
2. **What was found** — numbers, not just "significant" or "interesting"
3. **What this suggests** — next analysis step, hypothesis refinement
4. **Data quality issues** — any problems discovered along the way

**Use the Memory MCP** to persist key findings across sessions:
```
memory → create_entities([{name: "finding_alos_accom", ...}])
```

---

## Anti-Patterns to Avoid

| ❌ Don't | ✅ Do Instead |
|---|---|
| Run 20 correlations, report the significant ones | Pre-register hypotheses, adjust for multiple comparisons |
| Use full dataset including COVID years for trend | Separate pre/post periods, note structural break |
| Report r=0.85 without mentioning n=16 | Always: r, CI, p, n |
| Use Pearson on skewed expenditure data | Check normality first → prefer Spearman |
| Say "ALOS drives accommodation spending" | Say "ALOS is associated with higher accommodation expenditure" |
| Fit a model with 10 features on 16 observations | Keep models parsimonious: features << observations |
| Treat a coefficient as causal proof | Report as "estimated association" with uncertainty |
