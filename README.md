# SecTools — Security Toolkit CLI

A guided command-line security testing toolkit. Wraps popular pentesting tools with interactive menus so you don't need to memorize flags.

```
   ____            _____           _
  / ___|  ___  ___|_   _|__   ___ | |___
  \___ \ / _ \/ __| | |/ _ \ / _ \| / __|
   ___) |  __/ (__  | | (_) | (_) | \__ \
  |____/ \___|\___| |_|\___/ \___/|_|___/
```

## Quick Install

### macOS

```bash
git clone https://github.com/uct423-coder/SECTOOLS.git
cd SECTOOLS
chmod +x install.sh
./install.sh
sectool start
```

### Windows

> Run Command Prompt or PowerShell **as Administrator**

```cmd
git clone https://github.com/uct423-coder/SECTOOLS.git
cd SECTOOLS
install.bat
sectool start
```

### Linux (Debian/Ubuntu)

```bash
git clone https://github.com/uct423-coder/SECTOOLS.git
cd SECTOOLS
sudo apt update && sudo apt install -y nmap nikto hydra gobuster john hashcat netcat-openbsd sqlmap
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/sectool start
```

## Commands

```bash
sectool start              # Launch the interactive menu
sectool restart            # Restart SecTools
sectool update             # Pull latest changes from git and reinstall
sectool reinstall          # Clean reinstall (recreate venv and relink)
sectool uninstall          # Remove SecTools (venv, symlinks, optionally data)
sectool version            # Show version number
sectool status             # Quick tool status check
sectool hash <value>       # Identify a hash type from the command line
sectool encode base64 hi   # Quick encode (base64, url, hex, rot13)
sectool help               # Show all available commands
```

## What the installer does

| Step | macOS | Windows |
|------|-------|---------|
| Package manager | Homebrew | Chocolatey |
| Security tools | `brew install nmap nikto hydra ...` | `choco install nmap sqlmap ...` |
| Python venv | Auto-created | Auto-created |
| Wordlists | rockyou.txt + SecLists auto-downloaded | rockyou.txt + SecLists auto-downloaded |
| Global command | `sectool` | `sectool.bat` |

## Tools Included

### Recon & OSINT
| Tool | Description |
|------|-------------|
| **Recon Autopilot** | Runs multiple scans on a target automatically |
| **Nmap** | Network port scanning and service detection |
| **Nikto** | Web server vulnerability scanning |
| **Gobuster** | Directory and DNS subdomain brute-forcing |
| **OSINT** | Subdomain enumeration (crt.sh), reverse IP, HTTP headers |

### Exploitation
| Tool | Description |
|------|-------------|
| **Metasploit** | Guided exploitation workflows with preset modules |
| **SQLMap** | Automated SQL injection detection and exploitation |
| **Hydra** | Brute-force login attacks (SSH, FTP, HTTP, etc.) |

### Password Cracking
| Tool | Description |
|------|-------------|
| **John the Ripper** | CPU-based password hash cracking |
| **Hashcat** | GPU-accelerated password hash cracking (cross-platform rules paths) |

### Networking & Web
| Tool | Description |
|------|-------------|
| **Netcat** | Network connections, listeners, and port scanning (with port validation) |
| **HTTP Probe** | Quick URL scanner — status, headers, SSL, redirects |
| **Screenshot** | Capture web pages via Chrome or Safari |
| **Port Reference** | Look up 80+ common ports and services |
| **Subnet Calculator** | IP/CIDR network math (safe for large IPv6 networks) |

### Generators
| Tool | Description |
|------|-------------|
| **Reverse Shell Generator** | Generate payloads in 9 languages (Bash, Python, PHP, etc.) |
| **Password Generator** | Secure passwords with configurable length and charset |
| **Encoding / Decoding** | Base64, URL, hex, ROT13, HTML entities, binary |

### Analysis
| Tool | Description |
|------|-------------|
| **Hash Identifier** | Auto-detect hash types with hashcat/john format info |
| **Scan History Browser** | Browse, search, view, and delete past scan logs |
| **Diff Scans** | Compare two scan results with colored diff output |

### Management
| Tool | Description |
|------|-------------|
| **Target Groups** | Organize targets into named groups, scan all at once |
| **Scan Profiles** | Save custom scan configs as reusable profiles |
| **Wordlist Manager** | List, download, and manage wordlists |
| **Scan Scheduler** | Schedule scans to run on a delay or repeating interval |
| **Sessions** | Isolate targets and logs per engagement |
| **Scope Manager** | Define and enforce engagement scope (CIDR + domains) |
| **Credential Manager** | Securely store test account details |
| **Workflow Engine** | Chain multiple tools into automated workflows |
| **Proxy Settings** | Route tool traffic through a proxy |

## Features

- **ASCII art dashboard** — styled banner, stat cards, and tips on startup
- **Polished UI** — consistent ✔/✘ icons, styled headers, Rich-powered output
- **Guided menus** — pick scan types from presets, no flag memorization
- **Cheat sheets** — built-in flag reference for every tool
- **Auto URL cleanup** — enter `https://example.com` and it extracts the hostname
- **Saved targets with notes** — targets remembered across sessions with annotations
- **Target groups** — organize targets and scan entire groups at once
- **Scan profiles** — save and reuse custom tool+flag combos
- **Session isolation** — separate logs and targets per engagement
- **Scope enforcement** — warns when targeting out-of-scope hosts
- **Auto-logging** — all scan results saved to `~/sectools-logs/`
- **Scan history browser** — search and browse past scan results
- **Diff scans** — compare two scan results side by side
- **HTML & PDF reports** — generate reports from your scan history (Technical, Executive, Compliance)
- **Scan scheduler** — schedule delayed or repeating scans
- **Desktop notifications** — get notified when scans complete (macOS, Linux, Windows)
- **Wordlist manager** — download and manage wordlists from the menu
- **Auto-installer** — install missing security tools from the menu
- **Input validation** — port validation, hash file checks, integer guards
- **Shell-safe parsing** — `shlex.split()` for custom flags, escaped notifications
- **Plugin system** — drop `.py` files in `~/.sectools-plugins/`
- **Persistent config** — customize settings in `~/.sectools-config.json`
- **Self-update** — `sectool update` pulls the latest version from git
- **Quick restart** — `sectool restart` re-launches the app
- **Cross-platform** — works on macOS, Windows, and Linux

## Plugins

Create a `.py` file in `~/.sectools-plugins/` with:

```python
PLUGIN_NAME = "My Plugin"

def run(console):
    console.print("[bold]Hello from my plugin![/bold]")
```

It will appear in the Plugins menu automatically.

## Configuration

Settings are stored in `~/.sectools-config.json` and editable from the Settings menu:

| Setting | Default | Description |
|---------|---------|-------------|
| `default_wordlist` | `/usr/share/wordlists/rockyou.txt` | Default wordlist path |
| `default_dirwordlist` | `~/.sectools-wordlists/common.txt` | Default directory wordlist |
| `notifications_enabled` | `true` | Desktop notifications on scan complete |
| `theme_color` | `cyan` | UI accent color |
| `log_retention_days` | `30` | Auto-delete logs older than this |
| `auto_save_targets` | `false` | Auto-save targets without prompting |

## Changelog

### v1.1.8
- Visual overhaul: ASCII art banner, styled tool headers, ✔/✘ status icons
- All CLI commands (`update`, `reinstall`, `help`, `version`) use Rich styled output
- Consistent UI patterns across 30+ files

### v1.1.7
- Bug fixes: operator precedence in netcat, input validation in passgen
- Security: escape injection in notifications, validate ports
- Memory safety: avoid enumerating large IPv6 networks
- Use `shlex.split()` for custom flags, platform-aware hashcat rules
- Add missing `fpdf2` and `cryptography` to requirements.txt
- Remove unused imports, replace `os.system("clear")` with `console.clear()`
- Add `sectool restart` command

### v1.1.6
- Shared wordlist picker across all tools

### v1.1.3
- Workflow engine and proxy support

## Requirements

- Python 3.9+
- macOS (Homebrew), Windows (Chocolatey), or Linux (apt)

## Disclaimer

This toolkit is for **educational purposes and authorized security testing only**. Only scan systems you own or have explicit permission to test. Unauthorized access to computer systems is illegal.
