---
name: sustainable-tourism-sdg-metrics
description: >-
  Economic indicators for sustainable tourism aligned with UN SDG 8.9 and 12.b,
  including Value Retention Multipliers, Tourism Economic Yield, and Overtourism Risk.
---

# Sustainable Tourism & SDG Economic Metrics Standards

This skill defines the methodology, mathematical formulas, and reporting guardrails for the sustainable economic metrics in the **Malaysia Tourism Value Optimizer**, directly aligned with **UN Sustainable Development Goals (SDG)**.

---

## 1. SDG Alignment & Strategic Mandate

* **Primary SDG: Target 8.9**:
  > *"By 2030, devise and implement policies to promote sustainable tourism that creates jobs and promotes local culture and products."*
* **Secondary SDG: Target 12.b**:
  > *"Develop and implement tools to monitor sustainable development impacts for sustainable tourism that creates jobs and promotes local culture and products."*

### Core Strategic Shift:
$$\text{Volume Expansion } (\text{More Visitors}) \longrightarrow \text{Value Capture } (\text{More Economic Value from Existing Visitors})$$

### Mandatory Reporting Guardrail:
> **"This project focuses on the economic dimension of sustainable tourism. It does not measure complete environmental or social sustainability."**

---

## 2. Key Sustainable Tourism Economic Indicators

### A. Tourism Economic Yield per Visitor-Day (TEY)
Measures the domestic economic return generated per unit of visitor pressure:

$$\text{TEY}_s = \frac{\text{Total Tourism Expenditure}_s}{\text{Total Visitor-Days}_s}$$

Where:
$$\text{Total Visitor-Days}_s = (\text{Tourists}_s \times \text{ALOS}_s) + \text{Excursionists}_s$$

* **High TEY**: Destination extracts high economic value per day of visitor footprint (sustainable yield).
* **Low TEY**: Destination absorbs high visitor volumes with low domestic economic capture (congestion risk).

---

### B. Domestic Value Retention Multiplier (DVR)
Not all tourism expenditure contributes equally to the domestic economy. Fuel and imported retail goods have high leakage, whereas accommodation and local services have high domestic value retention.

Using TSA Value-Added Intensities ($VAI_k = \frac{\text{GVA}_k}{\text{Supply}_k}$):

$$\text{Estimated Attributable GVA}_s = \sum_{k \in \text{Categories}} \text{Expenditure}_{s, k} \times VAI_k$$

$$\text{Domestic Value Retention Rate (DVR)}_s = \frac{\text{Estimated Attributable GVA}_s}{\text{Total Tourism Expenditure}_s} \times 100\%$$

* **Empirical Benchmark (TSA 2025)**:
  * Accommodation Services: $VAI = 85.8\%$ (highest domestic value retention).
  * Food & Beverage Serving Services: $VAI = 43.2\%$.
  * Country-Specific Goods: $VAI = 70.9\%$.
  * Transport & Automotive Fuel: $VAI \approx 20\% - 35\%$.
* **Policy Implication**: Shifting visitor expenditure into accommodation maximizes domestic GVA generation per visitor.

---

### C. Excursionist Pressure Ratio (EPR) & Day-Trip Congestion
Measures the proportion of day-trippers relative to value-generating overnight guests:

$$\text{EPR}_s = \frac{\text{Excursionists}_s}{\text{Tourists}_s}$$

* $\text{EPR} > 2.0$: High excursionist vulnerability. Infrastructure, parking, and public amenities are utilized by same-day visitors without capturing overnight accommodation yield (e.g., Melaka, Selangor, Perak).
* $\text{EPR} < 1.0$: Healthy overnight conversion (e.g., Sabah, Sarawak, Penang).

---

### D. Feeder Concentration & Vulnerability (HHI)
$$\text{HHI}_d = \sum_{o \neq d} \left( \frac{F[o, d]}{\sum_{j \neq d} F[j, d]} \times 100 \right)^2$$

* $\text{HHI} > 2,500$: High concentration risk. Destination economy is hypersensitive to economic shifts, fuel prices, or travel disruptions in a single origin feeder (e.g., reliance on Klang Valley).

---

## 3. Policy Recommendation Matrix

| Indicator Signal | Diagnostic Diagnosis | Sustainable Policy Intervention |
| :--- | :--- | :--- |
| **High Volume + Low TEY** | Volume Trap | Shift promotion from volume to length of stay; bundle evening cultural events and multi-day hotel passes. |
| **High EPR (> 2.0) + Short ALOS** | Day-Trip Leakage | Introduce sunset/night tourism attractions; develop MICE and weekend retreat packages to convert day-trips into overnights. |
| **High HHI (> 2,500)** | Market Fragility | Diversify origin marketing toward secondary feeder states with complementary travel seasons. |
| **High TEY + Strong DVR** | Sustainable Benchmark | Implement carrying-capacity monitoring and protect high-value environmental and cultural assets. |
