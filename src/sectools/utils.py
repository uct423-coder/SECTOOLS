import os
import json
import shutil
import subprocess
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

LOGS_DIR = Path.home() / "sectools-logs"
TARGETS_FILE = Path.home() / ".sectools-targets"
WORDLISTS_DIR = Path.home() / ".sectools-wordlists"


def pick_wordlist(message: str, default: str) -> str:
    """Let user pick a wordlist from downloaded ones or enter a custom path."""
    from InquirerPy import inquirer

    available = sorted(WORDLISTS_DIR.glob("*.txt")) if WORDLISTS_DIR.exists() else []

    if available:
        choices = [f.name for f in available] + ["Custom path..."]
        choice = inquirer.select(
            message=message,
            choices=choices,
            default=Path(default).name if Path(default).name in [f.name for f in available] else None,
            pointer="❯",
        ).execute()

        if choice == "Custom path...":
            return inquirer.text(message="Path:", default=default).execute().strip()
        return str(WORDLISTS_DIR / choice)

    return inquirer.text(message=message, default=default).execute().strip()

# Tool name -> binary name mapping
TOOL_BINARIES = {
    "Nmap": "nmap",
    "Metasploit": "msfconsole",
    "SQLMap": "sqlmap",
    "Nikto": "nikto",
    "Hydra": "hydra",
    "Gobuster": "gobuster",
    "John the Ripper": "john",
    "Hashcat": "hashcat",
    "Netcat": "nc",
}


def check_installed(binary: str) -> bool:
    """Check if a binary is available on PATH."""
    return shutil.which(binary) is not None


def show_tool_status(console: Console):
    """Display a table of all tools and their install status."""
    table = Table(
        title="[bold]Tool Status[/bold]",
        border_style="bright_cyan",
        show_lines=True,
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey11"],
        padding=(0, 1),
    )
    table.add_column("", width=3, justify="center")
    table.add_column("Tool", style="bold")
    table.add_column("Binary", style="dim italic")
    table.add_column("Status", justify="center")

    for tool, binary in TOOL_BINARIES.items():
        if check_installed(binary):
            icon = "[green]✔[/green]"
            status = "[bold green]Installed[/bold green]"
        else:
            icon = "[red]✘[/red]"
            status = "[dim red]Missing[/dim red]"
        table.add_row(icon, tool, binary, status)

    console.print(table)
    console.print()


def extract_hostname(target: str) -> tuple[str, bool]:
    """Strip URL scheme and path, returning (hostname, was_modified)."""
    from urllib.parse import urlparse
    stripped = target.strip()
    if "://" in stripped:
        parsed = urlparse(stripped)
        hostname = parsed.hostname or stripped
        return hostname, hostname != stripped
    return stripped, False


def run_logged(cmd: list[str], console: Console, tool_name: str) -> subprocess.CompletedProcess:
    """Run a command, display it, capture output to a log file, and stream to terminal."""
    from sectools.proxy import get_proxy_args, get_proxy_env

    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = tool_name.lower().replace(" ", "_")
    log_file = LOGS_DIR / f"{safe_name}_{timestamp}.log"

    # Inject proxy flags if enabled
    binary = cmd[0] if cmd else ""
    proxy_args = get_proxy_args(binary)
    if proxy_args:
        cmd = [cmd[0]] + proxy_args + cmd[1:]
        console.print(f"[dim]Proxy: {' '.join(proxy_args)}[/dim]")

    # Proxy env vars for tools that use them
    env = None
    proxy_env = get_proxy_env()
    if proxy_env:
        import os
        env = {**os.environ, **proxy_env}

    console.print(Panel(
        f"[bold white]{' '.join(cmd)}[/bold white]\n[dim]Log: {log_file}[/dim]",
        title=f"[bold cyan]▶ {tool_name}[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))

    with open(log_file, "w") as f:
        f.write(f"# {tool_name} scan — {datetime.datetime.now().isoformat()}\n")
        f.write(f"# Command: {' '.join(cmd)}\n\n")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        for line in process.stdout:
            print(line, end="", flush=True)
            f.write(line)
        process.wait()

    # Read back the full output for summary
    output = log_file.read_text()

    console.print()
    console.print(Panel(
        f"[bold green]✔ Results saved[/bold green]\n[cyan]{log_file}[/cyan]",
        border_style="green",
        padding=(0, 2),
    ))

    # Show smart summary
    _show_scan_summary(console, tool_name, output)

    from sectools.notifications import notify
    notify("SecTools", f"{tool_name} scan complete")
    return process


import re as _re


def _show_scan_summary(console: Console, tool_name: str, output: str):
    """Parse scan output and show a clean summary panel."""
    tool = tool_name.lower().replace(" ", "_")
    lines = output.splitlines()

    # Skip comment/header lines from our own logging
    content_lines = [l for l in lines if not l.startswith("#") and l.strip()]

    summary_items = []
    details_table = None

    # ── Nmap ──────────────────────────────────────────────────────
    if "nmap" in tool:
        open_ports = []
        host_up = False
        os_info = None
        for line in content_lines:
            if "Host is up" in line:
                host_up = True
            m = _re.match(r'^(\d+/\w+)\s+(\w+)\s+(.+)$', line.strip())
            if m and "open" in m.group(2):
                open_ports.append((m.group(1), m.group(2), m.group(3).strip()))
            if "OS details:" in line:
                os_info = line.split("OS details:")[-1].strip()
            if "Running:" in line:
                os_info = os_info or line.split("Running:")[-1].strip()

        summary_items.append(f"[bold]Host:[/bold] {'[green]Up[/green]' if host_up else '[red]Down / No response[/red]'}")
        summary_items.append(f"[bold]Open ports:[/bold] [cyan]{len(open_ports)}[/cyan]")
        if os_info:
            summary_items.append(f"[bold]OS:[/bold] {os_info}")

        if open_ports:
            details_table = Table(border_style="dim", show_lines=False, padding=(0, 1))
            details_table.add_column("Port", style="cyan", justify="right")
            details_table.add_column("State", style="green")
            details_table.add_column("Service", style="white")
            for port, state, service in open_ports[:20]:
                details_table.add_row(port, state, service)
            if len(open_ports) > 20:
                summary_items.append(f"[dim]... and {len(open_ports) - 20} more ports[/dim]")

    # ── Nikto ─────────────────────────────────────────────────────
    elif "nikto" in tool:
        findings = []
        server = None
        for line in content_lines:
            if line.strip().startswith("+ Server:"):
                server = line.split("+ Server:")[-1].strip()
            elif line.strip().startswith("+") and ("OSVDB" in line or "found" in line.lower() or "vuln" in line.lower()):
                finding = line.strip().lstrip("+ ").strip()
                if finding:
                    findings.append(finding)
            elif line.strip().startswith("+") and len(line.strip()) > 10 and "+" != line.strip():
                txt = line.strip().lstrip("+ ").strip()
                if any(kw in txt.lower() for kw in ["header", "allow", "option", "cookie", "xss", "x-frame", "csrf"]):
                    findings.append(txt)

        if server:
            summary_items.append(f"[bold]Server:[/bold] {server}")
        summary_items.append(f"[bold]Findings:[/bold] [cyan]{len(findings)}[/cyan]")

        if findings:
            details_table = Table(border_style="dim", show_lines=False, padding=(0, 1))
            details_table.add_column("#", style="dim", width=4, justify="right")
            details_table.add_column("Finding", style="yellow")
            for i, f in enumerate(findings[:15], 1):
                details_table.add_row(str(i), f[:120])
            if len(findings) > 15:
                summary_items.append(f"[dim]... and {len(findings) - 15} more findings[/dim]")

    # ── Gobuster ──────────────────────────────────────────────────
    elif "gobuster" in tool:
        discovered = []
        for line in content_lines:
            # Gobuster output: /path (Status: 200) [Size: 1234]
            m = _re.match(r'^(/\S+)\s+\(Status:\s*(\d+)\)', line.strip())
            if m:
                discovered.append((m.group(1), m.group(2)))
            # Quiet mode: /path
            elif line.strip().startswith("/") and "Status:" not in line:
                path = line.strip().split()[0]
                discovered.append((path, "???"))

        summary_items.append(f"[bold]Paths found:[/bold] [cyan]{len(discovered)}[/cyan]")

        if discovered:
            details_table = Table(border_style="dim", show_lines=False, padding=(0, 1))
            details_table.add_column("Path", style="cyan")
            details_table.add_column("Status", style="green", justify="right")
            for path, status in discovered[:20]:
                color = "green" if status.startswith("2") else "yellow" if status.startswith("3") else "red"
                details_table.add_row(path, f"[{color}]{status}[/{color}]")
            if len(discovered) > 20:
                summary_items.append(f"[dim]... and {len(discovered) - 20} more paths[/dim]")

    # ── SQLMap ────────────────────────────────────────────────────
    elif "sqlmap" in tool:
        injectable = []
        databases = []
        tables = []
        for line in content_lines:
            if "is vulnerable" in line.lower() or "injectable" in line.lower():
                injectable.append(line.strip())
            m = _re.match(r'^\[\*\]\s+(.+)$', line.strip())
            if m:
                val = m.group(1).strip()
                if val and not val.startswith("---"):
                    databases.append(val)
            if "| " in line and "tables" not in line.lower():
                tables.append(line.strip())

        if injectable:
            summary_items.append(f"[bold red]Injections found:[/bold red] [red]{len(injectable)}[/red]")
            for inj in injectable[:5]:
                summary_items.append(f"  [red]>[/red] {inj[:100]}")
        else:
            summary_items.append("[bold]Injections found:[/bold] [green]0[/green]")
        if databases:
            summary_items.append(f"[bold]Databases:[/bold] {', '.join(databases[:10])}")

    # ── Hydra ─────────────────────────────────────────────────────
    elif "hydra" in tool:
        creds_found = []
        for line in content_lines:
            if "login:" in line.lower() and "password:" in line.lower():
                creds_found.append(line.strip())

        if creds_found:
            summary_items.append(f"[bold red]Credentials found:[/bold red] [red]{len(creds_found)}[/red]")
            details_table = Table(border_style="dim", show_lines=False, padding=(0, 1))
            details_table.add_column("#", style="dim", width=4, justify="right")
            details_table.add_column("Result", style="red bold")
            for i, cred in enumerate(creds_found[:10], 1):
                details_table.add_row(str(i), cred[:120])
        else:
            summary_items.append("[bold]Credentials found:[/bold] [green]0[/green]")

    # ── John / Hashcat ────────────────────────────────────────────
    elif "john" in tool or "hashcat" in tool:
        cracked = []
        for line in content_lines:
            # John: password (username)
            # Hashcat: hash:password
            if ":" in line and not line.startswith("#") and not line.startswith("["):
                parts = line.strip().split(":")
                if len(parts) >= 2 and len(parts[-1]) < 100:
                    cracked.append(line.strip())

        summary_items.append(f"[bold]Cracked:[/bold] [cyan]{len(cracked)}[/cyan]")
        if cracked:
            for c in cracked[:10]:
                summary_items.append(f"  [green]>[/green] {c[:80]}")

    # ── HTTP Probe (assessment) ───────────────────────────────────
    elif "http" in tool:
        status_code = None
        headers_missing = []
        server_info = None
        ssl_subject = None
        redirect_count = 0
        for line in content_lines:
            if line.startswith("Status:"):
                status_code = line.split("Status:")[-1].strip()
            if "Missing" in line and "]" in line:
                m = _re.match(r'\s*\[(\w+)\]\s+(.+?):\s+(.+)', line)
                if m:
                    headers_missing.append((m.group(2), m.group(1)))
            if "Server version disclosed" in line:
                server_info = line.split(":")[-1].strip()
            if line.strip().startswith("Subject:"):
                ssl_subject = line.split("Subject:")[-1].strip()
            if "->" in line and _re.match(r'^\s*\d{3}\s', line.strip()):
                redirect_count += 1

        if status_code:
            color = "green" if status_code.startswith("2") else "yellow" if status_code.startswith("3") else "red"
            summary_items.append(f"[bold]Status:[/bold] [{color}]{status_code}[/{color}]")
        if redirect_count:
            summary_items.append(f"[bold]Redirects:[/bold] {redirect_count}")
        if server_info:
            summary_items.append(f"[bold]Server:[/bold] [yellow]{server_info}[/yellow]")
        if ssl_subject:
            summary_items.append(f"[bold]SSL:[/bold] {ssl_subject}")
        if headers_missing:
            summary_items.append(f"[bold]Missing security headers:[/bold] [yellow]{len(headers_missing)}[/yellow]")
            for header, severity in headers_missing[:8]:
                color = "red" if severity == "High" else "yellow" if severity == "Medium" else "dim"
                summary_items.append(f"  [{color}][{severity}][/{color}] {header}")

    # ── OSINT ─────────────────────────────────────────────────────
    elif "osint" in tool:
        subdomains = []
        for line in content_lines:
            stripped = line.strip()
            if stripped and "." in stripped and not stripped.startswith(("Subdomain", "#", "[", "crt")):
                subdomains.append(stripped)
        count_match = _re.search(r'Subdomains found:\s*(\d+)', output)
        count = int(count_match.group(1)) if count_match else len(subdomains)
        summary_items.append(f"[bold]Subdomains found:[/bold] [cyan]{count}[/cyan]")
        if subdomains:
            for s in subdomains[:10]:
                summary_items.append(f"  [cyan]>[/cyan] {s}")
            if count > 10:
                summary_items.append(f"  [dim]... and {count - 10} more[/dim]")

    # ── Generic fallback ──────────────────────────────────────────
    else:
        total_lines = len(content_lines)
        summary_items.append(f"[bold]Output:[/bold] {total_lines} lines")
        # Show last 5 interesting lines
        interesting = [l for l in content_lines if l.strip() and len(l.strip()) > 5][-5:]
        if interesting:
            for line in interesting:
                summary_items.append(f"  [dim]│[/dim] {line.strip()[:100]}")

    # ── Render the summary ────────────────────────────────────────
    if not summary_items and not details_table:
        return  # Nothing to summarize

    summary_text = "\n".join(summary_items)

    from rich.console import Group
    parts = []
    if summary_text:
        from rich.text import Text
        parts.append(summary_text)
    if details_table:
        parts.append(details_table)

    console.print()
    console.print(Panel(
        Group(*parts) if len(parts) > 1 else parts[0],
        title=f"[bold bright_white]Scan Summary[/bold bright_white]",
        border_style="bright_cyan",
        padding=(1, 2),
    ))


def _load_targets_json() -> list[dict]:
    """Load targets as JSON. Auto-migrates old plain-text format."""
    if not TARGETS_FILE.exists():
        return []
    raw = TARGETS_FILE.read_text().strip()
    if not raw:
        return []
    # Try JSON first
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    # Migrate old plain-text format
    entries = [{"target": t.strip(), "notes": ""} for t in raw.splitlines() if t.strip()]
    TARGETS_FILE.write_text(json.dumps(entries, indent=2))
    return entries


def _save_targets_json(targets: list[dict]):
    TARGETS_FILE.write_text(json.dumps(targets, indent=2))


def save_target(target: str):
    """Save a target to the targets file."""
    entries = _load_targets_json()
    if not any(e["target"] == target for e in entries):
        entries.append({"target": target, "notes": ""})
        _save_targets_json(entries)


def load_targets() -> list[str]:
    """Load saved targets (returns list of target strings for compatibility)."""
    return [e["target"] for e in _load_targets_json()]


def load_targets_with_notes() -> list[dict]:
    """Load saved targets with notes."""
    return _load_targets_json()


def edit_target_notes(console: Console):
    """Let user pick a target and edit its notes."""
    from InquirerPy import inquirer
    entries = _load_targets_json()
    if not entries:
        console.print("[yellow]No saved targets.[/yellow]")
        return
    choices = [f"{e['target']} ({e['notes'] or 'no notes'})" for e in entries]
    choice = inquirer.select(message="Select target:", choices=choices, pointer="❯").execute()
    idx = choices.index(choice)
    note = inquirer.text(message="Note:", default=entries[idx]["notes"]).execute()
    entries[idx]["notes"] = note
    _save_targets_json(entries)
    console.print("[green]Note saved.[/green]")


def ask_target(console: Console, message: str = "Target (IP/hostname):") -> str | None:
    """Ask for a target with option to pick from saved targets."""
    from InquirerPy import inquirer

    entries = _load_targets_json()
    if entries:
        choices = ["Enter new target"] + [
            f"{e['target']} ({e['notes']})" if e["notes"] else e["target"]
            for e in entries
        ]
        choice = inquirer.select(
            message="Select target:",
            choices=choices,
            pointer="❯",
        ).execute()

        if choice != "Enter new target":
            # Extract target from display string
            target = choice.split(" (")[0] if " (" in choice else choice
            # Scope check
            from sectools.scope import is_in_scope
            scope_result = is_in_scope(target)
            if scope_result is False:
                console.print(f"[bold yellow]⚠ Warning: {target} is OUT OF SCOPE[/bold yellow]")
                proceed = inquirer.confirm(message="Proceed anyway?", default=False).execute()
                if not proceed:
                    return None
            return target

    target = inquirer.text(message=message).execute().strip()
    if not target:
        console.print("[red]No target provided.[/red]")
        return None

    save_target(target)

    # Scope check
    from sectools.scope import is_in_scope
    scope_result = is_in_scope(target)
    if scope_result is False:
        console.print(f"[bold yellow]⚠ Warning: {target} is OUT OF SCOPE[/bold yellow]")
        proceed = inquirer.confirm(message="Proceed anyway?", default=False).execute()
        if not proceed:
            return None

    return target


def _html_style():
    return """body { background: #1a1a2e; color: #e0e0e0; font-family: 'Courier New', monospace; padding: 40px; }
h1 { color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }
h2 { color: #ff6b6b; margin-top: 30px; }
h3 { color: #00d4ff; }
.scan { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; padding: 20px; margin: 15px 0; }
.meta { color: #888; font-size: 0.85em; margin-bottom: 10px; }
pre { background: #0a0a1a; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }
.badge { display: inline-block; background: #00d4ff; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
.section { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; padding: 20px; margin: 15px 0; }"""


def _build_technical(logs, timestamp):
    """Build Technical Detail report (original behavior)."""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = [
        f"<!DOCTYPE html><html><head><title>SecTools Report</title><style>{_html_style()}</style></head><body>",
        f"<h1>SecTools Scan Report</h1>",
        f"<p class='meta'>Generated: {now}</p>",
        f"<p><span class='badge'>{len(logs)} scans</span></p>",
    ]
    for log in logs[:20]:
        content = log.read_text()
        name = log.stem.replace("_", " ").title()
        mtime = datetime.datetime.fromtimestamp(log.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        html.append(f"<div class='scan'><h2>{name}</h2>")
        html.append(f"<p class='meta'>{mtime}</p>")
        safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html.append(f"<pre>{safe_content}</pre></div>")
    html.append("</body></html>")
    return html


def _build_executive(logs, timestamp):
    """Build Executive Summary report — high-level overview, no raw output."""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Extract unique targets from log filenames
    targets = set()
    for log in logs[:20]:
        parts = log.stem.split("_")
        if len(parts) >= 2:
            targets.add(parts[-2] if len(parts) > 2 else parts[0])
    html = [
        f"<!DOCTYPE html><html><head><title>Executive Summary</title><style>{_html_style()}</style></head><body>",
        f"<h1>Executive Summary</h1>",
        f"<p class='meta'>Generated: {now}</p>",
        f"<div class='section'>",
        f"<h2>Overview</h2>",
        f"<p>Total scans performed: <strong>{len(logs)}</strong></p>",
        f"<p>Unique scan types: <strong>{len({l.stem.split('_')[0] for l in logs[:20]})}</strong></p>",
        f"<p>Report period: last {len(logs[:20])} scans</p>",
        f"</div>",
        f"<div class='section'>",
        f"<h2>Target Summary</h2>",
        f"<ul>",
    ]
    for t in sorted(targets):
        html.append(f"<li>{t}</li>")
    html.append("</ul></div>")
    html.append("<div class='section'><h2>Scan Activity</h2><table border='1' cellpadding='8' style='border-collapse:collapse;width:100%;color:#e0e0e0'>")
    html.append("<tr><th>Scan</th><th>Date</th></tr>")
    for log in logs[:20]:
        name = log.stem.replace("_", " ").title()
        mtime = datetime.datetime.fromtimestamp(log.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        html.append(f"<tr><td>{name}</td><td>{mtime}</td></tr>")
    html.append("</table></div></body></html>")
    return html


def _build_compliance(logs, timestamp):
    """Build Compliance report — structured sections."""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = [
        f"<!DOCTYPE html><html><head><title>Compliance Report</title><style>{_html_style()}</style></head><body>",
        f"<h1>Compliance Assessment Report</h1>",
        f"<p class='meta'>Generated: {now}</p>",
        f"<div class='section'><h2>1. Scope</h2>",
        f"<p>This report covers {len(logs)} scan(s) stored in the SecTools log directory.</p></div>",
        f"<div class='section'><h2>2. Methodology</h2>",
        f"<p>Scans were performed using SecTools CLI with the following tools:</p><ul>",
    ]
    tools_used = sorted({l.stem.split("_")[0] for l in logs[:20]})
    for tool in tools_used:
        html.append(f"<li>{tool}</li>")
    html.append("</ul></div>")
    html.append(f"<div class='section'><h2>3. Findings</h2>")
    for log in logs[:20]:
        content = log.read_text()
        name = log.stem.replace("_", " ").title()
        mtime = datetime.datetime.fromtimestamp(log.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html.append(f"<h3>{name}</h3><p class='meta'>{mtime}</p><pre>{safe_content}</pre>")
    html.append("</div>")
    html.append(f"<div class='section'><h2>4. Recommendations</h2>")
    html.append("<p>Review all findings above and prioritise remediation based on risk severity.</p>")
    html.append("<p>Re-scan after remediation to verify fixes.</p></div>")
    html.append("</body></html>")
    return html


def generate_report(console: Console):
    """Generate an HTML report from recent log files."""
    if not LOGS_DIR.exists():
        console.print("[red]No logs found.[/red]")
        return

    logs = sorted(LOGS_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not logs:
        console.print("[red]No logs found.[/red]")
        return

    from InquirerPy import inquirer

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Template choice
    template = inquirer.select(
        message="Report template:",
        choices=["Technical Detail (full)", "Executive Summary", "Compliance"],
        pointer="❯",
    ).execute()

    if template.startswith("Executive"):
        html = _build_executive(logs, timestamp)
    elif template.startswith("Compliance"):
        html = _build_compliance(logs, timestamp)
    else:
        html = _build_technical(logs, timestamp)

    report_file = LOGS_DIR / f"report_{timestamp}.html"
    report_file.write_text("\n".join(html))
    console.print(f"  [bold green]✔[/bold green] HTML report saved: [cyan]{report_file}[/cyan]")

    export = inquirer.select(
        message="Open as:",
        choices=["Browser (HTML)", "PDF", "Both"],
        pointer="❯",
    ).execute()

    if export in ("Browser (HTML)", "Both"):
        import webbrowser
        webbrowser.open(f"file://{report_file}")

    if export in ("PDF", "Both"):
        _export_pdf(console, logs, timestamp)


def _export_pdf(console: Console, logs: list, timestamp: str):
    """Generate a PDF report from log files using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Courier", "B", 18)
    pdf.cell(0, 15, "SecTools Scan Report", ln=True, align="C")
    pdf.set_font("Courier", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.cell(0, 8, f"{len(logs)} scans", ln=True, align="C")
    pdf.ln(10)

    for log in logs[:20]:
        name = log.stem.replace("_", " ").title()
        mtime = datetime.datetime.fromtimestamp(log.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        content = log.read_text()

        pdf.set_font("Courier", "B", 12)
        pdf.cell(0, 10, name, ln=True)
        pdf.set_font("Courier", "", 8)
        pdf.cell(0, 6, mtime, ln=True)
        pdf.ln(2)
        pdf.set_font("Courier", "", 7)
        for line in content.splitlines():
            safe = line.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 4, safe, ln=True)
        pdf.ln(5)

    pdf_file = LOGS_DIR / f"report_{timestamp}.pdf"
    pdf.output(str(pdf_file))
    console.print(f"  [bold green]✔[/bold green] PDF saved: [cyan]{pdf_file}[/cyan]")
