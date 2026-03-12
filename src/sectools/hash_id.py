"""Hash Identifier — detect hash type from a pasted string."""

import re

from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table
from sectools.theme import bold, rule_style


HASH_TYPES = [
    # (name, test_func, hashcat_mode, john_format)
    ("bcrypt", lambda h: bool(re.match(r'^\$2[aby]\$\d{2}\$.{53}$', h)), 3200, "bcrypt"),
    ("MD5 crypt", lambda h: bool(re.match(r'^\$1\$.{0,8}\$[./A-Za-z0-9]{22}$', h)), 500, "md5crypt"),
    ("SHA-256 crypt", lambda h: bool(re.match(r'^\$5\$.{0,16}\$[./A-Za-z0-9]{43}$', h)), 7400, "sha256crypt"),
    ("SHA-512 crypt", lambda h: bool(re.match(r'^\$6\$.{0,16}\$[./A-Za-z0-9]{86}$', h)), 1800, "sha512crypt"),
    ("MySQL 5.x", lambda h: bool(re.match(r'^\*[A-Fa-f0-9]{40}$', h)), 300, "mysql-sha1"),
    ("CRC32", lambda h: bool(re.match(r'^[A-Fa-f0-9]{8}$', h)) and len(h) == 8, 11500, "crc32"),
    ("MySQL 4.x", lambda h: bool(re.match(r'^[A-Fa-f0-9]{16}$', h)) and len(h) == 16, 200, "mysql"),
    ("MD5", lambda h: bool(re.match(r'^[A-Fa-f0-9]{32}$', h)), 0, "raw-md5"),
    ("NTLM", lambda h: bool(re.match(r'^[A-Fa-f0-9]{32}$', h)), 1000, "nt"),
    ("SHA-1", lambda h: bool(re.match(r'^[A-Fa-f0-9]{40}$', h)), 100, "raw-sha1"),
    ("SHA-256", lambda h: bool(re.match(r'^[A-Fa-f0-9]{64}$', h)), 1400, "raw-sha256"),
    ("SHA-512", lambda h: bool(re.match(r'^[A-Fa-f0-9]{128}$', h)), 1700, "raw-sha512"),
]


def run(console: Console) -> None:
    """Identify a hash type from user input."""
    console.rule(bold("Hash Identifier"), style=rule_style())
    console.print()

    hash_str = inquirer.text(message="Paste the hash string:").execute()
    if not hash_str:
        console.print("[red]No input provided.[/red]")
        return

    hash_str = hash_str.strip()
    matches = []
    for name, test, hc_mode, john_fmt in HASH_TYPES:
        if test(hash_str):
            matches.append((name, str(hc_mode), john_fmt))

    _show_matches(console, hash_str, matches)


def identify_hash(console: Console, hash_str: str) -> None:
    """Identify a hash type from a string (for CLI use)."""
    hash_str = hash_str.strip()
    matches = []
    for name, test, hc_mode, john_fmt in HASH_TYPES:
        if test(hash_str):
            matches.append((name, str(hc_mode), john_fmt))
    _show_matches(console, hash_str, matches)


def _show_matches(console: Console, hash_str: str, matches: list) -> None:
    if not matches:
        console.print(f"[yellow]No known hash type matched for:[/yellow] {hash_str}")
        return

    table = Table(title="Possible Hash Types")
    table.add_column("Hash Type", style="green")
    table.add_column("Hashcat Mode", style="cyan")
    table.add_column("John Format", style="magenta")

    for name, hc, jf in matches:
        table.add_row(name, hc, jf)

    console.print(table)
