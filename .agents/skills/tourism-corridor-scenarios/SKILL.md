---
name: tourism-corridor-scenarios
description: >-
  Network modeling, Origin-Destination corridor classification, HHI market concentration,
  and transparent what-if scenario simulation engine for tourism policy interventions.
---

# Tourism Corridor Network & Policy Scenario Standards

This skill defines the mathematical formulations, network metrics, corridor classification criteria, and what-if simulation engine for Stages D, E, and F of the **Malaysia Tourism Value Optimizer**.

---

## 1. Origin-Destination (OD) Value Network Analysis (Stage D)

Let $F[o, d]$ denote the annual domestic tourist flow from origin state $o$ to destination state $d$.

### A. Network Metrics
1. **Weighted Out-Strength (Feeder Power)**:
   $$\text{OutStrength}_o = \sum_{d \neq o} F[o, d]$$
   Measures the total domestic tourist generation capacity of origin market $o$.

2. **Weighted In-Strength (Destination Volume)**:
   $$\text{InStrength}_d = \sum_{o \neq d} F[o, d]$$
   Measures the total domestic tourist intake of destination $d$.

3. **Destination Feeder Concentration (Herfindahl-Hirschman Index - HHI)**:
   $$s_{o, d} = \frac{F[o, d]}{\text{InStrength}_d}$$
   $$\text{HHI}_d = \sum_{o \neq d} (s_{o, d} \times 100)^2$$
   * $\text{HHI} < 1,500$: Diversified origin market.
   * $1,500 \le \text{HHI} \le 2,500$: Moderately concentrated origin market.
   * $\text{HHI} > 2,500$: Highly concentrated (vulnerable to shocks in a single feeder state).

---

## 2. 4-Tier Tourism Value Corridor Classification (Stage E)

Corridors ($o \rightarrow d$) are classified using a multi-criteria percentile matrix combining:
1. **Flow Volume ($F[o, d]$)**: Median or 60th percentile cutoff across all active inter-state corridors.
2. **Destination ALOS ($\text{ALOS}_d$)**: Benchmark against national domestic ALOS.
3. **Accommodation Expenditure Yield**: Spend per tourist or accommodation share at destination $d$.

### Typology Matrix:

| Classification | Flow Profile | Economic / ALOS Profile | Strategic Policy Action |
| :--- | :--- | :--- | :--- |
| **Priority Conversion Corridor** | **High Flow** (Above median) | **Low ALOS** and/or **Weak Accommodation Spend** | **Primary Target**: Convert same-day/short-stay visitors into overnight stays; enhance night-time economy and hotel packaging. |
| **Protect & Deepen** | **High Flow** (Above median) | **Strong ALOS** and **Strong Accommodation Spend** | **Anchor**: Maintain high satisfaction, increase repeat visits, premium experiential offerings. |
| **Growth Opportunity** | **Moderate/Lower Flow** (Below median) | **Strong ALOS** and **Strong Accommodation Spend** | **Yield Multiplier**: Expand marketing and transport connectivity to an already high-yield destination. |
| **Lower Strategic Priority** | **Low Flow** (Below median) | **Weak ALOS** and **Weak Accommodation Spend** | Low immediate ROI for targeted economic intervention. |

---

## 3. Transparent Scenario Simulator Engine (Stage F)

The simulator models the potential gross accommodation expenditure and attributable value added resulting from incremental policy shifts (e.g., lengthening stays, converting day trips to overnight stays).

### A. Mathematical Formulation
Given:
* $F[o, d]$: Baseline tourist flow between origin $o$ and destination $d$.
* $\Delta \text{ALOS}$: Incremental change in average length of stay (e.g., $+0.2$ nights, $+0.5$ nights).
* $\text{SpendPerNight}_d$: Baseline destination accommodation spend per night:
  $$\text{SpendPerNight}_d = \frac{\text{AccommodationExpenditure}_d}{\text{Tourists}_d \times \text{ALOS}_d}$$
* $\text{AccommodationVAI}$: National TSA accommodation value-added intensity ($\approx 0.35 - 0.45$).

The simulated incremental outcomes are:

1. **Additional Tourist Nights Generated**:
   $$\Delta \text{TouristNights}_{o, d} = F[o, d] \times \Delta \text{ALOS}$$

2. **Additional Accommodation Expenditure**:
   $$\Delta \text{AccommodationSpend}_{o, d} = \Delta \text{TouristNights}_{o, d} \times \text{SpendPerNight}_d$$

3. **Potential Additional Value Added (Analytical Proxy)**:
   $$\Delta \text{ValueAdded}_{o, d} = \Delta \text{AccommodationSpend}_{o, d} \times \text{AccommodationVAI}$$

---

## 4. Non-Negotiable Mandatory Guardrails

> [!IMPORTANT]
> ### Mandatory Disclaimer Requirement
> Every scenario card, table, and visualization output MUST prominently display this exact statement:
> 
> **"Scenario estimate, not a causal forecast."**

* **No Guaranteed Impact Claims**: Never present scenario outputs as guaranteed financial returns or promises.
* **Causality vs Association**: Never claim that an increase in ALOS *causes* higher TDGDP. It is an economic yield model based on current observed spending propensities.
* **Bounded Parameters**: The UI and scenario inputs should constrain $\Delta \text{ALOS}$ within realistic policy ranges (e.g., $+0.1$ to $+1.5$ nights).
