"""Windows platform-specific utilities."""

from __future__ import annotations

import subprocess
import sys


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        True if the current platform is Windows.
    """
    return sys.platform == "win32"


def run_command(command: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the result.

    Args:
        command: The command string to execute.
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        CompletedProcess instance with stdout/stderr.
    """
    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        check=check,
    )


def open_file(path: str) -> subprocess.Popen[str]:
    """Open a file with the default application (Windows only).

    Args:
        path: Path to the file or URL.

    Returns:
        Popen instance for the launched process.
    """
    return subprocess.Popen(  # noqa: S603
        ["cmd", "/c", "start", "", path],  # noqa: S607
        shell=False,
    )
