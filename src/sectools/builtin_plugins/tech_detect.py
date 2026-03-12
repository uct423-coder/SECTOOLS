PLUGIN_NAME = "Tech Stack Detector"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

import urllib.request
import re
from InquirerPy import inquirer


HEADER_SIGS = {
    "x-powered-by": "Powered By",
    "server": "Server",
    "x-aspnet-version": "ASP.NET",
    "x-drupal-cache": "Drupal",
    "x-generator": "Generator",
    "x-shopify-stage": "Shopify",
}

BODY_SIGS = [
    (r"wp-content|wp-includes|wordpress", "WordPress"),
    (r"Joomla", "Joomla"),
    (r"Drupal\.settings", "Drupal"),
    (r"shopify\.com", "Shopify"),
    (r"react", "React"),
    (r"vue\.js|vuejs", "Vue.js"),
    (r"angular", "Angular"),
    (r"jquery", "jQuery"),
    (r"bootstrap", "Bootstrap"),
    (r"tailwindcss|tailwind", "Tailwind CSS"),
    (r"next\.js|nextjs|_next/", "Next.js"),
    (r"nuxt", "Nuxt.js"),
    (r"laravel", "Laravel"),
    (r"django", "Django"),
    (r"flask", "Flask"),
    (r"express", "Express.js"),
    (r"cloudflare", "Cloudflare"),
    (r"google-analytics|gtag", "Google Analytics"),
    (r"recaptcha", "reCAPTCHA"),
]


def run(console):
    console.rule("[bold cyan]Tech Stack Detector[/bold cyan]")
    url = inquirer.text(message="URL:").execute().strip()
    if not url:
        console.print("[red]No URL.[/red]")
        return
    if not url.startswith("http"):
        url = f"https://{url}"

    console.print(f"[dim]Scanning {url}...[/dim]\n")
    detected = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            headers = dict(resp.headers)
            body = resp.read(50000).decode("utf-8", errors="ignore")

            # Check headers
            for hdr, label in HEADER_SIGS.items():
                val = headers.get(hdr) or headers.get(hdr.title())
                if val:
                    detected.append((label, val))

            # Check body
            for pattern, name in BODY_SIGS:
                if re.search(pattern, body, re.IGNORECASE):
                    detected.append((name, "Detected in HTML"))

    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
        return

    if detected:
        seen = set()
        for tech, detail in detected:
            if tech not in seen:
                console.print(f"  [green][+][/green] [bold]{tech}[/bold] — {detail}")
                seen.add(tech)
        console.print(f"\n[bold]{len(seen)} technologies detected[/bold]")
    else:
        console.print("[yellow]No technologies detected.[/yellow]")
