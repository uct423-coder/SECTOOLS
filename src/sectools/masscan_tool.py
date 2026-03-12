import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool

PRESETS = {
    "Top 100 ports (--top-ports 100)": ["--top-ports", "100"],
    "Top 1000 ports (--top-ports 1000)": ["--top-ports", "1000"],
    "All ports (-p0-65535)": ["-p0-65535"],
    "Common web ports (-p80,443,8080,8443)": ["-p80,443,8080,8443"],
    "Custom port range": "ports",
    "Custom flags": None,
}


class MasscanTool(BaseTool):
    name = "Masscan — Fast Port Scanner"
    binary = "masscan"
    target_prompt = "Target (IP/CIDR range):"

    def _build_command(self, console: Console, target: str) -> list[str]:
        preset = inquirer.select(
            message="Scan type:",
            choices=list(PRESETS.keys()),
            pointer="❯",
        ).execute()

        if PRESETS[preset] is None:
            flags_str = inquirer.text(message="Enter masscan flags:").execute()
            flags = shlex.split(flags_str)
        elif PRESETS[preset] == "ports":
            port_range = inquirer.text(message="Enter port range (e.g. 1-1024):").execute()
            flags = [f"-p{port_range}"]
        else:
            flags = PRESETS[preset]

        rate = inquirer.text(
            message="Rate (packets/sec):",
            default="1000",
        ).execute()

        return ["masscan"] + flags + ["--rate", rate, target]

_tool = MasscanTool()
run = _tool.run
