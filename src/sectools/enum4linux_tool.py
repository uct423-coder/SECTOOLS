import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool

PRESETS = {
    "Full enumeration (-a)": ["-a"],
    "User enumeration (-U)": ["-U"],
    "Share enumeration (-S)": ["-S"],
    "Password policy (-P)": ["-P"],
    "Group enumeration (-G)": ["-G"],
    "OS info (-o)": ["-o"],
    "Custom flags": None,
}


class Enum4LinuxTool(BaseTool):
    name = "Enum4Linux — SMB Enumeration"
    binary = "enum4linux"
    target_prompt = "Target IP:"

    def _build_command(self, console: Console, target: str) -> list[str] | None:
        preset = inquirer.select(
            message="Enumeration type:",
            choices=list(PRESETS.keys()) + ["View cheat sheet"],
            pointer="❯",
        ).execute()

        if preset == "View cheat sheet":
            from sectools.cheatsheets import show_cheatsheet
            show_cheatsheet(console, "enum4linux")
            return None

        if PRESETS[preset] is None:
            flags_str = inquirer.text(message="Enter enum4linux flags:").execute()
            flags = shlex.split(flags_str)
        else:
            flags = PRESETS[preset]

        return ["enum4linux"] + flags + [target]

_tool = Enum4LinuxTool()
run = _tool.run
