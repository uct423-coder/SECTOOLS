@echo off
setlocal EnableDelayedExpansion

cls

echo.
echo    [36m[1m
echo    _____ ______  ______ ______  ____   ____  __   _____
echo   / ___// ____/ / ____//_  __/ / __ \ / __ \/ /  / ___/
echo   \__ \/ __/   / /      / /   / / / // / / // /   \__ \
echo  ___/ / /___  / /___   / /   / /_/ // /_/ // /______/ /
echo /____/_____/  \____/  /_/    \____/ \____//_____/____/
echo    [0m
echo   [1mSecurity Toolkit Installer[0m [90mv1.0.2[0m
echo   [90mMade by Shepard Sotiroglou[0m
echo.
echo   [90m---------------------------------------------[0m
echo   [90mEducational security testing toolkit.[0m
echo   [90mUse responsibly. Only test what you own.[0m
echo   [90m---------------------------------------------[0m
echo.

timeout /t 1 >nul 2>nul

:: ── Step 1: Python ──
echo [1m[1/6] Checking Python...[0m
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo   [31m[!][0m Python not found.
    echo   [90mPlease install Python 3.9+ from https://python.org[0m
    echo   [90mMake sure to check "Add Python to PATH" during install.[0m
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   [32m[+][0m %%v
echo.

:: ── Step 2: Chocolatey ──
echo [1m[2/6] Checking package manager...[0m
where choco >nul 2>nul
if %errorlevel% neq 0 (
    echo   [36m[*][0m Chocolatey not found. Installing...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if %errorlevel% neq 0 (
        echo   [31m[!][0m Failed to install Chocolatey. Run as Administrator.
        pause
        exit /b 1
    )
    echo   [32m[+][0m Chocolatey installed
) else (
    echo   [32m[+][0m Chocolatey found
)
echo.

:: ── Step 3: Security tools ──
echo [1m[3/6] Installing security tools...[0m

call :install_tool nmap nmap
call :install_tool sqlmap sqlmap
call :install_tool hashcat hashcat
call :install_tool ncrack ncrack

echo   [90m(i) Netcat included with Nmap as ncat[0m
echo.
echo   [90mTools that need manual install on Windows:[0m
echo   [90m  - Metasploit: https://www.metasploit.com/download[0m
echo   [90m  - Nikto:      https://github.com/sullo/nikto[0m
echo   [90m  - Hydra:      https://github.com/vanhauser-thc/thc-hydra[0m
echo   [90m  - Gobuster:   https://github.com/OJ/gobuster/releases[0m
echo   [90m  - John:       https://www.openwall.com/john/[0m
echo.

:: ── Step 4: Virtual environment ──
echo [1m[4/6] Setting up environment...[0m
if not exist "%~dp0.venv" (
    python -m venv "%~dp0.venv"
    echo   [32m[+][0m Virtual environment created
) else (
    echo   [32m[+][0m Virtual environment exists
)
echo.

:: ── Step 5: Install package ──
echo [1m[5/6] Installing SecTools package...[0m
"%~dp0.venv\Scripts\pip.exe" install -e "%~dp0" --quiet
echo   [32m[+][0m SecTools installed
echo.

:: ── Step 6: Global command ──
echo [1m[6/6] Setting up global command...[0m
(
    echo @echo off
    echo "%~dp0.venv\Scripts\sectool.exe" %%*
) > "%~dp0sectool.bat"
echo   [32m[+][0m sectool.bat created
echo.
echo   [90mTo run 'sectool' from anywhere, add this folder to PATH:[0m
echo   [90m  %~dp0[0m
echo.

:: ── Done ──
echo [36m[1m
echo   +================================================+
echo   ^|          Installation Complete!                 ^|
echo   +================================================+
echo   ^|                                                 ^|
echo   ^|   sectool start     Launch the toolkit          ^|
echo   ^|   sectool update    Update to latest            ^|
echo   ^|   sectool help      Show all commands           ^|
echo   ^|                                                 ^|
echo   +================================================+
echo   ^|   Made by Shepard Sotiroglou                    ^|
echo   ^|   github.com/uct423-coder/SECTOOLS             ^|
echo   +================================================+
echo [0m
echo.
pause
exit /b 0

:install_tool
where %1 >nul 2>nul
if %errorlevel% equ 0 (
    echo   [32m[+][0m %2
) else (
    echo   [36m[*][0m Installing %2...
    choco install %2 -y >nul 2>nul
    if %errorlevel% equ 0 (
        echo   [32m[+][0m %2 installed
    ) else (
        echo   [31m[!][0m Failed to install %2 — skipping
    )
)
exit /b 0
