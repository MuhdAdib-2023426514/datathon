---
name: analytical-review-methodology
description: >-
  Auditing playbook and validation methodology for econometric models, accounting formulas,
  synthetic fixtures, and capacity constraints in tourism economics.
---

# Analytical Review & Audit Methodology

This skill codifies the core audit principles and defect prevention patterns established in `docs/analytics-improvement-plan.md` for the **Malaysia Tourism Value Optimizer**.

---

## 1. The 10 Core Review Principles

### 1. Zero Tolerance for Fabricated Defaults
* **Anti-Pattern**: Replacing unobserved fields with hardcoded assumptions (e.g. `tourists = visitors * 0.5`, `ALOS = 2.4`, or `.fillna(0)` on required denominators).
* **Audit Rule**:
  - Distinguish between **observed zero**, **suppressed data**, and **missing/unobserved data**.
  - Missing values must remain `null` or carry an explicit quality flag (`status="imputed"`).
  - Never use `.replace(0, 1)` to bypass division-by-zero errors without logging an assertion error.

### 2. Predictive $R^2$ vs. Squared Correlation
* **Anti-Pattern**: Reporting $\text{Corr}(y, \hat{y})^2$ as model $R^2$.
* **Audit Rule**:
  - Squared correlation measures linear association, not calibration or accuracy. A model predicting double the true value can have $r^2 = 0.99$ while having a negative predictive $R^2$.
  - Always report true out-of-sample predictive $R^2$:
    $$R_{\text{pred}}^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$

### 3. Strict Temporal Separation (No Future Leakage)
* **Anti-Pattern**: Evaluating model fit on historical data using parameters or target-derived features computed from the full longitudinal dataset (or 2025 actuals).
* **Audit Rule**:
  - Train on $t \le T_{\text{train}}$ (e.g., 2018–2024), evaluate on $t > T_{\text{train}}$ (2025 actuals).
  - Feature transformations (standardization, target encoding) must be fit on training folds only.

### 4. Clustered Standard Errors in Panel Regressions
* **Anti-Pattern**: Reporting unadjusted OLS standard errors on pooled cross-sectional time series with 16 states across 8 years.
* **Audit Rule**:
  - Panel observations within the same state exhibit serial correlation.
  - Always use State-Clustered Standard Errors (`cov_type='cluster'`, `groups=df['state']`) or Huber-White robust standard errors (`HC1`).
  - Flag when statistical significance vanishes after clustering.

### 5. Portfolio-Level Capacity Feasibility
* **Anti-Pattern**: Evaluating the feasibility of single corridor interventions in isolation (e.g. Selangor $\rightarrow$ Pahang +0.5 nights is 83% AOR, KL $\rightarrow$ Pahang +0.5 nights is 82% AOR) while ignoring that both interventions compete for the **same** hotel rooms.
* **Audit Rule**:
  - Total incremental room demand across all feeder corridors must satisfy:
    $$\sum_{o} \Delta \text{RoomNights}_{o, d} \le \text{Spare Room Nights}_d = \text{Total Rooms}_d \times 365 \times \left(1 - \frac{\text{AOR}_d}{100}\right)$$
  - Implied portfolio AOR must not exceed the physical ceiling ($100\%$) or the practical saturation threshold ($80\%$).

### 6. Population Consistency in Concentration Metrics (HHI)
* **Anti-Pattern**: Mixing intra-state stayers and interstate travelers when comparing Herfindahl-Hirschman Index (HHI) across states.
* **Audit Rule**:
  - Clearly distinguish **Interstate Feeder HHI** (shares summing to 100% across 15 external states) from **All-Origin HHI** (including residents staying within their home state).
  - Label HHI figures explicitly: `hhi_interstate` vs. `hhi_total`.

### 7. Radar Scale Outlier Resistance
* **Anti-Pattern**: Using global Min-Max scaling on heavily skewed metrics (e.g., spending per night dominated by Labuan/KL), causing 15 out of 16 states to compress to zero.
* **Audit Rule**:
  - Use percentile ranking or median-anchored robust scaling for radar visualizations:
    $$\text{Score}_i = \text{clip}\left(\frac{x_i - Q_{0.05}}{Q_{0.95} - Q_{0.05}} \times 100, 0, 100\right)$$

### 8. Strict Association Language
* **Anti-Pattern**: Claiming "Increasing ALOS causes RM 120M in revenue" or "Accommodation drives TDGVA".
* **Audit Rule**:
  - Strictly follow AGENTS.md Section 9:
  - Allowed: "associated with", "econometric proxy", "scenario potential", "value-added intensive".
  - Prohibited: "proves", "causes", "guarantees", "direct causal impact".

---

## 2. Audit Checklist Before Merging Analytics Code

- [ ] All formulas verified against AGENTS.md definitions.
- [ ] No division by zero / silent fallback replacements.
- [ ] Panel models use clustered/robust covariance matrices.
- [ ] Out-of-sample evaluations use true predictive $R^2$.
- [ ] Scenario simulations display mandatory disclaimer.
- [ ] Unit tests pass via `python src/pipeline.py --stage validate`.
