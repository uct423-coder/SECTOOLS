#!/bin/bash
set -e

echo ""
echo "   _____ ______  ______ ______  ____   ____  __   _____"
echo "  / ___// ____/ / ____//_  __/ / __ \ / __ \/ /  / ___/"
echo "  \__ \/ __/   / /      / /   / / / // / / // /   \__ \ "
echo " ___/ / /___  / /___   / /   / /_/ // /_/ // /______/ /"
echo "/____/_____/  \____/  /_/    \____/ \____//_____/____/ "
echo ""
echo "SecTools Installer"
echo "===================="
echo ""

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "[!] Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "[✓] Homebrew found"
fi

# Install security tools
echo ""
echo "[*] Installing security tools..."
TOOLS="nmap nikto hydra gobuster john hashcat netcat sqlmap"
for tool in $TOOLS; do
    if brew list "$tool" &> /dev/null; then
        echo "  [✓] $tool already installed"
    else
        echo "  [*] Installing $tool..."
        brew install "$tool" 2>/dev/null || echo "  [!] Failed to install $tool — skipping"
    fi
done

# Metasploit (cask)
if brew list --cask metasploit &> /dev/null 2>&1; then
    echo "  [✓] metasploit already installed"
else
    echo "  [*] Installing metasploit (this may take a while)..."
    brew install --cask metasploit 2>/dev/null || echo "  [!] Failed to install metasploit — skipping"
fi

# Check for Python 3
echo ""
if ! command -v python3 &> /dev/null; then
    echo "[*] Installing Python 3..."
    brew install python3
else
    echo "[✓] Python 3 found"
fi

# Set up virtual environment
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo ""
echo "[*] Setting up Python virtual environment..."
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    python3 -m venv "$SCRIPT_DIR/.venv"
    echo "  [✓] Virtual environment created"
else
    echo "  [✓] Virtual environment already exists"
fi

# Install Python package
echo "[*] Installing SecTools..."
"$SCRIPT_DIR/.venv/bin/pip" install -e "$SCRIPT_DIR" --quiet
echo "  [✓] SecTools installed"

# Create symlink so 'start' works globally
echo ""
echo "[*] Setting up 'start' command..."
if [ -d /opt/homebrew/bin ]; then
    ln -sf "$SCRIPT_DIR/.venv/bin/start" /opt/homebrew/bin/start
    echo "  [✓] 'start' command ready"
elif [ -w /usr/local/bin ]; then
    ln -sf "$SCRIPT_DIR/.venv/bin/start" /usr/local/bin/start
    echo "  [✓] 'start' command ready"
else
    echo "  [!] Could not create global command. Run with: $SCRIPT_DIR/.venv/bin/start"
fi

echo ""
echo "============================================"
echo "  Installation complete! Type 'start' to run"
echo "============================================"
echo ""
