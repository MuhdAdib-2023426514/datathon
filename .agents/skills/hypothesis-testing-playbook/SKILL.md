---
name: hypothesis-testing-playbook
description: >-
  Statistical method selection guide calibrated to the Malaysia tourism
  dataset sizes (16 states, 126 state-years, 240 corridors).
  Prevents common small-sample mistakes and enforces proper inference.
---

# Hypothesis Testing Playbook

This skill ensures the agent selects appropriate statistical methods for the
Malaysia Tourism Value Optimizer's specific data regime. Most tourism datasets
are small by statistical standards — this playbook prevents overconfident
conclusions from undersized samples.

---

## 1. Sample Size Reality Check

Before choosing any method, know your N:

| Dataset | N | Degrees of Freedom Budget | Appropriate Methods |
|---|---|---|---|
| Cross-section (states, single year) | 16 | ~12 usable DF | Non-parametric, exact tests, robust regression with ≤3 predictors |
| Panel (state × year) | ~126 | 16 clusters for SE | Fixed effects with clustered SE; report small-cluster caveat |
| Corridors (single year) | ~240 | Shared origin/dest structure | Gravity model, clustered by origin+destination pair |
| Corridor panel | ~1,680 | ~240 corridors × years | Panel gravity, but check temporal coverage per corridor |
| Products (year) | ~110 | ~10 products × 11 years | Descriptive, period comparison; panel only if balanced |

**Rule of thumb:** Never fit a model with more than n/10 free parameters.
With 16 states, that means ≤1–2 predictors in cross-sectional regression.

---

## 2. Decision Tree: Which Test?

### Testing Correlation

```
Is the relationship expected to be linear?
├── No, or unsure → Spearman rank correlation
└── Yes, and data is approximately normal
    └── Pearson correlation

In both cases, report:
- Coefficient with 95% CI (Fisher z-transform)
- p-value
- Sample size
- Effect size interpretation (weak/moderate/strong)
```

**Critical thresholds with n=16:**
- r must exceed ~0.50 to achieve p < 0.05 (Spearman)
- r = 0.70 gives approximate 80% power
- Correlations below 0.4 are essentially undetectable with this sample size

**Use:** `stats_engine → correlation_test(table, col_a, col_b, method='spearman')`

---

### Comparing Two Groups

```
Are both groups n ≥ 30?
├── No (typical for state subgroups) → Mann-Whitney U test
└── Yes → Welch's t-test (not Student's)

Always report:
- Test statistic and p-value
- Effect size (rank-biserial r for Mann-Whitney, Cohen's d for t-test)
- Group medians and IQRs (not just means)
```

**Use:** `stats_engine → compare_groups(table, value_col, group_col)`

---

### Comparing 3+ Groups

```
Kruskal-Wallis H test (non-parametric ANOVA)
- Report: H statistic, p-value, ε² effect size
- If significant, follow up with pairwise Mann-Whitney with Bonferroni correction
```

---

### Testing for Trend Over Time

```
Mann-Kendall trend test
- Report: Kendall's τ, p-value, Sen's slope
- Robust to non-normality and outliers
- Separate pre-COVID (2015-2019) and post-recovery (2023-2025)
```

**Use:** `stats_engine → trend_test(table, value_col, 'year')`

---

### Panel Regression

```
Fixed effects with:
- State effects (αₛ): absorb time-invariant state characteristics
- Year effects (λₜ): absorb macro shocks (COVID, policy changes)
- State-clustered standard errors: account for within-state correlation

With only 16 clusters, add:
- Small-cluster bias caveat in all reporting
- Leave-one-state-out sensitivity check
- Comparison of results with and without year effects
```

**Critical:** With 16 clusters, clustered SE may be unreliable. Consider:
- Wild cluster bootstrap (if statsmodels supports it)
- Reporting both heteroskedasticity-robust and cluster-robust SE
- Treating results as suggestive, not definitive

---

## 3. Multiple Comparisons

When testing multiple hypotheses (common in exploratory analysis):

| Number of Tests | Correction | Method |
|---|---|---|
| 2–5 planned comparisons | Bonferroni | α_adj = 0.05 / k |
| 5–20 exploratory | Benjamini-Hochberg | Controls FDR at 5% |
| >20 (correlation matrices) | Report raw and adjusted p | Flag exploratory nature |

**Rule:** Always distinguish:
- **Confirmatory tests** — pre-specified hypotheses, strict α
- **Exploratory tests** — data-driven discovery, report as "suggestive findings requiring confirmation"

---

## 4. Red Flags to Catch

These are the exact mistakes found in the improvement plan review:

| Red Flag | What Happened | Correct Approach |
|---|---|---|
| R² = squared correlation | Gravity model reported r²=0.59 as R² | Use `1 - SSE/SST` for predictive R²; report correlation separately |
| Fabricated defaults | `tourists = visitors × 0.5` when data missing | Use `NaN`; let downstream skip missing |
| Future data in predictors | Destination 2025 demand used to "predict" 2025 flows | Only use features available before the prediction period |
| Coefficient stability ignored | Single model, single specification | Compare ≥2 specifications; report if sign/significance changes |
| Small sample inflated precision | "Significant at p=0.01" with n=16 | Report CI width; note that n=16 limits detectable effects |
| COVID years dominate trends | 2020-2022 create artificial trend | Exclude or separate disruption period |
| Portfolio infeasibility | Individual corridors each feasible, but combined > 100% capacity | Aggregate before asserting feasibility |

---

## 5. Reporting Template

Every statistical result should include:

```markdown
## [Test Name]: [Variable A] × [Variable B]

**Method:** [Spearman/Pearson/Mann-Whitney/etc.]
**Sample:** n = [N], [description of sample, exclusions]
**Period:** [years included]

**Result:**
- Statistic = [value]
- 95% CI: [lower, upper]
- p-value = [value]
- Effect size: [value] ([interpretation])

**Interpretation:** [Variable A] is [associated with / not associated with]
[Variable B] (r = X, 95% CI [Y, Z], n = N).

**Limitations:**
- [Small sample caveat if n < 30]
- [Multiple comparison adjustment if applicable]
- [Period restriction if applicable]

**Note:** Association does not establish causation.
```

---

## 6. Method Selection Quick Reference

| Question Type | n < 20 | 20 ≤ n < 50 | n ≥ 50 |
|---|---|---|---|
| Correlation | Spearman + exact p | Spearman | Spearman or Pearson |
| 2-group comparison | Mann-Whitney U | Mann-Whitney U | Welch's t |
| k-group comparison | Kruskal-Wallis | Kruskal-Wallis | One-way ANOVA |
| Trend | Mann-Kendall | Mann-Kendall | Mann-Kendall or OLS |
| Regression | Robust, ≤2 predictors | OLS with robust SE | OLS or regularized |
| Panel regression | FE + report cluster caveat | FE + clustered SE | FE + clustered SE |
| Distribution test | Shapiro-Wilk | Shapiro-Wilk | D'Agostino-Pearson |

---

## 7. Language Rules (from AGENTS.md)

### ✅ Approved Phrasing
- "associated with"
- "estimated elasticity"
- "within-state association"
- "scenario estimate, not a causal forecast"
- "the data are consistent with / inconsistent with"
- "suggests a [weak/moderate/strong] [positive/negative] association"

### ❌ Prohibited Claims
- "causes", "proves", "guarantees"
- "ALOS increase will generate RM X"
- "accommodation drives TDGVA growth"
- "significant" without specifying α, test, and sample size
- Any causal claim from observational data alone
