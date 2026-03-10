"""Proxy support — inject proxy flags into tool commands."""

from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer
from sectools.config import load_config, save_config


# How each tool accepts proxy settings
PROXY_FLAGS = {
    "nmap": lambda url: ["--proxy", url],
    "nikto": lambda url: ["-useproxy", url],
    "sqlmap": lambda url: ["--proxy", url],
    "gobuster": lambda url: ["-p", url],
    "hydra": lambda url: ["-x", url],  # SOCKS proxy; HTTP via env
    "curl": lambda url: ["--proxy", url],
}


def get_proxy_args(tool_binary: str) -> list[str]:
    """Return proxy flags for a tool, or empty list if proxy is disabled."""
    config = load_config()
    if not config.get("proxy_enabled", False):
        return []

    proxy_url = config.get("proxy_url", "")
    if not proxy_url:
        return []

    flag_fn = PROXY_FLAGS.get(tool_binary)
    if flag_fn:
        return flag_fn(proxy_url)
    return []


def get_proxy_env() -> dict:
    """Return proxy environment variables (for tools that use env vars)."""
    config = load_config()
    if not config.get("proxy_enabled", False):
        return {}

    proxy_url = config.get("proxy_url", "")
    if not proxy_url:
        return {}

    return {
        "http_proxy": proxy_url,
        "https_proxy": proxy_url,
        "HTTP_PROXY": proxy_url,
        "HTTPS_PROXY": proxy_url,
    }


def proxy_menu(console: Console):
    """Configure proxy settings."""
    config = load_config()

    while True:
        enabled = config.get("proxy_enabled", False)
        url = config.get("proxy_url", "")

        table = Table(title="Proxy Configuration", border_style="dim")
        table.add_column("Setting", style="bold")
        table.add_column("Value")
        table.add_row("Enabled", "[green]Yes[/green]" if enabled else "[red]No[/red]")
        table.add_row("Proxy URL", url or "[dim]not set[/dim]")
        table.add_row("", "")
        table.add_row("[dim]Supported[/dim]", "[dim]nmap, nikto, sqlmap, gobuster, hydra[/dim]")
        console.print(table)

        choice = inquirer.select(
            message="Proxy settings:",
            choices=[
                "Toggle proxy on/off",
                "Set proxy URL",
                "Test proxy",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if choice == "Back":
            save_config(config)
            return
        elif choice == "Toggle proxy on/off":
            config["proxy_enabled"] = not enabled
            state = "enabled" if config["proxy_enabled"] else "disabled"
            console.print(f"[green]Proxy {state}.[/green]")
        elif choice == "Set proxy URL":
            new_url = inquirer.text(
                message="Proxy URL (e.g. http://127.0.0.1:8080, socks5://proxy:1080):",
                default=url,
            ).execute().strip()
            config["proxy_url"] = new_url
            console.print(f"[green]Proxy URL set to: {new_url}[/green]")
        elif choice == "Test proxy":
            _test_proxy(console, config)

        save_config(config)
        console.print()


def _test_proxy(console: Console, config: dict):
    """Quick connectivity test through the proxy."""
    import subprocess

    url = config.get("proxy_url", "")
    if not url:
        console.print("[red]No proxy URL configured.[/red]")
        return

    console.print(f"[dim]Testing connection through {url}...[/dim]")
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--proxy", url,
             "--connect-timeout", "5", "https://httpbin.org/ip"],
            capture_output=True, text=True, timeout=10,
        )
        code = result.stdout.strip()
        if code == "200":
            console.print(f"[bold green]Proxy working — HTTP 200[/bold green]")
        elif code:
            console.print(f"[yellow]Got HTTP {code} — proxy may be misconfigured.[/yellow]")
        else:
            console.print(f"[red]No response — check proxy URL and that it's running.[/red]")
            if result.stderr:
                console.print(f"[dim]{result.stderr.strip()}[/dim]")
    except FileNotFoundError:
        console.print("[red]curl not found — install curl to test proxy.[/red]")
    except subprocess.TimeoutExpired:
        console.print("[red]Connection timed out.[/red]")
