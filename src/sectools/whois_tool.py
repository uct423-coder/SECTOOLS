from rich.console import Console
from sectools.base_tool import BaseTool


class WhoisTool(BaseTool):
    name = "Whois — Domain Lookup"
    binary = "whois"
    target_prompt = "Domain or IP:"

    def _build_command(self, console: Console, target: str) -> list[str]:
        return ["whois", target]

_tool = WhoisTool()
run = _tool.run
