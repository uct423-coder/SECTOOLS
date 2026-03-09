"""Encoding/Decoding Utility — Base64, URL, Hex, ROT13, HTML entities, Binary."""

import base64
import codecs
import html
import urllib.parse

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel


def _b64_encode(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _b64_decode(text: str) -> str:
    return base64.b64decode(text).decode()


def _url_encode(text: str) -> str:
    return urllib.parse.quote(text, safe="")


def _url_decode(text: str) -> str:
    return urllib.parse.unquote(text)


def _hex_encode(text: str) -> str:
    return text.encode().hex()


def _hex_decode(text: str) -> str:
    return bytes.fromhex(text).decode()


def _rot13_encode(text: str) -> str:
    return codecs.encode(text, "rot_13")


def _html_encode(text: str) -> str:
    return html.escape(text, quote=True)


def _html_decode(text: str) -> str:
    return html.unescape(text)


def _bin_encode(text: str) -> str:
    return " ".join(format(b, "08b") for b in text.encode())


def _bin_decode(text: str) -> str:
    parts = text.strip().split()
    return bytes(int(b, 2) for b in parts).decode()


CODECS = {
    "Base64": {"encode": _b64_encode, "decode": _b64_decode},
    "URL": {"encode": _url_encode, "decode": _url_decode},
    "Hex": {"encode": _hex_encode, "decode": _hex_decode},
    "ROT13": {"encode": _rot13_encode, "decode": _rot13_encode},
    "HTML Entities": {"encode": _html_encode, "decode": _html_decode},
    "Binary": {"encode": _bin_encode, "decode": _bin_decode},
}


def run(console: Console) -> None:
    """Encode or decode text using various schemes."""
    console.print("\n[bold cyan]Encoding / Decoding Utility[/bold cyan]\n")

    codec_name = inquirer.select(
        message="Select encoding:",
        choices=list(CODECS.keys()),
    ).execute()

    if codec_name == "ROT13":
        direction = "encode"
    else:
        direction = inquirer.select(
            message="Operation:",
            choices=["encode", "decode"],
        ).execute()

    text = inquirer.text(message="Enter input text:").execute()
    if not text:
        console.print("[red]No input provided.[/red]")
        return

    try:
        result = CODECS[codec_name][direction](text)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        return

    label = f"{codec_name} {direction}"
    console.print()
    console.print(Panel(result, title=label, border_style="green", expand=False))
