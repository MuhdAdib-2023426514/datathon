---
name: data-pipeline-validation
description: >-
  Data quality checklist, Excel ingestion procedures, schema enforcement,
  status flag preservation (e/p/r), unit reconciliations, and assertion tests.
---

# Data Pipeline & Validation Standards

This skill defines ingestion workflows, data quality gates, and automated test assertions for transforming raw DOSM Excel tables into clean analytical datasets.

## 1. Primary Source Inventory & Expected Structures

1. **TSA Malaysia 2015–2025**:
   * File: `data/tsa/tourism_2025.xlsx`
   * Key tables: Macro TDGVA/TDGDP, Domestic Supply by product, Gross Value Added by industry, Internal Tourism Consumption (ITC), Tourism Ratios, Tourism Employment.
2. **National Domestic Tourism Survey 2025**:
   * File: `data/malaysia/TABLE DTS 2025.xlsx`
   * Key tables: Total visitors, overnight tourists, same-day excursionists, average length of stay (ALOS), expenditure components, national OD matrix.
3. **State Domestic Tourism Survey 2025 (16 Files)**:
   * Directory: `data/state/`
   * Files: `TABLE OF PUBLICATION DTS 2025 <STATE>.xlsx` (e.g., JOHOR, KEDAH, ..., W.P. PUTRAJAYA).
   * Key tables: State visitors, tourists, trip purpose, expenditure by category (accommodation, F&B, transport, shopping, entertainment), accommodation type, ALOS.

---

## 2. Target Analytical Schemas (Tidy Tables)

Ingestion scripts must output structured Parquet files and DuckDB tables matching these exact schemas:

### Table 1: `tourism_product_year`
* `year`: INTEGER (2015 to 2025)
* `product`: VARCHAR (Tourism characteristic/connected product name)
* `industry`: VARCHAR (Corresponding tourism industry name)
* `domestic_supply`: DOUBLE (Domestic supply at basic/producers prices, in RM Million)
* `gva`: DOUBLE (Gross Value Added, in RM Million)
* `itc`: DOUBLE (Internal Tourism Consumption, in RM Million)
* `tourism_ratio`: DOUBLE (TSA Tourism Ratio, range 0.0 to 1.0)
* `employment`: DOUBLE (Tourism employment, thousands or persons)
* `vai`: DOUBLE (Calculated $VAI = GVA / Supply$)
* `estimated_tourism_gva`: DOUBLE (Analytical proxy: $ITC \times VAI$)
* `data_status`: VARCHAR (`actual`, `p` for preliminary, `e` for estimate, `r` for revised)

### Table 2: `state_year`
* `year`: INTEGER (2025)
* `state`: VARCHAR (Standardized canonical state name)
* `state_code`: VARCHAR (ISO 3166-2:MY)
* `visitors`: DOUBLE (Total domestic visitors in millions / thousands)
* `tourists`: DOUBLE (Overnight domestic tourists)
* `trips`: DOUBLE (Total domestic trips)
* `total_expenditure`: DOUBLE (Total domestic tourism expenditure, in RM Million)
* `accommodation_expenditure`: DOUBLE (Expenditure on accommodation, in RM Million)
* `food_expenditure`: DOUBLE (Expenditure on food & beverage, in RM Million)
* `transport_expenditure`: DOUBLE (Expenditure on transport, in RM Million)
* `shopping_expenditure`: DOUBLE (Expenditure on shopping, in RM Million)
* `recreation_expenditure`: DOUBLE (Expenditure on entertainment/recreation, in RM Million)
* `alos`: DOUBLE (Average Length of Stay in days / nights)
* `accommodation_share`: DOUBLE (Accommodation spend / total expenditure)
* `spend_per_tourist`: DOUBLE (Accommodation spend / overnight tourists)
* `spend_per_night`: DOUBLE (Accommodation spend / (tourists * alos))

### Table 3: `origin_destination`
* `year`: INTEGER (2025)
* `origin`: VARCHAR (Standardized origin state)
* `destination`: VARCHAR (Standardized destination state)
* `is_interstate`: BOOLEAN (True if origin != destination)
* `tourist_flow`: DOUBLE (Number of domestic tourist trips between o and d)

---

## 3. Data Quality & Cleaning Rules

1. **Status Code Preservation**:
   * Cells containing flags (e.g., `12,450 p`, `15,320 e`, `9,810 r`) must be split into:
     * Clean numerical value (`12450.0`)
     * Status flag column (`p`, `e`, `r`, or `actual`)
2. **Explicit Unit Standardization**:
   * Confirm source units in sheet title/footnote (e.g., "RM Million", "RM '000", "Billion", "Persons", "'000 Persons").
   * Convert all expenditure and supply metrics to uniform **RM Million**.
   * Convert all visitor counts to uniform **Thousands ('000)** or absolute counts with explicit column labeling.
3. **Handling Footnotes and Disclaimers**:
   * Drop footnote markers (e.g., `[1]`, `*`, `a/`) during regex cleaning.
   * Strip trailing spaces and non-breaking spaces (`\xa0`).
4. **Reconciliation Checks**:
   * Sum of product components vs. official published total (variance must be $< 0.1\%$ due to rounding).
   * Sum of state expenditures vs. national published total (log any methodological divergence between national and state aggregation).

---

## 4. Automated Pipeline Assertions (Unit Tests)

Every transformation script must execute assertion gates prior to writing to `tourism_data.duckdb`:

```python
def validate_tourism_product_year(df):
    assert not df.empty, "Dataframe is empty!"
    assert df['year'].between(2015, 2025).all(), "Year out of expected 2015-2025 range."
    assert (df['domestic_supply'] >= 0).all(), "Negative domestic supply detected."
    assert (df['gva'] >= 0).all(), "Negative GVA detected."
    assert (df['itc'] >= 0).all(), "Negative ITC detected."
    assert df['vai'].between(0.0, 1.0).all(), "VAI must be bounded between 0.0 and 1.0."
    assert (df['tourism_ratio'].dropna().between(0.0, 1.0)).all(), "Tourism ratio must be between 0.0 and 1.0."

def validate_state_year(df):
    assert len(df['state'].unique()) == 16, f"Expected 16 states, found {len(df['state'].unique())}"
    assert (df['alos'] > 0).all(), "ALOS must be strictly positive."
    assert df['accommodation_share'].between(0.0, 1.0).all(), "Accommodation share must be between 0 and 1."
    assert (df['tourists'] <= df['visitors']).all(), "Overnight tourists cannot exceed total visitors."

def validate_origin_destination(df):
    assert (df['tourist_flow'] >= 0).all(), "Negative tourist flow detected."
    valid_states = set(STATE_CANONICAL_MAP.values())
    assert set(df['origin']).issubset(valid_states), "Unknown origin state names detected."
    assert set(df['destination']).issubset(valid_states), "Unknown destination state names detected."
```
