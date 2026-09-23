"""Application launcher actions.

Maps friendly application names to their executable commands.
Only whitelisted applications can be launched.
"""

from __future__ import annotations

import subprocess
from typing import Any

import structlog

log = structlog.get_logger()

# ── Application command map ───────────────────────────────────────
# Only these applications can be launched (whitelist).
_APP_COMMANDS: dict[str, str] = {
    "chrome": "start chrome",
    "firefox": "start firefox",
    "edge": "start msedge",
    "vscode": "code",
    "code": "code",
    "terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "discord": "start discord",
    "spotify": "start spotify",
    "notepad": "notepad",
    "explorer": "explorer",
    "settings": "ms-settings:",
    "task_manager": "taskmgr",
    "calculator": "calc",
    "paint": "mspaint",
    "word": "start winword",
    "excel": "start excel",
    "powerpoint": "start powerpnt",
    "slack": "start slack",
    "teams": "start ms-teams",
    "zoom": "start zoom",
    "obs": "start obs64",
    "steam": "start steam",
}


def open_application(target: str, **kwargs: Any) -> dict[str, Any]:
    """Launch a whitelisted application.

    Args:
        target: Application identifier (e.g., "chrome", "vscode").
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    command = _APP_COMMANDS.get(target)

    if command is None:
        log.warning("unknown_app", target=target)
        return {
            "status": "error",
            "message": f"Unknown application: {target}",
        }

    log.info("launching_app", target=target, command=command)

    try:
        subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {
            "status": "success",
            "action": "open_app",
            "target": target,
            "message": f"Launched {target}",
        }
    except OSError as exc:
        log.error("app_launch_failed", target=target, error=str(exc))
        return {
            "status": "error",
            "message": f"Failed to launch {target}: {exc}",
        }


def close_application(target: str, **kwargs: Any) -> dict[str, Any]:
    """Close a running application by name.

    Args:
        target: Application name to close (e.g., "chrome", "discord").
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    # Map friendly names to process names
    process_names: dict[str, str] = {
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "vscode": "Code.exe",
        "code": "Code.exe",
        "terminal": "WindowsTerminal.exe",
        "discord": "Discord.exe",
        "spotify": "Spotify.exe",
        "notepad": "Notepad.exe",
        "slack": "Slack.exe",
        "teams": "Teams.exe",
        "obs": "obs64.exe",
        "steam": "steam.exe",
    }

    process_name = process_names.get(target)

    if process_name is None:
        log.warning("unknown_app_for_close", target=target)
        return {
            "status": "error",
            "message": f"Unknown application: {target}",
        }

    log.info("closing_app", target=target, process=process_name)

    try:
        result = subprocess.run(
            f"taskkill /IM {process_name} /F",
            shell=True,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "action": "close_app",
                "target": target,
                "message": f"Closed {target}",
            }
        return {
            "status": "warning",
            "action": "close_app",
            "target": target,
            "message": f"{target} may not be running",
        }
    except OSError as exc:
        log.error("app_close_failed", target=target, error=str(exc))
        return {
            "status": "error",
            "message": f"Failed to close {target}: {exc}",
        }


def get_available_apps() -> list[str]:
    """List all available application identifiers.

    Returns:
        Sorted list of app names that can be launched.
    """
    return sorted(_APP_COMMANDS.keys())
