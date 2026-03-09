"""Tip of the Day — random security tips shown on the dashboard."""

import random

TIPS = [
    "Always scan with permission — unauthorized scanning is illegal.",
    "Use nmap's -sV flag to detect service versions on open ports.",
    "Keep your tools updated to get the latest vulnerability checks.",
    "Save your targets to track progress across sessions.",
    "Use target groups to organise related hosts for batch scanning.",
    "Check HTTP headers for security misconfigurations (X-Frame-Options, CSP, etc.).",
    "Rotate your wordlists — different lists catch different results.",
    "Use --script=vuln with nmap to run vulnerability detection scripts.",
    "Always document your findings as you go — memory fades fast.",
    "Start recon broad, then narrow down to interesting services.",
    "Use Gobuster with multiple wordlists for better directory coverage.",
    "Check for default credentials on discovered services.",
    "DNS enumeration can reveal subdomains the target forgot about.",
    "Use scope management to avoid accidentally scanning out-of-scope hosts.",
    "Export your reports in multiple formats for different audiences.",
    "SSL/TLS certificates can reveal hostnames and organisational info.",
    "Reverse DNS lookups can uncover related infrastructure.",
    "Use scan profiles to save and reuse your favourite configurations.",
    "Schedule scans during off-peak hours for less disruption.",
    "Compare scan diffs to spot new services or closed ports over time.",
    "Always verify findings manually before reporting them.",
    "Use the credential manager to securely store test account details.",
    "WHOIS data can reveal registrant info and name servers.",
    "Check robots.txt and sitemap.xml for hidden paths.",
    "Use sessions to keep different engagements organised.",
    "HTTP methods like PUT and DELETE may be enabled unnecessarily.",
    "Banner grabbing with netcat is quick and stealthy.",
    "Use encoding tools to test for input validation bypasses.",
    "Hash identification helps choose the right cracking approach.",
    "Back up your logs and reports — they're your evidence.",
]


def get_tip() -> str:
    """Return a random security tip."""
    return random.choice(TIPS)
