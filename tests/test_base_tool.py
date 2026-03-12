"""Tests for BaseTool template method."""

from unittest.mock import MagicMock, patch
from sectools.base_tool import BaseTool


class DummyTool(BaseTool):
    name = "Dummy Tool"
    binary = "dummy"
    target_prompt = "Target:"

    def _build_command(self, console, target):
        return ["dummy", target]


def test_base_tool_run_calls_template_methods():
    tool = DummyTool()
    console = MagicMock()

    with patch.object(tool, "_prompt_target", return_value="example.com") as mock_prompt, \
         patch.object(tool, "_execute") as mock_exec:
        tool.run(console)
        mock_prompt.assert_called_once()
        mock_exec.assert_called_once_with(console, ["dummy", "example.com"])


def test_base_tool_run_aborts_on_no_target():
    tool = DummyTool()
    console = MagicMock()

    with patch.object(tool, "_prompt_target", return_value=None) as mock_prompt, \
         patch.object(tool, "_execute") as mock_exec:
        tool.run(console)
        mock_prompt.assert_called_once()
        mock_exec.assert_not_called()


def test_base_tool_run_aborts_on_null_command():
    class NullCmdTool(BaseTool):
        name = "Null"
        binary = "null"
        def _build_command(self, console, target):
            return None

    tool = NullCmdTool()
    console = MagicMock()

    with patch.object(tool, "_prompt_target", return_value="test"), \
         patch.object(tool, "_execute") as mock_exec:
        tool.run(console)
        mock_exec.assert_not_called()
