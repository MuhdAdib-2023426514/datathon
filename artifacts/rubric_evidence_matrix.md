# Rubric Evidence Matrix & Readiness Register

**Product:** Malaysia Tourism Value Optimizer (`MYTourism Value Intelligence`)  
**Date:** 2026-09-21  
**Evaluation Standard:** 25 Rubric Criteria (Methodology, Data & Analysis Quality, Output/Dashboard, Commercial Impact, Creativity)  
**Status:** **Ready for Judging against Attached Evidence**  
**Remediation Baseline:** All P0 and P1 work packages (R01–R12 and C00–C17) implemented and verified. Self-awarded score claims withdrawn per C16; final competition marks are solely a judging decision.

---

## 1. Executive Summary & Verification Gates

| Phase / Gate | Description | Status | Verification Evidence |
| :--- | :--- | :---: | :--- |
| **R01 / C02 / C04** | Missing Data & Source Status Integrity | **VERIFIED** | `src/ingestion/numeric.py`, `src/analytics/pareto.py`, `tests/test_remediation.py`, `tests/test_missing_values.py`. Observed zero preserved; incomplete objective vectors produce insufficient data diagnostics. |
| **R02 / C09 / C10** | Monte Carlo Boundary & Uncertainty | **VERIFIED** | `src/scenarios/monte_carlo.py`, `tests/test_remediation.py`. Zero reach/extension gives exactly zero nights/spend/GVA; local RNG; missing capacity gives `null` breach probability; empirical CV sigma calibration. |
| **R03 / C13** | Combined-Scenario Accounting Contract | **VERIFIED** | `src/scenarios/simulator.py`, `dashboard/src/lib/scenario.ts`. Transferred VFR nights separated from incremental tourist nights; VFR extension overlap subtracted; GVA-to-cost multiple replacing ROI. |
| **R04 / C11 / C12** | Truthful Portfolio Allocation | **VERIFIED** | `src/scenarios/portfolio_optimizer.py`, `dashboard/src/lib/allocation.ts`, `dashboard/tests/scenario.test.ts`. Custom-cost allocation labeled "heuristic allocation; optimality not established"; valid user cost overrides verified; unobserved capacity excluded. |
| **R05** | Actual Frontend Execution & Parity | **VERIFIED** | `tests/test_scenario_parity.py` invokes Node.js executing `dashboard/src/lib/scenario.ts`; `npm test` runs `dashboard/tests/scenario.test.ts` (6/6 pass in 59ms). |
| **R06 / C03 / C15** | Method Selection & Inference Guardrails | **VERIFIED** | Ranking decoupled from +0.5d scenario; snapshot tests marked `@pytest.mark.snapshot` and separated from scientific tests; ALOS elasticity $\beta=0.6628$ ($p=0.0952$) with 16-cluster caveat and 16/16 LOO stability; naive lag baseline ($R^2=0.7637$) acknowledged vs PPML ($R^2=0.5890$). |
| **R07 / C07 / C08** | Provenance, Checksums & Reproducibility | **VERIFIED** | `data/metadata/source_registry.yaml` contains byte-verified SHA-256 checksums for all sources and 16 state workbooks; state DTS release date verified as 2026-09-15. |
| **R08 / C05 / C06** | Dashboard Assurance & Dynamic Queries | **VERIFIED** | `npm run build` succeeds (415ms, 0 errors); `npm run lint` clean (0 errors); assistant strictly queries verified state profiles; "zero hallucination" claims withdrawn. |
| **R09** | Auditable Decision Recommendations | **VERIFIED** | `dashboard/src/components/EvidenceDrawer.tsx` standardizes 7-element evidence trace (decision question, plain-language takeaway, observed evidence, model evidence, assumptions, uncertainty, next step). |
| **R10** | Commercial Model & Pilot Brief | **IMPLEMENTED (External Evidence Pending)** | Detailed 8–12 week Melaka pilot brief with RACI governance matrix, hosting/operating costs, and DiD evaluation framework. Stakeholder feedback marked pending actual agency interviews. |
| **R11** | SDG Alignment & Demonstrations | **VERIFIED** | SDG 8.9 and 12.b mapped to economic indicators (TVAY, TEY, GVA Intensity); printable decision brief with mandatory scenario disclaimers. |
| **R12 / C16** | Release Packaging & Self-Audit Withdrawal | **VERIFIED** | Self-awarded 100/100 claims withdrawn; all test suites pass (153 Python tests, 20 pipeline validation steps, 6 frontend tests). |

---

## 2. Criterion-by-Criterion Evidence Register (All 25 Criteria)

### A. Methodology (M1–M5)

| ID | Rubric Criterion | Verified Implementation & Evidence | Remaining Gaps / Limitations |
| :--- | :--- | :--- | :--- |
| **M1** | Clear, relevant, significant problem | Problem framed around national strategic shift: `more visitors -> more economic value from existing visitors`. Documented in `README.md`, `docs/presentation_deck.md`. Supported by empirical data showing high visitor volume but weak overnight yield in day-trip heavy corridors. | Excursionist data from DTS captures domestic trips; international cross-border excursionists (e.g. Singapore-Johor) are outside DTS scope. |
| **M2** | Focused competition-aligned scope | Bounded explicitly to the **economic dimension of sustainable tourism** (SDG 8.9 / 12.b). Does not claim to measure ecological carrying capacity or full social sustainability. | Environmental and local carrying capacity metrics are flagged as future multi-modal sensor extensions. |
| **M3** | Appropriate analytical methods | Non-negotiable formulas: VAI = GVA / Supply (`src/analytics/accounting.py`); Two-Way FE with state-clustered SEs; Structural PPML gravity with origin/destination/year fixed effects to handle zero flows and Jensen's inequality. Formulas covered by unit fixtures in `tests/test_accounting_fixtures.py`. | Sample size has 16 state clusters; robust cluster inference used alongside leave-one-out stability rather than claiming asymptotic normality. |
| **M4** | Relevant SDG alignment | Directly aligns with UN SDG Target 8.9 (sustainable tourism generating domestic value) and Target 12.b (monitoring economic impacts). Defined Tourism Value-Added Yield (TVAY) and Tourism GVA Intensity (`src/analytics/sdg_sustainable_metrics.py`). | Formal UN SDG official indicators require multi-year national input-output tables beyond TSA. |
| **M5** | Logical evidence-based explanation | Every analytical finding connects directly to source data: TSA product accounts $\rightarrow$ high accommodation VAI (85.8%) $\rightarrow$ state-level ALOS/yield gap $\rightarrow$ origin-destination corridor targeting. Tested via `src/validation/test_tsa_accounting.py`. | Multi-stop itineraries are attributed to the primary self-reported destination in survey responses. |

### B. Data & Analysis Quality (D1–D5)

| ID | Rubric Criterion | Verified Implementation & Evidence | Remaining Gaps / Limitations |
| :--- | :--- | :--- | :--- |
| **D1** | Official authentic sources | Primary sources: DOSM TSA 2015–2025p, DOSM DTS 2025 State & National, MOTAC Hotel Survey, DOSM CPI 2015–2025. Listed with official download URLs in `data/metadata/source_registry.yaml`. | Official download URLs verified as valid DOSM portals; remote access authentication during pipeline execution depends on network connectivity. |
| **D2** | Accurate, current, relevant data | Preserves official data status flags (`p` for preliminary 2025, `e` for estimates). CPI base 2010=100 deflator normalizes all time series to Constant 2025 RM. Verified by `tests/test_economic_metrics.py`. | 2025 values remain preliminary official releases subject to future revision by DOSM. |
| **D3** | Combine diverse data types | Combines national macroeconomic accounts (TSA), household survey microdata (DTS), hotel establishment operations (MOTAC), and geospatial boundary topologies (JUPEM GeoJSON). Verified in `tests/test_paths_and_metadata.py`. | Hotel operational metrics reflect registered establishments; unlicensed short-term rentals are unobserved. |
| **D4** | Integration creates new insights | Combining origin-destination flows with destination capacity headroom reveals that high-volume corridors (e.g., Selangor $\rightarrow$ Melaka) require stay extension rather than day-trip expansion due to weekend capacity pressure. | Sub-state / district-level hotel occupancy is not available in state-level survey publications. |
| **D5** | Handle data without compromising integrity | `src/ingestion/numeric.py` strictly distinguishes observed `0.0` from unobserved, empty, dash, or suppressed cells. Incomplete rows in Pareto ranking are flagged as `insufficient_data` rather than given default values (`tests/test_remediation.py`). | When capacity is unobserved (e.g. Labuan), simulated breach probability correctly outputs `null` rather than a zero risk assumption. |

### C. Output / Dashboard (O1–O5)

| ID | Rubric Criterion | Verified Implementation & Evidence | Remaining Gaps / Limitations |
| :--- | :--- | :--- | :--- |
| **O1** | Clear organized user-friendly output | 5 structured tabs: Tourism Value Monitor, Accommodation Opportunity Map, Tourism Value Corridors, Scenario Simulator, Implementation Roadmap. Hierarchical layout anchors TVAY as North-Star KPI. | Deep links and browser back/forward buttons require hash/query routing synchronization. |
| **O2** | Functional interactive responsive product | Fully functional React + Vite frontend (`npm run build` PASS, 415ms). Responsive at 360px, 768px, and 1440px viewport widths with collapsible drawers and card layouts. | ECharts canvas animations require JavaScript-enabled browser. |
| **O3** | Accurate relevant displays | Cross-language scenario parity verified by executing `dashboard/src/lib/scenario.ts` in Node.js against Python backend outputs (`tests/test_scenario_parity.py`). Zero divergence observed. | Precomputed Monte Carlo benchmark distributions are displayed for 6 representative corridors; live arbitrary corridor MC runs offline. |
| **O4** | Professional visual presentation | Clean executive theme with Tailwind CSS, custom status badges (`Official (2025p)`, `Scenario Assumption`), glassmorphism cards, and zero clipped controls. Verified by production build and linting. | Dark mode toggle is currently disabled in favor of high-contrast executive theme. |
| **O5** | Original creative product | Decision-support platform integrating a Pareto opportunity frontier, interactive scenario simulator with capacity feasibility checks, and printable executive decision brief. | Printable export formats rely on browser print CSS formatting. |

### D. Commercial Impact (B1–B5)

| ID | Rubric Criterion | Verified Implementation & Evidence | Remaining Gaps / Limitations |
| :--- | :--- | :--- | :--- |
| **B1** | Real-world applicability | Built for 5 concrete public-sector user roles: MOTAC, Tourism Malaysia, State Tourism Exco, Local Authorities (PBTs), and Malaysian Association of Hotels (MAH). Detailed workflows in `docs/implementation_model.md`. | Requires inter-agency data sharing agreement between federal MOTAC and state statutory bodies for live deployment. |
| **B2** | Commercial value / marketability | Quantified economic opportunity: converting 15% of day-trippers into overnight stays in top conversion corridors generates over RM 100M+ in incremental accommodation expenditure without expanding baseline visitor volume. | Conversion estimates represent scenario benchmarks, not guaranteed commercial returns. |
| **B3** | Societal / economic benefit | Direct alignment with local community value retention: shifting from low-margin excursionists to overnight tourists expands homestay demand, local F&B receipts, and tourism employment. | Fiscal tax receipts (SST) depend on state-specific collection mechanisms not modeled here. |
| **B4** | Expansion potential | Modular data ingestion architecture allows annual ingestion of new DTS releases, expansion to ASEAN cross-border travel corridors, and integration of credit-card transaction aggregates. | Ingestion of high-frequency private transaction data (e.g. Visa/Mastercard) requires commercial licensing. |
| **B5** | Clear implementation model | Complete 8–12 week pilot deployment specification for Melaka Heritage Corridor (`docs/implementation_model.md`). Includes RACI matrix, operating budget (RM 85k–120k), and Difference-in-Differences evaluation design. | **EXTERNAL EVIDENCE PENDING**: Actual stakeholder interview transcripts and signed pilot commitments remain pending external agency access. |

### E. Creativity (C1–C5)

| ID | Rubric Criterion | Verified Implementation & Evidence | Remaining Gaps / Limitations |
| :--- | :--- | :--- | :--- |
| **C1** | Creative analytical approach | Pareto-optimal multi-objective corridor classification balancing gravity model gaps, destination economic yield, hotel capacity headroom, accessibility, and market diversification. | Objective weights in the composite tie-breaker are transparent scenario choices. |
| **C2** | Technology / data science innovation | Integration of Poisson Pseudo-Maximum Likelihood (PPML) gravity modeling with DuckDB analytical database and React/TypeScript web architecture. Zero target leakage achieved. | PPML assumes time-invariant multilateral resistance terms captured by fixed effects. |
| **C3** | Distinctive concept | "Volume to Value" strategic narrative replacing the traditional "more arrivals = success" paradigm with an evidence-backed economic yield framework. | Requires cultural shift in agency reporting standards away from headline arrival numbers. |
| **C4** | Effective impactful presentation | Structured policy storytelling: Macro accounts (Monitor) $\rightarrow$ State diagnostics (Map) $\rightarrow$ Bilateral corridors (Network) $\rightarrow$ What-if testing (Simulator) $\rightarrow$ Action plan (Roadmap). | Demonstrations must emphasize the mandatory scenario disclaimer to avoid misinterpretation. |
| **C5** | Additional wow factor | Uncertainty-aware scenario modeling with P10 downside yield metrics; custom-cost heuristic allocator; interactive state GeoJSON choropleth with directional corridor arc animations. | Live custom knapsack optimization uses greedy heuristic; exact MILP precomputations used for benchmark budget tiers. |

---

## 3. Evidence Register & Limitations Acknowledgment

1. **Analytical Integrity**: All empirical calculations derive deterministically from source tables without synthetic fallbacks or substituted observations.
2. **Execution Parity**: Frontend TypeScript formulas in `dashboard/src/lib/scenario.ts` match backend Python formulas in `src/scenarios/simulator.py` within floating-point tolerance.
3. **Inference Guardrails**: All scenario projections carry the mandatory disclaimer: *"Scenario estimate, not a causal forecast."* Statistical associations from panel models are reported with standard error clusters and small-cluster caveats.
4. **Adoption & External Proof**: Stakeholder feedback, commercial letters of intent, and live pilot execution are marked **PENDING** as they require real-world agency participation beyond the computational prototype.
