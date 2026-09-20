---
name: dashboard-design-system
description: >-
  Visual tokens, semantic color schemes, ECharts configuration standards,
  and layout guidelines for the Malaysia Tourism Value Optimizer web application.
---

# Dashboard Design System & Visualization Guidelines

This skill defines the UI tokens, semantic color palettes, chart styling conventions, and layout invariants for the **Malaysia Tourism Value Optimizer** React dashboard.

---

## 1. Semantic Color Palettes

### A. Tourism Value Corridor Categories (View 3 & 4)

| Category | Hex Code | Tailwind Class | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| **Priority Conversion Corridor** | `#f43f5e` | `rose-500` | High visitor flow with weak stay/spending capture — prime conversion target |
| **Protect / Deepen** | `#10b981` | `emerald-500` | High volume, high ALOS, strong accommodation capture — core revenue pillar |
| **Growth Opportunity** | `#0ea5e9` | `sky-500` | Moderate flow with strong yield — capacity expansion corridor |
| **Lower Priority** | `#64748b` | `slate-500` | Low volume, low economic capture — secondary monitoring |

### B. Strategic Quadrants (TSA Product VAI vs. ITC Scale)

| Quadrant | Hex Code | Tailwind Class | Strategic Meaning |
| :--- | :--- | :--- | :--- |
| **High-Value Core Activity** | `#10b981` | `emerald-500` | High VAI ($\ge 0.50$) + High ITC (e.g. Accommodation) |
| **Growth Opportunity** | `#0ea5e9` | `sky-500` | High VAI ($\ge 0.50$) + Low ITC |
| **Efficiency Improvement** | `#f59e0b` | `amber-500` | Low VAI ($< 0.50$) + High ITC (e.g. F&B, Retail) |
| **Lower Immediate Priority** | `#94a3b8` | `slate-400` | Low VAI ($< 0.50$) + Low ITC |

### C. SDG 8.9 & 12.b Diagnosis Colors

| Diagnosis | Color Code | Status Indicator |
| :--- | :--- | :--- |
| **High Yield, High Retention** | `#10b981` (Emerald) | Top TEY (>RM 300/day), DVR > 60% |
| **Day-Tripper Transit Pressure (High EPR)** | `#f59e0b` (Amber) | EPR > 1.8 (Severe excursionist infrastructure load) |
| **VFR-Trapped High ALOS** | `#8b5cf6` (Violet) | ALOS > 2.5 nights, commercial lodging < 40% |
| **Frontier / Specialized** | `#0ea5e9` (Sky Blue) | Emerging cross-border / regional gateway |

---

## 2. ECharts Configuration Standards

All Apache ECharts instances in `dashboard/src/components/` must adopt these base configurations:

### Dark Theme Palette & Glassmorphism
```typescript
export const ECHARTS_THEME = {
  backgroundColor: "transparent",
  textStyle: {
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    color: "#94a3b8", // Slate 400
  },
  title: {
    textStyle: { color: "#f8fafc", fontWeight: 600, fontSize: 15 },
    subtextStyle: { color: "#64748b", fontSize: 12 },
  },
  tooltip: {
    backgroundColor: "rgba(15, 23, 42, 0.92)", // Slate 900 Glassmorphic
    borderColor: "#334155",
    borderWidth: 1,
    padding: [10, 14],
    textStyle: { color: "#f8fafc", fontSize: 12 },
    extraCssText: "backdrop-filter: blur(8px); border-radius: 8px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);",
  },
  grid: {
    top: 45,
    right: 25,
    bottom: 40,
    left: 55,
    borderColor: "#1e293b",
  },
};
```

### Axis Formatting Rules
* **Currency**: Prefix `RM` and suffix `M` (Millions) or `B` (Billions).
* **Ratios**: Format as percentages with 1 decimal place (`45.2%`).
* **Durations**: Always append units (`nights` or `days`).
* **Zero Line**: Highlight `yAxis.axisLine` when data crosses zero.

---

## 3. Mandatory Disclaimer Standards

Per **AGENTS.md Section 7 & 9**, any UI view presenting what-if scenario simulations or econometric forecasts must render this exact notice:

> ⚠️ **Scenario estimate, not a causal forecast.**

### Styling Token for Disclaimer Badge:
```tsx
<div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
  <span>⚠️ Scenario estimate, not a causal forecast.</span>
</div>
```

---

## 4. Layout & Responsive Breakpoints

* **Desktop First**: Minimum optimized viewport: $1280 \times 800$ (Standard laptop).
* **Grid Structure**:
  - Top: Header with National Macro KPIs (ITC, TDGVA, TDGVA/ITC, Employment).
  - Main: 2-column or 3-column split (Map/Network on left, Detail Cards/Radar on right).
  - Bottom: Scenario Simulation Drawer / Comparative Panel.
* **Component IDs**: Every major interactive element (dropdown, button, slider) must possess a descriptive, unique HTML `id` for automated browser testing.
