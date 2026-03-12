import json
import os
from pathlib import Path
from typing import Any
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

CONFIG_PATH = Path.home() / ".sectools-config.json"


def _get_accent() -> str:
    """Lazy import to avoid circular dependency with theme module."""
    from sectools.theme import accent
    return accent()

DEFAULT_CONFIG = {
    "default_wordlist": str(Path.home() / ".sectools-wordlists" / "default-passwords.txt"),
    "default_dirwordlist": str(Path.home() / ".sectools-wordlists" / "common.txt"),
    "notifications_enabled": True,
    "theme_color": "cyan",
    "log_retention_days": 30,
    "auto_save_targets": False,
    "favorites": [],
    "strict_scope": False,
}

THEME_CHOICES = ["cyan", "green", "red", "blue", "magenta"]


def _migrate_config(config: dict) -> bool:
    """Fix stale wordlist paths from old onboarding. Returns True if changed."""
    changed = False
    wordlists_dir = str(Path.home() / ".sectools-wordlists")
    for key in ("default_wordlist", "default_dirwordlist"):
        val = config.get(key, "")
        if not val:
            continue
        bare = "/" not in val and "\\" not in val
        stale = "/usr/share/wordlists/" in val
        if bare or stale:
            default_name = "default-passwords.txt" if key == "default_wordlist" else "common.txt"
            config[key] = str(Path(wordlists_dir) / default_name)
            changed = True
    return changed


def load_config() -> dict[str, Any]:
    """Load config from file, filling in defaults for any missing keys."""
    from sectools.schema import SecToolsConfig
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    if _migrate_config(config):
        save_config(config)
    # Validate with pydantic (graceful fallback)
    try:
        validated = SecToolsConfig(**config)
        config.update(validated.model_dump())
    except Exception:
        pass
    return config


def save_config(config: dict[str, Any]) -> None:
    """Write config dict to the config file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def config_menu(console: Console):
    """Interactive menu for viewing and editing settings."""
    config = load_config()

    SETTING_ICONS = {
        "default_wordlist": "📄",
        "default_dirwordlist": "📂",
        "notifications_enabled": "🔔",
        "theme_color": "🎨",
        "log_retention_days": "📅",
        "auto_save_targets": "💾",
        "favorites": "⭐",
    }

    while True:
        # Display current settings
        table = Table(
            title="[bold]Settings[/bold]",
            border_style=_get_accent(),
            show_lines=True,
            header_style="bold bright_white on grey23",
            row_styles=["", "on grey11"],
            padding=(0, 1),
        )
        table.add_column("", width=3, justify="center")
        table.add_column("Setting", style="cyan bold")
        table.add_column("Value", style="bold")
        for key, value in config.items():
            icon = SETTING_ICONS.get(key, "⚙️")
            display = str(value)
            if isinstance(value, bool):
                display = "[green]✔ on[/green]" if value else "[red]✘ off[/red]"
            elif isinstance(value, int):
                display = f"[yellow]{value}[/yellow]"
            elif isinstance(value, list):
                display = f"[dim]{len(value)} items[/dim]" if value else "[dim]empty[/dim]"
            table.add_row(icon, key, display)
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
