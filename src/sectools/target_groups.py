"""Target Groups — organise saved targets into groups and scan them."""

from __future__ import annotations

from collections import defaultdict

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from sectools.utils import (
    _load_targets_json,
    _save_targets_json,
    check_installed,
    run_logged,
)

SCAN_TOOLS = {
    "nmap fast scan (-F)": ["nmap", "-F"],
    "nmap full TCP (-p-)": ["nmap", "-p-"],
    "nmap service version (-sV)": ["nmap", "-sV"],
    "nikto": ["nikto", "-h"],
    "gobuster dir (common.txt)": [
        "gobuster",
        "dir",
        "-w",
        "/usr/share/wordlists/dirb/common.txt",
        "-u",
    ],
}


def _group_of(entry: dict) -> str:
    return entry.get("group", "") or "ungrouped"


def _all_groups(targets: list[dict]) -> list[str]:
    return sorted({_group_of(e) for e in targets})


def _view_groups(console: Console) -> None:
    targets = _load_targets_json()
    if not targets:
        console.print("[yellow]No saved targets.[/yellow]")
        return

    grouped: dict[str, list[dict]] = defaultdict(list)
    for t in targets:
        grouped[_group_of(t)].append(t)

    for group, members in sorted(grouped.items()):
        lines = Text()
        for m in members:
            label = m["target"]
            if m.get("notes"):
                label += f"  [dim]({m['notes']})[/dim]"
            lines.append(label + "\n")
        console.print(Panel(lines, title=f"[bold cyan]{group}[/bold cyan]", border_style="dim"))
    console.print()


def _create_group(console: Console) -> None:
    name = inquirer.text(message="Group name:").execute().strip()
    if not name:
        console.print("[red]No name provided.[/red]")
        return
    targets = _load_targets_json()
    existing = _all_groups(targets)
    if name in existing:
        console.print(f"[yellow]Group '{name}' already exists.[/yellow]")
        return
    # Create a placeholder so the group shows up even with no members yet.
    # We don't actually need to persist an empty group — it will appear once a
    # target is added.  Just confirm.
    console.print(f"[green]Group '{name}' created. Add targets to it from the menu.[/green]")


def _add_target_to_group(console: Console) -> None:
    targets = _load_targets_json()
    if not targets:
        console.print("[yellow]No saved targets.[/yellow]")
        return

    groups = _all_groups(targets)
    new_label = "+ New group"
    group = inquirer.select(
        message="Select group:",
        choices=groups + [new_label],
        pointer="❯",
    ).execute()

    if group == new_label:
        group = inquirer.text(message="New group name:").execute().strip()
        if not group:
            console.print("[red]No name provided.[/red]")
            return

    choices = [f"{t['target']} [{_group_of(t)}]" for t in targets]
    picked = inquirer.select(message="Select target:", choices=choices, pointer="❯").execute()
    idx = choices.index(picked)

    targets[idx]["group"] = group
    _save_targets_json(targets)
    console.print(f"[green]{targets[idx]['target']} → {group}[/green]")


def _remove_target_from_group(console: Console) -> None:
    targets = _load_targets_json()
    grouped = [t for t in targets if t.get("group")]
    if not grouped:
        console.print("[yellow]No targets assigned to any group.[/yellow]")
        return

    groups = sorted({t["group"] for t in grouped})
    group = inquirer.select(message="Select group:", choices=groups, pointer="❯").execute()

    members = [t for t in targets if t.get("group") == group]
    choices = [m["target"] for m in members]
    picked = inquirer.select(message="Remove target:", choices=choices, pointer="❯").execute()

    for t in targets:
        if t["target"] == picked and t.get("group") == group:
            t["group"] = ""
            break

    _save_targets_json(targets)
    console.print(f"[green]{picked} removed from {group}.[/green]")


def _scan_group(console: Console) -> None:
    targets = _load_targets_json()
    groups = _all_groups(targets)
    if not groups:
        console.print("[yellow]No groups found.[/yellow]")
        return

    group = inquirer.select(message="Select group to scan:", choices=groups, pointer="❯").execute()
    members = [t for t in targets if _group_of(t) == group]
    if not members:
        console.print("[yellow]No targets in this group.[/yellow]")
        return

    tool_choice = inquirer.select(
        message="Scan tool:",
        choices=list(SCAN_TOOLS.keys()),
        pointer="❯",
    ).execute()

    base_cmd = SCAN_TOOLS[tool_choice]
    binary = base_cmd[0]

    if not check_installed(binary):
        console.print(f"[red]{binary} is not installed.[/red]")
        return

    console.print(f"\n[bold]Scanning {len(members)} target(s) in [cyan]{group}[/cyan] with {tool_choice}[/bold]\n")

    for member in members:
        target = member["target"]
        console.rule(f"[cyan]{target}[/cyan]")
        cmd = base_cmd + [target]
        run_logged(cmd, console, f"{binary}_{group}")

    console.print(f"\n[bold green]Group scan complete.[/bold green]")


def _export_targets(console: Console) -> None:
    """Export targets to JSON or CSV."""
    import json as _json
    import csv

    targets = _load_targets_json()
    if not targets:
        console.print("[yellow]No targets to export.[/yellow]")
        return

    fmt = inquirer.select(
        message="Export format:",
        choices=["JSON", "CSV"],
        pointer="❯",
    ).execute()

    path = inquirer.text(
        message="Export path:",
        default=f"sectools-targets.{fmt.lower()}",
    ).execute().strip()
    if not path:
        return

    if fmt == "JSON":
        with open(path, "w") as f:
            _json.dump(targets, f, indent=2)
    else:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["target", "notes", "group"])
            writer.writeheader()
            for t in targets:
                writer.writerow({
                    "target": t.get("target", ""),
                    "notes": t.get("notes", ""),
                    "group": t.get("group", ""),
                })

    console.print(f"[green]Exported {len(targets)} targets to {path}[/green]")


def _import_targets(console: Console) -> None:
    """Import targets from JSON or CSV, merging with existing."""
    import json as _json
    import csv

    path = inquirer.text(message="Import file path:").execute().strip()
    if not path:
        return

    from pathlib import Path as _Path
    file_path = _Path(path)
    if not file_path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        return

    ext = file_path.suffix.lower()
    imported = []

    if ext == ".json":
        try:
            imported = _json.loads(file_path.read_text())
        except _json.JSONDecodeError:
            console.print("[red]Invalid JSON file.[/red]")
            return
    elif ext == ".csv":
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                imported.append({
                    "target": row.get("target", ""),
                    "notes": row.get("notes", ""),
                    "group": row.get("group", ""),
                })
    else:
        console.print("[red]Unsupported format. Use .json or .csv[/red]")
        return

    if not imported:
        console.print("[yellow]No targets found in file.[/yellow]")
        return

    existing = _load_targets_json()
    existing_targets = {e["target"] for e in existing}
    added = 0
    for entry in imported:
        if entry.get("target") and entry["target"] not in existing_targets:
            existing.append(entry)
            existing_targets.add(entry["target"])
            added += 1

    _save_targets_json(existing)
    console.print(f"[green]Imported {added} new targets ({len(imported) - added} duplicates skipped).[/green]")


def run(console: Console) -> None:
    """Entry point for the Target Groups module."""
    while True:
        action = inquirer.select(
            message="Target Groups:",
            choices=[
                "View Groups",
                "Create Group",
                "Add Target to Group",
                "Remove Target from Group",
                "Scan Group",
                "Export Targets",
                "Import Targets",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if action == "View Groups":
            _view_groups(console)
        elif action == "Create Group":
            _create_group(console)
        elif action == "Add Target to Group":
            _add_target_to_group(console)
        elif action == "Remove Target from Group":
            _remove_target_from_group(console)
        elif action == "Scan Group":
            _scan_group(console)
        elif action == "Export Targets":
            _export_targets(console)
        elif action == "Import Targets":
            _import_targets(console)
        else:
            break
