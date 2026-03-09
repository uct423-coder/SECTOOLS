import subprocess
import datetime
from pathlib import Path
from InquirerPy import inquirer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from sectools.utils import extract_hostname, LOGS_DIR, save_target


RECON_SCANS = {
    "Quick recon (Nmap fast + Gobuster)": ["nmap_fast", "gobuster"],
    "Full recon (Nmap + Nikto + Gobuster)": ["nmap_full", "nikto", "gobuster"],
    "Web app recon (Nikto + Gobuster + SQLMap crawl)": ["nikto", "gobuster", "sqlmap_crawl"],
    "Stealth recon (Nmap SYN scan only)": ["nmap_stealth"],
}


def _run_scan(cmd: list[str], name: str, log_file: Path, console: Console) -> str:
    """Run a scan and return its output."""
    console.print(f"  [dim]{' '.join(cmd)}[/dim]")
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
        output = result.stdout or ""
    except subprocess.TimeoutExpired:
        output = "[TIMEOUT after 5 minutes]"
    except FileNotFoundError:
        output = f"[SKIPPED — {cmd[0]} not installed]"

    with open(log_file, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"# {name}\n")
        f.write(f"# Command: {' '.join(cmd)}\n")
        f.write(f"{'='*60}\n")
        f.write(output + "\n")

    return output


def run(console: Console):
    console.rule("[bold cyan]Recon Autopilot[/bold cyan]")
    console.print("[dim]Runs multiple scans on a target automatically.[/dim]\n")

    target = inquirer.text(message="Target (IP/hostname/URL):").execute().strip()
    if not target:
        console.print("[red]No target provided.[/red]")
        return

    hostname, was_url = extract_hostname(target)
    if was_url:
        console.print(f"[yellow]Extracted hostname: {hostname}[/yellow]")
    save_target(hostname)

    url_target = target if "://" in target else f"https://{hostname}"

    preset = inquirer.select(
        message="Recon type:",
        choices=list(RECON_SCANS.keys()),
        pointer="❯",
    ).execute()

    scans = RECON_SCANS[preset]
    wordlist = "/Users/u.c.t./Projects/CLI/wordlists/common.txt"

    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"recon_{hostname.replace('.', '_')}_{timestamp}.log"

    with open(log_file, "w") as f:
        f.write(f"# Recon Autopilot — {hostname}\n")
        f.write(f"# Started: {datetime.datetime.now().isoformat()}\n")
        f.write(f"# Preset: {preset}\n")

    scan_map = {
        "nmap_fast": (["nmap", "-F", hostname], "Nmap Fast Scan"),
        "nmap_full": (["nmap", "-sV", "--top-ports", "1000", hostname], "Nmap Full Scan"),
        "nmap_stealth": (["nmap", "-sS", "-T2", hostname], "Nmap Stealth Scan"),
        "nikto": (["nikto", "-h", hostname, "-maxtime", "120s"], "Nikto Web Scan"),
        "gobuster": (["gobuster", "dir", "-u", url_target, "-w", wordlist, "-t", "10", "-q", "--no-error"], "Gobuster Directory Scan"),
        "sqlmap_crawl": (["sqlmap", "-u", url_target, "--crawl=2", "--batch", "--forms"], "SQLMap Crawl"),
    }

    total = len(scans)
    console.print(f"\n[bold]Running {total} scans on [cyan]{hostname}[/cyan]...[/bold]\n")

    results = {}
    for i, scan_key in enumerate(scans, 1):
        cmd, name = scan_map[scan_key]
        console.print(f"[bold][{i}/{total}] {name}[/bold]")
        output = _run_scan(cmd, name, log_file, console)

        # Show summary
        lines = [l for l in output.splitlines() if l.strip()]
        if "[SKIPPED" in output or "[TIMEOUT" in output:
            console.print(f"  [yellow]{output.strip()}[/yellow]")
        else:
            console.print(f"  [green]Done — {len(lines)} lines of output[/green]")
        results[name] = output
        console.print()

    console.print(f"[bold green]Recon complete! Full log: {log_file}[/bold green]\n")

    # Print summary
    console.rule("[bold]Summary[/bold]")
    for name, output in results.items():
        console.print(f"\n[bold cyan]{name}[/bold cyan]")
        lines = output.strip().splitlines()
        # Show last 10 interesting lines
        interesting = [l for l in lines if l.strip() and not l.startswith("#")]
        for line in interesting[-10:]:
            console.print(f"  {line}")
