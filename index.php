<?php
/**
 * SecTools — Web Summary Page
 * A clean, modern landing page that summarizes what SecTools is,
 * what it does, and how to install it. For people who aren't
 * going to dig through a CLI repo to figure it out.
 */

$version = "2.1.0";
$tools = [
    ["Recon & OSINT", [
        ["Recon Autopilot", "Chains multiple scans automatically on a target", "nmap + nikto + gobuster"],
        ["Nmap", "Network port scanner and service detection", "nmap"],
        ["Nikto", "Web server vulnerability scanner", "nikto"],
        ["OSINT", "Subdomain enumeration, reverse IP, HTTP headers", "crt.sh + hackertarget"],
        ["Assessment Wizard", "Full automated security assessment with reporting", "multi-tool"],
        ["Subfinder", "Fast passive subdomain discovery using multiple sources", "subfinder"],
        ["WhatWeb", "Identify web technologies, CMS, frameworks, and servers", "whatweb"],
        ["Whois", "Domain and IP registration lookup", "whois"],
        ["DNS Toolkit", "DNS lookups, reverse DNS, zone transfers, record queries", "dig"],
    ]],
    ["Exploitation", [
        ["Metasploit", "Guided workflows for MSF modules and payloads", "msfconsole"],
        ["SQLMap", "Automated SQL injection detection and exploitation", "sqlmap"],
        ["Hydra", "Network login brute-forcer for SSH, FTP, HTTP, etc.", "hydra"],
        ["WPScan", "WordPress vulnerability scanner — plugins, themes, users", "wpscan"],
        ["Nuclei", "Template-based vulnerability scanner by ProjectDiscovery", "nuclei"],
    ]],
    ["Fuzzing & Brute Force", [
        ["Ffuf", "Fast web fuzzer for directories, subdomains, and parameters", "ffuf"],
        ["Dirb", "URL brute-forcer with recursive scanning", "dirb"],
        ["Gobuster", "Directory, DNS, and vhost brute-forcing", "gobuster"],
    ]],
    ["Password Cracking", [
        ["John the Ripper", "CPU-based password hash cracker", "john"],
        ["Hashcat", "GPU-accelerated password cracker with mask attacks", "hashcat"],
    ]],
    ["Networking & Web", [
        ["Netcat", "TCP/UDP connections, listeners, and port scanning", "nc / ncat"],
        ["HTTP Probe", "Inspect HTTP responses, headers, redirects, and SSL certs", "built-in"],
        ["Screenshot", "Capture web page screenshots via Chrome or Safari", "headless chrome"],
        ["Port Reference", "Look up ~90 common ports by number or service", "built-in"],
        ["Subnet Calculator", "CIDR notation parser with full network details", "built-in"],
        ["Masscan", "Extremely fast port scanner for large networks", "masscan"],
        ["SSLScan", "Analyze SSL/TLS protocols, ciphers, and certificates", "sslscan"],
        ["Wafw00f", "Detect web application firewalls (100+ WAFs)", "wafw00f"],
    ]],
    ["Generators", [
        ["Reverse Shell Generator", "Payloads for Bash, Python, PHP, Perl, Ruby, PowerShell, Java, Lua, Netcat", "built-in"],
        ["Password Generator", "Cryptographically secure passwords with entropy estimate", "built-in"],
        ["Encoding / Decoding", "Base64, URL, Hex, ROT13, HTML entities, Binary", "built-in"],
    ]],
    ["Analysis", [
        ["Hash Identifier", "Detect hash type with Hashcat mode and John format", "built-in"],
        ["Scan History", "Browse, search, view, and delete scan logs", "built-in"],
        ["Diff Scans", "Compare two scan outputs side by side", "built-in"],
        ["Enum4Linux", "Windows/SMB enumeration — users, shares, groups, policies", "enum4linux"],
    ]],
];

$features = [
    ["Interactive Menus", "Navigate everything with arrow keys. No commands to memorize."],
    ["Auto-Logging", "Every scan is logged with timestamps. Generate HTML or PDF reports."],
    ["Workflows", "Chain tools into automated pipelines. Built-in templates + custom."],
    ["Target Management", "Save targets, add notes, organize into groups."],
    ["Scope Management", "Define engagement scope. Get warnings before scanning out-of-scope."],
    ["Session Tracking", "Keep different engagements organized with named sessions."],
    ["Credential Manager", "Store test credentials securely for brute-force tools."],
    ["Scan Profiles", "Save and reuse favorite scan configurations."],
    ["Wordlist Manager", "Auto-download and manage wordlists from SecLists."],
    ["Cheat Sheets", "Built-in reference cards for every tool."],
    ["Notifications", "Desktop notifications when long scans complete."],
    ["Proxy Support", "Route tool traffic through a proxy (Burp, ZAP, etc)."],
    ["Plugin System", "Drop Python scripts into a plugins folder to extend."],
    ["AI Advice", "Optional Claude-powered remediation advice on assessment reports."],
    ["Auto-Updates", "One command to pull latest changes and reinstall."],
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecTools v<?= $version ?> — Security Toolkit CLI</title>
    <style>
        :root {
            --bg: #0a0a12;
            --bg2: #12121e;
            --bg3: #1a1a2e;
            --cyan: #00d4ff;
            --blue: #4a6cf7;
            --magenta: #c471ed;
            --green: #00e676;
            --yellow: #ffd600;
            --red: #ff5252;
            --text: #e0e0e0;
            --dim: #666;
            --border: #1e1e3a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', 'Cascadia Code', monospace;
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* Header */
        .hero {
            text-align: center;
            padding: 80px 20px 60px;
            background: linear-gradient(135deg, var(--bg) 0%, var(--bg3) 50%, var(--bg) 100%);
            border-bottom: 1px solid var(--border);
            position: relative;
        }
        .hero::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--cyan), var(--blue), var(--magenta), transparent);
        }
        .hero pre {
            color: var(--cyan);
            font-size: clamp(10px, 2.5vw, 16px);
            line-height: 1.2;
            margin-bottom: 20px;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }
        .hero h1 { display: none; }
        .hero .tagline {
            font-size: 1.1em;
            color: var(--dim);
            margin-bottom: 30px;
        }
        .hero .version {
            display: inline-block;
            background: var(--bg3);
            border: 1px solid var(--cyan);
            color: var(--cyan);
            padding: 4px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-bottom: 30px;
        }
        .hero .author {
            color: var(--dim);
            font-size: 0.85em;
        }

        /* Install Banner */
        .install-bar {
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 20px;
            text-align: center;
        }
        .install-bar code {
            background: var(--bg);
            border: 1px solid var(--border);
            padding: 10px 24px;
            border-radius: 6px;
            font-size: 1em;
            color: var(--green);
            display: inline-block;
            cursor: pointer;
            transition: border-color 0.2s;
        }
        .install-bar code:hover { border-color: var(--cyan); }
        .install-bar .hint { color: var(--dim); font-size: 0.8em; margin-top: 8px; }

        /* Container */
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Section */
        section {
            padding: 60px 0;
            border-bottom: 1px solid var(--border);
        }
        section:last-child { border-bottom: none; }
        .section-title {
            text-align: center;
            font-size: 1.5em;
            color: var(--cyan);
            margin-bottom: 10px;
        }
        .section-sub {
            text-align: center;
            color: var(--dim);
            margin-bottom: 40px;
            font-size: 0.9em;
        }

        /* Tool Categories */
        .category { margin-bottom: 40px; }
        .category h3 {
            font-size: 1.1em;
            color: var(--magenta);
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }
        .tool-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 12px;
        }
        .tool-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            transition: border-color 0.2s, transform 0.2s;
        }
        .tool-card:hover {
            border-color: var(--cyan);
            transform: translateY(-2px);
        }
        .tool-card .name {
            color: var(--cyan);
            font-weight: bold;
            font-size: 0.95em;
        }
        .tool-card .desc {
            color: var(--text);
            font-size: 0.8em;
            margin: 6px 0;
        }
        .tool-card .engine {
            color: var(--dim);
            font-size: 0.7em;
        }

        /* Features Grid */
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }
        .feature {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            border-left: 3px solid var(--blue);
        }
        .feature .name {
            color: var(--green);
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 6px;
        }
        .feature .desc {
            color: var(--dim);
            font-size: 0.8em;
        }

        /* Commands */
        .commands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 12px;
        }
        .cmd {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 12px 16px;
            display: flex;
            gap: 12px;
            align-items: baseline;
        }
        .cmd .key {
            color: var(--cyan);
            font-weight: bold;
            white-space: nowrap;
            min-width: 120px;
        }
        .cmd .val { color: var(--dim); font-size: 0.85em; }

        /* Stats */
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            margin: 40px 0;
        }
        .stat { text-align: center; }
        .stat .num {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, var(--cyan), var(--magenta));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .stat .label { color: var(--dim); font-size: 0.85em; }

        /* Footer */
        footer {
            text-align: center;
            padding: 40px 20px;
            color: var(--dim);
            font-size: 0.8em;
            border-top: 1px solid var(--border);
        }
        footer a { color: var(--cyan); text-decoration: none; }
        footer a:hover { text-decoration: underline; }

        /* Requirements */
        .req-list {
            list-style: none;
            columns: 2;
            gap: 20px;
        }
        .req-list li {
            padding: 4px 0;
            color: var(--dim);
            font-size: 0.85em;
        }
        .req-list li::before {
            content: '>';
            color: var(--cyan);
            margin-right: 8px;
        }

        @media (max-width: 600px) {
            .tool-grid, .features-grid, .commands-grid { grid-template-columns: 1fr; }
            .req-list { columns: 1; }
            .stats { gap: 20px; }
        }
    </style>
</head>
<body>
    <div class="hero">
        <pre>
   ____            _____           _
  / ___|  ___  ___|_   _|__   ___ | |___
  \___ \ / _ \/ __| | |/ _ \ / _ \| / __|
   ___) |  __/ (__  | | (_) | (_) | \__ \
  |____/ \___|\___| |_|\___/ \___/|_|___/</pre>
        <h1>SecTools</h1>
        <div class="version">v<?= $version ?></div>
        <p class="tagline">All-in-one security toolkit CLI. Interactive menus. Auto-logging. Reports.</p>
        <p class="author">Made by Shepard Sotiroglou</p>
    </div>

    <div class="install-bar">
        <code onclick="navigator.clipboard.writeText('git clone https://github.com/yourusername/sectools && cd sectools && bash install.sh')">
            git clone &amp; bash install.sh
        </code>
        <p class="hint">Click to copy. Works on macOS, Linux, and Windows (WSL).</p>
    </div>

    <div class="container">

        <!-- Stats -->
        <div class="stats">
            <div class="stat">
                <div class="num"><?= array_sum(array_map(fn($c) => count($c[1]), $tools)) ?></div>
                <div class="label">Tools Integrated</div>
            </div>
            <div class="stat">
                <div class="num"><?= count($features) ?></div>
                <div class="label">Features</div>
            </div>
            <div class="stat">
                <div class="num">21</div>
                <div class="label">Cheat Sheets</div>
            </div>
            <div class="stat">
                <div class="num">5</div>
                <div class="label">Workflow Templates</div>
            </div>
        </div>

        <!-- Tools -->
        <section>
            <h2 class="section-title">Tools</h2>
            <p class="section-sub">Everything you need for a pentest, organized into categories.</p>

            <?php foreach ($tools as [$category, $items]): ?>
            <div class="category">
                <h3><?= htmlspecialchars($category) ?></h3>
                <div class="tool-grid">
                    <?php foreach ($items as [$name, $desc, $engine]): ?>
                    <div class="tool-card">
                        <div class="name"><?= htmlspecialchars($name) ?></div>
                        <div class="desc"><?= htmlspecialchars($desc) ?></div>
                        <div class="engine"><?= htmlspecialchars($engine) ?></div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </section>

        <!-- Features -->
        <section>
            <h2 class="section-title">Features</h2>
            <p class="section-sub">Not just a wrapper. A full toolkit with built-in management.</p>

            <div class="features-grid">
                <?php foreach ($features as [$name, $desc]): ?>
                <div class="feature">
                    <div class="name"><?= htmlspecialchars($name) ?></div>
                    <div class="desc"><?= htmlspecialchars($desc) ?></div>
                </div>
                <?php endforeach; ?>
            </div>
        </section>

        <!-- Commands -->
        <section>
            <h2 class="section-title">Commands</h2>
            <p class="section-sub">Simple CLI commands. Everything else is interactive.</p>

            <div class="commands-grid">
                <?php
                $commands = [
                    ["sectool start", "Launch the interactive menu"],
                    ["sectool restart", "Restart SecTools"],
                    ["sectool update", "Pull latest + reinstall"],
                    ["sectool reinstall", "Clean reinstall"],
                    ["sectool uninstall", "Remove everything"],
                    ["sectool version", "Show version"],
                    ["sectool status", "Check installed tools"],
                    ["sectool hash <value>", "Identify a hash type"],
                    ["sectool encode <method> <text>", "Quick encode"],
                    ["sectool help", "Show all commands"],
                ];
                foreach ($commands as [$key, $val]):
                ?>
                <div class="cmd">
                    <span class="key"><?= htmlspecialchars($key) ?></span>
                    <span class="val"><?= htmlspecialchars($val) ?></span>
                </div>
                <?php endforeach; ?>
            </div>
        </section>

        <!-- Requirements -->
        <section>
            <h2 class="section-title">Requirements</h2>
            <p class="section-sub">Python 3.9+ required. External tools are optional — install what you need.</p>

            <ul class="req-list">
                <li>Python 3.9+</li>
                <li>pip (comes with Python)</li>
                <li>Nmap (network scanning)</li>
                <li>Nikto (web scanning)</li>
                <li>Gobuster (dir brute-force)</li>
                <li>SQLMap (SQL injection)</li>
                <li>Hydra (brute force)</li>
                <li>Metasploit Framework</li>
                <li>John the Ripper</li>
                <li>Hashcat (GPU cracking)</li>
                <li>Netcat / Ncat</li>
                <li>Chrome (for screenshots)</li>
            </ul>
        </section>
    </div>

    <footer>
        <p>SecTools v<?= $version ?> &mdash; Made by Shepard Sotiroglou</p>
        <p style="margin-top: 8px;">
            Built with Python + Rich + InquirerPy
        </p>
    </footer>
</body>
</html>
