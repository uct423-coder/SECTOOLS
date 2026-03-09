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
sectool start    # Launch the interactive menu
sectool update   # Pull latest changes from git and reinstall
```

## What the installer does

| Step | macOS | Windows |
|------|-------|---------|
| Package manager | Homebrew | Chocolatey |
| Security tools | `brew install nmap nikto hydra ...` | `choco install nmap sqlmap ...` |
| Python venv | Auto-created | Auto-created |
| Global command | `sectool` | `sectool.bat` |

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
- **Cheat sheets** — built-in flag reference for every tool
- **Auto URL cleanup** — enter `https://example.com` and it extracts the hostname
- **Saved targets with notes** — targets are remembered across sessions with optional annotations
- **Auto-logging** — all scan results saved to `~/sectools-logs/`
- **Diff scans** — compare two scan results side by side with colored diff
- **HTML & PDF reports** — generate reports from your scan history
- **Scan scheduler** — schedule scans to run on a delay or repeating interval
- **Desktop notifications** — get notified when scans complete
- **Plugin system** — drop `.py` files in `~/.sectools-plugins/` to add custom tools
- **Tool status** — see which tools are installed at a glance
- **Recon autopilot** — run multiple scans on a target with one command
- **Self-update** — `sectool update` pulls the latest version from git
- **Cross-platform** — works on macOS, Windows, and Linux

## Plugins

Create a `.py` file in `~/.sectools-plugins/` with:

```python
PLUGIN_NAME = "My Plugin"

def run(console):
    console.print("[bold]Hello from my plugin![/bold]")
```

It will appear in the Plugins menu automatically.

## Requirements

- Python 3.9+
- macOS (Homebrew), Windows (Chocolatey), or Linux (apt)

## Disclaimer

This toolkit is for **educational purposes and authorized security testing only**. Only scan systems you own or have explicit permission to test. Unauthorized access to computer systems is illegal.
