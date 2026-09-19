# AGENTS.md — Malaysia Tourism Value Optimizer

## 1. Purpose

This repository builds a datathon project called **Malaysia Tourism Value Optimizer**.

Primary goal:

> Identify where Malaysia can generate more domestic economic value from existing tourism demand, with special focus on high-value tourism activities, accommodation expenditure, length of stay, and domestic origin-destination tourism corridors.

This project focuses on the **economic dimension of sustainable tourism**. Do not claim that the project measures complete environmental or social sustainability.

The core strategic shift is:

`more visitors` -> `more economic value from existing visitors`

## 2. Core research questions

1. Which tourism products consistently have the highest value-added intensity from 2015-2025?
2. Is accommodation consistently a high-value-added tourism activity?
3. What factors are associated with higher accommodation expenditure?
4. How is Average Length of Stay (ALOS) related to accommodation expenditure and tourism economic yield?
5. Which Malaysian states receive high domestic tourist flows but have relatively short stays or weak accommodation expenditure?
6. Which origin-destination corridors have the strongest potential to convert existing visitor volume into additional overnight stays and accommodation value?
7. Under transparent scenarios, how much additional accommodation expenditure and potential value added could be generated?

## 3. Non-negotiable analytical definitions

### Value-Added Intensity (VAI)

Use:

`VAI[i,t] = GVA[i,t] / DomesticSupply[i,t]`

Interpretation: proportion of the corresponding tourism activity's supply/output represented by Gross Value Added.

Use VAI as the main product/industry value-efficiency indicator.

### Estimated tourism-attributable GVA

When needed, use the analytical proxy:

`EstimatedTourismGVA[i,t] = ITC[i,t] * VAI[i,t]`

Equivalent under the simple proportional allocation approximation:

`EstimatedTourismGVA[i,t] = IndustryGVA[i,t] * TourismRatio[i,t]`

Never label this as official product-level TDGVA.

Preferred labels:
- `Estimated tourism-attributable GVA`
- `Tourism value-added proxy`

### Tourism ratio

Treat the tourism ratio as the share of relevant domestic supply consumed by visitors, according to the TSA concept used in the source tables.

Do not multiply a tourism-attributable GVA by the tourism ratio again.

### Internal Tourism Consumption (ITC)

Use the official TSA definition. Do not assume Domestic Tourism Survey expenditure totals are conceptually identical to TSA ITC.

### Accommodation performance metrics

When definitions are compatible, calculate:

`AccommodationShare = AccommodationExpenditure / TotalTourismExpenditure`

`AccommodationSpendPerVisitor = AccommodationExpenditure / DomesticVisitors`

`AccommodationSpendPerTourist = AccommodationExpenditure / OvernightTourists`

Do not mix incompatible numerators and denominators.

## 4. Data sources

Primary official sources:

1. **Tourism Satellite Account Malaysia 2015-2025**
   - GVA by tourism industry
   - domestic supply by tourism product
   - tourism ratios
   - ITC
   - TDGVA / TDGDP
   - tourism employment

2. **Domestic Tourism Survey Malaysia 2025**
   - visitors
   - tourists
   - trips
   - total expenditure
   - expenditure components
   - ALOS
   - origin-destination tourism flows

3. **State Domestic Tourism Survey files**
   - same/similar indicators for each Malaysian state

4. Optional official datasets
   - hotel occupancy
   - Average Room Rate
   - hotel guests
   - hotel and room inventory
   - Malaysian state boundary GIS files

Prefer DOSM and other official Malaysian government sources. Record dataset name, table/sheet, year, unit, revision status, and transformation used.

## 5. Data model

Prefer transforming Excel workbooks into tidy analytical tables.

### tourism_product_year

Required fields where available:

- year
- product
- industry
- itc
- domestic_supply
- gva
- tourism_ratio
- employment
- vai
- estimated_tourism_gva
- data_status

### state_year

Required fields where available:

- year
- state
- visitors
- tourists
- trips
- total_expenditure
- accommodation_expenditure
- food_expenditure
- transport_expenditure
- shopping_expenditure
- recreation_expenditure
- alos
- occupancy
- rooms

### origin_destination

Required fields:

- year
- origin
- destination
- tourist_flow

Do not duplicate values to force datasets to reconcile.

## 6. Data quality rules

Before modelling or dashboard work:

1. Standardize state names and codes.
2. Preserve original units.
3. Explicitly convert RM thousand / million / billion when necessary.
4. Check missing values.
5. Check duplicate rows.
6. Check year labels and source-table status.
7. Preserve `e`, `p`, and `r` meanings where present:
   - `e` = estimate
   - `p` = preliminary
   - `r` = revised
8. Reconcile product totals against official totals where concepts match.
9. Do not force reconciliation where TSA and survey definitions differ.
10. Add assertions/tests for formulas used in production code.

## 7. Analytical pipeline

Follow this order unless the task explicitly requires otherwise.

### Stage A — Product value analysis

For each tourism product/industry across 2015-2025:

- calculate VAI
- calculate ITC scale
- calculate estimated tourism-attributable GVA proxy if useful
- calculate median VAI
- calculate mean VAI
- calculate coefficient of variation
- calculate trend
- compare pre-COVID and post-recovery periods

Use periods:

- Pre-COVID: 2015-2019
- Disruption/recovery: 2020-2022
- Post-recovery: 2023-2025

Do not let COVID anomalies dominate structural conclusions.

### Stage B — Identify high-value products

Do not rank products using VAI alone.

Use at least:

- value-added intensity
- tourism expenditure scale
- consistency / volatility
- trend

Strategic interpretation:

- High VAI + High ITC = high-value core activity
- High VAI + Low ITC = growth opportunity
- Low VAI + High ITC = efficiency-improvement priority
- Low VAI + Low ITC = lower immediate economic priority

Accommodation is a hypothesis to validate, not a predetermined winner.

### Stage C — Accommodation analysis

If accommodation is supported as a high-value activity, analyse:

- accommodation expenditure
- accommodation share
- accommodation spend per visitor/tourist
- ALOS
- overnight tourists
- paid accommodation usage
- hotel occupancy/capacity where available

Conceptual decomposition:

`AccommodationExpenditure ≈ OvernightTourists * ALOS * AccommodationSpendPerNight`

Use this only when variables support the calculation.

Policy levers:

- day trip -> overnight stay
- short stay -> longer stay
- low-value night -> higher-value night

### Stage D — Origin-destination value network

The OD component is not just a network chart.

Its purpose is:

> Identify which existing domestic tourism corridors should be targeted to convert high visitor flow into higher overnight economic value.

Use:

`F[o,d] = tourist flow from origin o to destination d`

Useful network measures:

- weighted out-strength: major origin markets
- weighted in-strength: major destinations
- destination origin-share concentration / HHI

Avoid adding irrelevant graph metrics purely for complexity.

### Stage E — Tourism Value Corridor classification

For each origin-destination corridor combine:

- tourist flow
- destination ALOS
- accommodation expenditure performance
- accommodation value opportunity

Preferred transparent classification:

**Priority Conversion Corridor**
- high flow
- low ALOS and/or weak accommodation spending

**Protect / Deepen**
- high flow
- strong ALOS
- strong accommodation value

**Growth Opportunity**
- lower/medium flow
- strong destination accommodation value

**Lower Priority**
- low flow
- weak value indicators

Prefer rule-based or percentile classifications over arbitrary weighted scores.

### Stage F — Scenario simulator

A scenario may estimate:

`AdditionalTouristNights[o,d] = TouristFlow[o,d] * DeltaALOS`

If accommodation spend per night is available:

`AdditionalAccommodationSpend = AdditionalTouristNights * AccommodationSpendPerNight`

Then:

`PotentialAdditionalValueAdded = AdditionalAccommodationSpend * AccommodationVAI`

Every scenario output must display:

> Scenario estimate, not a causal forecast.

Never present scenario output as guaranteed impact.

## 8. Statistical / ML guidance

Prioritize transparent methods that match the sample size.

Good defaults:

- descriptive statistics
- correlation / Spearman correlation
- robust regression
- panel regression if state-by-year data are available
- hierarchical clustering for a small number of states
- HHI / concentration analysis
- geospatial analysis
- transparent scenario simulation

Use XGBoost / CatBoost / SHAP only if the dataset is large enough to justify it.

Do not use deep learning, reinforcement learning, or complex ML merely for novelty.

If using SHAP, describe it as model-prediction explanation, not causal proof.

## 9. Claims and interpretation guardrails

Never claim:

- accommodation causes TDGVA growth
- GVA * tourism ratio is official product-level TDGVA
- ALOS increase guarantees RM X impact
- origin X spends more than origin Y unless origin-specific expenditure exists
- this project measures total sustainable tourism
- correlation proves causation

Preferred wording:

- `associated with`
- `value-added intensive`
- `estimated`
- `scenario`
- `potential opportunity`
- `economic dimension of sustainable tourism`

## 10. Travel-agency interpretation

If discussing Travel Agencies and Other Reservation Services:

Do not say the industry collapsed in 2025 solely because GVA/supply declined.

Correct interpretation:

- GVA increased
- supply increased much faster
- ITC increased strongly
- tourism ratio was relatively stable
- therefore value-added intensity fell

Potential mechanisms such as platform commissions, digitalisation, intermediate consumption, foreign services, low-margin bookings, or recovery normalisation are hypotheses unless validated by additional data.

## 11. SDG alignment

Primary:

- SDG 8, especially Target 8.9: sustainable tourism, jobs, local culture and products

Secondary:

- SDG 12, especially Target 12.b: monitoring sustainable-tourism impacts

Always state:

> This prototype focuses on the economic dimension of sustainable tourism. Environmental and broader social dimensions are future extensions.

## 12. Dashboard / product requirements

Product name:

**Malaysia Tourism Value Optimizer**

Alternative:

**MYTourism Value Intelligence**

Treat it as a tourism economic decision-support system, not merely a dashboard.

Minimum views:

### View 1 — Tourism Value Monitor

Show:
- ITC
- TDGVA
- TDGVA/ITC
- VAI by product
- VAI trend
- ITC scale
- high-value products
- value-conversion warnings

### View 2 — Accommodation Opportunity Map

Show by state:
- visitors
- tourists
- total expenditure
- accommodation expenditure
- accommodation share
- accommodation spend per visitor
- ALOS
- optional occupancy/capacity

### View 3 — Tourism Value Corridor

Show:
- origin -> destination flow
- top origins for selected destination
- destination ALOS
- accommodation performance
- source concentration
- corridor category

### View 4 — Scenario Simulator

Inputs:
- origin
- destination
- Delta ALOS and/or overnight-conversion scenario

Outputs:
- additional tourist nights
- additional accommodation expenditure
- potential additional value-added proxy

## 13. UX requirements

The final dashboard must be:

- responsive
- fast
- clear
- professional
- visually consistent
- interactive only where interaction helps decisions

Every major visual should answer a specific question.

Avoid decorative charts.

Use plain-language insight summaries so a judge or policymaker does not need to interpret every chart manually.

## 14. Geospatial requirements

If GIS boundaries are available:

- use a Malaysia state choropleth
- allow state selection
- use OD flows as map arcs or an OD heatmap
- keep state naming consistent with analytical tables

The map should help answer where intervention opportunities exist, not serve as decoration.

## 15. Commercial / implementation framing

Potential users:

- MOTAC
- Tourism Malaysia
- state tourism boards
- local authorities
- destination-management organisations
- hotel associations
- tourism investors
- event organisers

Core product functions:

**Monitor** — Which activities create value?

**Diagnose** — Where is value conversion weak?

**Target** — Which states/corridors should be prioritised?

**Simulate** — What is the potential RM opportunity under a transparent scenario?

Future architecture:

`Official data -> ETL -> Unified tourism database -> Analytics engine -> OD opportunity engine -> Scenario engine -> Dashboard/API`

## 16. Coding expectations

When modifying the repository:

1. Inspect existing architecture before adding new libraries or patterns.
2. Reuse existing utilities/components where reasonable.
3. Separate raw data ingestion, transformations, analytics, and UI code.
4. Keep formulas in reusable tested functions rather than embedding them in chart components.
5. Use descriptive variable names that match tourism terminology.
6. Preserve raw input files; write cleaned/derived data to separate paths.
7. Keep derived outputs reproducible from source data.
8. Add comments only where accounting logic or transformations are non-obvious.
9. Do not hardcode analytical results that can be derived from data.
10. Prefer deterministic pipelines.

## 17. Suggested repository structure

Adapt to the existing repository rather than forcing this structure if one already exists.

```text
/
├── AGENTS.md
├── README.md
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── geo/
├── src/
│   ├── ingestion/
│   ├── transforms/
│   ├── analytics/
│   ├── network/
│   ├── scenarios/
│   └── validation/
├── dashboard/
├── notebooks/
├── tests/
└── docs/
```

## 18. Validation checklist before considering a task complete

For data/analytics changes:

- formulas are unit-tested or independently checked
- units are correct
- state names reconcile
- years are correct
- preliminary/estimated statuses are preserved
- totals are reconciled where concepts allow
- no division by zero / silent missing-value substitution
- derived metrics have documented formulas
- scenario outputs state assumptions

For dashboard changes:

- no broken interactions
- loading/error/empty states handled
- values match analytical tables
- filters update all relevant views consistently
- mobile/desktop layouts remain usable
- chart labels and units are explicit

## 19. Priority order for the 3-day datathon

If time is constrained, prioritize in this order:

1. Correct TSA VAI calculations and validation
2. State accommodation + ALOS analysis
3. Origin-destination data integration
4. Tourism Value Corridor classification
5. Interactive Malaysia state map
6. Scenario simulator
7. Optional advanced network/community analysis

Never sacrifice data correctness or a working dashboard for optional ML.

## 20. Decision rule for new ideas

Before adding a model, metric, page, package, or visualization, ask:

> Does this help identify, explain, target, or simulate how Malaysia can generate greater domestic economic value from existing tourism demand?

If not, it is probably out of scope for the datathon prototype.

## 21. One-sentence project description

> Malaysia Tourism Value Optimizer integrates Tourism Satellite Account data with state tourism expenditure, length-of-stay, geospatial information, and origin-destination flows to identify where existing visitor demand can be converted into higher overnight economic value and to simulate the potential impact of targeted tourism strategies.
