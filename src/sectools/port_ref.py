"""Port Reference Lookup — search ~80 common ports by number or service name."""

from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table

# (port, protocol, service, description)
PORTS: list[tuple[int, str, str, str]] = [
    (7, "TCP/UDP", "Echo", "Echo service"),
    (20, "TCP", "FTP-Data", "FTP data transfer"),
    (21, "TCP", "FTP", "File Transfer Protocol control"),
    (22, "TCP", "SSH", "Secure Shell"),
    (23, "TCP", "Telnet", "Unencrypted remote login"),
    (25, "TCP", "SMTP", "Simple Mail Transfer Protocol"),
    (43, "TCP", "WHOIS", "WHOIS directory service"),
    (49, "TCP/UDP", "TACACS+", "Terminal Access Controller Access-Control"),
    (53, "TCP/UDP", "DNS", "Domain Name System"),
    (67, "UDP", "DHCP-Server", "DHCP server"),
    (68, "UDP", "DHCP-Client", "DHCP client"),
    (69, "UDP", "TFTP", "Trivial File Transfer Protocol"),
    (79, "TCP", "Finger", "Finger user information"),
    (80, "TCP", "HTTP", "Hypertext Transfer Protocol"),
    (88, "TCP/UDP", "Kerberos", "Kerberos authentication"),
    (110, "TCP", "POP3", "Post Office Protocol v3"),
    (111, "TCP/UDP", "RPCBind", "RPC port mapper"),
    (113, "TCP", "Ident", "Identification Protocol"),
    (119, "TCP", "NNTP", "Network News Transfer Protocol"),
    (123, "UDP", "NTP", "Network Time Protocol"),
    (135, "TCP", "MSRPC", "Microsoft RPC"),
    (137, "UDP", "NetBIOS-NS", "NetBIOS Name Service"),
    (138, "UDP", "NetBIOS-DGM", "NetBIOS Datagram Service"),
    (139, "TCP", "NetBIOS-SSN", "NetBIOS Session Service"),
    (143, "TCP", "IMAP", "Internet Message Access Protocol"),
    (161, "UDP", "SNMP", "Simple Network Management Protocol"),
    (162, "UDP", "SNMP-Trap", "SNMP trap"),
    (179, "TCP", "BGP", "Border Gateway Protocol"),
    (194, "TCP", "IRC", "Internet Relay Chat"),
    (201, "TCP", "AppleTalk", "AppleTalk routing"),
    (264, "TCP", "BGMP", "Border Gateway Multicast Protocol"),
    (389, "TCP", "LDAP", "Lightweight Directory Access Protocol"),
    (443, "TCP", "HTTPS", "HTTP over TLS/SSL"),
    (445, "TCP", "SMB", "Server Message Block / Microsoft-DS"),
    (465, "TCP", "SMTPS", "SMTP over SSL (deprecated)"),
    (500, "UDP", "IKE", "Internet Key Exchange (IPSec)"),
    (514, "UDP", "Syslog", "System logging"),
    (515, "TCP", "LPD", "Line Printer Daemon"),
    (520, "UDP", "RIP", "Routing Information Protocol"),
    (523, "TCP", "IBM-DB2", "IBM DB2 discovery"),
    (530, "TCP", "RPC", "Remote Procedure Call"),
    (548, "TCP", "AFP", "Apple Filing Protocol"),
    (554, "TCP", "RTSP", "Real Time Streaming Protocol"),
    (587, "TCP", "SMTP-Sub", "SMTP message submission"),
    (593, "TCP", "HTTP-RPC", "HTTP RPC endpoint mapper"),
    (623, "UDP", "IPMI", "Intelligent Platform Management Interface"),
    (636, "TCP", "LDAPS", "LDAP over SSL"),
    (873, "TCP", "Rsync", "Rsync file synchronization"),
    (902, "TCP", "VMware", "VMware ESXi/vSphere"),
    (993, "TCP", "IMAPS", "IMAP over SSL"),
    (995, "TCP", "POP3S", "POP3 over SSL"),
    (1080, "TCP", "SOCKS", "SOCKS proxy"),
    (1099, "TCP", "Java-RMI", "Java Remote Method Invocation"),
    (1433, "TCP", "MSSQL", "Microsoft SQL Server"),
    (1434, "UDP", "MSSQL-Browser", "MS SQL Server Browser"),
    (1521, "TCP", "Oracle", "Oracle database listener"),
    (1723, "TCP", "PPTP", "Point-to-Point Tunneling Protocol"),
    (1883, "TCP", "MQTT", "Message Queuing Telemetry Transport"),
    (2049, "TCP/UDP", "NFS", "Network File System"),
    (2181, "TCP", "ZooKeeper", "Apache ZooKeeper"),
    (2375, "TCP", "Docker", "Docker REST API (unencrypted)"),
    (2376, "TCP", "Docker-TLS", "Docker REST API (TLS)"),
    (3268, "TCP", "LDAP-GC", "LDAP Global Catalog"),
    (3306, "TCP", "MySQL", "MySQL database"),
    (3389, "TCP", "RDP", "Remote Desktop Protocol"),
    (3690, "TCP", "SVN", "Subversion"),
    (4443, "TCP", "HTTPS-Alt", "HTTPS alternate"),
    (4505, "TCP", "SaltStack", "SaltStack publish"),
    (4506, "TCP", "SaltStack-Ret", "SaltStack return"),
    (5000, "TCP", "UPnP", "Universal Plug and Play / Flask dev"),
    (5432, "TCP", "PostgreSQL", "PostgreSQL database"),
    (5672, "TCP", "AMQP", "Advanced Message Queuing Protocol"),
    (5900, "TCP", "VNC", "Virtual Network Computing"),
    (5985, "TCP", "WinRM-HTTP", "Windows Remote Management HTTP"),
    (5986, "TCP", "WinRM-HTTPS", "Windows Remote Management HTTPS"),
    (6379, "TCP", "Redis", "Redis key-value store"),
    (6667, "TCP", "IRC", "Internet Relay Chat (alternate)"),
    (8000, "TCP", "HTTP-Alt", "HTTP alternate (dev servers)"),
    (8080, "TCP", "HTTP-Proxy", "HTTP proxy / alternate"),
    (8443, "TCP", "HTTPS-Alt", "HTTPS alternate"),
    (8888, "TCP", "HTTP-Alt2", "HTTP alternate (Jupyter, etc.)"),
    (9090, "TCP", "WebSM", "Web management console"),
    (9200, "TCP", "Elasticsearch", "Elasticsearch REST API"),
    (9300, "TCP", "Elasticsearch-T", "Elasticsearch transport"),
    (11211, "TCP/UDP", "Memcached", "Memcached caching system"),
    (27017, "TCP", "MongoDB", "MongoDB database"),
    (27018, "TCP", "MongoDB-Shard", "MongoDB shard server"),
    (50000, "TCP", "SAP", "SAP Management Console"),
    (50070, "TCP", "HDFS", "Hadoop HDFS NameNode web UI"),
]


def run(console: Console) -> None:
    """Look up common ports by number or service name."""
    console.print("\n[bold cyan]Port Reference Lookup[/bold cyan]\n")

    query = inquirer.text(message="Search by port number or service name:").execute()
    if not query:
        console.print("[red]No query provided.[/red]")
        return

    query = query.strip()
    results: list[tuple[int, str, str, str]] = []

    if query.isdigit():
        port_num = int(query)
        results = [p for p in PORTS if p[0] == port_num]
    else:
        q_lower = query.lower()
        results = [
            p for p in PORTS
            if q_lower in p[2].lower() or q_lower in p[3].lower()
        ]

    if not results:
        console.print(f"[yellow]No matches for '{query}'.[/yellow]")
        return

    table = Table(title="Port Reference")
    table.add_column("Port", style="cyan", justify="right")
    table.add_column("Protocol", style="blue")
    table.add_column("Service", style="green")
    table.add_column("Description", style="white")

    for port, proto, svc, desc in results:
        table.add_row(str(port), proto, svc, desc)

    console.print(table)
