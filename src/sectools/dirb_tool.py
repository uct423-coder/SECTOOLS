import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.theme import bold, rule_style
from sectools.utils import run_logged, pick_wordlist, WORDLISTS_DIR, ask_target
from sectools.config import load_config

PRESETS = {
    "Standard scan": [],
    "Non-recursive (-r)": ["-r"],
    "Show NOT_FOUND pages (-f)": ["-f"],
    "Case insensitive (-i)": ["-i"],
    "With extensions (-X .php,.html,.txt)": ["-X", ".php,.html,.txt"],
    "Custom flags": None,
}


def run(console: Console):
    console.rule(bold("Dirb — URL Brute Forcer"), style=rule_style())
    console.print()

    target = ask_target(console, "Target URL:")
    if not target:
        return

    config = load_config()
    wordlist = pick_wordlist("Wordlist:", config.get("default_dirwordlist", str(WORDLISTS_DIR / "common.txt")))
    if not wordlist:
        return

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()),
        pointer="❯",
    ).execute()

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter dirb flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    cmd = ["dirb", target, wordlist] + flags
    run_logged(cmd, console, "dirb")
