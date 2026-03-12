"""Security Assessment Wizard — automated multi-tool security assessment."""

import datetime
import json
import os
import ssl
import socket
import subprocess
import time
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from sectools.utils import (
    extract_hostname, pick_wordlist, save_target, check_installed,
    _html_style, LOGS_DIR, WORDLISTS_DIR,
)
from sectools.config import load_config
from sectools.http_probe import _get_ssl_info
from sectools.notifications import notify
from sectools.theme import bold as th_bold, rule_style, accent, primary

DEFAULT_WORDLIST = load_config().get("default_dirwordlist", str(WORDLISTS_DIR / "common.txt"))

# ── Scan matrix ────────────────────────────────────────────────────

SCAN_MATRIX = {
    "quick": [
        ("HTTP Probe", "_scan_http_probe"),
        ("Nmap Fast Scan", "_scan_nmap_fast"),
    ],
    "standard": [
        ("HTTP Probe", "_scan_http_probe"),
        ("OSINT Subdomain Enum", "_scan_osint"),
        ("Nmap Service Scan", "_scan_nmap_service"),
        ("Nikto Web Scan", "_scan_nikto"),
        ("Gobuster Dir Scan", "_scan_gobuster"),
    ],
    "deep": [
        ("HTTP Probe", "_scan_http_probe"),
        ("OSINT Subdomain Enum", "_scan_osint"),
        ("Nmap Service Scan", "_scan_nmap_service"),
        ("Nmap Vuln Scripts", "_scan_nmap_vuln"),
        ("Nikto Web Scan", "_scan_nikto"),
        ("Gobuster Dir Scan", "_scan_gobuster"),
        ("SQLMap Crawl", "_scan_sqlmap"),
        ("Hydra Brute Force", "_scan_hydra"),
    ],
}

DEPTH_LABELS = {"quick": "Quick (~3 min)", "standard": "Standard (~10 min)", "deep": "Deep (~20+ min)"}

# ── Security headers to check ─────────────────────────────────────

SECURITY_HEADERS = [
    ("Strict-Transport-Security", "High", "Enable HSTS to prevent protocol downgrade attacks."),
    ("Content-Security-Policy", "Medium", "Add a CSP header to mitigate XSS and injection attacks."),
    ("X-Frame-Options", "Medium", "Set to DENY or SAMEORIGIN to prevent clickjacking."),
    ("X-Content-Type-Options", "Low", "Set to 'nosniff' to prevent MIME-type sniffing."),
    ("X-XSS-Protection", "Low", "Set to '1; mode=block' for legacy XSS protection."),
    ("Referrer-Policy", "Low", "Control referrer information sent with requests."),
    ("Permissions-Policy", "Low", "Restrict browser features available to the page."),
]


# ── Entry point ────────────────────────────────────────────────────

def run(console: Console) -> None:
    """Security Assessment Wizard entry point."""
    console.print(f"\n{th_bold('━━━ Security Assessment Wizard ━━━')}\n")
    console.print("[dim]Automated multi-tool security assessment with reporting.[/dim]\n")

    # 1. Target URL
    url = inquirer.text(message="Target URL (e.g. https://example.com):").execute().strip()
    if not url:
        console.print("[red]No URL provided.[/red]")
        return
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    hostname, _ = extract_hostname(url)
    save_target(hostname)

    # Scope check
    from sectools.scope import is_in_scope
    if is_in_scope(hostname) is False:
        console.print(f"[bold yellow]⚠ Warning: {hostname} is OUT OF SCOPE[/bold yellow]")
        if not inquirer.confirm(message="Proceed anyway?", default=False).execute():
            return

    # 2. Depth
    depth = inquirer.select(
        message="Assessment depth:",
        choices=[
            {"name": "Quick (~3 min) — HTTP probe + fast Nmap", "value": "quick"},
            {"name": "Standard (~10 min) — adds OSINT, Nikto, Gobuster", "value": "standard"},
            {"name": "Deep (~20+ min) — adds vuln scripts, SQLMap, Hydra", "value": "deep"},
        ],
        pointer="❯",
    ).execute()

    # 3. Credentials (only for deep)
    credentials = None
    if depth == "deep":
        if inquirer.confirm(message="Provide login credentials for brute-force testing?", default=False).execute():
            cred_user = inquirer.text(message="Username:").execute().strip()
            cred_pass = inquirer.text(message="Password list path (or single password):").execute().strip()
            if cred_user and cred_pass:
                credentials = {"username": cred_user, "password": cred_pass}

    # 4. Wordlist
    wordlist = None
    scans = SCAN_MATRIX[depth]
    needs_wordlist = any(name in ("Gobuster Dir Scan",) for name, _ in scans)
    if needs_wordlist:
        if inquirer.confirm(message="Choose a custom wordlist? (default: common.txt)", default=False).execute():
            wordlist = pick_wordlist("Wordlist:", "DEFAULT_WORDLIST")
    if not wordlist:
        wordlist = "DEFAULT_WORDLIST"

    # 5. Summary
    summary = Table(title="Assessment Plan", border_style=primary())
    summary.add_column("Setting", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", url)
    summary.add_row("Hostname", hostname)
    summary.add_row("Depth", DEPTH_LABELS[depth])
    summary.add_row("Scans", ", ".join(name for name, _ in scans))
    summary.add_row("Credentials", "Provided" if credentials else "None")
    summary.add_row("Wordlist", wordlist)
    console.print(summary)

    if not inquirer.confirm(message="Start assessment?", default=True).execute():
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Ensure wordlists exist
    from sectools.wordlist_mgr import ensure_wordlists
    ensure_wordlists(console)

    # 6. Run
    config = {
        "url": url, "hostname": hostname, "depth": depth,
        "credentials": credentials, "wordlist": wordlist,
    }
    results = _run_assessment(console, config)

    # 7. Report
    html_path, pdf_path = _build_assessment_report(results, config)
    console.print(f"\n  [bold green]✔[/bold green] HTML report: [cyan]{html_path}[/cyan]")
    if pdf_path:
        console.print(f"  [bold green]✔[/bold green] PDF report:  [cyan]{pdf_path}[/cyan]")

    output = inquirer.select(
        message="Open report as:",
        choices=["Browser (HTML)", "Download PDF", "Both", "Skip"],
        pointer="❯",
    ).execute()

    if output in ("Browser (HTML)", "Both"):
        webbrowser.open(f"file://{html_path}")
    if output in ("Download PDF", "Both") and not pdf_path:
        pdf_path = _export_assessment_pdf(results, config)
        console.print(f"  [bold green]✔[/bold green] PDF saved: [cyan]{pdf_path}[/cyan]")

    # 8. AI advice
    _generate_ai_advice(console, results)

    notify("SecTools", f"Assessment of {hostname} complete")


# ── Scan orchestration ─────────────────────────────────────────────

def _run_assessment(console: Console, config: dict) -> dict:
    """Run all scans for the given depth and return results."""
    scans = SCAN_MATRIX[config["depth"]]
    results = {"scans": {}, "config": config, "start_time": datetime.datetime.now().isoformat()}

    console.print()
    console.print(Panel(
        f"[bold bright_white]Running {len(scans)} scan(s) against [cyan]{config['hostname']}[/cyan][/bold bright_white]",
        border_style=primary(),
        padding=(0, 2),
    ))
    console.print()

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold]{task.description}[/bold]"),
        BarColumn(bar_width=30, complete_style="cyan", finished_style="green"),
        TextColumn("[dim]{task.fields[status_text]}[/dim]"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        overall = progress.add_task("Overall", total=len(scans), status_text="")

        for i, (name, method_name) in enumerate(scans, 1):
            progress.update(overall, status_text=f"[{i}/{len(scans)}] {name}...")
            start = time.time()
            try:
                scan_func = globals()[method_name]
                output, findings = scan_func(config)
                duration = round(time.time() - start, 1)
                status = "ok"
            except FileNotFoundError as e:
                duration = round(time.time() - start, 1)
                output = f"Tool not installed: {e.filename or 'unknown'}"
                findings = 0
                status = "skipped"
            except Exception as e:
                duration = round(time.time() - start, 1)
                output = f"Error: {e}"
                findings = 0
                status = "error"

            results["scans"][name] = {
                "output": output, "status": status,
                "duration": duration, "findings": findings,
            }

            # Print result line
            if status == "ok":
                console.print(f"  [green]✔[/green] {name} [dim]({duration}s, {findings} finding(s))[/dim]")
            elif status == "skipped":
                console.print(f"  [yellow]⚠[/yellow] {name} [dim](skipped — tool not installed)[/dim]")
            else:
                console.print(f"  [red]✘[/red] {name} [dim](error — {output})[/dim]")

            progress.advance(overall)

        progress.update(overall, status_text="[bold green]Done![/bold green]")

    results["end_time"] = datetime.datetime.now().isoformat()

    # Summary table
    console.print()
    summary_tbl = Table(
        title="[bold]Assessment Results[/bold]",
        border_style=accent(),
        show_lines=True,
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey11"],
        padding=(0, 1),
    )
    summary_tbl.add_column("Scan", style="bold")
    summary_tbl.add_column("Status", justify="center")
    summary_tbl.add_column("Findings", justify="right")
    summary_tbl.add_column("Duration", justify="right", style="dim")

    for scan_name, data in results["scans"].items():
        if data["status"] == "ok" and data["findings"] == 0:
            st = "[bold green]✔ Pass[/bold green]"
        elif data["status"] == "ok":
            st = "[bold yellow]⚠ Issues[/bold yellow]"
        elif data["status"] == "skipped":
            st = "[dim]⊘ Skipped[/dim]"
        else:
            st = "[bold red]✘ Error[/bold red]"
        summary_tbl.add_row(scan_name, st, str(data["findings"]), f"{data['duration']}s")

    console.print(summary_tbl)

    # Per-scan smart summaries
    from sectools.utils import _show_scan_summary
    for scan_name, data in results["scans"].items():
        if data["status"] != "ok" or not data["output"]:
            continue
        # Map scan name to tool key for the parser
        tool_key = scan_name.lower().split()[0]  # "http", "osint", "nmap", "nikto", "gobuster", "sqlmap", "hydra"
        _show_scan_summary(console, tool_key, data["output"])

    console.print()

    # Save raw log
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"assessment_{config['hostname']}_{ts}.log"
    with open(log_path, "w") as f:
        f.write(f"# Security Assessment — {config['hostname']}\n")
        f.write(f"# URL: {config['url']}\n")
        f.write(f"# Depth: {config['depth']}\n")
        f.write(f"# Date: {results['start_time']}\n\n")
        for scan_name, data in results["scans"].items():
            f.write(f"{'='*60}\n{scan_name} [{data['status']}] ({data['duration']}s)\n{'='*60}\n")
            f.write(data["output"] + "\n\n")
    results["log_path"] = str(log_path)

    return results


# ── Individual scan functions ──────────────────────────────────────
# Each returns (output_text, findings_count)

def _scan_http_probe(config: dict) -> tuple[str, int]:
    """HTTP probe: headers, redirects, SSL."""
    url = config["url"]
    hostname = config["hostname"]
    lines = []
    findings = 0

    # HTTP request
    redirects = []

    class RedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            redirects.append(f"{code} -> {newurl}")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(RedirectHandler)
    req = urllib.request.Request(url, headers={"User-Agent": "SecTools-Assessment/1.0"})

    try:
        resp = opener.open(req, timeout=10)
    except urllib.error.HTTPError as e:
        resp = e
    except urllib.error.URLError as e:
        return f"Connection error: {e.reason}", 1

    status = getattr(resp, "status", getattr(resp, "code", "N/A"))
    lines.append(f"Status: {status}")

    if redirects:
        lines.append(f"Redirects: {len(redirects)}")
        for r in redirects:
            lines.append(f"  {r}")

    # Headers
    headers_dict = dict(resp.headers.items())
    lines.append(f"\nResponse Headers ({len(headers_dict)}):")
    for k, v in headers_dict.items():
        lines.append(f"  {k}: {v}")

    # Security header analysis
    header_issues = _analyze_security_headers(headers_dict)
    if header_issues:
        findings += len(header_issues)
        lines.append(f"\nSecurity Header Issues ({len(header_issues)}):")
        for issue in header_issues:
            lines.append(f"  [{issue['severity']}] {issue['header']}: {issue['status']}")

    # Server disclosure
    server = headers_dict.get("Server", "")
    if server and any(c.isdigit() for c in server):
        findings += 1
        lines.append(f"\n⚠ Server version disclosed: {server}")

    # SSL cert
    parsed = urlparse(url)
    if parsed.scheme == "https":
        cert = _get_ssl_info(parsed.hostname, parsed.port or 443)
        if cert:
            subject = dict(x[0] for x in cert.get("subject", ()))
            issuer = dict(x[0] for x in cert.get("issuer", ()))
            lines.append(f"\nSSL Certificate:")
            lines.append(f"  Subject: {subject.get('commonName', 'N/A')}")
            lines.append(f"  Issuer: {issuer.get('commonName', 'N/A')}")
            lines.append(f"  Not After: {cert.get('notAfter', 'N/A')}")

    return "\n".join(lines), findings


def _scan_osint(config: dict) -> tuple[str, int]:
    """OSINT subdomain enumeration via crt.sh."""
    hostname = config["hostname"]
    url = f"https://crt.sh/?q=%.{hostname}&output=json"
    req = urllib.request.Request(url, headers={"User-Agent": "SecTools-Assessment/1.0"})

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
    except Exception as e:
        return f"crt.sh query failed: {e}", 0

    subdomains = sorted({entry.get("name_value", "").strip() for entry in data if entry.get("name_value")})
    # Filter wildcards and deduplicate
    subdomains = [s for s in subdomains if not s.startswith("*")]

    lines = [f"Subdomains found: {len(subdomains)}", ""]
    for s in subdomains[:50]:
        lines.append(f"  {s}")
    if len(subdomains) > 50:
        lines.append(f"  ... and {len(subdomains) - 50} more")

    return "\n".join(lines), len(subdomains)


def _scan_nmap_fast(config: dict) -> tuple[str, int]:
    """Nmap fast scan (-F)."""
    if not check_installed("nmap"):
        raise FileNotFoundError(None, "nmap")
    result = subprocess.run(
        ["nmap", "-F", "--open", config["hostname"]],
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    # Count open ports
    findings = output.count("/open/") + output.count("open ")
    return output, findings


def _scan_nmap_service(config: dict) -> tuple[str, int]:
    """Nmap service version scan."""
    if not check_installed("nmap"):
        raise FileNotFoundError(None, "nmap")
    result = subprocess.run(
        ["nmap", "-sV", "--top-ports", "1000", "--open", config["hostname"]],
        capture_output=True, text=True, timeout=300,
    )
    output = result.stdout + result.stderr
    findings = output.count("/open/") + output.count("open ")
    return output, findings


def _scan_nmap_vuln(config: dict) -> tuple[str, int]:
    """Nmap vuln scripts."""
    if not check_installed("nmap"):
        raise FileNotFoundError(None, "nmap")
    result = subprocess.run(
        ["nmap", "--script", "vuln", config["hostname"]],
        capture_output=True, text=True, timeout=600,
    )
    output = result.stdout + result.stderr
    findings = output.lower().count("vulnerable") + output.lower().count("vuln")
    return output, findings


def _scan_nikto(config: dict) -> tuple[str, int]:
    """Nikto web scan."""
    if not check_installed("nikto"):
        raise FileNotFoundError(None, "nikto")
    result = subprocess.run(
        ["nikto", "-h", config["url"], "-maxtime", "300s"],
        capture_output=True, text=True, timeout=360,
    )
    output = result.stdout + result.stderr
    # Count OSVDB/finding lines
    findings = sum(1 for line in output.splitlines() if line.strip().startswith("+") and "OSVDB" in line)
    return output, findings


def _scan_gobuster(config: dict) -> tuple[str, int]:
    """Gobuster directory scan."""
    if not check_installed("gobuster"):
        raise FileNotFoundError(None, "gobuster")
    wordlist = config.get("wordlist", "DEFAULT_WORDLIST")
    if not Path(wordlist).exists():
        return f"Wordlist not found: {wordlist}", 0
    result = subprocess.run(
        ["gobuster", "dir", "-u", config["url"], "-w", wordlist, "-q", "-t", "10"],
        capture_output=True, text=True, timeout=300,
    )
    output = result.stdout + result.stderr
    findings = sum(1 for line in output.splitlines() if line.strip() and "Status:" in line)
    return output, findings


def _scan_sqlmap(config: dict) -> tuple[str, int]:
    """SQLMap crawl scan."""
    if not check_installed("sqlmap"):
        raise FileNotFoundError(None, "sqlmap")
    result = subprocess.run(
        ["sqlmap", "-u", config["url"], "--batch", "--crawl=2", "--random-agent"],
        capture_output=True, text=True, timeout=600,
    )
    output = result.stdout + result.stderr
    findings = output.lower().count("injectable") + output.lower().count("vulnerability")
    return output, findings


def _scan_hydra(config: dict) -> tuple[str, int]:
    """Hydra brute force (only if credentials provided)."""
    creds = config.get("credentials")
    if not creds:
        return "Skipped — no credentials provided.", 0
    if not check_installed("hydra"):
        raise FileNotFoundError(None, "hydra")

    cmd = [
        "hydra", "-l", creds["username"], "-P", creds["password"],
        config["hostname"], "http-get", "/",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    output = result.stdout + result.stderr
    findings = output.lower().count("login:") + output.lower().count("valid")
    return output, findings


# ── Security header analysis ───────────────────────────────────────

def _analyze_security_headers(headers: dict) -> list[dict]:
    """Check response headers for common security misconfigurations."""
    # Normalize header keys to lowercase for comparison
    lower_headers = {k.lower(): v for k, v in headers.items()}
    issues = []

    for header_name, severity, recommendation in SECURITY_HEADERS:
        if header_name.lower() not in lower_headers:
            issues.append({
                "header": header_name,
                "status": "Missing",
                "severity": severity,
                "recommendation": recommendation,
            })

    # Server version disclosure
    server = lower_headers.get("server", "")
    if server and any(c.isdigit() for c in server):
        issues.append({
            "header": "Server",
            "status": f"Version disclosed: {server}",
            "severity": "Medium",
            "recommendation": "Remove or obscure server version information.",
        })

    return issues


# ── Report builder ─────────────────────────────────────────────────

def _build_assessment_report(results: dict, config: dict) -> tuple[Path, Path | None]:
    """Build HTML and PDF assessment reports. Returns (html_path, pdf_path)."""
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    scans = results["scans"]
    total = len(scans)
    passed = sum(1 for s in scans.values() if s["status"] == "ok" and s["findings"] == 0)
    issues = sum(1 for s in scans.values() if s["status"] == "ok" and s["findings"] > 0)
    skipped = sum(1 for s in scans.values() if s["status"] == "skipped")
    errors = sum(1 for s in scans.values() if s["status"] == "error")
    total_findings = sum(s["findings"] for s in scans.values())

    # Risk rating
    if total_findings == 0:
        risk = ("Low", "#4caf50")
    elif total_findings <= 5:
        risk = ("Medium", "#ff9800")
    else:
        risk = ("High", "#f44336")

    # HTML
    html = [
        f"<!DOCTYPE html><html><head><title>Security Assessment — {config['hostname']}</title>",
        f"<style>{_html_style()}",
        ".summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin: 20px 0; }",
        ".summary-card { background: #0a0a1a; border-radius: 8px; padding: 15px; text-align: center; }",
        ".summary-card .num { font-size: 2em; font-weight: bold; }",
        ".risk-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 1.1em; }",
        "details { margin: 10px 0; }",
        "summary { cursor: pointer; color: #00d4ff; }",
        ".severity-high { color: #f44336; } .severity-medium { color: #ff9800; } .severity-low { color: #4caf50; }",
        "</style></head><body>",
        f"<h1>Security Assessment Report</h1>",
        f"<p class='meta'>Target: <strong>{config['url']}</strong> | Depth: {DEPTH_LABELS[config['depth']]} | Date: {now}</p>",

        # Executive summary
        f"<div class='section'><h2>Executive Summary</h2>",
        f"<div class='summary-grid'>",
        f"<div class='summary-card'><div class='num'>{total}</div>Scans Run</div>",
        f"<div class='summary-card'><div class='num' style='color:#4caf50'>{passed}</div>Clean</div>",
        f"<div class='summary-card'><div class='num' style='color:#ff9800'>{issues}</div>With Issues</div>",
        f"<div class='summary-card'><div class='num' style='color:#888'>{skipped}</div>Skipped</div>",
        f"<div class='summary-card'><div class='num' style='color:{risk[1]}'>{total_findings}</div>Findings</div>",
        f"</div>",
        f"<p>Overall Risk: <span class='risk-badge' style='background:{risk[1]};color:#000'>{risk[0]}</span></p>",
        f"</div>",
    ]

    # Per-scan sections
    for scan_name, data in scans.items():
        if data["status"] == "ok" and data["findings"] == 0:
            badge = "<span class='badge' style='background:#4caf50'>✔ Pass</span>"
        elif data["status"] == "ok":
            badge = "<span class='badge' style='background:#ff9800'>⚠ Issues Found</span>"
        elif data["status"] == "skipped":
            badge = "<span class='badge' style='background:#888'>⊘ Skipped</span>"
        else:
            badge = "<span class='badge' style='background:#f44336'>✘ Error</span>"

        safe_output = data["output"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html.append(f"<div class='scan'><h2>{scan_name} {badge}</h2>")
        html.append(f"<p class='meta'>Duration: {data['duration']}s | Findings: {data['findings']}</p>")
        html.append(f"<details><summary>Show raw output</summary><pre>{safe_output}</pre></details>")
        html.append("</div>")

    # Security headers section (from HTTP Probe)
    http_data = scans.get("HTTP Probe", {})
    if http_data.get("status") == "ok" and "Security Header Issues" in http_data.get("output", ""):
        html.append("<div class='section'><h2>Security Header Analysis</h2><table border='1' cellpadding='8' style='border-collapse:collapse;width:100%;color:#e0e0e0'>")
        html.append("<tr><th>Header</th><th>Status</th><th>Severity</th><th>Recommendation</th></tr>")
        # Re-parse from output lines
        for line in http_data["output"].splitlines():
            if line.strip().startswith("["):
                # Format: [Severity] Header: Status
                import re
                m = re.match(r'\s*\[(\w+)\]\s+(.+?):\s+(.+)', line)
                if m:
                    sev, header, status_text = m.groups()
                    sev_class = f"severity-{sev.lower()}"
                    rec = next((r for h, _, r in SECURITY_HEADERS if h == header), "")
                    html.append(f"<tr><td>{header}</td><td>{status_text}</td><td class='{sev_class}'>{sev}</td><td>{rec}</td></tr>")
        html.append("</table></div>")

    html.append("</body></html>")

    html_path = LOGS_DIR / f"assessment_{config['hostname']}_{ts}.html"
    html_path.write_text("\n".join(html))

    # PDF
    pdf_path = None
    try:
        pdf_path = _export_assessment_pdf(results, config, ts)
    except ImportError:
        pass

    return html_path, pdf_path


def _export_assessment_pdf(results: dict, config: dict, ts: str | None = None) -> Path:
    """Generate PDF assessment report using fpdf2."""
    from fpdf import FPDF

    if not ts:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Courier", "B", 18)
    pdf.cell(0, 15, "Security Assessment Report", ln=True, align="C")
    pdf.set_font("Courier", "", 10)
    pdf.cell(0, 8, f"Target: {config['url']}", ln=True, align="C")
    pdf.cell(0, 8, f"Depth: {DEPTH_LABELS[config['depth']]}  |  Date: {results.get('start_time', '')[:19]}", ln=True, align="C")
    pdf.ln(10)

    # Summary
    scans = results["scans"]
    total_findings = sum(s["findings"] for s in scans.values())
    pdf.set_font("Courier", "B", 12)
    pdf.cell(0, 10, f"Total Findings: {total_findings}", ln=True)
    pdf.ln(5)

    # Per-scan
    for scan_name, data in scans.items():
        pdf.set_font("Courier", "B", 11)
        status_mark = "PASS" if data["status"] == "ok" and data["findings"] == 0 else data["status"].upper()
        pdf.cell(0, 8, f"{scan_name} [{status_mark}] ({data['duration']}s)", ln=True)
        pdf.set_font("Courier", "", 7)
        for line in data["output"].splitlines()[:40]:
            safe = line.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 4, safe, ln=True)
        if len(data["output"].splitlines()) > 40:
            pdf.cell(0, 4, "... (truncated)", ln=True)
        pdf.ln(3)

    pdf_path = LOGS_DIR / f"assessment_{config['hostname']}_{ts}.pdf"
    pdf.output(str(pdf_path))
    return pdf_path


# ── AI remediation advice ─────────────────────────────────────────

def _generate_ai_advice(console: Console, results: dict) -> None:
    """Optionally generate AI-powered remediation advice via Claude API."""
    if not inquirer.confirm(message="Generate AI-powered remediation advice?", default=False).execute():
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[yellow]ANTHROPIC_API_KEY not set. Set it to enable AI advice:[/yellow]")
        console.print("[dim]  export ANTHROPIC_API_KEY=sk-ant-...[/dim]")
        return

    # Build condensed findings summary
    summary_lines = []
    for scan_name, data in results["scans"].items():
        if data["status"] == "ok" and data["findings"] > 0:
            # Include first 20 lines of output for context
            excerpt = "\n".join(data["output"].splitlines()[:20])
            summary_lines.append(f"## {scan_name} ({data['findings']} findings)\n{excerpt}")

    if not summary_lines:
        console.print("[green]No issues found — no remediation needed.[/green]")
        return

    findings_text = "\n\n".join(summary_lines)

    prompt = (
        f"You are a cybersecurity expert. Analyze the following security assessment findings "
        f"for {results['config']['url']} and provide prioritized remediation steps.\n\n"
        f"Findings:\n{findings_text}\n\n"
        f"Provide a concise, prioritized list of remediation actions grouped by severity "
        f"(Critical, High, Medium, Low). Include specific steps, not just general advice."
    )

    console.print("[dim]Generating AI advice...[/dim]")

    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode())
        advice = result.get("content", [{}])[0].get("text", "No response.")

        console.print(Panel(advice, title="AI Remediation Advice", border_style="green", expand=False))

    except Exception as e:
        console.print(f"[red]AI advice failed: {e}[/red]")
