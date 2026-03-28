import requests
from urllib.parse import urlparse

PLATFORM_SIGNALS = {
    "wix": ["wix.com", "wixsite.com", "x-wix-", "WixCodeApi"],
    "squarespace": ["squarespace.com", "squarespace-cdn", "static1.squarespace"],
    "weebly": ["weebly.com", "weeblycloud.com"],
    "wordpress": ["/wp-content/", "/wp-includes/", "wp-json"],
}

def _is_safe_url(url: str) -> bool:
    """Reject loopback, link-local, and RFC-1918 addresses to prevent SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        if host in ("localhost", "127.0.0.1", "::1"):
            return False
        if host.startswith("169.254."):
            return False
        if host.startswith("10.") or host.startswith("192.168."):
            return False
        if host.startswith("172."):
            second = host.split(".")[1] if len(host.split(".")) > 1 else ""
            if second.isdigit() and 16 <= int(second) <= 31:
                return False
        return True
    except Exception:
        return False

def detect_platform(url: str, timeout: int = 8) -> str:
    if not _is_safe_url(url):
        return "unknown"
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        content = resp.text
        final_url = resp.url
        for platform, signals in PLATFORM_SIGNALS.items():
            if any(s in content or s in final_url for s in signals):
                return platform
        return "custom"
    except Exception:
        return "unknown"

def check_ssl(url: str, timeout: int = 8) -> bool:
    if not _is_safe_url(url):
        return False
    try:
        parsed = urlparse(url)
        https_url = parsed._replace(scheme="https").geturl()
        resp = requests.get(https_url, timeout=timeout, allow_redirects=True)
        return resp.url.startswith("https://")
    except Exception:
        return False
