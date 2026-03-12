import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.base_tool import BaseTool

PRESETS = {
    "Standard scan": [],
    "Show certificate": ["--show-certificate"],
    "No color (--no-colour)": ["--no-colour"],
    "Check specific protocol (--tls10/--tls11/--tls12/--tls13)": None,
    "Custom flags": None,
}

PROTOCOL_CHOICES = ["--tls10", "--tls11", "--tls12", "--tls13"]


class SSLScanTool(BaseTool):
    name = "SSLScan — TLS/SSL Analyzer"
    binary = "sslscan"
    target_prompt = "Host:port (e.g. example.com:443):"

    def _build_command(self, console: Console, target: str) -> list[str]:
        preset = inquirer.select(
            message="Scan type:",
            choices=list(PRESETS.keys()),
            pointer="❯",
        ).execute()

        if preset == "Check specific protocol (--tls10/--tls11/--tls12/--tls13)":
            protocol = inquirer.select(
                message="Select protocol:",
                choices=PROTOCOL_CHOICES,
                pointer="❯",
            ).execute()
            flags = [protocol]
        elif preset == "Custom flags":
            flags_str = inquirer.text(message="Enter sslscan flags:").execute()
            flags = shlex.split(flags_str)
        else:
            flags = PRESETS[preset]

        return ["sslscan"] + flags + [target]

_tool = SSLScanTool()
run = _tool.run
