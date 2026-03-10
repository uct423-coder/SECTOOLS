import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

CONFIG_PATH = Path.home() / ".sectools-config.json"

DEFAULT_CONFIG = {
    "default_wordlist": str(Path.home() / ".sectools-wordlists" / "default-passwords.txt"),
    "default_dirwordlist": str(Path.home() / ".sectools-wordlists" / "common.txt"),
    "notifications_enabled": True,
    "theme_color": "cyan",
    "log_retention_days": 30,
    "auto_save_targets": False,
    "favorites": [],
}

THEME_CHOICES = ["cyan", "green", "red", "blue", "magenta"]


def load_config() -> dict:
    """Load config from file, filling in defaults for any missing keys."""
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    return config


def save_config(config: dict):
    """Write config dict to the config file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def config_menu(console: Console):
    """Interactive menu for viewing and editing settings."""
    config = load_config()

    while True:
        # Display current settings
        table = Table(title="⚙️  Configuration", border_style="dim", show_lines=False)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="bold")
        for key, value in config.items():
            display = str(value)
            if isinstance(value, bool):
                display = "[green]✔ on[/green]" if value else "[red]✘ off[/red]"
            table.add_row(key, display)
        console.print(table)

        choices = list(config.keys()) + ["Save & Back"]
        choice = inquirer.select(
            message="Edit a setting (or save & exit):",
            choices=choices,
            pointer="❯",
        ).execute()

        if choice == "Save & Back":
            save_config(config)
            console.print("[green]✔ Configuration saved.[/green]")
            return

        # Edit the chosen setting
        current = config[choice]

        if choice == "theme_color":
            config[choice] = inquirer.select(
                message="Select theme color:",
                choices=THEME_CHOICES,
                default=current,
                pointer="❯",
            ).execute()

        elif isinstance(current, bool):
            config[choice] = inquirer.confirm(
                message=f"{choice}:",
                default=current,
            ).execute()

        elif isinstance(current, int):
            value = inquirer.number(
                message=f"{choice}:",
                default=current,
                min_allowed=1,
            ).execute()
            config[choice] = int(value)

        else:
            config[choice] = inquirer.text(
                message=f"{choice}:",
                default=str(current),
            ).execute()
