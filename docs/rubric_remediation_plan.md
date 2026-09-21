# Rubric remediation implementation plan

Date: 2026-09-21  
Product: **Malaysia Tourism Value Optimizer**  
Status: **Planned — implementation and acceptance gates remain open**

This plan addresses the code review findings in `src/` and `dashboard/src/`. It supplements `../IMPLEMENTATION_PLAN.md` and takes precedence over historical completion claims for the issues listed here. Recheck current behavior before changing it; preserve working functionality and existing user edits.

The objective is to produce evidence supporting the highest rubric band across all 25 criteria. Full marks remain a judging decision. Passing tests, adding features, or an internal score cannot guarantee them.

## 1. Baseline and completion rules

The preceding review observed 136 passing Python tests and a successful dashboard production build. Lint was blocked by a missing native `oxlint` binding. No live browser usability audit, independent source authentication, or stakeholder validation was completed in that review.

Confirmed review reproductions:

- Monte Carlo with zero reach and zero stay extension produced positive additional nights because distributions enforce positive lower bounds.
- Missing capacity produced a zero breach probability despite unavailable occupancy results.
- Parser paths still substitute zero for missing empirical cells.
- Custom-cost allocation uses a greedy selection path with invented capacity fallbacks.
- Frontend parity tests replicate TypeScript formulas in Python without executing TypeScript.

Each task starts **OPEN**. Move it to **VERIFIED** only when its acceptance gate has evidence attached. Use **IMPLEMENTED / UNVERIFIED** when code exists but validation is pending, and **EXTERNAL EVIDENCE PENDING** for adoption evidence awaiting actual participants. Never mark missing stakeholder evidence complete based on a written proposal.

Maintain a task register in `../IMPLEMENTATION_STATUS.md` with task ID, owner, status, changed files, validation command, result, evidence path, and remaining limitations. Replace unsupported blanket “100/100” or “zero fallbacks” claims with scoped, dated evidence as part of final packaging.

## 2. Execution order and responsibility

Roles below are responsibilities to assign, not people already committed to the project.

| Phase | Tasks | Priority | Responsible role | Dependency | Rough effort |
| --- | --- | --- | --- | --- | --- |
| A: Integrity | R01–R02 | P0 | Data/analytics engineer | Baseline capture | 1–2 working days |
| B: Scenario correctness | R03–R05 | P0 | Analytics + frontend engineer | A contracts | 2–3 working days |
| C: Evidence and inference | R06–R07 | P1 | Analyst + data steward | A; can overlap B | 1–2 working days |
| D: Dashboard assurance | R08–R09 | P1 | Frontend + QA | B output contracts | 1–2 working days |
| E: Adoption and presentation | R10–R12 | P1/P2 | Product/presentation lead | Verified analytical outputs | 1–2 working days plus external lead time |

Effort estimates are planning allowances, not delivery promises. Start arranging stakeholder evidence early. No additional algorithms are required to complete this plan.

## 3. Work packages and acceptance gates

### R01 — Preserve missing data and source status end to end

**Files:** `src/ingestion/tsa_parser.py`, `state_parser.py`, other ingestion parsers found by audit, `src/analytics/accounting.py`, `src/analytics/export_dashboard_json.py`, `dashboard/src/types.ts`, `tests/test_missing_values.py`.

- Inventory numeric defaults and distinguish empirical observations from explicit scenario assumptions. Review each occurrence; do not blindly replace valid observed zeros.
- Introduce/reuse a parser utility preserving observed zero, blank, suppressed, invalid, and unavailable values with status/reason metadata.
- Reuse tested accounting functions for VAI and other ratios. Missing inputs or invalid denominators must produce unavailable derived metrics, not zero or infinity.
- Preserve `e`, `p`, and `r` from the appropriate source table; do not infer all dataset statuses from one year header or the global UI badge.
- Serialize missing values as JSON `null`; reject non-standard `NaN`/`Infinity` output. Update consumers to render unavailable values explicitly.

**Gate:** Workbook fixtures with blanks, dashes, zero, invalid text, and revision flags survive ingestion → calculations → JSON correctly. Valid existing observations reconcile within documented rounding tolerance. No empirical fallback remains in the audited production paths without an explicit, justified status.

### R02 — Repair Monte Carlo boundary and unavailable-data behavior

**Files:** `src/scenarios/monte_carlo.py`, `src/scenarios/simulator.py`, `tests/test_commercial_and_monte_carlo.py`, `tests/test_scenario_engine.py`.

- Define `affected_share=0` or `delta_alos=0` as exactly zero additional nights, spend, and GVA for stay-extension scenarios.
- Validate finite inputs, allowed reach/stay bounds, positive guest density, planning thresholds, and positive integer simulation counts. Reject invalid inputs consistently across engines.
- Use a local seeded random generator. Document distribution bounds and distinguish location parameters from actual truncated-distribution means.
- Return `null` and an unavailable reason for breach probability when capacity is unknown. With zero intervention and known capacity, still report any pre-existing threshold breach correctly.
- Remove empirical VAI fallbacks. Mark assumed uncertainty parameters as assumptions when historical calibration is unavailable; never label those paths data-calibrated.
- Explain that historical variability is a sensitivity calibration, not evidence of campaign treatment effectiveness. Document independence assumptions, clipping, and whether occupancy variability is actually sampled.

**Gate:** Reproduce and eliminate the two review defects. Tests cover zero reach, zero extension, missing inventory, missing occupancy, zero observed occupancy, absent VAI, invalid inputs, and same-seed reproducibility. Quantiles are ordered and supported probabilities lie in `[0,1]`.

### R03 — Establish a coherent combined-scenario accounting contract

**Files:** `src/scenarios/simulator.py`, `dashboard/src/components/ScenarioSimulator.tsx`, `dashboard/src/types.ts`, `docs/methodology.md`, scenario fixtures.

- Separate incremental tourist nights from existing VFR nights transferred into paid lodging and from incremental commercial room nights.
- Specify mutually exclusive visitor groups or explicit overlap adjustments before adding lever results. Do not silently assume independently targeted cohorts are disjoint.
- Derive the incremental paid nights for VFR converts from baseline paid lodging and stay-extension exposure. Document how spending on already-existing nights differs from new-trip spending.
- Reconcile the spending denominator: all overnight tourist nights versus paid accommodation guest nights. Do not treat the population-average accommodation spend rate as a room rate without a stated conversion assumption.
- Make the homestay price floor/discount, campaign reach, guest density, and yield-uplift coverage explicit assumptions. Scope a price uplift to the intended covered population.
- Separate hotel and homestay capacity where compatible inventories exist; otherwise label the capacity check partial/unavailable. Retain the annual-versus-peak-period caveat.
- Use “Estimated tourism-attributable GVA” or “Tourism value-added proxy” consistently. National average VAI is a proportional scenario assumption when applied to incremental state spending.

**Gate:** Independently worked fixtures cover no intervention, each lever alone, combined levers, overlapping VFR cohorts, and capacity scope. No nights or spending are counted twice. Output definitions, units, and assumptions agree in Python, TypeScript, JSON, and documentation.

### R04 — Make custom portfolio allocation truthful and feasible

**Files:** `src/scenarios/portfolio_optimizer.py`, `src/analytics/export_dashboard_json.py`, `dashboard/src/components/ScenarioSimulator.tsx`, portfolio tests.

- Preserve the static dashboard architecture initially: retain precomputed MILP solutions and label custom-cost results **“Heuristic allocation; optimality not established.”** Remove “Optimal” from heuristic results.
- Extract custom allocation into a testable utility. Match backend eligibility, destination corridor limits, budget units, and aggregate destination-capacity constraints. Exclude candidates with missing capacity; remove fabricated rooms/occupancy and fallback risk factors.
- Validate cost overrides and define zero-cost behavior explicitly. Never select ineligible candidates because their recorded cost or demand is zero.
- For precomputed solutions, require exact budget/threshold/objective matches. If unavailable, report that state rather than silently loading another tier.
- Export solver method, status, objective, feasibility, and optimality gap where available. “Optimal” requires solver evidence.
- If exact interactive optimization is later needed, route custom inputs through the same backend MILP contract; this is an optional architecture extension, not a prerequisite for an honest prototype.
- Do not label a sum of corridor P10 values as the portfolio P10. Either describe it as a sum of downside scores or estimate a joint portfolio distribution with shared destination shocks.

**Gate:** Adversarial small fixtures demonstrate budget, eligibility, per-destination limits, and aggregated capacity conservation. Compare small MILP cases with exhaustive enumeration. Include a case where the greedy heuristic is suboptimal to verify its disclosure. Missing tiers never produce mismatched results.

### R05 — Execute actual frontend formulas and bind results to inputs

**Files:** `tests/test_scenario_parity.py`, `dashboard/src/components/ScenarioSimulator.tsx`, new `dashboard/src/lib/scenario.ts` and allocation utility, `dashboard/package.json`, shared scenario fixtures.

- Move economic formulas out of the chart component into pure TypeScript functions implementing R03.
- Select a minimal frontend test runner after checking installed tooling. Execute the production TypeScript functions against shared fixtures; compare them to Python outputs with unit-specific tolerances before display rounding.
- Keep the Python replica only if useful as an independent reference; do not claim that it tests frontend execution.
- Keep Monte Carlo benchmarks explicitly precomputed. Identify each by origin, destination, baseline year, assumptions, seed, and model/data version.
- Never substitute Selangor → Melaka for an unavailable requested corridor. Show a useful unavailable state and the supported benchmark choices.
- When policy sliders differ from a benchmark, visibly state the mismatch or disable comparison. Add live recomputation only if justified later.

**Gate:** A deliberate TypeScript formula change breaks parity tests. Fixtures include missing data and all scenario boundary cases. Selected corridor and displayed benchmark always agree; displayed assumptions describe the actual calculation.

### R06 — Strengthen method selection and inference explanations

**Files:** `src/analytics/product_value.py`, `panel_econometrics.py`, `gravity_corridor_model.py`, `docs/model_validation.md`, `docs/methodology.md`, dashboard evidence panels.

- Map each research question to its data population, method, result, uncertainty, limitation, and decision use.
- Present product VAI alongside ITC scale, post-recovery volatility, and structural trend. Treat accommodation as a tested hypothesis; explain trade-offs rather than declaring it best from VAI alone.
- Preserve COVID period separation and report sensitivity to disruption years. Keep travel-agency interpretation consistent with GVA and supply movements.
- Display the ALOS confidence interval and small-cluster caveat prominently. Leave-one-state-out sign stability is sensitivity evidence, not causal proof or a replacement for inference.
- Consider small-cluster bootstrap sensitivity if a significance claim is central to the presentation; do not pursue significance as an acceptance target.
- Remove test-outcome-mean fallbacks from holdout baselines. Estimate fallback quantities on training data only and disclose missing predictions.
- Compare PPML with previous-year flow and historical-mean baselines on identical held-out observations. Separate structural explanation from forecasting performance.
- Replace unsupported confidence badges with documented evidence-strength rules that can represent weak/insufficient evidence.

**Gate:** Changing held-out target values cannot change fitted predictions or baseline inputs. Metrics recompute from saved predictions. Every central claim includes scope and limitations; documentation acknowledges when a simpler baseline performs better.

### R07 — Verify provenance, integration, and clean reproducibility

**Files:** `data/metadata/source_registry.yaml`, `src/pipeline.py`, `src/config/paths.py`, `src/analytics/export_dashboard_json.py`, data-quality validation, provenance drawer, `docs/data_dictionary.md`.

- Verify official release/download links, publication dates, reference periods, geography, units, revision flags, workbook sheets, and raw-file hashes. Mark unverifiable entries unverified rather than inventing metadata.
- Record boundary dataset origin, version, attribution/license, and state-code joins. A hash establishes file identity, not official authenticity.
- Audit all pipeline prerequisites, including population, purpose, income, price indices, and geospatial inputs. Distinguish reproducible generated outputs from curated external inputs.
- Add safe isolated rebuild support or use an isolated writable output directory. Preserve current raw files and working data; do not delete the existing database to test reproducibility.
- Build a manifest containing input hashes, dependency versions, seed configuration, output counts, units, and validation outcomes.
- Rebuild twice from declared inputs. Compare canonical analytical content, excluding timestamps and other explicitly non-semantic metadata.

**Gate:** An isolated rebuild succeeds without relying on undeclared existing tables. State/year keys, reconciliation checks, and source statuses pass. One displayed recommendation is traced to its source cells and transformations. Two rebuilds yield equal analytical content.

### R08 — Verify interactions, accessibility, and performance

**Files:** `dashboard/src/App.tsx`, all major dashboard components, drawers, styles, `dashboard/package.json`, browser tests.

- Repair the lint installation and establish a repeatable clean dependency install with the existing lockfile strategy.
- Validate dataset schemas on load where failure could cause misleading outputs. Provide clear empty/unavailable/error states without silently substituting another selection.
- Synchronize year labels with the active animation/filter; distinguish historical flows from 2025 destination diagnostics. Validate URL parameters and browser back/forward state.
- Add drawer dialog semantics, accessible names, focus trapping/restoration, Escape handling, and keyboard access to decision-critical controls. Provide text/table equivalents where charts alone carry key evidence.
- Check widths of 360, 768, and 1440 pixels, zoom, keyboard-only use, and reduced motion. Remove implementation labels such as “Phase 26” from product flows.
- Measure load and interaction performance on a documented device/network profile. Aim for visible content within 3 seconds and ordinary local-control response within 200 ms on that profile; record exceptions and address measured bottlenecks rather than adding speculative optimizations.

**Gate:** Browser tests cover navigation, filters, deep links, reset, drawers, missing data, changed costs, unavailable benchmarks, and no uncaught errors. No clipped critical controls at tested widths. Build and lint pass; screenshots and performance measurements are saved with the tested version.

### R09 — Make recommendations concise and auditable

**Files:** `EvidenceDrawer.tsx`, `AccommodationMap.tsx`, `CorridorNetwork.tsx`, `TourismValueMonitor.tsx`, export metadata.

- Give each major visual a decision question and a plain-language interpretation generated from the selected data.
- Present recommendation, observed evidence, model evidence, assumptions, uncertainty, constraints, and next action as distinct fields.
- Make source/status badges specific to the metric. State that corridor spending uses destination averages where origin-specific expenditure is unavailable.
- Keep interstate HHI separate from all-origin HHI. Disclose classification cutoffs and test whether modest threshold changes substantially alter priority corridors.
- Preserve the distinction between economic value added, resident income, financial return, and fiscal revenue. Do not call annual hotel headroom proof of complete sustainability.

**Gate:** A reviewer can answer “where did this number come from?” for every headline result. Selected-state/corridor changes update the recommendation and its evidence together. No confidence label exceeds its documented evidential basis.

### R10 — Make the implementation model commercially testable

**Files:** `docs/implementation_model.md`, `ImplementationRoadmap.tsx`, implementation metadata; proposed `docs/pilot_validation.md`.

- Specify the first buyer, primary user, decision frequency, existing alternative, proposed pricing/procurement hypothesis, and operating responsibilities.
- Estimate hosting, data refresh, analyst review, support, onboarding, and maintenance costs with dated assumptions. Separate product operating costs from intervention campaign budgets.
- Obtain feedback from at least two intended user roles where feasible. Record actual feedback and resulting changes; no fabricated quotes or implied agency endorsement. Contact requires separate explicit user authorization.
- Confirm access to pilot measurements before claiming weekly/monthly measurement readiness. Annual DTS cannot automatically supply corridor-level weekly treatment outcomes.
- Define baseline, treatment eligibility, measurement owner, sample/coverage, consent/access arrangements where relevant, success criteria, and stop/adjust conditions.
- Evaluate proposed controls for pre-trends, spillovers, comparable measurement, and small treatment counts. Present difference-in-differences as a proposed design conditional on those assumptions, not validated causal evidence.

**Gate:** A concrete pilot brief names responsible roles, budget assumptions, data needs, measurement cadence, and evaluation limits. Stakeholder feedback and data-access commitments are attached if obtained; otherwise explicitly mark adoption validation pending.

### R11 — Align SDGs and create a coherent demonstration

**Files:** `docs/presentation_deck.md`, `docs/judge_defense.md`, `ImplementationRoadmap.tsx`, proposed decision-brief export.

- Map SDG 8.9 to economic tourism monitoring and proposed local-business participation outcomes; map 12.b to traceable monitoring. Do not claim compliance with official SDG indicator methodology without demonstrating it.
- Separate measured economic indicators from proposed future jobs, local supplier, environmental, and social measures. Include: “This prototype focuses on the economic dimension of sustainable tourism. Environmental and broader social dimensions are future extensions.”
- Build one 3–5 minute demonstration: monitor products → diagnose a state → select an existing corridor → simulate a modest intervention → inspect capacity/uncertainty → explain the pilot.
- Add a printable/exportable decision brief using existing verified data: corridor, baseline year, evidence, assumptions, potential expenditure/GVA, capacity, allocation method, cost assumptions, version, limitations, and mandatory scenario disclaimer.
- Document original project contributions and reused libraries/data/assets with attribution. Keep the evidence-query assistant clearly described according to its actual capabilities.

**Gate:** A fresh reviewer can explain the decision, evidence, uncertainty, and implementation after the demonstration. Exported figures match the active verified scenario or explicitly identified fixed benchmark. All monetary units and statuses are visible.

### R12 — Close the evidence register and package a release candidate

- Update README, implementation status, results artifacts, and any earlier audit report to agree with verified behavior. Preserve historical context while withdrawing unsupported completion claims.
- Record tests actually executed, failures, environment limitations, source verification status, and external evidence still pending.
- Produce `artifacts/rubric_evidence_matrix.md` linking all rubric criteria below to evidence, tested version, and remaining gaps.
- Rehearse missing-data and unavailable-benchmark paths as well as the main demonstration. Include a static demonstration backup generated from the same verified artifacts.

**Gate:** All P0 tasks verified; no unresolved defect that fabricates data or misrepresents a calculation; release checks pass; every criterion has evidence or an explicit limitation. Replace numerical self-certification with “ready for judging against attached evidence.”

## 4. Coverage of all 25 rubric criteria

| ID | Criterion | Work packages | Evidence required |
| --- | --- | --- | --- |
| M1 | Clear, relevant, significant problem | R06, R11 | One problem statement supported by sourced observations |
| M2 | Focused competition-aligned scope | R06, R11 | Research-question map and explicit economic scope |
| M3 | Appropriate analytical methods | R02–R06 | Formula contracts, validation, baselines, inference limits |
| M4 | Relevant SDG alignment | R11 | Target-to-indicator mapping with measured/proposed distinction |
| M5 | Logical evidence-based explanation | R06, R09 | Traceable claim-to-evidence briefs |
| D1 | Official authentic sources | R07 | Verified publications/downloads, source lineage, attribution |
| D2 | Accurate, current, relevant data | R01, R07 | Reference/release dates, status, reconciliation, freshness caveats |
| D3 | Combine diverse data types | R07, R09 | Structured tables plus geospatial joins; no decorative unstructured data |
| D4 | Integration creates new insights | R06, R09 | Corridor decision requiring flow, yield, and capacity together |
| D5 | Handle data without compromising integrity | R01–R07 | Missing-data fixtures, leakage checks, reproducible transformations |
| O1 | Clear organized user-friendly output | R08, R09 | Tested decision workflow and reviewer feedback |
| O2 | Functional interactive responsive product | R05, R08 | Frontend execution tests and browser/device evidence |
| O3 | Accurate relevant displays | R05, R09 | Executed parity fixtures and selected-context consistency |
| O4 | Professional visual presentation | R08, R11 | Desktop/mobile screenshots and readability checks |
| O5 | Original creative product | R11 | Contribution/attribution record and working decision brief |
| B1 | Real-world applicability | R10 | Named use case, operational workflow, user feedback |
| B2 | Commercial value/marketability | R10 | Buyer hypothesis, alternatives, operating-cost/pricing assumptions |
| B3 | Societal/economic benefit | R03, R10, R11 | Measured baseline and proposed beneficiary outcomes without guarantees |
| B4 | Expansion potential | R07, R10 | Refresh ownership, modular architecture, staged expansion prerequisites |
| B5 | Clear implementation model | R10 | Pilot responsibilities, budget, measurements, evaluation plan |
| C1 | Creative analytical approach | R04, R06 | Justified corridor targeting and capacity-aware allocation |
| C2 | Technology/data science/geospatial innovation | R05, R09 | Functioning map-to-scenario evidence workflow |
| C3 | Clear structured distinctive concept | R11 | Volume-to-value story connecting research to decisions |
| C4 | Effective impactful presentation | R11 | Timed rehearsal and fresh-reviewer comprehension |
| C5 | Additional wow factor | R04, R11 | Trustworthy budget comparison and exportable decision brief |

## 5. Validation and release checklist

Run targeted tests during implementation. At integration freeze, run once against the final candidate:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python src/pipeline.py --stage validate
```

From `dashboard/`:

```bash
npm run build
npm run lint
```

R05 and R08 must add documented frontend unit and browser-test commands to `dashboard/package.json`; do not report those checks as available before implementation. Run the isolated full rebuild introduced in R07 separately from validation against existing artifacts.

- [ ] R01–R05 correctness gates verified with executed tests.
- [ ] R06 claims and method selection reviewed against actual model outputs.
- [ ] R07 source audit and isolated deterministic rebuild recorded.
- [ ] R08–R09 browser, accessibility, and context consistency checks complete.
- [ ] R10 adoption evidence obtained or explicitly marked pending.
- [ ] R11 demonstration and exported brief verified.
- [ ] R12 evidence matrix complete and historical claims reconciled.

## 6. Three-day contingency

If only three days are available, reduce feature scope rather than weakening correctness.

- **Day 1:** R01–R02 and the core R03 accounting contract; verify the two reproduced failures are fixed.
- **Day 2:** R04–R05; retain clearly labeled fixed Monte Carlo benchmarks and heuristic custom allocations. Disable combined levers or result modes whose correctness cannot be established.
- **Day 3:** Run critical R06–R09 checks, repair claims, and rehearse R11 with one verified corridor. Produce the evidence matrix and describe R10 as a proposed pilot wherever external validation is absent.

Defer live solver infrastructure, new models, extra animation, and expanded assistants. Outstanding source, correctness, or adoption gaps remain visible; the contingency does not establish full rubric coverage by itself.
