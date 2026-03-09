"""Password Generator — cryptographically secure passwords with strength estimate."""

import math
import secrets
import string

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def _estimate_strength(length: int, pool_size: int) -> str:
    entropy = length * math.log2(pool_size) if pool_size > 0 else 0
    if entropy >= 128:
        return f"[bold green]Very Strong[/bold green] ({entropy:.0f} bits)"
    if entropy >= 80:
        return f"[green]Strong[/green] ({entropy:.0f} bits)"
    if entropy >= 60:
        return f"[yellow]Moderate[/yellow] ({entropy:.0f} bits)"
    if entropy >= 40:
        return f"[red]Weak[/red] ({entropy:.0f} bits)"
    return f"[bold red]Very Weak[/bold red] ({entropy:.0f} bits)"


def run(console: Console) -> None:
    """Generate secure random passwords."""
    console.print("\n[bold cyan]Password Generator[/bold cyan]\n")

    length = int(inquirer.text(message="Password length:", default="16").execute())
    count = int(inquirer.text(message="How many passwords:", default="5").execute())

    use_upper = inquirer.confirm(message="Include uppercase?", default=True).execute()
    use_lower = inquirer.confirm(message="Include lowercase?", default=True).execute()
    use_digits = inquirer.confirm(message="Include digits?", default=True).execute()
    use_special = inquirer.confirm(message="Include special chars?", default=True).execute()

    pool = ""
    if use_upper:
        pool += string.ascii_uppercase
    if use_lower:
        pool += string.ascii_lowercase
    if use_digits:
        pool += string.digits
    if use_special:
        pool += string.punctuation

    if not pool:
        console.print("[red]No character sets selected.[/red]")
        return

    passwords = ["".join(secrets.choice(pool) for _ in range(length)) for _ in range(count)]
    strength = _estimate_strength(length, len(pool))

    table = Table(title="Generated Passwords")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Password", style="green")

    for i, pw in enumerate(passwords, 1):
        table.add_row(str(i), pw)

    console.print(table)
    console.print(f"\nCharacter pool size: {len(pool)}  |  Strength: {strength}")
