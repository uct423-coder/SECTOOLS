"""Onboarding Wizard — first-run setup for new users."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from InquirerPy import inquirer

from sectools.config import CONFIG_PATH, DEFAULT_CONFIG, THEME_CHOICES, save_config

TOTAL_STEPS = 4


def needs_onboarding() -> bool:
    """Return True if this is the first run (no config file)."""
    return not CONFIG_PATH.exists()


def _step_header(console: Console, step: int, title: str):
    """Print a styled step indicator."""
    bar = "━" * 40
    filled = int(bar.__len__() * step / TOTAL_STEPS)
    progress_bar = f"[bold cyan]{'━' * filled}[/bold cyan][dim]{'━' * (len(bar) - filled)}[/dim]"
    console.print()
    console.print(f"  {progress_bar}  [bold]Step {step} of {TOTAL_STEPS}[/bold]")
    console.print(f"  [bold bright_white]{title}[/bold bright_white]\n")


def run_onboarding(console: Console):
    """Interactive first-run setup wizard."""
    from sectools.dashboard import BANNER
    console.print(BANNER)
    console.print()
    welcome = Text(justify="center")
    welcome.append("\n", style="bold")
    welcome.append("Welcome to SecTools!\n", style="bold bright_white on blue")
    welcome.append("\n", style="bold")
    welcome.append("Your all-in-one security toolkit.\n", style="bold cyan")
    welcome.append("Let's get you set up in 4 quick steps.\n\n", style="dim")
    welcome.append("━" * 44 + "\n", style="cyan")
    console.print(Panel(
        welcome,
        border_style="bright_cyan",
        padding=(1, 6),
        title="[bold bright_white] Setup Wizard [/bold bright_white]",
        subtitle="[dim]Powered by SecTools[/dim]",
    ))

    config = dict(DEFAULT_CONFIG)

    # 1. Theme
    _step_header(console, 1, "Choose Your Theme")
    config["theme_color"] = inquirer.select(
        message="Pick a theme color:",
        choices=THEME_CHOICES,
        default="cyan",
        pointer="❯",
    ).execute()

    # 2. Notifications
    _step_header(console, 2, "Notification Preferences")
    config["notifications_enabled"] = inquirer.confirm(
        message="Enable desktop notifications?",
        default=True,
    ).execute()

    # 3. Log retention
    _step_header(console, 3, "Log Management")
    retention = inquirer.number(
        message="Auto-delete logs older than (days):",
        default=30,
        min_allowed=1,
    ).execute()
    config["log_retention_days"] = int(retention)

    # 4. Scope
    _step_header(console, 4, "Engagement Scope")
    setup_scope = inquirer.confirm(
        message="Define an engagement scope now?",
        default=False,
    ).execute()

    save_config(config)

    # Auto-download essential wordlists
    console.print()
    console.print(Panel(
        "[bold cyan]Downloading essential wordlists...[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))
    from sectools.wordlist_mgr import ensure_wordlists
    ensure_wordlists(console)

    # Auto-install missing tools
    console.print()
    console.print(Panel(
        "[bold cyan]Checking for missing tools...[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))
    from sectools.auto_installer import run as auto_install
    auto_install(console)

    if setup_scope:
        from sectools.scope import run as scope_menu
        scope_menu(console)

    done = Text(justify="center")
    done.append("\n✔ Setup complete!\n\n", style="bold green")
    done.append("You can change these anytime in Settings.\n", style="dim")
    done.append("Happy hacking!\n", style="bold cyan")
    console.print(Panel(
        done,
        border_style="bright_green",
        padding=(1, 4),
        title="[bold bright_white] All Done [/bold bright_white]",
    ))
    console.print()
