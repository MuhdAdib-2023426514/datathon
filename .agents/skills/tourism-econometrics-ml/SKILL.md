---
name: tourism-econometrics-ml
description: >-
  Econometric panel modeling (fixed effects), gravity models of inter-state tourism corridors,
  unsupervised state clustering, and explainable ML for sustainable tourism economics.
---

# Tourism Econometrics & Machine Learning Guidelines

This skill governs the statistical, econometric, and machine learning methods applied to the **Malaysia Tourism Value Optimizer**, strictly adhering to the methodology, transparency, and reporting standards in `AGENTS.md`.

---

## 1. Core Principles & Guardrails

1. **Proportional Complexity**: Use statistical models calibrated to the sample size (16 states/FTs, 8 years of panel data = 126 state-year observations, 240 active inter-state corridors).
2. **Transparent & Deterministic**: Prioritize interpretable econometric models (OLS, Fixed Effects, Log-Log elasticities, Gravity formulations) over black-box deep learning.
3. **Causal Humility**:
   * **NEVER** claim regression coefficients prove causality or guarantee RM impact.
   * Use terms: *"associated with"*, *"estimated elasticity"*, *"under the scenario assumption"*.
   * Any scenario output must carry the mandatory disclaimer: *"Scenario estimate, not a causal forecast."*

---

## 2. State Panel Econometrics (2018–2025)

With 8 annual panels across 16 states ($N=16, T=8$), estimate within-state behavioral elasticities while controlling for unobserved time-invariant state characteristics (geography, natural endowments, baseline heritage).

### A. State Fixed-Effects Model (Within-Estimator)
$$\ln(\text{AccomSpend}_{s,t}) = \alpha_s + \lambda_t + \beta_1 \ln(\text{ALOS}_{s,t}) + \beta_2 \ln(\text{Tourists}_{s,t}) + \beta_3 \text{ExcursionistShare}_{s,t} + \varepsilon_{s,t}$$

Where:
* $\alpha_s$: State-specific fixed effect (absorbs baseline tourism attractiveness, highway proximity).
* $\lambda_t$: Year fixed effect (absorbs macro COVID disruptions, national economic cycles).
* $\beta_1$: **Within-state elasticity of ALOS** on accommodation spend:
  $$\% \Delta \text{AccomSpend} \approx \beta_1 \times (\% \Delta \text{ALOS})$$
* Standard errors must be robust or clustered by state (Huber-White / HC1).

### B. Post-Pandemic Volume vs. Value Recovery Index (2019 vs. 2025)
To identify whether a state's recovery is **Volume-Driven (congestion risk)** or **Value-Driven (economic yield upgrade)**:

1. **Volume Recovery Index**:
   $$\text{VRI}_s = \frac{\text{Visitors}_{s, 2025}}{\text{Visitors}_{s, 2019}} \times 100$$
2. **Real Value Recovery Index**:
   $$\text{YRI}_s = \frac{\text{SpendPerVisitor}_{s, 2025}}{\text{SpendPerVisitor}_{s, 2019}} \times 100$$
3. **Stay-Lag Delta**:
   $$\Delta \text{ALOS}_s = \text{ALOS}_{s, 2025} - \text{ALOS}_{s, 2019}$$

---

## 3. Spatial Gravity Model of Domestic Tourism Corridors

For the $16 \times 16$ origin-destination network (240 inter-state corridors), estimate spatial interaction potential:

$$\ln(F_{o,d}) = \beta_0 + \beta_1 \ln(\text{Pop}_o) + \beta_2 \ln(\text{GVA}_o) + \beta_3 \ln(\text{Attractions}_d) - \beta_4 \ln(\text{Distance}_{o,d}) + \varepsilon_{o,d}$$

### A. Gravity Residuals & Corridor Optimization
* **Expected Flow ($\hat{F}_{o,d}$)**: Flow predicted by origin market mass and highway/geographic distance.
* **Corridor Performance Gap**:
  $$\text{Residual}_{o,d} = \ln(F_{o,d}) - \ln(\hat{F}_{o,d})$$
  * **Positive Residual ($\text{Residual} > 0$)**: Over-performing corridor (high affinity, strong network links).
  * **Negative Residual ($\text{Residual} < 0$)**: Under-performing corridor with high unrealized gravity potential (growth opportunity for targeted transport and packaging).

---

## 4. Unsupervised Clustering for State Typologies

Group Malaysian states into 4 strategic economic archetypes using standardized features ($z$-scores):
* **Features**:
  1. Average Length of Stay ($\text{ALOS}$)
  2. Accommodation Spend Per Night ($\text{SpendPerNight}$)
  3. Excursionist Ratio ($\text{Excursionists} / \text{Visitors}$)
  4. Commercial Accommodation Share ($\text{AccomSpend} / \text{TotalSpend}$)

### Resulting Strategic Archetypes:
1. **Volume Trap**: High visitor volume, short ALOS, low spend/night (Perak, Negeri Sembilan).
2. **Transit Spender**: High spend/night, but very short ALOS and high day-trip leakage (Melaka, Pahang).
3. **High-Yield Paradigm**: Long ALOS, high spend/night, high value retention (Penang, Sabah, Sarawak).
4. **Budget / VFR Retreat**: Long ALOS (family visits), low commercial spend/night (Kelantan, Terengganu, Perlis).

---

## 5. Machine Learning Feature Attribution (SHAP / ElasticNet)

When applying regularized regression or gradient boosting on corridor/state features:
1. Use **ElasticNet** or **Random Forest / LightGBM** with cross-validation strictly if features exceed standard degrees of freedom.
2. Present **SHAP (SHapley Additive exPlanations)** values strictly as **model-prediction feature contributions**, NEVER as causal proofs.
3. Keep hyperparameter spaces bounded to prevent overfitting on 16 cross-sectional units.
