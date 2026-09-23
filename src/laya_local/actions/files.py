"""Folder and file opening actions.

Opens known system folders and arbitrary file paths.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

# ── Known folder paths ────────────────────────────────────────────
_KNOWN_FOLDERS: dict[str, str] = {
    "downloads": str(Path.home() / "Downloads"),
    "documents": str(Path.home() / "Documents"),
    "desktop": str(Path.home() / "Desktop"),
    "pictures": str(Path.home() / "Pictures"),
    "music": str(Path.home() / "Music"),
    "videos": str(Path.home() / "Videos"),
    "home": str(Path.home()),
}


def open_folder(target: str, **kwargs: Any) -> dict[str, Any]:
    """Open a known folder or arbitrary path.

    Args:
        target: Folder identifier (e.g., "downloads") or a path string.
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    # Check known folders first
    folder_path = _KNOWN_FOLDERS.get(target)

    # If not a known folder, treat as a path
    if folder_path is None:
        folder_path = target

    if not Path(folder_path).is_dir():
        log.warning("folder_not_found", target=target, path=folder_path)
        return {
            "status": "error",
            "message": f"Folder not found: {folder_path}",
        }

    log.info("opening_folder", target=target, path=folder_path)

    try:
        subprocess.Popen(
            ["explorer", folder_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {
            "status": "success",
            "action": "open_folder",
            "target": target,
            "path": folder_path,
            "message": f"Opened {folder_path}",
        }
    except OSError as exc:
        log.error("folder_open_failed", target=target, error=str(exc))
        return {
            "status": "error",
            "message": f"Failed to open folder: {exc}",
        }


def open_file(file_path: str, **kwargs: Any) -> dict[str, Any]:
    """Open a file with the default application.

    Args:
        file_path: Path to the file to open.
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    if not Path(file_path).is_file():
        log.warning("file_not_found", path=file_path)
        return {
            "status": "error",
            "message": f"File not found: {file_path}",
        }

    log.info("opening_file", path=file_path)

    try:
        os.startfile(file_path)  # type: ignore[attr-defined]
        return {
            "status": "success",
            "action": "open_file",
            "path": file_path,
            "message": f"Opened {file_path}",
        }
    except OSError as exc:
        log.error("file_open_failed", path=file_path, error=str(exc))
        return {
            "status": "error",
            "message": f"Failed to open file: {exc}",
        }


def get_known_folders() -> dict[str, str]:
    """List all known folder identifiers and their paths.

    Returns:
        Dictionary mapping folder names to paths.
    """
    return dict(_KNOWN_FOLDERS)
