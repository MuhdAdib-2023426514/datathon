---
name: malaysia-geo-standards
description: >-
  Geospatial standards, state name reconciliation dictionaries, ISO codes, coordinates,
  and choropleth projection conventions for all 16 Malaysian states and Federal Territories.
---

# Malaysia Geospatial & Regional Standards

This skill provides canonical geographic references, spelling reconciliations, state centroid coordinates, and mapping conventions for the **Malaysia Tourism Value Optimizer**.

## 1. Canonical State Reference Table (16 States & Federal Territories)

All ingestion pipelines, analytical tables, and UI components must standardize state names and codes against this reference:

| Canonical Name | Common Variations / Aliases | ISO 3166-2 Code | Region | Centroid Lat | Centroid Lon |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Johor** | Johor Darul Ta'zim, JHR | `MY-01` | Southern | 1.9344 | 103.3587 |
| **Kedah** | Kedah Darul Aman, KDH | `MY-02` | Northern | 6.1184 | 100.3685 |
| **Kelantan** | Kelantan Darul Naim, KTN | `MY-03` | East Coast | 5.3117 | 102.0040 |
| **Melaka** | Malacca, Melaka Bandaraya Bersejarah, MLK | `MY-04` | Southern | 2.2458 | 102.2741 |
| **Negeri Sembilan** | N. Sembilan, Negeri Sembilan Darul Khusus, NSN | `MY-05` | Central | 2.7258 | 102.2430 |
| **Pahang** | Pahang Darul Makmur, PHG | `MY-06` | East Coast | 3.8126 | 102.3256 |
| **Perak** | Perak Darul Ridzuan, PRK | `MY-08` | Northern | 4.6940 | 101.0901 |
| **Perlis** | Perlis Indera Kayangan, PLS | `MY-09` | Northern | 6.4449 | 100.2048 |
| **Pulau Pinang** | Penang, P. Pinang, PNG | `MY-07` | Northern | 5.4141 | 100.3288 |
| **Sabah** | Sabah Negeri Di Bawah Bayu, SBH | `MY-12` | East Malaysia | 5.9788 | 116.0753 |
| **Sarawak** | Sarawak Bumi Kenyalang, SWK | `MY-13` | East Malaysia | 2.5574 | 113.0012 |
| **Selangor** | Selangor Darul Ehsan, SGR | `MY-10` | Central | 3.0738 | 101.5183 |
| **Terengganu** | Terengganu Darul Iman, TRG | `MY-11` | East Coast | 4.8810 | 103.1167 |
| **W.P. Kuala Lumpur** | Kuala Lumpur, WP Kuala Lumpur, KL | `MY-14` | Central | 3.1390 | 101.6869 |
| **W.P. Labuan** | Labuan, WP Labuan, LBN | `MY-15` | East Malaysia | 5.2831 | 115.2308 |
| **W.P. Putrajaya** | Putrajaya, WP Putrajaya, PJY | `MY-16` | Central | 2.9264 | 101.6964 |

---

## 2. Regional Groupings for Macro-Corridor Analysis

When aggregating cross-state tourism flows, use the official macro-regions:

* **Northern**: Kedah, Perak, Perlis, Pulau Pinang
* **Central**: Selangor, W.P. Kuala Lumpur, W.P. Putrajaya, Negeri Sembilan
* **Southern**: Johor, Melaka
* **East Coast**: Kelantan, Pahang, Terengganu
* **East Malaysia (Borneo)**: Sabah, Sarawak, W.P. Labuan

---

## 3. Name Standardization Python Utility

Use this deterministic mapping function when parsing raw Excel headers or survey tables:

```python
STATE_CANONICAL_MAP = {
    # Variations -> Canonical
    "JOHOR": "Johor",
    "KEDAH": "Kedah",
    "KELANTAN": "Kelantan",
    "MELAKA": "Melaka",
    "MALACCA": "Melaka",
    "NEGERI SEMBILAN": "Negeri Sembilan",
    "N. SEMBILAN": "Negeri Sembilan",
    "PAHANG": "Pahang",
    "PERAK": "Perak",
    "PERLIS": "Perlis",
    "PULAU PINANG": "Pulau Pinang",
    "PENANG": "Pulau Pinang",
    "P. PINANG": "Pulau Pinang",
    "SABAH": "Sabah",
    "SARAWAK": "Sarawak",
    "SELANGOR": "Selangor",
    "TERENGGANU": "Terengganu",
    "W.P. KUALA LUMPUR": "W.P. Kuala Lumpur",
    "WP KUALA LUMPUR": "W.P. Kuala Lumpur",
    "KUALA LUMPUR": "W.P. Kuala Lumpur",
    "W.P. LABUAN": "W.P. Labuan",
    "WP LABUAN": "W.P. Labuan",
    "LABUAN": "W.P. Labuan",
    "W.P. PUTRAJAYA": "W.P. Putrajaya",
    "WP PUTRAJAYA": "W.P. Putrajaya",
    "PUTRAJAYA": "W.P. Putrajaya",
}

def standardize_state_name(raw_name: str) -> str:
    cleaned = raw_name.strip().upper()
    return STATE_CANONICAL_MAP.get(cleaned, raw_name.strip().title())
```

---

## 4. Origin-Destination (OD) Flow Mapping Rules

1. **Origin ($o$) and Destination ($d$)**:
   Both endpoints must resolve to one of the 16 canonical state names.
2. **Intra-State vs Inter-State Flows**:
   * Intra-state flow: $o == d$ (residents travelling within their own home state).
   * Inter-state corridor: $o \neq d$ (visitors travelling across state boundaries).
   * Note: Analysis must distinguish between intra-state trips and inter-state flows when modeling accommodation demand, as intra-state visitors frequently stay with relatives or take day trips.
3. **Map Visualization Conventions**:
   * Use geodesic curved arcs connecting origin centroid to destination centroid.
   * Arc thickness proportional to visitor flow volume ($F[o,d]$).
   * Arc color encoded by Corridor Category (*Priority Conversion*, *Protect/Deepen*, *Growth Opportunity*, *Lower Priority*).
   * Dashboard choropleth bounding box: Center coordinate approx `[4.2105, 101.9758]` with bounds accommodating both Peninsular Malaysia and East Malaysia (`lat: 0.8 to 7.5`, `lon: 99.5 to 119.5`).
