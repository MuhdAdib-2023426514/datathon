---
name: unit-conversion-standards
description: >-
  Standard lookup tables, conversion multipliers, and scope compatibility rules
  for currency (RM), volume, duration, and capacity metrics across Malaysian official tourism sources.
---

# Unit Conversion Standards & Harmonization Guide

This skill enforces strict unit normalization across all raw sources (DTS, TSA, MOTAC KPI, HIES, DOSM Census) ingested into the **Malaysia Tourism Value Optimizer**.

---

## 1. Currency Normalization Matrix (Ringgit Malaysia)

| Source Dataset | Source Unit | Canonical Output Unit | Normalization Factor | Formula |
| :--- | :--- | :--- | :--- | :--- |
| **TSA Product Supply & GVA** | RM Million | RM Million | $1.0$ | No conversion needed |
| **TSA Macro (TDGVA, ITC)** | RM Million / Billion | RM Million | $1,000.0$ if Billion | $\text{Billion} \times 1,000$ |
| **DTS State Total Spend** | RM Million | RM Million | $1.0$ | No conversion needed |
| **DTS Granular Expenditure Items** | RM Million / RM '000 | RM Million | $\div 1,000$ if '000 | $\text{RM '000} \div 1,000$ |
| **Spend per Tourist** | RM (exact) | RM (exact) | $1.0$ | $\frac{\text{Spend (RM M)} \times 10^6}{\text{Tourists ('000)} \times 10^3} = \frac{\text{Spend\_M}}{\text{Tourists\_K}} \times 1,000$ |
| **Spend per Visitor-Night** | RM (exact) | RM (exact) | $1.0$ | $\frac{\text{Spend per Tourist}}{\text{ALOS (Nights)}}$ |
| **Median Household Income (HIES)** | RM (exact monthly) | RM (exact monthly) | $1.0$ | No conversion needed |

> [!CAUTION]
> **Never mix Thousands and Millions without explicit conversion!**
> Always verify column suffixes: `_rm_million`, `_rm_thousand`, `_rm`.

---

## 2. Visitor & Tourist Volume Units

| Concept | Source Unit | Canonical Storage | Target Metric Unit | Conversion Formula |
| :--- | :--- | :--- | :--- | :--- |
| **Domestic Visitors** | '000 persons | '000 persons | Thousands | Sum of Tourists + Excursionists |
| **Overnight Tourists** | '000 persons | '000 persons | Thousands | Overnight stays $\ge 1$ night |
| **Day Excursionists** | '000 persons | '000 persons | Thousands | Same-day visits ($0$ nights) |
| **Origin-Destination Flows** | '000 persons | '000 persons | Thousands | Directed flow $F_{o,d}$ |
| **Hotel Guests (Domestic/Foreign)**| Exact count | Exact count | Integer | Absolute guest arrivals |
| **Resident Population** | '000 persons | '000 persons | Thousands | DOSM State Demographics |

---

## 3. Stay Duration: Days vs. Nights Disambiguation

* **DTS Average Length of Stay (ALOS)**:
  * In the Domestic Tourism Survey, ALOS for **overnight tourists** represents **nights spent in the destination state**.
  * Range in Malaysia: **$1.8$ to $3.1$ nights** per tourist trip.
  * For **same-day excursionists**, stay duration is $0$ nights ($1$ day).
* **Visitor-Days vs. Tourist-Nights**:
  * $\text{Tourist Nights}_s = \text{Overnight Tourists}_s \times \text{ALOS}_s$
  * $\text{Total Visitor Days}_s = (\text{Overnight Tourists}_s \times \text{ALOS}_s) + \text{Excursionists}_s$
  * Used in calculating **Tourism Economic Yield (TEY)**:
    $$\text{TEY}_s = \frac{\text{Total Expenditure (RM)}_s}{\text{Total Visitor Days}_s}$$

---

## 4. Accommodation Capacity & Operational Metrics

* **Hotel Rooms**: Total physical room inventory (integer count).
* **Available Room Nights per Year**: $\text{Rooms} \times 365$.
* **Average Occupancy Rate (AOR)**:
  * Stored as a **percentage** ($0.0\%$ to $100.0\%$) or proportion ($0.0$ to $1.0$).
  * Canonical convention in analytical tables: **Percentage points** ($45.5$ means $45.5\%$).
* **Occupied Room Nights**: $\text{Total Rooms} \times 365 \times \frac{\text{AOR}}{100}$.
* **Spare Room Headroom**: $\text{Total Rooms} \times 365 \times \left(1 - \frac{\text{AOR}}{100}\right)$.
* **Average Guests per Room (Assumption)**: $1.8$ persons per occupied room night.

---

## 5. Expenditure Scope Guardrails: DTS vs. TSA ITC

Do **NOT** equate Domestic Tourism Survey (DTS) expenditure totals with Tourism Satellite Account (TSA) Internal Tourism Consumption (ITC):

| Scope Dimension | Domestic Tourism Survey (DTS) | TSA Internal Tourism Consumption (ITC) |
| :--- | :--- | :--- |
| **Inbound International Visitors** | Excluded | **Included** |
| **Domestic Resident Tourism** | **Included** | **Included** |
| **Imputed Housing Services** | Excluded | **Included** (owner-occupied vacation homes) |
| **Government Non-Market Services** | Excluded | **Included** (cultural/heritage subsidies) |
| **Business Travel Expenses** | Partially captured (per diem) | **Included** (intermediate consumption) |

> [!IMPORTANT]
> - DTS measures direct household out-of-pocket expenditure within states.
> - TSA ITC measures total macroeconomic consumption of tourism products nationwide.
> - Never divide DTS state accommodation spend by TSA national accommodation supply.
