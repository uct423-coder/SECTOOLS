"""Centralized theme and styling for SecTools."""

from sectools.config import load_config

# Semantic role → color mapping per theme
_THEMES = {
    "cyan": {
        "primary": "cyan",
        "accent": "bright_cyan",
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "muted": "dim",
    },
    "green": {
        "primary": "green",
        "accent": "bright_green",
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "muted": "dim",
    },
    "red": {
        "primary": "red",
        "accent": "bright_red",
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "muted": "dim",
    },
    "blue": {
        "primary": "blue",
        "accent": "bright_blue",
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "muted": "dim",
    },
    "magenta": {
        "primary": "magenta",
        "accent": "bright_magenta",
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "muted": "dim",
    },
}


def _get_theme() -> dict:
    """Get the current theme colors based on config."""
    config = load_config()
    name = config.get("theme_color", "cyan")
    return _THEMES.get(name, _THEMES["cyan"])


def primary() -> str:
    """Return the primary theme color string."""
    return _get_theme()["primary"]


def accent() -> str:
    """Return the accent theme color string."""
    return _get_theme()["accent"]


def styled(text: str, role: str = "primary") -> str:
    """Wrap text in Rich markup for the given semantic role."""
    color = _get_theme().get(role, _get_theme()["primary"])
    return f"[{color}]{text}[/{color}]"


def bold(text: str, role: str = "primary") -> str:
    """Wrap text in bold Rich markup for the given semantic role."""
    color = _get_theme().get(role, _get_theme()["primary"])
    return f"[bold {color}]{text}[/bold {color}]"


def rule_style() -> str:
    """Return the style string for Rich rules."""
    return primary()


def border_style() -> str:
    """Return the style string for Rich panel/table borders."""
    return primary()
