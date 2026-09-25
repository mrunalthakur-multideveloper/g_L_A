"""
Multi-Platform Job Retrieval & Database Sync Runner
Retrieves job postings domain-by-domain, populates search_keyword with target domains,
exports per-domain CSVs, and syncs into Neon PostgreSQL database.
"""

import sys
import os
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from crm.pipeline import run_crm_domain_pipeline
from utils.proxy import get_webshare_proxy_url


def main():
    parser = argparse.ArgumentParser(description="Multi-Platform ATS Job Retrieval & Database Sync")
    parser.add_argument("--crm-url", type=str, default=None, help="Custom data endpoint URL")
    parser.add_argument("--hours", type=int, default=int(os.getenv("HOURS_WINDOW", "24")), help="Time window in hours (default: 24)")
    parser.add_argument("--target-date", type=str, default=os.getenv("TARGET_DATE"), help="Target date YYYY-MM-DD")
    parser.add_argument("--workers", type=int, default=25, help="Number of parallel worker threads (default: 25)")
    parser.add_argument("--input-file", type=str, default="us_companies.json", help="Company slugs JSON/CSV file")
    parser.add_argument("--sample", type=int, default=None, help="Limit number of companies for quick testing")
    parser.add_argument("--table", type=str, default=os.getenv("NEON_TABLE") or "links", help="Target database table")
    parser.add_argument("--no-db", action="store_true", help="Disable database synchronization")
    parser.add_argument("--domain", type=str, default=None, help="Optionally run for a specific domain only")
    parser.add_argument("--country", type=str, default="USA", help="Optionally override target country")
    parser.add_argument("--list-domains", action="store_true", help="Inspect and list target domains and database records")

    args = parser.parse_args()

    if args.list_domains:
        import check_crm_domains
        check_crm_domains.main()
        return



    override_clients = None
    if args.domain:
        override_clients = [{
            "domain": args.domain,
            "normalized_domain": args.domain.strip().lower().replace(" ", "_"),
            "country": args.country,
            "normalized_country": args.country.upper()
        }]

    run_crm_domain_pipeline(
        custom_crm_url=args.crm_url,
        hours_window=args.hours,
        target_date=args.target_date,
        workers=args.workers,
        company_input_file=args.input_file,
        sample_companies=args.sample,
        table_name=args.table,
        no_db=args.no_db,
        override_clients=override_clients
    )


if __name__ == "__main__":
    main()
