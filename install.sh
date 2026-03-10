#!/bin/bash
set -e

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

clear

echo ""
echo -e "${CYAN}${BOLD}"
echo "   _____ ______  ______ ______  ____   ____  __   _____"
echo "  / ___// ____/ / ____//_  __/ / __ \ / __ \/ /  / ___/"
echo "  \__ \/ __/   / /      / /   / / / // / / // /   \__ \ "
echo " ___/ / /___  / /___   / /   / /_/ // /_/ // /______/ /"
echo "/____/_____/  \____/  /_/    \____/ \____//_____/____/ "
echo -e "${RESET}"
echo -e "${BOLD}  Security Toolkit Installer ${DIM}v1.0.2${RESET}"
echo -e "${DIM}  Made by Shepard Sotiroglou${RESET}"
echo ""
echo -e "${DIM}  ─────────────────────────────────────────────${RESET}"
echo -e "${DIM}  Educational security testing toolkit.${RESET}"
echo -e "${DIM}  Use responsibly. Only test what you own.${RESET}"
echo -e "${DIM}  ─────────────────────────────────────────────${RESET}"
echo ""

sleep 1

# ── Step 1: Homebrew ──
echo -e "${BOLD}[1/7] Checking package manager...${RESET}"
if ! command -v brew &> /dev/null; then
    echo -e "  ${YELLOW}[!] Homebrew not found. Installing...${RESET}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo -e "  ${GREEN}[✓]${RESET} Homebrew found"
fi
echo ""

# ── Step 2: Security tools ──
echo -e "${BOLD}[2/7] Installing security tools...${RESET}"
TOOLS="nmap nikto hydra gobuster john hashcat netcat sqlmap"
INSTALLED=0
TOTAL=0
for tool in $TOOLS; do
    TOTAL=$((TOTAL + 1))
    if brew list "$tool" &> /dev/null; then
        echo -e "  ${GREEN}[✓]${RESET} $tool"
        INSTALLED=$((INSTALLED + 1))
    else
        echo -e "  ${CYAN}[*]${RESET} Installing $tool..."
        if brew install "$tool" 2>/dev/null; then
            echo -e "  ${GREEN}[✓]${RESET} $tool installed"
            INSTALLED=$((INSTALLED + 1))
        else
            echo -e "  ${RED}[!]${RESET} Failed to install $tool — skipping"
        fi
    fi
done

# Metasploit (cask)
TOTAL=$((TOTAL + 1))
if brew list --cask metasploit &> /dev/null 2>&1; then
    echo -e "  ${GREEN}[✓]${RESET} metasploit"
    INSTALLED=$((INSTALLED + 1))
else
    echo -e "  ${CYAN}[*]${RESET} Installing metasploit (this may take a while)..."
    if brew install --cask metasploit 2>/dev/null; then
        echo -e "  ${GREEN}[✓]${RESET} metasploit installed"
        INSTALLED=$((INSTALLED + 1))
    else
        echo -e "  ${RED}[!]${RESET} Failed to install metasploit — skipping"
    fi
fi
echo -e "  ${DIM}$INSTALLED/$TOTAL tools ready${RESET}"
echo ""

# ── Step 3: Python ──
echo -e "${BOLD}[3/7] Checking Python...${RESET}"
if ! command -v python3 &> /dev/null; then
    echo -e "  ${CYAN}[*]${RESET} Installing Python 3..."
    brew install python3
else
    PY_VER=$(python3 --version 2>&1)
    echo -e "  ${GREEN}[✓]${RESET} $PY_VER"
fi
echo ""

# ── Step 4: Virtual environment ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo -e "${BOLD}[4/7] Setting up environment...${RESET}"
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    python3 -m venv "$SCRIPT_DIR/.venv"
    echo -e "  ${GREEN}[✓]${RESET} Virtual environment created"
else
    echo -e "  ${GREEN}[✓]${RESET} Virtual environment exists"
fi
echo ""

# ── Step 5: Install package ──
echo -e "${BOLD}[5/7] Installing SecTools package...${RESET}"
"$SCRIPT_DIR/.venv/bin/pip" install -e "$SCRIPT_DIR" --quiet
echo -e "  ${GREEN}[✓]${RESET} SecTools installed"
echo ""

# ── Step 6: Wordlists ──
echo -e "${BOLD}[6/7] Setting up wordlists...${RESET}"
WORDLISTS_DIR="$HOME/.sectools-wordlists"
mkdir -p "$WORDLISTS_DIR"

# Copy bundled wordlists
if [ -d "$SCRIPT_DIR/wordlists" ]; then
    cp -n "$SCRIPT_DIR/wordlists/"* "$WORDLISTS_DIR/" 2>/dev/null || true
    echo -e "  ${GREEN}[✓]${RESET} Bundled wordlists copied"
fi

# Download rockyou.txt (compressed ~15MB → ~140MB extracted)
if [ ! -f "$WORDLISTS_DIR/rockyou.txt" ]; then
    echo -e "  ${CYAN}[*]${RESET} Downloading rockyou.txt..."
    if curl -fsSL "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt" \
        -o "$WORDLISTS_DIR/rockyou.txt" 2>/dev/null; then
        echo -e "  ${GREEN}[✓]${RESET} rockyou.txt downloaded ($( du -h "$WORDLISTS_DIR/rockyou.txt" | cut -f1 ))"
    else
        echo -e "  ${YELLOW}[!]${RESET} Failed to download rockyou.txt — you can grab it later from Wordlist Manager"
    fi
else
    echo -e "  ${GREEN}[✓]${RESET} rockyou.txt already exists"
fi

# Download SecLists essentials (POSIX-compatible — no associative arrays)
SECLISTS_BASE="https://raw.githubusercontent.com/danielmiessler/SecLists/master"

download_if_missing() {
    local filename="$1"
    local url="$2"
    if [ ! -f "$WORDLISTS_DIR/$filename" ]; then
        echo -e "  ${CYAN}[*]${RESET} Downloading $filename..."
        if curl -fsSL "$url" -o "$WORDLISTS_DIR/$filename" 2>/dev/null; then
            echo -e "  ${GREEN}[✓]${RESET} $filename"
        else
            echo -e "  ${YELLOW}[!]${RESET} Failed: $filename"
            rm -f "$WORDLISTS_DIR/$filename"
        fi
    else
        echo -e "  ${GREEN}[✓]${RESET} $filename already exists"
    fi
}

download_if_missing "subdomains-top1million-5000.txt" "$SECLISTS_BASE/Discovery/DNS/subdomains-top1million-5000.txt"
download_if_missing "directory-list-2.3-small.txt"    "$SECLISTS_BASE/Discovery/Web-Content/directory-list-2.3-small.txt"
download_if_missing "top-usernames-shortlist.txt"     "$SECLISTS_BASE/Usernames/top-usernames-shortlist.txt"
download_if_missing "default-passwords.txt"           "$SECLISTS_BASE/Passwords/Default-Credentials/default-passwords.txt"
download_if_missing "common-web-passwords.txt"        "$SECLISTS_BASE/Passwords/Common-Credentials/10k-most-common.txt"

echo -e "  ${DIM}Wordlists directory: $WORDLISTS_DIR${RESET}"
echo ""

# ── Step 7: Global command ──
echo -e "${BOLD}[7/7] Setting up global command...${RESET}"
if [ -d /opt/homebrew/bin ]; then
    ln -sf "$SCRIPT_DIR/.venv/bin/sectool" /opt/homebrew/bin/sectool
    echo -e "  ${GREEN}[✓]${RESET} 'sectool' command linked"
elif [ -w /usr/local/bin ]; then
    ln -sf "$SCRIPT_DIR/.venv/bin/sectool" /usr/local/bin/sectool
    echo -e "  ${GREEN}[✓]${RESET} 'sectool' command linked"
else
    echo -e "  ${YELLOW}[!]${RESET} Could not create global command."
    echo -e "  ${DIM}Run with: $SCRIPT_DIR/.venv/bin/sectool${RESET}"
fi
echo ""

# ── Done ──
echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║          Installation Complete!              ║"
echo "  ╠══════════════════════════════════════════════╣"
echo "  ║                                              ║"
echo "  ║   sectool start     Launch the toolkit       ║"
echo "  ║   sectool update    Update to latest          ║"
echo "  ║   sectool help      Show all commands        ║"
echo "  ║                                              ║"
echo "  ╠══════════════════════════════════════════════╣"
echo "  ║   Made by Shepard Sotiroglou                 ║"
echo "  ║   github.com/uct423-coder/SECTOOLS           ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
echo ""
