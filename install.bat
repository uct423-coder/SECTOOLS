@echo off
setlocal

echo.
echo    _____ ______  ______ ______  ____   ____  __   _____
echo   / ___// ____/ / ____//_  __/ / __ \ / __ \/ /  / ___/
echo   \__ \/ __/   / /      / /   / / / // / / // /   \__ \
echo  ___/ / /___  / /___   / /   / /_/ // /_/ // /______/ /
echo /____/_____/  \____/  /_/    \____/ \____//_____/____/
echo.
echo SecTools Installer (Windows)
echo ============================
echo.

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python not found. Please install Python 3.9+ from https://python.org
    echo     Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo [✓] Python found

:: Check for Chocolatey
where choco >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [*] Chocolatey not found. Installing...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if %errorlevel% neq 0 (
        echo [!] Failed to install Chocolatey. Run this script as Administrator.
        pause
        exit /b 1
    )
    echo [✓] Chocolatey installed
) else (
    echo [✓] Chocolatey found
)

:: Install security tools via Chocolatey
echo.
echo [*] Installing security tools...

call :install_tool nmap nmap
call :install_tool sqlmap sqlmap
call :install_tool hashcat hashcat
call :install_tool ncrack ncrack

:: Nmap includes ncat (netcat) on Windows
echo   [i] Netcat included with Nmap (ncat)

echo.
echo [*] Tools that need manual install on Windows:
echo   - Metasploit: https://www.metasploit.com/download
echo   - Nikto:      https://github.com/sullo/nikto
echo   - Hydra:      https://github.com/vanhauser-thc/thc-hydra
echo   - Gobuster:   https://github.com/OJ/gobuster/releases
echo   - John:       https://www.openwall.com/john/

:: Set up virtual environment
echo.
echo [*] Setting up Python virtual environment...
if not exist "%~dp0.venv" (
    python -m venv "%~dp0.venv"
    echo   [✓] Virtual environment created
) else (
    echo   [✓] Virtual environment already exists
)

:: Install Python package
echo [*] Installing SecTools...
"%~dp0.venv\Scripts\pip.exe" install -e "%~dp0" --quiet
echo   [✓] SecTools installed

:: Create batch file shortcut
echo [*] Setting up 'sectools' command...
(
    echo @echo off
    echo "%~dp0.venv\Scripts\start.exe" %%*
) > "%~dp0sectools.bat"
echo   [✓] Run with: sectools.bat

:: Try to add to PATH
echo.
echo [*] To run 'sectools' from anywhere, add this folder to your PATH:
echo     %~dp0
echo.
echo ============================================
echo   Installation complete!
echo   Run 'sectools.bat' or '.venv\Scripts\start.exe'
echo ============================================
echo.
pause
exit /b 0

:install_tool
where %1 >nul 2>nul
if %errorlevel% equ 0 (
    echo   [✓] %2 already installed
) else (
    echo   [*] Installing %2...
    choco install %2 -y >nul 2>nul
    if %errorlevel% equ 0 (
        echo   [✓] %2 installed
    ) else (
        echo   [!] Failed to install %2 — skipping
    )
)
exit /b 0
