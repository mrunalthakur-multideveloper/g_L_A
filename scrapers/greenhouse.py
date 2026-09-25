"""
Greenhouse ATS Scraper Adapter
Crawls public Greenhouse boards, extracts jobs with undisturbed descriptions, and converts to NormalizedJob.
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


def extract_greenhouse_logo(company_slug: str) -> Optional[str]:
    """Extract company logo from Greenhouse board HTML"""
    if company_slug in _LOGO_CACHE:
        return _LOGO_CACHE[company_slug]
    url = f"https://boards.greenhouse.io/{company_slug}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=2)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                _LOGO_CACHE[company_slug] = og["content"]
                return og["content"]
            img = soup.select_one("#logo img, .logo img, header img")
            if img and img.get("src"):
                _LOGO_CACHE[company_slug] = img["src"]
                return img["src"]
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


def scrape_greenhouse_company(
    slug: str,
    target_date: Optional[str] = None,
    last_24_hours: bool = False,
    hours_window: Optional[int] = None
) -> List[NormalizedJob]:
    """Scrapes all matching jobs for a Greenhouse company slug"""
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    
    jobs: List[NormalizedJob] = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_job_list = data.get("jobs", [])
            if not raw_job_list:
                return []

            logo = None
            
            for item in raw_job_list:
                location_name = item.get("location", {}).get("name") or ""
                
                # USA Location Filter
                if not is_us_location(location_name):
                    continue
                    
                # Date Filter
                updated_at = item.get("updated_at")
                if not matches_date_filter(updated_at, target_date=target_date, last_24_hours=last_24_hours, hours_window=hours_window):
                    continue

                if logo is None:
                    logo = extract_greenhouse_logo(slug)
                    
                city, state, country, is_remote = parse_us_location(location_name)
                raw_content = item.get("content") or ""
                plain_desc = clean_html_to_plain(raw_content)
                
                sal_min, sal_max, sal_curr, sal_text = extract_salary_range(plain_desc)
                auth = extract_work_auth(plain_desc)
                
                dept_name = None
                depts = item.get("departments")
                if depts and isinstance(depts, list) and len(depts) > 0:
                    dept_name = depts[0].get("name")
                    
                raw_id = str(item.get('id', ''))
                
                job = NormalizedJob(
                    id=raw_id,
                    job_id=raw_id,
                    source="greenhouse",
                    title=item.get("title") or "",
                    company_name=slug.replace("-", " ").title(),
                    company_logo=logo,
                    company_url=f"https://boards.greenhouse.io/{slug}",
                    department=dept_name,
                    location_display=location_name,
                    location_city=city,
                    location_state=state,
                    location_country="USA",
                    is_remote=is_remote,
                    date_posted=item.get("updated_at"),
                    job_url=item.get("absolute_url") or f"https://boards.greenhouse.io/{slug}/jobs/{item.get('id')}",
                    apply_url=item.get("absolute_url") or f"https://boards.greenhouse.io/{slug}/jobs/{item.get('id')}",
                    compensation_min=sal_min,
                    compensation_max=sal_max,
                    compensation_currency=sal_curr or "USD",
                    salary_text=sal_text,
                    sponsorship_h1b=auth,
                    search_keyword=slug,
                    description=plain_desc,
                    description_html=raw_content,
                    description_plain=plain_desc,
                    raw_data=json.dumps(item)
                )
                jobs.append(job)
    except Exception as e:
        # Graceful error handling
        pass
        
    return jobs
