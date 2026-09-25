"""
Master IT Job Classification Engine
Orchestrates Non-IT filtering, family classification, primary/secondary domain scoring,
technology extraction, specialization detection, seniority detection, and confidence calculation.
"""

from typing import Optional, Dict, Any, List
from models.job import NormalizedJob
from .non_it import evaluate_non_it_purpose
from .domains import IT_JOB_TAXONOMY
from .technology_extractor import extract_technologies, extract_specializations
from .seniority import detect_seniority
from .experience import extract_experience
from .scorer import score_domains
from .ai_fallback import classify_with_ai


def classify_job(job: NormalizedJob) -> NormalizedJob:
    """
    Executes the comprehensive multi-level IT classification pipeline on a NormalizedJob.
    Mutates and returns the NormalizedJob with all classification fields populated.
    """
    title = job.title or ""
    dept = job.department or ""
    desc = job.description or job.description_plain or ""
    
    # 1. Non-IT Gate Evaluation (Fast first check)
    is_non_it, non_it_reason = evaluate_non_it_purpose(title, dept, desc)
    if is_non_it:
        job.is_it_job = False
        job.it_job_family = None
        job.job_domain = None
        job.job_domains = []
        job.classification_confidence = 0.95
        job.classification_method = "rules"
        job.classification_reason = non_it_reason
        return job

    # 2. Seniority & Experience Detection
    job.job_level = detect_seniority(title, job.job_level)
    if not job.experience:
        job.experience = extract_experience(desc, title=title, level=job.job_level)
    
    # 3. Extract Technologies & Specializations
    full_text = f"{title}\n{dept}\n{desc}"
    job.technologies = extract_technologies(full_text)
    job.specializations = extract_specializations(full_text)
    
    # Merge extracted languages/frameworks into job.skills
    detected_skills_flat = []
    for cat_items in job.technologies.values():
        detected_skills_flat.extend(cat_items)
    for s in job.specializations:
        detected_skills_flat.append(s)
    # Deduplicate while preserving order
    for sk in detected_skills_flat:
        if sk not in job.skills:
            job.skills.append(sk)

    # 4. Score IT Domains
    ranked_domains = score_domains(
        title=title,
        department=dept,
        extracted_techs=job.technologies,
        specializations=job.specializations,
        description=desc
    )
    
    if ranked_domains:
        top_domain, top_score, top_reason = ranked_domains[0]
        
        # Primary domain threshold
        if top_score >= 8.0:
            job.is_it_job = True
            job.job_domain = top_domain
            job.it_job_family = IT_JOB_TAXONOMY[top_domain]["family"]
            
            # Secondary domains (up to 5 other high scoring matches)
            secondaries = [d[0] for d in ranked_domains[1:6] if d[1] >= 6.0 and d[0] != top_domain]
            job.job_domains = secondaries
            
            # Confidence calculation based on score strength
            if top_score >= 18.0:
                job.classification_confidence = 0.98
            elif top_score >= 12.0:
                job.classification_confidence = 0.90
            elif top_score >= 8.0:
                job.classification_confidence = 0.80
            else:
                job.classification_confidence = 0.65
                
            job.classification_method = "rules"
            job.classification_reason = f"Primary: {top_domain} ({top_reason})"
            return job

    # 5. Low Confidence / Ambiguous Fallback
    ai_result = classify_with_ai(title, dept, job.skills, desc)
    if ai_result and ai_result.get("is_it_job") is not None:
        job.is_it_job = bool(ai_result.get("is_it_job"))
        job.it_job_family = ai_result.get("job_family")
        job.job_domain = ai_result.get("primary_domain")
        job.job_domains = ai_result.get("secondary_domains", [])
        job.classification_confidence = float(ai_result.get("confidence", 0.85))
        job.classification_method = "ai_fallback"
        job.classification_reason = ai_result.get("reason", "Classified via AI fallback model")
        return job

    # 6. Default Fallback if completely ambiguous
    # If title has any tech keyword, classify generically
    if ranked_domains and ranked_domains[0][1] >= 4.0:
        top_domain = ranked_domains[0][0]
        job.is_it_job = True
        job.job_domain = top_domain
        job.it_job_family = IT_JOB_TAXONOMY[top_domain]["family"]
        job.job_domains = [d[0] for d in ranked_domains[1:4] if d[0] != top_domain]
        job.classification_confidence = 0.55
        job.classification_method = "rules_low_confidence"
        job.classification_reason = f"Low confidence match: {ranked_domains[0][2]}"
    else:
        job.is_it_job = False
        job.it_job_family = None
        job.job_domain = None
        job.job_domains = []
        job.classification_confidence = 0.50
        job.classification_method = "rules_unclassified"
        job.classification_reason = "Insufficient technical evidence found in title or description"
        
    return job
