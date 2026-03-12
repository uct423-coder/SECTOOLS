"""Base class for CLI tool wrappers with template method pattern."""

from abc import ABC, abstractmethod
from rich.console import Console
from sectools.theme import bold, rule_style
from sectools.utils import ask_target, run_logged


class BaseTool(ABC):
    """Template for wrapping external CLI tools."""

    name: str = "Tool"
    binary: str = "tool"
    target_prompt: str = "Target (IP/hostname):"

    def run(self, console: Console) -> None:
        """Template method: header → target → validate → build → execute."""
        self._show_header(console)
        target = self._prompt_target(console)
        if target is None:
            return
        if not self._validate_target(console, target):
            return
        cmd = self._build_command(console, target)
        if cmd is None:
            return
        self._execute(console, cmd)

    def _show_header(self, console: Console) -> None:
        console.rule(bold(self.name), style=rule_style())
        console.print()

    def _prompt_target(self, console: Console) -> str | None:
        return ask_target(console, self.target_prompt)

    def _validate_target(self, console: Console, target: str) -> bool:
        return True

    @abstractmethod
    def _build_command(self, console: Console, target: str) -> list[str] | None:
        ...

    def _execute(self, console: Console, cmd: list[str]) -> None:
        run_logged(cmd, console, self.binary)
