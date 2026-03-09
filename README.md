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

```bash
git clone https://github.com/uct423-coder/SECTOOLS.git
cd SECTOOLS
chmod +x install.sh
./install.sh
```

That's it. The installer will:
- Install Homebrew (if missing)
- Install all security tools (Nmap, Nikto, Hydra, Gobuster, John the Ripper, Hashcat, Netcat, SQLMap, Metasploit)
- Set up Python virtual environment
- Install SecTools
- Make the `start` command available globally

## Usage

```bash
start
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

## Requirements

- macOS (Homebrew)
- Python 3.9+

## Disclaimer

This toolkit is for **educational purposes and authorized security testing only**. Only scan systems you own or have explicit permission to test. Unauthorized access to computer systems is illegal.
