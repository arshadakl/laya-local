"""Media playback control actions.

Play/pause, next/previous track, and volume controls for media.
"""

from __future__ import annotations

from typing import Any

import pyautogui
import structlog

log = structlog.get_logger()


def play_pause(**kwargs: Any) -> dict[str, Any]:
    """Toggle media play/pause.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("media_play_pause")
    pyautogui.press("playpause")
    return {
        "status": "success",
        "action": "media",
        "target": "play_pause",
        "message": "Play/pause toggled",
    }


def next_track(**kwargs: Any) -> dict[str, Any]:
    """Skip to next track.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("media_next")
    pyautogui.press("nexttrack")
    return {
        "status": "success",
        "action": "media",
        "target": "next_track",
        "message": "Next track",
    }


def previous_track(**kwargs: Any) -> dict[str, Any]:
    """Go to previous track.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("media_previous")
    pyautogui.press("prevtrack")
    return {
        "status": "success",
        "action": "media",
        "target": "previous_track",
        "message": "Previous track",
    }


def media_volume_up(**kwargs: Any) -> dict[str, Any]:
    """Increase media volume.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("media_volume_up")
    pyautogui.press("volumeup")
    return {
        "status": "success",
        "action": "media",
        "target": "volume_up",
        "message": "Media volume increased",
    }


def media_volume_down(**kwargs: Any) -> dict[str, Any]:
    """Decrease media volume.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("media_volume_down")
    pyautogui.press("volumedown")
    return {
        "status": "success",
        "action": "media",
        "target": "volume_down",
        "message": "Media volume decreased",
    }


def stop_media(**kwargs: Any) -> dict[str, Any]:
    """Stop media playback.

    Args:
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    log.info("media_stop")
    pyautogui.press("stop")
    return {
        "status": "success",
        "action": "media",
        "target": "stop",
        "message": "Media stopped",
    }


# ── Media action map ──────────────────────────────────────────────
MEDIA_ACTIONS: dict[str, Any] = {
    "play_pause": play_pause,
    "next_track": next_track,
    "previous_track": previous_track,
    "volume_up": media_volume_up,
    "volume_down": media_volume_down,
    "stop": stop_media,
}


def execute_media_control(target: str, **kwargs: Any) -> dict[str, Any]:
    """Execute a media control action by target name.

    Args:
        target: Media control target name.
        **kwargs: Additional arguments passed to the handler.

    Returns:
        Dictionary with status and details.
    """
    handler = MEDIA_ACTIONS.get(target)

    if handler is None:
        log.warning("unknown_media_action", target=target)
        return {
            "status": "error",
            "message": f"Unknown media action: {target}",
        }

    return handler(**kwargs)
