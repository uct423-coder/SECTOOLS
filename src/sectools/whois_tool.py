from rich.console import Console
from sectools.utils import run_logged, ask_target


def run(console: Console):
    console.rule("[bold cyan]Whois — Domain Lookup[/bold cyan]", style="cyan")
    console.print()

    target = ask_target(console, "Domain or IP:")
    if not target:
        return

    cmd = ["whois", target]
    run_logged(cmd, console, "whois")
