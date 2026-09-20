"""
Authoritative Accounting Functions for Malaysia Tourism Value Optimizer.
Follows AGENTS.md Section 3 non-negotiable analytical definitions:
- Value-Added Intensity (VAI): VAI[i,t] = GVA[i,t] / DomesticSupply[i,t]
- Estimated tourism-attributable GVA: ITC[i,t] * VAI[i,t]
- Accommodation share: AccommodationExpenditure / TotalTourismExpenditure
- Accommodation spend per visitor: AccommodationExpenditure / DomesticVisitors
- Accommodation spend per tourist: AccommodationExpenditure / OvernightTourists
- Spend per night: AccommodationExpenditure / (OvernightTourists * ALOS)
"""

from typing import Dict, Optional, Union
import numpy as np


def calc_vai(gva: Optional[float], domestic_supply: Optional[float]) -> float:
    """
    Calculate Value-Added Intensity (VAI).
    VAI = GVA / DomesticSupply.
    Proportion of supply represented by Gross Value Added.
    """
    if domestic_supply is None or np.isnan(domestic_supply) or domestic_supply <= 0:
        return 0.0
    if gva is None or np.isnan(gva):
        return 0.0
    return float(gva / domestic_supply)


def calc_estimated_tourism_gva(itc: Optional[float], vai: Optional[float]) -> float:
    """
    Calculate Estimated Tourism-Attributable GVA Proxy = ITC * VAI.
    Note: Never label this as official product-level TDGVA.
    Preferred label: 'Estimated tourism-attributable GVA' or 'Tourism value-added proxy'.
    """
    if itc is None or np.isnan(itc) or vai is None or np.isnan(vai):
        return 0.0
    return float(itc * vai)


def calc_accommodation_share(
    accommodation_expenditure: Optional[float], total_expenditure: Optional[float]
) -> float:
    """
    Calculate Accommodation Share = AccommodationExpenditure / TotalTourismExpenditure.
    """
    if total_expenditure is None or np.isnan(total_expenditure) or total_expenditure <= 0:
        return 0.0
    if accommodation_expenditure is None or np.isnan(accommodation_expenditure):
        return 0.0
    return float(accommodation_expenditure / total_expenditure)


def calc_spend_per_visitor(
    accommodation_expenditure_rm: Optional[float], visitors_count: Optional[float]
) -> float:
    """
    Accommodation Spend Per Visitor (RM) = AccommodationExpenditure / DomesticVisitors.
    """
    if visitors_count is None or np.isnan(visitors_count) or visitors_count <= 0:
        return 0.0
    if accommodation_expenditure_rm is None or np.isnan(accommodation_expenditure_rm):
        return 0.0
    return float(accommodation_expenditure_rm / visitors_count)


def calc_spend_per_tourist(
    accommodation_expenditure_rm: Optional[float], tourists_count: Optional[float]
) -> float:
    """
    Accommodation Spend Per Tourist (RM) = AccommodationExpenditure / OvernightTourists.
    """
    if tourists_count is None or np.isnan(tourists_count) or tourists_count <= 0:
        return 0.0
    if accommodation_expenditure_rm is None or np.isnan(accommodation_expenditure_rm):
        return 0.0
    return float(accommodation_expenditure_rm / tourists_count)


def calc_spend_per_night(
    accommodation_expenditure_rm: Optional[float],
    tourists_count: Optional[float],
    alos_days: Optional[float],
) -> float:
    """
    Accommodation Spend Per Night (RM) = AccommodationExpenditure / (OvernightTourists * ALOS).
    Aggregate constructed ratio; correlations with ALOS are denominator-dependent.
    """
    if tourists_count is None or alos_days is None:
        return 0.0
    nights = tourists_count * alos_days
    if np.isnan(nights) or nights <= 0:
        return 0.0
    if accommodation_expenditure_rm is None or np.isnan(accommodation_expenditure_rm):
        return 0.0
    return float(accommodation_expenditure_rm / nights)


def calc_sdg_attributable_gva(
    accommodation_exp: Optional[float],
    food_exp: Optional[float],
    shopping_exp: Optional[float],
    transport_exp: Optional[float],
    other_exp: Optional[float],
    vai_map: Dict[str, float],
) -> float:
    """
    Calculates total attributable GVA across all DTS expenditure categories.
    Guarantees no component is dropped due to ternary/operator precedence bugs.
    """
    accom_gva = (accommodation_exp or 0.0) * vai_map.get("accommodation", 0.0)
    food_gva = (food_exp or 0.0) * (
        vai_map.get("food_beverage") or vai_map.get("food") or 0.0
    )
    shop_gva = (shopping_exp or 0.0) * (
        vai_map.get("shopping") or vai_map.get("country_specific_goods") or 0.0
    )
    trans_gva = (transport_exp or 0.0) * (
        vai_map.get("transport") or vai_map.get("passenger_transport") or 0.0
    )
    other_gva = (other_exp or 0.0) * vai_map.get("other", 0.500)

    return float(accom_gva + food_gva + shop_gva + trans_gva + other_gva)


def calc_value_retention_rate(
    attributable_gva: Optional[float], total_expenditure: Optional[float]
) -> float:
    """
    Domestic Value Retention Rate (%) = (Attributable GVA / Total Expenditure) * 100.
    """
    if total_expenditure is None or np.isnan(total_expenditure) or total_expenditure <= 0:
        return 0.0
    if attributable_gva is None or np.isnan(attributable_gva):
        return 0.0
    return float((attributable_gva / total_expenditure) * 100.0)
