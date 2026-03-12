import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool

PRESETS = {
    "Enumerate plugins (--enumerate p)": ["--enumerate", "p"],
    "Enumerate users (--enumerate u)": ["--enumerate", "u"],
    "Enumerate themes (--enumerate t)": ["--enumerate", "t"],
    "Full enumeration (--enumerate ap,at,u)": ["--enumerate", "ap,at,u"],
    "Aggressive plugin detection (--enumerate p --plugins-detection aggressive)": [
        "--enumerate", "p", "--plugins-detection", "aggressive",
    ],
    "Custom flags": None,
}


class WPScanTool(BaseTool):
    name = "WPScan — WordPress Scanner"
    binary = "wpscan"
    target_prompt = "Target URL:"

    def _build_command(self, console: Console, target: str) -> list[str] | None:
        preset = inquirer.select(
            message="Scan type:",
            choices=list(PRESETS.keys()) + ["View cheat sheet"],
            pointer="❯",
        ).execute()

        if preset == "View cheat sheet":
            from sectools.cheatsheets import show_cheatsheet
            show_cheatsheet(console, "wpscan")
            return None

        if PRESETS[preset] is None:
            flags_str = inquirer.text(message="Enter wpscan flags:").execute()
            flags = shlex.split(flags_str)
        else:
            flags = PRESETS[preset]

        return ["wpscan", "--url", target] + flags

_tool = WPScanTool()
run = _tool.run
