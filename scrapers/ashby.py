"""
Ashby ATS Scraper Adapter
Crawls public Ashby job postings, extracts jobs with undisturbed descriptions, and converts to NormalizedJob.
"""

import urllib.request
import json
import time
import re
import html
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from models.job import NormalizedJob
from filters.usa import is_us_location, parse_us_location
from filters.date import matches_date_filter

_LOGO_CACHE = {}


def extract_ashby_logo(company_slug: str) -> Optional[str]:
    """Extract company logo from Ashby board HTML"""
    if company_slug in _LOGO_CACHE:
        return _LOGO_CACHE[company_slug]
    url = f"https://jobs.ashbyhq.com/{company_slug}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=2)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                _LOGO_CACHE[company_slug] = og["content"]
                return og["content"]
    except Exception:
        pass
    _LOGO_CACHE[company_slug] = None
    return None


def clean_html_to_plain(raw_html: str) -> str:
    """Helper to convert HTML to 100% clean, human-readable plain text without any HTML entities or leftover tags"""
    if not raw_html:
        return ""
    text = html.unescape(str(raw_html))
    text = html.unescape(text)  # Nested entities
    text = re.sub(r'[\u202f\u00a0\u200b\ufeff\u200e\u2028\u2029]+', ' ', text)
    text = re.sub(r'&(?:nbsp|amp|quot|#39|#039|lt|gt);?', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*li[^>]*>', '• ', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*li\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*(?:p|div|h[1-6]|tr|blockquote|section)\s*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[ \t\u202f\u00a0]+', ' ', text)
    text = re.sub(r'\n[ \t\u202f\u00a0]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_salary_range(text: str):
    """Extract salary min, max, interval from text"""
    if not text:
        return None, None, None, None
    text_lower = text.lower()
    matches = re.findall(r'\$\s*(\d{2,3}(?:,\d{3})?|\d{2,3}[kK])\s*(?:-|–|to)\s*\$\s*(\d{2,3}(?:,\d{3})?|\d{2,3}[kK])', text)
    if matches:
        m = matches[0]
        v1 = float(m[0].replace(',', '').replace('K', '000').replace('k', '000'))
        v2 = float(m[1].replace(',', '').replace('K', '000').replace('k', '000'))
        interval = "hourly" if "hour" in text_lower or "/hr" in text_lower else "annual"
        sal_text = f"${v1:,.0f} - ${v2:,.0f}/{interval}"
        return min(v1, v2), max(v1, v2), "USD", sal_text
    return None, None, None, None


def extract_work_auth(text: str) -> str:
    """Extract H1B visa sponsorship indicator"""
    if not text:
        return "No"
    t = text.lower()
    if any(k in t for k in ["h1b", "h-1b", "visa sponsorship", "will sponsor", "provides sponsorship", "eligible for sponsorship"]):
        return "Yes"
    if any(k in t for k in ["no visa sponsorship", "does not sponsor", "cannot sponsor", "unable to sponsor", "must be a us citizen"]):
        return "No"
    if any(k in t for k in ["opt", "cpt", "case by case", "may consider sponsorship", "tn visa"]):
        return "Maybe"
    return "No"


def scrape_ashby_company(
    slug: str,
    target_date: Optional[str] = None,
    last_24_hours: bool = False,
    hours_window: Optional[int] = None
) -> List[NormalizedJob]:
    """Scrapes all matching jobs for an Ashby company slug"""
    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json"})
    
    jobs: List[NormalizedJob] = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            job_list = data.get("jobs", []) or data.get("jobPostings", [])
            if not job_list:
                return []

            logo = None
            
            for item in job_list:
                location_name = item.get("location") or ""
                address_dict = item.get("address") or {}
                secondary_locs = item.get("secondaryLocations") or []
                
                # USA Location Filter
                if not is_us_location(location_name, address_dict, secondary_locs):
                    continue
                    
                # Date Filter
                published_at = item.get("publishedAt")
                if not matches_date_filter(published_at, target_date=target_date, last_24_hours=last_24_hours, hours_window=hours_window):
                    continue

                if logo is None:
                    logo = extract_ashby_logo(slug)
                    
                city, state, country, is_remote = parse_us_location(location_name)
                if item.get("isRemote"):
                    is_remote = True
                    
                raw_html = item.get("descriptionHtml") or ""
                plain_desc = clean_html_to_plain(raw_html) or item.get("descriptionPlain") or ""
                
                sal_min, sal_max, sal_curr, sal_text = extract_salary_range(plain_desc)
                
                # Supplement structured compensation summary if present
                comp = item.get("compensation") or {}
                if not sal_text and isinstance(comp, dict):
                    c_summary = comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary")
                    if c_summary:
                        sal_text = c_summary
                        
                auth = extract_work_auth(plain_desc)
                dept = item.get("department") or item.get("team")
                raw_id = str(item.get('id', ''))
                
                job = NormalizedJob(
                    id=raw_id,
                    job_id=raw_id,
                    source="ashby",
                    title=item.get("title") or "",
                    company_name=slug.replace("-", " ").title(),
                    company_logo=logo,
                    company_url=f"https://jobs.ashbyhq.com/{slug}",
                    department=dept,
                    job_type=item.get("employmentType"),
                    location_display=location_name,
                    location_city=city,
                    location_state=state,
                    location_country="USA",
                    is_remote=is_remote,
                    date_posted=str(item.get("publishedAt")),
                    job_url=item.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{item.get('id')}",
                    apply_url=item.get("applyUrl") or f"https://jobs.ashbyhq.com/{slug}/{item.get('id')}/application",
                    compensation_min=sal_min,
                    compensation_max=sal_max,
                    compensation_currency=sal_curr or "USD",
                    salary_text=sal_text,
                    sponsorship_h1b=auth,
                    search_keyword=slug,
                    description=plain_desc,
                    description_html=raw_html,
                    description_plain=item.get("descriptionPlain"),
                    raw_data=json.dumps(item)
                )
                jobs.append(job)
    except Exception:
        pass
        
    return jobs
