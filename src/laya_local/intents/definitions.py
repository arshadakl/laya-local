"""Laya question schemas for command intent classification.

Defines the structured questions that Laya evaluates to determine
what action the user wants to perform.
"""

from __future__ import annotations

from typing import Any


# ── Action categories ─────────────────────────────────────────────
ACTION_CRITERIA: dict[str, str] = {
    "open_app": "Open or launch an application",
    "close_app": "Close or quit an application",
    "open_folder": "Open a folder or directory",
    "open_url": "Open a website or URL in the browser",
    "search": "Search the web or local files",
    "system_control": "System operations: shutdown, restart, lock, sleep, volume, brightness",
    "media": "Media playback: play, pause, next, previous, volume",
    "type_text": "Type or dictate text",
    "unknown": "None of the above or unclear intent",
}

# ── Application targets ───────────────────────────────────────────
APP_TARGET_CRITERIA: dict[str, str] = {
    "chrome": "Google Chrome browser",
    "firefox": "Mozilla Firefox browser",
    "edge": "Microsoft Edge browser",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code (alias)",
    "terminal": "Windows Terminal or command prompt",
    "cmd": "Windows Command Prompt",
    "powershell": "Windows PowerShell",
    "discord": "Discord chat application",
    "spotify": "Spotify music player",
    "notepad": "Notepad text editor",
    "explorer": "Windows File Explorer",
    "file_manager": "File manager or explorer",
    "settings": "Windows Settings",
    "task_manager": "Windows Task Manager",
    "calculator": "Calculator app",
    "paint": "Microsoft Paint",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "slack": "Slack messaging app",
    "teams": "Microsoft Teams",
    "zoom": "Zoom video conferencing",
    "obs": "OBS Studio",
    "steam": "Steam gaming platform",
    "unknown_app": "Unknown or other application",
}

# ── Folder targets ────────────────────────────────────────────────
FOLDER_TARGET_CRITERIA: dict[str, str] = {
    "downloads": "Downloads folder",
    "documents": "Documents folder",
    "desktop": "Desktop folder",
    "pictures": "Pictures folder",
    "music": "Music folder",
    "videos": "Videos folder",
    "home": "User home directory",
    "project": "A project or code directory",
    "unknown_folder": "Unknown or other folder",
}

# ── System control targets ────────────────────────────────────────
SYSTEM_TARGET_CRITERIA: dict[str, str] = {
    "shutdown": "Shut down the computer",
    "restart": "Restart the computer",
    "lock": "Lock the computer screen",
    "sleep": "Put computer to sleep",
    "hibernate": "Hibernate the computer",
    "volume_up": "Increase system volume",
    "volume_down": "Decrease system volume",
    "mute": "Mute or unmute audio",
    "brightness_up": "Increase screen brightness",
    "brightness_down": "Decrease screen brightness",
    "unknown_system": "Unknown system control",
}

# ── Media targets ─────────────────────────────────────────────────
MEDIA_TARGET_CRITERIA: dict[str, str] = {
    "play_pause": "Play or pause current media",
    "next_track": "Skip to next track",
    "previous_track": "Go to previous track",
    "volume_up": "Increase media volume",
    "volume_down": "Decrease media volume",
    "stop": "Stop media playback",
    "unknown_media": "Unknown media control",
}


def build_questions() -> dict[str, Any]:
    """Build the complete Laya question schema for command classification.

    Returns:
        Dictionary of questions for Laya predict().
    """
    return {
        "action": {
            "type": "choice",
            "instructions": "What action does the user want to perform?",
            "criteria": ACTION_CRITERIA,
        },
        "app_target": {
            "type": "choice",
            "instructions": "Which application does the user want to open or interact with?",
            "criteria": APP_TARGET_CRITERIA,
        },
        "folder_target": {
            "type": "choice",
            "instructions": "Which folder does the user want to open?",
            "criteria": FOLDER_TARGET_CRITERIA,
        },
        "system_target": {
            "type": "choice",
            "instructions": "Which system control does the user want?",
            "criteria": SYSTEM_TARGET_CRITERIA,
        },
        "media_target": {
            "type": "choice",
            "instructions": "Which media control does the user want?",
            "criteria": MEDIA_TARGET_CRITERIA,
        },
    }


# Legacy alias for backward compatibility
COMMAND_QUESTIONS = build_questions()
