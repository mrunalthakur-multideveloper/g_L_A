"""
Seniority Level Classifier
Determines role seniority from job title and level indicators.
Does not infer seniority solely from experience if clear title level exists.
"""

import re
from typing import Optional

SENIORITY_PATTERNS = [
    (r'\b(?:executive\s*vice\s*president|evp|senior\s*vice\s*president|svp|vice\s*president|vp)\b', "VP"),
    (r'\b(?:c-level|cto|cio|ciso|chief\s*technology\s*officer|chief\s*information\s*officer)\b', "Executive"),
    (r'\b(?:director\s*of|senior\s*director|director)\b', "Director"),
    (r'\b(?:head\s*of)\b', "Head"),
    (r'\b(?:engineering\s*manager|software\s*manager|devops\s*manager|manager)\b', "Manager"),
    (r'\b(?:distinguished\s*engineer|distinguished|fellow)\b', "Distinguished"),
    (r'\b(?:principal\s*engineer|principal\s*developer|principal|founding\s*engineer)\b', "Principal"),
    (r'\b(?:staff\s*engineer|staff\s*developer|staff)\b', "Staff"),
    (r'\b(?:lead\s*engineer|lead\s*developer|tech\s*lead|technical\s*lead|team\s*lead|lead)\b', "Lead"),
    (r'\b(?:architect|solutions\s*architect|software\s*architect|enterprise\s*architect)\b', "Architect"),
    (r'\b(?:senior\s*iii|senior\s*ii|senior\s*i|senior|sr\b|sr\.)\b', "Senior"),
    (r'\b(?:mid-level|mid\s*level|intermediate|experienced)\b', "Mid-Level"),
    (r'\b(?:associate\s*engineer|associate\s*developer|associate)\b', "Associate"),
    (r'\b(?:junior\s*engineer|junior\s*developer|junior|jr\b|jr\.)\b', "Junior"),
    (r'\b(?:entry-level|entry\s*level|graduate|new\s*grad|university\s*grad)\b', "Entry Level"),
    (r'\b(?:internship|intern|trainee|apprentice|co-op)\b', "Intern")
]


def detect_seniority(title: str, level_hint: Optional[str] = None) -> Optional[str]:
    """Detect seniority level from title or level hints"""
    if not title and not level_hint:
        return None
        
    text = f"{title or ''} {level_hint or ''}".lower()
    
    for pattern, level_name in SENIORITY_PATTERNS:
        if re.search(pattern, text):
            return level_name
            
    return None
