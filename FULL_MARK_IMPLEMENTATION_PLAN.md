# MYTourism Value Intelligence

## Full-Mark Implementation Plan for Gemini Antigravity

Repository:

```text
https://github.com/MuhdAdib-2023426514/datathon
```

Purpose:

> Fix the remaining methodological, data-integrity, dashboard-consistency, documentation and commercial-readiness issues identified after execution of the first `IMPLEMENTATION_PLAN.md`.

This plan assumes that the following major upgrades already exist and should **not be reimplemented unnecessarily**:

* two-way state/year fixed effects;
* CPI/real-RM adjustment;
* state-clustered inference;
* leave-one-state-out diagnostics;
* influence diagnostics;
* PPML gravity;
* origin/destination/year effects;
* true 2018–2024 → 2025 holdout;
* proper OOS \(R^2\);
* forecasting baselines;
* structural distance-change testing;
* provenance framework;
* Pareto corridor analysis;
* Monte Carlo module;
* portfolio optimizer;
* temporal OD visualization;
* implementation roadmap.

Antigravity must inspect the actual implementation before editing anything.

---

# 1. Objective

The final system must satisfy five principles:

```text
1. Every number is traceable.
2. Every model claim matches the actual model.
3. Missing empirical data are never silently invented.
4. Simulation assumptions are visibly separated from observations.
5. Dashboard, README and generated outputs tell the same story.
```

The final product positioning is:

> MYTourism Value Intelligence shifts Malaysian tourism planning from maximizing visitor volume toward maximizing sustainable domestic economic value generated per visitor-day, while accounting for market structure, destination capacity and uncertainty.

---

# 2. Primary Analytical Framework

All methodology, dashboard storytelling and documentation should align to:

$$
TourismEconomicValue
=
Visitors
\times
StayDuration
\times
SpendPerVisitorDay
\times
ValueAddedIntensity
$$

Primary state productivity KPI:

$$
\boxed{
TourismValueAddedYield
=
\frac{EstimatedTourismGVA}
{VisitorDays}
}
$$

where:

$$
VisitorDays
=
Tourists\times ALOS
+
Excursionists
$$

Supporting metrics:

```text
Visitor volume
Visitor-days
ALOS
Tourism expenditure yield
Accommodation yield
Tourism GVA intensity
Estimated tourism GVA
Tourism value-added yield
AOR
ADR / RevPAR when available
Origin HHI
Capacity headroom
Structural OD flow gap
Scenario incremental GVA
Scenario uncertainty
```

---

# 3. Execution Rules for Gemini Antigravity

Before making changes, Antigravity must read:

```text
AGENTS.md
IMPLEMENTATION_PLAN.md
IMPLEMENTATION_STATUS.md
README.md
```

Then inspect the current implementation.

Do not assume `IMPLEMENTATION_STATUS.md` proves a feature is correct.

Verify the actual code.

---

## 3.1 Phase-gated execution

Do not execute the entire plan in one pass.

Execute:

```text
Sprint 1
→ tests
→ audit
→ status update

Sprint 2
→ tests
→ audit
→ status update
```

and continue only when the current sprint passes.

---

## 3.2 Do not preserve old conclusions artificially

Never modify data or methodology merely to preserve conclusions such as:

```text
Accommodation must rank #1.
ALOS must be significant.
Selangor → Melaka must remain a priority corridor.
PPML must outperform the baseline.
```

The data must determine the result.

---

## 3.3 Stop conditions

Stop the current sprint and document the issue if:

```text
source data are missing;
reconciliation materially fails;
model estimation fails;
PPML does not converge;
train/test leakage appears;
required variables are missing;
dashboard differs from analytical output;
a recommendation requires fabricated data.
```

Do not hide the problem with a fallback value.

---

# 4. Priority Levels

```text
P0 = required before submission
P1 = strongly recommended for full marks
P2 = advanced polish / competitive advantage
```

Complete all P0 tasks before implementing P2 work.

---

# 5. Sprint 1 — Remove All Remaining Empirical Fallbacks

Priority:

```text
P0 — critical
```

This is the highest-risk remaining data-integrity issue.

Search the repository for hard-coded fallback values.

Commands:

```bash
rg "50\.0|5000\.0|300\.0|1500\.0|120\.0|60\.0|2\.5|0\.8579" src dashboard
rg "\?\?" dashboard/src
rg "\|\|" dashboard/src
```

Inspect every match manually.

Do not blindly replace every numeric constant. Distinguish:

```text
empirical value
scenario assumption
threshold
display constant
mathematical constant
```

---

## 5.1 `state_diagnostics.py`

Inspect fallbacks such as:

```python
dest_baseline_aor_pct = 50.0
dest_available_rooms = 5000.0
distance = 300.0
hhi = 1500.0
spend_per_night = 120.0
```

Remove these if they are substitutes for missing observations.

Use:

```python
np.nan
```

Then propagate missingness.

Example:

```python
if pd.isna(dest_baseline_aor_pct):
    capacity_headroom = np.nan
    capacity_evidence_status = "insufficient_data"
```

---

## 5.2 Monte Carlo

Inspect:

```text
src/scenarios/monte_carlo.py
```

Remove empirical fallbacks such as:

```python
baseline_alos = 2.5
spend_per_night = 60.0
vai = 0.8579
```

unless explicitly passed as scenario assumptions.

If a variable is unavailable:

```text
Monte Carlo status:
UNAVAILABLE — missing baseline data
```

Do not silently construct a distribution around an invented baseline.

---

## 5.3 Portfolio optimizer

Inspect:

```text
src/scenarios/portfolio_optimizer.py
```

Remove fallback values for:

```text
distance
ALOS
yield
capacity
flow
cost
```

If required empirical evidence is missing, the intervention should become:

```text
eligible = false
reason = insufficient evidence
```

---

## 5.4 Acceptance criteria

```text
[ ] No empirical metric uses an arbitrary fallback
[ ] Missing data propagate as NaN/null
[ ] Scenario assumptions remain possible but are labelled
[ ] Opportunity analysis excludes incomplete corridors where necessary
[ ] Tests cover missing data behavior
```

---

# 6. Sprint 2 — Fix Opportunity Engine Semantics

Priority:

```text
P0
```

The opportunity engine currently mixes:

```text
structural residual
Pareto status
weighted score
scenario value
```

These must be separated.

---

## 6.1 Create distinct concepts

### A. Structural Flow Status

Derived only from gravity model:

```text
Below Model Expected
Near Model Expected
Above Model Expected
```

Example:

$$
FlowGapRatio
=
\frac{ActualFlow}{ExpectedFlow}
$$

This is **not yet an opportunity classification**.

---

### B. Opportunity Evidence

Dimensions:

```text
Demand gap
Tourism value-added yield
Capacity headroom
Accessibility
Diversification benefit
Evidence completeness
```

---

### C. Pareto Status

Example:

```text
Pareto Optimal
Pareto Dominated
Insufficient Evidence
```

Pareto status should be the main data-driven opportunity concept.

---

### D. Scenario Impact

Only calculate monetary impact after the user explicitly selects an intervention.

Do not embed:

```text
+0.5 nights for 100% of corridor tourists
```

inside the opportunity-ranking process.

---

# 7. Remove Old +0.5-Night Opportunity Assumption

Priority:

```text
P0
```

Search for:

```text
0.5
additional_nights
corridor_opportunity_gap
```

If the opportunity table calculates:

$$
AdditionalNights
=
Flow\times0.5
$$

remove this from ranking.

Opportunity detection should not depend on an arbitrary intervention.

Instead:

```text
Opportunity engine → identifies candidate corridor
Scenario engine → evaluates intervention
```

Correct separation:

```text
Observation
→ Opportunity
→ Intervention
→ Scenario impact
```

---

# 8. Eliminate Ranking Ambiguity

Priority:

```text
P0/P1
```

Current system may contain:

```text
Pareto rank
composite score
opportunity rank
```

Define one hierarchy.

Recommended:

```text
Primary:
Pareto status

Secondary:
Policy score

Tertiary:
Scenario impact
```

Do not rank by projected accommodation expenditure before the scenario is selected.

---

## 8.1 Policy score

If a weighted score remains, make weights explicit.

Example:

```text
Economic yield       30%
Capacity headroom    25%
Demand gap           20%
Diversification      15%
Accessibility        10%
```

But these should be user-configurable.

Do not imply one weighting system is objectively correct.

Store:

```json
{
  "policy_weights": {
    "yield": 0.30,
    "capacity": 0.25,
    "demand_gap": 0.20,
    "diversification": 0.15,
    "accessibility": 0.10
  },
  "status": "scenario_assumption"
}
```

---

# 9. Sprint 3 — Reframe Gravity Model Correctly

Priority:

```text
P0
```

Current results indicate the PPML structural model does **not** outperform the 2024 persistence baseline for 2025 prediction.

Do not hide this.

---

## 9.1 Define two model purposes

### Structural Gravity Model

Purpose:

> Explain and benchmark structural bilateral tourism flows.

Use:

```text
PPML
origin FE
destination FE
year FE
distance
cross-region
other validated covariates
```

Output:

```text
expected structural flow
structural flow gap
distance friction
```

---

### Forecast Baseline

Purpose:

> Short-term prediction.

Current baseline:

$$
Flow_{2025}=Flow_{2024}
$$

If this remains stronger than PPML, report that clearly.

---

## 9.2 Dashboard model card

Show:

```text
STRUCTURAL MODEL
PPML gravity
OOS R²: 0.xxx

SHORT-TERM BENCHMARK
Previous-year persistence
OOS R²: 0.xxx
```

Interpretation:

> PPML is retained for structural benchmarking, while the persistence model currently performs better for short-term forecasting.

This is a strength, not a weakness.

---

# 10. Sprint 4 — Rewrite README From Current Generated Outputs

Priority:

```text
P0 — extremely important
```

The README must no longer contain legacy findings.

Do not manually reuse old values.

Read:

```text
dashboard/public/data/model_metrics.json
current analytical output files
source registry
quality report
scenario metadata
```

and rewrite README.

---

## 10.1 Remove legacy terminology

Search README for:

```text
DVR
Domestic Value Retention
Root Cause
VFR Trap
VFR leakage
pricing power
proves
causes
yields
generates
0.5158
1.241
HC1
log gravity
```

Remove or update as appropriate.

---

## 10.2 Current panel-model language

Current result should be presented accurately.

Example:

> After controlling for state fixed effects, year effects and inflation, ALOS retains a positive estimated association with real accommodation expenditure. The coefficient is approximately 0.66 and is statistically imprecise at the conventional 5% level.

Do not convert this into:

> Increasing ALOS causes accommodation expenditure to rise by 6.6%.

---

## 10.3 Robustness wording

If leave-one-state-out analysis preserves the coefficient sign, use:

> The estimated sign remains positive under leave-one-state-out sensitivity checks, suggesting the result is not driven by a single state.

Do not say:

```text
proven
structurally confirmed
causal
```

---

## 10.4 Distance-friction finding

Current structural-change test should be presented as:

> Distance remains an important structural friction in domestic tourism flows. The post-recovery distance interaction is not statistically significant at conventional thresholds, so the analysis does not establish that distance sensitivity changed materially after recovery.

Do not claim highway expansion caused the coefficient change.

---

# 11. README Analytical Architecture

Priority:

```text
P0
```

Rewrite the main story as:

```text
National Tourism Value
↓
State Productivity
↓
Exploratory Drivers
↓
Domestic Mobility
↓
Structural Flow Gap
↓
Opportunity Screening
↓
Scenario Testing
↓
Uncertainty
↓
Budget Optimization
↓
Decision Brief
```

Use this as the main architecture diagram.

---

# 12. Fix Observation Counts

Priority:

```text
P0
```

Verify whether gravity observations include:

```text
256 origin-destination pairs × 8 years = 2,048
```

or only interstate:

```text
240 interstate corridors × 8 years = 1,920
```

README, model card and methodology documentation must distinguish:

```text
all OD pairs
interstate corridors
intrastate flows
```

Do not mix them.

---

# 13. Sprint 5 — Fix “Grounded Policy Assistant”

Priority:

```text
P0 — critical dashboard issue
```

Current assistant must not contain stale hard-coded numerical answers.

Inspect:

```text
dashboard/src/components/ImplementationRoadmap.tsx
```

and any other assistant-related files.

---

## 13.1 Remove hard-coded evidence

Delete embedded claims such as:

```text
Melaka AOR = 63.8%
Melaka ALOS = 1.70
```

if these are not dynamically retrieved.

---

## 13.2 Replace with structured evidence lookup

Assistant evidence must come from:

```text
state_metrics.json
model_metrics.json
od_corridors.json
scenario_engine.json
source_metadata.json
```

Example data flow:

```text
User asks question
↓
Resolve state/corridor
↓
Retrieve current structured metrics
↓
Construct evidence object
↓
Generate explanation
```

---

## 13.3 Competition-safe alternative

If no actual LLM retrieval is implemented, rename:

```text
Grounded AI Assistant
```

to:

```text
Evidence Query Assistant
```

and use deterministic response templates.

Example:

```typescript
const response = {
  conclusion: "...",
  evidence: [
    stateMetrics.alos,
    stateMetrics.aor,
    stateMetrics.valueAddedYield
  ],
  limitations: [...]
}
```

This is better than falsely implying dynamic AI grounding.

---

# 14. Remove “Zero-Hallucination” Claims

Priority:

```text
P0
```

Do not say:

```text
zero hallucination
guaranteed grounded
fully accurate
```

unless technically enforceable.

Use:

```text
Evidence-grounded
Structured-data backed
Metric-linked
```

---

# 15. Remove Unsupported Sub-State Claims

Priority:

```text
P0
```

Search assistant and dashboard text for claims like:

```text
weekend shortage in Bandar Hilir
specific district capacity pressure
hotel deficit in X neighbourhood
```

unless sub-state/time-granular evidence exists.

Replace with:

> Annual state-level occupancy may conceal peak-period or location-specific capacity pressure; finer-grained hotel occupancy data would be needed to verify this.

---

# 16. Sprint 6 — Fix Provenance Registry

Priority:

```text
P0
```

Audit:

```text
data/metadata/source_registry.yaml
```

against actual official releases.

Correct:

```text
publication date
reference year
status
source organization
URL
```

---

## 16.1 Add audit fields

For each input dataset include:

```yaml
source_url:
source_file:
reference_period:
publication_date:
download_date:
data_status:
geography:
unit:
license:
checksum:
```

Generate checksum automatically where possible.

Example:

```bash
sha256sum data/raw/...
```

---

## 16.2 Acceptance criteria

```text
[ ] DOSM release dates verified
[ ] URLs valid
[ ] source file names documented
[ ] file checksums generated
[ ] preliminary/estimate status correct
```

---

# 17. Sprint 7 — Monte Carlo Calibration

Priority:

```text
P1
```

Current Monte Carlo architecture is good, but uncertainty should be more evidence-based.

Separate:

```text
empirical uncertainty
policy uncertainty
scenario uncertainty
```

---

## 17.1 Data-derived uncertainty

Where historical data are available, estimate variation for:

```text
ALOS
Spend per tourist-night
Tourism expenditure yield
VAI
AOR
```

Examples:

$$
\sigma_{ALOS,s}
=
SD(ALOS_{s,t})
$$

$$
\sigma_{Yield,s}
=
SD(Yield_{s,t})
$$

Use robust alternatives if sample size is small.

---

## 17.2 Policy assumptions

Keep:

```text
affected share
campaign conversion rate
intervention uptake
```

as explicitly configurable priors.

Example:

```json
{
  "affected_share": {
    "distribution": "triangular",
    "min": 0.05,
    "mode": 0.15,
    "max": 0.25,
    "status": "policy_assumption"
  }
}
```

---

## 17.3 Display uncertainty provenance

Dashboard should distinguish:

```text
Historically calibrated uncertainty
Scenario assumption uncertainty
```

---

# 18. Sprint 8 — Fix Portfolio Optimizer Costs

Priority:

```text
P0/P1
```

This is the largest remaining commercial-credibility problem.

Do not derive intervention cost from arbitrary formulas such as:

$$
RM50,000 + RM25\times flow
$$

unless clearly labelled illustrative.

---

## 18.1 Preferred architecture

Allow user-supplied intervention cost.

Input table:

| Corridor          | Intervention            |   Cost |
| ----------------- | ----------------------- | -----: |
| Selangor → Melaka | Stay-extension campaign | RM ___ |
| Johor → Melaka    | Overnight conversion    | RM ___ |

Then solve:

$$
\max\sum_i ExpectedIncrementalGVA_i x_i
$$

subject to:

$$
\sum_i Cost_i x_i\le Budget
$$

---

## 18.2 If no real cost exists

Label clearly:

```text
ILLUSTRATIVE COST ASSUMPTION
```

Do not call:

```text
ROI
return on investment
commercial return
```

unless intervention cost is sourced or user-provided.

Use:

```text
Expected GVA under assumed intervention costs
```

---

# 19. Connect Monte Carlo to Optimization

Priority:

```text
P2
```

This is one of the best possible remaining “wow-factor” upgrades.

Allow optimization targets:

```text
Expected GVA
Median GVA
Conservative P10 GVA
Risk-adjusted GVA
```

Example:

$$
Objective =
E[GVA] - \lambda\sigma_{GVA}
$$

or:

$$
Objective=P10(GVA)
$$

where:

```text
λ = user-selected risk aversion
```

Dashboard:

```text
Optimization Mode

○ Expected Value
○ Conservative
○ Risk Adjusted
```

This strongly integrates:

```text
Monte Carlo
+
MILP
```

rather than showing them as separate features.

---

# 20. Sprint 9 — Fix Scenario Architecture Claim

Priority:

```text
P1
```

Current system may still calculate formulas in both Python and React.

Determine actual architecture.

If React still independently calculates scenario formulas, do not describe the system as:

```text
single source of truth
single calculation engine
```

unless you actually replace frontend formulas.

---

## Option A — True single source of truth

Preferred architecture:

```text
React
↓ parameters
Python API
↓ results
React
```

---

## Option B — Static deployment compatibility

If Netlify must remain static:

```text
Python reference implementation
+
TypeScript mirror
+
automated parity tests
```

Document honestly as:

> Dual-runtime scenario implementation with automated contract-parity validation.

Add tests using identical fixtures.

---

# 21. Scenario Parity Tests

Priority:

```text
P0/P1
```

Create fixtures:

```json
{
  "destination": "Melaka",
  "tourists": ...,
  "alos_uplift": 0.5,
  "affected_share": 0.15,
  "guests_per_room": 1.8
}
```

Calculate result in Python.

Calculate same result in TypeScript.

Assert equality within tolerance for:

```text
additional visitor nights
additional room nights
additional expenditure
incremental GVA
projected AOR
capacity status
```

---

# 22. Sprint 10 — Fix Validation Philosophy

Priority:

```text
P0
```

Move predetermined results into snapshot tests.

Current examples:

```python
assert top_product == "Accommodation services"
```

and required named priority corridors.

These should not be scientific-validation tests.

---

## Test structure

```text
tests/
├── scientific/
│   ├── accounting/
│   ├── data_quality/
│   ├── econometrics/
│   ├── gravity/
│   ├── scenarios/
│   └── optimization/
│
└── snapshot/
    ├── current_tsa_ranking/
    └── current_corridor_outputs/
```

---

## Scientific tests should check

```text
VAI formula
TVAY formula
valid ranges
missing values
no leakage
train/test split
PPML output schema
scenario arithmetic
optimizer constraints
```

---

## Snapshot tests may check

```text
Current dataset ranks accommodation first by VAI
Current dataset includes a specific corridor in a specific output
```

Label them:

```text
snapshot regression checks
```

Never:

```text
hypothesis confirmed
```

---

# 23. Sprint 11 — Terminology Audit

Priority:

```text
P0
```

Run:

```bash
rg -i "prove|proves|proven|cause|causes|causal|root cause|trap|leakage|pricing power|official brief|zero hallucination"
```

Review every occurrence.

---

## Preferred replacements

| Avoid              | Replace                               |
| ------------------ | ------------------------------------- |
| root cause         | exploratory driver                    |
| causes             | is associated with                    |
| proves             | provides evidence                     |
| VFR trap           | low commercial lodging capture        |
| VFR leakage        | VFR commercial conversion opportunity |
| pricing power      | occupancy intensity                   |
| official brief     | prototype decision-support brief      |
| zero hallucination | evidence-grounded                     |
| guaranteed impact  | scenario-estimated impact             |

---

# 24. Sprint 12 — Update Dashboard Model Interpretation

Priority:

```text
P1
```

Add a methodology card explaining:

## State panel

```text
Purpose:
Estimate within-state longitudinal associations.

Controls:
State fixed effects
Year fixed effects

Inference:
State-clustered SE

Interpretation:
Associational, not causal.
```

---

## Gravity

```text
Purpose:
Structural OD benchmarking.

Model:
PPML with origin/destination/year FE.

Prediction:
Compared against persistence baseline.

Interpretation:
Useful for structural flow gaps,
not necessarily best short-term forecast.
```

This is an excellent credibility feature.

---

# 25. Sprint 13 — Update SDG Story

Priority:

```text
P1
```

Do not only show logos.

Explicitly connect features.

## SDG 8.9

Project contribution:

```text
measuring tourism economic productivity
supporting higher-value tourism strategy
identifying value-generation opportunities
```

---

## SDG 12.b

Project contribution:

```text
tourism-impact monitoring
destination-capacity monitoring
scenario testing
decision-support indicators
```

Avoid claiming that the project directly measures every aspect of sustainability.

State:

> The current project focuses specifically on the economic dimension of sustainable tourism.

---

# 26. Sprint 14 — Commercial Implementation Model

Priority:

```text
P1
```

Strengthen the existing implementation roadmap with one concrete operating example.

Example:

## Pilot deployment — Melaka

### Baseline quarter

```text
Measure:
ALOS
TVAY
AOR
top feeder shares
OD flows
```

### Intervention design

```text
Target:
selected feeder corridor

Intervention:
stay-extension package
```

### Pilot

```text
8–12 weeks
```

### Outcome tracking

```text
ALOS
commercial room nights
spend per visitor-day
TVAY
```

### Evaluation

Use:

```text
before/after
matched corridor if possible
difference-in-differences in future version
```

---

# 27. Add Commercial Roles

Priority:

```text
P1
```

For every action identify:

```text
decision owner
data owner
implementation owner
review frequency
```

Example:

| Function                 | Owner                        |
| ------------------------ | ---------------------------- |
| TSA data refresh         | DOSM/public-data pipeline    |
| State campaign selection | State Tourism Board          |
| National portfolio       | MOTAC                        |
| Hotel capacity review    | Industry / tourism authority |
| Dashboard maintenance    | Analytics team               |

---

# 28. Sprint 15 — Headline KPI Hierarchy

Priority:

```text
P1
```

Avoid showing too many equally important KPIs.

Primary KPI:

$$
\boxed{TourismValueAddedYield}
$$

Secondary drivers:

```text
Visitor volume
ALOS
Spend per visitor-day
GVA intensity
```

Constraints:

```text
AOR
capacity headroom
origin concentration
distance/accessibility
```

Opportunity:

```text
structural flow gap
Pareto status
```

Outcome:

```text
scenario incremental GVA
risk range
```

This creates a much clearer decision hierarchy.

---

# 29. Sprint 16 — Final Dashboard Story

Priority:

```text
P1
```

Recommended navigation:

```text
1. National Value
2. State Productivity
3. Drivers
4. Mobility
5. Opportunities
6. Simulate
7. Optimize
8. Action Brief
9. Methodology
10. Implementation
```

---

## Page 1 — National Value

Question:

> Where does Malaysian tourism create domestic economic value?

---

## Page 2 — State Productivity

Question:

> Which states generate the most value from each visitor-day?

---

## Page 3 — Drivers

Question:

> Which factors are associated with stronger state tourism productivity?

---

## Page 4 — Mobility

Question:

> Where do domestic tourists travel from and to?

---

## Page 5 — Opportunities

Question:

> Which corridors combine structural demand gap, high yield and available capacity?

---

## Page 6 — Simulate

Question:

> What could happen under a specific intervention?

---

## Page 7 — Optimize

Question:

> How should a limited tourism budget be allocated?

---

## Page 8 — Action Brief

Question:

> What should the decision maker implement?

---

# 30. Sprint 17 — Evidence Drawer

Priority:

```text
P1
```

Every recommendation should support:

```text
Why is this recommended?
```

Drawer should display:

```text
Observation
Supporting metrics
Model evidence
Source
Status
Confidence
Limitations
```

Example:

```text
Recommendation
Evaluate stay-extension intervention.

Evidence
ALOS below peer median.
Tourism value-added yield above peer median.
Capacity headroom available.
Origin market concentration moderate.

Confidence
Medium

Limitation
Scenario outcome depends on campaign reach.
```

---

# 31. Sprint 18 — Current-Results Summary File

Priority:

```text
P1
```

Generate:

```text
artifacts/current_results.json
```

This should contain every headline result used in:

```text
README
dashboard
presentation
policy brief
```

Example:

```json
{
  "panel": {
    "alos_elasticity": 0.6628,
    "alos_p_value": 0.0952
  },
  "gravity": {
    "ppml_oos_r2": 0.589,
    "lag_baseline_oos_r2": 0.764
  }
}
```

This becomes the headline-results contract.

---

# 32. README / Dashboard Consistency Test

Priority:

```text
P0/P1
```

Where feasible, generate README result tables automatically.

At minimum test:

```text
README coefficient == current_results coefficient
dashboard coefficient == current_results coefficient
model_metrics coefficient == current_results coefficient
```

No stale analytical value should survive unnoticed.

---

# 33. Final Rubric-Oriented Audit

Before submission, Antigravity must produce:

```text
artifacts/final_rubric_audit.md
```

with this structure.

---

## Methodology

Check:

```text
[ ] Problem statement clear
[ ] Economic scope explicit
[ ] North-star KPI defined
[ ] Two-way FE documented
[ ] PPML documented
[ ] Structural vs forecasting distinction documented
[ ] Causal claims removed
[ ] SDG linkage explicit
[ ] Statistical limitations visible
```

---

## Data & Analysis Quality

```text
[ ] Official sources verified
[ ] Source dates correct
[ ] Checksums present
[ ] Missing values preserved
[ ] No hidden empirical fallbacks
[ ] CPI adjustment documented
[ ] Mapping coverage reported
[ ] Reconciliation passes
[ ] Snapshot tests separated
```

---

## Dashboard

```text
[ ] All headline numbers dynamic
[ ] Assistant uses current data
[ ] No unsupported sub-state claims
[ ] Scenario parity passes
[ ] Provenance accessible
[ ] Status badges visible
[ ] Responsive layout verified
[ ] No console errors
```

---

## Commercial Impact

```text
[ ] Decision users documented
[ ] Operating model documented
[ ] Cost assumptions transparent
[ ] Optimizer does not imply fake ROI
[ ] Pilot implementation example included
[ ] Refresh cadence documented
[ ] Expansion roadmap included
```

---

## Creativity

```text
[ ] PPML
[ ] Geospatial OD
[ ] Pareto opportunity
[ ] Monte Carlo
[ ] Risk-aware optimization
[ ] Temporal network animation
[ ] Evidence-grounded assistant
[ ] Automated policy brief
```

---

# 34. Target Score After Completion

The goal is not to manipulate a numerical score.

The goal is to remove every obvious reason a judge could deduct marks.

Expected quality target:

| Rubric                   |     Target |
| ------------------------ | ---------: |
| Methodology              | 19–20 / 20 |
| Data & Analysis Quality  | 19–20 / 20 |
| Dashboard / Final Output | 19–20 / 20 |
| Commercial Impact        | 19–20 / 20 |
| Creativity               | 19–20 / 20 |

A literal 100/100 cannot be guaranteed because judging remains subjective.

The implementation objective is:

> **No preventable methodological, data-quality, UX or credibility weakness should remain.**

---

# 35. Execution Order

Gemini Antigravity should execute in this exact order.

## Sprint A — Credibility blockers

```text
[ ] Remove hidden empirical fallbacks
[ ] Fix opportunity architecture
[ ] Remove +0.5-night ranking assumption
[ ] Fix provenance metadata
[ ] Fix assistant hard-coded evidence
[ ] Remove unsupported terminology
```

## Sprint B — Documentation truthfulness

```text
[ ] Rewrite README
[ ] Update methodology docs
[ ] Correct observation counts
[ ] Separate structural model from forecasting
[ ] Update gravity interpretation
[ ] Update ALOS interpretation
```

## Sprint C — Commercial credibility

```text
[ ] Replace optimizer fake costs
[ ] Add editable intervention costs
[ ] Remove unsupported ROI wording
[ ] Add pilot operating model
```

## Sprint D — Uncertainty and optimization integration

```text
[ ] Calibrate Monte Carlo from historical variation
[ ] Separate data uncertainty from policy uncertainty
[ ] Add risk-adjusted optimization
```

## Sprint E — Dashboard integrity

```text
[ ] Dynamic assistant evidence
[ ] Scenario parity tests
[ ] Evidence drawer
[ ] Data status display
[ ] Headline KPI hierarchy
```

## Sprint F — Final audit

```text
[ ] Snapshot/scientific test split
[ ] Current-results contract
[ ] README/dashboard consistency check
[ ] Full dashboard build
[ ] Full Python test suite
[ ] Final rubric audit
```

---

# 36. Mandatory Sprint Completion Report

After each sprint update:

```text
IMPLEMENTATION_STATUS.md
```

with:

```markdown
## Sprint X Completion

### Files changed
- ...

### Problems fixed
- ...

### Analytical changes
- ...

### Tests
- X passed
- X failed

### Dashboard build
PASS / FAIL

### Data reconciliation
PASS / FAIL

### Results changed
| Metric | Before | After | Reason |
|---|---:|---:|---|

### Remaining issues
- ...

### Acceptance criteria
- [x] ...
- [ ] ...

### Ready for next sprint
YES / NO
```

Do not continue when:

```text
Ready for next sprint = NO
```

---

# 37. Antigravity Initial Prompt

Start Gemini Antigravity with:

```text
Read AGENTS.md, IMPLEMENTATION_PLAN.md, IMPLEMENTATION_STATUS.md,
README.md and the current source tree completely before making changes.

This repository has already completed a large implementation plan.
Do NOT reimplement features that already exist.

Your task is to execute the Full-Mark Implementation Plan phase by phase.

Begin with Sprint A only.

Before modifying anything:

1. Audit all remaining empirical fallback values.
2. Identify where opportunity detection still mixes scenario assumptions.
3. Identify stale or hard-coded assistant evidence.
4. Verify source-registry metadata against current repository evidence.
5. Search for unsupported terminology and stale methodological claims.
6. List all files that require modification.
7. List the tests that must be added or updated.

Then execute Sprint A.

Important:
- Never fabricate empirical values.
- Do not change data or models to preserve a preferred conclusion.
- Missing empirical values must remain null/NaN.
- Model outputs must be treated as data, not manually retyped.
- Do not start Sprint B until Sprint A acceptance criteria pass.
- Update IMPLEMENTATION_STATUS.md when finished.
```

---

# 38. Final Project Narrative

Once implementation is complete, the project should communicate:

> Malaysia's tourism performance should not be assessed only by how many visitors arrive. MYTourism Value Intelligence measures how effectively destinations convert visitor-days into domestic economic value. It combines official tourism accounts, state surveys, hotel capacity and origin-destination mobility to identify structural constraints, screen high-value opportunities, test interventions under capacity limits, quantify uncertainty and support transparent allocation of tourism-development resources.

The final decision chain should be:

$$
\boxed{
Measure
\rightarrow
Diagnose
\rightarrow
Benchmark
\rightarrow
Identify
\rightarrow
Simulate
\rightarrow
QuantifyRisk
\rightarrow
Optimize
\rightarrow
Act
}
$$

---

# 39. Final Definition of Done

The project is competition-ready only when the following judge questions can be answered immediately.

### “Where did this number come from?”

The system shows:

```text
source
formula
status
reference period
```

### “Why does this state perform differently?”

The system shows:

```text
state productivity
driver evidence
uncertainty
limitations
```

### “Why is this corridor an opportunity?”

The system shows:

```text
structural gap
economic yield
capacity
accessibility
diversification
Pareto status
```

### “What happens if your assumption is wrong?”

The system shows:

```text
P10
P50
P90
capacity risk
```

### “Why should government trust this?”

The system shows:

```text
official sources
provenance
data-quality tests
model validation
limitations
```

### “How would this be implemented?”

The system shows:

```text
decision owner
pilot process
budget input
monitoring cycle
refresh schedule
```

If all six questions can be answered without relying on invented numbers, stale documentation or unsupported claims, the project is ready for final submission.
