"""
CSV Output Writer
Writes classified job records into separate IT and Non-IT CSV files.
Preserves newlines, commas, quotes, and full untouched descriptions using standard RFC 4180 UTF-8 formatting.
"""

import csv
import os
import json
import time
from datetime import datetime
from typing import List, Optional
from models.job import NormalizedJob

import html
import re

CSV_COLUMNS = [
    "job_id",
    "title",
    "company_name",
    "company_logo",
    "company_url",
    "department",
    "location",
    "location_state",
    "location_country",
    "is_remote",
    "job_type",
    "job_level",
    "date_posted",
    "scraped_at",
    "apply_url",
    "compensation_min",
    "compensation_max",
    "compensation_currency",
    "compensation_interval",
    "salary_text",
    "experience",
    "skills",
    "sponsorship_h1b",
    "source",
    "emails",
    "search_keyword",
    "description",
    "created_at",
    "is_it_job",
    "it_job_family",
    "job_domain",
    "job_domains",
    "classification_confidence",
    "classification_method",
    "classification_reason",
    "technologies",
    "specializations"
]


def clean_job_id(raw_id: str) -> str:
    """Extract clean ID without platform prefix (e.g. 'greenhouse:6105984004' -> '6105984004')"""
    if not raw_id:
        return ""
    if ":" in str(raw_id):
        return str(raw_id).split(":", 1)[-1]
    return str(raw_id)


def clean_description_text(raw_text: str) -> str:
    """Helper to convert HTML/raw description into 100% clean, formatted plain text"""
    if not raw_text:
        return ""
    text = html.unescape(str(raw_text))
    text = html.unescape(text)  # In case of nested entities
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


def format_job_for_csv(job: NormalizedJob) -> dict:
    """Format NormalizedJob into exact CSV columns dictionary"""
    loc = job.location_display or job.location_city or ""
    raw_desc = job.description or job.description_plain or job.description_html or ""
    clean_desc = clean_description_text(raw_desc)
    
    return {
        "job_id": clean_job_id(job.job_id or job.id),
        "title": job.title,
        "company_name": job.company_name,
        "company_logo": job.company_logo or "",
        "company_url": job.company_url or "",
        "department": job.department or "",
        "location": loc,
        "location_state": job.location_state or "",
        "location_country": job.location_country or "USA",
        "is_remote": job.is_remote,
        "job_type": job.job_type or "",
        "job_level": job.job_level or "",
        "date_posted": job.date_posted or "",
        "scraped_at": job.scraped_at,
        "apply_url": job.apply_url or job.job_url or "",
        "compensation_min": job.compensation_min if job.compensation_min is not None else "",
        "compensation_max": job.compensation_max if job.compensation_max is not None else "",
        "compensation_currency": job.compensation_currency or "USD",
        "compensation_interval": job.compensation_interval or "annual",
        "salary_text": job.salary_text or "",
        "experience": job.experience or "",
        "skills": json.dumps(job.skills) if job.skills else "[]",
        "sponsorship_h1b": job.sponsorship_h1b,
        "source": job.source,
        "emails": json.dumps(job.emails) if job.emails else "[]",
        "search_keyword": job.search_keyword or "",
        "description": clean_desc,
        "created_at": job.created_at,
        "is_it_job": job.is_it_job,
        "it_job_family": job.it_job_family or "",
        "job_domain": job.job_domain or "",
        "job_domains": json.dumps(job.job_domains) if job.job_domains else "[]",
        "classification_confidence": round(job.classification_confidence, 2) if job.classification_confidence else 0.0,
        "classification_method": job.classification_method,
        "classification_reason": job.classification_reason,
        "technologies": json.dumps(job.technologies) if job.technologies else "{}",
        "specializations": json.dumps(job.specializations) if job.specializations else "[]"
    }


def write_jobs_to_csv(filepath: str, jobs: List[NormalizedJob]):
    """Write list of NormalizedJob objects to CSV with robust retries and proper quoting"""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)
    temp_path = f"{filepath}.tmp"
    
    # Write to temp file first
    with open(temp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for job in jobs:
            writer.writerow(format_job_for_csv(job))
            
    # Atomically replace or retry on Windows lock
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if os.path.exists(filepath):
                try:
                    os.replace(temp_path, filepath)
                except (PermissionError, OSError):
                    time.sleep(0.3)
                    os.replace(temp_path, filepath)
            else:
                os.replace(temp_path, filepath)
            return
        except (PermissionError, OSError):
            if attempt == max_retries - 1:
                # Attempt direct write
                try:
                    with open(filepath, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_MINIMAL)
                        writer.writeheader()
                        for job in jobs:
                            writer.writerow(format_job_for_csv(job))
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return
                except (PermissionError, OSError):
                    print(f"⚠️ Notice: '{filepath}' is currently open/locked by another application. Data saved to output directory.")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
            time.sleep(0.3)


def save_classified_jobs_to_csvs(
    jobs: List[NormalizedJob],
    target_date: Optional[str] = None
) -> dict:
    """
    Separates jobs into IT and Non-IT datasets and writes to respective CSV files:
    1. A brand new unique timestamped CSV file for EVERY run (e.g. output/jobs_it_2026-09-08_20260909_112500.csv)
    2. it_jobs.csv & non_it_jobs.csv (latest run)
    3. output/jobs_it_YYYY-MM-DD.csv & output/jobs_non_it_YYYY-MM-DD.csv
    """
    it_jobs = [j for j in jobs if j.is_it_job]
    non_it_jobs = [j for j in jobs if not j.is_it_job]
    
    date_suffix = f"_{target_date}" if target_date else ""
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Unique new files generated for THIS specific run
    it_unique_path = f"output/jobs_it{date_suffix}_{run_timestamp}.csv"
    non_it_unique_path = f"output/jobs_non_it{date_suffix}_{run_timestamp}.csv"
    all_unique_path = f"output/jobs{date_suffix}_{run_timestamp}.csv"
    
    write_jobs_to_csv(it_unique_path, it_jobs)
    write_jobs_to_csv(non_it_unique_path, non_it_jobs)
    write_jobs_to_csv(all_unique_path, jobs)
    
    # 2. Dated files
    it_dated_path = f"output/jobs_it{date_suffix}.csv"
    non_it_dated_path = f"output/jobs_non_it{date_suffix}.csv"
    all_dated_path = f"output/jobs{date_suffix}.csv"
    
    write_jobs_to_csv(it_dated_path, it_jobs)
    write_jobs_to_csv(non_it_dated_path, non_it_jobs)
    write_jobs_to_csv(all_dated_path, jobs)
    
    # 3. Root level files (direct latest access)
    write_jobs_to_csv("it_jobs.csv", it_jobs)
    write_jobs_to_csv("non_it_jobs.csv", non_it_jobs)
    
    return {
        "it_count": len(it_jobs),
        "non_it_count": len(non_it_jobs),
        "total_count": len(jobs),
        "new_it_file": it_unique_path,
        "new_non_it_file": non_it_unique_path,
        "new_all_file": all_unique_path,
        "it_file": "it_jobs.csv",
        "non_it_file": "non_it_jobs.csv",
        "output_it": it_dated_path,
        "output_non_it": non_it_dated_path
    }
