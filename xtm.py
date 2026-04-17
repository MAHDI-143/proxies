#!/usr/bin/env python3
import os
import sys
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import subprocess

os.system("clear" if os.name == "posix" else "cls")

def banner():
    print("\033[91m" + "=" * 50 + "\033[0m")
    print("\033[93m" + "    143/B/M" + "\033[0m")
    print("\033[92m" + "         XTM" + "\033[0m")
    print("\033[96m" + "      VERSION: 2.0" + "\033[0m")
    print("\033[91m" + "=" * 50 + "\033[0m")
    print()
    print("\033[92m[*] OWNER    : MAHDI\033[0m")
    print("\033[92m[*] FACEBOOK : MAHDI\033[0m")
    print("\033[92m[*] GITHUB   : MAHDI-143\033[0m")
    print("\033[92m[*] VERSION  : 2.0\033[0m")
    print()
    print("\033[93m" + "=" * 50 + "\033[0m")
    print()

def update_proxies():
    print("\n\033[96m[+] FETCHING PROXIES...\033[0m")
    
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
            print(f"\033[92m[✓] Got {len(found)} proxies\033[0m")
        except:
            print(f"\033[91m[✗] Failed: {url}\033[0m")
    
    print(f"\n\033[96m[+] TESTING {len(proxies)} PROXIES...\033[0m")
    
    def test(p):
        try:
            r = requests.get("http://httpbin.org/ip", proxies={"http": f"http://{p}"}, timeout=5)
            return p if r.status_code == 200 else None
        except:
            return None
    
    working = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        for result in ex.map(test, list(proxies)[:300]):
            if result:
                working.append(result)
                print(f"\033[92m[✓] {result}\033[0m")
    
    with open("proxies.txt", "w") as f:
        f.write("\n".join(working))
    
    print(f"\n\033[92m[✓] SAVED {len(working)} WORKING PROXIES\033[0m")
    
    # Auto push to GitHub
    print("\n\033[96m[+] PUSHING TO GITHUB...\033[0m")
    subprocess.run(["git", "add", "proxies.txt"], capture_output=True)
    subprocess.run(["git", "commit", "-m", f"update {datetime.now()}"], capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], capture_output=True)
    print("\033[92m[✓] UPLOADED TO GITHUB\033[0m")
    
    input("\n\033[93m[+] Press Enter to continue...\033[0m")

def show_proxies():
    try:
        with open("proxies.txt", "r") as f:
            proxies = f.read().splitlines()
        print(f"\n\033[96m[+] TOTAL PROXIES: {len(proxies)}\033[0m")
        print("\033[93m" + "-" * 40 + "\033[0m")
        for i, proxy in enumerate(proxies[:20], 1):
            print(f"\033[92m[{i}] {proxy}\033[0m")
        if len(proxies) > 20:
            print(f"\033[93m... and {len(proxies)-20} more\033[0m")
    except:
        print("\033[91m[✗] No proxies found! Run update first.\033[0m")
    input("\n\033[93m[+] Press Enter to continue...\033[0m")

def get_link():
    print("\n\033[96m[+] YOUR PROXY LINK:\033[0m")
    print("\033[92mhttps://raw.githubusercontent.com/MAHDI-143/proxies/main/proxies.txt\033[0m")
    input("\n\033[93m[+] Press Enter to continue...\033[0m")

def about():
    print("\n\033[96m[+] ABOUT XTM\033[0m")
    print("\033[93m" + "-" * 40 + "\033[0m")
    print("\033[92mTool     : XTM Proxy Master\033[0m")
    print("\033[92mVersion  : 2.0\033[0m")
    print("\033[92mOwner    : MAHDI\033[0m")
    print("\033[92mGitHub   : MAHDI-143\033[0m")
    print("\033[92mPurpose  : Auto proxy scraper & tester\033[0m")
    input("\n\033[93m[+] Press Enter to continue...\033[0m")

def main():
    while True:
        os.system("clear" if os.name == "posix" else "cls")
        banner()
        print("\033[93m    [1] UPDATE PROXIES\033[0m")
        print("\033[93m    [2] SHOW PROXIES\033[0m")
        print("\033[93m    [3] GET LINK\033[0m")
        print("\033[93m    [4] ABOUT\033[0m")
        print("\033[93m    [5] EXIT\033[0m")
        print("\033[91m" + "=" * 50 + "\033[0m")
        
        choice = input("\033[96m[?] PUT FILE NAME : \033[0m")
        
        if choice == "1":
            update_proxies()
        elif choice == "2":
            show_proxies()
        elif choice == "3":
            get_link()
        elif choice == "4":
            about()
        elif choice == "5":
            print("\n\033[92m[+] GOODBYE! THANKS FOR USING XTM\033[0m")
            sys.exit()
        else:
            print("\033[91m[✗] INVALID CHOICE!\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    main()
