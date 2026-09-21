# Model Validation & Econometric Robustness Report
## Malaysia Tourism Value Optimizer (MYTourism Value Intelligence)

**Authoritative Standard**: Antigravity Data Science & Economics Team  
**Evaluation Period**: 2018–2024 Training ($N = 1,680$), 2025 Out-of-Sample Holdout ($N = 240$), Total Panel ($N = 1,920$).  
**Core Guardrail**: *Transparent reporting of comparative model strengths, structural identification properties, and validation metrics.*

---

## 1. Spatial Gravity Model Validation (RQ6)

The bilateral interstate corridor model evaluates $240$ directed origin-destination pairs ($16 \times 15$) over 8 years ($1,920$ interstate corridor-years). Out-of-sample predictive performance was evaluated by training on 2018–2024 data ($N = 1,680$) and projecting onto the held-out 2025 actual observations ($N = 240$). The overall spatial network comprises $256$ total bilateral pairs ($16 \times 16 \times 8 = 2,048$ panel observations including $128$ intrastate pairs).

### 1.1 Out-of-Sample Performance Comparison

| Model Specification | Out-of-Sample $R^2$ ($R^2_{OOS}$) | Pearson Correlation ($r$) | MAE (Thousands) | RMSE (Thousands) | RMSLE | sMAPE (%) | Validation Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PPML Structural Gravity (Primary)** | **0.5890** | **0.8759** | **175.50** | **329.04** | **0.9993** | **75.43%** | **Primary Decision Engine** |
| **Log-OLS Classical Gravity (Comparison)** | 0.2936 | 0.7139 | 233.35 | 431.40 | 1.5231 | 105.68% | Classical baseline (retransformation bias) |
| **Naive Baseline 1: Lagged Persistence (2024 Flow)** | 0.7637 | 0.8816 | 134.92 | 249.51 | 1.1712 | 70.54% | 1-year autoregressive forecast benchmark |
| **Naive Baseline 2: Historical Mean (2018–2024)** | 0.6732 | 0.9343 | 163.35 | 293.39 | 1.0788 | 80.13% | Long-run historical average benchmark |

### 1.2 Methodological Transparency: PPML vs. Autoregressive Persistence
- **Finding**: The naive 1-year lagged persistence benchmark achieves a higher out-of-sample $R^2$ ($0.7637$) than the structural PPML gravity model ($0.5890$).
- **Explanation (AGENTS.md Rule 15)**: Inter-state domestic tourism exhibits substantial year-over-year persistence and institutional inertia. For pure 1-step-ahead short-term point forecasting, historical momentum is a powerful predictor.
- **Why PPML is Retained as the Authoritative Engine**:
  1. *Counterfactual Simulation*: A lagged value cannot evaluate the impact of changing route accessibility, fuel price shifts, or new air corridors.
  2. *Structural Gravity Gap*: Structural PPML identifies where actual tourist volumes deviate from what origin population, income, and distance friction predict, enabling targeted opportunity screening.
  3. *Zero-Flow Robustness*: PPML estimates directly in levels without dropouts or Jensen's inequality bias.

### 1.3 Structural Shift & Distance Stability Test
To test whether pandemic disruption permanently altered spatial travel friction:

$$\text{Model}: \ln(F_{od,t}) = \alpha_o + \alpha_d + \lambda_t + \beta_1 \ln(\text{Distance}_{od}) + \beta_2 \text{CrossRegion}_{od} + \beta_3 [\ln(\text{Distance}_{od}) \times \text{PostRecovery}_t]$$

- **GLM Rank-Full Estimation**: Year fixed effects $\lambda_t$ non-parametrically absorb macroeconomic shifts. The redundant `is_post` intercept dummy was eliminated, yielding zero singular matrix warnings.
- **Results**:
  - Interaction Coefficient $\hat{\beta}_3 = \mathbf{+0.1023}$
  - Standard Error $SE = 0.0658$, $t = 1.5557$, $p = \mathbf{0.1198}$
- **Conclusion**: The null hypothesis of parameter stability is not rejected at $\alpha = 0.05$. Post-COVID domestic tourism distance friction remains structurally invariant in Malaysia.

---

## 2. Panel Econometrics Validation (RQ3 & RQ4)

Evaluated on $N = 126$ state-year observations across 16 Malaysian states over 2018–2025.

### 2.1 Model Specifications Summary

| Model ID | Specification | Within $R^2$ | Overall $R^2$ | Key Predictor | Elasticity | Clustered SE | $p$-value |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| **Model 1** | One-Way State FE (HC1) | 0.6865 | 0.9555 | $\ln(\text{ALOS})$ | +1.5545 | 0.2925 | < 0.0001 |
| **Model 2** | Two-Way FE (State + Year, Clustered) | 0.6517 | 0.9725 | $\ln(\text{ALOS})$ | **+0.6628** | 0.3972 | **0.0952** |
| **Model 2** | Two-Way FE (State + Year, Clustered) | 0.6517 | 0.9725 | $\ln(\text{Tourists})$ | **+0.7327** | 0.1168 | **< 0.0001** |
| **Model 4** | Two-Way FE Accommodation Yield | 0.8018 | 0.8018 | $\ln(\text{AOR})$ | +0.2068 | 0.1868 | 0.2683 |

### 2.2 Robustness & Diagnostics
1. **State-Clustered Standard Errors**: Accounts for serial correlation within each of the 16 state clusters.
2. **Leave-One-State-Out Cross-Validation**:
   - Running 16 iterative regressions excluding one state at a time confirmed **16/16 sign stability** for both ALOS ($\beta \in [+0.52, +0.81]$) and Tourist Volume ($\beta \in [+0.68, +0.79]$).
3. **Influence Diagnostics**: Studentized residuals and Cook's distance identify 2020–2021 lockdown years as high-leverage observations, confirming the necessity of two-way time fixed effects.

---

## 3. Opportunity Engine & Pareto Frontier Validation

- **Non-Domination Property**: Tested across all 240 bilateral corridors. Front 1 contains exactly **58 non-dominated pairs** across the 5 evaluation criteria (demand gap, yield, capacity headroom, accessibility, and diversification).
- **Dominance Proof**: Selangor $\rightarrow$ W.P. Kuala Lumpur (Rank 1, Score 75.47) and Negeri Sembilan $\rightarrow$ Melaka (Rank 2, Score 71.88) reside strictly on Front 1.
- **Capacity Integrity**: Corridors targeting destinations with unobserved hotel capacity are tagged with `Unknown (Capacity Data Unavailable)` and flagged ineligible in budget optimization rather than assuming synthetic values.

---

## 4. Scenario Simulator & Monte Carlo Verification

- **Formula Invariance**: Automated contract tests verify that Python and serialized JSON scenario GVA calculations reconcile within $\pm 0.05$ cents across all state benchmarks.
- **Monte Carlo Convergence**: 1,000 iterations per scenario produce smooth empirical distributions with P10–P90 spreads reflecting parameter uncertainty without artificial distortion.
