"""Onboarding Wizard — first-run setup for new users."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from InquirerPy import inquirer

from sectools.config import CONFIG_PATH, DEFAULT_CONFIG, THEME_CHOICES, save_config


def needs_onboarding() -> bool:
    """Return True if this is the first run (no config file)."""
    return not CONFIG_PATH.exists()


def run_onboarding(console: Console):
    """Interactive first-run setup wizard."""
    from sectools.dashboard import BANNER
    console.print(BANNER)
    console.print()
    welcome = Text(justify="center")
    welcome.append("Welcome to SecTools!\n\n", style="bold white")
    welcome.append("Let's set up your toolkit in a few quick steps.", style="dim")
    console.print(Panel(welcome, border_style="cyan", padding=(1, 4)))

    config = dict(DEFAULT_CONFIG)

    # 1. Theme
    config["theme_color"] = inquirer.select(
        message="Pick a theme color:",
        choices=THEME_CHOICES,
        default="cyan",
        pointer="❯",
    ).execute()

    # 2. Password wordlist
    config["default_wordlist"] = inquirer.text(
        message="Password wordlist path:",
        default=config["default_wordlist"],
    ).execute().strip()

    # 3. Directory wordlist
    config["default_dirwordlist"] = inquirer.text(
        message="Directory wordlist path (for Gobuster):",
        default=config["default_dirwordlist"],
    ).execute().strip()

    # 4. Notifications
    config["notifications_enabled"] = inquirer.confirm(
        message="Enable desktop notifications?",
        default=True,
    ).execute()

    # 5. Log retention
    retention = inquirer.number(
        message="Auto-delete logs older than (days):",
        default=30,
        min_allowed=1,
    ).execute()
    config["log_retention_days"] = int(retention)

    # 6. Scope
    setup_scope = inquirer.confirm(
        message="Define an engagement scope now?",
        default=False,
    ).execute()

    save_config(config)

    # Auto-download essential wordlists
    console.print("\n[bold cyan]Downloading essential wordlists...[/bold cyan]")
    from sectools.wordlist_mgr import ensure_wordlists
    ensure_wordlists(console)

    if setup_scope:
        from sectools.scope import run as scope_menu
        scope_menu(console)

    done = Text(justify="center")
    done.append("✔ Setup complete!\n\n", style="bold green")
    done.append("You can change these anytime in ⚙️  Settings.", style="dim")
    console.print(Panel(done, border_style="green", padding=(1, 4)))
    console.print()
