"""
ApplyUs CRM Active Clients Integration Client
Fetches active clients from ApplyUs CRM endpoint and extracts deduplicated (domain, country) pairs.
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

DEFAULT_CRM_URL = "https://api.applyus.org/api/clients/active"


def get_crm_url() -> str:
    """Returns the CRM active clients endpoint URL."""
    backend_url = os.getenv("CRM_BACKEND_URL", "").strip()
    if backend_url:
        backend_url = backend_url.rstrip("/")
        if backend_url.endswith("/api/clients/active"):
            return backend_url
        if backend_url.endswith("/api"):
            return f"{backend_url}/clients/active"
        return f"{backend_url}/api/clients/active"
    return DEFAULT_CRM_URL


def get_crm_api_key() -> str:
    """
    Retrieves the CRM API key from environment variables.
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
    Hits the CRM route: GET https://api.applyus.org/api/clients/active
    Authenticates with header 'x-api-key' loaded from environment.
    Retries up to max_retries on timeout/connection issues.
    Extracts each active client's domain and country.
    If a client's domain is NULL or empty, skips that client completely and moves to the next.
    Falls back gracefully to local crm_active_clients.json cache if offline.
    """
    url = custom_url or get_crm_url()
    api_key = get_crm_api_key()
    cache_file = "crm_active_clients.json"

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Connection": "close"
    }
    if api_key:
        headers["x-api-key"] = api_key

    session = get_requests_session(timeout=timeout, headers=headers)
    raw_clients_data = []

    print(f"📡 Connecting to ApplyUs CRM at {url}...")
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
                print(f"✅ Received {len(raw_clients_data)} client records from CRM API")
                
                # Save cache for offline/future fallback
                if raw_clients_data:
                    try:
                        with open(cache_file, "w", encoding="utf-8") as cf:
                            json.dump(raw_clients_data, cf, indent=2)
                    except Exception:
                        pass
                break
            else:
                print(f"⚠️ Attempt {attempt}/{max_retries}: CRM API returned HTTP status {resp.status_code}")
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️ Attempt {attempt}/{max_retries} failed ({e}). Retrying in {attempt}s...")
                import time
                time.sleep(attempt)
            else:
                print(f"⚠️ Could not reach CRM endpoint after {max_retries} attempts: {e}")

    # If CRM endpoint returned 0 records or is offline, check cache file
    if not raw_clients_data:
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    if isinstance(cached, list):
                        raw_clients_data = cached
                    elif isinstance(cached, dict) and "data" in cached:
                        raw_clients_data = cached["data"]
                print(f"📂 Loaded {len(raw_clients_data)} active clients from local cache ({cache_file})")
            except Exception:
                pass

    # If still empty, check configured CRM_CLIENT_DOMAIN in .env
    client_domain_env = (os.getenv("CRM_CLIENT_DOMAIN") or os.getenv("CLIENT_DOMAIN") or "").strip()
    if not raw_clients_data and client_domain_env and not is_null_domain(client_domain_env):
        raw_clients_data = [{
            "domain": client_domain_env,
            "country": os.getenv("TARGET_COUNTRY", "USA"),
            "full_name": "Active Client"
        }]
        print(f"ℹ️ Loaded active client domain from .env: '{client_domain_env}'")

    # Extract domain & country pairs from desired_job_titles and domain with strict NULL skipping
    seen_pairs = set()
    deduped_clients: List[Dict[str, Any]] = []

    GENERIC_DOMAINS = {"engineering", "general", "technology", "it", "other", "all"}
    client_domain_env = (os.getenv("CRM_CLIENT_DOMAIN") or os.getenv("CLIENT_DOMAIN") or "").strip()

    for item in raw_clients_data:
        if not isinstance(item, dict):
            continue

        client_name = item.get("full_name") or f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or item.get("name", "Unknown Client")
        country_raw = (
            item.get("country")
            or item.get("target_country")
            or item.get("location_country")
            or "USA"
        ).strip()
        norm_country = country_raw.upper() if country_raw else "USA"

        domain_raw = (
            item.get("domain")
            or item.get("job_domain")
            or item.get("target_role")
            or item.get("role")
            or item.get("title")
            or ""
        )

        desired_titles = item.get("desired_job_titles") or []
        if isinstance(desired_titles, str):
            desired_titles = [desired_titles] if not is_null_domain(desired_titles) else []

        # Collect candidate search domains from desired_job_titles and client domain
        candidate_domains: List[str] = []

        # 1. Add valid titles from desired_job_titles
        for dt in desired_titles:
            if not is_null_domain(dt):
                d_str = str(dt).strip()
                if d_str and d_str.lower() not in GENERIC_DOMAINS and d_str not in candidate_domains:
                    candidate_domains.append(d_str)

        # 2. Add domain_raw if valid and not generic
        if not is_null_domain(domain_raw):
            d_raw_str = str(domain_raw).strip()
            if d_raw_str and d_raw_str.lower() not in GENERIC_DOMAINS and d_raw_str not in candidate_domains:
                candidate_domains.append(d_raw_str)

        # STRICT NULL CHECK: If no valid search domains found for client, skip completely
        if not candidate_domains:
            print(f"  ⏭️ [SKIPPED] Client '{client_name}': domain is NULL / empty. Skipping and moving to next client.")
            continue

        for domain_name in candidate_domains:
            norm_domain = normalize_domain_key(domain_name)
            if not norm_domain or is_null_domain(norm_domain):
                continue

            pair_key = (norm_domain, norm_country)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            deduped_clients.append({
                "domain": domain_name,
                "normalized_domain": norm_domain,
                "country": country_raw or "USA",
                "normalized_country": norm_country,
                "client_name": client_name,
                "client_id": item.get("lead_id") or item.get("id") or "",
                "skills": item.get("skills") or [],
                "raw": item
            })

    # Save to local cache for offline resilience
    if deduped_clients:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(raw_clients_data, f, indent=2)
        except Exception:
            pass

    print(f"🎯 Extracted {len(deduped_clients)} valid active client (domain, country) pairs (NULL domains excluded)\n")
    return deduped_clients
