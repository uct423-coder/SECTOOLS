import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool

PRESETS = {
    "Basic enumeration": [],
    "Silent mode (-silent)": ["-silent"],
    "Recursive (-recursive)": ["-recursive"],
    "All sources (-all)": ["-all"],
    "Custom flags": None,
}


class SubfinderTool(BaseTool):
    name = "Subfinder — Subdomain Discovery"
    binary = "subfinder"
    target_prompt = "Domain:"

    def _prompt_target(self, console: Console) -> str | None:
        domain = inquirer.text(message="Domain:").execute()
        if not domain:
            console.print("[red]No domain provided.[/red]")
            return None
        return domain

    def _build_command(self, console: Console, target: str) -> list[str]:
        preset = inquirer.select(
            message="Scan type:",
            choices=list(PRESETS.keys()),
            pointer="❯",
        ).execute()

        if PRESETS[preset] is None:
            flags_str = inquirer.text(message="Enter subfinder flags:").execute()
            flags = shlex.split(flags_str)
        else:
            flags = PRESETS[preset]

        threads = inquirer.text(
            message="Threads (default: 10):",
            default="10",
        ).execute()

        return ["subfinder", "-d", target] + flags + ["-t", threads]

_tool = SubfinderTool()
run = _tool.run
