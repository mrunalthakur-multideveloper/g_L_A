"""
Weighted Evidence Scorer for IT Job Classification
Evaluates evidence across title, department, skills, and description to score primary and secondary domains.
Enforces the principle: Technology != Job Purpose (e.g. Data Scientist with Python != Python Developer).
"""

import re
from typing import Dict, List, Tuple, Any
from .domains import IT_JOB_TAXONOMY


# Explicit Role Purpose vs Implementation Language Priority
SPECIFIC_PURPOSE_DOMAINS = {
    "Machine Learning Engineer", "AI Engineer", "Generative AI / LLM Engineer",
    "Deep Learning / NLP / Computer Vision Engineer", "Research Scientist", "MLOps Engineer",
    "Data Scientist", "Data Engineer", "Data Analyst / BI Developer", "Database Engineer / DBA",
    "DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer (SRE)",
    "Platform / Infrastructure Engineer", "Cybersecurity Engineer", "SOC Analyst / Security Analyst",
    "QA / SDET Engineer", "Mobile Developer (iOS / Android)", "Embedded / Firmware Engineer",
    "Blockchain / Web3 Developer", "Game Developer", "Network Engineer",
    "Technical Product / Program Manager", "Software Architect"
}

GENERIC_LANGUAGE_DOMAINS = {
    "Python Developer", "Java Developer", "C++ Developer", "C#/.NET Developer",
    "Go Developer", "Rust Developer", "Ruby Developer", "PHP Developer", "Scala Developer",
    "JavaScript Developer", "TypeScript Developer"
}

# Precompile all domain title regexes once
COMPILED_TAXONOMY_TITLES = {}
for _domain, _cfg in IT_JOB_TAXONOMY.items():
    COMPILED_TAXONOMY_TITLES[_domain] = [re.compile(p, re.IGNORECASE) for p in _cfg["titles"]]

# Precompile specific purpose patterns
SPECIFIC_PURPOSE_COMPILED = []
for _spec in SPECIFIC_PURPOSE_DOMAINS:
    if _spec in COMPILED_TAXONOMY_TITLES:
        SPECIFIC_PURPOSE_COMPILED.extend(COMPILED_TAXONOMY_TITLES[_spec])


def score_domains(
    title: str,
    department: str = "",
    extracted_techs: Dict[str, List[str]] = None,
    specializations: List[str] = None,
    description: str = ""
) -> List[Tuple[str, float, str]]:
    """
    Scores all IT taxonomy domains against available evidence.
    Returns list of tuples: [(domain_name, score, reason), ...] sorted by score descending.
    """
    title_clean = (title or "").strip()
    dept_clean = (department or "").strip()
    dept_lower = dept_clean.lower()
    
    extracted_techs = extracted_techs or {}
    specializations = specializations or []
    
    all_extracted_flat = []
    for cat_items in extracted_techs.values():
        all_extracted_flat.extend(cat_items)
    all_extracted_set = set(all_extracted_flat)
    
    # Check once whether the title indicates a specific purpose role
    has_specific_title = any(p.search(title_clean) for p in SPECIFIC_PURPOSE_COMPILED)
    
    domain_scores = []
    
    for domain_name, config in IT_JOB_TAXONOMY.items():
        score = 0.0
        reasons = []
        title_patterns = COMPILED_TAXONOMY_TITLES[domain_name]
        
        # 1. Exact / Strong Title Match (+12 to +15)
        title_matched = False
        for p in title_patterns:
            if p.search(title_clean):
                raw_pat = p.pattern.lower()
                if any(lang in raw_pat for lang in ["java", "python", "react", "angular", "vue", "c++", "c#", "rust", "go", "node", "ruby", "php"]):
                    score += 15.0
                else:
                    score += 12.0
                title_matched = True
                reasons.append(f"Title matched '{p.pattern}'")
                break
                
        # 2. Department / Team Match (+8)
        if dept_lower:
            for p in title_patterns:
                if p.search(dept_clean):
                    score += 8.0
                    reasons.append(f"Department matched '{p.pattern}'")
                    break
            if config["family"].lower() in dept_lower:
                score += 5.0
                reasons.append(f"Department matches family '{config['family']}'")
                
        # 3. Technology / Language Matches (+6 per matching language/framework)
        matched_langs = [l for l in config.get("languages", []) if l in all_extracted_set]
        if matched_langs:
            score += min(len(matched_langs) * 6.0, 12.0)
            reasons.append(f"Languages: {', '.join(matched_langs)}")
            
        matched_frameworks = [f for f in config.get("frameworks", []) if f in all_extracted_set]
        if matched_frameworks:
            score += min(len(matched_frameworks) * 6.0, 12.0)
            reasons.append(f"Frameworks: {', '.join(matched_frameworks)}")
            
        # 4. Specialization Matches (+4 to +8)
        matched_specs = [s for s in config.get("specializations", []) if s in specializations]
        if matched_specs:
            score += min(len(matched_specs) * 4.0, 8.0)
            reasons.append(f"Specializations: {', '.join(matched_specs)}")
            
        # 5. Purpose Demotion for Generic Languages when Specific Purpose is Present
        if domain_name in GENERIC_LANGUAGE_DOMAINS and not title_matched and has_specific_title:
            score = min(score, 9.0)
                
        if score > 0:
            reason_summary = "; ".join(reasons)
            domain_scores.append((domain_name, score, reason_summary))
            
    domain_scores.sort(key=lambda x: x[1], reverse=True)
    return domain_scores
