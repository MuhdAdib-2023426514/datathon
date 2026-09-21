# Full-Mark Implementation Plan

> **Current remediation plan (2026-09-21):** See [Rubric remediation implementation plan](docs/rubric_remediation_plan.md) for the code-review fixes, dependency order, acceptance gates, and evidence requirements covering all 25 rubric criteria. These issues remain open regardless of historical completion claims below. The original plan is retained as architectural context.

> **Execution scope:** Implement R01–R12 **and** the mandatory [C00–C17 checklist addendum](docs/rubric_remediation_plan.md#7-mandatory-checklist-addendum-workspace-analytical-claims-and-publication). Track each acceptance gate separately. The addendum covers GitHub reconciliation, README/results consistency, diagnostic and optimizer fallbacks, scenario-independent ranking, Pareto eligibility, assistant claims, provenance, uncertainty/risk modes, test separation, audit claims, and optional wild-cluster bootstrap. Local completion and verified delivery to GitHub `main` are separate milestones.

## Malaysian Sustainable Tourism Economic Intelligence

Repository:

```text
https://github.com/MuhdAdib-2023426514/datathon
```

Primary objective:

> Upgrade the current project into a statistically defensible, transparent, reproducible and commercially actionable tourism economic decision-support system capable of satisfying all competition rubric dimensions at the highest level.

---

# 1. Codex Execution Rules

Codex must follow these rules throughout implementation.

## 1.1 Do not blindly implement this document

Before modifying any file:

1. inspect the current implementation;
2. identify whether the requested improvement already exists;
3. compare actual behavior with this specification;
4. modify only what is necessary;
5. preserve working functionality;
6. add/update tests;
7. run relevant tests;
8. record the result.

Do not overwrite a newer or better implementation merely because this plan describes another approach.

---

## 1.2 Methodological integrity has priority over visual features

Implementation priority:

```text
DATA INTEGRITY
    ↓
ACCOUNTING CORRECTNESS
    ↓
STATISTICAL VALIDITY
    ↓
MODEL VALIDATION
    ↓
SCENARIO CONSISTENCY
    ↓
DASHBOARD INTEGRATION
    ↓
COMMERCIAL FEATURES
    ↓
WOW FEATURES
```

Do not implement AI assistants, optimization or visual animations before P0 methodological issues pass validation.

---

## 1.3 Never fabricate empirical observations

Forbidden pattern:

```python
value = real_value if available else 50
```

for empirical variables.

Missing observations must become:

```python
np.nan
```

or:

```typescript
null
```

Dashboard rendering:

```text
N/A
Data unavailable
Insufficient data
```

Scenario assumptions are allowed only when clearly identified as assumptions.

---

## 1.4 One analytical source of truth

Architecture must be:

```text
Official Data
    ↓
Python Ingestion
    ↓
Validation
    ↓
Feature Engineering
    ↓
Analytics / Models
    ↓
Scenario Engine
    ↓
Generated JSON
    ↓
React Dashboard
```

React must not independently reproduce major economic, econometric or scenario calculations.

---

## 1.5 Do not hard-code analytical findings

Forbidden:

```tsx
<R2>0.5900</R2>
<Coefficient>-0.603</Coefficient>
<HHI>0.318</HHI>
```

Required:

```text
Python
→ generated JSON
→ frontend
```

Every important number shown in the dashboard must be traceable to an analytical output.

---

## 1.6 Avoid unsupported causal language

Use:

```text
associated with
related to
estimated relationship
model-estimated
consistent with
scenario result
exploratory evidence
```

Avoid:

```text
causes
proves
generates
drives
guarantees
root cause
```

unless causal identification exists.

---

# 2. Competition North-Star

The entire system should revolve around:

$$
\boxed{
TourismEconomicValue
=
Visitors
\times
StayDuration
\times
SpendPerVisitorDay
\times
ValueAddedIntensity
}
$$

The project should not optimize visitor count alone.

Primary strategic question:

> How can Malaysian destinations generate greater sustainable domestic economic value from each visitor-day while respecting destination capacity, accessibility, market risk and uncertainty?

---

# 3. North-Star KPI

Implement:

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

and:

$$
EstimatedTourismGVA
=
\sum_k
Expenditure_k\times VAI_k
$$

This should become the key state economic-productivity KPI.

Do not replace TEY.

Use both:

```text
Tourism Expenditure Yield
Tourism Value-Added Yield
```

They answer different questions.

---

# 4. Priority System

Use:

```text
P0 = required before competition submission
P1 = strongly recommended for high score
P2 = advanced competition feature
P3 = optional wow factor
```

Codex must complete all P0 tasks before implementing P2/P3 features.

---

# 5. Phase 0 — Create Baseline

Priority:

```text
P0
```

## Goal

Preserve the current project's results before changing analytical methodology.

## Tasks

Create:

```text
artifacts/baseline/
```

Run the entire current analytical workflow.

Save:

```text
tsa_product_ranking.csv
state_metrics.csv
panel_coefficients.csv
gravity_coefficients.csv
gravity_predictions.csv
corridor_classifications.csv
scenario_examples.json
model_metrics.json
```

Create:

```text
docs/baseline.md
```

Record:

```text
commit hash
date
Python version
Node version
data versions
tests passing
key model metrics
known methodological issues
```

## Acceptance criteria

```text
[ ] Existing tests executed
[ ] Existing dashboard builds
[ ] Baseline outputs saved
[ ] Current major analytical results documented
```

---

# 6. Phase 1 — Reproducibility Cleanup

Priority:

```text
P0
```

## 6.1 Remove absolute paths

Search repository:

```bash
rg "/home/"
rg "C:\\"
rg "muhammad_adib"
```

Fix files such as:

```text
src/analytics/product_value.py
```

Use common project paths.

Create if necessary:

```python
# src/config/paths.py

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
DASHBOARD_DATA_DIR = PROJECT_ROOT / "dashboard" / "public" / "data"
```

All modules should import from this configuration.

---

## 6.2 Fix `pyproject.toml`

Replace placeholder:

```toml
description = "Add your description here"
```

with a proper project description.

Review:

```toml
requires-python = ">=3.14"
```

Prefer:

```toml
requires-python = ">=3.11,<3.13"
```

unless Python 3.14 is genuinely required.

---

## 6.3 Create one pipeline command

Implement:

```text
src/pipeline.py
```

Target command:

```bash
uv run python -m src.pipeline
```

Pipeline order:

```text
1. ingest
2. validate raw inputs
3. transform
4. reconcile
5. calculate economic metrics
6. TSA analysis
7. state analysis
8. panel models
9. gravity model
10. corridor opportunities
11. scenario outputs
12. dashboard exports
13. QA report
```

## Acceptance criteria

A new machine can clone the project and reproduce analytical outputs without changing source-code paths.

---

# 7. Phase 2 — Fix Missing-Value Handling

Priority:

```text
P0 — critical
```

This is one of the highest-risk competition issues.

## 7.1 Parser defaults

Inspect:

```text
src/ingestion/granular_dts_parser.py
```

and all ingestion modules.

Replace:

```python
hotel_share = 0.0
vfr_share = 0.0
air_share = 0.0
b40_share = 0.0
```

with:

```python
hotel_share = np.nan
vfr_share = np.nan
air_share = np.nan
b40_share = np.nan
```

Zero must mean actual observed zero.

Missing must mean missing.

---

## 7.2 Accounting functions

Inspect:

```text
src/analytics/accounting.py
```

Replace behavior such as:

```python
if value is None or np.isnan(value):
    return 0.0
```

with appropriate missing-value propagation.

Example:

```python
if value is None or pd.isna(value):
    return np.nan
```

unless the mathematical operation explicitly defines missing as zero.

---

## 7.3 Frontend fallback removal

Search:

```bash
rg "\?\?" dashboard/src
rg "\|\|" dashboard/src
```

Inspect every fallback.

Remove empirical defaults such as:

```typescript
residentHouseholds || 250
unpaid_vfr_pct ?? 50
```

Replace with nullable handling.

---

## 7.4 Validation

Create tests ensuring a missing source cell produces:

```text
NaN / null
```

rather than:

```text
0
50
100
etc.
```

## Acceptance criteria

```text
[ ] No empirical missing observation becomes an arbitrary number
[ ] Zero remains distinct from missing
[ ] Dashboard supports N/A states
[ ] Tests verify missing-value propagation
```

---

# 8. Phase 3 — Data Provenance Registry

Priority:

```text
P0/P1
```

Create:

```text
data/metadata/source_registry.yaml
```

Example:

```yaml
tsa_2025:
  organization: Department of Statistics Malaysia
  publication: Tourism Satellite Account 2025
  reference_year: 2025
  publication_date: 2026-09-15
  data_status: preliminary
  geography: Malaysia
  url: ...
```

Each analytical dataset should be linked to:

```text
source
reference period
release
status
unit
geography
transformation
```

Allowed statuses:

```text
official
preliminary
estimate
derived
model_estimate
scenario_assumption
```

Generate:

```text
dashboard/public/data/source_metadata.json
```

---

# 9. Phase 4 — Data Quality Report

Priority:

```text
P0
```

Create:

```text
src/validation/data_quality_report.py
```

Output:

```text
artifacts/data_quality_report.json
artifacts/data_quality_report.md
```

Report:

```text
row counts
duplicate keys
missing values
out-of-range values
category totals
state/national reconciliation
unmatched parser labels
mapping coverage
data status
```

## Required reconciliation

Where data supports it:

```text
Σ state visitors ≈ national visitors
Σ state expenditure ≈ national expenditure
Tourists + Excursionists ≈ Visitors
Accommodation shares ≈ 100%
Purpose shares ≈ 100%
Origin shares ≈ 100%
```

Document tolerances.

---

# 10. Phase 5 — Inflation Adjustment

Priority:

```text
P0/P1
```

## Goal

Avoid interpreting inflation as real tourism growth.

Add official Malaysia CPI or appropriate tourism-related price index.

Create:

```text
data/processed/price_index.csv
```

Fields:

```text
year
index
base_year
source
```

Calculate:

```text
real_total_expenditure
real_accommodation_expenditure
real_spend_per_tourist
real_spend_per_visitor_day
real_estimated_tourism_gva
```

Formula:

$$
RealValue_t
=
NominalValue_t
\times
\frac{Index_{2025}}{Index_t}
$$

Preserve nominal values.

Dashboard labels:

```text
Nominal RM
Constant 2025 RM
```

Default analytical longitudinal comparisons should use real RM where appropriate.

---

# 11. Phase 6 — Replace Domestic Value Retention

Priority:

```text
P0
```

Current terminology:

```text
Domestic Value Retention
DVR
```

must be removed unless regional leakage is genuinely measured.

Replace with:

```text
Tourism GVA Intensity
```

Definition:

$$
TourismGVAIntensity_s
=
\frac{
\sum_k Expenditure_{sk}VAI_k
}{
\sum_k MappedExpenditure_{sk}
}
$$

Also calculate:

$$
EstimatedTourismGVA_s
=
\sum_k Expenditure_{sk}VAI_k
$$

---

## 11.1 Remove arbitrary VAI fallback

Remove:

```python
"other": 0.50
```

as a default for unmapped categories.

Do not assume VAI for unknown expenditure.

Instead:

```text
Mapped expenditure
Unmapped expenditure
Mapping coverage
```

Calculate:

$$
MappingCoverage_s
=
\frac{MappedExpenditure_s}
{TotalExpenditure_s}
$$

Dashboard example:

```text
Estimated tourism GVA: RM X
Mapping coverage: 91.2%
```

If coverage is low, display warning.

---

# 12. Phase 7 — Implement Tourism Value-Added Yield

Priority:

```text
P0
```

Add to shared accounting module.

## Visitor days

$$
VisitorDays =
Tourists\times ALOS + Excursionists
$$

## Tourism Expenditure Yield

$$
TEY =
\frac{TotalTourismExpenditure}
{VisitorDays}
$$

## Accommodation Yield

$$
AccommodationYield
=
\frac{AccommodationExpenditure}
{Tourists\times ALOS}
$$

## Tourism Value-Added Yield

$$
TVAY
=
\frac{EstimatedTourismGVA}
{VisitorDays}
$$

Add real-price versions where longitudinal comparisons occur.

Generate state-level fields:

```text
visitor_days
expenditure_yield
accommodation_yield
tourism_gva_intensity
estimated_tourism_gva
tourism_value_added_yield
gva_mapping_coverage
```

---

# 13. Phase 8 — Rebuild State Typology

Priority:

```text
P1
```

Remove any typology using:

```text
ALOS + spend_per_tourist
```

while describing the second dimension as spend/day.

Preferred dimensions:

```text
ALOS
Tourism Value-Added Yield
```

Fallback:

```text
ALOS
Tourism Expenditure Yield
```

Quadrants:

```text
Short Stay / Low Yield
Short Stay / High Yield
Long Stay / Low Yield
Long Stay / High Yield
```

Optional user-friendly labels may be displayed as secondary text only.

Do not hide the underlying metric definitions.

---

# 14. Phase 9 — Rebuild State Panel Econometrics

Priority:

```text
P0 — critical
```

Inspect:

```text
src/analytics/panel_econometrics.py
```

## 14.1 Two-way fixed effects

Existing state-only FE models must gain year FE.

Example:

```python
formula = """
ln_real_accom_spend
~ ln_alos
+ ln_tourists
+ ln_aor
+ foreign_share
+ C(state)
+ C(year)
"""
```

---

## 14.2 Cluster uncertainty by state

Replace HC1-only inference where appropriate with:

```python
.fit(
    cov_type="cluster",
    cov_kwds={"groups": data["state"]}
)
```

Document small-cluster limitations.

---

## 14.3 Add yield-focused model

Primary second model:

```python
formula = """
ln_real_accommodation_yield
~ ln_aor
+ paid_accommodation_share
+ holiday_share
+ foreign_share
+ C(state)
+ C(year)
"""
```

Reason:

Total accommodation expenditure mechanically depends partly on tourist count and stay duration.

The yield model asks a more meaningful economic question:

> Why does each tourist-night generate more value in some states than others?

---

## 14.4 Add robustness diagnostics

Output:

```text
coefficient
standard_error
confidence_interval
p_value
N
states
years
R²
within R² if supported
```

Optional:

```text
wild cluster bootstrap
```

if feasible.

---

# 15. Phase 10 — Rename Root-Cause Analysis

Priority:

```text
P0
```

Search globally:

```bash
rg -i "root.?cause"
```

Replace observational cross-state analysis terminology with:

```text
Exploratory Driver Analysis
```

or:

```text
Structural Diagnostic Analysis
```

unless actual causal identification is implemented.

Add:

```text
This analysis identifies associations and should not be interpreted
as causal evidence.
```

---

# 16. Phase 11 — Cross-State Robustness

Priority:

```text
P1
```

Because N≈16 is small, implement:

## Leave-one-state-out analysis

For each state:

```text
remove state
refit regression
store coefficients
```

Create:

```text
artifacts/model_validation/state_leave_one_out.csv
```

## Influence diagnostics

Calculate:

```text
Cook's distance
leverage
studentized residual
```

Dashboard/methodology only needs summarized results.

Example:

```text
ALOS coefficient remains positive in 15/16 leave-one-state-out models.
```

Do not overclaim significance.

---

# 17. Phase 12 — Hotel Economics

Priority:

```text
P1
```

If consistent official ARR/ADR data are available, calculate:

$$
RevPAR
=
ADR\times\frac{AOR}{100}
$$

Maintain distinction:

```text
AOR = utilization
ADR = pricing
RevPAR = revenue productivity
```

Do not describe AOR as pricing power.

If ADR is unavailable:

```text
N/A
```

rather than imputation unless modelled and labelled.

---

# 18. Phase 13 — Fix VFR Framing

Priority:

```text
P0/P1
```

Search:

```bash
rg -i "VFR trap|VFR leakage|leakage"
```

Avoid representing unpaid lodging as total economic leakage.

Use:

```text
Low commercial-accommodation capture
```

or:

```text
VFR commercial-accommodation conversion opportunity
```

Explain:

```text
VFR visitors may still contribute through food,
shopping, transport, recreation and other expenditure.
```

Where data permits, compare visitor-day spending by accommodation type.

---

# 19. Phase 14 — Upgrade Gravity Model to PPML

Priority:

```text
P0/P1 — major methodological upgrade
```

Inspect:

```text
src/analytics/gravity_corridor_model.py
```

Main model should become:

$$
E(Flow_{odt}|X)
=
\exp(
X_{odt}\beta+
OriginFE+
DestinationFE+
YearFE
)
$$

Use PPML.

Advantages:

```text
supports zero flows
avoids log(0)
avoids clipping to 0.01
better suited to heteroskedastic flow data
```

Keep log-OLS only as a robustness model.

---

# 20. Phase 15 — Remove Gravity Target Leakage

Priority:

```text
P0
```

Do not predict:

```text
Flow_od
```

using:

```text
DestinationTotalTourists_d
```

when it includes:

```text
Flow_od
```

Options:

### Option A

$$
DestinationPull_{-o,d}
=
DestinationTotal_d-Flow_{od}
$$

### Preferred option B

Use:

```text
destination FE
hotel room supply
tourism establishments
population
accessibility
attractions
AOR
ADR if available
```

---

# 21. Phase 16 — Proper Gravity Validation

Priority:

```text
P0
```

## Time split

Use:

```text
Train: 2018–2024
Test: 2025
```

2025 observations must not participate in model training when measuring 2025 predictive performance.

---

## Proper OOS R²

Replace correlation².

Use:

```python
r2 = 1 - (
    ((y_true - y_pred) ** 2).sum()
    /
    ((y_true - y_true.mean()) ** 2).sum()
)
```

Also report:

```text
MAE
RMSE
RMSLE
sMAPE
```

---

## Baselines

Compare against:

### Baseline 1

```text
2025 flow = 2024 flow
```

### Baseline 2

```text
historical mean corridor flow
```

Optional baseline 3:

```text
origin share × destination volume
```

Model performance should be shown relative to these baselines.

---

# 22. Phase 17 — Single Model Metrics File

Priority:

```text
P0
```

Generate:

```text
dashboard/public/data/model_metrics.json
```

Example:

```json
{
  "gravity": {
    "model": "PPML",
    "train_period": "2018-2024",
    "test_period": "2025",
    "r2_oos": 0.42,
    "mae": 123.4,
    "rmse": 210.8,
    "smape": 18.2
  }
}
```

React must load this.

Remove every hard-coded:

```text
coefficient
R²
p-value
sample size
HHI
```

from UI components.

---

# 23. Phase 18 — Structural Change Test

Priority:

```text
P1
```

Instead of separately comparing distance coefficients pre/post, estimate interaction:

$$
Flow
\sim
Distance
+
PostRecovery
+
Distance\times PostRecovery
+
Controls
+
FE
$$

Test:

$$
H_0:
\beta_{Distance\times Post}=0
$$

Interpret:

```text
Distance sensitivity changed / did not change materially.
```

Do not attribute change to highways or road-trip behaviour unless directly tested.

---

# 24. Phase 19 — Corridor Opportunity Redesign

Priority:

```text
P0/P1
```

Raw model residual should only represent:

```text
Below model expected
Near model expected
Above model expected
```

Do not automatically call below-expected flow:

```text
High-potential opportunity
```

---

## Opportunity framework

Opportunity must consider:

```text
Demand Gap
Economic Yield
Capacity Headroom
Accessibility
Market Diversification
Model Confidence
```

Preferred approach:

### Pareto frontier

Avoid arbitrary weights initially.

A corridor is attractive when it is non-dominated across:

```text
high demand gap
high tourism value-added yield
high capacity headroom
good accessibility
useful diversification
```

Optional later composite score may be added only with sensitivity analysis.

---

# 25. Phase 20 — HHI Market Diversification

Priority:

```text
P1
```

Calculate:

$$
HHI=\sum_i share_i^2
$$

For each destination output:

```text
origin_hhi
top_origin_share
top_3_origin_share
meaningful_origin_count
```

Use neutral terminology:

```text
market concentration
feeder concentration
diversification
```

Do not assume concentration is always negative.

---

# 26. Phase 21 — Unify Scenario Engine

Priority:

```text
P0 — critical
```

Current backend/frontend calculation duplication must be removed.

Target:

```text
Python Scenario Engine
        ↓
scenario outputs
        ↓
React visualization
```

React should not independently calculate:

```text
incremental expenditure
incremental GVA
room demand
AOR impact
capacity tier
```

---

# 27. Phase 22 — Add Scenario Affected Share

Priority:

```text
P0/P1
```

Current:

$$
AdditionalNights
=
Tourists\times\Delta ALOS
$$

Improved:

$$
\boxed{
AdditionalNights
=
Tourists
\times
AffectedShare
\times
\Delta ALOS
}
$$

Example inputs:

```text
Campaign reach: 15%
Stay extension among affected visitors: +0.5 nights
```

Add UI control:

```text
Affected visitors
5% ───── 10% ───── 25%
```

---

# 28. Phase 23 — Correct Room-Night Capacity

Priority:

```text
P0
```

Use consistently:

$$
AdditionalRoomNights
=
\frac{AdditionalGuestNights}
{GuestsPerOccupiedRoom}
$$

Then:

$$
ProjectedOccupiedRoomNights
=
BaselineOccupiedRoomNights
+
AdditionalRoomNights
$$

$$
ProjectedAOR
=
\frac{
ProjectedOccupiedRoomNights
}{
AvailableRoomNights
}
$$

`GuestsPerOccupiedRoom` must be clearly identified as:

```text
SCENARIO ASSUMPTION
```

if not directly observed.

No frontend/backend discrepancy allowed.

---

# 29. Phase 24 — Correct VFR Scenario Capacity

Priority:

```text
P0
```

If a scenario converts VFR stays to commercial room demand, converted nights must affect:

```text
economic impact
AND
capacity impact
```

Do not count VFR conversion revenue while omitting associated room nights.

---

# 30. Phase 25 — Scenario Assumption Metadata

Priority:

```text
P1
```

Every scenario output must contain:

```text
inputs
assumptions
sources
empirical values
derived values
scenario values
limitations
```

Example:

```json
{
  "affected_share": {
    "value": 0.15,
    "status": "scenario_assumption"
  },
  "baseline_aor": {
    "value": 67.4,
    "status": "official"
  }
}
```

---

# 31. Phase 26 — Monte Carlo Uncertainty

Priority:

```text
P2
```

Implement after deterministic simulator passes all tests.

Uncertain parameters:

```text
affected_share
ALOS uplift
spend_per_night
VFR conversion rate
guests_per_room
value-added intensity
```

Run:

```text
10,000 simulations
```

Return:

```text
P10
P50
P90
mean
probability projected AOR > threshold
```

Dashboard example:

```text
Median incremental GVA:
RM 47.2m

P10–P90:
RM 31.5m – RM 66.8m

Probability AOR exceeds 80%:
14%
```

---

# 32. Phase 27 — Capacity Sensitivity

Priority:

```text
P1
```

Do not present 80% as a universal sustainability truth.

Use configurable planning thresholds:

```text
75%
80%
85%
```

Show:

```text
Planning threshold selected by user
```

If only annual AOR is available:

```text
Annual occupancy may hide seasonal/weekend capacity pressure.
```

---

# 33. Phase 28 — Fix Corridor → Simulator Workflow

Priority:

```text
P0
```

Current callback must preserve selected corridor.

Store:

```typescript
selectedOrigin
selectedDestination
selectedCorridor
```

Preferred implementation:

```text
URL query parameters
```

Example:

```text
/simulate?origin=Selangor&destination=Melaka
```

Benefits:

```text
shareable
bookmarkable
reproducible
```

Simulator should open pre-populated.

---

# 34. Phase 29 — Dashboard Provenance Drawer

Priority:

```text
P1
```

For every major KPI provide:

```text
Definition
Formula
Source
Reference year
Status
Transformation
Limitations
```

Example:

```text
Tourism Value-Added Yield

RM 94 / visitor-day

Formula
Estimated tourism GVA / visitor-days

Sources
DOSM DTS 2025
DOSM TSA 2025

Status
Derived

Mapping coverage
93.1%

Limitation
National TSA VAI is applied to state expenditure composition.
```

---

# 35. Phase 30 — Visible Data Status

Priority:

```text
P1
```

Render badges:

```text
OFFICIAL
PRELIMINARY
ESTIMATE
DERIVED
MODEL
SCENARIO
```

Example:

```text
2025 TSA
PRELIMINARY
```

Use status metadata already present in the project.

---

# 36. Phase 31 — Remove “Official Brief” Language

Priority:

```text
P0
```

Search:

```bash
rg -i "official.*brief|official policy"
```

Replace:

```text
Official Decision-Support Brief
```

with:

```text
MYTourism Value Intelligence
State Decision-Support Brief
```

Possible subtitle:

```text
Prototype based on official Malaysian tourism data
```

This properly distinguishes official data from project endorsement.

---

# 37. Phase 32 — State Decision Summary

Priority:

```text
P1
```

At top of each state page show:

```text
Tourism Value-Added Yield
Tourism Expenditure Yield
ALOS
Accommodation Yield
AOR
ADR/RevPAR if available
Capacity Headroom
Origin HHI
Primary Constraint
Primary Opportunity
Evidence Confidence
```

Example:

```text
Primary Constraint
Short stay duration

Evidence
ALOS below national median
Accommodation yield above national median
Capacity headroom available

Potential Intervention
Stay-extension campaigns targeted at nearby feeder markets
```

---

# 38. Phase 33 — Evidence-Based Recommendation Engine

Priority:

```text
P1
```

Recommendations should initially be rule-based.

Example:

```python
if (
    alos < median_alos
    and value_added_yield > median_yield
    and capacity_headroom > threshold
):
    recommendation = "Evaluate stay-extension intervention"
```

Each recommendation must include:

```text
recommendation
evidence
metric values
benchmark
source
confidence
limitation
```

Avoid unconstrained LLM recommendation generation.

---

# 39. Phase 34 — Product Value Frontier

Priority:

```text
P1
```

Keep and improve VAI-vs-scale visualization.

Generate:

```text
X = Tourism Consumption
Y = VAI
Bubble Size = Estimated Tourism GVA
```

Optional:

```text
Year animation
```

Use language distinguishing:

```text
Efficiency
Scale
Contribution
Growth
Resilience
```

Do not call high-VAI product automatically most economically important.

---

# 40. Phase 35 — Commercial Implementation Page

Priority:

```text
P1
```

Add:

```text
Implementation
```

page.

## Users

| User                 | Decision                         |
| -------------------- | -------------------------------- |
| MOTAC                | National resource allocation     |
| Tourism Malaysia     | Domestic feeder-market campaigns |
| State tourism boards | State tourism strategy           |
| Local authorities    | Destination capacity planning    |
| DMOs                 | Product/itinerary development    |
| Hotel associations   | Demand development               |

## Operating model

```text
Official data
   ↓
Economic diagnosis
   ↓
Opportunity detection
   ↓
Scenario testing
   ↓
Intervention selection
   ↓
Pilot implementation
   ↓
Observed outcomes
   ↓
Model refresh
```

Document expected refresh:

```text
TSA / DTS: annual
Hotel indicators: quarterly if available
OD model: annual
Scenario assumptions: user configurable
```

---

# 41. Phase 36 — Portfolio Optimization

Priority:

```text
P2
```

Implement after scenario model is stable.

Decision question:

> Given a fixed tourism-development budget, which interventions maximize expected economic value while respecting destination capacity?

Formulation:

$$
\max
\sum_i ExpectedIncrementalGVA_i x_i
$$

subject to:

$$
\sum_i Cost_i x_i\le Budget
$$

$$
ProjectedAOR_d\le Threshold_d
$$

Optional constraints:

```text
regional coverage
risk tolerance
market concentration
minimum investment
maximum interventions/state
```

Use:

```text
OR-Tools
PuLP
scipy.optimize
```

as appropriate.

Dashboard:

```text
Optimize Investment
```

Inputs:

```text
Budget
Capacity threshold
Risk tolerance
Regional constraints
```

Outputs:

```text
Selected interventions
Budget used
Expected GVA
GVA uncertainty
Capacity impact
```

This is a major “wow factor”.

---

# 42. Phase 37 — OD Time Animation

Priority:

```text
P2
```

Add:

```text
2018 → 2025
```

animation.

Modes:

```text
Actual Flow
Expected Flow
Flow Gap
Value Yield
Opportunity
```

Allow users to observe:

```text
COVID disruption
recovery
corridor emergence
market concentration changes
```

---

# 43. Phase 38 — Optional Grounded AI Assistant

Priority:

```text
P3
```

Only implement after all P0/P1 validation.

Assistant should answer from:

```text
state metrics
corridor metrics
scenario results
model metrics
source metadata
```

Example:

```text
Why is Melaka classified as capacity constrained?
```

Answer must reference structured evidence.

Never allow numerical hallucination.

---

# 44. Phase 39 — Test Suite Refactor

Priority:

```text
P0
```

Suggested:

```text
tests/
├── ingestion/
├── data_quality/
├── accounting/
├── panel/
├── gravity/
├── opportunity/
├── scenario/
├── dashboard_contract/
└── snapshot/
```

---

## Data tests

Validate:

```text
ranges
duplicates
null handling
totals
category shares
geographic keys
```

---

## Accounting tests

Validate formulas:

```text
VAI
Visitor Days
TEY
Accommodation Yield
Estimated Tourism GVA
Tourism GVA Intensity
Tourism Value-Added Yield
Mapping Coverage
RevPAR
```

---

## Gravity tests

Validate:

```text
2025 absent from training set
zero flows supported
no target leakage
correct OOS R²
baselines calculated
prediction schema valid
```

---

## Scenario tests

Validate:

```text
Affected Share
ALOS uplift
room-night conversion
VFR room demand
capacity threshold
zero-impact scenario
missing capacity
```

---

# 45. Phase 40 — Separate Scientific Tests from Snapshot Tests

Priority:

```text
P0
```

Move assertions such as:

```python
assert top_product == "Accommodation services"
```

into:

```text
tests/snapshot/
```

Similarly:

```text
Selangor → Melaka should currently appear as priority
```

is snapshot behavior, not scientific validation.

Scientific tests should verify:

```text
formulas
data integrity
model validation
reconciliation
```

Never print:

```text
Hypothesis CONFIRMED
```

from a test whose expected result was predetermined.

---

# 46. Phase 41 — Dashboard Contract Tests

Priority:

```text
P0
```

Create automated tests ensuring:

```text
dashboard R² == Python R²
dashboard coefficients == model output
dashboard scenario GVA == scenario engine output
dashboard HHI == analytical output
dashboard state KPI == pipeline output
```

Goal:

> No model statistic should differ between README, Python output and dashboard.

---

# 47. Phase 42 — Documentation

Priority:

```text
P1
```

Create:

```text
docs/methodology.md
docs/data_dictionary.md
docs/model_validation.md
docs/data_quality.md
docs/limitations.md
docs/implementation_model.md
```

---

## Methodology

Explain:

```text
problem statement
economic decomposition
TSA analysis
state productivity
panel analysis
gravity model
opportunity framework
scenario model
uncertainty
optimization
```

---

## Limitations

Explicitly state:

```text
observational relationships are not causal
state sample is small
national VAI applied to state spending composition
annual AOR may hide peak congestion
some spending categories may remain unmapped
scenario outcomes depend on assumptions
survey estimates contain sampling uncertainty
```

Transparency improves credibility.

---

# 48. Phase 43 — README Rewrite

Priority:

```text
P1
```

README should contain:

```text
1. Problem
2. Why it matters
3. Main research question
4. Economic framework
5. Data sources
6. Analytical architecture
7. Main findings
8. Validation
9. Dashboard
10. Commercial implementation
11. Limitations
12. Reproduction instructions
```

Do not let README contain hard-coded results manually copied from earlier runs.

Where possible generate summary values automatically.

---

# 49. Phase 44 — Dashboard Information Architecture

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
```

Each page should answer one decision question.

---

## National Value

> Where does Malaysian tourism create economic value?

---

## State Productivity

> Which states generate the greatest economic value from each visitor-day?

---

## Drivers

> Which measurable factors are associated with tourism economic productivity?

---

## Mobility

> Where do domestic visitors come from and where do they travel?

---

## Opportunities

> Which corridors combine flow gap, high yield and spare capacity?

---

## Simulate

> What might happen under a specific tourism intervention?

---

## Optimize

> How should a fixed tourism-development budget be allocated?

---

## Action Brief

> What should a decision maker implement and monitor?

---

# 50. Phase 45 — SDG Integration

Priority:

```text
P1
```

Do more than display SDG logos.

## SDG 8.9

Connect:

```text
Tourism GVA
Tourism Value-Added Yield
local tourism economic productivity
```

to sustainable tourism economic development.

## SDG 12.b

Connect:

```text
state monitoring
visitor-day productivity
capacity monitoring
scenario evaluation
```

to tools for monitoring tourism impacts.

Add methodology explanation.

---

# 51. Competition Storyline

The final presentation should follow:

```text
Malaysia has recovered tourism volume
            ↓
Volume alone does not measure economic sustainability
            ↓
Measure economic value generated from each visitor-day
            ↓
Understand state productivity differences
            ↓
Understand what is associated with those differences
            ↓
Map where domestic visitors actually travel
            ↓
Identify demand gaps with economic value + capacity
            ↓
Test interventions
            ↓
Quantify uncertainty
            ↓
Allocate limited resources
            ↓
Produce actionable policy brief
```

---

# 52. Dashboard Headline

Recommended:

> **From More Tourists to More Value**

Supporting sentence:

> MYTourism Value Intelligence helps Malaysian destinations identify how to generate greater domestic economic value from each visitor-day while respecting destination capacity and market risk.

---

# 53. Final Analytical Architecture

```text
                     OFFICIAL DATA
                          │
                          ▼
                ┌──────────────────┐
                │ INGESTION & QA   │
                │ Parsing          │
                │ Validation       │
                │ Reconciliation   │
                │ Provenance       │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ ECONOMIC METRICS │
                │ Real RM          │
                │ Visitor Days     │
                │ TEY              │
                │ GVA Intensity    │
                │ Value Yield      │
                └────────┬─────────┘
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
      TSA PRODUCT     STATE PANEL      OD GRAVITY
      VALUE MODEL     ECONOMETRICS     PPML MODEL
          │              │               │
          └──────────────┼───────────────┘
                         ▼
               ┌────────────────────┐
               │ OPPORTUNITY ENGINE │
               │ Flow Gap           │
               │ Economic Yield     │
               │ Capacity           │
               │ Diversification    │
               └──────────┬─────────┘
                          ▼
               ┌────────────────────┐
               │ SCENARIO ENGINE    │
               │ Reach              │
               │ ALOS               │
               │ Conversion         │
               │ Capacity           │
               │ Uncertainty        │
               └──────────┬─────────┘
                          ▼
               ┌────────────────────┐
               │ OPTIMIZATION       │
               │ Budget             │
               │ Capacity           │
               │ Economic Value     │
               │ Risk               │
               └──────────┬─────────┘
                          ▼
               ┌────────────────────┐
               │ DECISION DASHBOARD │
               │ Monitor            │
               │ Diagnose           │
               │ Target             │
               │ Simulate           │
               │ Optimize           │
               │ Act                │
               └────────────────────┘
```

---

# 54. Exact Implementation Order

Codex should execute in the following order.

## Sprint 1 — Integrity

```text
[ ] Baseline current outputs
[ ] Remove absolute paths
[ ] Fix project metadata
[ ] Create master pipeline
[ ] Replace missing-value defaults
[ ] Remove frontend empirical fallbacks
[ ] Add source registry
[ ] Add QA report
```

## Sprint 2 — Economic Metrics

```text
[ ] Add real RM
[ ] Remove DVR terminology
[ ] Remove 0.50 unmatched VAI
[ ] Add mapping coverage
[ ] Add visitor-days
[ ] Add TEY
[ ] Add accommodation yield
[ ] Add Tourism GVA Intensity
[ ] Add Tourism Value-Added Yield
[ ] Rebuild state typology
[ ] Fix VFR terminology
```

## Sprint 3 — Econometrics

```text
[ ] Add year FE
[ ] Add state-clustered errors
[ ] Add yield model
[ ] Rename root-cause analysis
[ ] Add leave-one-state-out
[ ] Add influence diagnostics
```

## Sprint 4 — Gravity

```text
[ ] Implement PPML
[ ] Add origin FE
[ ] Add destination FE
[ ] Add year FE
[ ] Remove target leakage
[ ] Implement true holdout
[ ] Fix OOS R²
[ ] Add MAE/RMSE/RMSLE/sMAPE
[ ] Add naive baselines
[ ] Test distance structural change
```

## Sprint 5 — Opportunity Engine

```text
[ ] Separate model gap from opportunity
[ ] Add capacity
[ ] Add yield
[ ] Add HHI
[ ] Add accessibility
[ ] Add confidence
[ ] Implement Pareto opportunity framework
```

## Sprint 6 — Scenario Engine

```text
[ ] One source of truth
[ ] Add affected share
[ ] Fix room-night conversion
[ ] Fix VFR capacity
[ ] Add assumption metadata
[ ] Add capacity sensitivity
```

## Sprint 7 — Dashboard Integrity

```text
[ ] Remove hard-coded model values
[ ] Load model_metrics.json
[ ] Fix corridor → simulator
[ ] Display data status
[ ] Add provenance drawer
[ ] Rename official brief
[ ] Add state decision summary
[ ] Update VAI-scale visualization
```

## Sprint 8 — Commercial / Wow

```text
[ ] Add implementation page
[ ] Add Monte Carlo
[ ] Add portfolio optimizer
[ ] Add OD animation
[ ] Optional grounded AI
```

---

# 55. Definition of Done — Code Changes

A task is not complete until:

```text
[ ] Existing code inspected
[ ] New implementation completed
[ ] Unit tests added
[ ] Integration tests added where relevant
[ ] Relevant tests pass
[ ] No regression detected
[ ] Output manually sanity checked
[ ] Documentation updated
[ ] Dashboard contract checked
[ ] No unsupported causal claims introduced
```

---

# 56. Definition of Done — Analytical Metric

Every metric must document:

```text
[ ] Name
[ ] Formula
[ ] Unit
[ ] Source
[ ] Reference period
[ ] Status
[ ] Missing-value behavior
[ ] Interpretation
[ ] Limitation
```

---

# 57. Definition of Done — Dashboard Component

```text
[ ] Responsive
[ ] Keyboard-accessible where practical
[ ] No console error
[ ] Loading state
[ ] Error state
[ ] Missing-data state
[ ] Units visible
[ ] Source accessible
[ ] Status visible where necessary
[ ] Analytical value generated by backend
[ ] No invented empirical default
```

---

# 58. Final Pre-Submission Audit

## Methodology

```text
[ ] Problem statement centered on economic sustainability
[ ] Main KPI = value per visitor-day
[ ] SDG linkage explained
[ ] Two-way FE implemented
[ ] Clustered uncertainty implemented
[ ] Root-cause wording removed
[ ] PPML implemented
[ ] True OOS validation implemented
[ ] Scenario clearly non-causal
```

## Data Quality

```text
[ ] Official sources documented
[ ] Current releases documented
[ ] Preliminary/estimate status visible
[ ] No silent empirical fallback
[ ] Parser failures visible
[ ] Mapping coverage reported
[ ] Constant-price RM available
[ ] Reconciliation tests pass
```

## Dashboard

```text
[ ] All model values generated
[ ] No hard-coded R²/coefficient/HHI
[ ] Corridor selection passes to simulator
[ ] Backend/frontend scenario outputs identical
[ ] Provenance drawer works
[ ] N/A states render properly
[ ] Mobile/tablet checked
[ ] Action brief works
```

## Commercial Impact

```text
[ ] Target users identified
[ ] Decisions identified
[ ] Implementation model explained
[ ] Refresh model explained
[ ] Scenario workflow demonstrated
[ ] Monitoring loop demonstrated
```

## Creativity

```text
[ ] Geospatial OD
[ ] Econometrics
[ ] Value-added accounting
[ ] Capacity-aware scenarios
[ ] Uncertainty
[ ] Portfolio optimization if possible
[ ] OD time animation if possible
```

---

# 59. Recommended Codex Commit Strategy

Create small commits.

Suggested sequence:

```text
chore: establish analytical baseline

refactor: centralize project paths and pipeline configuration

fix: preserve missing empirical values across ingestion

test: add tourism data reconciliation and missing-value checks

feat: add source provenance registry and quality report

feat: add constant-price tourism economic metrics

refactor: replace value-retention metric with tourism gva intensity

feat: add visitor-day and tourism value-added yield metrics

refactor: rebuild state productivity typology

feat: implement two-way fixed-effects state models

feat: add clustered inference and robustness diagnostics

refactor: reframe root-cause analysis as exploratory diagnostics

feat: implement ppml domestic tourism gravity model

fix: remove gravity destination-volume target leakage

fix: implement genuine out-of-sample gravity validation

feat: add gravity baseline comparisons

refactor: separate flow residuals from corridor opportunity

feat: add capacity-yield-diversification opportunity framework

refactor: centralize scenario calculation in python

feat: add intervention reach parameter

fix: align room-night and vfr capacity calculations

feat: expose scenario assumptions and capacity sensitivity

refactor: remove hard-coded analytical dashboard values

fix: persist corridor selection into simulator

feat: add metric provenance and status UI

feat: add evidence-based state decision summaries

feat: add monte carlo tourism intervention uncertainty

feat: add tourism investment portfolio optimizer

feat: add longitudinal od network animation

docs: update methodology data dictionary limitations and implementation

test: add dashboard analytical contract tests
```

---

# 60. Final Product Definition

The completed system should be positioned as:

> **MYTourism Value Intelligence is a Malaysian sustainable-tourism economic decision-support system that combines official tourism accounts, domestic-tourism surveys, accommodation operations and origin-destination mobility data to evaluate how efficiently destinations convert visitor-days into domestic economic value. It identifies structural constraints and market opportunities, estimates travel-flow gaps, tests interventions under accommodation-capacity constraints, quantifies uncertainty and supports evidence-based allocation of tourism-development resources.**

Primary message:

$$
\boxed{
Do\ not\ only\ maximize\ tourists.
Maximize\ sustainable\ economic\ value\ per\ visitor-day.
}
$$

---

# 61. Codex Stop Conditions

Codex must stop and report instead of masking the issue when:

```text
official source data are missing
an empirical field cannot be parsed
state/national totals fail reconciliation materially
model does not converge
PPML suffers unidentified fixed effects
training/test leakage is detected
scenario capacity data are unavailable
dashboard output differs from backend result
```

Do not solve these by inventing data.

Report:

```text
problem
affected file
affected metric
probable cause
recommended resolution
```

---

# 62. Codex Progress Tracking

Create:

```text
IMPLEMENTATION_STATUS.md
```

Format:

```markdown
# Implementation Status

## P0

- [x] Remove hard-coded paths
- [x] Preserve missing values
- [ ] Add inflation adjustment
- [ ] Two-way FE
- [ ] PPML
...

## Latest Validation

Pipeline: PASS
Tests: 148 passed / 0 failed
Dashboard build: PASS
Data reconciliation: PASS

## Open Issues

1. ADR unavailable for Sabah 2019.
2. PPML drops one fixed-effect group.
3. CPI mapping pending validation.
```

Update this file after each implementation phase.

---

# 63. Codex Final Instruction

Do not optimize the project for the largest number of algorithms.

Optimize for:

```text
Correctness
Transparency
Reproducibility
Interpretability
Decision usefulness
Statistical defensibility
Data integrity
```

A simpler method with strong justification and validation is preferable to a more complex model with weak evidence.

The final product must be able to answer five judge questions convincingly:

### 1. Where did this number come from?

Show source, formula and status.

### 2. Why do you believe this relationship?

Show model specification, diagnostics and limitations.

### 3. Why should this corridor be targeted?

Show flow gap, value yield, capacity and market evidence.

### 4. What happens if your assumptions are wrong?

Show sensitivity or uncertainty.

### 5. How would a real organization use this?

Show the implementation and decision workflow.

If the system can answer all five clearly, the project is ready for final competition presentation.
