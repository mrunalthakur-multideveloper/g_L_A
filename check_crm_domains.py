"""
CRM & Neon DB Domain Inspector
Hits the CRM route to inspect active client domains, and queries Neon DB (public.links)
to show all existing domains, job counts, and sync status side-by-side.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from crm.client import fetch_active_clients, get_crm_url
from database.postgres import get_database_domain_summary, get_neon_connection


def main():
    print("=" * 75)
    print("🔍 DATABASE & TARGET DOMAINS INSPECTOR")
    print("=" * 75)

    # 1. Inspect Target Domains
    print(f"\n📡 1. Querying Target Domains Route: {get_crm_url()}...")
    active_clients = fetch_active_clients()

    print("\n📋 ACTIVE CLIENT PROFILES (CRM API):")
    print(f"{'#':<3} {'CLIENT NAME':<20} {'DOMAIN':<26} {'COUNTRY':<14} {'TITLES':<8} {'KEYWORDS':<8}")
    print("-" * 85)
    if active_clients:
        for idx, c in enumerate(active_clients, 1):
            titles_cnt = len(c.get('desired_job_titles', []))
            kws_cnt = len(c.get('keywords', []))
            name = c.get('full_name') or c.get('client_name') or 'Client'
            print(f"{idx:<3} {name:<20} {c['domain']:<26} {c['country']:<14} {titles_cnt:<8} {kws_cnt:<8}")
    else:
        print("  (No active client profiles returned from endpoint or cache)")

    # 2. Inspect Neon Database Domains
    print("\n" + "=" * 75)
    print("🗄️  2. Querying Neon PostgreSQL Database ('public.links')...")
    db_summary = get_database_domain_summary("links")

    print("\n📊 DOMAINS CURRENTLY STORED IN NEON DB:")
    print(f"{'#':<3} {'SEARCH_KEYWORD / DOMAIN':<35} {'JOBS':<8} {'COMPANIES':<10} {'LATEST POSTED'}")
    print("-" * 75)
    if db_summary:
        total_jobs = sum(s['job_count'] for s in db_summary)
        for idx, s in enumerate(db_summary, 1):
            latest = s.get('latest_posted') or 'N/A'
            print(f"{idx:<3} {s['domain']:<35} {s['job_count']:<8} {s.get('companies_count', 0):<10} {latest}")
        print("-" * 75)
        print(f"Total Records in DB: {total_jobs:,} across {len(db_summary)} domain categories")
    else:
        print("  (0 records found in database table or connection pending)")

    print("=" * 75)


if __name__ == "__main__":
    main()
