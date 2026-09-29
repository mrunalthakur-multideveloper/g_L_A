"""
Job Enrichment and Field Standardization Engine
Ensures 100% of NormalizedJob attributes and database columns are fully populated:
- Seniority Level (job_level)
- Experience text and numeric ranges (experience, experience_min, experience_max)
- Job Employment Type (job_type)
- Location parsing (location_city, location_state, location_country, is_remote)
- Company URL & Company Logo
- Department & Job Function
- Industry & Sector Classification
- Compensation (min, max, currency, interval, salary_text)
- Email addresses extraction
- Technology and skill categorization
"""

import re
import json
import html
from typing import Tuple, Optional, List, Dict, Any

from models.job import NormalizedJob
from classification.seniority import detect_seniority
from classification.experience import extract_experience
from classification.technology_extractor import extract_technologies, extract_specializations
from filters.usa import parse_us_location
from filters.country import parse_country_location


def parse_experience_range(exp_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """
    Parses numeric min and max years of experience from experience strings.
    Examples:
      '3-5 years' -> (3, 5)
      '5+ years' -> (5, None)
      '0-1 years (Internship)' -> (0, 1)
      '0-2 years (Entry Level)' -> (0, 2)
      '3 to 6 years' -> (3, 6)
      '7 years' -> (7, 7)
    """
    if not exp_str:
        return None, None

    clean = str(exp_str).strip()

    # Pattern: 3-5 or 3 to 5 or 3–5
    m_range = re.search(r'(\d{1,2})\s*(?:-|–|—|\s*to\s*)\s*(\d{1,2})', clean)
    if m_range:
        try:
            v1 = int(m_range.group(1))
            v2 = int(m_range.group(2))
            return min(v1, v2), max(v1, v2)
        except (ValueError, TypeError):
            pass

    # Pattern: 5+ or 5 +
    m_plus = re.search(r'(\d{1,2})\s*\+', clean)
    if m_plus:
        try:
            return int(m_plus.group(1)), None
        except (ValueError, TypeError):
            pass

    # Pattern: single number followed by year(s)
    m_single = re.search(r'(\d{1,2})\s*(?:years?|yrs?)', clean, re.IGNORECASE)
    if m_single:
        try:
            v = int(m_single.group(1))
            return v, v
        except (ValueError, TypeError):
            pass

    return None, None


def extract_emails_from_text(text: str) -> List[str]:
    """
    Extracts valid contact, recruiting, or inquiry email addresses from job posting text.
    Filters out noise, dummy templates, and image extensions.
    """
    if not text:
        return []

    raw = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    valid = []
    seen = set()
    skip_domains = {"example.com", "domain.com", "sentry.io", "w3.org", "schema.org", "github.com", "google.com"}
    skip_prefixes = {"noreply", "no-reply", "donotreply", "test", "user"}

    for item in raw:
        e = item.strip().lower().rstrip('.,;:)]}\'"')
        parts = e.split('@')
        if len(parts) != 2:
            continue
        user, domain = parts
        if domain in skip_domains or any(bad in domain for bad in ["example", "sentry", "png", "jpg", "gif"]):
            continue
        if user in skip_prefixes:
            continue
        if len(e) >= 6 and e not in seen:
            seen.add(e)
            valid.append(e)

    return valid


def detect_job_type(title: str, text: str, existing: Optional[str] = None) -> str:
    """
    Standardizes employment type (Full-time, Part-time, Contract, Internship).
    """
    if existing and existing.strip():
        et = existing.strip().lower()
        if "full" in et:
            return "Full-time"
        if "part" in et:
            return "Part-time"
        if "contract" in et or "temp" in et or "c2c" in et or "w2" in et:
            return "Contract"
        if "intern" in et or "co-op" in et:
            return "Internship"
        return existing.strip().title()

    combined = f"{title} {text}".lower()
    if re.search(r'\b(?:internship|intern|trainee|apprentice|co-op)\b', combined):
        return "Internship"
    if re.search(r'\b(?:contract|contractor|c2c|w2\s*contract|freelance|temp|temporary)\b', combined):
        return "Contract"
    if re.search(r'\b(?:part-time|part\s*time)\b', combined):
        return "Part-time"
    return "Full-time"


def detect_seniority_level(title: str, desc: str, existing_level: Optional[str] = None, exp: Optional[str] = None) -> str:
    """
    Resolves seniority level: VP, Executive, Director, Manager, Principal, Staff,
    Lead, Architect, Senior, Mid-Level, Junior, Entry Level, Intern.
    """
    lvl = detect_seniority(title, existing_level)
    if lvl:
        return lvl

    # Fallback to experience
    if exp:
        min_yrs, _ = parse_experience_range(exp)
        if min_yrs is not None:
            if min_yrs >= 5:
                return "Senior"
            if min_yrs >= 2:
                return "Mid-Level"
            if min_yrs >= 0:
                return "Entry Level"

    title_lower = (title or "").lower()
    if any(k in title_lower for k in ["senior", "sr.", "sr ", "lead", "principal", "staff"]):
        return "Senior"
    if any(k in title_lower for k in ["junior", "jr.", "jr ", "entry", "associate", "intern"]):
        return "Entry Level"

    return "Mid-Level"


def detect_company_industry(title: str, desc: str, existing_industry: Optional[str] = None) -> str:
    """
    Detects realistic company industry based on keywords and role context.
    """
    if existing_industry and existing_industry.strip():
        return existing_industry.strip()

    t = f"{title} {desc[:2000]}".lower()
    if any(k in t for k in ["fintech", "financial", "banking", "payments", "trading", "crypto", "blockchain", "insurance", "capital"]):
        return "Financial Services & Fintech"
    if any(k in t for k in ["healthcare", "health", "medical", "clinical", "hospital", "patient", "biotech", "pharma", "therapeutics"]):
        return "Healthcare & Life Sciences"
    if any(k in t for k in ["security", "cyber", "infosec", "threat", "soc", "compliance", "fraud", "zero trust"]):
        return "Cybersecurity & Information Security"
    if any(k in t for k in ["ecommerce", "e-commerce", "retail", "marketplace", "consumer goods", "logistics", "supply chain"]):
        return "E-Commerce & Retail Technology"
    if any(k in t for k in ["automotive", "autonomous", "vehicle", "aerospace", "defense", "hardware"]):
        return "Defense & Advanced Technologies"
    if any(k in t for k in ["artificial intelligence", "machine learning", "deep learning", "llm", "genai", "computer vision"]):
        return "Artificial Intelligence & Machine Learning"
    if any(k in t for k in ["cloud", "saas", "infrastructure", "devops", "platform", "software", "data"]):
        return "Information Technology & Cloud Services"

    return "Technology, Information and Internet"


def detect_job_function(job: NormalizedJob) -> str:
    """
    Resolves job function or department hierarchy.
    """
    if job.department and job.department.strip():
        return job.department.strip()
    if job.job_function and job.job_function.strip():
        return job.job_function.strip()
    if job.it_job_family and job.it_job_family.strip():
        return job.it_job_family.strip()
    if job.job_domain and job.job_domain.strip():
        return job.job_domain.strip()

    t = (job.title or "").lower()
    if any(k in t for k in ["front", "react", "vue", "angular", "ui", "web"]):
        return "Frontend Engineering"
    if any(k in t for k in ["back", "python", "golang", "java", "api", "node"]):
        return "Backend Engineering"
    if any(k in t for k in ["full", "fullstack", "stack"]):
        return "Full Stack Engineering"
    if any(k in t for k in ["data", "etl", "analytics", "bi", "warehouse", "dba", "database"]):
        return "Data Engineering & Analytics"
    if any(k in t for k in ["devops", "sre", "cloud", "infra", "infrastructure", "platform", "kubernetes"]):
        return "DevOps & Cloud Engineering"
    if any(k in t for k in ["security", "cyber", "infosec"]):
        return "Information Security"
    if any(k in t for k in ["qa", "test", "quality", "sdet"]):
        return "Quality Assurance & Testing"
    if any(k in t for k in ["product manager", "product owner"]):
        return "Product Management"

    return "Software Engineering"


def extract_salary_info(text: str) -> Tuple[Optional[float], Optional[float], str, str, Optional[str]]:
    """
    Extracts compensation_min, compensation_max, currency, interval, and salary_text.
    Supports $, €, £, USD, EUR, GBP, annual and hourly rates.
    """
    if not text:
        return None, None, "USD", "yearly", None

    currency = "USD"
    if "€" in text or " eur " in text.lower() or " euro" in text.lower():
        currency = "EUR"
    elif "£" in text or " gbp " in text.lower():
        currency = "GBP"

    # Pattern 1: $120,000 - $180,000 or $120k - $180k or €60,000 - 80,000
    p1 = r'([$€£])\s*(\d{2,3}(?:,\d{3})?|\d{2,3}[kK])\s*(?:-|–|—|\s*to\s*)\s*[$€£]?\s*(\d{2,3}(?:,\d{3})?|\d{2,3}[kK])'
    m1 = re.search(p1, text)
    if m1:
        sym = m1.group(1)
        cur = "EUR" if sym == "€" else ("GBP" if sym == "£" else "USD")
        raw_v1 = m1.group(2).replace(',', '').replace('K', '000').replace('k', '000')
        raw_v2 = m1.group(3).replace(',', '').replace('K', '000').replace('k', '000')
        try:
            v1 = float(raw_v1)
            v2 = float(raw_v2)
            context = text[max(0, m1.start() - 25):min(len(text), m1.end() + 35)].lower()
            interval = "hourly" if any(w in context for w in ["hour", "/hr", "per hour"]) else "yearly"
            sal_text = f"{sym}{v1:,.0f} - {sym}{v2:,.0f}/{interval}"
            return min(v1, v2), max(v1, v2), cur, interval, sal_text
        except (ValueError, TypeError):
            pass

    # Pattern 2: $150,000 / year or $65 / hr
    p2 = r'([$€£])\s*(\d{2,3}(?:,\d{3})?|\d{2,3}[kK])\s*(?:/|\s+a\s+|\s+per\s+)(year|annum|yr|hour|hr)'
    m2 = re.search(p2, text, re.IGNORECASE)
    if m2:
        sym = m2.group(1)
        cur = "EUR" if sym == "€" else ("GBP" if sym == "£" else "USD")
        raw_v = m2.group(2).replace(',', '').replace('K', '000').replace('k', '000')
        unit = m2.group(3).lower()
        interval = "hourly" if "h" in unit else "yearly"
        try:
            v = float(raw_v)
            sal_text = f"{sym}{v:,.0f}/{interval}"
            return v, v, cur, interval, sal_text
        except (ValueError, TypeError):
            pass

    return None, None, currency, "yearly", None


def extract_board_slug(job: NormalizedJob) -> str:
    """Extracts ATS company slug from URLs or company name."""
    url = job.job_url or job.apply_url or ""
    m = re.search(r'(?:greenhouse\.io|lever\.co|ashbyhq\.com)/([^/?#]+)', url)
    if m:
        return m.group(1).strip()
    if job.search_keyword and " " not in job.search_keyword:
        return job.search_keyword.strip().lower()
    if job.company_name:
        return re.sub(r'[^a-zA-Z0-9]+', '', job.company_name).lower()
    return ""


def enrich_job(job: NormalizedJob) -> NormalizedJob:
    """
    Enriches all missing or partial fields in a NormalizedJob object in-place:
    1. Extracts/cleans plain text description
    2. Populates Seniority (job_level) & Experience (experience, experience_min, experience_max)
    3. Resolves Job Type (job_type)
    4. Resolves Location (location_city, location_state, location_country, is_remote)
    5. Resolves Company URL & Logo
    6. Extracts Emails
    7. Resolves Compensation (min, max, currency, interval, salary_text)
    8. Enriches Industry & Job Function
    9. Extracts Skills & Technologies
    """
    desc = job.description or job.description_plain or job.description_html or ""
    title = job.title or ""

    # 1. Location Standardization
    loc_display = job.location_display or ""
    if not job.location_country or job.location_country.upper() in ["US", "USA", "UNITED STATES"]:
        if "ireland" in loc_display.lower() or any(c in loc_display.lower() for c in ["dublin", "cork", "galway", "limerick"]):
            job.location_country = "Ireland"
        else:
            job.location_country = "USA"

    if (
        "remote" in loc_display.lower()
        or "remote" in title.lower()
        or bool(re.search(r'\b(?:100%\s*remote|fully\s*remote|remote\s*optional|remote\s*friendly|work\s*from\s*home|wfh)\b', desc, re.IGNORECASE))
    ):
        job.is_remote = True

    if not job.location_city:
        if job.location_country == "Ireland":
            city, state, _, r = parse_country_location(loc_display, target_country="Ireland")
            job.location_city = city or (loc_display.split(',')[0].strip() if loc_display else "Dublin")
        else:
            city, state, _, r = parse_us_location(loc_display)
            job.location_city = city or (loc_display.split(',')[0].strip() if loc_display else None)
            if not job.location_state:
                job.location_state = state

    if not job.location_city and job.is_remote:
        job.location_city = "Remote"

    # 2. Seniority & Experience
    if not job.experience:
        job.experience = extract_experience(desc, title=title, level=job.job_level)

    job.job_level = detect_seniority_level(title, desc, existing_level=job.job_level, exp=job.experience)

    exp_min, exp_max = parse_experience_range(job.experience)
    job.experience_min = exp_min
    job.experience_max = exp_max

    # 3. Employment Type
    if not job.job_type:
        job.job_type = detect_job_type(title, desc)

    # 4. Compensation
    if not job.salary_text or job.compensation_min is None:
        c_min, c_max, cur, interval, s_text = extract_salary_info(desc)
        if s_text:
            job.salary_text = s_text
            job.compensation_min = c_min
            job.compensation_max = c_max
            job.compensation_currency = cur
            job.compensation_interval = interval

    if not job.compensation_currency:
        job.compensation_currency = "EUR" if job.location_country == "Ireland" else "USD"
    if not job.compensation_interval:
        job.compensation_interval = "yearly"

    # 5. Emails Extraction
    if not job.emails:
        job.emails = extract_emails_from_text(f"{desc} {job.description_html or ''}")

    # 6. Company URL & Logo
    slug = extract_board_slug(job)
    if not job.company_url and slug:
        if job.source == "lever":
            job.company_url = f"https://jobs.lever.co/{slug}"
        elif job.source == "ashby":
            job.company_url = f"https://jobs.ashbyhq.com/{slug}"
        else:
            job.company_url = f"https://boards.greenhouse.io/{slug}"

    if not job.company_logo and slug:
        job.company_logo = f"https://logo.clearbit.com/{slug}.com"

    # 7. Industry & Job Function
    if not job.company_industry:
        job.company_industry = detect_company_industry(title, desc)

    if not job.job_function:
        job.job_function = detect_job_function(job)

    # 8. Technologies & Skills extraction if empty
    if not job.skills:
        tech_dict = extract_technologies(f"{title}\n{desc}")
        specs = extract_specializations(f"{title}\n{desc}")
        skills_set = set()
        for cat_list in tech_dict.values():
            skills_set.update(cat_list)
        skills_set.update(specs)
        job.skills = sorted(list(skills_set))

    # 9. Sponsorship fallback
    if not job.sponsorship_h1b:
        job.sponsorship_h1b = "No"

    return job
