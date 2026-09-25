"""
Domain & Job Matching Engine for Active CRM Clients
Matches classified NormalizedJob records against CRM client domain specifications.
"""

import re
from typing import Optional, List, Set
from models.job import NormalizedJob
from classification.domains import IT_JOB_TAXONOMY


def tokenize_domain(domain_str: str) -> List[str]:
    """Tokenizes domain string into individual lowercase keywords."""
    clean = re.sub(r'[\s\-_/]+', ' ', domain_str.lower()).strip()
    return [w for w in clean.split() if w]


def does_job_match_client_domain(job: NormalizedJob, client_domain: str) -> bool:
    """
    Evaluates if a NormalizedJob matches a target client domain keyword/role.
    Checks:
    1. Direct match with job.job_domain, job.it_job_family, or job.job_domains
    2. Exact title token matching with client domain keywords
    3. Taxonomy alias / regex matching
    4. Skills and specializations matching
    """
    if not client_domain:
        return True

    domain_clean = client_domain.strip().lower()
    domain_normalized = re.sub(r'[\s\-_/]+', ' ', domain_clean)
    domain_tokens = tokenize_domain(client_domain)

    # Ignore generic filler words for matching
    significant_tokens = [t for t in domain_tokens if t not in ["a", "an", "the", "and", "or", "in", "for", "with", "of"]]
    if not significant_tokens:
        significant_tokens = domain_tokens

    title = (job.title or "").lower()
    dept = (job.department or "").lower()
    primary_domain = (job.job_domain or "").lower()
    family = (job.it_job_family or "").lower()
    secondaries = [d.lower() for d in (job.job_domains or [])]

    # 1. Exact match against Primary Domain or Family
    if domain_normalized == primary_domain or domain_normalized == family:
        return True

    if any(domain_normalized == s for s in secondaries):
        return True

    # 2. Check if all significant tokens from client domain are present in title
    if all(t in title for t in significant_tokens):
        return True

    # 3. Check Taxonomy Title Regexes for matching taxonomy domain
    for tax_domain, tax_info in IT_JOB_TAXONOMY.items():
        tax_norm = tax_domain.lower()
        if tax_norm == domain_normalized:
            for pattern in tax_info.get("titles", []):
                if re.search(pattern, title, re.IGNORECASE):
                    return True

    # 4. Check if core domain keywords (excluding generic 'engineer', 'developer', 'manager', 'lead') match
    role_types = {"engineer", "developer", "specialist", "architect", "lead", "manager", "director", "consultant", "analyst"}
    core_tokens = [t for t in significant_tokens if t not in role_types]

    if core_tokens:
        # All core technology/domain tokens MUST be matched
        core_in_title = all(t in title for t in core_tokens)
        if core_in_title and any(r in title for r in role_types if r in significant_tokens):
            return True
            
        skills_and_specs = f"{' '.join(job.skills).lower()} {' '.join(job.specializations).lower()} {primary_domain}"
        core_in_tech = all(t in skills_and_specs for t in core_tokens)
        if core_in_tech and any(r in title for r in role_types if r in significant_tokens):
            return True
    else:
        # Generic role without tech spec (e.g. 'Software Engineer')
        if all(t in title for t in significant_tokens):
            return True
        if domain_normalized == primary_domain:
            return True

    return False
