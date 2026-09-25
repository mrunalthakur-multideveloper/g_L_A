"""
Active Clients Job Pipeline Orchestrator
Iterates domain-by-domain for active CRM clients, runs multi-platform ATS job retrieval for target country & date window,
populates search_keyword with client domain, writes dedicated per-domain CSVs, and syncs to Neon PostgreSQL table.
"""

import os
import sys
import time
import copy
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.job import NormalizedJob
from classification.classifier import classify_job
from scrapers.greenhouse import scrape_greenhouse_company
from scrapers.lever import scrape_lever_company
from scrapers.ashby import scrape_ashby_company
from database.postgres import save_jobs_to_database
from output.csv_writer import write_jobs_to_csv
from filters.country import is_country_location
from filters.date import matches_date_filter
from utils.proxy import enforce_proxy_or_abort

from .client import fetch_active_clients, normalize_domain_key
from .matcher import does_job_match_client_domain


def load_all_company_slugs(input_file: str = "us_companies.json") -> List[Dict[str, str]]:
    """Loads company list for multi-platform ATS retrieval."""
    from main import load_companies_to_scrape
    return load_companies_to_scrape(input_file)


def scrape_single_company_for_country(
    row: Dict[str, str],
    target_country: str = "USA",
    target_date: Optional[str] = None,
    last_24_hours: bool = False,
    hours_window: Optional[int] = None
) -> List[NormalizedJob]:
    """Retrieves a company board and applies country and date filtering."""
    platform = row.get("platform", "").lower().strip()
    slug = row.get("slug", "").strip()
    if not slug:
        return []

    try:
        if platform == "greenhouse":
            jobs = scrape_greenhouse_company(slug, target_date=target_date, last_24_hours=last_24_hours, hours_window=hours_window)
        elif platform == "lever":
            jobs = scrape_lever_company(slug, target_date=target_date, last_24_hours=last_24_hours, hours_window=hours_window)
        elif platform == "ashby":
            jobs = scrape_ashby_company(slug, target_date=target_date, last_24_hours=last_24_hours, hours_window=hours_window)
        else:
            return []

        # If country is not USA, ensure country matching
        if target_country and target_country.upper() not in ["USA", "US", "UNITED STATES"]:
            filtered = []
            for j in jobs:
                if is_country_location(j.location_display, target_country=target_country):
                    filtered.append(j)
            return filtered

        return jobs
    except Exception:
        return []


def run_crm_domain_pipeline(
    custom_crm_url: Optional[str] = None,
    hours_window: int = 24,
    target_date: Optional[str] = None,
    workers: int = 25,
    company_input_file: str = "us_companies.json",
    sample_companies: Optional[int] = None,
    table_name: str = "links",
    no_db: bool = False,
    override_clients: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Executes the domain job retrieval workflow:
    1. Fetches target domains from data endpoint
    2. Deduplicates (domain, country) pairs
    3. Retrieves ATS platforms for target country and date window (24h)
    4. Matches and classifies jobs per target domain
    5. Sets search_keyword = target domain
    6. Writes dedicated per-domain CSVs (e.g. greenhouse_{domain}_jobs.csv)
    7. Syncs records into Neon PostgreSQL public.links table
    """
    start_time = time.time()
    print("=" * 65)
    print("🚀 JOB RETRIEVAL & DATABASE SYNC PIPELINE")
    print(f"⏰ Time Window: Last {hours_window} hours (or Target Date: {target_date or 'Latest'})")
    print(f"🗄️ Database Sync: {'DISABLED (--no-db)' if no_db else f'Neon PostgreSQL (table: {table_name})'}")
    print(f"⚙️ Parallel Workers: {workers}")
    print("=" * 65)

    # Proxy check if configured
    enforce_proxy_or_abort()

    # 1. Fetch target domains
    if override_clients:
        active_clients = override_clients
    else:
        active_clients = fetch_active_clients(custom_url=custom_crm_url)

    if not active_clients:
        print("⚠️ No target domains found from data endpoint or fallback.")
        return {"clients_processed": 0, "total_jobs_scraped": 0, "total_jobs_synced": 0}

    print("\n📋 TARGET DOMAINS:")
    for idx, c in enumerate(active_clients, 1):
        print(f"  {idx:2d}. DOMAIN: {c['domain']:<32} | COUNTRY: {c['country']:<10}")
    print()

    # 2. Load companies
    companies = load_all_company_slugs(company_input_file)
    if sample_companies:
        companies = companies[:sample_companies]
    print(f"🏢 Loaded {len(companies):,} company boards across ATS platforms\n")

    # Group domains by country to optimize retrieval passes
    country_groups: Dict[str, List[Dict[str, Any]]] = {}
    for c in active_clients:
        country_key = c.get("country", "USA").upper()
        if country_key not in country_groups:
            country_groups[country_key] = []
        country_groups[country_key].append(c)

    total_synced_records = 0
    total_domain_files_created = 0
    client_summary_results = []

    # 3. Process country by country, domain by domain
    for country, client_list in country_groups.items():
        print("=" * 65)
        print(f"🌍 COUNTRY: {country} — Processing {len(client_list)} Target Domain(s)")
        print("=" * 65)

        # Retrieve all active boards for this country with live progress
        raw_jobs: List[NormalizedJob] = []
        completed_boards = 0
        total_boards = len(companies)
        print(f"⏳ Starting parallel retrieval across {total_boards:,} company boards ({workers} worker threads)...", flush=True)

        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(
                        scrape_single_company_for_country,
                        comp,
                        country,
                        target_date,
                        last_24_hours=(hours_window <= 24 and not target_date),
                        hours_window=(hours_window if not target_date else None)
                    ): comp for comp in companies
                }
                for future in as_completed(futures):
                    completed_boards += 1
                    try:
                        res = future.result()
                        if res:
                            raw_jobs.extend(res)
                    except Exception:
                        pass

                    if completed_boards in (1, 10, 50, 100, 250) or completed_boards % 250 == 0 or completed_boards == total_boards:
                        pct = (completed_boards / total_boards) * 100
                        print(f"  📊 Boards: {completed_boards:,}/{total_boards:,} ({pct:.1f}%) | Matching Jobs: {len(raw_jobs):,}", flush=True)
        except KeyboardInterrupt:
            print(f"\n⚠️ Process interrupted by user. Proceeding with {len(raw_jobs):,} jobs collected so far...\n", flush=True)

        print(f"\n📥 Fetched {len(raw_jobs):,} total job postings for country {country}", flush=True)

        # Deduplicate raw jobs
        seen_job_ids = set()
        deduped_jobs: List[NormalizedJob] = []
        for j in raw_jobs:
            jid = j.job_id or j.id or j.job_url
            if jid and jid not in seen_job_ids:
                seen_job_ids.add(jid)
                deduped_jobs.append(j)

        # Run classification engine
        print(f"🧠 Classifying {len(deduped_jobs):,} jobs...")
        with ThreadPoolExecutor(max_workers=min(workers, 20)) as classifier_executor:
            classified_jobs = list(classifier_executor.map(classify_job, deduped_jobs))

        # 4. Filter and process domain by domain
        for client_idx, client in enumerate(client_list, 1):
            domain_name = client["domain"]
            norm_domain = client["normalized_domain"]

            print("\n" + "-" * 65)
            print(f"🎯 [DOMAIN {client_idx}/{len(client_list)}]: '{domain_name}' | COUNTRY: '{country}'")
            print(f"   Searching and matching jobs for domain '{domain_name}'...")
            print("-" * 65)

            matched_jobs_for_domain: List[NormalizedJob] = []
            for j in classified_jobs:
                if does_job_match_client_domain(j, domain_name):
                    # Clone job to avoid search_keyword collision between domains
                    cloned_job = copy.deepcopy(j)
                    # Requirement 5: Ensure jobs have search_keyword populated with domain
                    cloned_job.search_keyword = domain_name
                    matched_jobs_for_domain.append(cloned_job)

            print(f"   ✅ Matched {len(matched_jobs_for_domain):,} jobs for domain '{domain_name}'")

            # Show a quick preview of top matched jobs
            if matched_jobs_for_domain:
                print("   🔍 Sample Matched Roles:")
                for sample_j in matched_jobs_for_domain[:3]:
                    print(f"      • {sample_j.title} @ {sample_j.company_name} ({sample_j.location_display})")
                    print(f"        └─ search_keyword: '{sample_j.search_keyword}' | URL: {sample_j.job_url}")

            # Requirement 6: Write dedicated CSV file per domain (e.g., greenhouse_{domain}_jobs.csv)
            primary_csv = f"greenhouse_{norm_domain}_jobs.csv"
            output_dated_csv = f"output/crm/greenhouse_{norm_domain}_{country.lower()}_jobs.csv"
            
            write_jobs_to_csv(primary_csv, matched_jobs_for_domain)
            write_jobs_to_csv(output_dated_csv, matched_jobs_for_domain)
            total_domain_files_created += 1

            # Sync records into Neon PostgreSQL public.links table if DB sync is enabled
            db_saved = 0
            if not no_db and matched_jobs_for_domain:
                db_saved = save_jobs_to_database(
                    matched_jobs_for_domain,
                    table_name=table_name,
                    only_it=False
                )
                total_synced_records += db_saved
                print(f"   💾 Saved Domain CSV: {primary_csv}")
                print(f"   📤 Neon DB Sync:     {db_saved:,} records synced into table '{table_name}'")
            else:
                print(f"   💾 Saved Domain CSV: {primary_csv} (DB Sync: skipped/0)")

            client_summary_results.append({
                "domain": domain_name,
                "country": country,
                "matched_jobs": len(matched_jobs_for_domain),
                "csv_file": primary_csv,
                "db_synced": db_saved
            })

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print("📊 PIPELINE SUMMARY — DOMAIN BREAKDOWN")
    print("=" * 65)
    print(f"{'DOMAIN':<32} {'COUNTRY':<10} {'JOBS':<8} {'CSV FILE':<35} {'DB'}")
    print("-" * 95)
    for r in client_summary_results:
        print(f"{r['domain']:<32} {r['country']:<10} {r['matched_jobs']:<8} {r['csv_file']:<35} {r['db_synced']}")

    print("=" * 95)
    print(f"Total Unique Domains Processed: {len(active_clients)}")
    print(f"Total Domain CSV Files Created: {total_domain_files_created}")
    print(f"Total Database Records Synced:  {total_synced_records:,}")
    print(f"Total Execution Time:           {elapsed:.1f}s")
    print("=" * 95)

    return {
        "clients_processed": len(active_clients),
        "total_domain_files_created": total_domain_files_created,
        "total_jobs_synced": total_synced_records,
        "details": client_summary_results
    }
