# Accommodation Map UI, UX, and Data Storytelling Implementation Plan

Status: Proposed implementation; no application changes made by this plan.

## 1. Objective

Help a policymaker answer: **Where could existing tourism demand support more accommodation value, and what should we investigate or test next?**

The page should follow this sequence:

**Find a state → compare performance → inspect evidence → explore corridors or test a scenario.**

Prioritise analytical credibility, clear comparisons, and useful next actions. Preserve the existing React, ECharts, Tailwind, and application navigation patterns without introducing new dependencies unless a demonstrated need emerges.

## 2. Scope and guardrails

- Primary component: `dashboard/src/components/AccommodationMap.tsx`.
- Supporting integration: `dashboard/src/App.tsx`, `CorridorNetwork.tsx`, shared types, comparison utilities, and dashboard tests.
- Reuse the existing `stateMedian` helper and its tests.
- Preserve ongoing workspace changes; review the current diff before implementation.
- Keep this view explicitly tied to its available 2025 baseline. Do not relabel `baseline_2025` as another selected year.
- Distinguish observed statistics, derived proxies, hypotheses, and proposed interventions.
- Do not infer environmental carrying capacity, causal effects, or origin-specific spending from state-level economic indicators.
- Preserve source units, missing values, and available estimate/preliminary/revision statuses.
- Show: “This prototype focuses on the economic dimension of sustainable tourism. Environmental and broader social dimensions are future extensions.”
- Scenario outputs must display: **“Scenario estimate, not a causal forecast.”**

## 3. Review findings to address

| Priority | Finding | Required outcome |
| --- | --- | --- |
| P0 | Hardcoded yield medians disagree with bundled data | One shared, data-derived benchmark source |
| P0 | Recommendations and confidence badges overstate evidence | Separate observations, hypotheses, and actions to test |
| P0 | Occupancy threshold gap is labelled room capacity | Correct percentage-point label and explicit assumption |
| P0 | Missing yield becomes zero | Missing data remains unavailable throughout the UI and exports |
| P1 | Eight indicators and multiple filter pills compete for attention | Three primary metrics with progressive disclosure |
| P1 | Map filters only dim states without explaining selection behaviour | Visible match count, criteria, and selection status |
| P1 | Selected map fill replaces the metric colour | Selection outline preserves quantitative encoding |
| P1 | Driver percentage bars multiply values by three | Bar lengths accurately represent their stated scale |
| P1 | State exploration does not lead directly into other decision views | Destination-aware corridor and simulator actions |
| P1 | Modal and toggle semantics are incomplete | Keyboard-accessible controls and brief dialog |

Review-time values from `dashboard/public/data/state_profiles.json`: median ALOS **2.505 days**, median accommodation spend/night **RM43.70**, and median TVAY **RM109.70**. These are audit references, not constants to embed in production. The existing RM58 TVAY threshold classifies every observed state as high yield in this snapshot.

## 4. Phase 1 — Correct the analytical story

### Implementation

1. Extract `computeStateDecisionSummary` into a pure utility such as `dashboard/src/lib/stateDecisionSummary.ts`.
2. Build benchmarks from finite, observed state values using `stateMedian`; keep genuine zero observations.
3. Use the same benchmark object for the summary, metric cards, comparison bars, tooltips, and exported brief.
4. Label benchmarks “Unweighted median across available states and federal territories.” Display the observation count. Keep benchmarks independent of focus filters.
5. Distinguish statistical medians from illustrative policy thresholds. Define equality as “at the median”; do not describe equality as above or below.
6. Avoid silently substituting spend/night for missing TVAY when assigning the same classification. Return an insufficient-data state or explicitly identify a separate fallback rule and indicator.
7. Restructure the summary into:
   - **Observed performance:** values and differences from benchmarks.
   - **Possible explanation:** qualified hypotheses, supported by relevant lodging or purpose data when available.
   - **Action to test:** a proposed intervention, without promised impact.
8. Remove universal “High confidence” labels. Show source coverage, derived-proxy status, and limitations instead. Use a confidence score only if a defensible assessment method is implemented.
9. Rename `headroom` to an explicit occupancy-threshold gap. Display `max(0, threshold − annual occupancy)` in percentage points; handle occupancy above the threshold with an explicit status. State that the 80% threshold is illustrative and does not measure available rooms or seasonal capacity.
10. Replace missing-value-to-zero conversions in yield and radar data. If radar inputs are incomplete, explain the incomplete profile rather than plotting fabricated zero scores.
11. Preserve metric meaning: distinguish visitor-day, tourist-night, ALOS days, accommodation spending, and value-added proxies. Confirm denominator definitions against exporter metadata before revising labels.

### Acceptance criteria

- Changing the input dataset updates benchmarks and classifications consistently.
- Missing or invalid inputs cannot produce a confident diagnosis, zero-valued yield, or a rendering exception.
- Short stays alone do not establish day-trip transit behaviour; long stays and low yield alone do not establish unpaid lodging usage.
- Annual occupancy does not trigger claims of demonstrated weekend or environmental pressure.
- The rendered brief and Markdown export use the same summary and definitions.

## 5. Phase 2 — Simplify the page hierarchy

### Proposed layout

```text
Accommodation Opportunity Map                     2025 baseline
Where could existing demand support more accommodation value?

[Stay duration] [Accommodation share] [Spend per night] [More indicators]
[Focus: All states and federal territories] [Matching count and criteria]

Desktop: Map and comparisons      | Selected-state insight
                                 | Three benchmarked metrics
                                 | Evidence and an action to test
                                 | Explore corridors / Test scenario

Expandable details: Lodging and capacity / Demographics / Model evidence
Secondary action: Export state brief
```

### Implementation

- Keep accommodation share as the initial metric to preserve current behaviour; make all three primary options equally discoverable.
- Move TVAY, TEY, GVA intensity, tourism intensity, and archetype into “More indicators.” Explain acronyms and label proxies clearly.
- Lead the state panel with one data-derived sentence and three values: ALOS, accommodation share, and accommodation spend/night.
- Add signed differences from the shared benchmark with correct units: days, percentage points, and RM/night. Avoid implying that every larger value is inherently better.
- Keep visitor/tourist volume available as context for opportunity scale. Do not rank intervention priorities by yield alone.
- Reduce repeated badges and nested cards. Increase essential labels from 9–11px to a readable project-consistent size.
- Place the selected-state insight immediately after the map on mobile, before extended comparisons and evidence.
- Move radar, demographics, and model diagnostics into expandable sections. Retain the radar only if its normalisation and decision purpose are clear; favour existing benchmark bars for direct comparisons.

### Acceptance criteria

- A reader can identify the selected state's performance, evidence, and next action without opening advanced sections.
- All three primary metrics explain their units and denominator.
- Desktop and mobile reading order follows the same decision sequence.
- There is no horizontal page overflow at a 390px viewport.

## 6. Phase 3 — Make map interactions interpretable

### Implementation

- Consolidate filter labels, predicates, and descriptions into shared definitions so displayed criteria match actual logic, including OR conditions.
- Rename filters as economic focus areas; do not imply measured sustainability or carrying capacity.
- Treat filters explicitly as highlighting: show “X of 16 match; other states are dimmed.” Keep the selected state stable and flag when it falls outside the focus.
- Provide a clear focus-reset action and a descriptive no-match state.
- Preserve metric fills on selected polygons; indicate selection with a contrasting border and label.
- Format tooltip values consistently and show meaningful numeric legend endpoints with units.
- Review fixed colour ranges for clipping. Derive suitable ranges from observed values or document intentional fixed ranges and show out-of-range values clearly.
- Show missing observations with a neutral fill and an “Unavailable” legend entry.
- Retain the state dropdown and zoom reset for small territories and keyboard users; add a compact textual value list if needed to make national comparisons available without hover.
- Guard map rendering until registration is ready and provide explicit states for empty profiles, missing geography, and unavailable diagnostics.

### Acceptance criteria

- Switching metric, focus, or state leaves map and detail panel consistent.
- Selected states retain their quantitative colour meaning.
- The focus count and description exactly match the highlighted states.
- Every state is selectable without clicking a polygon.
- Missing data is visually distinct from low values.

## 7. Phase 4 — Connect diagnosis to action

### Implementation

- Add callbacks from the map for “Explore inbound corridors” and “Test a stay-extension scenario.”
- Reuse `App.tsx` navigation and `handleSelectCorridorForScenario` where appropriate.
- Add destination initialisation/synchronisation to `CorridorNetwork`; its current destination filter is local state. Ensure revisiting the mounted view also respects navigation intent.
- Preserve destination in existing URL parameters and initialise the map selection from shared state or URL context.
- When opening the simulator without an origin, use its supported destination-level behaviour or require an origin choice. Do not invent an origin-specific assumption.
- Respect the fixed map baseline when linking to year-sensitive views; explicitly communicate any baseline mismatch.
- Keep the brief as a secondary action and update both dossier and Markdown wording together.

### Acceptance criteria

- Selecting a state and opening corridors preselects that destination.
- Opening a scenario carries the intended state and supported baseline context.
- Returning to the map preserves the selected state.
- Shareable URLs restore destination context using existing application conventions.
- Every displayed scenario estimate includes the required disclaimer.

## 8. Phase 5 — Accessibility and model evidence

### Implementation

- Give metric and focus buttons `aria-pressed` or an appropriate single-selection control pattern, descriptive IDs, and visible focus treatment.
- Implement proper tab semantics and keyboard behaviour if the diagnostic switch remains a tab interface.
- Implement the brief with dialog semantics, labelled title, initial focus, focus containment, Escape dismissal, focus restoration, and an accessible close-button name.
- Verify essential text contrast and touch-target spacing. Respect reduced-motion preferences and remove the pulsing baseline indicator, which can imply live data.
- Rename model attribution to “Factors associated with accommodation spending” after confirming the actual model outcome and units.
- Replace tripled driver-bar widths with actual percentages. Document how importance is calculated; do not portray coefficient-derived shares as causal contributions or variance explained.
- Read sample size and model details from metadata rather than hardcoding them. Keep technical statistics in expandable methodology content.
- Ensure source/proxy badges remain distinct from claims about recommendation confidence.
- Verify print output includes the full brief without the modal overlay or scroll clipping. Surface clipboard/download failures clearly.

### Acceptance criteria

- Keyboard users can operate selection controls and open, use, and close the brief without losing focus.
- Driver bar lengths match their displayed percentages.
- Model descriptions distinguish association from causation and state-level observations from model-wide findings.
- Printed, copied, and downloaded briefs preserve definitions, baseline year, and limitations.

## 9. Suggested code organisation

Adapt these boundaries to existing components rather than creating abstractions solely to reduce file length.

| File or area | Responsibility |
| --- | --- |
| `AccommodationMap.tsx` | Selection state, layout, and navigation callbacks |
| `lib/stateComparison.ts` | Shared observed-value benchmarks |
| `lib/stateDecisionSummary.ts` | Tested observations, hypotheses, and recommendation rules |
| Accommodation metric configuration | Typed labels, units, getters, formatting, and legend rules |
| State map component | ECharts options, geography readiness, selection, and highlighting |
| State summary component | Insight, comparison values, evidence, and next actions |
| State evidence component | Lodging, demographic, and model detail |
| State brief component and formatter | Accessible dialog and shared export content |

Use existing `StateProfile` contracts and suitable ECharts/GeoJSON types. Replace local `any` casts where the refactor touches them. Keep production analytical formulas outside chart components and cover them with focused tests.

## 10. Validation plan

### Automated checks

- Extend existing Node tests for benchmarks: odd/even samples, real zero, missing/non-finite values, and all-missing input.
- Test decision rules with synthetic fixtures covering all comparison combinations, exact equality, missing TVAY, and absent lodging/occupancy data.
- Test percentage-point threshold-gap calculations below, at, and above the illustrative threshold.
- Test filter predicates and counts against their displayed definitions.
- Verify summary/export parity for units, baseline year, missing values, and qualified claims.
- Update the dashboard test command to include relevant new tests and the existing `stateComparison.test.ts`; currently `npm test` runs only `tests/scenario.test.ts`.
- Run dashboard tests, `npm run build`, and `npm run lint`. Investigate failures against the existing workspace state rather than overwriting unrelated changes.
- If exporter contracts change, also run the relevant Python dashboard-integrity tests and rebuild affected artifacts deterministically. A UI-only refactor should not require rewriting source data.

### Browser checks

Check 390px mobile, 1280px laptop, and 1440px desktop layouts:

- Select states through map and dropdown, including small territories.
- Change every primary metric and open additional indicators.
- Apply a focus that excludes the selected state; verify the explanation and reset behaviour.
- Inspect missing-data and empty-data cases.
- Navigate to corridors and simulator; verify destination and baseline context.
- Open, keyboard-navigate, dismiss, print, copy, and download the brief.
- Check readable legends, essential text contrast, visible focus, and absence of clipped content.

Record which checks were actually run and any remaining limitations; do not describe code inspection as browser verification.

## 11. Delivery order and completion criteria

1. **Correctness:** shared benchmarks, honest recommendations, missing-data handling, occupancy units, and truthful driver scales.
2. **Core experience:** simpler metrics, concise state summary, consistent highlighting, and readable mobile ordering.
3. **Decision flow:** destination-aware navigation, shared selection context, and export parity.
4. **Verification:** accessibility, interaction, build, lint, and analytical rule tests.

The work is complete when a user can select a state, understand its performance relative to a correctly labelled benchmark, distinguish observations from hypotheses, and carry the state into corridor exploration or a transparent scenario—with consistent values and terminology across the map, detail panel, and brief.
