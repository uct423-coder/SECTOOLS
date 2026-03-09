"""HTTP Probe — inspect HTTP responses, headers, redirects, and SSL certs."""

import re
import ssl
import socket
import urllib.request
import urllib.error
from html.parser import HTMLParser
from urllib.parse import urlparse

from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class _TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_title = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self._in_title = True

    def handle_data(self, data):
        if self._in_title:
            self.title = data.strip()

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False


def _get_ssl_info(hostname: str, port: int) -> dict | None:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, port))
            cert = s.getpeercert()
        return cert
    except Exception:
        return None


def run(console: Console) -> None:
    """Probe a URL and display HTTP response details."""
    console.print("\n[bold cyan]HTTP Probe[/bold cyan]\n")

    url = inquirer.text(message="Enter URL:").execute()
    if not url:
        console.print("[red]No URL provided.[/red]")
        return

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Track redirects
    redirects: list[str] = []

    class RedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            redirects.append(f"{code} -> {newurl}")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(RedirectHandler)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SecTools-HTTPProbe/1.0"})
        resp = opener.open(req, timeout=10)
    except urllib.error.HTTPError as e:
        resp = e
    except urllib.error.URLError as e:
        console.print(f"[red]Connection error: {e.reason}[/red]")
        return
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    status = getattr(resp, "status", getattr(resp, "code", "N/A"))
    console.print(f"\n[bold]Status:[/bold] {status}")

    # Redirect chain
    if redirects:
        console.print(Panel("\n".join(redirects), title="Redirect Chain", border_style="yellow", expand=False))

    # Headers table
    headers_table = Table(title="Response Headers")
    headers_table.add_column("Header", style="cyan")
    headers_table.add_column("Value", style="white")

    for key, val in resp.headers.items():
        headers_table.add_row(key, val)

    console.print(headers_table)

    # Highlighted fields
    server = resp.headers.get("Server", "N/A")
    ctype = resp.headers.get("Content-Type", "N/A")
    clength = resp.headers.get("Content-Length", "N/A")
    console.print(f"[bold]Server:[/bold] {server}")
    console.print(f"[bold]Content-Type:[/bold] {ctype}")
    console.print(f"[bold]Content-Length:[/bold] {clength}")

    # Page title
    if "html" in ctype.lower():
        try:
            body = resp.read(65536).decode("utf-8", errors="replace")
            parser = _TitleParser()
            parser.feed(body)
            if parser.title:
                console.print(f"[bold]Page Title:[/bold] {parser.title}")
        except Exception:
            pass

    # SSL cert info
    parsed = urlparse(url)
    if parsed.scheme == "https":
        port = parsed.port or 443
        cert = _get_ssl_info(parsed.hostname, port)
        if cert:
            cert_table = Table(title="SSL Certificate")
            cert_table.add_column("Field", style="cyan")
            cert_table.add_column("Value", style="white")

            subject = dict(x[0] for x in cert.get("subject", ()))
            issuer = dict(x[0] for x in cert.get("issuer", ()))
            cert_table.add_row("Subject CN", subject.get("commonName", "N/A"))
            cert_table.add_row("Issuer CN", issuer.get("commonName", "N/A"))
            cert_table.add_row("Issuer Org", issuer.get("organizationName", "N/A"))
            cert_table.add_row("Not Before", cert.get("notBefore", "N/A"))
            cert_table.add_row("Not After", cert.get("notAfter", "N/A"))

            san = cert.get("subjectAltName", ())
            if san:
                names = ", ".join(v for _, v in san[:10])
                cert_table.add_row("SANs", names)

            console.print(cert_table)
