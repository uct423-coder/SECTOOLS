"""Workflow engine — chain multiple tools into automated pipelines."""

import json
import re
import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from InquirerPy import inquirer

from sectools.utils import (
    extract_hostname, run_logged, save_target, LOGS_DIR,
)
from sectools.config import load_config, save_config

WORKFLOWS_FILE = Path.home() / ".sectools-workflows.json"

# ── Built-in workflow templates ───────────────────────────────────────

BUILTIN_WORKFLOWS = {
    "Web App Recon": {
        "description": "Nmap → Nikto → Gobuster → SQLMap crawl",
        "steps": [
            {"tool": "nmap", "args": ["-sV", "--top-ports", "1000"], "label": "Nmap Service Scan"},
            {"tool": "nikto", "args": ["-maxtime", "120s"], "label": "Nikto Web Scan"},
            {"tool": "gobuster", "args": ["dir", "-t", "10", "-q", "--no-error"], "needs_wordlist": True, "needs_url": True, "label": "Gobuster Dir Scan"},
            {"tool": "sqlmap", "args": ["--crawl=2", "--batch", "--forms"], "needs_url": True, "label": "SQLMap Crawl"},
        ],
    },
    "Quick Port & Web": {
        "description": "Fast Nmap → Nikto on discovered web ports",
        "steps": [
            {"tool": "nmap", "args": ["-F", "-sV"], "label": "Nmap Fast Scan"},
            {"tool": "nikto", "args": [], "label": "Nikto Web Scan"},
        ],
    },
    "Full Network Audit": {
        "description": "Full Nmap → Vuln scripts → Nikto → Gobuster",
        "steps": [
            {"tool": "nmap", "args": ["-sV", "-p-"], "label": "Nmap Full Port Scan"},
            {"tool": "nmap", "args": ["--script", "vuln"], "label": "Nmap Vuln Scripts"},
            {"tool": "nikto", "args": ["-ssl"], "label": "Nikto SSL Scan"},
            {"tool": "gobuster", "args": ["dir", "-t", "10", "-q", "--no-error"], "needs_wordlist": True, "needs_url": True, "label": "Gobuster Dir Scan"},
        ],
    },
    "Stealth Recon": {
        "description": "Low-and-slow SYN scan → OSINT subdomain enum",
        "steps": [
            {"tool": "nmap", "args": ["-sS", "-T2", "--top-ports", "100"], "label": "Nmap Stealth Scan"},
        ],
    },
    "Brute Force Pipeline": {
        "description": "Nmap service detection → Hydra brute force",
        "steps": [
            {"tool": "nmap", "args": ["-sV", "--top-ports", "100"], "label": "Nmap Service Detect"},
            {"tool": "hydra", "args": [], "interactive": True, "label": "Hydra Brute Force"},
        ],
    },
}


def _load_custom_workflows() -> dict:
    if WORKFLOWS_FILE.exists():
        try:
            return json.loads(WORKFLOWS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_custom_workflows(workflows: dict):
    WORKFLOWS_FILE.write_text(json.dumps(workflows, indent=2))


def _build_command(step: dict, hostname: str, url_target: str, wordlist: str) -> list[str]:
    """Build the command list for a workflow step."""
    tool = step["tool"]
    args = list(step.get("args", []))

    if tool == "nmap":
        return ["nmap"] + args + [hostname]
    elif tool == "nikto":
        return ["nikto", "-h", hostname] + args
    elif tool == "gobuster":
        if step.get("needs_wordlist"):
            return ["gobuster"] + args + ["-u", url_target, "-w", wordlist]
        return ["gobuster"] + args + ["-u", url_target]
    elif tool == "sqlmap":
        return ["sqlmap", "-u", url_target, "--batch"] + args
    elif tool == "hydra":
        return None  # Interactive — handled separately
    else:
        return [tool] + args + [hostname]


def _run_workflow(console: Console, name: str, workflow: dict):
    """Execute a workflow's steps sequentially."""
    steps = workflow["steps"]

    # Get target
    target = inquirer.text(message="Target (IP/hostname/URL):").execute().strip()
    if not target:
        console.print("[red]No target provided.[/red]")
        return

    hostname, was_url = extract_hostname(target)
    if was_url:
        console.print(f"[yellow]Extracted hostname: {hostname}[/yellow]")
    save_target(hostname)

    url_target = target if "://" in target else f"https://{hostname}"

    # Wordlist (if any step needs it)
    config = load_config()
    wordlist = config.get("default_dirwordlist", "common.txt")
    needs_wl = any(s.get("needs_wordlist") for s in steps)
    if needs_wl:
        wordlist = inquirer.text(
            message="Wordlist path:",
            default=wordlist,
        ).execute().strip()

    # Confirm
    console.print()
    console.print(Panel(
        "\n".join(f"  [{i+1}] {s['label']}" for i, s in enumerate(steps)),
        title=f"[bold cyan]{name}[/bold cyan]",
        subtitle=f"Target: {hostname}",
        border_style="cyan",
    ))

    if not inquirer.confirm(message=f"Run {len(steps)} steps?", default=True).execute():
        return

    # Setup log
    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"workflow_{hostname.replace('.', '_')}_{timestamp}.log"

    with open(log_file, "w") as f:
        f.write(f"# Workflow: {name}\n")
        f.write(f"# Target: {hostname}\n")
        f.write(f"# Started: {datetime.datetime.now().isoformat()}\n")
        f.write(f"# Steps: {len(steps)}\n\n")

    console.print(f"\n[bold]Running workflow: [cyan]{name}[/cyan] on [cyan]{hostname}[/cyan][/bold]\n")

    results = {}
    for i, step in enumerate(steps, 1):
        label = step["label"]
        console.rule(f"[bold][{i}/{len(steps)}] {label}[/bold]")

        if step.get("interactive"):
            console.print(f"[yellow]Skipping {label} — requires interactive input.[/yellow]")
            console.print("[dim]Run this tool manually from the main menu.[/dim]")
            results[label] = "[SKIPPED — interactive]"
            continue

        cmd = _build_command(step, hostname, url_target, wordlist)
        if cmd is None:
            results[label] = "[SKIPPED]"
            continue

        # Use run_logged for each step (streams output + saves individual log)
        try:
            run_logged(cmd, console, f"workflow_{step['tool']}")
            results[label] = "completed"
        except FileNotFoundError:
            console.print(f"[red]{step['tool']} is not installed — skipping.[/red]")
            results[label] = f"[SKIPPED — {step['tool']} not installed]"
        except KeyboardInterrupt:
            console.print(f"\n[yellow]Step interrupted. Continue workflow?[/yellow]")
            if not inquirer.confirm(message="Continue remaining steps?", default=True).execute():
                break

        # Append to workflow log
        with open(log_file, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"# Step {i}: {label}\n")
            f.write(f"# Status: {results[label]}\n")
            f.write(f"{'='*60}\n")

        console.print()

    # Summary
    console.print()
    console.rule("[bold]Workflow Summary[/bold]")
    for label, status in results.items():
        if status == "completed":
            console.print(f"  [green]✓[/green] {label}")
        else:
            console.print(f"  [yellow]⊘[/yellow] {label} — {status}")

    console.print(f"\n[bold green]Workflow log: {log_file}[/bold green]")

    from sectools.notifications import notify
    notify("SecTools", f"Workflow '{name}' complete")


def _create_workflow(console: Console):
    """Let user build a custom workflow."""
    name = inquirer.text(message="Workflow name:").execute().strip()
    if not name:
        console.print("[red]No name provided.[/red]")
        return

    description = inquirer.text(message="Description:").execute().strip()

    available_tools = {
        "Nmap — Port scan": {"tool": "nmap"},
        "Nmap — Vuln scripts": {"tool": "nmap", "args": ["--script", "vuln"]},
        "Nmap — OS detection": {"tool": "nmap", "args": ["-O", "-sV"]},
        "Nikto — Web scan": {"tool": "nikto"},
        "Nikto — SSL scan": {"tool": "nikto", "args": ["-ssl"]},
        "Gobuster — Dir brute-force": {"tool": "gobuster", "args": ["dir", "-t", "10", "-q", "--no-error"], "needs_wordlist": True, "needs_url": True},
        "Gobuster — DNS brute-force": {"tool": "gobuster", "args": ["dns"], "needs_wordlist": True},
        "SQLMap — Crawl": {"tool": "sqlmap", "args": ["--crawl=2", "--batch", "--forms"], "needs_url": True},
        "SQLMap — Basic": {"tool": "sqlmap", "args": ["--batch"], "needs_url": True},
    }

    steps = []
    console.print("[dim]Add steps to your workflow. Select 'Done' when finished.[/dim]\n")

    while True:
        choices = list(available_tools.keys()) + ["Done"]
        choice = inquirer.select(
            message=f"Add step {len(steps)+1}:",
            choices=choices,
            pointer="❯",
        ).execute()

        if choice == "Done":
            break

        step_template = dict(available_tools[choice])

        # Ask for custom flags
        extra = inquirer.text(message="Extra flags (or leave empty):").execute().strip()
        if extra:
            step_template.setdefault("args", [])
            step_template["args"] = step_template["args"] + extra.split()

        step_template["label"] = choice.split(" — ")[0] + (f" ({extra})" if extra else "")
        steps.append(step_template)
        console.print(f"  [green]Added:[/green] {step_template['label']}")

    if not steps:
        console.print("[yellow]No steps added.[/yellow]")
        return

    workflows = _load_custom_workflows()
    workflows[name] = {"description": description, "steps": steps}
    _save_custom_workflows(workflows)
    console.print(f"\n[bold green]Workflow '{name}' saved with {len(steps)} steps.[/bold green]")


def _delete_workflow(console: Console):
    """Delete a custom workflow."""
    workflows = _load_custom_workflows()
    if not workflows:
        console.print("[yellow]No custom workflows saved.[/yellow]")
        return

    choices = list(workflows.keys()) + ["Cancel"]
    choice = inquirer.select(message="Delete workflow:", choices=choices, pointer="❯").execute()
    if choice == "Cancel":
        return

    del workflows[choice]
    _save_custom_workflows(workflows)
    console.print(f"[green]Deleted '{choice}'.[/green]")


def run(console: Console):
    """Workflow engine menu."""
    console.rule("[bold cyan]Workflows[/bold cyan]")
    console.print("[dim]Chain multiple tools into automated pipelines.[/dim]\n")

    while True:
        # Merge built-in + custom
        custom = _load_custom_workflows()
        all_workflows = {}

        choices = []
        if BUILTIN_WORKFLOWS:
            choices.append("── Built-in ──")
            for name, wf in BUILTIN_WORKFLOWS.items():
                label = f"{name}  [dim]— {wf['description']}[/dim]"
                choices.append(name)
                all_workflows[name] = wf

        if custom:
            choices.append("── Custom ──")
            for name, wf in custom.items():
                choices.append(name)
                all_workflows[name] = wf

        choices.append("── Manage ──")
        choices.extend(["Create New Workflow", "Delete Workflow", "Back"])

        choice = inquirer.select(
            message="Workflows:",
            choices=choices,
            pointer="❯",
        ).execute()

        if choice == "Back":
            return
        elif choice == "Create New Workflow":
            _create_workflow(console)
        elif choice == "Delete Workflow":
            _delete_workflow(console)
        elif choice.startswith("──"):
            continue
        elif choice in all_workflows:
            try:
                _run_workflow(console, choice, all_workflows[choice])
            except KeyboardInterrupt:
                console.print("\n[yellow]Workflow interrupted.[/yellow]")
        console.print()
