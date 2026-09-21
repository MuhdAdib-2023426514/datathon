"""Numeric source-cell parsing: absence is never an observed zero."""
import math


def parse_observation(value):
    if value is None or str(value).strip() == "":
        return float("nan"), "missing"
    if str(value).strip().lower() in {"-", "..", "...", "n/a", "na"}:
        return float("nan"), "suppressed_or_unavailable"
    try:
        number = float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return float("nan"), "invalid"
    return (number, "observed") if math.isfinite(number) else (float("nan"), "invalid")


def source_number(value):
    return parse_observation(value)[0]
