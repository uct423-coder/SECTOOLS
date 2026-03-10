import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import extract_hostname, run_logged, ask_target

PRESETS = {
    "Fast Scan (-F)": ["-F"],
    "Quick Scan (-sV --top-ports 100)": ["-sV", "--top-ports", "100"],
    "Full Port Scan (-sV -p-)": ["-sV", "-p-"],
    "Vuln Scan (--script vuln)": ["--script", "vuln"],
    "OS Detection (-O -sV)": ["-O", "-sV"],
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]Nmap[/bold cyan]")

    target = ask_target(console, "Target (IP/hostname):")
    if not target:
        return

    hostname, was_url = extract_hostname(target)
    if was_url:
        console.print(f"[yellow]Extracted hostname: {hostname}[/yellow]")

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "nmap")
        return

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter nmap flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    cmd = ["nmap"] + flags + [hostname]
    run_logged(cmd, console, "nmap")
