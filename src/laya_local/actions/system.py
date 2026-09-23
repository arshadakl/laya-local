"""System control actions.

Shutdown, restart, lock, sleep, volume, and brightness controls.
"""

from __future__ import annotations

import subprocess
from typing import Any

import structlog

log = structlog.get_logger()


def _run_powershell(command: str) -> dict[str, Any]:
    """Execute a PowerShell command for system control.

    Args:
        command: PowerShell command string.

    Returns:
        Dictionary with status and details.
    """
    try:
        result = subprocess.run(  # noqa: S603
            ["powershell", "-Command", command],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            return {"status": "success"}
        else:
            return {
                "status": "error",
                "message": result.stderr.strip() or "Command failed",
            }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Command timed out"}
    except OSError as exc:
        return {"status": "error", "message": str(exc)}


def shutdown_computer(target: str = "now", **kwargs: Any) -> dict[str, Any]:
    """Shut down the computer.

    Args:
        target: "now" for immediate, or minutes string like "5" for delayed.
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    if target == "now":
        cmd = "shutdown /s /t 0"
    else:
        cmd = f"shutdown /s /t {target}"

    log.info("shutting_down", target=target)
    result = _run_powershell(cmd)

    if result["status"] == "success":
        return {
            "status": "success",
            "action": "system_control",
            "target": "shutdown",
            "message": "Shutting down",
        }
    return result


def restart_computer(target: str = "now", **kwargs: Any) -> dict[str, Any]:
    """Restart the computer.

    Args:
        target: "now" for immediate, or minutes string like "5" for delayed.
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    if target == "now":
        cmd = "shutdown /r /t 0"
    else:
        cmd = f"shutdown /r /t {target}"

    log.info("restarting", target=target)
    result = _run_powershell(cmd)

    if result["status"] == "success":
        return {
            "status": "success",
            "action": "system_control",
            "target": "restart",
            "message": "Restarting",
        }
    return result


def lock_computer(**kwargs: Any) -> dict[str, Any]:
    """Lock the computer screen.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("locking_computer")
    result = _run_powershell("rundll32.exe user32.dll,LockWorkStation")

    if result["status"] == "success":
        return {
            "status": "success",
            "action": "system_control",
            "target": "lock",
            "message": "Computer locked",
        }
    return result


def sleep_computer(**kwargs: Any) -> dict[str, Any]:
    """Put the computer to sleep.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("sleeping_computer")
    result = _run_powershell("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    if result["status"] == "success":
        return {
            "status": "success",
            "action": "system_control",
            "target": "sleep",
            "message": "Computer sleeping",
        }
    return result


def volume_up(**kwargs: Any) -> Any:
    """Increase system volume by one step.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("volume_up")
    import pyautogui

    pyautogui.press("volumeup")
    return {
        "status": "success",
        "action": "system_control",
        "target": "volume_up",
        "message": "Volume increased",
    }


def volume_down(**kwargs: Any) -> Any:
    """Decrease system volume by one step.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("volume_down")
    import pyautogui

    pyautogui.press("volumedown")
    return {
        "status": "success",
        "action": "system_control",
        "target": "volume_down",
        "message": "Volume decreased",
    }


def mute(**kwargs: Any) -> Any:
    """Mute or unmute system audio.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("mute_toggle")
    import pyautogui

    pyautogui.press("volumemute")
    return {
        "status": "success",
        "action": "system_control",
        "target": "mute",
        "message": "Audio muted/unmuted",
    }


# ── System action map ─────────────────────────────────────────────
SYSTEM_ACTIONS: dict[str, Any] = {
    "shutdown": shutdown_computer,
    "restart": restart_computer,
    "lock": lock_computer,
    "sleep": sleep_computer,
    "hibernate": sleep_computer,  # Alias
    "volume_up": volume_up,
    "volume_down": volume_down,
    "mute": mute,
}


def execute_system_control(target: str, **kwargs: Any) -> dict[str, Any]:
    """Execute a system control action by target name.

    Args:
        target: System control target name.
        **kwargs: Additional arguments passed to the handler.

    Returns:
        Dictionary with status and details.
    """
    handler = SYSTEM_ACTIONS.get(target)

    if handler is None:
        log.warning("unknown_system_action", target=target)
        return {
            "status": "error",
            "message": f"Unknown system action: {target}",
        }

    return handler(target=target, **kwargs)
