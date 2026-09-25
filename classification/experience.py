"""
Experience Requirement Extractor
Extracts required years of experience, experience ranges, degree combinations,
internships, and entry-level indicators from job posting descriptions.
"""

import re
from typing import Optional


EXPERIENCE_PATTERNS = [
    # 1. Standard: '8+ years in information security', '5+ years of software engineering experience'
    r'\b(\d{1,2}(?:\s*(?:\+|plus|-|\s*to\s*|\s*–\s*)\s*\d{1,2})?)\s*(?:\+)?\s*(?:years?|yrs?)\s+(?:in|of)\s+(?:[a-zA-Z\s]{3,35}\s+)?(?:experience|background|security|software|engineering|development|data|cloud|devops|product|leadership|operations|management)\b',
    
    # 2. Standard: '5+ years of ... experience', '3 - 5 years of relevant experience'
    r'\b(\d{1,2}(?:\s*(?:\+|plus|-|\s*to\s*|\s*–\s*)\s*\d{1,2})?)\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant|hands-on|professional|proven|direct|industry|work|practical|demonstrated|specialized|technical|software|engineering|coding|related|prior|full-time))?\s+(?:experience|background)\b',
    
    # 3. Minimum / At least 'minimum 3 years', 'at least 5+ years of experience'
    r'\b(?:minimum|at least|requires?|have|with)\s+(\d{1,2}(?:\s*(?:\+|plus|-|\s*to\s*|\s*–\s*)\s*\d{1,2})?)\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+\w+)?\s+(?:experience|background|work)\b',
    
    # 4. Direct: '3+ years experience', '5 years of professional experience'
    r'\b(\d{1,2}(?:\s*(?:\+|plus|-|\s*to\s*|\s*–\s*)\s*\d{1,2})?)\s*(?:\+)?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional|technical|industry|relevant|hands-on)?\s*experience\b',
    
    # 5. Active verbs: '5+ years leading security teams', '3+ years building web applications'
    r'\b(\d{1,2}(?:\s*(?:\+|plus|-|\s*to\s*|\s*–\s*)\s*\d{1,2})?)\s*(?:\+)?\s*(?:years?|yrs?)\s+(?:leading|managing|building|developing|designing|architecting|working|supporting|coding|writing)\b',
    
    # 6. Header format: 'Experience: 5+ years', 'Experience Required: 3-5 years'
    r'\b(?:experience(?:\s+level|\s+required)?\s*[:\-]\s*)(\d{1,2}(?:\s*(?:\+|plus|-|\s*to\s*|\s*–\s*)\s*\d{1,2})?)\s*(?:\+)?\s*(?:years?|yrs?)\b',
    
    # 7. Degree combo: 'Bachelor\'s degree and 4+ years', 'BS with 3-5 years'
    r'\b(?:bachelor\'?s|master\'?s|bs|ms|phd|degree)\s+(?:degree\s+)?(?:and|with|plus)\s+(\d{1,2}(?:\s*(?:\+|plus|-|\s*to\s*|\s*–\s*)\s*\d{1,2})?)\s*(?:\+)?\s*(?:years?|yrs?)\b',
    
    # 8. Entry level range: '0-2 years'
    r'\b(0\s*(?:-|to|–)\s*[1-3])\s*(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?\b'
]


def extract_experience(text: str, title: str = "", level: Optional[str] = None) -> Optional[str]:
    """
    Extracts required years of experience or experience level from job posting text.
    Handles numerical year ranges, degree requirements, entry-level indicators, and seniority levels.
    """
    if not text and not title:
        return None
    
    # 1. Clean and normalize whitespace & unicode spaces
    combined = f"{title}\n{text}"
    clean = re.sub(r'[\u202f\u00a0\u200b\ufeff\u200e\u2028\u2029\t]+', ' ', combined)
    clean = re.sub(r'\s+', ' ', clean)
    
    # 2. Check numerical experience patterns
    found_matches = []
    for pat in EXPERIENCE_PATTERNS:
        for m in re.finditer(pat, clean, re.IGNORECASE):
            full_match = m.group(0).strip()
            num_part = m.group(1).strip() if m.groups() else ''
            
            # Normalize digits and separators
            num_part = re.sub(r'\s*to\s*|\s*–\s*', '-', num_part)
            num_part = re.sub(r'\s*\+\s*', '+', num_part)
            num_part = re.sub(r'\s+', '', num_part)
            
            if num_part and not num_part.endswith('+') and '-' not in num_part and 'year' not in num_part.lower():
                if '+' in full_match:
                    num_part = f"{num_part}+"
                    
            formatted = f"{num_part} years" if num_part and "year" not in num_part.lower() else num_part
            found_matches.append((m.start(), formatted, full_match))
            
    if found_matches:
        found_matches.sort(key=lambda x: x[0])
        return found_matches[0][1]
        
    # 3. Entry Level / New Grad / Intern Detection
    if re.search(r'\b(?:internship|intern|trainee|apprentice|co-op)\b', clean, re.IGNORECASE):
        return "0-1 years (Internship)"
    if re.search(r'\b(?:new grad|university graduate|recent graduate|entry level|college grad)\b', clean, re.IGNORECASE):
        return "0-1 years (Entry Level)"

    # 4. Fallback based on explicit seniority level if available
    if level:
        if level in ["Senior", "Staff", "Principal", "Lead", "Architect"]:
            return f"5+ years ({level})"
        elif level in ["Junior", "Entry Level"]:
            return f"0-2 years ({level})"
        elif level in ["Mid-Level"]:
            return f"2-5 years ({level})"
            
    return None
