import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.theme import bold, rule_style
from sectools.utils import run_logged, ask_target

DNS_CHOICES = [
    "DNS Lookup (dig)",
    "Reverse DNS",
    "Zone Transfer",
    "MX Records",
    "NS Records",
    "TXT Records",
    "Any Records",
    "Back",
]


def run(console: Console):
    console.rule(bold("DNS Toolkit"), style=rule_style())
    console.print()

    choice = inquirer.select(
        message="Select DNS operation:",
        choices=DNS_CHOICES,
        pointer="❯",
    ).execute()

    if choice == "Back":
        return

    if choice == "Reverse DNS":
        target = ask_target(console, "IP address:")
    else:
        target = ask_target(console, "Domain:")

    if not target:
        return

    if choice == "DNS Lookup (dig)":
        cmd = ["dig", target]
    elif choice == "Reverse DNS":
        cmd = ["dig", "-x", target]
    elif choice == "Zone Transfer":
        ns = ask_target(console, "Nameserver (optional, leave blank to skip):")
        if ns:
            cmd = ["dig", "axfr", target, f"@{ns}"]
        else:
            cmd = ["dig", "axfr", target]
    elif choice == "MX Records":
        cmd = ["dig", target, "MX"]
    elif choice == "NS Records":
        cmd = ["dig", target, "NS"]
    elif choice == "TXT Records":
        cmd = ["dig", target, "TXT"]
    elif choice == "Any Records":
        cmd = ["dig", target, "ANY"]
    else:
        return

    run_logged(cmd, console, "dig")
