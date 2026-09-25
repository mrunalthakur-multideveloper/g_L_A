"""
Unified Multi-Source ATS Job Retrieval & Classification Pipeline
Crawls Greenhouse, Lever, and Ashby, applies USA & Target Date filters, deduplicates,
executes multi-level IT/Non-IT classification, and writes separate IT and Non-IT CSVs + PostgreSQL.
"""

import sys
import os
import csv
import argparse
import time
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

import utils.proxy  # Auto-configures transparent Webshare/HTTP proxy if present in .env
from utils.proxy import enforce_proxy_or_abort
from models.job import NormalizedJob
from classification.classifier import classify_job
from scrapers.greenhouse import scrape_greenhouse_company
from scrapers.lever import scrape_lever_company
from scrapers.ashby import scrape_ashby_company
from output.csv_writer import save_classified_jobs_to_csvs
from database.postgres import save_jobs_to_database


def load_companies_to_scrape(input_path: str = "us_companies.json") -> List[Dict[str, str]]:
    """
    Loads company slugs from us_companies.json, CSV, or TXT slug files.
    Supports:
      - JSON format (e.g. us_companies.json: {"greenhouse": [...], "lever": [...], "ashby": [...]})
      - CSV format with 'platform' and 'slug' headers (e.g. ats_active_companies.csv)
      - TXT slug files (slugs_greenhouse.txt, slugs_lever.txt, slugs_ashby.txt)
    """
    companies = []
    
    # 1. If explicit input file given and exists
    if input_path and os.path.exists(input_path):
        if input_path.endswith(".json"):
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for platform in ["greenhouse", "lever", "ashby"]:
                        if platform in data and isinstance(data[platform], list):
                            for slug in data[platform]:
                                s = str(slug).strip()
                                if s:
                                    companies.append({"platform": platform, "slug": s})
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            p = item.get("platform", "").lower().strip()
                            s = item.get("slug", "").strip()
                            if p in ["greenhouse", "lever", "ashby"] and s:
                                companies.append({"platform": p, "slug": s})
            except Exception as e:
                print(f"⚠️ Error reading JSON from {input_path}: {e}")
        elif input_path.endswith(".csv"):
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        p = row.get("platform", "").lower().strip()
                        s = row.get("slug", "").strip()
                        if p in ["greenhouse", "lever", "ashby"] and s:
                            companies.append({"platform": p, "slug": s})
            except Exception as e:
                print(f"⚠️ Error reading CSV from {input_path}: {e}")

    # 2. If nothing loaded yet, try us_companies.json fallback
    if not companies and os.path.exists("us_companies.json"):
        try:
            with open("us_companies.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for platform in ["greenhouse", "lever", "ashby"]:
                    if platform in data and isinstance(data[platform], list):
                        for slug in data[platform]:
                            s = str(slug).strip()
                            if s:
                                companies.append({"platform": platform, "slug": s})
        except Exception:
            pass

    # 3. If still nothing, fallback to ats_active_companies.csv
    if not companies and os.path.exists("ats_active_companies.csv"):
        try:
            with open("ats_active_companies.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    p = row.get("platform", "").lower().strip()
                    s = row.get("slug", "").strip()
                    if p in ["greenhouse", "lever", "ashby"] and s:
                        companies.append({"platform": p, "slug": s})
        except Exception:
            pass

    # 4. Fallback to individual .txt files
    if not companies:
        for p, txt_file in [("greenhouse", "slugs_greenhouse.txt"), ("lever", "slugs_lever.txt"), ("ashby", "slugs_ashby.txt")]:
            if os.path.exists(txt_file):
                with open(txt_file, "r", encoding="utf-8") as f:
                    for line in f:
                        s = line.strip()
                        if s and not s.startswith("#"):
                            companies.append({"platform": p, "slug": s})
                            
    return companies


def scrape_company_worker(row: Dict[str, str], target_date: str, last_24h: bool) -> List[NormalizedJob]:
    """Worker function to scrape a single company row"""
    platform = row.get("platform", "").lower().strip()
    slug = row.get("slug", "").strip()
    if not slug:
        return []
        
    try:
        if platform == "greenhouse":
            return scrape_greenhouse_company(slug, target_date=target_date, last_24_hours=last_24h)
        elif platform == "lever":
            return scrape_lever_company(slug, target_date=target_date, last_24_hours=last_24h)
        elif platform == "ashby":
            return scrape_ashby_company(slug, target_date=target_date, last_24_hours=last_24h)
    except Exception:
        pass
    return []


def main():
    parser = argparse.ArgumentParser(description="Multi-Source ATS Job Retrieval with IT Job Classification")
    parser.add_argument("--target-date", type=str, default=os.getenv("TARGET_DATE"), help="Target publication date (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Retrieve all available dates without date filter")
    parser.add_argument("--24h", dest="last_24h", action="store_true", help="Filter jobs posted in last 24 hours")
    parser.add_argument("--workers", type=int, default=25, help="Number of parallel worker threads (default: 25)")
    parser.add_argument("--input-file", type=str, default="us_companies.json", help="Input file containing active companies (JSON or CSV)")
    parser.add_argument("--sample", type=int, default=None, help="Limit number of companies for quick testing")
    parser.add_argument("--scrape-only", action="store_true", help="Fetch Greenhouse, Lever, and Ashby jobs and save to CSV without running classification")
    parser.add_argument("--table", type=str, default=os.getenv("NEON_TABLE") or "links", help="Target database table name (default: links)")
    parser.add_argument("--no-db", action="store_true", help="Disable database storage to Neon DB / Supabase")
    parser.add_argument("--only-it", action="store_true", help="Store only classified IT jobs into database (default: False, stores all jobs)")
    parser.add_argument("--crm", action="store_true", help="Run active clients domain-by-domain pipeline")
    parser.add_argument("--crm-url", type=str, default=None, help="Custom CRM active clients endpoint URL")
    parser.add_argument("--hours", type=int, default=int(os.getenv("HOURS_WINDOW", "24")), help="Time window in hours for CRM pipeline (default: 24)")
    parser.add_argument("--list-domains", action="store_true", help="Inspect and display active CRM domains and existing Neon DB domains")
    
    args = parser.parse_args()

    if args.list_domains:
        import check_crm_domains
        check_crm_domains.main()
        return

    if args.crm:
        from crm.pipeline import run_crm_domain_pipeline
        run_crm_domain_pipeline(
            custom_crm_url=args.crm_url,
            hours_window=args.hours,
            target_date=args.target_date,
            workers=args.workers,
            company_input_file=args.input_file,
            sample_companies=args.sample,
            table_name=args.table,
            no_db=args.no_db
        )
        return
    
    target_date = None if (args.all or args.last_24h) else args.target_date
    last_24h = args.last_24h
    if not target_date and not args.all and not last_24h:
        # Default behavior: if TARGET_DATE env exists use it, else last 24h
        if os.getenv("TARGET_DATE"):
            target_date = os.getenv("TARGET_DATE")
        else:
            last_24h = True
            
    print("=" * 60)
    print("🚀 ADVANCED IT JOB RETRIEVAL & CLASSIFICATION PIPELINE")
    print(f"📅 Filter Mode: {'ALL DATES' if args.all else (f'Target Date: {target_date}' if target_date else 'Last 24 Hours')}")
    print(f"📁 Input File: {args.input_file}")
    print(f"⚙️ Workers: {args.workers}")
    print("=" * 60)

    # Strictly verify Webshare Proxy before scraping
    enforce_proxy_or_abort()
    
    # 1. Load active companies
    companies = load_companies_to_scrape(args.input_file)
    if not companies:
        print(f"❌ No companies found in {args.input_file} or fallback files!")
        return

    if args.sample:
        companies = companies[:args.sample]
        
    print(f"🎯 Loaded {len(companies):,} companies to scrape\n")
    
    raw_collected_jobs: List[NormalizedJob] = []
    platform_counts = {"greenhouse": 0, "lever": 0, "ashby": 0}
    
    start_time = time.time()
    
    # 2. Parallel Scraping
    completed_count = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(scrape_company_worker, c, target_date, last_24h): c for c in companies}
        for future in as_completed(futures):
            c = futures[future]
            completed_count += 1
            try:
                jobs = future.result()
                if jobs:
                    raw_collected_jobs.extend(jobs)
                    platform_counts[c["platform"]] += len(jobs)
                    print(f"  [{c['platform'].upper():<10}] {c['slug']:<25} → {len(jobs)} jobs")
            except Exception:
                pass
                
            if completed_count % 500 == 0 or completed_count == len(companies):
                print(f"  ⏳ Progress: {completed_count:,}/{len(companies):,} companies scanned | Matches found: {len(raw_collected_jobs):,}")
                
    total_fetched = len(raw_collected_jobs)
    print(f"\n📥 Total raw jobs fetched across all sources: {total_fetched:,}")
    
    # 3. Deduplication
    seen_ids = set()
    seen_urls = set()
    deduped_jobs: List[NormalizedJob] = []
    
    for job in raw_collected_jobs:
        # Check duplicate by ID or URL
        if job.job_id in seen_ids or (job.job_url and job.job_url in seen_urls):
            continue
        seen_ids.add(job.job_id)
        if job.job_url:
            seen_urls.add(job.job_url)
        deduped_jobs.append(job)
        
    print(f"🔄 Deduplicated jobs count: {len(deduped_jobs):,}")
    
    if args.scrape_only:
        from output.csv_writer import write_jobs_to_csv
        from datetime import datetime
        run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_suffix = f"_{target_date}" if target_date else ""
        new_scraped_path = f"output/scraped_jobs{target_suffix}_{run_ts}.csv"
        
        # Phase 1: Save to CSV
        write_jobs_to_csv(new_scraped_path, deduped_jobs)
        write_jobs_to_csv("scraped_jobs.csv", deduped_jobs)
        print(f"\n💾 New Run Scrape File: {new_scraped_path} ({len(deduped_jobs):,} jobs)")
        print(f"💾 Updated Scraped CSV:   scraped_jobs.csv")
        print("👉 Scraped jobs saved to CSV. Run 'python main.py' to classify and store IT jobs into Neon DB.")
        print("=" * 60)
        return
        
    # 4. Multi-Level IT Classification
    print("\n🧠 Executing IT / Non-IT Classification Engine...")
    def safe_classify(j: NormalizedJob) -> NormalizedJob:
        try:
            return classify_job(j)
        except Exception as e:
            j.is_it_job = False
            j.classification_reason = f"Classification error: {e}"
            return j

    with ThreadPoolExecutor(max_workers=min(args.workers, 20)) as classifier_executor:
        classified_jobs = list(classifier_executor.map(safe_classify, deduped_jobs))
            
    it_jobs = [j for j in classified_jobs if j.is_it_job]
    non_it_jobs = [j for j in classified_jobs if not j.is_it_job]
    ambiguous_jobs = [j for j in classified_jobs if j.classification_confidence < 0.60]
    
    # 5. Output to Separate CSV Files (Phase 1)
    csv_results = save_classified_jobs_to_csvs(classified_jobs, target_date=target_date)
    print(f"\n💾 New Run IT File:     {csv_results['new_it_file']} ({len(it_jobs):,} jobs)")
    print(f"💾 New Run Non-IT File: {csv_results['new_non_it_file']} ({len(non_it_jobs):,} jobs)")
    print(f"💾 Root Output:         {csv_results['it_file']} & {csv_results['non_it_file']}")
    print(f"💾 Dated Output:        {csv_results['output_it']} & {csv_results['output_non_it']}")
    
    # 6. Database Storage (Phase 2: Store ONLY IT jobs into Neon DB table after CSV save)
    db_saved = 0
    if not args.no_db and it_jobs:
        print(f"\n🚀 Storing {len(it_jobs):,} IT jobs at once into database table '{args.table}' (Non-IT jobs excluded)...")
        db_saved = save_jobs_to_database(it_jobs, table_name=args.table, only_it=True)
        if db_saved:
            print(f"📤 Saved {db_saved:,} IT jobs to database table '{args.table}' successfully!")
        else:
            print(f"ℹ️ Database: 0 records written or database up-to-date")
    elif not args.no_db and not it_jobs:
        print(f"\nℹ️ 0 IT jobs identified to store in database table '{args.table}'. Non-IT jobs ({len(non_it_jobs):,}) are excluded.")

    # 7. Comprehensive Domain Statistics
    domain_counter = Counter(j.job_domain for j in it_jobs if j.job_domain)
    family_counter = Counter(j.it_job_family for j in it_jobs if j.it_job_family)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 50)
    print("SCRAPER SUMMARY")
    print("=" * 50)
    print(f"Greenhouse fetched: {platform_counts['greenhouse']:,}")
    print(f"Lever fetched:      {platform_counts['lever']:,}")
    print(f"Ashby fetched:      {platform_counts['ashby']:,}")
    print(f"Total fetched:      {total_fetched:,}")
    print(f"Deduplicated total: {len(classified_jobs):,}")
    print(f"USA matched:        {len(classified_jobs):,}")
    print(f"IT jobs:            {len(it_jobs):,}")
    print(f"Non-IT jobs:        {len(non_it_jobs):,}")
    print(f"Ambiguous jobs:     {len(ambiguous_jobs):,}")
    
    print("\n" + "=" * 50)
    print("DOMAIN SUMMARY (TOP 20)")
    print("=" * 50)
    for domain, count in domain_counter.most_common(20):
        print(f"{domain:<35}: {count}")
        
    print("\n" + "=" * 50)
    print("IT FAMILY SUMMARY")
    print("=" * 50)
    for fam, count in family_counter.most_common():
        print(f"{fam:<35}: {count}")

    print("\n" + "=" * 50)
    print("OUTPUT")
    print("=" * 50)
    print(f"New IT CSV:     {csv_results['new_it_file']}")
    print(f"New Non-IT CSV: {csv_results['new_non_it_file']}")
    print(f"Latest IT CSV:  it_jobs.csv & {csv_results['output_it']}")
    print(f"Latest Non-IT:  non_it_jobs.csv & {csv_results['output_non_it']}")
    print(f"PostgreSQL:     {db_saved if db_saved else 0} records")
    print(f"Execution Time: {elapsed:.1f}s")
    print("=" * 50)
    print("🎉 Pipeline execution completed successfully!")


if __name__ == "__main__":
    main()
