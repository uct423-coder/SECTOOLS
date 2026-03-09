import importlib.util
from pathlib import Path
from rich.console import Console
from InquirerPy import inquirer

PLUGINS_DIR = Path.home() / ".sectools-plugins"


def discover_plugins() -> list[dict]:
    """Find valid plugins in the plugins directory."""
    if not PLUGINS_DIR.exists():
        return []

    plugins = []
    for f in sorted(PLUGINS_DIR.glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "PLUGIN_NAME") and hasattr(mod, "run"):
                plugins.append({"name": mod.PLUGIN_NAME, "run": mod.run, "path": f})
        except Exception:
            continue
    return plugins


def plugins_menu(console: Console):
    """Show installed plugins and let user run one."""
    plugins = discover_plugins()
    if not plugins:
        console.print(f"[yellow]No plugins found. Drop .py files in {PLUGINS_DIR}[/yellow]")
        PLUGINS_DIR.mkdir(exist_ok=True)
        return

    choices = [p["name"] for p in plugins] + ["Back"]
    choice = inquirer.select(message="Select plugin:", choices=choices, pointer="❯").execute()
    if choice == "Back":
        return

    plugin = next(p for p in plugins if p["name"] == choice)
    try:
        plugin["run"](console)
    except Exception as e:
        console.print(f"[red]Plugin error: {e}[/red]")


def get_plugin_menu_items() -> list[str]:
    """Return menu item strings for discovered plugins."""
    plugins = discover_plugins()
    return [f"Plugin: {p['name']}" for p in plugins]
