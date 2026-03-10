import os
import subprocess
import platform


def notify(title: str, message: str):
    """Send a desktop notification. No dependencies required."""
    try:
        from sectools.config import load_config
        if not load_config().get("notifications_enabled", True):
            return
    except Exception:
        pass
    system = platform.system()
    try:
        if system == "Darwin":
            safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
            safe_message = message.replace('\\', '\\\\').replace('"', '\\"')
            subprocess.run([
                "osascript", "-e",
                f'display notification "{safe_message}" with title "{safe_title}"',
            ], check=False, capture_output=True)
        elif system == "Linux":
            subprocess.run(["notify-send", title, message], check=False, capture_output=True)
        elif system == "Windows":
            safe_title = title.replace("'", "''")
            safe_message = message.replace("'", "''")
            subprocess.run([
                "powershell", "-Command",
                f"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                f"$n = New-Object System.Windows.Forms.NotifyIcon; "
                f"$n.Icon = [System.Drawing.SystemIcons]::Information; "
                f"$n.Visible = $true; "
                f"$n.ShowBalloonTip(5000, '{safe_title}', '{safe_message}', 'Info')",
            ], check=False, capture_output=True)
    except Exception:
        pass
