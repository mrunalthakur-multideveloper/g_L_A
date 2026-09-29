"""
Data Integration Client
Fetches target domains from data endpoint and extracts deduplicated (domain, country) pairs.
"""

import os
import sys
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from utils.proxy import get_requests_session

DEFAULT_CRM_URL = "https://api.applyus.org/api/clients/active-domains"


def get_crm_url() -> str:
    """Returns the CRM active-domains endpoint URL."""
    backend_url = os.getenv("CRM_BACKEND_URL", "").strip()
    if backend_url:
        backend_url = backend_url.rstrip("/")
        if backend_url.endswith("/api/clients/active-domains"):
            return backend_url
        if backend_url.endswith("/api/clients/active"):
            return backend_url.replace("/api/clients/active", "/api/clients/active-domains")
        if backend_url.endswith("/api"):
            return f"{backend_url}/clients/active-domains"
        return f"{backend_url}/api/clients/active-domains"
    return DEFAULT_CRM_URL


def get_crm_api_key() -> str:
    """
    Retrieves the API key from environment variables.
    Checks INTERNAL_SERVICE_API_KEY, then CRM_API_KEY, then CRM_KEY.
    """
    return (
        os.getenv("INTERNAL_SERVICE_API_KEY", "")
        or os.getenv("CRM_API_KEY", "")
        or os.getenv("CRM_KEY", "")
        or os.getenv("X_API_KEY", "")
    ).strip()


def normalize_domain_key(domain: str) -> str:
    """
    Normalizes a domain keyword string for matching and filenames:
    e.g. 'Full Stack Java Developer' -> 'full_stack_java_developer'
    """
    if not domain:
        return ""
    d = str(domain).strip().lower()
    # Replace non-alphanumeric chars with underscore
    d = re.sub(r'[\s\-_/]+', '_', d)
    d = re.sub(r'[^a-z0-9_]', '', d)
    return d.strip('_')


def is_null_domain(val: Any) -> bool:
    """Checks if a domain value is null, empty, or undefined."""
    if val is None:
        return True
    s = str(val).strip().lower()
    return s in ("", "null", "none", "undefined", "n/a", "nil")


def fetch_active_clients(
    custom_url: Optional[str] = None,
    timeout: int = 15,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Hits the data endpoint: GET active target records
    Authenticates with header 'x-api-key' loaded from environment.
    Retries up to max_retries on timeout/connection issues.
    Extracts each target domain and country.
    If a record's domain is NULL or empty, skips that record completely and moves to the next.
    Falls back gracefully to local crm_active_clients.json cache if offline.
    """
    url = custom_url or get_crm_url()
    api_key = get_crm_api_key()
    cache_file = "crm_active_clients.json"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Connection": "close"
    }
    if api_key:
        headers["x-api-key"] = api_key

    session = get_requests_session(timeout=timeout, headers=headers)
    raw_clients_data = []

    print(f"📡 Connecting to data endpoint at {url}...")
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200:
                try:
                    res_json = resp.json()
                except Exception:
                    res_json = {}
                if isinstance(res_json, dict):
                    data_val = res_json.get("data")
                    if isinstance(data_val, list):
                        raw_clients_data = data_val
                    elif isinstance(res_json.get("clients"), list):
                        raw_clients_data = res_json.get("clients")
                    elif isinstance(res_json.get("results"), list):
                        raw_clients_data = res_json.get("results")
                elif isinstance(res_json, list):
                    raw_clients_data = res_json
                if not isinstance(raw_clients_data, list):
                    raw_clients_data = []
                print(f"✅ Received {len(raw_clients_data)} records from API")
                
                # Save cache for offline/future fallback
                if raw_clients_data:
                    try:
                        with open(cache_file, "w", encoding="utf-8") as cf:
                            json.dump(raw_clients_data, cf, indent=2)
                    except Exception:
                        pass
                break
            else:
                print(f"⚠️ Attempt {attempt}/{max_retries}: API returned HTTP status {resp.status_code}")
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️ Attempt {attempt}/{max_retries} failed ({e}). Retrying in {attempt}s...")
                import time
                time.sleep(attempt)
            else:
                print(f"⚠️ Could not reach endpoint after {max_retries} attempts: {e}")

    # If endpoint returned 0 records or is offline, check cache file
    if not raw_clients_data:
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    if isinstance(cached, list):
                        raw_clients_data = cached
                    elif isinstance(cached, dict) and "data" in cached:
                        raw_clients_data = cached["data"]
                print(f"📂 Loaded {len(raw_clients_data)} records from local cache ({cache_file})")
            except Exception:
                pass

    # If still empty, check configured CRM_CLIENT_DOMAIN in .env
    client_domain_env = (os.getenv("CRM_CLIENT_DOMAIN") or os.getenv("CLIENT_DOMAIN") or "").strip()
    if not raw_clients_data and client_domain_env and not is_null_domain(client_domain_env):
        raw_clients_data = [{
            "domain": client_domain_env,
            "desired_job_titles": [client_domain_env],
            "keywords": [w for w in client_domain_env.split() if len(w) > 2],
            "country": os.getenv("TARGET_COUNTRY", "United States"),
            "full_name": "Target Domain Client"
        }]
        print(f"ℹ️ Loaded target domain from .env: '{client_domain_env}'")

    # Ingest Client Profiles: full_name, domain, desired_job_titles, keywords, country
    # Strictly skip records whose domain is NULL or empty
    seen_clients = set()
    deduped_clients: List[Dict[str, Any]] = []

    for item in raw_clients_data:
        if not isinstance(item, dict):
            continue

        full_name = (
            item.get("full_name")
            or f"{item.get('first_name', '')} {item.get('last_name', '')}".strip()
            or item.get("name")
            or "Candidate"
        ).strip()

        domain_raw = (
            item.get("domain")
            or item.get("job_domain")
            or item.get("target_role")
            or item.get("role")
            or item.get("title")
            or ""
        )

        # STRICT NULL CHECK: If domain is NULL or empty, skip record completely
        if is_null_domain(domain_raw):
            print(f"  ⏭️ [SKIPPED] Record '{full_name}': domain is NULL / empty. Skipping.")
            continue

        domain_str = str(domain_raw).strip()
        norm_domain = normalize_domain_key(domain_str)
        if not norm_domain:
            continue

        country_raw = (
            item.get("country")
            or item.get("target_country")
            or item.get("location_country")
            or "United States"
        ).strip()
        norm_country = country_raw.upper() if country_raw else "UNITED STATES"

        # Desired Job Titles
        desired_titles_raw = item.get("desired_job_titles") or []
        if isinstance(desired_titles_raw, str):
            desired_titles_raw = [desired_titles_raw]
        desired_titles: List[str] = []
        for t in desired_titles_raw:
            t_str = str(t).strip()
            if t_str and not is_null_domain(t_str) and t_str not in desired_titles:
                desired_titles.append(t_str)
        if not desired_titles:
            desired_titles = [domain_str]

        # Keywords (25-35 skill/tool/framework keywords)
        keywords_raw = item.get("keywords") or item.get("skills") or []
        if isinstance(keywords_raw, str):
            keywords_raw = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        keywords: List[str] = []
        for k in keywords_raw:
            k_str = str(k).strip()
            if k_str and not is_null_domain(k_str) and k_str not in keywords:
                keywords.append(k_str)

        # Prevent exact duplicate client registrations
        client_key = (full_name.lower(), norm_domain, norm_country)
        if client_key in seen_clients:
            continue
        seen_clients.add(client_key)

        deduped_clients.append({
            "full_name": full_name,
            "domain": domain_str,
            "normalized_domain": norm_domain,
            "desired_job_titles": desired_titles,
            "keywords": keywords,
            "country": country_raw or "United States",
            "normalized_country": norm_country,
            "client_name": full_name,
            "client_id": str(item.get("lead_id") or item.get("id") or ""),
            "raw": item
        })

    # Save to local cache for offline resilience
    if deduped_clients:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(raw_clients_data, f, indent=2)
        except Exception:
            pass

    print(f"🎯 Extracted {len(deduped_clients)} active client profiles (NULL domains excluded)\n")
    return deduped_clients
