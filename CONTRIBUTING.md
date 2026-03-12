# Contributing to SecTools

## Development Setup

```bash
git clone <repo-url>
cd CLI
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Tool Interface Pattern

Each tool module follows one of two patterns:

### BaseTool (preferred for new tools)

```python
from sectools.base_tool import BaseTool
from rich.console import Console

class MyTool(BaseTool):
    name = "My Tool — Description"
    binary = "mytool"
    target_prompt = "Target:"

    def _build_command(self, console: Console, target: str) -> list[str]:
        return ["mytool", target]

_tool = MyTool()
run = _tool.run
```

### Legacy function-based

```python
from rich.console import Console
from sectools.utils import run_logged, ask_target

def run(console: Console):
    target = ask_target(console, "Target:")
    if not target:
        return
    cmd = ["mytool", target]
    run_logged(cmd, console, "mytool")
```

## Plugin Interface

Plugins live in `src/sectools/builtin_plugins/` or `~/.sectools-plugins/`.

Required attributes:
- `PLUGIN_NAME: str` — display name
- `PLUGIN_VERSION: str` — semver string
- `PLUGIN_API_VERSION: str` — must be "1.0"
- `run(console: Console)` — entry point

## Registering a Tool in main.py

1. Import your tool module in `main.py`
2. Add it to the appropriate category in `CATEGORIES`
3. Add a keyboard shortcut in `SHORTCUTS` if desired

## Theme / Styling

Use `sectools.theme` for brand colors:
```python
from sectools.theme import bold, rule_style
console.rule(bold("My Tool"), style=rule_style())
```

Do NOT hardcode `[bold cyan]` — use the theme system so colors respect user settings.
