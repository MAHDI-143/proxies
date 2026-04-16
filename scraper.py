import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

print("🔄 Fetching proxies...")

sources = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
]

all_proxies = set()

for url in sources:
    try:
        r = requests.get(url, timeout=10)
        proxies = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b', r.text)
        all_proxies.update(proxies)
        print(f"✓ Got {len(proxies)} from {url.split('/')[2]}")
    except:
        print(f"✗ Failed: {url.split('/')[2]}")

print(f"\n📊 Total unique: {len(all_proxies)}")
print("\n🧪 Testing proxies...")

working = []

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = []
    for proxy in list(all_proxies)[:200]:
        futures.append(executor.submit(
            lambda p: p if requests.get("http://httpbin.org/ip", 
                       proxies={"http": f"http://{p}"}, timeout=5).status_code == 200 else None,
            proxy
        ))
    
    for future in as_completed(futures):
        result = future.result()
        if result:
            working.append(result)
            print(f"  ✅ {result}")

with open("proxies.txt", "w") as f:
    f.write("\n".join(working))

print(f"\n✨ Saved {len(working)} working proxies to proxies.txt")
