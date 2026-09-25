"""
USA Location Filter
Strictly checks whether a job's location is in the United States.
Handles US states, major cities, and explicit US remote indicators (e.g. 'Remote - US').
Does not treat generic international remote as USA.
"""

import re
from typing import Tuple, Optional, List, Dict, Any

US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
    'DC': 'District of Columbia', 'PR': 'Puerto Rico'
}

US_CITIES_PATTERN = (
    r'\b(new york|los angeles|chicago|houston|phoenix|philadelphia|san antonio|san diego|dallas|'
    r'austin|boston|seattle|denver|miami|atlanta|portland|detroit|minneapolis|las vegas|orlando|'
    r'san francisco|mountain view|sunnyvale|palo alto|san jose|berkeley|oakland|redmond|bellevue|'
    r'boulder|cambridge|raleigh|durham|charlotte|nashville|salt lake city|pittsburgh)\b'
)

US_COUNTRY_KEYWORDS = [
    "united states", "usa", "us", "u.s.", "u.s.a", "united states of america", "america"
]

NON_US_EXCLUSIONS = [
    r'\bcanada\b', r'\buk\b', r'\bunited\s*kingdom\b', r'\blondon\b', r'\bgermany\b', r'\bberlin\b',
    r'\bfrance\b', r'\bparis\b', r'\bindia\b', r'\bbangalore\b', r'\bhyderabad\b', r'\baustralia\b',
    r'\bsydney\b', r'\bnetherlands\b', r'\bamsterdam\b', r'\bsingapore\b', r'\bireland\b', r'\bdublin\b',
    r'\bbrazil\b', r'\bmexico\b', r'\bspain\b', r'\bpoland\b', r'\bsweden\b', r'\bswitzerland\b'
]


def is_us_location(
    location_str: Optional[str] = None,
    address_dict: Optional[Dict[str, Any]] = None,
    secondary_locations: Optional[List[Any]] = None
) -> bool:
    """
    Evaluates if location is within the United States.
    """
    # 1. Check structured address object if available
    if address_dict and isinstance(address_dict, dict):
        postal = address_dict.get("postalAddress", {})
        country = (postal.get("addressCountry") or "").strip().lower()
        if country in ["united states", "us", "usa", "united states of america"]:
            return True
        elif country and any(re.search(n, country) for n in NON_US_EXCLUSIONS):
            return False

    if not location_str:
        return False
        
    loc = location_str.strip()
    loc_lower = loc.lower()
    
    # 2. Check explicit non-US exclusions
    for non_us in NON_US_EXCLUSIONS:
        if re.search(non_us, loc_lower):
            # Exception if explicitly "US or UK", etc.
            if not any(k in loc_lower for k in ["united states", "usa", "remote - us", "remote, us"]):
                return False

    # 3. Check explicit US keywords
    if any(k in loc_lower for k in ["remote - us", "remote us", "remote - united states", "remote united states", "remote (us)", "us remote", "united states remote", "remote, us"]):
        return True

    for keyword in US_COUNTRY_KEYWORDS:
        if re.search(rf'\b{re.escape(keyword)}\b', loc_lower):
            return True

    # 4. Check state abbreviation (e.g. "San Francisco, CA")
    state_abbr_pattern = r'\b(' + '|'.join(US_STATES.keys()) + r')\b'
    if re.search(state_abbr_pattern, loc.upper()):
        return True

    # 5. Check full state name
    for full_name in US_STATES.values():
        if re.search(rf'\b{re.escape(full_name.lower())}\b', loc_lower):
            return True

    # 6. Check major US cities
    if re.search(US_CITIES_PATTERN, loc_lower):
        return True

    # 7. Check secondary locations
    if secondary_locations and isinstance(secondary_locations, list):
        for sec in secondary_locations:
            sec_loc = sec.get("location", "") if isinstance(sec, dict) else str(sec)
            if is_us_location(sec_loc):
                return True

    return False


def parse_us_location(location_str: Optional[str]) -> Tuple[Optional[str], Optional[str], str, bool]:
    """
    Parses location into (city, state, country, is_remote)
    """
    if not location_str:
        return None, None, "USA", False
        
    loc = location_str.strip()
    loc_lower = loc.lower()
    is_remote = "remote" in loc_lower
    
    state_abbr = None
    for abbr in US_STATES.keys():
        if f", {abbr}" in loc or f" {abbr}" in loc or loc.endswith(abbr):
            state_abbr = abbr
            break
            
    if not state_abbr:
        for abbr, full_name in US_STATES.items():
            if full_name.lower() in loc_lower:
                state_abbr = abbr
                break
                
    parts = loc.split(',')
    city = parts[0].strip() if parts else None
    
    return city, state_abbr, "USA", is_remote
