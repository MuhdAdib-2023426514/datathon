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

## 7. Mandatory checklist addendum: workspace, analytical claims, and publication

This addendum is part of the executable plan, not optional background. Execute **C00–C17** alongside their linked R work packages. These tasks make the additional review checklist explicit and take precedence over historical claims of completion. Inspect current code first: a fix already present still requires verification, not unnecessary reimplementation.

All tasks initially remain **OPEN**. Track them individually in `IMPLEMENTATION_STATUS.md` using the completion rules in Section 1. For each task record the implementation commit, changed files, executed checks, evidence artifact, and unresolved limitations. C17 is conditional as specified below; C00 has separate local and remote completion gates.

### C00 — Reconcile the workspace with GitHub `main`

**Order:** Capture the baseline before R01; perform remote delivery after C01–C16 and release validation.  
**Files/evidence:** Git history and working tree, `IMPLEMENTATION_STATUS.md`, proposed `artifacts/release_verification.md`.

- Inspect the configured remote, current branch, HEAD, working-tree changes, and local/remote tracking state. Fetch remote refs when access permits; do not treat a stale tracking ref as current GitHub state.
- Compare HEAD and current remote `main` using their merge base and ahead/behind commits. Inspect differences in code, README, results artifacts, and implementation status.
- Preserve existing local edits. Integrate relevant remote changes through a reviewed merge/rebase or isolated branch as appropriate; do not discard changes, overwrite unrelated work, or force-push to resolve divergence.
- Reconcile documentation against actual tested behavior, not whichever document declares the most progress.
- Prepare a reviewable implementation commit/branch and release report before any final publication step. Commit/push/merge only within the authorization of the execution session and repository rules. This document-editing request does not itself publish changes or authorize bypassing branch protection.
- When publication is authorized, push the verified branch and use the repository's supported path to `main`. If a PR or merge remains pending, report it as pending; a branch push is not completion of a `main` delivery.
- After delivery, fetch again and verify that the implementation commit is included in remote `main`, that the expected files/results match, and that required remote checks pass. Record the remote SHA and verification time. If other commits landed meanwhile, verify inclusion and relevant content rather than requiring HEAD equality blindly.

**Gate:** Local reconciliation is complete only with a documented comparison and passing validation. Remote delivery is complete only with verified inclusion in current GitHub `main`. Lack of credentials, authorization, or an unmerged PR must remain an explicit outstanding delivery item.

### C01 — Rebuild README findings from `current_results.json`

**Links:** R07, R12.  
**Files:** `src/analytics/export_dashboard_json.py`, `artifacts/current_results.json`, `dashboard/public/data/current_results.json`, `README.md`, `tests/test_results_consistency.py`.

- Derive the results contract from freshly validated analytics, then render README numerical findings from that contract using a reproducible generator or marked generated section.
- Keep explanations and limitations editable outside generated sections. Do not manually edit the JSON to reproduce preferred README claims.
- Validate the contract's schema, units, status, and data/model version. Replace brittle assertions about specific historical coefficients with comparisons against the actual current contract where appropriate.
- Include the README and matching artifacts in C00 delivery; do not push an updated README against incompatible code/results.

**Gate:** Changing a fixture result changes the generated finding; regeneration is idempotent; README and both results JSON copies agree. Record local completion separately from verified remote publication.

### C02 — Remove empirical fallbacks from state diagnostics

**Links:** R01, R09.  
**Files:** `src/analytics/state_diagnostics.py`, its exporters/consumers, `tests/test_missing_values.py` and diagnostic fixtures.

- Audit every default for observed ALOS, spending, lodging share, population, room capacity, and other empirical inputs, including `.fillna`, dictionary defaults, and truthiness expressions.
- Preserve legitimate observed zeros; propagate unavailable values and reasons. Do not invent observations to keep a recommendation or score available.
- Allow policy assumptions only in explicitly labeled scenario fields, never in observed diagnostic fields.

**Gate:** Removing each required empirical field in fixtures produces unavailable/insufficient-evidence diagnostics rather than substituted numbers. Complete-data results remain correct.

### C03 — Remove the +0.5-night scenario from opportunity ranking

**Links:** R06, R09.  
**Files:** `src/analytics/state_diagnostics.py`, `src/network/corridor_network.py`, ranking exports and consumers; locate other ranking implementations before editing.

- Trace the ranking dependency graph and remove fixed +0.5-night simulated spending/GVA from opportunity eligibility, scores, ordering, Pareto objectives, and tie-breakers.
- Build opportunity classification from documented observed indicators and transparently labeled model diagnostics. Keep model residual gaps distinct from demonstrated economic opportunities.
- Preserve +0.5 nights as a selectable scenario if useful, displayed separately after targeting. Scenario portfolio allocation is a separate, explicitly assumption-dependent decision.

**Gate:** Changing any stay-extension scenario setting cannot change the observed opportunity classification, ordering, or frontier. Tests demonstrate this invariance while showing scenario outputs change as expected.

### C04 — Restrict Pareto comparisons to complete evidence

**Links:** R01, R09.  
**Files:** Pareto/frontier computation located during C03, export contracts, corridor/map displays, `tests/test_corridor_opportunity.py`.

- Declare the exact objective set, direction of preference, units, and required fields before determining eligibility.
- Admit only candidates with finite, conceptually compatible observations for every required objective. Treat zero as valid where its domain permits it.
- Exclude incomplete candidates from comparisons and rankings without treating them as dominated. Display “Insufficient evidence” and list missing objectives.
- Retain excluded counts and coverage in the exported evidence; do not manufacture values or silently drop rows from reporting.

**Gate:** Hand-computed fixtures cover dominance, ties, zero, null, and infinity. Incomplete rows never enter the frontier or dominate complete rows. Counts reconcile across eligible, excluded, and total candidates.

### C05 — Ground assistant responses in current JSON or withdraw the claim

**Links:** R09, R11.  
**Files:** `dashboard/src/components/ImplementationRoadmap.tsx`, evidence/result JSON, related README and status claims.

- Locate response construction and remove hard-coded empirical findings from answer templates. Templates may supply phrasing, but values, entities, periods, status, and supporting evidence must come from the selected current dataset.
- Show evidence references and limitations. Unsupported questions or unavailable fields must receive a clear unsupported/unavailable response.
- Describe a deterministic lookup interface as an evidence-query tool. Do not imply a generative AI capability that is not implemented.
- If dynamic evidence cannot be delivered reliably, remove/disable the assistant feature and its unsupported capability claims while preserving the rest of the decision workflow.

**Gate:** Mutating a JSON fixture changes the corresponding answer, missing evidence produces no invented answer, and unrelated questions do not receive an apparently authoritative canned result. Claims match the implemented capability.

### C06 — Remove “zero hallucination” guarantees

**Links:** R11, R12.  
**Files:** README, status, plans, presentation material, dashboard text, assistant descriptions, and generated metadata.

- Remove affirmative guarantees such as “zero hallucination,” “hallucination-free,” and equivalent certainty claims. Use testable descriptions such as “answers use the displayed dataset and show supporting evidence.”
- Keep any necessary historical quotation explicitly identified as a withdrawn claim; instructions prohibiting the phrase are not product claims.

**Gate:** A repository text audit and rendered UI review find no active unsupported guarantee. Document the scope actually validated by C05 tests.

### C07 — Verify and correct the state-DTS publication date

**Links:** R07.  
**Files:** `data/metadata/source_registry.yaml`, exported source metadata, provenance UI, source citations in documentation.

- Verify the claimed **15 September 2026** date against the exact official DOSM state-DTS publication. Distinguish publication date from the 2025 reference year and from any national-DTS release date.
- If the official state release confirms this date, update every affected record and regenerate exports. If it contradicts the supplied date, use the evidenced official date and document the discrepancy.
- If verification is unavailable, mark the release date unverified and retain this task as pending. Do not infer authenticity from a plausible URL or silently overwrite all DTS dates.

**Gate:** Record the exact official release URL, title, supported publication date, and verification date. Registry, exported JSON, and UI agree with that evidence.

### C08 — Make source-URL and checksum claims real

**Links:** R07.  
**Files:** Source registry, provenance export/drawer, raw-input manifest, `docs/data_quality.md`, README.

- Add working official source/download URLs and computed SHA-256 values for the actual files used, with file paths, sizes, reference periods, retrieval information where known, and source identity.
- Compute checksums from bytes rather than inserting placeholder strings. Ensure claims accurately describe which artifacts contain the hashes.
- A registry-only URL is not proof of an accessible download or authentic content. Document unresolved access/provenance gaps and narrow claims accordingly.

**Gate:** Recomputing hashes matches the manifest; changing a fixture file fails verification; sampled source links resolve to the intended official release. Do not claim complete verification where coverage is partial.

### C09 — Remove Monte Carlo ALOS, RM60, and VAI defaults

**Links:** R01, R02.  
**Files:** `src/scenarios/monte_carlo.py`, exports, consumers, Monte Carlo tests.

- Explicitly search for fallback ALOS, RM60 spend-per-night, fixed VAI, and equivalent empirical defaults in all executable branches, not just the usual dataset path.
- Require empirical baselines or return insufficient evidence. Remove unused constants that imply an empirical default is supported.
- Keep user-selected policy parameters separate from empirical baselines and label them accordingly.

**Gate:** Missing each baseline independently makes the simulation unavailable with its reason. No simulated distribution is presented as evidence-based when a required empirical baseline is absent.

### C10 — Validate historical uncertainty calibration claims

**Links:** R02, R06.  
**Files:** Monte Carlo calibration, historical panel queries, uncertainty provenance exports, tests and methodology.

- Define the calibration window, exclusions, units/price basis, required sample count, dispersion estimator, bounds, and treatment of missing observations for each random parameter.
- Derive claimed empirical dispersion from the documented historical series. Distinguish spending variability, national VAI variability, and policy-assumption uncertainty.
- Do not report a parameter as sampled when it is only exported as metadata. Identify assumed dispersion explicitly where empirical calibration is unavailable, or disable that mode.
- If full calibration is deferred, withdraw the historical-calibration claim for unsupported parameters rather than retaining it in status/docs.

**Gate:** Synthetic histories with known dispersion yield expected calibration; changing historical inputs changes calibrated parameters; insufficient histories are flagged. Recorded provenance describes the distributions actually used.

### C11 — Remove optimizer distance, ALOS, and spending defaults

**Links:** R01, R04.  
**Files:** `src/scenarios/portfolio_optimizer.py`, candidate generation, frontend allocation utility, candidate exports/tests.

- Audit distance, ALOS, spend-per-night, VAI, and capacity defaults across Python and TypeScript. Specify which inputs are required for each allocation mode.
- Make candidates missing required evidence ineligible with explicit reasons. An optional display-only field may remain unavailable without unnecessarily disqualifying a valid candidate.
- Prevent custom-cost edits from bypassing backend eligibility or recreating missing observations.

**Gate:** Candidate fixtures with absent required fields remain ineligible in both precomputed and custom paths; frontend and backend eligibility agree. Real zero values receive domain-specific handling.

### C12 — Label illustrative costs and test editable overrides

**Links:** R04, R10.  
**Files:** Optimizer, scenario component/allocation utility, types, exported cost metadata and implementation model.

- Label generated campaign costs **“Illustrative cost assumption”** in candidate records, tables, summaries, and exported briefs. Expose the formula, units, and bounds.
- Allow valid user overrides in clearly stated RM units and identify them as user-supplied assumptions, not observed market prices.
- Recalculate allocation and totals using overrides; state whether the result uses a heuristic or an exact solver. Validate invalid/negative/non-finite costs and explicitly define zero-cost handling.

**Gate:** An edited cost changes the actual allocation inputs and budget totals, resetting restores the benchmark, and provenance survives export. No resulting multiple is labeled commercial profitability.

### C13 — Replace “Portfolio ROI Multiplier” terminology

**Links:** R04, R09.  
**Files:** Optimizer fields, frontend types/labels, JSON exports, README, reports, tests, implementation metadata.

- Use **“Scenario GVA-to-Cost Multiple”** for scenario potential GVA divided by assumed campaign cost. State numerator/denominator units and whether the numerator is expected or a downside objective.
- Explain that GVA is economic value added, not investor cash return, net profit, or tax receipts. Return unavailable for an undefined denominator rather than inventing a multiple.
- Migrate misleading internal `roi` fields where feasible; any temporarily retained compatibility alias must not surface as an ROI claim.

**Gate:** No active dashboard/report label describes the measure as ROI. Fixtures verify the ratio and denominator boundaries; types, JSON, and displayed labels agree.

### C14 — Verify risk-adjusted/P10 modes or remove their claims

**Links:** R04, R05.  
**Files:** Optimizer objective definitions, solver/export tiers, scenario controls, status/docs, optimizer tests.

- Specify expected-value, risk-adjusted, and P10/downside objectives mathematically, including the risk-aversion parameter and uncertainty source. Remove hard-coded percentage substitutes for unavailable risk evidence.
- Verify the selected objective reaches the allocation algorithm and every budget/threshold combination is correctly identified. Never show another mode's cached result under the selected label.
- Respect R04's distinction between summed marginal P10 scores and a joint portfolio P10; explicitly model dependence if claiming the latter.
- If a mode is not implemented and validated, remove/disable its control and retract the corresponding completion claim.

**Gate:** A controlled candidate fixture where risk preferences should change selection demonstrates that they do. Objective totals reconcile and budget/capacity gates hold in every supported mode. Tests do not require different real-data selections when objectives legitimately agree.

### C15 — Separate empirical snapshots from scientific validation

**Links:** R06, R12.  
**Files:** `tests/`, `tests/snapshot/`, pytest markers, `src/pipeline.py`, validation documentation.

- Inventory assertions requiring a particular observed sign, significance threshold, ranking, coefficient, corridor count, or model superiority. Move dataset-specific expectations into versioned snapshot/regression tests where appropriate.
- Keep formula correctness, inference implementation, leakage prevention, conservation, and domain constraints in scientific/functional validation using independent synthetic fixtures.
- Preserve scientific tests with known simulated truths; the problem is requiring a preferred empirical conclusion, not testing an estimator on controlled data.
- Update the pipeline and test reporting so snapshot success is never described as confirming an economic hypothesis.

**Gate:** A plausible revised dataset can change empirical conclusions without falsely failing method correctness. Snapshot changes receive explicit review; validation summaries distinguish snapshots, functional tests, and inferential findings.

### C16 — Withdraw the self-awarded 100/100 audit

**Links:** R12.  
**Files:** `artifacts/final_rubric_audit.md`, implementation status, README, presentation material, exported commercial metadata.

- Replace active self-certification with a dated criterion-by-criterion evidence register and outstanding limitations.
- If keeping the prior audit for history, mark it superseded and link to the verified evidence matrix; do not present its score as a current outcome.
- State that rubric readiness is an internal assessment and competition marks are determined by judges.

**Gate:** No current claim says full marks have been achieved. Every completed checklist item links to implementation and validation evidence, while incomplete external evidence remains visible.

### C17 — Add wild-cluster bootstrap sensitivity if time permits

**Links:** R06. **Priority:** P2, conditional on completion of correctness gates and continued use of headline FE inference.  
**Files:** `src/analytics/panel_econometrics.py`, model-validation artifacts, tests, `docs/model_validation.md`, headline evidence panels.

- Select and document an appropriate wild-cluster bootstrap procedure for the FE coefficient test with state-level clustering, including null restriction, weights, replication count, seed, and treatment of fixed effects.
- Validate the implementation against an established reference implementation or independently checked benchmark. Save convergence/failure information and finite-sample limitations.
- Present bootstrap sensitivity alongside the original coefficient, clustered interval/p-value, and the 16-cluster caveat. Do not select a procedure because it makes the result significant.
- If deferred, record **DEFERRED — small-cluster inference limitation remains**, keep cautious association language, and remove any claim that bootstrap validation is complete.

**Gate:** Either provide reproducible, independently checked bootstrap results and accurate UI/docs, or explicitly document deferral and retained limitations. The presence of this task does not justify claiming stronger inference before implementation.

## 8. Combined completion checklist

Use this checklist in addition to Section 5. Execute C00 baseline comparison first, integrate C01–C16 into R01–R12, resolve C17 as implemented or explicitly deferred, and finish C00 remote delivery only after validation and applicable authorization.

- [ ] C00 local/remote comparison and safe local reconciliation recorded.
- [ ] C01 README findings regenerated from validated current results.
- [ ] C02 state diagnostics empirical defaults removed.
- [ ] C03 observed opportunity ranking independent of +0.5-night scenarios.
- [ ] C04 Pareto comparisons restricted to complete compatible evidence.
- [ ] C05 evidence-query responses dynamic, or unsupported assistant claims withdrawn.
- [ ] C06 unsupported hallucination guarantees removed.
- [ ] C07 official state-DTS publication date verified and propagated.
- [ ] C08 actual source URLs and computed checksums supplied with accurate coverage claims.
- [ ] C09 Monte Carlo empirical defaults removed.
- [ ] C10 historical calibration verified, or unsupported calibration claims withdrawn.
- [ ] C11 optimizer empirical defaults removed and eligibility preserved.
- [ ] C12 illustrative editable cost behavior verified.
- [ ] C13 Scenario GVA-to-Cost Multiple terminology and formula verified.
- [ ] C14 supported risk objectives executed and tested, or unsupported modes/claims removed.
- [ ] C15 empirical snapshots separated from scientific validation.
- [ ] C16 self-awarded full-mark claims replaced with evidence.
- [ ] C17 wild-cluster sensitivity verified or explicitly deferred with limitations.
- [ ] C00 remote delivery verified on GitHub `main`, or explicitly reported pending.
