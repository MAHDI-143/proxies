#!/usr/bin/env python3
import os
import sys
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import subprocess

# Colors
G = "\033[38;5;46m"
GGG = "\033[38;5;49m"
XX = "\033[1;92m"

# Your Logo
logo = (f"""
╔━━━━━━━━━━━━━━━━━━━━━━╗━━━━━━━━━━━╗
║      \x1b[38;5;47m┳┳┓┏┓┓┏┳┓┳      ║143/B/M    ║
║      \x1b[38;5;49m┃┃┃┣┫┣┫┃┃┃      ║XTM        ║
║      \x1b[38;5;50m┛ ┗┛┗┛┗┻┛┻      ║VERSION:2.0║
╚━━━━━━━━━━━━━━━━━━━━━━╝━━━━━━━━━━━╝
{G}⋆{GGG}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{G}⋆
\x1b[1;92m {XX}[\x1b[1;92m⍣{XX}]\x1b[38;5;46m OWNER     : MAHDI            
\x1b[1;92m {XX}[\x1b[1;92m⍣{XX}] \x1b[38;5;47mFACEBOOK  : MAHDI           
\x1b[1;92m {XX}[\x1b[1;92m⍣{XX}] \x1b[38;5;48mGITHUB    : MAHDI-143         
{G}⋆{GGG}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{G}⋆""")

def linex():
    print(f'{G}⋆{GGG}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{G}⋆')

def clear():
    os.system('clear')
    print(logo)
    print()

def update_proxies():
    print("\n\x1b[96m[+] FETCHING PROXIES...\x1b[0m")
    
    sources = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    ]
    
    proxies = set()
    for url in sources:
        try:
            r = requests.get(url, timeout=10)
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r.text)
            proxies.update(found)
            print(f"\x1b[92m[✓] Got {len(found)} proxies\x1b[0m")
        except:
            print(f"\x1b[91m[✗] Failed: {url}\x1b[0m")
    
    print(f"\n\x1b[96m[+] TESTING {len(proxies)} PROXIES...\x1b[0m")
    
    def test(proxy):
        try:
            start = time.time()
            r = requests.get("http://httpbin.org/ip", proxies={"http": f"http://{proxy}"}, timeout=5)
            elapsed = time.time() - start
            if r.status_code == 200:
                return {"proxy": proxy, "speed": round(elapsed, 2)}
        except:
            pass
        return None
    
    working = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(test, p) for p in list(proxies)[:300]]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working.append(result)
                speed_indicator = "⚡" if result["speed"] < 2 else "🐢" if result["speed"] > 4 else "✓"
                print(f"\x1b[92m   {speed_indicator} {result['proxy']} [http] - {result['speed']}s\x1b[0m")
    
    with open("proxies.txt", "w") as f:
        for p in working:
            f.write(f"{p['proxy']}\n")
    
    print(f"\n\x1b[92m[✓] SAVED {len(working)} WORKING PROXIES\x1b[0m")
    
    # Show speed stats
    if working:
        speeds = [p['speed'] for p in working]
        print(f"\n\x1b[96m[+] SPEED STATS:\x1b[0m")
        print(f"   \x1b[92mFastest: {min(speeds)}s\x1b[0m")
        print(f"   \x1b[93mSlowest: {max(speeds)}s\x1b[0m")
        print(f"   \x1b[96mAverage: {sum(speeds)/len(speeds):.2f}s\x1b[0m")
    
    print("\n\x1b[96m[+] PUSHING TO GITHUB...\x1b[0m")
    subprocess.run(["git", "add", "proxies.txt"], capture_output=True)
    subprocess.run(["git", "commit", "-m", f"update {datetime.now()}"], capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], capture_output=True)
    print("\x1b[92m[✓] UPLOADED TO GITHUB\x1b[0m")
    
    input("\n\x1b[93m[+] Press Enter to continue...\x1b[0m")

def show_proxies():
    try:
        with open("proxies.txt", "r") as f:
            proxies = f.read().splitlines()
        print(f"\n\x1b[96m[+] TOTAL PROXIES: {len(proxies)}\x1b[0m")
        linex()
        for i, proxy in enumerate(proxies[:20], 1):
            print(f"\x1b[92m[{i}] {proxy}\x1b[0m")
        if len(proxies) > 20:
            print(f"\x1b[93m... and {len(proxies)-20} more\x1b[0m")
    except:
        print("\x1b[91m[✗] No proxies found! Run update first.\x1b[0m")
    input("\n\x1b[93m[+] Press Enter to continue...\x1b[0m")

def get_link():
    linex()
    print("\n\x1b[96m[+] YOUR PROXY LINK:\x1b[0m")
    print("\x1b[92mhttps://raw.githubusercontent.com/MAHDI-143/proxies/main/proxies.txt\x1b[0m")
    linex()
    input("\n\x1b[93m[+] Press Enter to continue...\x1b[0m")

def about():
    linex()
    print("\n\x1b[96m[+] ABOUT XTM\x1b[0m")
    print("\x1b[92mTool     : XTM Proxy Master\x1b[0m")
    print("\x1b[92mVersion  : 2.0\x1b[0m")
    print("\x1b[92mOwner    : MAHDI\x1b[0m")
    print("\x1b[92mGitHub   : MAHDI-143\x1b[0m")
    print("\x1b[92mPurpose  : Auto proxy scraper & tester\x1b[0m")
    linex()
    input("\n\x1b[93m[+] Press Enter to continue...\x1b[0m")

def main():
    while True:
        clear()
        print("\x1b[93m    [1] UPDATE PROXIES\x1b[0m")
        print("\x1b[93m    [2] SHOW PROXIES\x1b[0m")
        print("\x1b[93m    [3] GET LINK\x1b[0m")
        print("\x1b[93m    [4] ABOUT\x1b[0m")
        print("\x1b[93m    [5] EXIT\x1b[0m")
        linex()
        
        choice = input("\x1b[96m[?] PUT FILE NAME : \x1b[0m")
        
        if choice == "1":
            update_proxies()
        elif choice == "2":
            show_proxies()
        elif choice == "3":
            get_link()
        elif choice == "4":
            about()
        elif choice == "5":
            print("\n\x1b[92m[+] GOODBYE! THANKS FOR USING XTM\x1b[0m")
            sys.exit()
        else:
            print("\x1b[91m[✗] INVALID CHOICE!\x1b[0m")
            time.sleep(1)

if __name__ == "__main__":
    main()
