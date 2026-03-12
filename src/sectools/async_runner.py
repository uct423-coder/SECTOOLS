"""Async subprocess runner for parallel workflow steps."""

import asyncio
import datetime
from pathlib import Path
from rich.console import Console


async def run_command_async(
    cmd: list[str],
    console: Console,
    tool_name: str,
    logs_dir: Path,
) -> dict:
    """Run a command asynchronously, capturing output.

    Returns dict with keys: tool, cmd, returncode, output, log_file.
    """
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = tool_name.lower().replace(" ", "_")
    log_file = logs_dir / f"{safe_name}_{timestamp}.log"

    console.print(f"  [dim]Starting: {' '.join(cmd)}[/dim]")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout_bytes, _ = await process.communicate()
        output = stdout_bytes.decode("utf-8", errors="replace")
    except FileNotFoundError:
        output = f"ERROR: {cmd[0]} not found"
        returncode = -1
    else:
        returncode = process.returncode

    with open(log_file, "w") as f:
        f.write(f"# {tool_name} — {datetime.datetime.now().isoformat()}\n")
        f.write(f"# Command: {' '.join(cmd)}\n\n")
        f.write(output)

    return {
        "tool": tool_name,
        "cmd": cmd,
        "returncode": returncode,
        "output": output,
        "log_file": log_file,
    }


async def run_parallel_group(
    commands: list[tuple[list[str], str]],
    console: Console,
    logs_dir: Path,
) -> list[dict]:
    """Run multiple commands in parallel.

    commands: list of (cmd, tool_name) tuples.
    Returns list of result dicts.
    """
    tasks = [
        run_command_async(cmd, console, name, logs_dir)
        for cmd, name in commands
    ]
    return await asyncio.gather(*tasks)
