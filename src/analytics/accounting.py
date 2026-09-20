"""
Authoritative Accounting Functions for Malaysia Tourism Value Optimizer.
Follows AGENTS.md Section 3 non-negotiable analytical definitions:
- Value-Added Intensity (VAI): VAI[i,t] = GVA[i,t] / DomesticSupply[i,t]
- Estimated tourism-attributable GVA: ITC[i,t] * VAI[i,t]
- Accommodation share: AccommodationExpenditure / TotalTourismExpenditure
- Accommodation spend per visitor: AccommodationExpenditure / DomesticVisitors
- Accommodation spend per tourist: AccommodationExpenditure / OvernightTourists
- Spend per night: AccommodationExpenditure / (OvernightTourists * ALOS)

Sprint 2 Modernizations (IMPLEMENTATION_PLAN.md Phases 5, 6, 6.1, 7, 8, 13):
- Real RM Deflation: RealValue_t = NominalValue_t * (Index_2025 / Index_t)
- Visitor-Days Footprint: VisitorDays = Tourists * ALOS + Excursionists
- Tourism Expenditure Yield (TEY): TotalExpenditure / VisitorDays
- Accommodation Yield: AccommodationExpenditure / (Tourists * ALOS)
- Tourism GVA Intensity: sum_k (Exp_k * VAI_k) / sum_k (MappedExp_k) * 100%
- Zero Arbitrary Fallback: Remove 'other': 0.50 default; explicitly track Mapping Coverage.
- Tourism Value-Added Yield (TVAY): EstimatedTourismGVA / VisitorDays
- State Typology: ALOS vs TVAY 4-quadrant classification.

Missing Value Policy (AGENTS.md Rule 6 & Sprint 1):
Never fabricate or coerce unobserved observations to 0.0. Missing or invalid inputs propagate as np.nan.
"""

from typing import Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Section 1: Standard TSA Product & Accommodation Indicators (AGENTS.md Sec 3)
# ---------------------------------------------------------------------------

def calc_vai(gva: Optional[float], domestic_supply: Optional[float]) -> float:
    """
    Calculate Value-Added Intensity (VAI).
    VAI = GVA / DomesticSupply.
    Proportion of supply represented by Gross Value Added.
    Returns np.nan if supply is missing, <= 0, or gva is missing.
    """
    if domestic_supply is None or pd.isna(domestic_supply) or domestic_supply <= 0:
        return np.nan
    if gva is None or pd.isna(gva):
        return np.nan
    return float(gva / domestic_supply)


def calc_estimated_tourism_gva(itc: Optional[float], vai: Optional[float]) -> float:
    """
    Calculate Estimated Tourism-Attributable GVA Proxy = ITC * VAI.
    Note: Never label this as official product-level TDGVA.
    Preferred label: 'Estimated tourism-attributable GVA' or 'Tourism value-added proxy'.
    Returns np.nan if either input is missing or NaN.
    """
    if itc is None or pd.isna(itc) or vai is None or pd.isna(vai):
        return np.nan
    return float(itc * vai)


def calc_accommodation_share(
    accommodation_expenditure: Optional[float], total_expenditure: Optional[float]
) -> float:
    """
    Calculate Accommodation Share = AccommodationExpenditure / TotalTourismExpenditure.
    Returns np.nan if total expenditure is missing or <= 0.
    """
    if total_expenditure is None or pd.isna(total_expenditure) or total_expenditure <= 0:
        return np.nan
    if accommodation_expenditure is None or pd.isna(accommodation_expenditure):
        return np.nan
    return float(accommodation_expenditure / total_expenditure)


def calc_spend_per_visitor(
    accommodation_expenditure_rm: Optional[float], visitors_count: Optional[float]
) -> float:
    """
    Accommodation Spend Per Visitor (RM) = AccommodationExpenditure / DomesticVisitors.
    Returns np.nan if visitors count is missing or <= 0.
    """
    if visitors_count is None or pd.isna(visitors_count) or visitors_count <= 0:
        return np.nan
    if accommodation_expenditure_rm is None or pd.isna(accommodation_expenditure_rm):
        return np.nan
    return float(accommodation_expenditure_rm / visitors_count)


def calc_spend_per_tourist(
    accommodation_expenditure_rm: Optional[float], tourists_count: Optional[float]
) -> float:
    """
    Accommodation Spend Per Tourist (RM) = AccommodationExpenditure / OvernightTourists.
    Returns np.nan if tourists count is missing or <= 0.
    """
    if tourists_count is None or pd.isna(tourists_count) or tourists_count <= 0:
        return np.nan
    if accommodation_expenditure_rm is None or pd.isna(accommodation_expenditure_rm):
        return np.nan
    return float(accommodation_expenditure_rm / tourists_count)


def calc_spend_per_night(
    accommodation_expenditure_rm: Optional[float],
    tourists_count: Optional[float],
    alos_days: Optional[float],
) -> float:
    """
    Accommodation Spend Per Night (RM) = AccommodationExpenditure / (OvernightTourists * ALOS).
    Aggregate constructed ratio; correlations with ALOS are denominator-dependent.
    Returns np.nan if tourists count or ALOS is missing, <= 0.
    """
    if tourists_count is None or alos_days is None or pd.isna(tourists_count) or pd.isna(alos_days):
        return np.nan
    nights = tourists_count * alos_days
    if pd.isna(nights) or nights <= 0:
        return np.nan
    if accommodation_expenditure_rm is None or pd.isna(accommodation_expenditure_rm):
        return np.nan
    return float(accommodation_expenditure_rm / nights)


# ---------------------------------------------------------------------------
# Section 2: Real RM Deflation (IMPLEMENTATION_PLAN.md Phase 5)
# ---------------------------------------------------------------------------

def calc_real_value(
    nominal_value: Optional[float],
    year: int,
    price_index_map: Dict[int, float],
    base_year: int = 2025,
) -> float:
    """
    Convert nominal RM to constant base year RM using official CPI index:
    RealValue_t = NominalValue_t * (Index_base / Index_t)
    Returns np.nan if nominal_value or indices are missing or <= 0.
    """
    if nominal_value is None or pd.isna(nominal_value):
        return np.nan
    base_index = price_index_map.get(base_year)
    year_index = price_index_map.get(year)
    if base_index is None or pd.isna(base_index) or base_index <= 0:
        return np.nan
    if year_index is None or pd.isna(year_index) or year_index <= 0:
        return np.nan
    return float(nominal_value * (base_index / year_index))


# ---------------------------------------------------------------------------
# Section 3: Yield & Carrying Capacity Metrics (IMPLEMENTATION_PLAN.md Phase 7)
# ---------------------------------------------------------------------------

def calc_visitor_days(
    tourists_count: Optional[float],
    alos_days: Optional[float],
    excursionists_count: Optional[float],
) -> float:
    """
    Total Visitor-Days Footprint:
    VisitorDays = Tourists * ALOS + Excursionists
    Returns np.nan if any component is missing or invalid.
    """
    if tourists_count is None or alos_days is None or excursionists_count is None:
        return np.nan
    if pd.isna(tourists_count) or pd.isna(alos_days) or pd.isna(excursionists_count):
        return np.nan
    if tourists_count < 0 or alos_days <= 0 or excursionists_count < 0:
        return np.nan
    return float((tourists_count * alos_days) + excursionists_count)


def calc_tey(
    total_expenditure_rm: Optional[float],
    visitor_days: Optional[float],
) -> float:
    """
    Tourism Expenditure Yield (TEY, RM/day) = TotalTourismExpenditure / VisitorDays.
    Returns np.nan if visitor_days is missing or <= 0.
    """
    if total_expenditure_rm is None or visitor_days is None:
        return np.nan
    if pd.isna(total_expenditure_rm) or pd.isna(visitor_days) or visitor_days <= 0:
        return np.nan
    return float(total_expenditure_rm / visitor_days)


def calc_accommodation_yield(
    accommodation_expenditure_rm: Optional[float],
    tourists_count: Optional[float],
    alos_days: Optional[float],
) -> float:
    """
    Accommodation Yield (RM/night) = AccommodationExpenditure / (Tourists * ALOS).
    Directly equivalent to spend per tourist night.
    Returns np.nan if denominator is missing or <= 0.
    """
    return calc_spend_per_night(
        accommodation_expenditure_rm=accommodation_expenditure_rm,
        tourists_count=tourists_count,
        alos_days=alos_days,
    )


# ---------------------------------------------------------------------------
# Section 4: Tourism GVA Intensity & Mapping Coverage (Phases 6 & 6.1)
# ---------------------------------------------------------------------------

def calc_estimated_tourism_gva_state(
    expenditure_by_category: Dict[str, Optional[float]],
    vai_map: Dict[str, float],
) -> Tuple[float, float]:
    """
    Calculate state-level Estimated Tourism GVA Proxy and Mapped Expenditure.
    Follows Phase 6.1:
    - NO arbitrary 'other': 0.50 fallback.
    - Only categories with empirical TSA VAI mappings are included in GVA and Mapped Expenditure.
    Returns:
        (estimated_tourism_gva, mapped_expenditure)
    """
    cat_aliases = {
        "accommodation": ["accommodation", "lodging"],
        "food_beverage": ["food_beverage", "food", "fnb"],
        "shopping": ["shopping", "country_specific_goods", "retail"],
        "transport": ["transport", "passenger_transport"],
        "recreation": ["recreation", "entertainment", "cultural"],
    }

    estimated_gva = 0.0
    mapped_exp = 0.0

    for exp_cat, exp_val in expenditure_by_category.items():
        if exp_val is None or pd.isna(exp_val) or exp_val <= 0:
            continue
        exp_cat_lower = str(exp_cat).lower().strip()

        matched_vai = None
        # Check direct match in vai_map
        if exp_cat_lower in vai_map and vai_map[exp_cat_lower] is not None:
            matched_vai = float(vai_map[exp_cat_lower])
        else:
            # Check canonical alias groups
            for canon_name, aliases in cat_aliases.items():
                if exp_cat_lower in aliases:
                    if canon_name in vai_map and vai_map[canon_name] is not None:
                        matched_vai = float(vai_map[canon_name])
                    else:
                        for a in aliases:
                            if a in vai_map and vai_map[a] is not None:
                                matched_vai = float(vai_map[a])
                                break
                    break

        if matched_vai is not None and not pd.isna(matched_vai) and matched_vai >= 0:
            estimated_gva += float(exp_val * matched_vai)
            mapped_exp += float(exp_val)
        # Explicitly: If unmapped or unknown ('other'), DO NOT assume 0.50. Leave unmapped!

    return float(estimated_gva), float(mapped_exp)


def calc_mapping_coverage(
    mapped_expenditure: Optional[float],
    total_expenditure: Optional[float],
) -> float:
    """
    Mapping Coverage (%) = (MappedExpenditure / TotalExpenditure) * 100.
    Returns np.nan if total_expenditure is missing or <= 0.
    """
    if total_expenditure is None or pd.isna(total_expenditure) or total_expenditure <= 0:
        return np.nan
    if mapped_expenditure is None or pd.isna(mapped_expenditure):
        return np.nan
    return float((mapped_expenditure / total_expenditure) * 100.0)


def calc_tourism_gva_intensity(
    estimated_gva: Optional[float],
    mapped_expenditure: Optional[float],
) -> float:
    """
    Tourism GVA Intensity (%) = (EstimatedTourismGVA / MappedExpenditure) * 100.
    Replaces deprecated 'Domestic Value Retention' (DVR) terminology.
    Measures the value-added density of observed tourism expenditure.
    Returns np.nan if mapped_expenditure is missing or <= 0.
    """
    if mapped_expenditure is None or pd.isna(mapped_expenditure) or mapped_expenditure <= 0:
        return np.nan
    if estimated_gva is None or pd.isna(estimated_gva):
        return np.nan
    return float((estimated_gva / mapped_expenditure) * 100.0)


def calc_tvay(
    estimated_tourism_gva_rm: Optional[float],
    visitor_days: Optional[float],
) -> float:
    """
    Tourism Value-Added Yield (TVAY, RM/visitor-day) = EstimatedTourismGVA / VisitorDays.
    Measures the net gross value added generated per unit of domestic visitor pressure.
    Returns np.nan if visitor_days is missing or <= 0.
    """
    if estimated_tourism_gva_rm is None or visitor_days is None:
        return np.nan
    if pd.isna(estimated_tourism_gva_rm) or pd.isna(visitor_days) or visitor_days <= 0:
        return np.nan
    return float(estimated_tourism_gva_rm / visitor_days)


# ---------------------------------------------------------------------------
# Section 5: State Typology Quadrants (IMPLEMENTATION_PLAN.md Phase 8)
# ---------------------------------------------------------------------------

def classify_state_yield_typology(
    alos: Optional[float],
    yield_val: Optional[float],
    alos_median: float,
    yield_median: float,
) -> str:
    """
    Classify destination into a 2x2 policy quadrant using:
      Dimension 1: ALOS (Stay Duration)
      Dimension 2: Yield (TVAY or TEY per visitor-day)
    Quadrants:
      - Short Stay / Low Yield
      - Short Stay / High Yield
      - Long Stay / Low Yield
      - Long Stay / High Yield
    """
    if alos is None or yield_val is None or pd.isna(alos) or pd.isna(yield_val):
        return "Unclassified"

    is_long_stay = alos >= alos_median
    is_high_yield = yield_val >= yield_median

    if not is_long_stay and not is_high_yield:
        return "Short Stay / Low Yield"
    elif not is_long_stay and is_high_yield:
        return "Short Stay / High Yield"
    elif is_long_stay and not is_high_yield:
        return "Long Stay / Low Yield"
    else:
        return "Long Stay / High Yield"


# ---------------------------------------------------------------------------
# Section 6: Backward-Compatibility Shims (Deprecated)
# ---------------------------------------------------------------------------

def calc_sdg_attributable_gva(
    accommodation_exp: Optional[float],
    food_exp: Optional[float],
    shopping_exp: Optional[float],
    transport_exp: Optional[float],
    other_exp: Optional[float],
    vai_map: Dict[str, float],
) -> float:
    """
    Legacy compatibility shim for calc_estimated_tourism_gva_state.
    Note: Phase 6.1 eliminates the 0.50 fallback on unmapped expenditure.
    """
    exp_dict = {
        "accommodation": accommodation_exp,
        "food_beverage": food_exp,
        "shopping": shopping_exp,
        "transport": transport_exp,
    }
    # Only include other_exp if 'other' has an explicit empirical mapping in vai_map
    if "other" in vai_map and other_exp is not None:
        exp_dict["other"] = other_exp

    gva, _ = calc_estimated_tourism_gva_state(exp_dict, vai_map)
    return gva


def calc_value_retention_rate(
    attributable_gva: Optional[float], total_expenditure: Optional[float]
) -> float:
    """
    Legacy compatibility wrapper for calc_tourism_gva_intensity.
    """
    return calc_tourism_gva_intensity(attributable_gva, total_expenditure)
