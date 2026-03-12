"""Plugin system — discover, validate, and run plugins."""

import importlib
import importlib.util
from pathlib import Path
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer
from sectools.theme import primary

from sectools.builtin_plugins._base import validate_plugin, PLUGIN_API_VERSION

PLUGINS_DIR = Path.home() / ".sectools-plugins"

# Built-in plugin module names
_BUILTIN_MODULES = [
    "whois_lookup",
    "dns_resolver",
    "ping_sweep",
    "mac_lookup",
    "jwt_decoder",
    "ssl_checker",
    "dirlist_checker",
    "tech_detect",
]


def _load_builtin_plugins() -> list[dict]:
    """Load built-in plugins from the builtin_plugins package."""
    plugins = []
    for name in _BUILTIN_MODULES:
        try:
            mod = importlib.import_module(f"sectools.builtin_plugins.{name}")
            valid, err = validate_plugin(mod)
            if valid:
                plugins.append({
                    "name": mod.PLUGIN_NAME,
                    "run": mod.run,
                    "version": getattr(mod, "PLUGIN_VERSION", "0.0"),
                    "api_version": getattr(mod, "PLUGIN_API_VERSION", "0.0"),
                    "builtin": True,
                    "path": None,
                })
        except Exception:
            continue
    return plugins


def _load_user_plugins() -> list[dict]:
    """Find valid user plugins in the plugins directory."""
    if not PLUGINS_DIR.exists():
        return []

    plugins = []
    for f in sorted(PLUGINS_DIR.glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            valid, err = validate_plugin(mod)
            if valid:
                plugins.append({
                    "name": mod.PLUGIN_NAME,
                    "run": mod.run,
                    "version": getattr(mod, "PLUGIN_VERSION", "0.0"),
                    "api_version": getattr(mod, "PLUGIN_API_VERSION", "0.0"),
                    "builtin": False,
                    "path": f,
                })
        except Exception:
            continue
    return plugins


def discover_plugins() -> list[dict]:
    """Find all valid plugins (built-in + user)."""
    return _load_builtin_plugins() + _load_user_plugins()


def _uninstall_plugin(console: Console):
    """Uninstall a user-installed plugin."""
    user_plugins = _load_user_plugins()
    if not user_plugins:
        console.print("[yellow]No user plugins installed.[/yellow]")
        return
    choices = [p["name"] for p in user_plugins] + ["Back"]
    choice = inquirer.select(message="Uninstall which plugin?", choices=choices, pointer="❯").execute()
    if choice == "Back":
        return
    plugin = next(p for p in user_plugins if p["name"] == choice)
    if plugin["path"]:
        plugin["path"].unlink()
    console.print(f"[green]Uninstalled {choice}.[/green]")


def plugins_menu(console: Console):
    """Plugin hub — run, list, or uninstall plugins."""
    PLUGINS_DIR.mkdir(exist_ok=True)

    while True:
        choice = inquirer.select(
            message="Plugins:",
            choices=[
                "Run a Plugin",
                "List All Plugins",
                "Uninstall User Plugin",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if choice == "Back":
            return

        elif choice == "Run a Plugin":
            plugins = discover_plugins()
            if not plugins:
                console.print("[yellow]No plugins available.[/yellow]")
                continue
            names = [p["name"] for p in plugins] + ["Back"]
            pick = inquirer.select(message="Select plugin:", choices=names, pointer="❯").execute()
            if pick == "Back":
                continue
            plugin = next(p for p in plugins if p["name"] == pick)
            try:
                plugin["run"](console)
            except Exception as e:
                console.print(f"[red]Plugin error: {e}[/red]")

        elif choice == "List All Plugins":
            plugins = discover_plugins()
            if not plugins:
                console.print("[yellow]No plugins available.[/yellow]")
                continue
            table = Table(title="Plugins", border_style=primary())
            table.add_column("#", style="cyan", width=3)
            table.add_column("Plugin", style="bold")
            table.add_column("Version")
            table.add_column("Type")
            for i, p in enumerate(plugins, 1):
                ptype = "[dim]Built-in[/dim]" if p["builtin"] else "[green]User[/green]"
                table.add_row(str(i), p["name"], p["version"], ptype)
            console.print(table)

        elif choice == "Uninstall User Plugin":
            _uninstall_plugin(console)

        console.print()


def get_plugin_menu_items() -> list[str]:
    """Return menu item strings for discovered plugins."""
    plugins = discover_plugins()
    return [f"Plugin: {p['name']}" for p in plugins]
