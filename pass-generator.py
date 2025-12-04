import os
import itertools
from termcolor import colored, cprint
import pyfiglet

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = pyfiglet.figlet_format("SOC PROFILER", font="slant")
    cprint(banner, 'cyan', attrs=['bold'])
    print(colored("[+] Generator Password Tertarget (OSINT Based)", "yellow"))
    print(colored("[+] Created by: INDRAYAZA Z", "yellow"))
    print("-" * 60)

def generate_wordlist():
    print_banner()
    print(colored("Jawab pertanyaan tentang target (kosongkan jika tidak tahu):", "white"))
    
    # 1. Pengumpulan Data (OSINT)
    first_name = input(">> Nama Depan Target      : ").strip()
    last_name  = input(">> Nama Belakang Target   : ").strip()
    nickname   = input(">> Nama Panggilan/Alias   : ").strip()
    birth_year = input(">> Tahun Lahir (YYYY)     : ").strip() # cth: 1990
    birth_date = input(">> Tanggal Lahir (DDMM)   : ").strip() # cth: 1708
    partner    = input(">> Nama Pasangan/Pacar    : ").strip()
    child      = input(">> Nama Anak/Hewan        : ").strip()
    company    = input(">> Nama Perusahaan/Kampus : ").strip()
    phone      = input(">> 4 Digit Terakhir HP    : ").strip()
    
    # 2. Logic Kombinasi
    base_words = [first_name, last_name, nickname, partner, child, company]
    base_words = [w for w in base_words if w] # Hapus yang kosong
    
    years = [birth_year, "2020", "2021", "2022", "2023", "2024", "2025", "123", "1234", "12345"]
    years = [y for y in years if y]
    
    separators = ["", ".", "_", "@", "#", "!"]
    
    passwords = set() # Gunakan set agar tidak ada duplikat

    print(colored("\n[*] Sedang meracik kombinasi logika...", "cyan"))

    # Kombinasi Level 1: Kata Dasar + Angka/Tahun
    # Contoh: indra1990, indra123, indra2024
    for word in base_words:
        # Variasi Huruf (huruf kecil, Kapital Depan, KAPITAL SEMUA)
        cases = [word.lower(), word.capitalize(), word.upper()]
        
        for case in cases:
            passwords.add(case) # Kata murni (jarang, tapi mungkin)
            
            for year in years:
                passwords.add(f"{case}{year}")       # indra123
                passwords.add(f"{case}{year}!")      # indra123!
                passwords.add(f"{case}@{year}")      # indra@123
                passwords.add(f"{year}{case}")       # 123indra

    # Kombinasi Level 2: Kata Dasar + Spesial + Kata Lain
    # Contoh: indra_budi, indra@susi
    for w1 in base_words:
        for w2 in base_words:
            if w1 == w2: continue
            for sep in separators:
                passwords.add(f"{w1}{sep}{w2}")
                passwords.add(f"{w1}{sep}{w2}123")

    # Kombinasi Level 3: Leet Speak Sederhana (Substitusi)
    # Contoh: 1ndr4, s0ccer
    leet_map = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5'}
    temp_leet = set()
    for pwd in passwords:
        chars = list(pwd)
        new_pwd = []
        changed = False
        for char in chars:
            if char.lower() in leet_map:
                new_pwd.append(leet_map[char.lower()])
                changed = True
            else:
                new_pwd.append(char)
        if changed:
            temp_leet.add("".join(new_pwd))
    passwords.update(temp_leet)

    # Tambahkan Phone Number jika ada
    if phone:
        for word in base_words:
            passwords.add(f"{word}{phone}")

    # 3. Simpan Hasil
    filename = f"target_{first_name}.txt"
    with open(filename, "w") as f:
        for p in passwords:
            f.write(p + "\n")
            
    print(colored("-" * 60, "white"))
    print(colored(f"[SUCCESS] Berhasil membuat profil target!", "green", attrs=['bold']))
    print(colored(f"[+] Total Kombinasi : {len(passwords)} password", "yellow"))
    print(colored(f"[+] Disimpan sebagai: {filename}", "cyan"))
    print(colored("-" * 60, "white"))
    print(colored(f"Sekarang gunakan '{filename}' di SOC_MULTITOOL.py", "white"))

if __name__ == "__main__":
    generate_wordlist()
