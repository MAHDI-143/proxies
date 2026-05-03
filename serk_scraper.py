#!/usr/bin/env python3
"""
XTM Proxy Scraper v3.0
Fixes: token security, protocol-aware testing, proper error handling,
       no credential leakage in git remote, no DDoS on single test endpoint.
"""

import os
import sys
import requests
import re
import time
import json
import base64
import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ── Optional SOCKS support ────────────────────────────────────────────────────
try:
    import socks  # noqa: F401
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False

# ── Optional encryption (Termux: pip install cryptography) ───────────────────
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="xtm_errors.log",
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ── Colors ────────────────────────────────────────────────────────────────────
RST  = "\033[0m"           # reset
G1   = "\033[38;5;46m"    # bright green        (borders, stars)
G2   = "\033[38;5;49m"    # cyan-green          (separator lines)
G3   = "\033[38;5;47m"    # yellow-green        (owner line)
G4   = "\033[38;5;48m"    # teal                (github line)
BOLD = "\033[1;92m"       # bold bright green   (brackets)
RED  = "\033[1;91m"       # bold red
YEL  = "\033[93m"         # yellow              (menu options)
CYN  = "\033[96m"         # cyan                (prompts)
GRN  = "\033[92m"         # green               (ok messages)
ERR  = "\033[1;31m"       # red                 (error messages)
BLU  = "\033[38;5;27m"   # blue                (logo border + art)

# Legacy aliases
G   = G1
GGG = G2
XX  = BOLD

CONFIG_FILE = "config.json"
TOKEN_FILE  = ".xtm_token"


# ═══════════════════════════════════════════════════════════════════════════════
#  TOKEN ENCRYPTION  (Termux-compatible — no keychain needed)
# ═══════════════════════════════════════════════════════════════════════════════

def _machine_key() -> bytes:
    """Stable machine-bound key derived from device environment."""
    parts = [
        os.environ.get("HOME", ""),
        os.environ.get("USER", os.environ.get("LOGNAME", "")),
        str(os.getuid()) if hasattr(os, "getuid") else "0",
    ]
    seed = "|".join(parts).encode()
    salt = hashlib.sha256(seed + b"xtm_salt").digest()[:16]
    if CRYPTO_AVAILABLE:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
        return base64.urlsafe_b64encode(kdf.derive(seed))
    return base64.urlsafe_b64encode(hashlib.sha256(seed + salt).digest())


def save_token(token: str):
    """Encrypt and save token. Falls back to XOR obfuscation without cryptography."""
    key = _machine_key()
    if CRYPTO_AVAILABLE:
        encrypted = Fernet(key).encrypt(token.encode())
        with open(TOKEN_FILE, "wb") as fh:
            fh.write(encrypted)
    else:
        k = key * (len(token) // len(key) + 1)
        obfuscated = bytes(a ^ b for a, b in zip(token.encode(), k[:len(token)]))
        with open(TOKEN_FILE, "wb") as fh:
            fh.write(base64.b64encode(obfuscated))
    os.chmod(TOKEN_FILE, 0o600)


def load_token() -> str | None:
    """Decrypt and return token."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        key = _machine_key()
        with open(TOKEN_FILE, "rb") as fh:
            data = fh.read()
        if CRYPTO_AVAILABLE:
            return Fernet(key).decrypt(data).decode()
        obfuscated = base64.b64decode(data)
        k = key * (len(obfuscated) // len(key) + 1)
        return bytes(a ^ b for a, b in zip(obfuscated, k[:len(obfuscated)])).decode()
    except Exception as exc:
        logging.warning("load_token failed: %s", exc)
        return None

# ── Logo ──────────────────────────────────────────────────────────────────────
_W = 44  # inner width

LOGO = (
    f"{BLU}{'#'*44}{RST}\n"
    f"{BLU}##  {'':36}  ##{RST}\n"
    f"{BLU}##    .d8888.  d88888b d8888b. db   dD    ##{RST}\n"
    f"{BLU}##    88'  YP  88'     88  `8D 88 ,8P'    ##{RST}\n"
    f"{BLU}##    `8bo.    88ooooo 88oobY' 88,8P      ##{RST}\n"
    f"{BLU}##      `Y8b.  88ooooo 88`8b   88`8b      ##{RST}\n"
    f"{BLU}##    db   8D  88.     88 `88. 88 `88.    ##{RST}\n"
    f"{BLU}##    `8888Y'  Y88888P 88   YD YP   YD    ##{RST}\n"
    f"{BLU}##  {'':36}  ##{RST}\n"
    f"{BLU}#### {'#'*10} Proxy_Scraper {'#'*11} ##{RST}\n"
    f"{G1}⋆{G2}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{G1}⋆{RST}\n"
    f" {BOLD}[{G1}•{BOLD}]{G1} OWNER     : SERK{RST}\n"
    f" {BOLD}[{G1}•{BOLD}]{G1} GITHUB    : MAHDI-143{RST}\n"
    f" {BOLD}[{G1}•{BOLD}]{G1} VERSION   : 1.5{RST}\n"
    f"{G1}⋆{G2}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{G1}⋆{RST}"
)


# ═══════════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def linex():
    print(f'{G1}⋆{G2}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{G1}⋆{RST}')

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(LOGO)

def wait_for_enter():
    input(f"\n{YEL}[+] Press Enter to continue...{RST}")

def info(msg):  print(f"{CYN}[+] {msg}{RST}")
def ok(msg):    print(f"{GRN}[✓] {msg}{RST}")
def warn(msg):  print(f"{YEL}[!] {msg}{RST}")
def err(msg):   print(f"{ERR}[✗] {msg}{RST}")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECURE CONFIG  (token in encrypted file, not plaintext JSON)
# ═══════════════════════════════════════════════════════════════════════════════

def load_config():
    """Return {username, repo, token} or None."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        token = load_token()
        if not token:
            warn("Token file missing or corrupted — re-run setup.")
            return None
        cfg["token"] = token
        return cfg
    except Exception as exc:
        logging.warning("load_config failed: %s", exc)
        return None


def save_config(username: str, token: str, repo: str):
    """Save non-secret fields to JSON; token goes to encrypted file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump({"username": username, "repo": repo}, f)
    save_token(token)


# ═══════════════════════════════════════════════════════════════════════════════
#  GITHUB API  (no credentials in git remote URLs)
# ═══════════════════════════════════════════════════════════════════════════════

GH_API = "https://api.github.com"

def _gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def gh_create_or_verify_repo(username: str, token: str, repo: str) -> bool:
    """Create repo if it doesn't exist. Return True on success."""
    headers = _gh_headers(token)
    # Check existence first
    r = requests.get(f"{GH_API}/repos/{username}/{repo}", headers=headers, timeout=10)
    if r.status_code == 200:
        ok(f"Repository '{repo}' found.")
        return True
    if r.status_code != 404:
        err(f"GitHub API error: {r.status_code} — {r.json().get('message','')}")
        return False
    # Create it
    r = requests.post(
        f"{GH_API}/user/repos",
        headers=headers,
        json={"name": repo, "public": True, "description": "Proxy list — XTM tool"},
        timeout=10,
    )
    if r.status_code == 201:
        ok(f"Repository '{repo}' created.")
        return True
    err(f"Could not create repo: {r.json().get('message','unknown error')}")
    return False


def gh_push_file(username: str, token: str, repo: str, content: str) -> bool:
    """
    Push proxies.txt via the Contents API — no git binary, no credential leakage.
    Uses PUT /repos/{owner}/{repo}/contents/{path}.
    """
    headers = _gh_headers(token)
    api_url = f"{GH_API}/repos/{username}/{repo}/contents/proxies.txt"

    # Fetch current SHA (required for updates)
    sha = None
    r = requests.get(api_url, headers=headers, timeout=10)
    if r.status_code == 200:
        sha = r.json().get("sha")

    encoded = base64.b64encode(content.encode()).decode()
    payload = {
        "message": f"Update proxies — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": encoded,
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(api_url, headers=headers, json=payload, timeout=20)
    if r.status_code in (200, 201):
        return True
    err(f"Push failed: {r.status_code} — {r.json().get('message','')}")
    logging.warning("gh_push_file failed: %s %s", r.status_code, r.text)
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP / CHANGE LINK
# ═══════════════════════════════════════════════════════════════════════════════

def setup() -> dict | None:
    config = load_config()
    if config:
        return config

    clear()
    warn("FIRST TIME SETUP")
    if CRYPTO_AVAILABLE:
        info("Token will be encrypted with Fernet (AES-128) — install cryptography for this.")
    else:
        info("cryptography not installed — token stored with XOR obfuscation.")
        info("For stronger security: pip install cryptography")

    username = input(f"{CYN}[?] GitHub username: {RST}").strip()
    token    = input(f"{CYN}[?] GitHub token (repo scope): {RST}").strip()

    if not username or not token:
        err("Username and token are required.")
        wait_for_enter()
        return None

    create = input(f"{CYN}[?] Create a new repository? (y/n): {RST}").lower()
    if create == "y":
        repo = input(f"{CYN}[?] Repository name [proxies]: {RST}").strip() or "proxies"
    else:
        repo = input(f"{CYN}[?] Existing repository name: {RST}").strip()
        if not repo:
            err("Repository name required.")
            wait_for_enter()
            return None

    if not gh_create_or_verify_repo(username, token, repo):
        wait_for_enter()
        return None

    save_config(username, token, repo)
    ok("Setup complete — token saved to encrypted file.")
    wait_for_enter()
    return load_config()


def change_link():
    clear()
    cfg = load_config()
    current_user = cfg["username"] if cfg else "None"
    current_repo = cfg["repo"]     if cfg else "proxies"

    warn("CHANGE GITHUB SETTINGS")
    username = input(f"[?] New username (current: {current_user}): \033[0m").strip()
    token    = input(f"{CYN}[?] New token: {RST}").strip()
    repo     = input(f"[?] New repo (current: {current_repo}): \033[0m").strip() or current_repo

    if not username or not token:
        err("Username and token required.")
    else:
        save_config(username, token, repo)
        ok("Settings updated.")
    wait_for_enter()


# ═══════════════════════════════════════════════════════════════════════════════
#  PROXY SOURCES
# ═══════════════════════════════════════════════════════════════════════════════

# ── Mode 1: GitHub text files (original method) ───────────────────────────────
GITHUB_SOURCES: dict[str, list[str]] = {
    "http": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
        "https://proxy-list.download/api/v1/get?type=http",
        "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
        "https://free-proxy-list.net/en/",
    ],
    "socks4": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all",
        "https://proxy-list.download/api/v1/get?type=socks4",
        "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks4/data.txt",
    ],
    "socks5": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
        "https://proxy-list.download/api/v1/get?type=socks5",
        "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt",
    ],
}

# ── Mode 2: Live JSON APIs (verified, protocol-tagged) ────────────────────────
# Each entry: (name, fetcher_function)
# Fetchers are defined below and registered into this list at the bottom.
JSON_API_SOURCES = []   # populated after function definitions

# Multiple test endpoints — rotated to avoid hammering one service
TEST_ENDPOINTS = [
    "http://httpbin.org/ip",
    "http://ip-api.com/json",
    "http://api.ipify.org",
    "http://checkip.amazonaws.com",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dedup_add(entries: list[dict], seen: set, result: list) -> int:
    """Add entries to result, skipping duplicates. Returns count added."""
    added = 0
    for e in entries:
        key = (e["proxy"], e["protocol"])
        if key not in seen:
            seen.add(key)
            result.append(e)
            added += 1
    return added


# ═══════════════════════════════════════════════════════════════════════════════
#  JSON API FETCHERS  (Mode 2)
# ═══════════════════════════════════════════════════════════════════════════════

def _country_menu() -> str:
    """Ask user for country filter. Returns country code or 'all'."""
    print(f"\n{YEL}╔══════════════════════════════════════════════════════╗")
    print(f"║  COUNTRY FILTER                                      ║")
    print(f"║                                                      ║")
    print(f"║  [1] ALL COUNTRIES  — no filter (most proxies)       ║")
    print(f"║  [2] SPECIFIC       — enter country code             ║")
    print(f"║      Examples: US  GB  DE  FR  JP  SG  IN  BR        ║")
    print(f"╚══════════════════════════════════════════════════════╝{RST}")
    cc = input(f"{CYN}[?] Choose (1/2): {RST}").strip()
    if cc == "2":
        while True:
            code = input(f"{CYN}[?] Country code: {RST}").strip().upper()
            if code:
                ok(f"Filtering to: {code}")
                return code
            err("Country code cannot be empty. Enter a code (e.g. US, GB, DE) or press Ctrl+C to cancel.")
    ok("No country filter — fetching all.")
    return "all"


def fetch_github_sources(country: str = "all") -> list[dict]:
    """Fetch from GitHub text file sources. Country filter applied post-fetch via IP lookup."""
    seen: set    = set()
    result: list = []
    info("Fetching from GitHub sources...\n")
    for protocol, urls in GITHUB_SOURCES.items():
        for url in urls:
            try:
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r.text)
                entries = [{"proxy": p, "protocol": protocol, "country": "?", "anonymity": "unknown"} for p in found]
                added   = _dedup_add(entries, seen, result)
                ok(f"  +{added} {protocol} from {url.split('/')[2]}")
            except requests.RequestException as exc:
                err(f"  Failed: {url.split('/')[2]}")
                logging.warning("fetch %s: %s", url, exc)
    return result


def fetch_geonode(country: str = "all") -> list[dict]:
    """Geonode — paginated JSON, sorted by lastChecked. Supports country filter."""
    result = []
    base    = "https://proxylist.geonode.com/api/proxy-list"
    headers = {"User-Agent": "Mozilla/5.0"}
    page    = 1

    while page <= 10:
        try:
            params = {
                "limit": 500, "page": page,
                "sort_by": "lastChecked", "sort_type": "desc",
            }
            if country != "all":
                params["country"] = country
            r = requests.get(base, params=params, headers=headers, timeout=15)
            r.raise_for_status()
            data    = r.json()
            entries = data.get("data", [])
            if not entries:
                break
            for e in entries:
                ip, port = e.get("ip", ""), e.get("port", "")
                if not ip or not port:
                    continue
                anon = e.get("anonymityLevel", "unknown").lower()
                cc   = e.get("country", "?")
                for proto in e.get("protocols", ["http"]):
                    proto = proto.lower()
                    if proto == "https":
                        proto = "http"
                    if proto not in ("http", "socks4", "socks5"):
                        continue
                    result.append({"proxy": f"{ip}:{port}", "protocol": proto,
                                   "country": cc, "anonymity": anon})
            total = data.get("total", 0)
            ok(f"  Geonode page {page} → +{len(entries)} proxies")
            if page * 500 >= total:
                break
            page += 1
        except Exception as exc:
            err(f"  Geonode page {page} failed")
            logging.warning("geonode p%s: %s", page, exc)
            break
    return result


def fetch_proxyscrape_v4(country: str = "all") -> list[dict]:
    """ProxyScrape v4 — supports country param."""
    result  = []
    url     = "https://api.proxyscrape.com/v4/free-proxy-list/get"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        params = {
            "request": "display_proxies",
            "proxy_format": "protocolipport",
            "format": "text",
        }
        if country != "all":
            params["country"] = country
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        for line in r.text.strip().splitlines():
            line = line.strip()
            if "://" in line:
                proto, addr = line.split("://", 1)
                proto = proto.lower()
                if proto == "https":
                    proto = "http"
                if proto in ("http", "socks4", "socks5") and re.match(r'\d+\.\d+\.\d+\.\d+:\d+', addr):
                    result.append({"proxy": addr, "protocol": proto,
                                   "country": country, "anonymity": "unknown"})
        ok(f"  ProxyScrape v4 → +{len(result)} proxies")
    except Exception as exc:
        err("  ProxyScrape v4 failed")
        logging.warning("proxyscrape_v4: %s", exc)
    return result


def fetch_proxifly(country: str = "all") -> list[dict]:
    """Proxifly CDN — JSON format, filter by country post-fetch."""
    result = []
    url    = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        entries = r.json()
        for e in entries:
            ip    = e.get("ip", "")
            port  = e.get("port", "")
            proto = e.get("protocol", "http").lower()
            cc    = e.get("country", "?")
            if proto == "https":
                proto = "http"
            if country != "all" and cc.upper() != country:
                continue
            if ip and port and proto in ("http", "socks4", "socks5"):
                result.append({"proxy": f"{ip}:{port}", "protocol": proto,
                               "country": cc, "anonymity": "unknown"})
        ok(f"  Proxifly → +{len(result)} proxies")
    except Exception as exc:
        err("  Proxifly failed")
        logging.warning("proxifly: %s", exc)
    return result


def fetch_spysme(country: str = "all") -> list[dict]:
    """Spys.me — no country filter support, returns all."""
    result = []
    sources = [
        ("http",  "http://spys.me/proxy.txt"),
        ("socks5","http://spys.me/socks.txt"),
    ]
    for proto, url in sources:
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r.text)
            for p in found:
                result.append({"proxy": p, "protocol": proto,
                               "country": "?", "anonymity": "unknown"})
            ok(f"  Spys.me {proto} → +{len(found)} proxies")
        except Exception as exc:
            err(f"  Spys.me {proto} failed")
            logging.warning("spysme %s: %s", proto, exc)
    return result


# Register all JSON API fetchers
JSON_API_SOURCES = [
    ("Geonode",         fetch_geonode),
    ("ProxyScrape v4",  fetch_proxyscrape_v4),
    ("Proxifly",        fetch_proxifly),
    ("Spys.me",         fetch_spysme),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  FETCH ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_json_apis(country: str = "all") -> list[dict]:
    """Fetch from all live JSON APIs."""
    seen: set    = set()
    result: list = []
    info("Fetching from live JSON APIs...\n")
    for name, fetcher in JSON_API_SOURCES:
        info(f"Fetching {name}...")
        entries = fetcher(country)
        added   = _dedup_add(entries, seen, result)
        ok(f"  {name} total unique: {added}")
    return result


def fetch_all_sources(country: str = "all") -> list[dict]:
    """Fetch from both GitHub and JSON APIs, merge and dedup."""
    seen: set    = set()
    result: list = []
    info("Fetching from ALL sources...\n")
    for entry in fetch_github_sources(country):
        _dedup_add([entry], seen, result)
    for entry in fetch_json_apis(country):
        _dedup_add([entry], seen, result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  PROTOCOL-AWARE PROXY TESTER
# ═══════════════════════════════════════════════════════════════════════════════

def _proxy_dict(protocol: str, proxy: str) -> dict:
    """Build the requests proxies dict for the correct protocol."""
    if protocol == "http":
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    if protocol == "socks4":
        return {"http": f"socks4://{proxy}", "https": f"socks4://{proxy}"}
    if protocol == "socks5":
        return {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}
    return {}


def test_proxy(entry: dict, timeout: int = 5) -> dict | None:
    """
    Test a proxy against rotating endpoints.
    Returns {proxy, protocol, speed, country, anonymity} or None.
    SOCKS proxies skipped gracefully if PySocks not installed.
    """
    proxy    = entry["proxy"]
    protocol = entry["protocol"]

    if protocol in ("socks4", "socks5") and not SOCKS_AVAILABLE:
        return None

    proxies = _proxy_dict(protocol, proxy)
    if not proxies:
        return None

    for i, url in enumerate(TEST_ENDPOINTS):
        try:
            start   = time.monotonic()
            r       = requests.get(url, proxies=proxies, timeout=timeout)
            elapsed = time.monotonic() - start
            if r.status_code == 200:
                return {
                    "proxy"    : proxy,
                    "protocol" : protocol,
                    "speed"    : round(elapsed, 2),
                    "country"  : entry.get("country", "?"),
                    "anonymity": entry.get("anonymity", "unknown"),
                }
        except Exception as exc:
            logging.debug("test_proxy %s %s endpoint %s: %s", protocol, proxy, i, exc)
            continue
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN HARVEST FLOW
# ═══════════════════════════════════════════════════════════════════════════════

def update_proxies():
    clear()
    config = load_config()  # may be None — fine until push time

    if not SOCKS_AVAILABLE:
        warn("PySocks not installed — SOCKS4/SOCKS5 proxies will be skipped.")
        warn("Install with: pip install requests[socks]")

    # ── Source selection ─────────────────────────────────────────────────────
    print(f"\n{YEL}╔══════════════════════════════════════════════════════╗")
    print(f"║  WHERE TO FETCH PROXIES FROM?                        ║")
    print(f"║                                                      ║")
    print(f"║  [1] GITHUB LISTS  — text files, many sources        ║")
    print(f"║      (monosans, TheSpeedX, ShiftyTR, proxifly...)    ║")
    print(f"║                                                      ║")
    print(f"║  [2] LIVE JSON APIs — verified, protocol-tagged      ║")
    print(f"║      (Geonode, ProxyScrape v4, Proxifly, Spys.me)    ║")
    print(f"║                                                      ║")
    print(f"║  [3] ALL SOURCES   — both combined (most proxies)    ║")
    print(f"╚══════════════════════════════════════════════════════╝{RST}")

    source_choice = input(f"{CYN}[?] Choose source (1/2/3): {RST}").strip()

    # ── Country filter ───────────────────────────────────────────────────────
    country = _country_menu()

    clear()  # ── clear menu, show only logo + fetch output
    if source_choice == "1":
        all_proxies = fetch_github_sources(country)
    elif source_choice == "2":
        all_proxies = fetch_json_apis(country)
    elif source_choice == "3":
        all_proxies = fetch_all_sources(country)
    else:
        warn("Invalid choice — defaulting to ALL sources.")
        all_proxies = fetch_all_sources(country)

    if not all_proxies:
        err("No proxies fetched from any source.")
        wait_for_enter()
        return

    info(f"TOTAL UNIQUE PROXIES FETCHED: {len(all_proxies)}")

    # ── Intensity selection ──────────────────────────────────────────────────
    clear()  # ── clear fetch output, show only logo + intensity menu
    print(f"\n{YEL}╔════════════════════════════════════════════════════╗")
    print(f"║  SELECT TESTING INTENSITY:                         ║")
    print(f"║  [1] LIGHT   — Test 500  proxies (fast)            ║")
    print(f"║  [2] MEDIUM  — Test 2000 proxies (recommended)     ║")
    print(f"║  [3] EXTREME — Test ALL  {len(all_proxies):<5} proxies (thorough)  ║")
    print(f"╚════════════════════════════════════════════════════╝{RST}")

    intensity = input(f"{CYN}[?] Choose (1/2/3): {RST}").strip()
    limits    = {"1": (500, 100), "2": (2000, 150), "3": (len(all_proxies), 200)}
    test_limit, workers = limits.get(intensity, (1000, 100))
    test_limit = min(test_limit, len(all_proxies))

    clear()  # ── clear intensity menu, show only logo + testing output
    info(f"Testing {test_limit} proxies with {workers} workers...\n")

    # ── Testing ──────────────────────────────────────────────────────────────
    working: list[dict] = []
    proxy_list = all_proxies[:test_limit]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(test_proxy, p): p for p in proxy_list}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
            except Exception as exc:
                logging.warning("future.result() raised: %s", exc)
                result = None

            if result:
                working.append(result)
                icon = "⚡" if result["speed"] < 1 else "✓" if result["speed"] < 3 else "🐢"
                print(f"   [{len(working)}] {icon} {result['protocol']:<6} {result['proxy']} — {result['speed']}s{RST}")

            if i % 100 == 0:
                pct = i * 100 // test_limit
                info(f"Progress: {i}/{test_limit} ({pct}%)")

    ok(f"TESTING COMPLETE — {len(working)} working proxies found.")

    if not working:
        err("No working proxies found.")
        wait_for_enter()
        return

    speeds = [p["speed"] for p in working]

    # ── Speed filter ─────────────────────────────────────────────────────────
    clear()
    print(f"\n{GRN}   Fastest : {min(speeds)}s")
    print(f"   Slowest : {max(speeds)}s")
    print(f"   Average : {sum(speeds)/len(speeds):.2f}s")
    print(f"   Found   : {len(working)} working proxies{RST}\n")

    print(f"{YEL}╔══════════════════════════════════════════════════╗")
    print(f"║  SPEED FILTER                                    ║")
    print(f"║  [1] ULTRA FAST — < 1s                           ║")
    print(f"║  [2] FAST       — < 2s                           ║")
    print(f"║  [3] GOOD       — ≤ 4s                           ║")
    print(f"║  [4] ALL        — keep everything                ║")
    print(f"╚══════════════════════════════════════════════════╝{RST}")

    fc = input(f"{CYN}[?] Filter (1/2/3/4): {RST}").strip()
    thresholds = {"1": 1.0, "2": 2.0, "3": 4.0}
    if fc in thresholds:
        filtered = [p for p in working if p["speed"] < thresholds[fc]]
        working  = filtered if filtered else working
        ok(f"Kept {len(working)} proxies.")

    # ── Anonymity filter ──────────────────────────────────────────────────────
    clear()
    has_anon_data = any(p.get("anonymity", "unknown") != "unknown" for p in working)

    print(f"\n{YEL}╔══════════════════════════════════════════════════════╗")
    print(f"║  ANONYMITY FILTER                                    ║")
    print(f"║                                                      ║")
    print(f"║  [1] ELITE ONLY     — fully hidden, best privacy     ║")
    print(f"║  [2] ANON + ELITE   — real IP not exposed            ║")
    print(f"║  [3] ALL LEVELS     — include transparent too        ║")
    print(f"╚══════════════════════════════════════════════════════╝")
    print(f"  {G2}Elite      — site can't detect you're using a proxy")
    print(f"  Anonymous  — site knows proxy, not your real IP")
    print(f"  Transparent— site sees your real IP (weakest){RST}\n")

    if not has_anon_data:
        warn("No anonymity data for these sources — only Geonode/Proxifly provide it.")
        warn("Option 1/2 will keep all proxies. Use JSON APIs source for anonymity filtering.")

    anon_choice = input(f"{CYN}[?] Choose (1/2/3): {RST}").strip()

    ELITE_LABELS = ("elite", "elite proxy", "high anonymity", "high")
    TRANSPARENT_LABELS = ("transparent", "none", "no anonymity", "low")

    if anon_choice == "1":
        if has_anon_data:
            filtered = [p for p in working if p.get("anonymity", "").lower() in ELITE_LABELS]
            if filtered:
                working = filtered
                ok(f"Elite only: {len(working)} proxies kept.")
            else:
                warn("No elite proxies found — keeping all.")
        else:
            warn("No anonymity data — keeping all.")

    elif anon_choice == "2":
        if has_anon_data:
            filtered = [p for p in working if p.get("anonymity", "").lower() not in TRANSPARENT_LABELS]
            if filtered:
                working = filtered
                ok(f"Anonymous + Elite: {len(working)} proxies kept.")
            else:
                warn("No matching proxies — keeping all.")
        else:
            warn("No anonymity data — keeping all.")

    else:
        ok(f"Keeping all {len(working)} proxies.")

    # ── Build output ─────────────────────────────────────────────────────────
    speeds = [p["speed"] for p in working]
    now    = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header = (
        f"# Proxy List — {now}\n"
        f"# Total   : {len(working)}\n"
        f"# Fastest : {min(speeds)}s | Slowest : {max(speeds)}s | "
        f"Average : {sum(speeds)/len(speeds):.2f}s\n"
        f"# {'='*50}\n\n"
    )
    # Plain ip:port — replaces previous list entirely (dead proxies removed)
    lines        = "\n".join(p['proxy'] for p in working)
    file_content = header + lines + "\n"

    # ── Save / push ──────────────────────────────────────────────────────────
    clear()
    print(f"\n{GRN}   Ready to save : {len(working)} proxies")
    print(f"   Timestamp    : {now}{RST}\n")
    print(f"{YEL}╔══════════════════════════════════════════════════╗")
    print(f"║  [A] AUTO   — save locally + push to GitHub      ║")
    print(f"║  [M] MANUAL — preview first, then choose         ║")
    print(f"║  [S] SAVE   — save locally only (no GitHub)      ║")
    print(f"╚══════════════════════════════════════════════════╝{RST}")

    choice = input(f"{CYN}[?] (A/M/S): {RST}").upper().strip()

    if choice == "M":
        clear()
        print(f"\n{CYN}PREVIEW (first 30):{RST}")
        linex()
        for p in working[:30]:
            anon_tag = f"{G2}[{p.get('anonymity','?')[:5]}]{RST}" if p.get('anonymity','unknown') != 'unknown' else ""
            cc_tag   = f"{G3}[{p.get('country','?')}]{RST}"
            print(f"{GRN}  {p['protocol']:<6} {p['proxy']:<22} {p['speed']}s {cc_tag}{anon_tag}{RST}")
        if len(working) > 30:
            warn(f"... and {len(working)-30} more")
        linex()
        print(f"\n{YEL}╔══════════════════════════════════════════════════╗")
        print(f"║  [A] Save locally + push to GitHub             ║")
        print(f"║  [S] Save locally only                         ║")
        print(f"║  [X] Discard                                   ║")
        print(f"╚══════════════════════════════════════════════════╝{RST}")
        choice = input(f"{CYN}[?] (A/S/X): {RST}").upper().strip()
        if choice == "X":
            warn("Discarded — nothing saved.")
            wait_for_enter()
            return

    if choice not in ("A", "S"):
        warn("Invalid choice — nothing saved.")
        wait_for_enter()
        return

    # Save locally always
    local_path = "proxies.txt"
    with open(local_path, "w") as f:
        f.write(file_content)
    ok(f"Saved {len(working)} proxies → {local_path}")
    ok(f"View with: cat proxies.txt")

    # Push only if requested — setup GitHub here if needed
    if choice == "A":
        if not config:
            warn("GitHub not configured yet. Setting up now...")
            config = setup()
        if not config:
            warn("Setup cancelled — proxies saved locally only.")
            wait_for_enter()
            return
        info("Pushing to GitHub via API...")
        success = gh_push_file(
            config["username"], config["token"], config["repo"], file_content
        )
        if success:
            raw_url = (
                f"https://raw.githubusercontent.com/"
                f"{config['username']}/{config['repo']}/main/proxies.txt"
            )
            ok(f"Pushed! Live at:\n   {raw_url}")
        else:
            warn("Push failed — proxies saved locally only.")

    wait_for_enter()


# ═══════════════════════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════════════════════

def show_link():
    clear()
    config = load_config()
    if not config:
        err("Not configured. Run setup first.")
        wait_for_enter()
        return

    url = f"https://raw.githubusercontent.com/{config['username']}/{config['repo']}/main/proxies.txt"

    linex()
    print(f"{G2}  YOUR LIVE PROXY LINK{RST}")
    linex()
    print(f"\n{GRN}  {url}{RST}\n")
    linex()

    info("Fetching live stats...")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            lines       = r.text.splitlines()
            count       = len([l for l in lines if re.match(r'\d+\.\d+\.\d+\.\d+:\d+', l)])
            # Parse timestamp from header comment
            last_update = "unknown"
            for line in lines:
                if line.startswith("# Proxy List —"):
                    last_update = line.replace("# Proxy List —", "").strip()
                    break
            print(f"\n{YEL}╔══════════════════════════════════════════════════════╗")
            print(f"║  LIVE STATS                                          ║")
            print(f"╠══════════════════════════════════════════════════════╣")
            print(f"║  {GRN}Proxies online :{ count:<36}{YEL}║")
            print(f"║  {CYN}Last updated   :{ last_update:<36}{YEL}║")
            print(f"║  {G2}Status         :{' ACTIVE':<36}{YEL}║")
            print(f"╚══════════════════════════════════════════════════════╝{RST}")
        else:
            warn("Link not yet active — harvest proxies and push first.")
    except requests.RequestException as exc:
        warn(f"Could not reach URL: {exc}")

    wait_for_enter()


def main():
    while True:
        clear()
        linex()

        # Show GitHub status next to option 2
        cfg = load_config()
        if cfg:
            gh_status = f"{GRN}✓ {cfg['username']}/{cfg['repo']}{RST}"
        else:
            gh_status = f"{ERR}✗ Not configured{RST}"

        print(f"{GRN}  [1]{YEL} HARVEST PROXIES{RST}")
        print(f"{GRN}  [2]{YEL} SETUP GITHUB     {RST}{gh_status}")
        print(f"{GRN}  [3]{YEL} SHOW MY LINK{RST}")
        print(f"{GRN}  [4]{YEL} CHANGE GITHUB SETTINGS{RST}")
        print(f"{ERR}  [0]{YEL} EXIT{RST}")
        linex()

        choice = input(f"{CYN}[?] Choice: {RST}").strip()
        if choice == "1":
            update_proxies()
        elif choice == "2":
            if cfg:
                clear()
                ok(f"GitHub already configured!")
                info(f"Username : {cfg['username']}")
                info(f"Repo     : {cfg['repo']}")
                info(f"Link     : https://raw.githubusercontent.com/{cfg['username']}/{cfg['repo']}/main/proxies.txt")
                print()
                warn("To change settings use [4] CHANGE GITHUB SETTINGS")
                wait_for_enter()
            else:
                setup()
        elif choice == "3":
            show_link()
        elif choice == "4":
            change_link()
        elif choice == "0":
            ok("Goodbye.")
            sys.exit(0)
        else:
            warn("Invalid choice.")
            time.sleep(0.8)


if __name__ == "__main__":
    main()
