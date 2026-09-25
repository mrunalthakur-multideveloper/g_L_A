"""
Multi-Country Location Filter
Extends location filtering to support USA, Canada, UK, India, Germany, and other target countries.
Ensures full backward compatibility with the existing USA location filters.
"""

import re
from typing import Tuple, Optional, List, Dict, Any
from .usa import is_us_location, parse_us_location, US_STATES, US_CITIES_PATTERN

# Canadian Provinces & Territories
CA_PROVINCES = {
    'ON': 'Ontario', 'BC': 'British Columbia', 'AB': 'Alberta', 'QC': 'Quebec',
    'MB': 'Manitoba', 'SK': 'Saskatchewan', 'NS': 'Nova Scotia', 'NB': 'New Brunswick',
    'NL': 'Newfoundland and Labrador', 'PE': 'Prince Edward Island',
    'YT': 'Yukon', 'NT': 'Northwest Territories', 'NU': 'Nunavut'
}

CA_CITIES_PATTERN = (
    r'\b(toronto|vancouver|montreal|ottawa|calgary|edmonton|waterloo|kitchener|'
    r'mississauga|winnipeg|quebec city|halifax|victoria|richmond|burnaby|markham|brampton)\b'
)

# UK Regions & Cities
UK_CITIES_PATTERN = (
    r'\b(london|manchester|birmingham|edinburgh|glasgow|leeds|bristol|cambridge|'
    r'oxford|liverpool|sheffield|newcastle|nottingham|cardiff|belfast)\b'
)

# India Cities
IN_CITIES_PATTERN = (
    r'\b(bangalore|bengaluru|hyderabad|pune|mumbai|delhi|new delhi|gurgaon|gurugram|'
    r'noida|chennai|kolkata|ahmedabad|kochi|indore)\b'
)

# Germany Cities
DE_CITIES_PATTERN = (
    r'\b(berlin|munich|münchen|frankfurt|hamburg|cologne|köln|stuttgart|düsseldorf|'
    r'leipzig|dortmund|essen|dresden|hannover)\b'
)


def normalize_country_name(country: Optional[str]) -> str:
    """Normalizes country names to a canonical code or uppercase name."""
    if not country:
        return "USA"
    c = country.strip().upper()
    if c in ["US", "USA", "UNITED STATES", "UNITED STATES OF AMERICA", "AMERICA"]:
        return "USA"
    if c in ["CA", "CAN", "CANADA"]:
        return "CANADA"
    if c in ["UK", "GB", "UNITED KINGDOM", "ENGLAND", "SCOTLAND", "WALES", "GREAT BRITAIN"]:
        return "UK"
    if c in ["IN", "IND", "INDIA"]:
        return "INDIA"
    if c in ["DE", "DEU", "GERMANY", "DEUTSCHLAND"]:
        return "GERMANY"
    if c in ["AU", "AUS", "AUSTRALIA"]:
        return "AUSTRALIA"
    return c


def is_canada_location(
    location_str: Optional[str] = None,
    address_dict: Optional[Dict[str, Any]] = None,
    secondary_locations: Optional[List[Any]] = None
) -> bool:
    """Checks if a location is in Canada."""
    if address_dict and isinstance(address_dict, dict):
        postal = address_dict.get("postalAddress", {})
        country = (postal.get("addressCountry") or "").strip().lower()
        if country in ["canada", "ca", "can"]:
            return True

    if not location_str:
        return False

    loc = location_str.strip()
    loc_lower = loc.lower()

    if any(k in loc_lower for k in ["canada", "remote - canada", "remote canada", "canada remote", "remote, canada", "remote (canada)"]):
        return True

    # Check Canadian province abbreviations
    prov_pattern = r'\b(' + '|'.join(CA_PROVINCES.keys()) + r')\b'
    if re.search(prov_pattern, loc.upper()):
        return True

    # Check full province names
    for full_name in CA_PROVINCES.values():
        if re.search(rf'\b{re.escape(full_name.lower())}\b', loc_lower):
            return True

    # Check major Canadian cities
    if re.search(CA_CITIES_PATTERN, loc_lower):
        return True

    if secondary_locations and isinstance(secondary_locations, list):
        for sec in secondary_locations:
            sec_loc = sec.get("location", "") if isinstance(sec, dict) else str(sec)
            if is_canada_location(sec_loc):
                return True

    return False


def is_uk_location(
    location_str: Optional[str] = None,
    address_dict: Optional[Dict[str, Any]] = None,
    secondary_locations: Optional[List[Any]] = None
) -> bool:
    """Checks if a location is in the United Kingdom."""
    if address_dict and isinstance(address_dict, dict):
        postal = address_dict.get("postalAddress", {})
        country = (postal.get("addressCountry") or "").strip().lower()
        if country in ["united kingdom", "uk", "gb", "great britain", "england", "scotland"]:
            return True

    if not location_str:
        return False

    loc = location_str.strip()
    loc_lower = loc.lower()

    if any(k in loc_lower for k in ["united kingdom", "uk", "remote - uk", "remote uk", "england", "scotland", "wales", "great britain"]):
        return True

    if re.search(UK_CITIES_PATTERN, loc_lower):
        return True

    if secondary_locations and isinstance(secondary_locations, list):
        for sec in secondary_locations:
            sec_loc = sec.get("location", "") if isinstance(sec, dict) else str(sec)
            if is_uk_location(sec_loc):
                return True

    return False


def is_country_location(
    location_str: Optional[str] = None,
    target_country: str = "USA",
    address_dict: Optional[Dict[str, Any]] = None,
    secondary_locations: Optional[List[Any]] = None
) -> bool:
    """
    Evaluates whether a job's location matches the requested target country.
    Supports USA, Canada, UK, India, Germany, Australia, and generic matching.
    """
    norm_target = normalize_country_name(target_country)

    if norm_target == "USA":
        return is_us_location(location_str, address_dict, secondary_locations)

    if norm_target == "CANADA":
        return is_canada_location(location_str, address_dict, secondary_locations)

    if norm_target == "UK":
        return is_uk_location(location_str, address_dict, secondary_locations)

    if not location_str:
        return False

    loc_lower = location_str.strip().lower()
    target_lower = target_country.strip().lower()

    # Address dict check
    if address_dict and isinstance(address_dict, dict):
        postal = address_dict.get("postalAddress", {})
        country = (postal.get("addressCountry") or "").strip().lower()
        if country == target_lower or norm_target in country.upper():
            return True

    # Generic check for target country in location string
    if target_lower in loc_lower or norm_target.lower() in loc_lower:
        return True

    if norm_target == "INDIA" and re.search(IN_CITIES_PATTERN, loc_lower):
        return True

    if norm_target == "GERMANY" and (re.search(DE_CITIES_PATTERN, loc_lower) or "deutschland" in loc_lower):
        return True

    if secondary_locations and isinstance(secondary_locations, list):
        for sec in secondary_locations:
            sec_loc = sec.get("location", "") if isinstance(sec, dict) else str(sec)
            if is_country_location(sec_loc, target_country):
                return True

    return False


def parse_country_location(
    location_str: Optional[str],
    target_country: str = "USA"
) -> Tuple[Optional[str], Optional[str], str, bool]:
    """
    Parses location into (city, state/province, country, is_remote) for target country.
    """
    norm_target = normalize_country_name(target_country)
    if norm_target == "USA":
        return parse_us_location(location_str)

    if not location_str:
        return None, None, target_country, False

    loc = location_str.strip()
    loc_lower = loc.lower()
    is_remote = "remote" in loc_lower

    parts = loc.split(',')
    city = parts[0].strip() if parts else None
    state_or_prov = parts[1].strip() if len(parts) > 1 else None

    return city, state_or_prov, target_country, is_remote
