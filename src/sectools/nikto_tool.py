from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool
from sectools.utils import extract_hostname

PRESETS = {
    "Standard scan": [],
    "Scan specific port": "port",
    "With SSL (-ssl)": ["-ssl"],
    "Custom flags": None,
}


class NiktoTool(BaseTool):
    name = "Nikto — Web Server Scanner"
    binary = "nikto"
    target_prompt = "Target host (IP/hostname/URL):"

    def _build_command(self, console: Console, target: str) -> list[str] | None:
        hostname, was_url = extract_hostname(target)
        if was_url:
            console.print(f"[yellow]Extracted hostname: {hostname}[/yellow]")

        preset = inquirer.select(
            message="Scan type:",
            choices=list(PRESETS.keys()) + ["View cheat sheet"],
            pointer="❯",
        ).execute()

        if preset == "View cheat sheet":
            from sectools.cheatsheets import show_cheatsheet
            show_cheatsheet(console, "nikto")
            return None

        flags = []
        val = PRESETS[preset]
        if val is None:
            flags_str = inquirer.text(message="Enter nikto flags:").execute()
            flags = flags_str.split()
        elif val == "port":
            port = inquirer.text(message="Port number:").execute()
            flags = ["-p", port.strip()]
        else:
            flags = val

        return ["nikto", "-h", hostname] + flags

_tool = NiktoTool()
run = _tool.run
