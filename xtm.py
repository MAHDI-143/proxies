#!/usr/bin/env python3
import os
import sys
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import subprocess
import json

CONFIG_FILE = "config.json"

# Colors
G = "\033[38;5;46m"
GGG = "\033[38;5;49m"
XX = "\033[1;92m"

logo = (f"""
╔━━━━━━━━━━━━━━━━━━━━━━╗━━━━━━━━━━━╗
║      \x1b[38;5;47m┳┳┓┏┓┓┏┳┓┳      ║PROXY      ║
║      \x1b[38;5;49m┃┃┃┣┫┣┫┃┃┃      ║SCRAPER    ║
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
    os.system('clear' if os.name == 'posix' else 'cls')
    print(logo)

def wait_for_enter():
    input("\n\033[93m[+] Press Enter to continue...\033[0m")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def check_link_status():
    """Check if user's GitHub link is valid and has proxies"""
    config = load_config()
    if not config:
        return False
    
    try:
        url = f"https://raw.githubusercontent.com/{config['username']}/{config['repo']}/main/proxies.txt"
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and len(r.text.strip()) > 0:
            return True
    except:
        pass
    return False

def setup():
    config = load_config()
    if not config:
        clear()
        print("\n\033[93m[!] FIRST TIME SETUP\033[0m")
        print("\033[96m[+] Proxies will be pushed to YOUR GitHub\033[0m")
        username = input("\033[96m[?] GitHub username: \033[0m").strip()
        token = input("\033[96m[?] GitHub token: \033[0m").strip()
        
        if not username or not token:
            print("\033[91m[✗] Username and token required!\033[0m")
            wait_for_enter()
            return None
        
        # Ask if they want to create new repo
        create_repo = input("\033[96m[?] Do you want to create a new repository? (y/n): \033[0m").lower()
        
        if create_repo == "y":
            repo = input("\033[96m[?] Repository name (default: proxies): \033[0m").strip() or "proxies"
            print(f"\n\033[96m[+] Creating repository '{repo}'...\033[0m")
            
            # Create repository via GitHub API
            api_url = "https://api.github.com/user/repos"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            data = {"name": repo, "public": True, "description": "Proxy list from XTM tool"}
            
            try:
                response = requests.post(api_url, json=data, headers=headers)
                if response.status_code == 201:
                    print(f"\033[92m[✓] Repository '{repo}' created successfully!\033[0m")
                elif response.status_code == 422:
                    print(f"\033[93m[!] Repository '{repo}' already exists. Connecting to it.\033[0m")
                else:
                    print(f"\033[91m[✗] Failed to create repository. Make sure your token has 'repo' scope.\033[0m")
                    wait_for_enter()
                    return None
            except Exception as e:
                print(f"\033[91m[✗] Error: {e}\033[0m")
                wait_for_enter()
                return None
        else:
            repo = input("\033[96m[?] Enter your existing repository name: \033[0m").strip()
            if not repo:
                print("\033[91m[✗] Repository name required!\033[0m")
                wait_for_enter()
                return None
            print(f"\n\033[96m[+] Checking if repository '{repo}' exists...\033[0m")
            
            # Check if repository exists
            api_url = f"https://api.github.com/repos/{username}/{repo}"
            headers = {"Authorization": f"token {token}"}
            
            try:
                response = requests.get(api_url, headers=headers)
                if response.status_code == 200:
                    print(f"\033[92m[✓] Repository '{repo}' found! Connecting...\033[0m")
                else:
                    print(f"\033[91m[✗] Repository '{repo}' not found! Check the name and try again.\033[0m")
                    wait_for_enter()
                    return None
            except Exception as e:
                print(f"\033[91m[✗] Error: {e}\033[0m")
                wait_for_enter()
                return None
        
        # Save config
        config = {"username": username, "token": token, "repo": repo}
        save_config(config)
        
        # Setup git remote
        os.system(f"rm -rf .git 2>/dev/null")
        os.system(f"git init")
        os.system(f"git remote add origin https://{username}:{token}@github.com/{username}/{repo}.git")
        os.system(f"git branch -M main")
        
        # Create initial proxies.txt
        with open("proxies.txt", "w") as f:
            f.write("# Proxy list will be updated here\n")
        
        # Test the link
        test_url = f"https://raw.githubusercontent.com/{username}/{repo}/main/proxies.txt"
        print(f"\n\033[96m[+] Testing your link...\033[0m")
        
        try:
            r = requests.get(test_url, timeout=5)
            if r.status_code == 200:
                print(f"\033[92m╔════════════════════════════════════════════════╗\033[0m")
                print(f"\033[92m║  ✅ YOUR LINK ADDED SUCCESSFULLY!              ║\033[0m")
                print(f"\033[92m║  📍 {test_url}\033[0m")
                print(f"\033[92m╚════════════════════════════════════════════════╝\033[0m")
            else:
                print(f"\033[93m╔════════════════════════════════════════════════╗\033[0m")
                print(f"\033[93m║  ⚠️ LINK CREATED BUT NOT YET ACTIVE            ║\033[0m")
                print(f"\033[93m║  📍 {test_url}\033[0m")
                print(f"\033[93m║  [!] Run [1] HARVEST PROXIES to add proxies    ║\033[0m")
                print(f"\033[93m╚════════════════════════════════════════════════╝\033[0m")
        except:
            print(f"\033[93m╔════════════════════════════════════════════════╗\033[0m")
            print(f"\033[93m║  ⚠️ LINK CREATED BUT NOT YET ACTIVE            ║\033[0m")
            print(f"\033[93m║  📍 {test_url}\033[0m")
            print(f"\033[93m║  [!] Run [1] HARVEST PROXIES to add proxies    ║\033[0m")
            print(f"\033[93m╚════════════════════════════════════════════════╝\033[0m")
        
        print("\n\033[92m[✓] Setup complete!\033[0m")
        wait_for_enter()
    
    return load_config()

def change_link():
    clear()
    current_config = load_config()
    print("\n\033[93m[!] CHANGE YOUR GITHUB SETTINGS\033[0m")
    username = input(f"\033[96m[?] New GitHub username (current: {current_config['username'] if current_config else 'None'}): \033[0m").strip()
    token = input("\033[96m[?] New GitHub token: \033[0m").strip()
    repo = input(f"\033[96m[?] New repository name (current: {current_config['repo'] if current_config else 'proxies'}): \033[0m").strip() or "proxies"
    
    if username and token:
        config = {"username": username, "token": token, "repo": repo}
        save_config(config)
        
        os.system(f"rm -rf .git 2>/dev/null")
        os.system(f"git init")
        os.system(f"git remote add origin https://{username}:{token}@github.com/{username}/{repo}.git")
        os.system(f"git branch -M main")
        print("\033[92m[✓] Settings updated! New link will be used for next harvest.\033[0m")
    else:
        print("\033[91m[✗] Username and token required!\033[0m")
    
    wait_for_enter()

def fetch_all_proxies():
    """Fetch proxies from multiple sources with better coverage"""
    sources = {
        "http": [
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
            "https://proxy-list.download/api/v1/get?type=http",
            "https://www.proxy-list.download/api/v1/get?type=http",
        ],
        "socks4": [
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all",
            "https://proxy-list.download/api/v1/get?type=socks4",
        ],
        "socks5": [
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
            "https://proxy-list.download/api/v1/get?type=socks5",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        ]
    }
    
    all_proxies = set()
    
    print("\n\033[96m[+] FETCHING PROXIES FROM 15+ SOURCES...\033[0m\n")
    
    for protocol, urls in sources.items():
        for url in urls:
            try:
                r = requests.get(url, timeout=15)
                found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r.text)
                all_proxies.update(found)
                print(f"\033[92m[✓] +{len(found)} from {url.split('/')[2]}\033[0m")
            except Exception as e:
                print(f"\033[91m[✗] Failed: {url.split('/')[2]}\033[0m")
    
    return list(all_proxies)

def test_proxy_advanced(proxy, timeout=5):
    """Test proxy with multiple endpoints for better reliability"""
    test_urls = [
        "http://httpbin.org/ip",
        "http://ip-api.com/json",
        "http://api.ipify.org"
    ]
    
    for url in test_urls:
        try:
            start = time.time()
            r = requests.get(url, proxies={"http": f"http://{proxy}"}, timeout=timeout)
            elapsed = time.time() - start
            if r.status_code == 200:
                return {"proxy": proxy, "speed": round(elapsed, 2)}
        except:
            continue
    return None

def update_proxies():
    clear()
    config = setup()
    if not config:
        return
    
    # Fetch all proxies
    all_proxies = fetch_all_proxies()
    
    if not all_proxies:
        print("\n\033[91m[✗] No proxies found from sources!\033[0m")
        wait_for_enter()
        return
    
    print(f"\n\033[96m[+] TOTAL UNIQUE PROXIES FETCHED: {len(all_proxies)}\033[0m")
    
    # Ask for test intensity
    print("\n\033[93m╔════════════════════════════════════════════════════╗\033[0m")
    print("\033[93m║  SELECT TESTING INTENSITY:                          ║\033[0m")
    print("\033[93m║  [1] LIGHT - Test 500 proxies (fast)               ║\033[0m")
    print("\033[93m║  [2] MEDIUM - Test 2000 proxies (recommended)      ║\033[0m")
    print("\033[93m║  [3] EXTREME - Test ALL proxies (slow but thorough)║\033[0m")
    print("\033[93m╚════════════════════════════════════════════════════╝\033[0m")
    
    intensity = input("\033[96m[?] Choose intensity (1/2/3): \033[0m")
    
    if intensity == "1":
        test_limit = min(500, len(all_proxies))
        workers = 100
        print(f"\n\033[96m[+] LIGHT MODE: Testing {test_limit} proxies...\033[0m")
    elif intensity == "2":
        test_limit = min(2000, len(all_proxies))
        workers = 150
        print(f"\n\033[96m[+] MEDIUM MODE: Testing {test_limit} proxies...\033[0m")
    elif intensity == "3":
        test_limit = len(all_proxies)
        workers = 200
        print(f"\n\033[96m[+] EXTREME MODE: Testing ALL {test_limit} proxies...\033[0m")
        print(f"\033[93m[!] This may take several minutes!\033[0m")
    else:
        test_limit = min(1000, len(all_proxies))
        workers = 100
        print(f"\n\033[96m[+] DEFAULT MODE: Testing {test_limit} proxies...\033[0m")
    
    print(f"\033[96m[+] Using {workers} concurrent workers for testing...\033[0m\n")
    
    # Test proxies
    working = []
    proxy_list = all_proxies[:test_limit]
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(test_proxy_advanced, p): p for p in proxy_list}
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                working.append(result)
                # Show progress
                speed_indicator = "⚡" if result["speed"] < 1 else "✓" if result["speed"] < 3 else "🐢"
                print(f"\033[92m   [{len(working)}] {speed_indicator} {result['proxy']} - {result['speed']}s\033[0m")
            
            # Show progress percentage every 100 proxies
            if i % 100 == 0:
                print(f"\033[96m   Progress: {i}/{test_limit} ({i*100//test_limit}%)\033[0m")
    
    print(f"\n\033[92m[✓] TESTING COMPLETE! Found {len(working)} WORKING PROXIES\033[0m")
    
    if working:
        speeds = [p['speed'] for p in working]
        print(f"\n\033[96m[+] SPEED STATS:\033[0m")
        print(f"   \033[92mFastest: {min(speeds)}s\033[0m")
        print(f"   \033[93mSlowest: {max(speeds)}s\033[0m")
        print(f"   \033[96mAverage: {sum(speeds)/len(speeds):.2f}s\033[0m")
        print(f"   \033[96mSuccess Rate: {len(working)*100//test_limit}%\033[0m")
        
        print("\n\033[93m╔══════════════════════════════════════════════════════════╗\033[0m")
        print("\033[93m║  [1] ULTRA FAST - Only proxies < 1s                        ║\033[0m")
        print("\033[93m║  [2] FAST - Only proxies < 2s                              ║\033[0m")
        print("\033[93m║  [3] GOOD - Remove slow proxies (> 4s)                     ║\033[0m")
        print("\033[93m║  [4] ALL WORKING - Keep all working proxies                ║\033[0m")
        print("\033[93m╚══════════════════════════════════════════════════════════╝\033[0m")
        
        filter_choice = input("\033[96m[?] Choose filter option (1/2/3/4): \033[0m")
        
        if filter_choice == "1":
            filtered = [p for p in working if p['speed'] < 1]
            if filtered:
                working = filtered
                print(f"\n\033[92m[✓] Kept {len(working)} ULTRA FAST proxies (< 1s)\033[0m")
            else:
                print(f"\n\033[93m[!] No proxies under 1s, keeping all {len(working)}\033[0m")
        
        elif filter_choice == "2":
            filtered = [p for p in working if p['speed'] < 2]
            if filtered:
                working = filtered
                print(f"\n\033[92m[✓] Kept {len(working)} FAST proxies (< 2s)\033[0m")
            else:
                print(f"\n\033[93m[!] No proxies under 2s, keeping all {len(working)}\033[0m")
        
        elif filter_choice == "3":
            filtered = [p for p in working if p['speed'] <= 4]
            removed = len(working) - len(filtered)
            if filtered:
                working = filtered
                print(f"\n\033[92m[✓] Kept {len(working)} proxies (removed {removed} slow ones)\033[0m")
            else:
                print(f"\n\033[93m[!] No proxies under 4s, keeping all {len(working)}\033[0m")
        
        elif filter_choice == "4":
            print(f"\n\033[92m[✓] Keeping ALL {len(working)} working proxies\033[0m")
        
        else:
            print(f"\n\033[93m[!] Invalid choice, keeping ALL {len(working)} proxies\033[0m")
    
    if not working:
        print("\n\033[91m[✗] No working proxies found!\033[0m")
        wait_for_enter()
        return
    
    # Save options
    print("\n\033[93m╔════════════════════════════════════════════════════╗\033[0m")
    print("\033[93m║  [A] AUTO - Push to GitHub automatically            ║\033[0m")
    print("\033[93m║  [M] MANUAL - Preview & decide                      ║\033[0m")
    print("\033[93m║  [S] SKIP - Save only locally                       ║\033[0m")
    print("\033[93m╚════════════════════════════════════════════════════╝\033[0m")
    
    choice = input("\033[96m[?] How to save these proxies? (A/M/S): \033[0m").upper()
    
    if choice == "A":
        # Save with timestamp and stats
        with open("proxies.txt", "w") as f:
            f.write(f"# Proxy List - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total Working: {len(working)}\n")
            f.write(f"# Fastest: {min(speeds)}s | Slowest: {max(speeds)}s | Average: {sum(speeds)/len(speeds):.2f}s\n")
            f.write("#" + "="*50 + "\n\n")
            for p in working:
                f.write(f"{p['proxy']}\n")
        
        print(f"\n\033[92m[✓] SAVED {len(working)} PROXIES TO proxies.txt\033[0m")
        
        print("\n\033[96m[+] PUSHING TO YOUR GITHUB...\033[0m")
        
        # Configure git user if not set
        subprocess.run(["git", "config", "user.email", "proxy@xtm.com"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "XTM Proxy"], capture_output=True)
        
        subprocess.run(["git", "add", "proxies.txt"], capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Update {len(working)} proxies - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], capture_output=True)
        result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\033[92m[✓] PROXIES PUSHED TO YOUR GITHUB\033[0m")
            print(f"\033[92m[✓] LINK: https://raw.githubusercontent.com/{config['username']}/{config['repo']}/main/proxies.txt\033[0m")
            print(f"\033[96m[✓] Total proxies online: {len(working)}\033[0m")
        else:
            print(f"\033[91m[✗] PUSH FAILED! {result.stderr}\033[0m")
            print(f"\033[93m[!] Proxies saved locally in proxies.txt\033[0m")
    
    elif choice == "M":
        print("\n\033[96m[+] WORKING PROXIES PREVIEW (First 30):\033[0m")
        linex()
        for i, p in enumerate(working[:30], 1):
            print(f"\033[92m[{i}] {p['proxy']} - {p['speed']}s\033[0m")
        if len(working) > 30:
            print(f"\033[93m... and {len(working)-30} more\033[0m")
        linex()
        
        save_choice = input("\n\033[96m[?] Save these proxies to file? (y/n): \033[0m").lower()
        if save_choice == 'y':
            with open("proxies.txt", "w") as f:
                f.write(f"# Proxy List - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total: {len(working)}\n\n")
                for p in working:
                    f.write(f"{p['proxy']}\n")
            print(f"\n\033[92m[✓] SAVED {len(working)} PROXIES TO proxies.txt\033[0m")
            
            push_choice = input("\n\033[96m[?] Push to GitHub? (y/n): \033[0m").lower()
            if push_choice == 'y':
                print("\n\033[96m[+] PUSHING TO YOUR GITHUB...\033[0m")
                subprocess.run(["git", "config", "user.email", "proxy@xtm.com"], capture_output=True)
                subprocess.run(["git", "config", "user.name", "XTM Proxy"], capture_output=True)
                      
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
