"""Screenshot Tool — capture web page screenshots using Chrome or Safari."""

import os
import subprocess
import shutil
import datetime
from pathlib import Path
from urllib.parse import urlparse

from rich.console import Console
from InquirerPy import inquirer

from sectools.utils import LOGS_DIR

SCREENSHOTS_DIR = LOGS_DIR / "screenshots"

if os.name == "nt":
    CHROME_CANDIDATES = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        "chrome",
    ]
else:
    CHROME_CANDIDATES = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ]


def _find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if os.path.isfile(candidate) or shutil.which(candidate):
            return candidate
    return None


def _safari_available() -> bool:
    return os.name != "nt" and os.path.isdir("/Applications/Safari.app")


def _screenshot_chrome(console: Console, chrome: str, url: str, output_path: Path):
    cmd = [
        chrome,
        "--headless",
        f"--screenshot={output_path}",
        "--window-size=1280,900",
        "--no-sandbox",
        "--disable-gpu",
        url,
    ]
    console.print(f"[dim]Capturing with Chrome: {url}...[/dim]")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if output_path.exists():
            console.print(f"[bold green]Screenshot saved: {output_path}[/bold green]")
        else:
            console.print("[red]Screenshot failed — no output file created.[/red]")
            if result.stderr:
                console.print(f"[dim]{result.stderr[:500]}[/dim]")
    except subprocess.TimeoutExpired:
        console.print("[red]Screenshot timed out after 30 seconds.[/red]")
    except FileNotFoundError:
        console.print(f"[red]Could not run Chrome at: {chrome}[/red]")


def _screenshot_safari(console: Console, url: str, output_path: Path):
    """Use AppleScript to open a URL in Safari and capture a screenshot via screencapture."""
    console.print(f"[dim]Capturing with Safari: {url}...[/dim]")

    # Open URL in Safari and wait for it to load
    applescript = f'''
    tell application "Safari"
        activate
        if (count of windows) = 0 then
            make new document
        end if
        set URL of current tab of front window to "{url}"
        delay 3
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], capture_output=True, timeout=15)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]Failed to open URL in Safari.[/red]")
        return

    # Give the page a moment to render
    import time
    time.sleep(2)

    # Capture the Safari window using screencapture
    try:
        # -l flag captures a specific window; -o excludes shadow
        # First, get Safari's window ID
        wid_script = '''
        tell application "System Events"
            tell process "Safari"
                set winID to id of front window
            end tell
        end tell
        return winID
        '''
        wid_result = subprocess.run(
            ["osascript", "-e", wid_script],
            capture_output=True, text=True, timeout=5,
        )
        window_id = wid_result.stdout.strip()

        if window_id:
            subprocess.run(
                ["screencapture", "-l", window_id, "-o", str(output_path)],
                capture_output=True, timeout=10,
            )
        else:
            # Fallback: capture the frontmost window interactively
            subprocess.run(
                ["screencapture", "-w", "-o", str(output_path)],
                capture_output=True, timeout=15,
            )

        if output_path.exists():
            console.print(f"[bold green]Screenshot saved: {output_path}[/bold green]")
        else:
            console.print("[red]Screenshot failed — no output file created.[/red]")
    except subprocess.TimeoutExpired:
        console.print("[red]screencapture timed out.[/red]")
    except FileNotFoundError:
        console.print("[red]screencapture not found.[/red]")


def run(console: Console):
    """Take a screenshot of a URL using Chrome or Safari."""
    chrome = _find_chrome()
    safari = _safari_available()

    if not chrome and not safari:
        console.print("[red]No supported browser found. Install Chrome or use Safari.[/red]")
        return

    # Build browser choices
    browsers = []
    if chrome:
        browsers.append("Chrome")
    if safari:
        browsers.append("Safari")

    if len(browsers) == 1:
        browser = browsers[0]
    else:
        browser = inquirer.select(
            message="Browser to use:",
            choices=browsers,
            pointer="❯",
        ).execute()

    url = inquirer.text(message="URL to screenshot:").execute().strip()
    if not url:
        console.print("[red]No URL provided.[/red]")
        return

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    domain = parsed.hostname or "unknown"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SCREENSHOTS_DIR / f"{domain}_{timestamp}.png"

    if browser == "Chrome":
        _screenshot_chrome(console, chrome, url, output_path)
    else:
        _screenshot_safari(console, url, output_path)
