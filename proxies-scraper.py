#!/usr/bin/env python3
import requests
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import subprocess

MAX_PROXIES_TO_TEST = 500
TEST_TIMEOUT = 5
THREADS = 50

SOURCES = {
    "http": [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    ]
}

def fetch_proxies_from_url(url, proxy_type):
    proxies = []
    try:
        print(f"     Fetching: {url.split('/')[2]}...")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            found = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b', response.text)
            for proxy in found:
                proxies.append({"proxy": proxy, "type": proxy_type})
        print(f"     ✓ Found {len(found)} proxies")
        return proxies
    except Exception as e:
        print(f"     ✗ Failed: {str(e)[:50]}")
        return []

def fetch_all_proxies():
    all_proxies = []
    print("\n📡 FETCHING PROXIES FROM SOURCES")
    print("=" * 50)
    for proxy_type, urls in SOURCES.items():
        print(f"\n  [{proxy_type.upper()} proxies]")
        for url in urls:
            proxies = fetch_proxies_from_url(url, proxy_type)
            all_proxies.extend(proxies)
    unique = {}
    for p in all_proxies:
        key = p["proxy"]
        if key not in unique:
            unique[key] = p
    print(f"\n📊 SUMMARY: Found {len(unique)} unique proxies")
    return list(unique.values())

def test_single_proxy(proxy_info):
    proxy = proxy_info["proxy"]
    proxy_type = proxy_info["type"]
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        start_time = time.time()
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=TEST_TIMEOUT)
        elapsed = time.time() - start_time
        if response.status_code == 200:
            return {"proxy": proxy, "type": proxy_type, "speed": round(elapsed, 2), "working": True}
    except:
        pass
    return None

def test_proxies(proxies):
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

def save_and_push(proxies):
    with open("proxies.txt", "w") as f:
        for p in proxies:
            f.write(f"{p['proxy']}\n")
    print(f"\n💾 Saved {len(proxies)} proxies to proxies.txt")
    
    print("\n📤 Auto-pushing to GitHub...")
    subprocess.run(["git", "add", "proxies.txt"], capture_output=True)
    subprocess.run(["git", "commit", "-m", f"auto-update {datetime.now().strftime('%Y-%m-%d %H:%M')}"], capture_output=True)
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Successfully pushed to GitHub!")
    else:
        print(f"⚠️ Push failed: {result.stderr[:100]}")

def show_statistics(proxies):
    print("\n" + "=" * 50)
    print("📊 PROXY STATISTICS")
    print("=" * 50)
    print(f"   Total working: {len(proxies)}")
    if proxies:
        speeds = [p['speed'] for p in proxies]
        print(f"   ├─ Fastest: {min(speeds)}s")
        print(f"   ├─ Slowest: {max(speeds)}s")
        print(f"   └─ Average: {sum(speeds)/len(speeds):.2f}s")
        fastest = sorted(proxies, key=lambda x: x['speed'])[:5]
        print(f"\n   🚀 Top 5 Fastest:")
        for i, p in enumerate(fastest, 1):
            print(f"      {i}. {p['proxy']} - {p['speed']}s")

def main():
    print("=" * 50)
    print("🚀 PROXY SCRAPER - AUTO MODE")
    print("=" * 50)
    
    all_proxies = fetch_all_proxies()
    if not all_proxies:
        print("\n❌ No proxies found!")
        return
    
    working_proxies = test_proxies(all_proxies)
    if not working_proxies:
        print("\n❌ No working proxies found!")
        return
    
    save_and_push(working_proxies)
    show_statistics(working_proxies)
    print("\n✅ Done! Proxies updated automatically.")

if __name__ == "__main__":
    main()
