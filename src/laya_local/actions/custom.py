"""Custom user-defined actions.

Loads custom actions from config.yaml and registers them.
Custom actions can run shell commands or open specific paths.
"""

from __future__ import annotations

import subprocess
from typing import Any

import structlog

log = structlog.get_logger()


def create_custom_handler(
    command: str | None = None,
    path: str | None = None,
) -> Any:
    """Create a handler function for a custom action.

    Args:
        command: Shell command to execute (optional).
        path: File/folder path to open (optional).

    Returns:
        Action handler function.
    """

    def handler(**kwargs: Any) -> dict[str, Any]:
        if command:
            log.info("custom_command", command=command)
            try:
                subprocess.Popen(  # noqa: S603
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return {
                    "status": "success",
                    "action": "custom",
                    "message": f"Executed: {command}",
                }
            except OSError as exc:
                return {
                    "status": "error",
                    "message": f"Failed: {exc}",
                }

        if path:
            import os

            log.info("custom_path", path=path)
            try:
                os.startfile(path)  # type: ignore[attr-defined]
                return {
                    "status": "success",
                    "action": "custom",
                    "message": f"Opened: {path}",
                }
            except OSError as exc:
                return {
                    "status": "error",
                    "message": f"Failed: {exc}",
                }

        return {
            "status": "error",
            "message": "Custom action has no command or path",
        }

    return handler


def load_custom_actions(
    custom_config: dict[str, dict[str, str]],
) -> list[tuple[str, Any]]:
    """Load custom actions from configuration.

    Args:
        custom_config: Dictionary of custom action definitions from config.yaml.

    Returns:
        List of (name, handler) tuples ready for registration.
    """
    actions: list[tuple[str, Any]] = []

    for name, definition in custom_config.items():
        command = definition.get("command")
        path = definition.get("path")

        if not command and not path:
            log.warning("custom_action_no_target", name=name)
            continue

        handler = create_custom_handler(command=command, path=path)
        actions.append((name, handler))
        log.debug("custom_action_loaded", name=name)

    return actions
