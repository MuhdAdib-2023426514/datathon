# Limitations & Caveats

**Project**: Malaysia Tourism Value Optimizer  
**Last Updated**: 2026-09-21

---

## 1. Observational Relationships Are Not Causal

All econometric models (Two-Way Fixed Effects panel, PPML gravity) identify statistical **associations**, not causal effects. The panel coefficient for ALOS (β = +0.66) means that, *within a given state over time*, periods with longer average stays are associated with higher real accommodation expenditure — it does not prove that extending stays causes proportional expenditure increases.

**Implication**: Policy scenario projections are estimates under stated assumptions, not guaranteed outcomes.

---

## 2. Small State-Level Sample

The Malaysian state panel contains **N = 16 states × 8 years = 126 observations**. With only 16 cluster units, state-clustered standard errors satisfy only approximate asymptotic conditions (the ideal threshold is 30–50 clusters).

**Mitigation**: Leave-one-state-out cross-validation confirms sign stability across all 16 exclusion runs. Influence diagnostics flag pandemic-period observations as expected.

---

## 3. National VAI Applied to State Expenditure Composition

Tourism Value-Added Intensity (VAI) is derived from the **national** Tourism Satellite Account. State-level expenditure is mapped to national product categories and multiplied by national VAI values. In reality, the value-added intensity of accommodation in Sabah may differ from Kuala Lumpur.

**Implication**: State-level Estimated Tourism GVA and Tourism Value-Added Yield (TVAY) are approximations. Mapping coverage (64%–79% across states) quantifies how much expenditure can be classified.

---

## 4. Annual Occupancy Rate Masks Seasonal Peaks

The Average Occupancy Rate (AOR) is an **annual average**. Destinations such as Melaka, Pulau Pinang, and Kuala Lumpur may experience weekend and holiday-season occupancy rates exceeding 90% even when their annual average is 65–70%.

**Implication**: Scenario capacity projections use annual AOR and should not be interpreted as peak-season feasibility assessments. The dashboard includes a prominent seasonal caveat.

---

## 5. Some Expenditure Categories Remain Unmapped

Not all DTS expenditure components have a direct match to TSA product categories. Unmapped categories are excluded from GVA calculations rather than assigned an arbitrary default VAI.

**Implication**: Mapping coverage is explicitly reported per state. States with lower coverage have more conservative GVA estimates (understated, not overstated).

---

## 6. Scenario Outcomes Depend on Stated Assumptions

Scenario projections require explicit assumptions about:
- **Campaign affected share** (default: 15% of tourists)
- **Stay extension magnitude** (e.g., +0.5 nights)
- **Guests per occupied room** (default: 1.8, labelled as scenario assumption)
- **Accommodation VAI** (national TSA value)

Different assumptions produce materially different projections. Monte Carlo uncertainty quantification (10,000 draws) provides P10–P90 confidence bands and capacity breach probabilities.

---

## 7. Survey Estimates Contain Sampling Uncertainty

The Domestic Tourism Survey (DTS) is a sample survey, not a census. Published estimates carry sampling variability that is not explicitly quantified in the published tables. State-level estimates for smaller states (e.g., W.P. Labuan, Perlis, W.P. Putrajaya) may have higher relative standard errors.

---

## 8. Gravity Model Predictive Limitations

The PPML gravity model achieves R²(OOS) = 0.5890 on 2025 holdout data. This means it explains ~59% of the variance in bilateral corridor flows from structural distance and fixed effects alone. The naive 2024-lagged persistence baseline achieves R²(OOS) = 0.7637. The gravity model's comparative advantage is **structural interpretation** (distance decay, Borneo barrier) rather than pure prediction.

---

## 9. No Explicit Environmental or Social Sustainability Measurement

This prototype focuses on the **economic dimension** of sustainable tourism (SDG 8.9 and 12.b). Environmental carrying capacity, carbon footprint, biodiversity impact, social equity, and cultural heritage preservation are acknowledged as essential dimensions of sustainability but are not measured in this version.

---

## 10. Data Currency

All primary data sources are from DOSM publications with reference year 2025 (preliminary status). Future official revisions may alter specific values but are unlikely to change structural patterns and typological classifications materially.
