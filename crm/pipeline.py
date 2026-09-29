"""
Two-Tier Client-Driven Scraping Pipeline Orchestrator
Integrates CRM active client profiles with multi-platform ATS job retrieval:
  Mode 1: Title-Driven Scraper (desired_job_titles matching)
  Mode 2: Keyword & Description-Driven Scraper (keywords retrieval + 5-Keyword Gatekeeper)
Applies Global Filters (United States & Republic of Ireland ONLY; Last 24 Hours)
and upserts verified postings into Neon PostgreSQL database (public.links).
"""

import os
import sys
import time
import copy
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.job import NormalizedJob
from classification.enrichment import enrich_job
from scrapers.greenhouse import scrape_greenhouse_company
from scrapers.lever import scrape_lever_company
from scrapers.ashby import scrape_ashby_company
from database.postgres import save_jobs_to_neon, save_jobs_to_database
from output.csv_writer import write_jobs_to_csv
from filters.country import is_country_location, is_us_or_ireland_location
from filters.date import matches_date_filter
from utils.proxy import enforce_proxy_or_abort

from .client import fetch_active_clients, normalize_domain_key
from .matcher import match_job_by_titles, match_job_by_keywords_gatekeeper, does_job_match_client_domain


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
            jobs = scrape_greenhouse_company(
                slug,
                target_date=target_date,
                last_24_hours=last_24_hours,
                hours_window=hours_window,
                target_country=target_country
            )
        elif platform == "lever":
            jobs = scrape_lever_company(
                slug,
                target_date=target_date,
                last_24_hours=last_24_hours,
                hours_window=hours_window,
                target_country=target_country
            )
        elif platform == "ashby":
            jobs = scrape_ashby_company(
                slug,
                target_date=target_date,
                last_24_hours=last_24_hours,
                hours_window=hours_window,
                target_country=target_country
            )
        else:
            return []

        # Secondary location safety verification
        if target_country:
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
    override_clients: Optional[List[Dict[str, Any]]] = None,
    mode: str = "all",
    gatekeeper_threshold: int = 5
) -> Dict[str, Any]:
    """
    Executes the Two-Tier Client-Driven Job Pipeline:
    1. Dynamic Client Ingestion from CRM API (https://api.applyus.org/api/clients/active-domains)
    2. Parallel ATS retrieval across Greenhouse, Lever, and Ashby (Last 24 Hours, US & Ireland ONLY)
    3. Mode 1: Title-Driven Scraper (desired_job_titles matching) -> CSV + Neon DB Upsert
    4. Mode 2: Keyword & Description-Driven Scraper (keywords retrieval + 5-Keyword Gatekeeper) -> CSV + Neon DB Upsert
    """
    start_time = time.time()
    print("=" * 75)
    print("🚀 TWO-TIER CLIENT-DRIVEN SCRAPING PIPELINE")
    print(f"⏰ Time Window: Last {hours_window} hours (or Target Date: {target_date or 'Latest 24h'})")
    print(f"🌍 Global Location Filter: United States & Republic of Ireland ONLY")
    print(f"🎯 Scraping Mode: {mode.upper()} (Threshold: >={gatekeeper_threshold} distinct keywords)")
    print(f"🗄️ Database Sync: {'DISABLED (--no-db)' if no_db else f'Neon PostgreSQL (table: {table_name})'}")
    print(f"⚙️ Parallel Workers: {workers}")
    print("=" * 75)

    # Proxy check if configured
    enforce_proxy_or_abort()

    # 1. Ingest active clients
    if override_clients:
        active_clients = override_clients
    else:
        active_clients = fetch_active_clients(custom_url=custom_crm_url)

    if not active_clients:
        print("⚠️ No active clients found from CRM API or cache.")
        return {"clients_processed": 0, "total_jobs_scraped": 0, "total_jobs_synced": 0}

    print("\n📋 ACTIVE CLIENT PROFILES INGESTED FROM CRM API:")
    for idx, c in enumerate(active_clients, 1):
        titles_cnt = len(c.get("desired_job_titles", []))
        kws_cnt = len(c.get("keywords", []))
        print(f"  {idx:2d}. {c.get('full_name', 'Client'):<20} | Domain: {c['domain']:<26} | Country: {c['country']:<14} | Titles: {titles_cnt:2d} | Keywords: {kws_cnt:2d}")
    print()

    # 2. Load companies
    companies = load_all_company_slugs(company_input_file)
    if sample_companies:
        companies = companies[:sample_companies]
    print(f"🏢 Loaded {len(companies):,} company boards across ATS platforms\n")

    # Group clients by target country to optimize board retrieval passes
    country_groups: Dict[str, List[Dict[str, Any]]] = {}
    for c in active_clients:
        country_key = c.get("country", "United States").strip()
        # Canonical country representation
        if country_key.lower() in ["ireland", "republic of ireland", "ie", "irl"]:
            country_norm = "Ireland"
        else:
            country_norm = "USA"
        if country_norm not in country_groups:
            country_groups[country_norm] = []
        country_groups[country_norm].append(c)

    total_synced_records = 0
    total_domain_files_created = 0
    client_summary_results = []
    os.makedirs("output/crm", exist_ok=True)

    # 3. Process country by country
    for country, client_list in country_groups.items():
        print("=" * 75)
        print(f"🌍 TARGET REGION: {country.upper()} — Processing {len(client_list)} Client(s)")
        print("=" * 75)

        raw_jobs: List[NormalizedJob] = []
        completed_boards = 0
        total_boards = len(companies)
        print(f"⏳ Starting parallel retrieval across {total_boards:,} company boards for {country} ({workers} worker threads)...", flush=True)

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
                        print(f"  📊 Boards: {completed_boards:,}/{total_boards:,} ({pct:.1f}%) | Matching Postings: {len(raw_jobs):,}", flush=True)
        except KeyboardInterrupt:
            print(f"\n⚠️ Process interrupted by user. Proceeding with {len(raw_jobs):,} jobs collected so far...\n", flush=True)

        print(f"\n📥 Fetched {len(raw_jobs):,} total job postings for region {country}", flush=True)

        # Deduplicate raw jobs by job_id
        seen_job_ids = set()
        deduped_jobs: List[NormalizedJob] = []
        for j in raw_jobs:
            jid = j.job_id or j.id or j.job_url
            if jid and jid not in seen_job_ids:
                seen_job_ids.add(jid)
                deduped_jobs.append(j)

        print(f"🔍 Unique post-filtering jobs available for evaluation: {len(deduped_jobs):,}\n")

        # Save ALL raw crawled jobs directly for AI classification
        if deduped_jobs:
            master_raw_csv = f"output/crm/all_crawled_raw_{country.lower()}_jobs.csv"
            write_jobs_to_csv(master_raw_csv, deduped_jobs)
            print(f"💾 Master Raw File: Saved {len(deduped_jobs):,} raw crawled jobs to '{master_raw_csv}'")

            if not no_db:
                print(f"📤 Syncing ALL {len(deduped_jobs):,} raw crawled jobs to Neon DB ('public.{table_name}')...", flush=True)
                db_all_saved = save_jobs_to_neon(deduped_jobs, table_name=table_name)
                total_synced_records += db_all_saved
                print(f"✅ Synced {db_all_saved:,} total raw crawled jobs to Neon DB ('public.{table_name}') for AI classification\n", flush=True)

        # 4. Evaluate each client in this country
        for client_idx, client in enumerate(client_list, 1):
            client_name = client.get("full_name") or client.get("client_name") or "Client"
            domain_name = client.get("domain", "")
            norm_domain = client.get("normalized_domain") or normalize_domain_key(domain_name)
            desired_titles = client.get("desired_job_titles", [])
            keywords = client.get("keywords", [])

            print("=" * 80)
            print(f"👤 CANDIDATE PROFILE [{client_idx}/{len(client_list)}]: {client_name.upper()}")
            print(f"   • Primary Domain: {domain_name}")
            print(f"   • Target Region:  {country}")
            print(f"   • Target Titles:  {len(desired_titles)} titles ({', '.join(desired_titles[:3])}{'...' if len(desired_titles) > 3 else ''})")
            print(f"   • Skill Keywords: {len(keywords)} keywords ({', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''})")
            print("-" * 80)

            mode1_matched: List[NormalizedJob] = []
            mode2_matched: List[NormalizedJob] = []
            db_mode1_saved = 0
            db_mode2_saved = 0

            # ----------------------------------------------------
            # MODE 1: Title-Driven Scraper (desired_job_titles)
            # ----------------------------------------------------
            if mode.lower() in ["all", "title", "mode1"]:
                for j in deduped_jobs:
                    if match_job_by_titles(j, desired_titles):
                        cloned = copy.deepcopy(j)
                        cloned.search_keyword = domain_name
                        mode1_matched.append(cloned)

                print(f"   🏷️  MODE 1 (Title-Driven Matching):")
                if mode1_matched:
                    print(f"       ✅ Status: {len(mode1_matched):,} job(s) matched targeted industry titles")
                    print(f"       🔍 Sample Verified Roles:")
                    for idx_s, s in enumerate(mode1_matched[:2], 1):
                        comp = s.company_name or 'Company'
                        loc = s.location_display or 'Location'
                        print(f"          {idx_s}. {s.title} @ {comp} ({loc})")
                        print(f"             └─ URL: {s.job_url}")

                    # Save CSVs
                    csv_mode1 = f"output/crm/mode1_title_{norm_domain}_{country.lower()}_jobs.csv"
                    csv_legacy = f"greenhouse_{norm_domain}_jobs.csv"
                    write_jobs_to_csv(csv_mode1, mode1_matched)
                    write_jobs_to_csv(csv_legacy, mode1_matched)
                    total_domain_files_created += 1

                    # Upsert into Neon DB public.links
                    if not no_db:
                        db_mode1_saved = save_jobs_to_neon(mode1_matched, table_name=table_name)
                        total_synced_records += db_mode1_saved
                        print(f"       💾 Saved CSV: {csv_mode1}")
                        print(f"       📤 Neon DB:   {db_mode1_saved:,} records upserted into 'public.{table_name}'")
                    else:
                        print(f"       💾 Saved CSV: {csv_mode1} (DB sync disabled)")
                else:
                    print(f"       ℹ️ Status: 0 jobs matched targeted titles in this batch of {len(deduped_jobs):,} postings")

            print()

            # ----------------------------------------------------
            # MODE 2: Keyword & Description-Driven (Gatekeeper >= 5)
            # ----------------------------------------------------
            if mode.lower() in ["all", "keyword", "mode2"]:
                for j in deduped_jobs:
                    is_matched, matched_kws, kw_cnt = match_job_by_keywords_gatekeeper(
                        j, keywords, min_threshold=gatekeeper_threshold
                    )
                    if is_matched:
                        cloned = copy.deepcopy(j)
                        cloned.skills = matched_kws
                        cloned.search_keyword = f"{domain_name} ({kw_cnt} Keywords Matched)"
                        mode2_matched.append(cloned)

                print(f"   🔬  MODE 2 (Skill & Description Gatekeeper — Threshold: >={gatekeeper_threshold} distinct keywords):")
                if mode2_matched:
                    print(f"       ✅ Status: {len(mode2_matched):,} job(s) passed the {gatekeeper_threshold}-keyword gatekeeper!")
                    print(f"       🔍 Sample Verified Roles & Matched Skills:")
                    for idx_s, s in enumerate(mode2_matched[:2], 1):
                        comp = s.company_name or 'Company'
                        loc = s.location_display or 'Location'
                        skills_preview = ', '.join(s.skills[:6]) + ('...' if len(s.skills) > 6 else '')
                        print(f"          {idx_s}. {s.title} @ {comp} ({loc})")
                        print(f"             ├─ Matched Skills ({len(s.skills)}): {skills_preview}")
                        print(f"             ├─ Search Tag: '{s.search_keyword}'")
                        print(f"             └─ URL: {s.job_url}")

                    # Save CSV
                    csv_mode2 = f"output/crm/mode2_keyword_{norm_domain}_{country.lower()}_jobs.csv"
                    write_jobs_to_csv(csv_mode2, mode2_matched)
                    total_domain_files_created += 1

                    # Upsert into Neon DB public.links
                    if not no_db:
                        db_mode2_saved = save_jobs_to_neon(mode2_matched, table_name=table_name)
                        total_synced_records += db_mode2_saved
                        print(f"       💾 Saved CSV: {csv_mode2}")
                        print(f"       📤 Neon DB:   {db_mode2_saved:,} records upserted into 'public.{table_name}'")
                    else:
                        print(f"       💾 Saved CSV: {csv_mode2} (DB sync disabled)")
                else:
                    print(f"       ℹ️ Status: 0 jobs had >={gatekeeper_threshold} distinct keywords in description in this batch")

            client_summary_results.append({
                "client": client_name,
                "domain": domain_name,
                "country": country,
                "mode1_jobs": len(mode1_matched),
                "mode1_db": db_mode1_saved,
                "mode2_jobs": len(mode2_matched),
                "mode2_db": db_mode2_saved,
                "total_db": db_mode1_saved + db_mode2_saved
            })
            print("=" * 80 + "\n")

    elapsed = time.time() - start_time
    total_mode1 = sum(r["mode1_jobs"] for r in client_summary_results)
    total_mode2 = sum(r["mode2_jobs"] for r in client_summary_results)

    print("\n" + "=" * 95)
    print("📊 FINAL PIPELINE EXECUTION SUMMARY")
    print("=" * 95)
    print(f"{'#':<3} {'CANDIDATE':<20} {'DOMAIN':<24} {'REGION':<10} {'MODE 1':<10} {'MODE 2':<10} {'NEON DB SYNC'}")
    print("-" * 95)
    for idx, r in enumerate(client_summary_results, 1):
        print(f"{idx:<3} {r['client']:<20} {r['domain']:<24} {r['country']:<10} {r['mode1_jobs']:<10} {r['mode2_jobs']:<10} {r['total_db']}")
    print("-" * 95)
    print("📋 SUMMARY METRICS:")
    print(f"   • Total Active Clients Evaluated:   {len(active_clients)}")
    print(f"   • Mode 1 (Title-Driven) Jobs:       {total_mode1:,}")
    print(f"   • Mode 2 (Keyword Gatekeeper) Jobs: {total_mode2:,}")
    print(f"   • Total Unique Neon DB Upserts:     {total_synced_records:,} records in 'public.{table_name}'")
    print(f"   • Total Dedicated CSVs Created:     {total_domain_files_created} files in 'output/crm/'")
    print(f"   • Total Pipeline Runtime:           {elapsed:.1f}s")
    print("=" * 95 + "\n")

    return {
        "clients_processed": len(active_clients),
        "total_domain_files_created": total_domain_files_created,
        "total_jobs_synced": total_synced_records,
        "details": client_summary_results
    }
