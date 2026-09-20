---
name: dashboard-export-contract
description: >-
  Authoritative JSON schemas, TypeScript interface bindings, serialization rules,
  and parity verification contracts between Python analytics exporters and the React dashboard.
---

# Dashboard Export Contract & Data Schema Guide

This skill specifies the exact JSON schemas, serialization invariants, and TypeScript interface mappings connecting `src/analytics/export_dashboard_json.py` to the React dashboard views (`dashboard/src/components/*`).

## 1. Export File Manifest

All dashboard JSON files are serialized to `dashboard/public/data/`:

| File | Primary Consumer | Primary TS Interface | Update Frequency |
| :--- | :--- | :--- | :--- |
| `tsa_macro.json` | View 1 (Tourism Value Monitor) | `TSAMacroData` | Pre-calculated 2015–2025 |
| `state_profiles.json` | View 2 (Accommodation Map) | `Record<string, StateProfile>` | 16 States multi-year |
| `od_corridors.json` | View 3 (Corridor Network) | `ODCorridorsData` | 2018–2025 longitudinal |
| `scenario_engine.json` | View 4 (Scenario Simulator) | `ScenarioEngineConfig` | Model constants & elasticities |
| `drivers_rq3.json` | Econometric Attribution Modal | `DriversData` | Panel FE / OLS beta coefficients |
| `geo_malaysia.json` | Leaflet / ECharts Map Views | GeoJSON `FeatureCollection` | Static 16-state boundary |

---

## 2. Serialization Invariants & Cleaning Rules

Python serializes via `clean_nan()` in `src/analytics/export_dashboard_json.py`:

```python
def clean_nan(obj: Any) -> Any:
    # 1. NaN and Inf MUST become JSON null (never NaN, Infinity, or string "NaN")
    # 2. Floats are rounded to 4 decimal places by default
    # 3. Integers and booleans preserve native types
    # 4. Dates are serialized as ISO-8601 strings or integer years
```

### Critical Rules
1. **Never Emit `NaN`**: JavaScript `JSON.parse("NaN")` throws a syntax error.
2. **Nullable Fields**: If an indicator is unobserved for a given state-year (e.g. 5-star hotel rooms in Perlis), emit `null`, never `0` unless `0` was an explicitly observed value.
3. **Array Consistency**: Arrays in time series (`time_series: any[]`) must be sorted chronologically by `year ASC`.

---

## 3. Detailed Data Schemas

### A. `tsa_macro.json` (`TSAMacroData`)

```typescript
export interface TSAMacroData {
  macro_series: TSAMacroYear[];     // 11 rows (2015 to 2025)
  product_series: TourismProductYear[]; // 88 rows (8 products x 11 years)
  product_summary: ProductSummary[];    // 8 rows (benchmarks & quadrants)
}
```

* **`product_summary` Strategic Quadrants**:
  - `High-Value Core Activity` (VAI $\ge 0.50$, ITC $\ge$ median)
  - `Growth Opportunity` (VAI $\ge 0.50$, ITC $<$ median)
  - `Efficiency Improvement Priority` (VAI $< 0.50$, ITC $\ge$ median)
  - `Lower Immediate Priority` (VAI $< 0.50$, ITC $<$ median)

### B. `state_profiles.json` (`Record<string, StateProfile>`)

Keyed by canonical state name (`"Johor"`, `"Melaka"`, `"W.P. Kuala Lumpur"`, etc.):

```typescript
export interface StateProfile {
  state: string;
  state_code: string;           // ISO 3166-2: e.g. "MY-04"
  region: string;               // "Northern" | "Central" | "Southern" | "East Coast" | "East Malaysia"
  archetype_name: string;       // Typology: e.g. "Prime Conversion Target (High Headroom)"
  archetype_desc: string;
  archetype_color: string;      // Hex color for chart tags
  cluster_id: number;
  radar_scores: {               // Normalized 0 to 100 for radar charts
    stay_duration: number;
    nightly_yield: number;
    accom_intensity: number;
    leisure_orientation: number;
    luxury_supply: number;
    resident_affluence: number;
  };
  baseline_2025: {
    visitors_thousands: number;
    tourists_thousands: number;
    alos_days: number;
    spend_per_night_rm: number;
    spend_per_tourist_rm: number;
    accommodation_share_pct: number;
    accommodation_expenditure_rm_million: number;
    total_expenditure_rm_million: number;
    hotel_rooms: number;
    aor_pct: number;
    resident_median_income_rm: number;
  };
  demographics: StateDemographics;
  lodging_shares?: StateLodgingShares; // Paid commercial vs unpaid VFR
  sdg_metrics: StateSDGMetrics;         // TEY, EPR, DVR, TIR, RYH
  hotel_stars: StateHotelStars;         // 3, 4, 5-star inventory breakdown
}
```

### C. `od_corridors.json` (`ODCorridorsData`)

```typescript
export interface ODCorridorsData {
  corridors_2025: Corridor[];           // 240 directed interstate corridors
  corridors_by_year?: Record<string, Corridor[]>; // 2018-2025
  destination_concentration: Array<{
    destination: string;
    hhi_interstate: number;
    top_origin: string;
    top_origin_share_pct: number;
    concentration_tier: "Moderate" | "Concentrated" | "Highly Concentrated";
  }>;
  category_summary: Record<string, number>;
}
```

* **Corridor Categories**:
  - `Priority Conversion Corridor`: High flow ($> \text{median}$), low stay / weak accommodation spend.
  - `Protect / Deepen`: High flow, strong ALOS and high accommodation capture.
  - `Growth Opportunity`: Moderate/low flow, strong destination spend yield.
  - `Lower Priority`: Low flow, weak value indicators.

### D. `scenario_engine.json` (`ScenarioEngineConfig`)

```typescript
export interface ScenarioEngineConfig {
  constants: {
    accommodation_vai: number;         // 0.8579 (TSA benchmark)
    fnb_vai: number;                   // 0.4318
    overall_tourism_vai: number;       // 0.5186
    disclaimer: string;                // "Scenario estimate, not a causal forecast."
  };
  state_baselines: Record<string, {
    alos: number;
    spend_per_night: number;
    tourists_k: number;
    hotel_rooms: number;
    aor: number;
  }>;
  gravity_elasticities: {
    distance_friction: number;        // -0.5592
    origin_working_age: number;
    origin_income: number;
    destination_pull: number;
    cross_region_barrier: number;
  };
}
```

---

## 4. Frontend Parity Testing Protocol

When modifying an exporter or analytical model:
1. Run `python src/pipeline.py --stage export`.
2. Inspect `dashboard/public/data/*.json` for non-null required keys.
3. Validate schema compatibility:
   ```bash
   npx tsc --noEmit --project dashboard/tsconfig.json
   ```
4. Verify that `disclaimer` is displayed prominently on all scenario simulation outputs.
