"""
Domain & Job Matching Engine for Active CRM Clients
Implements Two Distinct Scraping Modes:
  Mode 1: Title-Driven Scraper (desired_job_titles matching)
  Mode 2: Keyword & Description-Driven Scraper (keywords retrieval + 5-Keyword Gatekeeper)
"""

import re
import html
from typing import Optional, List, Set, Tuple
from models.job import NormalizedJob
from classification.domains import IT_JOB_TAXONOMY


def clean_description_for_gatekeeper(desc: Optional[str]) -> str:
    """
    Cleans raw job description for Gatekeeper evaluation:
    - Decodes HTML entities (e.g. &amp;, &lt;, &#39;)
    - Strips all HTML tags
    - Converts to lowercase
    - Normalizes multiple spaces/newlines
    """
    if not desc:
        return ""
    text = html.unescape(str(desc))
    text = html.unescape(text)  # Nested entities
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[\s\u00a0\u200b\u202f]+', ' ', text)
    return text.strip().lower()


def match_keyword_in_text(keyword: str, text: str) -> bool:
    """
    Checks if a keyword appears in text using whole-word boundary matching.
    Safely accommodates technical terms with symbols (e.g. C++, C#, .NET, Node.js, Vue.js).
    """
    kw_clean = keyword.strip().lower()
    if not kw_clean:
        return False

    # Dynamic boundary depending on whether keyword starts/ends with word character
    prefix = r'\b' if re.match(r'^\w', kw_clean) else r'(?:^|[\s\(\[\{<"\'/\\.,;:])'
    suffix = r'\b' if re.search(r'\w$', kw_clean) else r'(?:$|[\s\)\]\}>"\'/\\.,;!?:])'
    pattern = rf"{prefix}{re.escape(kw_clean)}{suffix}"

    return bool(re.search(pattern, text, re.IGNORECASE))


def match_job_by_titles(job: NormalizedJob, desired_job_titles: List[str]) -> bool:
    """
    Mode 1: Title-Driven Scraper Matching Rule.
    Matches jobs where the job title matches any title in the client's desired_job_titles array.
    Uses case-insensitive phrase and boundary matching.
    """
    if not desired_job_titles:
        return False

    job_title = (job.title or "").strip().lower()
    if not job_title:
        return False

    # Normalize hyphens and slashes for title matching (e.g., "Front-End" -> "Front End")
    job_title_norm = re.sub(r'[\-_/]+', ' ', job_title)
    job_title_norm = re.sub(r'\s+', ' ', job_title_norm)

    for target_title in desired_job_titles:
        if not target_title:
            continue
        target_clean = str(target_title).strip().lower()
        if not target_clean:
            continue

        target_norm = re.sub(r'[\-_/]+', ' ', target_clean)
        target_norm = re.sub(r'\s+', ' ', target_norm)

        # 1. Exact match
        if target_norm == job_title_norm:
            return True

        # 2. Word boundary match
        pattern = rf"\b{re.escape(target_norm)}\b"
        if re.search(pattern, job_title_norm, re.IGNORECASE):
            return True

        # 3. Handle common role variations (Frontend vs Front End, Fullstack vs Full Stack)
        compact_target = target_norm.replace(" ", "")
        compact_job_title = job_title_norm.replace(" ", "")
        if compact_target and compact_target in compact_job_title:
            # Verify significant words to prevent false positives
            target_words = [w for w in target_norm.split() if len(w) > 2]
            if all(w in job_title_norm for w in target_words):
                return True

    return False


def match_job_by_keywords_gatekeeper(
    job: NormalizedJob,
    keywords: List[str],
    min_threshold: int = 5
) -> Tuple[bool, List[str], int]:
    """
    Mode 2: Keyword & Description-Driven Scraper Matching Rule.
    Step 1: Candidate Retrieval - Candidate jobs matching ANY keyword from the client's keywords array.
    Step 2: Strict Description Gatekeeper - Clean description text (strip HTML, lowercase) and check
            against client's exact keywords array.
            Count distinct matched keywords using whole-word boundary matching (\\bkeyword\\b).
            THRESHOLD RULE: If distinct matched keywords >= min_threshold (default: 5), ACCEPT the job.
            Otherwise DISCARD.

    Returns:
        (is_accepted, matched_keywords_list, distinct_count)
    """
    if not keywords:
        return False, [], 0

    raw_desc = job.description or job.description_plain or job.description_html or ""
    clean_desc = clean_description_for_gatekeeper(raw_desc)
    title_lower = (job.title or "").strip().lower()
    dept_lower = (job.department or "").strip().lower()

    # Step 1: Candidate Retrieval - Must match ANY keyword in title, dept, or description
    has_candidate_hit = False
    for kw in keywords:
        if not kw:
            continue
        kw_lower = kw.strip().lower()
        if not kw_lower:
            continue
        if kw_lower in title_lower or kw_lower in dept_lower or kw_lower in clean_desc:
            has_candidate_hit = True
            break

    if not has_candidate_hit:
        return False, [], 0

    # Step 2: Strict Description Gatekeeper (Distinct Keyword Counting)
    distinct_matched_keywords: List[str] = []
    seen_matched_lower: Set[str] = set()

    for kw in keywords:
        if not kw:
            continue
        kw_clean = kw.strip()
        kw_lower = kw_clean.lower()
        if not kw_lower or kw_lower in seen_matched_lower:
            continue

        if match_keyword_in_text(kw_clean, clean_desc):
            seen_matched_lower.add(kw_lower)
            distinct_matched_keywords.append(kw_clean)

    distinct_count = len(distinct_matched_keywords)

    # THRESHOLD RULE: Must contain AT LEAST min_threshold distinct keywords
    if distinct_count >= min_threshold:
        return True, distinct_matched_keywords, distinct_count

    return False, distinct_matched_keywords, distinct_count


def tokenize_domain(domain_str: str) -> List[str]:
    """Tokenizes domain string into individual lowercase keywords."""
    clean = re.sub(r'[\s\-_/]+', ' ', domain_str.lower()).strip()
    return [w for w in clean.split() if w]


def does_job_match_client_domain(job: NormalizedJob, client_domain: str) -> bool:
    """
    Legacy Domain Matcher (Maintained for backwards compatibility).
    Evaluates if a NormalizedJob matches a target client domain keyword/role.
    """
    if not client_domain:
        return True

    domain_clean = client_domain.strip().lower()
    domain_normalized = re.sub(r'[\s\-_/]+', ' ', domain_clean)
    domain_tokens = tokenize_domain(client_domain)

    significant_tokens = [t for t in domain_tokens if t not in ["a", "an", "the", "and", "or", "in", "for", "with", "of"]]
    if not significant_tokens:
        significant_tokens = domain_tokens

    title = (job.title or "").lower()
    primary_domain = (job.job_domain or "").lower()
    family = (job.it_job_family or "").lower()
    secondaries = [d.lower() for d in (job.job_domains or [])]

    if domain_normalized == primary_domain or domain_normalized == family:
        return True

    if any(domain_normalized == s for s in secondaries):
        return True

    if all(t in title for t in significant_tokens):
        return True

    for tax_domain, tax_info in IT_JOB_TAXONOMY.items():
        tax_norm = tax_domain.lower()
        if tax_norm == domain_normalized:
            for pattern in tax_info.get("titles", []):
                if re.search(pattern, title, re.IGNORECASE):
                    return True

    role_types = {"engineer", "developer", "specialist", "architect", "lead", "manager", "director", "consultant", "analyst"}
    core_tokens = [t for t in significant_tokens if t not in role_types]

    if core_tokens:
        core_in_title = all(t in title for t in core_tokens)
        if core_in_title and any(r in title for r in role_types if r in significant_tokens):
            return True
            
        skills_and_specs = f"{' '.join(job.skills).lower()} {' '.join(job.specializations).lower()} {primary_domain}"
        core_in_tech = all(t in skills_and_specs for t in core_tokens)
        if core_in_tech and any(r in title for r in role_types if r in significant_tokens):
            return True
    else:
        if all(t in title for t in significant_tokens):
            return True
        if domain_normalized == primary_domain:
            return True

    return False
