# SecTools — Security Toolkit CLI

A guided command-line security testing toolkit. Wraps popular pentesting tools with interactive menus so you don't need to memorize flags.

```
   _____ ______  ______ ______  ____   ____  __   _____
  / ___// ____/ / ____//_  __/ / __ \ / __ \/ /  / ___/
  \__ \/ __/   / /      / /   / / / // / / // /   \__ \
 ___/ / /___  / /___   / /   / /_/ // /_/ // /______/ /
/____/_____/  \____/  /_/    \____/ \____//_____/____/
```

## Quick Install

### macOS

```bash
git clone https://github.com/uct423-coder/SECTOOLS.git
cd SECTOOLS
chmod +x install.sh
./install.sh
start
```

### Windows

> Run Command Prompt or PowerShell **as Administrator**

```cmd
git clone https://github.com/uct423-coder/SECTOOLS.git
cd SECTOOLS
install.bat
sectools.bat
```

### Linux (Debian/Ubuntu)

```bash
git clone https://github.com/uct423-coder/SECTOOLS.git
cd SECTOOLS
sudo apt update && sudo apt install -y nmap nikto hydra gobuster john hashcat netcat-openbsd sqlmap
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/start
```

## What the installer does

| Step | macOS | Windows |
|------|-------|---------|
| Package manager | Homebrew | Chocolatey |
| Security tools | `brew install nmap nikto hydra ...` | `choco install nmap sqlmap ...` |
| Python venv | Auto-created | Auto-created |
| Global command | `start` | `sectools.bat` |

## Usage

```bash
start          # macOS / Linux
sectools.bat   # Windows
```

## Tools Included

### Recon
| Tool | Description |
|------|-------------|
| **Recon Autopilot** | Runs multiple scans on a target automatically |
| **Nmap** | Network port scanning and service detection |
| **Nikto** | Web server vulnerability scanning |
| **Gobuster** | Directory and DNS subdomain brute-forcing |

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
| **Hashcat** | GPU-accelerated password hash cracking |

### Utilities
| Tool | Description |
|------|-------------|
| **Netcat** | Network connections, listeners, and port scanning |

## Features

- **Guided menus** — pick scan types from presets, no flag memorization
- **Auto URL cleanup** — enter `https://example.com` and it extracts the hostname for tools that need it
- **Saved targets** — targets are remembered across sessions
- **Auto-logging** — all scan results saved to `~/sectools-logs/`
- **HTML reports** — generate a report from your scan history and view it in browser
- **Tool status** — see which tools are installed at a glance
- **Recon autopilot** — run multiple scans on a target with one command
- **Cross-platform** — works on macOS, Windows, and Linux

## Requirements

- Python 3.9+
- macOS (Homebrew), Windows (Chocolatey), or Linux (apt)

## Disclaimer

This toolkit is for **educational purposes and authorized security testing only**. Only scan systems you own or have explicit permission to test. Unauthorized access to computer systems is illegal.
