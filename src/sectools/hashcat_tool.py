import subprocess
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged

HASH_TYPES = {
    "MD5 (0)": "0",
    "SHA-1 (100)": "100",
    "SHA-256 (1400)": "1400",
    "NTLM (1000)": "1000",
    "bcrypt (3200)": "3200",
    "WPA/WPA2 (22000)": "22000",
    "Custom hash type": None,
}

ATTACK_MODES = {
    "Dictionary (0)": "0",
    "Combination (1)": "1",
    "Brute-force / Mask (3)": "3",
    "Rule-based (0 + rules)": "0r",
}


def run(console: Console):
    console.rule("[bold cyan]Hashcat — GPU Password Cracker[/bold cyan]")

    hashfile = inquirer.text(message="Hash file path:").execute().strip()
    if not hashfile:
        console.print("[red]No hash file provided.[/red]")
        return

    hash_choice = inquirer.select(
        message="Hash type:",
        choices=list(HASH_TYPES.keys()),
        pointer="❯",
    ).execute()

    hash_type = HASH_TYPES[hash_choice]
    if hash_type is None:
        hash_type = inquirer.text(message="Hash type number (see hashcat --help):").execute().strip()

    attack = inquirer.select(
        message="Attack mode:",
        choices=list(ATTACK_MODES.keys()),
        pointer="❯",
    ).execute()
    attack_mode = ATTACK_MODES[attack]

    cmd = ["hashcat", "-m", hash_type]

    if attack_mode == "0r":
        wordlist = inquirer.text(message="Wordlist path:").execute().strip()
        rules = inquirer.text(message="Rules file:", default="/opt/homebrew/share/hashcat/rules/best64.rule").execute().strip()
        cmd += ["-a", "0", "-r", rules, hashfile, wordlist]
    elif attack_mode == "3":
        mask = inquirer.text(message="Mask (e.g. ?a?a?a?a?a?a):", default="?a?a?a?a?a?a").execute().strip()
        cmd += ["-a", "3", hashfile, mask]
    else:
        wordlist = inquirer.text(message="Wordlist path:").execute().strip()
        cmd += ["-a", attack_mode, hashfile, wordlist]

    run_logged(cmd, console, "hashcat")
