import subprocess
from InquirerPy import inquirer
from rich.console import Console

GUIDED_WORKFLOWS = {
    "Port scan (auxiliary/scanner/portscan/tcp)": {
        "module": "auxiliary/scanner/portscan/tcp",
        "options": [
            {"name": "RHOSTS", "prompt": "Target host(s) (RHOSTS):", "required": True},
            {"name": "THREADS", "prompt": "Threads (default 10):", "default": "10"},
        ],
    },
    "SMB enumeration (auxiliary/scanner/smb/smb_version)": {
        "module": "auxiliary/scanner/smb/smb_version",
        "options": [
            {"name": "RHOSTS", "prompt": "Target host(s) (RHOSTS):", "required": True},
        ],
    },
    "HTTP directory scanner (auxiliary/scanner/http/dir_scanner)": {
        "module": "auxiliary/scanner/http/dir_scanner",
        "options": [
            {"name": "RHOSTS", "prompt": "Target host(s) (RHOSTS):", "required": True},
        ],
    },
    "HTTP version scanner (auxiliary/scanner/http/http_version)": {
        "module": "auxiliary/scanner/http/http_version",
        "options": [
            {"name": "RHOSTS", "prompt": "Target host(s) (RHOSTS):", "required": True},
        ],
    },
    "Reverse shell handler (exploit/multi/handler)": {
        "module": "exploit/multi/handler",
        "options": [
            {"name": "payload", "prompt": "Payload (e.g. windows/meterpreter/reverse_tcp):", "required": True, "is_payload": True},
            {"name": "LHOST", "prompt": "Your IP (LHOST):", "required": True},
            {"name": "LPORT", "prompt": "Listen port (LPORT, default 4444):", "default": "4444"},
        ],
    },
    "Launch msfconsole (interactive)": None,
    "Custom module": "custom",
}


def _run_guided(console: Console, workflow: dict):
    """Run a guided workflow by prompting for options and building the command."""
    module = workflow["module"]
    cmds = [f"use {module}"]

    for opt in workflow["options"]:
        default = opt.get("default", "")
        value = inquirer.text(message=opt["prompt"], default=default).execute().strip()
        if not value and opt.get("required"):
            console.print(f"[red]{opt['name']} is required.[/red]")
            return
        if value:
            if opt.get("is_payload"):
                cmds.append(f"set payload {value}")
            else:
                cmds.append(f"set {opt['name']} {value}")

    cmds.append("run")
    cmd_str = "; ".join(cmds)
    console.print(f"\n[dim]Running: msfconsole -q -x \"{cmd_str}\"[/dim]\n")
    subprocess.run(["msfconsole", "-q", "-x", cmd_str])


def run(console: Console):
    console.rule("[bold cyan]Metasploit[/bold cyan]")

    action = inquirer.select(
        message="Action:",
        choices=list(GUIDED_WORKFLOWS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if action == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "metasploit")
        return

    val = GUIDED_WORKFLOWS[action]

    if val is None:
        console.print("[dim]Launching msfconsole… (type 'exit' to return)[/dim]\n")
        subprocess.run(["msfconsole"])
    elif val == "custom":
        module = inquirer.text(message="Module path (e.g. exploit/multi/handler):").execute()
        if not module.strip():
            console.print("[red]No module provided.[/red]")
            return
        options = inquirer.text(message="Options (e.g. RHOSTS=10.0.0.1 LHOST=10.0.0.2):").execute()

        rc_lines = [f"use {module.strip()}"]
        for opt in options.split():
            if "=" in opt:
                rc_lines.append(f"set {opt.replace('=', ' ')}")
        rc_lines.append("run")

        cmd_str = "; ".join(rc_lines)
        console.print(f"\n[dim]Running: msfconsole -q -x \"{cmd_str}\"[/dim]\n")
        subprocess.run(["msfconsole", "-q", "-x", cmd_str])
    else:
        _run_guided(console, val)
