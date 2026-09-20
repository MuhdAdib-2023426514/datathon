# Analytics improvement implementation plan

Project: **Malaysia Tourism Value Optimizer**  
Prepared: **2026-09-20**  
Status: **Planned — implementation has not started**

## 1. Objective and scope

Correct the analytical defects identified in the `src/` review, strengthen statistical evidence, and propagate consistent results into the dashboard. Success means that policy comparisons can be traced to compatible source observations, reproducible formulas, explicit assumptions, and appropriate validation.

This prototype focuses on the economic dimension of sustainable tourism. Environmental and broader social dimensions are future extensions.

Follow [AGENTS.md](../AGENTS.md), particularly its accounting definitions, data quality requirements, analytical stages, and claims guardrails. Reuse the existing Python, DuckDB, Pandas, SciPy, Statsmodels, and React architecture. Add dependencies only if an identified requirement cannot reasonably be met with the current stack.

This document is an execution plan. Its checkboxes describe future work; creating this file does not implement or validate those changes.

## 2. Review evidence to preserve

Capture these observations in a dated comparison report before implementation. They describe the reviewed database and code, not required results for future datasets.

| Finding | Evidence from the reviewed implementation |
| --- | --- |
| Missing accommodation GVA component | Kuala Lumpur's 2025 SDG proxy omitted approximately RM1,669 million. Adding only that term changed the calculated rate from 51.5% to 61.4%, with all other assumptions unchanged. |
| Wrong population for corridor conversion | A 1% day-trip conversion with zero ALOS extension returned RM18.15 million for Selangor → Melaka, Perlis → Melaka, and an invalid origin. |
| Incorrect baseline period | Exported Kuala Lumpur `baseline_2025` visitors were 31.02 million, versus 35.06 million in the 2025 state panel. |
| Historical outputs reuse current results | Selangor → Melaka had identical exported origin share and gravity prediction in 2018 and 2025. |
| Incorrect validation metric | Squared correlation was 0.5886; predictive R² was 0.4863. The training sample had 1,650 observations, despite its 1,680 label. |
| Sensitive ALOS conclusion | The baseline coefficient was approximately 1.61. Adding year effects and state-clustered errors produced approximately 0.66, with a 95% interval crossing zero. This was a sensitivity check, not a definitive replacement model. |
| Missing portfolio capacity assessment | Extending all interstate feeder stays to Pahang by 0.5 nights implied approximately 101% annual occupancy under the engine's assumptions. |
| Different HHI populations | Sabah interstate HHI was 1,449.92; all-origin HHI was 5,746.95. |
| Uninformative radar scale | Fifteen of sixteen states had a nightly-yield radar score of zero. |
| Inadequate validation coverage | Both existing validation scripts passed despite these issues. |

## 3. Coverage and execution order

Priority meanings: **P1** corrects results or evidence used in decisions; **P2** improves interpretation, robustness, or maintenance. Both priorities are required to complete this plan.

| Review recommendation | Work package | Priority |
| --- | --- | --- |
| 1. Restore accommodation GVA in SDG metrics | W2 | P1 |
| 2. Correct corridor day-trip conversion scope | W7 | P1 |
| 3. Export actual 2025 baselines | W9 | P1 |
| 4. Remove historical joins to 2025-only results | W4, W6, W9 | P1 |
| 5. Correct gravity validation and target-derived predictors | W6 | P1 |
| 6. Add panel robustness and appropriate inference | W5 | P1 |
| 7. Assess aggregate capacity and remove invented defaults | W7 | P1 |
| 8. Separate HHI populations | W4 | P2 |
| 9. Derive cluster descriptions and repair radar scales | W8 | P2 |
| 10. Preserve missingness and imputation provenance | W1 | P1 |
| Shared metric layer and source-derived VAI | W1, W2, W7, W9 | P1 |
| Better accommodation decomposition | W3, W5 | P2 |
| Stronger validation and alternative-result tests | W0 and every subsequent package | P1 |
| Correct interpretation of driver attribution | W5, W9 | P2 |
| Regenerate reproducible outputs and revise claims | W10 | P1 |

Execute in this order: **W0 → W1 → W2 → W3 → W4 → W5 → W6 → W7 → W8 → W9 → W10**. W0–W1 establish validation and input contracts; W2–W4 establish accounting, state metrics, and network definitions before model and scenario work. Implement the necessary tests alongside each change.

## 4. Work packages

### W0 — Establish a reproducible review baseline

**Dependencies:** None.  
**Main files:** `src/validation/test_tsa_accounting.py`, `src/validation/test_state_and_corridors.py`, proposed `tests/` fixtures and test modules.

- [ ] Record the code revision, source inventory/checksums, database schema, table counts, key uniqueness, current model outputs, and dashboard JSON schema.
- [ ] Run both existing validation scripts and preserve their results in a review report.
- [ ] Introduce small synthetic fixtures for accounting components, OD flows, multiple years, missing inputs, and capacity portfolios. Use the standard-library test runner unless a stronger requirement emerges.
- [ ] Make affected functions accept explicit input frames, database paths, and output paths so verification can use temporary storage.
- [ ] Separate immutable ingestion results from enriched analytical outputs; ensure integration tests never overwrite the working database or published JSON.
- [ ] Add reproductions of the confirmed defects as initially failing tests where the current interfaces permit it.

**Acceptance:** Tests reproduce the relevant defects with independently specified expected values. Existing outputs remain available for comparison, and raw files are preserved.

### W1 — Establish data contracts, provenance, and missing-value rules

**Dependencies:** W0.  
**Main files:** `src/ingestion/tsa_parser.py`, `state_parser.py`, `multi_year_state_parser.py`, `od_panel_parser.py`, `dts_profile_parser.py`, `dts_purpose_parser.py`, `granular_dts_parser.py`, `hies_income_parser.py`, `population_state_parser.py`, `mytourism_kpi_parser.py`; proposed shared transformation/validation utilities.

- [ ] Centralize canonical state names/codes and explicit unit conversion helpers without changing supported source layouts unnecessarily.
- [ ] Define unique keys: `(product_id, year)`, `(state, year)`, and `(origin, destination, year)`. Validate merge cardinality and report unmatched keys.
- [ ] Replace fabricated defaults such as `tourists = visitors * 0.5`, `ALOS = 2.4`, missing spend = zero, and unobserved model features = arbitrary constants with nullable values and quality flags.
- [ ] Preserve observed zero separately from unknown, suppressed, invalid, and missing observations. Remove denominator replacements such as `.replace(0, 1)` from affected calculations.
- [ ] Record source file, sheet/table, source year, original unit, normalized unit, revision status, and transformation. Use per-metric provenance or a companion provenance table where one row contains multiple sources.
- [ ] Preserve official `e`, `p`, and `r` meanings. Record analyst interpolation/extrapolation separately so it cannot be mistaken for an official DOSM estimate; retain HIES income status through downstream joins.
- [ ] Preserve full calculation precision and round at presentation/export boundaries with documented tolerances.
- [ ] Audit whether ALOS represents days or nights, whether flow counts represent persons or trips, and whether expenditure and population scopes match. Do not apply a day-to-night conversion without source support.
- [ ] Validate source layouts and year headers rather than silently selecting a fallback column. Make parse failures and excluded records visible in a quality report.
- [ ] Add an explicit observed-only analysis path. Any imputed sensitivity dataset must identify the method, affected variables, and number of observations; fit learned imputations within training folds only.

**Acceptance:** Missing inputs never silently become observed-looking numbers. Duplicate keys, incompatible units, invalid joins, and unknown states fail validation. Unavailable optional metrics stay null with a reason, while incomplete required inputs stop only the dependent calculation.

### W2 — Centralize accounting and repair TSA/SDG calculations

**Dependencies:** W1.  
**Main files:** `src/analytics/product_value.py`, `sdg_sustainable_metrics.py`, `state_diagnostics.py`, `src/ingestion/tsa_parser.py`; proposed reusable accounting module.

- [ ] Implement tested pure functions for VAI, estimated tourism-attributable GVA, accommodation shares, and compatible per-visitor/per-tourist/per-night metrics.
- [ ] Fix the SDG conditional-expression bug by selecting the food field first and then explicitly summing the accommodation and other mapped components.
- [ ] Build an auditable DTS expenditure-category → TSA product mapping. Keep fuel distinct from passenger transport and check retail expenditure versus supply valuation compatibility.
- [ ] Derive coefficients from `tourism_product_year`. Use matching-year coefficients for annual proxies by default; permit a labelled post-recovery median for scenarios as a separate configuration.
- [ ] Remove duplicated hardcoded VAI values, including unexplained transport coefficients and the blanket `other = 0.500` assumption. Export selected coefficient values, basis, source period, and statuses.
- [ ] Report mapped expenditure coverage. Do not silently treat unmapped expenditure as zero-value activity or a fully measured total; report a partial proxy or clearly labelled sensitivity assumption.
- [ ] Use identical accounting functions in SDG metrics, state diagnostics, scenario estimates, and dashboard exports.
- [ ] Export period counts, means, medians, CVs, and trends for product analysis. Preserve pre-COVID, disruption/recovery, and post-recovery comparisons.
- [ ] Keep VAI ranking descriptive; base strategic interpretation on intensity, scale, consistency, and trend. Allow accommodation to lose its top position in a valid alternative dataset.
- [ ] Investigate VAI outside expected bounds using source comparability and notes. Preserve anomalies with evidence; remove tests or narratives that assume subsidies explain them without validation.
- [ ] Label outputs as estimated tourism-attributable GVA or tourism value-added proxies. Do not imply these measure state-retained income or official product-level TDGVA.

**Acceptance:** A fixture containing only accommodation expenditure yields the expected nonzero proxy. Tests cover both food field aliases, missing categories, period selection, zero supply, and formula identities. Cross-module results agree when inputs and assumptions agree; official totals reconcile only where concepts match.

### W3 — Strengthen accommodation diagnosis

**Dependencies:** W1–W2.  
**Main files:** `src/analytics/state_diagnostics.py`, `src/ingestion/granular_dts_parser.py`, `dts_profile_parser.py`.

- [ ] Separate scale (tourists), duration (ALOS), lodging participation, and spending intensity in state diagnostic outputs.
- [ ] Treat `spend_per_night = expenditure / (tourists * ALOS)` as an aggregate constructed ratio. Flag correlations with ALOS as potentially affected by the shared denominator.
- [ ] Calculate paid-night yield only when paid nights and expenditure coverage are compatible. A share of tourists using paid lodging is not automatically a share of nights; expose an assumption-based estimate separately if needed.
- [ ] Standardize the affluence definition across granular and panel parsers. Retain literal income-band names unless an official source supports the B40/M40/T20 classification for the relevant population and year.
- [ ] Make state typology labels match the actual metric used; a spend-per-tourist threshold must not be described as spend per day.
- [ ] Use complete pairs for correlations, report sample sizes and uncertainty, and treat multiple exploratory comparisons transparently.
- [ ] Frame policy actions as hypotheses for investigation. Visitor/excursionist ratios alone do not establish congestion, environmental capacity, or the feasibility of converting VFR stays to paid lodging.

**Acceptance:** Every diagnostic records its denominator, population, period, and whether it is observed, derived, or assumption-based. Missing paid-night data produces an explicit unavailable result rather than an unsupported decomposition.

### W4 — Make network metrics and corridor classification annual

**Dependencies:** W1–W3.  
**Main files:** `src/network/corridor_network.py`, `src/ingestion/od_panel_parser.py`.

- [ ] Parameterize network calculations by year and carry year into every key and output.
- [ ] Publish separate `interstate_origin_hhi`, `all_origin_hhi`, and `intrastate_share_pct` values with matching top-feeder names/shares.
- [ ] Calculate destination inflow and origin outflow on documented populations; retain zero-flow corridors without treating them as missing.
- [ ] Return undefined concentration for no observed inbound flow rather than labelling it diversified.
- [ ] Recompute annual corridor classes using that year's flows and destination metrics. Export thresholds, comparison population, and classification rationale.
- [ ] Distinguish annual-relative thresholds from any fixed benchmark used for longitudinal comparison. Mark incomplete inputs unclassified rather than weak-value/lower-priority.
- [ ] Add the scenario disclaimer and equal-destination-yield assumption to any corridor spending proxy; do not imply observed origin-specific expenditure.

**Acceptance:** Hand-calculated fixtures verify HHI, shares, strengths, and intrastate treatment. Changes in one year's flows affect only that year's metrics. Annual classifications can change, and aggregation conserves observed flows.

### W5 — Improve panel inference and accommodation driver attribution

**Dependencies:** W1–W3.  
**Main files:** `src/analytics/panel_econometrics.py`, `accommodation_drivers_ml.py`, `state_diagnostics.py`.

- [ ] Retain the current state-effects model as a comparison; add a primary state-and-year-effects specification for descriptive within-state associations.
- [ ] Cluster panel errors by state and document small-cluster limitations. Include finite-sample correction and a suitable sensitivity assessment, such as leave-one-state-out estimates; do not treat 126 rows as 126 independent states.
- [ ] Report actual sample size, state count, years, exclusions, coefficient intervals, covariance method, and within-state fit where meaningful. Remove fixed sample labels.
- [ ] Compare full-period and defensible pre/post-recovery specifications. Document changes in sign, magnitude, uncertainty, and sample coverage without selecting the most favourable result.
- [ ] Keep nominal expenditure changes labelled nominal. Add real-spending sensitivity only with a compatible documented deflator; otherwise record the limitation.
- [ ] For repeated state-year driver data, account for state/year structure and clustered dependence. For the 16-state cross-section, keep models parsimonious and use robust errors/influence checks.
- [ ] Rename `importance_share_pct` to a precise coefficient-weight field if retained. Explain that normalized absolute standardized coefficients are neither causal contributions nor shares of expenditure or explained variance.
- [ ] Report coefficient signs, intervals, VIFs, influential observations, and stability. Fit standardization and imputation within training partitions for any predictive evaluation.
- [ ] Remove claims of ElasticNet/Ridge stability validation from docstrings unless that procedure is actually implemented and justified; additional ML is not required to complete this package.
- [ ] Generate significance labels and narratives from unrounded fitted results, with association wording and explicit uncertainty.

**Acceptance:** Reproducible model comparisons explain the ALOS sensitivity found in review. A coefficient interval crossing zero is never presented as a confirmed positive effect. A synthetic repeated-state fixture verifies design terms and sample/covariance metadata; alternative legitimate results do not fail tests.

### W6 — Correct gravity estimation, validation, and prediction scope

**Dependencies:** W1, W4–W5.  
**Main files:** `src/analytics/gravity_corridor_model.py`, `src/ingestion/od_panel_parser.py`.

- [ ] Replace squared correlation under the R² label with `1 - SSE/SST`. Report correlation separately, and handle constant targets explicitly.
- [ ] Derive sample labels from actual model inputs and report exclusions, missing-year coverage, and error metrics in their original units.
- [ ] Separate two use cases: a descriptive allocation model conditional on observed destination demand, and an out-of-time predictive model using only features available at the forecast cutoff.
- [ ] Remove current-year destination totals from forecasting features. Evaluate lagged demand/operations or other available predictors, documenting source release dates and analyst interpolation provenance.
- [ ] Use rolling year holdouts where coverage permits and a previous-year-flow baseline. Fit preprocessing within each fold; do not require an unseen target-year fixed effect to make a forecast.
- [ ] Retain zero flows and compare a transparent Poisson pseudo-maximum-likelihood specification with log-OLS instead of silently replacing zeros with arbitrary positive flows. If log-OLS remains, document zero handling and assess retransformation bias.
- [ ] Account for repeated corridor dependence in inference and document the chosen covariance structure. Treat shared origin/destination shocks as a sensitivity concern.
- [ ] Derive significance, direction, and validation status from measured results. Test any claimed pre/post structural difference directly rather than comparing point estimates alone.
- [ ] Export `(year, origin, destination)`, model version, training cutoff, predictor scope, and whether each value is fitted or held-out. Do not label a residual as proven untapped demand.

**Acceptance:** A miscalibrated prediction fixture with perfect correlation fails predictive R² appropriately. Changing held-out outcomes cannot change their forecasting features or training preprocessing. Historical predictions remain year-specific; model performance and baseline comparisons are reported even if weak.

### W7 — Correct scenario scope and destination capacity accounting

**Dependencies:** W1–W4; use W6 results only if a scenario explicitly depends on them.  
**Main files:** `src/scenarios/simulator.py`, `src/analytics/state_diagnostics.py`, `src/ingestion/mytourism_kpi_parser.py`.

- [ ] Separate corridor ALOS extension from destination-wide day-trip conversion in the API and result schema.
- [ ] Keep day-trip conversion destination-level until excursionist OD data is available. If explicit corridor allocation is offered, require labelled allocation weights and conserve the destination excursionist pool; do not infer those weights silently from overnight flows.
- [ ] Reject invalid origin/destination names, unavailable baselines, non-finite parameters, and out-of-range values. Preserve legitimate observed zero-flow cases.
- [ ] Use explicit converted-stay duration. Do not automatically apply the existing-tourist ALOS extension to newly converted tourists unless the scenario states that assumption.
- [ ] Use shared source-derived VAI and spend parameters, including baseline year, definition, status, and units.
- [ ] Convert additional tourist nights to hotel room nights using an explicit hotel-night share and guests-per-room assumption. Distinguish the aggregate spending proxy from paid-hotel-only spending assumptions.
- [ ] Aggregate additional room nights across all selected origins for a destination before assessing portfolio occupancy. Return individual contributions and the destination portfolio total.
- [ ] Use room supply and occupancy with compatible coverage and periods; choose one documented source precedence across all modules.
- [ ] Remove invented occupancy/room defaults. Return `unknown` capacity when required observations are absent.
- [ ] Treat the 80% threshold as a configurable planning assumption, distinguish it from physical capacity, and show unconstrained demand separately from any capacity-limited result. Report overflow rather than silently clamping it.
- [ ] Expose annual-average limitations and allow transparent seasonal-concentration sensitivity. Annual headroom alone must not produce an unconditional feasibility claim.
- [ ] Generate the corridor opportunity table using the same scenario functions, rather than duplicating equations.
- [ ] Include `Scenario estimate, not a causal forecast.` on single-corridor, destination, portfolio, exported, and displayed results. Provide low/base/high assumption scenarios without calling them statistical confidence intervals.

**Acceptance:** Invalid origins cannot generate spending; converting a destination pool once cannot be counted again through multiple origins. A fixture where individually feasible corridors exceed combined capacity raises a portfolio alert. Zero intervention yields zero incremental impact, and missing capacity never yields a positive feasibility assertion.

### W8 — Make clustering and radar summaries evidence-based

**Dependencies:** W1–W3.  
**Main files:** `src/analytics/state_clustering.py`.

- [ ] Keep the clustering period explicit and separate its averaged features from annual observations.
- [ ] Generate archetype descriptions and displayed figures from centroids and member states. Treat numeric cluster IDs as identifiers, not fixed policy meanings.
- [ ] Check feature redundancy and constant/missing columns before standardization. Exclude unusable features with a recorded reason.
- [ ] Assess sensitivity to reasonable cluster counts, feature subsets, and leave-one-state-out perturbations. Report unstable groupings as exploratory; retain transparent rule-based typologies as a comparison.
- [ ] Replace the RM80–300 nightly-yield clipping rule with a documented empirical or policy-supported scale. Prefer a frozen, versioned reference scale if scores are compared over time.
- [ ] Preserve raw values, scale parameters, missing values, and true zeros in exported radar data. Update consumers that replace a valid zero with a default such as `score || 50`.

**Acceptance:** Relabelling cluster IDs cannot change the meaning of an archetype. Distinct observed nightly yields remain distinguishable within the documented scale. Outputs expose the clustering/reference period and stability limitations.

### W9 — Align exported data, types, interactions, and explanations

**Dependencies:** W2–W8.  
**Main files:** `src/analytics/export_dashboard_json.py`, `dashboard/src/types.ts`, `App.tsx`, and `components/{TourismValueMonitor,AccommodationMap,CorridorNetwork,ScenarioSimulator}.tsx`.

- [ ] Populate annual baselines directly from the selected year in the validated state table. Keep clustering averages in a separately named object with period metadata.
- [ ] Join corridor classes, shares, concentration, and predictions using year-aware keys. Export historical HHI by year and preserve nulls for unavailable historical results.
- [ ] Export scenario parameters and fitted model coefficients from analytical tables/configuration; remove hardcoded VAI and gravity elasticities.
- [ ] Add schema version, source/reference years, model version, data status, missing-data reasons, and assumption metadata where applicable.
- [ ] Make TypeScript fields nullable where analytically appropriate and update every consumer. Show unavailable states without substituting plausible numbers or failing on null formatting.
- [ ] Update year filters so maps, tables, corridor cards, and comparisons use the same selected period. Clearly identify any fixed-period comparison.
- [ ] Implement scenario scope and portfolio changes in the UI. Keep frontend formulas in a reusable utility with parity fixtures generated from the Python engine; avoid embedding independent formulas in components.
- [ ] Replace coefficient-weight, HHI, capacity, GVA, and cluster descriptions with their corrected meanings. Show uncertainty where it affects interpretation.
- [ ] Preserve scope and scenario disclaimers in views and downloadable summaries. Remove claims that statistical associations establish causality, local income retention, or complete sustainability.

**Acceptance:** Exported annual baselines equal the corresponding analytical rows within display precision. A historical export cannot inherit a 2025 result without an explicit comparison label. Python/frontend scenario fixtures agree, and missing/zero values remain distinct in all four views.

### W10 — Rebuild, reconcile, and document the completed analysis

**Dependencies:** W0–W9.  
**Main files:** Proposed `src/pipeline.py`, validation modules, `README.md`, proposed `docs/analytics-methodology.md` and `docs/analytics-validation-report.md`.

- [ ] Add one documented pipeline entry point with explicit database/output paths, stage ordering, validation gates, and run metadata.
- [ ] Remove the existing dependency cycle around capacity construction reading granular room columns from enriched `state_year`: join validated base state and granular inventory inputs directly when building capacity.
- [ ] Build in temporary/staging storage, validate the complete run, then replace derived tables/files as a consistent set. Preserve raw inputs and the previous usable derived outputs if a run fails.
- [ ] Rebuild all dependent Parquet, CSV, DuckDB, and dashboard JSON outputs. Detect stale optional outputs instead of silently carrying them forward from an earlier run.
- [ ] Replace outcome-enforcing assertions with invariant tests. Keep source-specific reconciliation checks tied to a documented source release and expected coverage; do not weaken tolerances merely to obtain a pass.
- [ ] Compare old/new metrics, classifications, coefficients, uncertainty, capacity outcomes, and JSON values. Explain changes due to bug fixes separately from changes due to model assumptions or sample coverage.
- [ ] Revise README empirical claims, sample sizes, architecture inventory, model descriptions, and quickstart instructions to match regenerated evidence.
- [ ] Document unresolved source comparability questions and mark affected metrics unavailable or assumption-based. Do not substitute invented observations to achieve completeness.
- [ ] Run the documented pipeline twice and verify deterministic analytical values and schemas, excluding intentionally variable run timestamps.

**Acceptance:** A fresh run from preserved sources reproduces the dashboard data without manual database edits. Every review recommendation is linked to an implemented change and passing validation, or a documented source limitation with the affected output correctly withheld.

## 5. Planned production rebuild dependency sequence

Implement the runner around these dependencies rather than relying on the current README command order:

1. Validate source inventory; parse TSA, base state/year, granular DTS, purpose, income profile, hotel inventory, HIES, population, hotel operations, and raw OD inputs.
2. Validate and assemble canonical product/year, state/year, and OD/year tables with provenance. Assemble capacity from validated base inputs without requiring downstream diagnostics.
3. Calculate product summaries and shared economic metrics, then state accommodation diagnostics.
4. Calculate annual network strengths, HHI, and corridor classifications.
5. Estimate panel/driver models and gravity models with explicit validation splits; compute clustering and its stability diagnostics.
6. Generate scenario opportunity tables and destination portfolios from the shared engine.
7. Run analytical validation, export versioned dashboard data, run export/frontend parity checks, and publish the consistent derived output set.

## 6. Validation checklist and execution commands

Use small fixtures for formula/edge-case tests and the actual source data for integration/reconciliation. Formula expectations must be independently specified rather than copied from the implementation.

| Area | Required checks |
| --- | --- |
| Ingestion | Units, source years/statuses, observed zero vs missing, malformed headers, canonical states, duplicate keys, join cardinality, component totals where compatible. |
| Accounting | Accommodation-only proxy, all mapped components, food aliases, VAI period selection, unmapped coverage, zero denominators, no repeated tourism-ratio multiplication. |
| Temporal integrity | Correct annual baselines, year-specific shares/classes/predictions, no future predictors in forecasting, source/reference period labels. |
| Econometrics | Required effects, complete-case/sample metadata, clustered covariance metadata, intervals, influence/stability, fold-local preprocessing, alternative outcomes. |
| Gravity | Predictive R² vs correlation, constant targets, zero flows, baseline comparisons, rolling holdouts, generated significance text, fitted vs held-out labels. |
| Scenarios | Finite bounded inputs, invalid/zero/missing corridors, pool conservation, no duplicated conversions, units, aggregate capacity, unknown capacity, disclaimer. |
| Clustering | Relabel-invariant descriptions, constant features, stable reference scales, meaningful radar variation, zero/null distinction. |
| Delivery | Full rebuild, repeatability, stale-output detection, JSON contracts, Python/frontend parity, mobile/desktop and year-filter checks. |

Current regression commands, run against a configured test database after path injection is implemented:

```bash
.venv/bin/python src/validation/test_tsa_accounting.py
.venv/bin/python src/validation/test_state_and_corridors.py
```

Proposed commands to make available during implementation (the new runner and fixture suite do not exist yet):

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python -m src.pipeline --database /tmp/dosm-analytics-review/tourism_data.duckdb --output-dir /tmp/dosm-analytics-review --validate
npm --prefix dashboard run build
npm --prefix dashboard run lint
```

Document any separate frontend parity test command when its harness is implemented. Browser verification must cover all four views, year changes, state/corridor selection, scenario inputs, missing-data states, zero values, and portfolio capacity warnings.

## 7. Completion criteria

- [ ] All ten review findings have implemented corrections and targeted regression coverage.
- [ ] All four broader recommendations—shared metrics, accommodation decomposition, independent validation, and honest driver attribution—are implemented.
- [ ] Source statuses and analyst assumptions survive ingestion, modelling, export, and display.
- [ ] Accounting results, selected years, scenario coefficients, and capacity populations are consistent across Python, stored tables, and the dashboard.
- [ ] Model claims reflect actual validation and uncertainty; no prescribed winner or significance result is required for success.
- [ ] Full validation, dashboard build/lint, parity checks, and interaction checks pass, with any remaining limitations explicitly documented.
- [ ] The methodology and validation reports explain changed findings and remaining source limitations.
- [ ] Raw sources are unchanged, and a documented deterministic pipeline reproduces every derived deliverable.

## 8. Method references

- [Repository accounting and implementation requirements](../AGENTS.md)
- [Scikit-learn: predictive R² definition](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.r2_score.html)
- [Statsmodels: cluster-robust covariance](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html)

These references support the review's metric and inference corrections. Any additional methodological or source-definition decision introduced during implementation must be documented with its evidence in the methodology report.
