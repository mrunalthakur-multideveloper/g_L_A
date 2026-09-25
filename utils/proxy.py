"""
Webshare & Multi-Provider Proxy Configuration and Network Management Module
Provides transparent proxy support for requests and urllib with automatic environment variable detection,
session management, and Webshare proxy rotation capabilities.
"""

import os
import sys
import random
import urllib.request
from typing import Optional, Dict, Any, List, Tuple
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()


def get_webshare_proxy_url() -> Optional[str]:
    """
    Constructs or retrieves proxy URL from real-time .env configuration:
    1. PROXY_URL, WEBSHARE_PROXY, DECODO_PROXY, WEBSHARE_PROXY_URL
    2. Discrete WEBSHARE_USERNAME, WEBSHARE_PASSWORD, WEBSHARE_HOST, WEBSHARE_PORT
    3. Standard HTTP_PROXY, HTTPS_PROXY, ROTATING_PROXY_URL, SCRAPER_PROXY, ALL_PROXY
    """
    load_dotenv(override=True)

    # 1. Direct proxy string from .env
    proxy_val = (
        os.getenv("PROXY_URL")
        or os.getenv("WEBSHARE_PROXY")
        or os.getenv("DECODO_PROXY")
        or os.getenv("WEBSHARE_PROXY_URL")
        or os.getenv("DECODO_PROXY_URL")
        or os.getenv("WEBSHARE_URL")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("HTTP_PROXY")
        or os.getenv("ROTATING_PROXY_URL")
        or os.getenv("SCRAPER_PROXY")
        or os.getenv("ALL_PROXY")
    )
    if proxy_val and proxy_val.strip():
        proxy_clean = proxy_val.strip().strip('"').strip("'").strip()
        if proxy_clean:
            if not proxy_clean.startswith("http://") and not proxy_clean.startswith("https://") and not proxy_clean.startswith("socks5://"):
                proxy_clean = f"http://{proxy_clean}"
            return proxy_clean

    # 2. Discrete credentials fallback
    ws_user = os.getenv("WEBSHARE_USERNAME") or os.getenv("WEBSHARE_USER") or os.getenv("PROXY_USERNAME")
    ws_pass = os.getenv("WEBSHARE_PASSWORD") or os.getenv("WEBSHARE_PASS") or os.getenv("PROXY_PASSWORD")
    if ws_user and ws_pass:
        ws_host = os.getenv("WEBSHARE_HOST") or os.getenv("PROXY_HOST") or "p.webshare.io"
        ws_port = os.getenv("WEBSHARE_PORT") or os.getenv("PROXY_PORT") or "80"
        return f"http://{ws_user.strip()}:{ws_pass.strip()}@{ws_host.strip()}:{ws_port.strip()}"

    return None


def get_proxy_url() -> Optional[str]:
    """Alias for backwards compatibility and generic usage."""
    return get_webshare_proxy_url()


def get_proxies_dict() -> Optional[Dict[str, str]]:
    """
    Returns proxy dictionary for requests library (e.g. {'http': '...', 'https': '...'})
    """
    proxy_url = get_webshare_proxy_url()
    if not proxy_url:
        return None
    return {
        "http": proxy_url,
        "https": proxy_url
    }


def setup_global_proxy_environment():
    """
    Installs a global urllib ProxyHandler and populates OS proxy environment variables.
    Ensures all requests, urllib.request, and scraper calls automatically route through the proxy.
    """
    proxy_url = get_webshare_proxy_url()
    if proxy_url:
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url

        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy_url,
            "https": proxy_url
        })
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
        return opener
    return None


def setup_urllib_proxy():
    """Alias for setup_global_proxy_environment."""
    return setup_global_proxy_environment()


def get_requests_session(
    timeout: int = 20,
    headers: Optional[Dict[str, str]] = None,
    use_proxy: bool = True
) -> requests.Session:
    """
    Creates a pre-configured requests.Session with proxy support, default headers, and timeouts.
    """
    session = requests.Session()
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9"
    }
    if headers:
        default_headers.update(headers)
    session.headers.update(default_headers)

    if use_proxy:
        proxies = get_proxies_dict()
        if proxies:
            session.proxies.update(proxies)

    return session


def verify_proxy_health(timeout: int = 10) -> Tuple[bool, str]:
    """
    Actively tests the configured proxy by querying an external IP reflection endpoint.
    Returns (is_healthy, ip_or_error_message).
    """
    proxy_url = get_webshare_proxy_url()
    if not proxy_url:
        return False, "No proxy configured in environment (.env)"

    test_urls = [
        "https://api.ipify.org?format=json",
        "https://httpbin.org/ip",
        "https://api.my-ip.io/ip.json"
    ]
    proxies = {"http": proxy_url, "https": proxy_url}
    last_err = "Unknown error"

    for test_url in test_urls:
        try:
            resp = requests.get(
                test_url,
                proxies=proxies,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=timeout
            )
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    ip = data.get("ip") or data.get("origin") or resp.text.strip()
                    return True, str(ip)
                except Exception:
                    return True, resp.text.strip()
            else:
                last_err = f"HTTP {resp.status_code}"
        except Exception as e:
            last_err = str(e)

    return False, f"Proxy connection failed: {last_err}"


def enforce_proxy_or_abort() -> Optional[str]:
    """
    If a proxy is configured in .env, verifies health.
    If no proxy is configured, proceeds directly without errors.
    """
    proxy_url = get_webshare_proxy_url()
    if not proxy_url:
        return None

    masked_url = proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url
    is_healthy, info = verify_proxy_health(timeout=10)
    if is_healthy:
        print(f"🔒 Proxy Active ({masked_url}) - External IP: {info}\n", flush=True)
        return info
    else:
        print(f"⚠️ Configured proxy ({masked_url}) unreachable. Proceeding with direct connection.\n", flush=True)
        return None


# Auto-configure global proxy environment upon import only if present in environment
setup_global_proxy_environment()


