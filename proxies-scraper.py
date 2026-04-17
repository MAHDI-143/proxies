#!/usr/bin/env python3
"""
Advanced Proxy Scraper & Validator
Features:
- Multiple proxy types (HTTP, HTTPS, SOCKS)
- Speed testing
- Auto-save to GitHub
"""

import requests
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import subprocess

# ============ CONFIGURATION ============
MAX_PROXIES_TO_TEST = 500  # How many proxies to test (max)
TEST_TIMEOUT = 5           # Seconds to wait for proxy response
THREADS = 50               # How many proxies to test at once
# ======================================

# Multiple proxy sources (where we get proxies from)
SOURCES = {
    "http": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    ],
    "socks4": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
    ],
    "socks5": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
    ]
}

def fetch_proxies_from_url(url, proxy_type):
    """Fetch proxies from a single URL"""
    proxies = []
    try:
        source_name = url.split('/')[2] if 'raw' in url else url.split('/')[2].split('?')[0]
        print(f"     Fetching: {source_name}...")
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            found = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b', response.text)
            for proxy in found:
                proxies.append({"proxy": proxy, "type": proxy_type})
            print(f"     ✓ Found {len(found)} proxies")
        else:
            print(f"     ✗ Failed: HTTP {response.status_code}")
        return proxies
    except Exception as e:
        print(f"     ✗ Failed: {str(e)[:50]}")
        return []

def fetch_all_proxies():
    """Fetch proxies from all sources"""
    all_proxies = []
    print("\n📡 FETCHING PROXIES FROM SOURCES")
    print("=" * 50)
    
    for proxy_type, urls in SOURCES.items():
        print(f"\n  [{proxy_type.upper()} proxies]")
        for url in urls:
            proxies = fetch_proxies_from_url(url, proxy_type)
            all_proxies.extend(proxies)
    
    # Remove duplicates (same IP:PORT)
    unique = {}
    for p in all_proxies:
        key = p["proxy"]
        if key not in unique:
            unique[key] = p
    
    print(f"\n📊 SUMMARY: Found {len(unique)} unique proxies")
    return list(unique.values())

def test_single_proxy(proxy_info):
    """Test if a single proxy works and measure its speed"""
    proxy = proxy_info["proxy"]
    proxy_type = proxy_info["type"]
    
    # Choose the right protocol for testing
    if proxy_type == "http":
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    elif proxy_type == "socks4":
        proxies = {"http": f"socks4://{proxy}", "https": f"socks4://{proxy}"}
    elif proxy_type == "socks5":
        proxies = {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}
    else:
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    
    try:
        start_time = time.time()
        response = requests.get(
            "http://httpbin.org/ip",
            proxies=proxies,
            timeout=TEST_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return {
                "proxy": proxy,
                "type": proxy_type,
                "speed": round(elapsed, 2),
                "working": True
            }
    except:
        pass
    
    return None

def test_proxies(proxies):
    """Test multiple proxies in parallel (faster)"""
    print(f"\n🧪 TESTING PROXIES")
    print("=" * 50)
    print(f"   Testing {min(len(proxies), MAX_PROXIES_TO_TEST)} proxies...")
    print(f"   Timeout: {TEST_TIMEOUT}s | Threads: {THREADS}")
    print("\n   Results:")
    
    working = []
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(test_single_proxy, p): p for p in proxies[:MAX_PROXIES_TO_TEST]}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                working.append(result)
                speed_indicator = "⚡" if result["speed"] < 2 else "🐢" if result["speed"] > 4 else "✓"
                print(f"   {speed_indicator} {result['proxy']} [{result['type']}] - {result['speed']}s")
    
    return working

def save_proxies(proxies):
    """Save proxies to files"""
    # Save simple format (just IP:PORT)
    with open("proxies.txt", "w") as f:
        for p in proxies:
            f.write(f"{p['proxy']}\n")
    print(f"\n💾 Saved {len(proxies)} proxies to proxies.txt")
    
    # Save detailed format (with speed and type)
    with open("proxies_detailed.json", "w") as f:
        json.dump(proxies, f, indent=2)
    print(f"💾 Saved detailed info to proxies_detailed.json")
    
    # Save by type
    http_proxies = [p for p in proxies if p['type'] == 'http']
    socks4_proxies = [p for p in proxies if p['type'] == 'socks4']
    socks5_proxies = [p for p in proxies if p['type'] == 'socks5']
    
    if http_proxies:
        with open("http_proxies.txt", "w") as f:
            for p in http_proxies:
                f.write(f"{p['proxy']}\n")
        print(f"💾 Saved {len(http_proxies)} HTTP proxies to http_proxies.txt")
    
    if socks4_proxies:
        with open("socks4_proxies.txt", "w") as f:
            for p in socks4_proxies:
                f.write(f"{p['proxy']}\n")
        print(f"💾 Saved {len(socks4_proxies)} SOCKS4 proxies to socks4_proxies.txt")
    
    if socks5_proxies:
        with open("socks5_proxies.txt", "w") as f:
            for p in socks5_proxies:
                f.write(f"{p['proxy']}\n")
        print(f"💾 Saved {len(socks5_proxies)} SOCKS5 proxies to socks5_proxies.txt")

def push_to_github():
    """Auto-push to GitHub if in a git repo"""
    try:
        result = subprocess.run(["git", "status"], capture_output=True, text=True)
        
        if "not a git repository" in result.stderr:
            print("\n⚠️  Not in a git repository. Skipping GitHub push.")
            print("   To enable auto-push, run: git init && git remote add origin YOUR_URL")
            return
        
        subprocess.run(["git", "add", "proxies.txt", "proxies_detailed.json", "http_proxies.txt", "socks4_proxies.txt", "socks5_proxies.txt"], capture_output=True)
        
        commit_msg = f"Auto-update proxies {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)
        
        push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
        
        if push_result.returncode == 0:
            print("✅ Successfully pushed to GitHub!")
        else:
            print(f"⚠️  Push failed: {push_result.stderr[:100]}")
            
    except Exception as e:
        print(f"⚠️  GitHub push error: {e}")

def show_statistics(proxies):
    """Display nice statistics about the proxies"""
    print("\n" + "=" * 50)
    print("📊 PROXY STATISTICS")
    print("=" * 50)
    
    http_count = len([p for p in proxies if p['type'] == 'http'])
    socks4_count = len([p for p in proxies if p['type'] == 'socks4'])
    socks5_count = len([p for p in proxies if p['type'] == 'socks5'])
    
    print(f"   Total working: {len(proxies)}")
    print(f"   ├─ HTTP:  {http_count}")
    print(f"   ├─ SOCKS4: {socks4_count}")
    print(f"   └─ SOCKS5: {socks5_count}")
    
    if proxies:
        speeds = [p['speed'] for p in proxies]
        fastest = min(speeds)
        slowest = max(speeds)
        average = sum(speeds) / len(speeds)
        
        print(f"\n   Speed Stats:")
        print(f"   ├─ Fastest:  {fastest}s")
        print(f"   ├─ Slowest:  {slowest}s")
        print(f"   └─ Average:  {average:.2f}s")
        
        fastest_proxies = sorted(proxies, key=lambda x: x['speed'])[:5]
        print(f"\n   🚀 Top 5 Fastest Proxies:")
        for i, p in enumerate(fastest_proxies, 1):
            print(f"      {i}. {p['proxy']} [{p['type']}] - {p['speed']}s")

def main():
    print("=" * 50)
    print("🚀 ADVANCED PROXY SCRAPER v2.0")
    print("=" * 50)
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_proxies = fetch_all_proxies()
    
    if not all_proxies:
        print("\n❌ No proxies found! Try again later.")
        return
    
    working_proxies = test_proxies(all_proxies)
    
    if not working_proxies:
        print("\n❌ No working proxies found!")
        return
    
    save_proxies(working_proxies)
    show_statistics(working_proxies)
    
    print("\n" + "=" * 50)
    response = input("📤 Push to GitHub? (y/n): ").lower()
    
    if response == 'y':
        push_to_github()
    
    print("\n✅ Done! Run this script again later for fresh proxies.")

if __name__ == "__main__":
    main()
