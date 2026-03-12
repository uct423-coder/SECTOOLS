import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool

PRESETS = {
    "Quick scan (--aggression 1)": ["--aggression", "1"],
    "Standard scan (--aggression 3)": ["--aggression", "3"],
    "Aggressive scan (--aggression 4)": ["--aggression", "4"],
    "Verbose output (-v)": ["-v"],
    "Custom flags": None,
}


class WhatWebTool(BaseTool):
    name = "WhatWeb — Technology Identifier"
    binary = "whatweb"
    target_prompt = "Target URL:"

    def _prompt_target(self, console: Console) -> str | None:
        from InquirerPy import inquirer
        target = inquirer.text(message="Target URL:").execute()
        if not target or not target.strip():
            console.print("[red]No target provided.[/red]")
            return None
        return target.strip()

    def _build_command(self, console: Console, target: str) -> list[str] | None:
        preset = inquirer.select(
            message="Scan type:",
            choices=list(PRESETS.keys()) + ["View cheat sheet"],
            pointer="❯",
        ).execute()

        if preset == "View cheat sheet":
            from sectools.cheatsheets import show_cheatsheet
            show_cheatsheet(console, "whatweb")
            return None

        if PRESETS[preset] is None:
            flags_str = inquirer.text(message="Enter whatweb flags:").execute()
            flags = shlex.split(flags_str)
        else:
            flags = PRESETS[preset]

        return ["whatweb"] + flags + [target]

_tool = WhatWebTool()
run = _tool.run
