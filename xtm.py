#!/usr/bin/env python3
import os
import sys
import subprocess
import time

# Auto-install missing packages
def install_packages():
    """Check and install required packages"""
    required = ["python", "git", "requests"]
    missing = []
    
    try:
        subprocess.run(["python", "--version"], capture_output=True, check=True)
    except:
        missing.append("python")
    
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except:
        missing.append("git")
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    if missing:
        print("\n\033[93m[!] Missing packages detected!\033[0m")
        print(f"\033[96m[+] Installing: {', '.join(missing)}\033[0m")
        
        for pkg in missing:
            if pkg in ["python", "git"]:
                os.system(f"pkg install {pkg} -y")
            elif pkg == "requests":
                os.system("pip install requests")
        
        print("\033[92m[✓] All packages installed!\033[0m")
        time.sleep(1)
        return True
    return False

install_packages()

import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Colors
G = "\033[38;5;46m"
GGG = "\033[38;5;49m"
XX = "\033[1;92m"

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

def wait():
    input("\n\033[93m[+] Press Enter to continue...\033[0m")

def harvest():
    clear()
    print("\n\033[96m[+] FETCHING PROXIES FROM LATEST SOURCES...\033[0m")
    
    # UPDATED: Latest and most active proxy sources (2025-2026)
    sources = [
        # monosans - hourly verified, best quality
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        
        # TheSpeedX - daily updated, large volume
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        
        # ProxyScrape - real-time (minutes)
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
    ]
    
    proxies = set()
    for url in sources:
        try:
            r = requests.get(url, timeout=15)
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r.text)
            proxies.update(found)
            source_name = url.split('/')[2] if 'raw' in url else url.split('/')[2].split('?')[0]
            print(f"\033[92m[✓] Got {len(found)} from {source_name}\033[0m")
        except:
            source_name = url.split('/')[2] if 'raw' in url else url.split('/')[2].split('?')[0]
            print(f"\033[91m[✗] Failed: {source_name}\033[0m")
    
    print(f"\n\033[96m[+] TOTAL UNIQUE PROXIES: {len(proxies)}\033[0m")
    print(f"\n\033[96m[+] TESTING PROXIES (This may take a minute)...\033[0m")
    
    def test(proxy):
        try:
            start = time.time()
            r = requests.get("http://httpbin.org/ip", proxies={"http": f"http://{proxy}"}, timeout=5)
            if r.status_code == 200:
                return {"proxy": proxy, "speed": round(time.time() - start, 2)}
        except:
            pass
        return None
    
    working = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(test, p) for p in list(proxies)[:500]]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working.append(result)
                emoji = "⚡" if result["speed"] < 2 else "🐢" if result["speed"] > 4 else "✓"
                print(f"\033[92m   {emoji} {result['proxy']} - {result['speed']}s\033[0m")
    
    with open("proxies.txt", "w") as f:
        for p in working:
            f.write(f"{p['proxy']}\n")
    
    print(f"\n\033[92m[✓] SAVED {len(working)} WORKING PROXIES\033[0m")
    
    if working:
        speeds = [p['speed'] for p in working]
        print(f"\n\033[96m[+] SPEED STATS:\033[0m")
        print(f"   \033[92mFastest: {min(speeds)}s\033[0m")
        print(f"   \033[93mSlowest: {max(speeds)}s\033[0m")
        print(f"   \033[96mAverage: {sum(speeds)/len(speeds):.2f}s\033[0m")
    
    print(f"\n\033[92m[✓] Proxies saved to: proxies.txt\033[0m")
    wait()

def view_proxies():
    clear()
    try:
        with open("proxies.txt", "r") as f:
            proxies = f.read().splitlines()
        
        print(f"\n\033[96m[+] TOTAL PROXIES: {len(proxies)}\033[0m")
        linex()
        
        print("\033[93m[1] Show first 20\033[0m")
        print("\033[93m[2] Show all\033[0m")
        print("\033[93m[3] Show by range (e.g., 10-30)\033[0m")
        linex()
        choice = input("\033[96m[?] How to view? (1/2/3): \033[0m")
        
        if choice == "1":
            for i, p in enumerate(proxies[:20], 1):
                print(f"\033[92m[{i}] {p}\033[0m")
            if len(proxies) > 20:
                print(f"\033[93m... and {len(proxies)-20} more\033[0m")
        
        elif choice == "2":
            for i, p in enumerate(proxies, 1):
                print(f"\033[92m[{i}] {p}\033[0m")
        
        elif choice == "3":
            try:
                start = int(input("\033[96m[?] Start from: \033[0m"))
                end = int(input("\033[96m[?] End at: \033[0m"))
                for i, p in enumerate(proxies[start-1:end], start):
                    print(f"\033[92m[{i}] {p}\033[0m")
            except:
                print("\033[91m[✗] Invalid range!\033[0m")
        
        else:
            print("\033[91m[✗] Invalid choice!\033[0m")
    except:
        print("\033[91m[✗] No proxies found! Run harvest first.\033[0m")
    wait()

def copy_to_sdcard():
    clear()
    print("\n\033[96m[+] COPYING PROXIES TO SDCARD...\033[0m")
    try:
        sdcard_paths = ["/sdcard/", "/storage/emulated/0/", "/storage/sdcard0/"]
        success = False
        
        for path in sdcard_paths:
            try:
                os.system(f"cp proxies.txt {path} 2>/dev/null")
                if os.path.exists(f"{path}proxies.txt"):
                    print(f"\033[92m[✓] Copied to {path}proxies.txt\033[0m")
                    success = True
                    break
            except:
                pass
        
        if not success:
            print("\033[93m[!] Could not copy to SDCARD automatically\033[0m")
            print("\033[93m[!] Try manual copy: cp proxies.txt /sdcard/\033[0m")
    except:
        print("\033[91m[✗] Failed to copy to SDCARD\033[0m")
    wait()

def share_file():
    clear()
    print("\n\033[96m[+] SHARING PROXIES.TXT...\033[0m")
    try:
        result = subprocess.run(["termux-share", "proxies.txt"], capture_output=True)
        if result.returncode == 0:
            print("\033[92m[✓] Share dialog opened!\033[0m")
        else:
            print("\033[93m[!] termux-share not available\033[0m")
            print("\033[93m[!] Install termux-api: pkg install termux-api\033[0m")
    except:
        print("\033[91m[✗] Failed to share\033[0m")
        print("\033[93m[!] Install termux-api: pkg install termux-api\033[0m")
    wait()

def about():
    clear()
    linex()
    print("\n\033[96m[+] ABOUT XTM\033[0m")
    print("\033[92mTool     : XTM Proxy Master\033[0m")
    print("\033[92mVersion  : 2.0 (Lite)\033[0m")
    print("\033[92mOwner    : MAHDI\033[0m")
    print("\033[92mGitHub   : MAHDI-143\033[0m")
    print("\033[92mFacebook : @xmahdi143\033[0m")
    print("\033[92mPurpose  : Fast proxy scraper & tester\033[0m")
    print("\033[92mSources  : monosans, TheSpeedX, ProxyScrape\033[0m")
    linex()
    
    print("\n\033[93m[+] Opening Facebook...\033[0m")
    try:
        subprocess.run(["termux-open", "https://www.facebook.com/xmahdi143"], capture_output=True)
    except:
        try:
            import webbrowser
            webbrowser.open("https://www.facebook.com/xmahdi143")
        except:
            print("\033[91m[✗] Could not open Facebook automatically\033[0m")
            print("\033[93m[!] Visit: https://www.facebook.com/xmahdi143\033[0m")
    
    wait()

def main():
    while True:
        clear()
        print("\033[93m    [1] HARVEST PROXIES\033[0m")
        print("\033[93m    [2] VIEW PROXIES\033[0m")
        print("\033[93m    [3] COPY TO SDCARD\033[0m")
        print("\033[93m    [4] SHARE FILE\033[0m")
        print("\033[93m    [5] ABOUT\033[0m")
        print("\033[93m    [6] EXIT\033[0m")
        linex()
        choice = input("\033[96m    [?] CHOOSE : \033[0m")
        
        if choice == "1":
            harvest()
        elif choice == "2":
            view_proxies()
        elif choice == "3":
            copy_to_sdcard()
        elif choice == "4":
            share_file()
        elif choice == "5":
            about()
        elif choice == "6":
            clear()
            print("\n\033[92m[+] GOODBYE!\033[0m")
            sys.exit()
        else:
            print("\033[91m[✗] INVALID!\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    main()
EOF