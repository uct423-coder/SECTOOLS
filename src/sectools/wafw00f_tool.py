import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool

PRESETS = {
    "Detect WAF": [],
    "List all WAFs (wafw00f -l)": ["-l"],
    "Verbose (-v)": ["-v"],
    "Test all WAFs (-a)": ["-a"],
    "Custom flags": None,
}


class Wafw00fTool(BaseTool):
    name = "Wafw00f — WAF Detector"
    binary = "wafw00f"
    target_prompt = "Target URL:"

    def _build_command(self, console: Console, target: str) -> list[str]:
        preset = inquirer.select(
            message="Scan type:",
            choices=list(PRESETS.keys()),
            pointer="❯",
        ).execute()

        if PRESETS[preset] is None:
            flags_str = inquirer.text(message="Enter wafw00f flags:").execute()
            flags = shlex.split(flags_str)
        else:
            flags = PRESETS[preset]

        if preset == "List all WAFs (wafw00f -l)":
            return ["wafw00f"] + flags
        return ["wafw00f"] + flags + [target]

_tool = Wafw00fTool()
run = _tool.run
