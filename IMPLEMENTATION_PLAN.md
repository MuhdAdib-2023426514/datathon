# Comprehensive Full-Mark Remediation Plan: Addressing All 20 Reviewer Findings

This implementation plan establishes a deterministic, end-to-end remediation pipeline addressing every finding raised in the expert rubric audit. It closes the remaining gaps between documented claims and repository code, enforces zero empirical fabrication, separates scientific assertions from baseline snapshots, upgrades econometric and spatial inference, and provides user-configurable policy profiles and cost structures.

---

## User Review Required

> [!IMPORTANT]
> **Priority 0 Default Fix in Scenario Simulator (`simulate_corridor`)**:
> `src/scenarios/simulator.py` currently defaults `affected_share: float = 1.0` in `simulate_corridor()`, while `DEFAULT_AFFECTED_SHARE = 0.15`. Changing this default to `DEFAULT_AFFECTED_SHARE` (0.15) eliminates the 100% campaign reach assumption, ensuring calls without explicit parameters behave conservatively.

> [!IMPORTANT]
> **Separation of Scientific Invariants vs. Snapshot Baselines**:
> Moving predetermined outcomes (such as Accommodation Services ranking #1, or specific corridor pairs like Selangor $\rightarrow$ Melaka) out of unit tests and into `tests/snapshot/test_baseline_snapshots.py` ensures that `tests/` tests scientific properties (ranges, schemas, identities), while snapshot tests verify continuity with recorded official data releases.

> [!NOTE]
> **Econometric Enhancements**:
> We introduce a 999-replication **Wild Cluster Bootstrap** for the headline ALOS elasticity in the state panel model ($N=16$ clusters) and **corridor-clustered standard errors** ($N=240$ corridor clusters) for the longitudinal PPML gravity model. Both clustered and bootstrap $p$-values will be reported transparently.

---

## Proposed Changes

The plan is organized across six functional areas matching the review's 18-step priority order:

```
[Area 1: Opportunity Engine & Pareto Hierarchy] (Review Items 1, 2, 3, 4, 5)
       │
[Area 2: Scenario Engine & Monte Carlo Calibration] (Review Items 6, 7, 8)
       │
[Area 3: Advanced Econometrics & Spatial Inference] (Review Items 11, 12, 13)
       │
[Area 4: Commercial Portfolio Optimizer & Assistant] (Review Items 16, 17, 18, 19)
       │
[Area 5: Validation Architecture & Snapshot Separation] (Review Items 14, 15)
       │
[Area 6: Provenance, Documentation & Links] (Review Items 9, 10, 20)
```

---

### Area 1: Opportunity Engine & Pareto Hierarchy

#### [MODIFY] [state_diagnostics.py](file:///home/muhammad_adib/dosm/src/analytics/state_diagnostics.py)
1. **Remove All Empirical Defaults (Item 1)**:
   - Ensure `dest_baseline_aor_pct`, `dest_available_rooms`, `distance_km`, `dest_interstate_hhi`, and `dest_spend_per_night` preserve `np.nan`.
   - Explicitly classify missing capacity as `"Insufficient Evidence"` and `capacity_headroom_pct = np.nan`.
2. **Pure Gravity Gap / Normalized Gap Rate (Item 2)**:
   - Replace $c_1 = \max(0, \text{GravityGap}) + 0.5 \times \text{TouristFlow}$ with normalized demand gap rate:
     $$c_1 = \text{GapRate} = \frac{\max(0, \text{ExpectedFlow} - \text{ActualFlow})}{\text{ExpectedFlow}} \quad (\text{for } \text{ExpectedFlow} > 0)$$
   - Keep `tourist_flow_thousands` purely as a descriptive volume field without blending it into the Pareto demand gap.
3. **Decouple Scenario Simulation from Opportunity Screening (Item 3)**:
   - Ensure the opportunity table does not evaluate a baked-in $+0.5\text{d}$ stay extension at 100% reach.
   - Maintain nullable scenario compatibility columns (`additional_tourist_nights_thousands = np.nan`, `additional_accom_expenditure_rm_million = np.nan`) with `capacity_constraint_alert = "Baseline headroom only; simulate a policy in the scenario engine"`.
4. **Pareto-First Ranking Hierarchy (Item 4)**:
   - Primary: `pareto_rank` ascending (non-dominated Frontier 1 first).
   - Secondary: `policy_preference_score` descending.
   - Remove legacy expenditure-based `opportunity_rank` sorting.
5. **Configurable Policy Preference Weights (Item 5)**:
   - Refactor composite opportunity score into `policy_preference_score` with parameter `policy_weights: Optional[Dict[str, float]] = None`.
   - Default balanced profile: Yield (25%), Capacity Headroom (20%), Model Flow Gap (20%), Accessibility (20%), Diversification (15%).

#### [MODIFY] [CorridorNetwork.tsx](file:///home/muhammad_adib/dosm/dashboard/src/components/CorridorNetwork.tsx)
- Add a **Policy Preference Preset Selector** (Balanced Default, Value Maximizer, Dispersal First, Feeder Diversification) allowing policymakers to dynamically re-rank corridors according to their normative strategic weights.

---

### Area 2: Scenario Engine & Monte Carlo Calibration

#### [MODIFY] [simulator.py](file:///home/muhammad_adib/dosm/src/scenarios/simulator.py)
- **Change Default Affected Share (Item 6 - P0)**:
  - In `simulate_corridor()`, set default `affected_share: float = DEFAULT_AFFECTED_SHARE` (0.15), replacing the dangerous `1.0` default.
  - Document explicitly in docstrings that unspecified affected share assumes a realistic 15% campaign reach.

#### [MODIFY] [monte_carlo.py](file:///home/muhammad_adib/dosm/src/scenarios/monte_carlo.py)
1. **Zero Empirical Fallbacks (Item 7)**:
   - Eliminate any fallback to 2.5 days or RM 60/night.
   - If destination baseline ALOS or spend/night is `None` or `NaN`, return structured unavailable response:
     ```python
     {
         "status": "UNAVAILABLE",
         "reason": f"Destination '{destination}' lacks empirical baseline ALOS or spend per night.",
         "evidence_status": "insufficient_data"
     }
     ```
2. **Dual Uncertainty Calibration Framework (Item 8)**:
   - **Empirical Uncertainty (Historically Estimated)**:
     - Estimate state-specific historical ALOS standard deviation $\sigma(\text{ALOS}_s)$ across 2018–2025 panel alongside $\sigma(\text{Spend/Night}_s)$.
     - Draw baseline ALOS from log-normal distribution parameterized by empirical $\text{CV}_{\text{ALOS}, s}$.
     - Draw Accommodation VAI from truncated normal parameterized by longitudinal standard deviation $\sigma(\text{VAI}) = 0.039$.
   - **Policy Uncertainty (Scenario Sensitivity)**:
     - Policy reach: truncated normal around user assumption $AffectedShare$ ($\text{SD} = 0.04$).
     - Stay extension target: truncated normal around $\Delta \text{ALOS}$.
   - Expose explicit `uncertainty_breakdown: {"empirical": {...}, "policy": {...}}` in JSON output.

---

### Area 3: Advanced Econometrics & Spatial Inference

#### [MODIFY] [panel_econometrics.py](file:///home/muhammad_adib/dosm/src/analytics/panel_econometrics.py)
1. **Wild Cluster Bootstrap for Model 2 (Item 11)**:
   - Implement Wild Cluster Bootstrap (Rademacher / Webb weights, 999 replications) for the headline ALOS coefficient $t$-statistic in the Two-Way FE model with $N=16$ state clusters.
   - Output both `clustered_p_value` ($0.0952$) and `wild_bootstrap_p_value` ($p_{\text{boot}}$) in `panel_summary_records`.
2. **Transparent Imputation & Complete-Case Diagnostics (Item 12)**:
   - Replace silent `.fillna()` for `foreign_guest_share_pct` and `holiday_share_tourist`.
   - Add explicit missingness indicators `is_imputed_foreign_share` and `is_imputed_holiday_share`.
   - Run complete-case specifications ($N_{\text{complete}}$) alongside sensitivity checks, reporting both in summary records.

#### [MODIFY] [gravity_corridor_model.py](file:///home/muhammad_adib/dosm/src/analytics/gravity_corridor_model.py)
- **Corridor Panel Clustered Standard Errors (Item 13)**:
  - In longitudinal PPML estimation across 2018–2024 panel (1,680 observations across 240 directional corridors), cluster covariance by bilateral corridor:
    ```python
    df_fit["corridor_id"] = df_fit["origin"] + "_" + df_fit["destination"]
    model = glm(formula, data=df_fit, family=sm.families.Poisson()).fit(
        cov_type="cluster",
        cov_kwds={"groups": df_fit["corridor_id"]}
    )
    ```
  - Report corridor-clustered standard errors and robust $z$-statistics alongside OOS $R^2$.

---

### Area 4: Commercial Portfolio Optimizer & Assistant

#### [MODIFY] [portfolio_optimizer.py](file:///home/muhammad_adib/dosm/src/scenarios/portfolio_optimizer.py)
1. **User-Entered & Benchmark Cost Models (Item 17)**:
   - Add `custom_costs: Optional[Dict[str, float]] = None` and `cost_model: str = "illustrative_benchmark"`.
   - Explicitly label benchmark costs as `"ILLUSTRATIVE COST ASSUMPTION (Planning Benchmark)"`.
   - Support uniform campaign grant or user-provided budget inputs.
2. **Terminology Overhaul: Scenario GVA-to-Cost Multiple (Item 18)**:
   - Replace "Portfolio ROI Multiplier" and "ROI" with `"Scenario GVA-to-Cost Multiple"`:
     $$\text{Multiple} = \frac{\Delta \text{GVA}}{\text{Intervention Cost}}$$
   - Accompany all metrics with mandatory caveat: *"Based on illustrative intervention-cost assumptions; not financial ROI."*
3. **Evidence Query Assistant Refinement (Item 16)**:
   - Ensure `query_grounded_assistant()` dynamically populates all responses from DuckDB tables (`product_value_summary`, `corridor_opportunity_gap`, `state_year`, `source_metadata.json`).
   - Remove any legacy hardcoded numbers or claims of 77 corridors (authoritative count is 58 Pareto frontier corridors).
   - Drop the "zero-hallucination" phrase; maintain "Evidence Query Assistant (Structured State Evidence Lookup)".

#### [MODIFY] [ScenarioSimulator.tsx](file:///home/muhammad_adib/dosm/dashboard/src/components/ScenarioSimulator.tsx)
- Update KPI cards to display "Scenario GVA-to-Cost Multiple" with subtitle *"GVA per RM cost (Benchmark)"* and tooltip *"Scenario benchmark multiple based on promotional budget allocation assumptions; not a guaranteed financial ROI."*

---

### Area 5: Validation Architecture & Snapshot Separation

#### [MODIFY] [test_tsa_accounting.py](file:///home/muhammad_adib/dosm/src/validation/test_tsa_accounting.py)
- **Scientific Validation Focus (Item 14)**:
  - Test bounds ($0 \le \text{VAI} \le 1$), mathematical accounting identities, contiguous ranks $1..8$, and quadrant taxonomy.
  - Remove predetermined hypothesis assertion (`assert top_product["product"] == "Accommodation services"`), which belongs in snapshot testing.

#### [MODIFY] [test_state_and_corridors.py](file:///home/muhammad_adib/dosm/src/validation/test_state_and_corridors.py)
- **Mathematical & Structural Integrity Focus (Item 14 & 15)**:
  - Test deterministic Pareto sorting, valid tiers, and capacity bounds.
  - Move hardcoded corridor expectations (`("Selangor", "Melaka") in corridor_pairs`) to snapshot tests.
  - Update scenario simulator test assertion (line 169) to verify nights with `inputs["affected_share"] * inputs["delta_alos_nights"]`.

#### [MODIFY] [test_baseline_snapshots.py](file:///home/muhammad_adib/dosm/tests/snapshot/test_baseline_snapshots.py)
- Expand baseline snapshot tests to verify:
  - 2025 release snapshot maintains Accommodation Services as #1 VAI product.
  - 2025 corridor baseline snapshot records Selangor $\rightarrow$ Melaka and Selangor $\rightarrow$ Perak as priority corridors.
  - Econometric point-estimate snapshot records headline elasticity ($0.6628$) and PPML holdout $R^2$ ($0.5890$).

#### [MODIFY] [test_results_consistency.py](file:///home/muhammad_adib/dosm/tests/test_results_consistency.py)
- Verify contract schema compliance, numerical finiteness, and non-negativity, delegating historical point-estimate regression checks to `test_baseline_snapshots.py`.

---

### Area 6: Provenance, Documentation & Links

#### [MODIFY] [source_registry.yaml](file:///home/muhammad_adib/dosm/data/metadata/source_registry.yaml)
- Verify and enforce consistent metadata schema across all sources: `publication_date`, `source_url`, `source_file`, `download_date`, `checksum_sha256`, `reference_period`, `data_status`.
- Confirm State DTS release date is recorded as **15 September 2026**.

#### [MODIFY] [README.md](file:///home/muhammad_adib/dosm/README.md)
1. **Precise VAI Definition (Item 10)**:
   - Update Section 7.A to:
     > Accommodation's post-recovery VAI of 0.8579 means approximately **RM 85.79 of industry Gross Value Added (GVA) is generated per RM 100 of accommodation domestic supply** (2023–2025 post-recovery median VAI = 0.8579, CV = 0.039). Applying this VAI to Internal Tourism Consumption (ITC) serves as the derived tourism-attributable GVA proxy.
2. **Convert Local Links to Relative Markdown Links (Item 20)**:
   - Replace all `file:///home/muhammad_adib/dosm/...` links with standard relative repository links (`docs/methodology.md`, `artifacts/rubric_evidence_matrix.md`, `docs/presentation_deck.md`, etc.).

---

## Verification Plan

### Automated Tests
1. **Run Full Test Suite**:
   ```bash
   .venv/bin/python -m pytest -v
   ```
   *Expected*: All unit, econometric, scenario, and snapshot tests pass cleanly.

2. **Run Pipeline End-to-End**:
   ```bash
   .venv/bin/python src/pipeline.py --stage analytics
   .venv/bin/python src/pipeline.py --stage validate
   .venv/bin/python src/pipeline.py --stage export
   ```
   *Expected*: All 20 validation gates pass with 100% success; dashboard JSONs exported deterministically.

3. **Frontend Contract & Build Verification**:
   ```bash
   cd dashboard && npm test
   cd dashboard && npm run build
   ```
   *Expected*: 6/6 `node:test` runner tests pass; TypeScript compiles with zero errors.

### Manual Verification
1. Launch dashboard dev server (`npm run dev`) and inspect:
   - View 3 (Corridor Network): Verify policy priority presets recompute and sort corridors dynamically.
   - View 4 (Scenario Simulator): Confirm default affected share shows 15% and KPI cards show "Scenario GVA-to-Cost Multiple".
   - View 5 (Roadmap & Assistant): Test dynamic state dropdown; verify zero hardcoded hallucinations.
