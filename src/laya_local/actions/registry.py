"""Action registry for command execution.

Provides a central registry mapping action names to handler functions.
All actions are whitelisted — no arbitrary command execution.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import structlog

log = structlog.get_logger()

# Type alias for action handler functions
ActionHandler = Callable[..., dict[str, Any]]


class ActionRegistry:
    """Registry of whitelisted action handlers.

    Actions are registered by name and looked up during execution.
    Only pre-registered actions can be executed (whitelist model).
    """

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, name: str, handler: ActionHandler) -> None:
        """Register an action handler.

        Args:
            name: Action name (e.g., "open_app", "shutdown").
            handler: Callable that executes the action.

        Raises:
            ValueError: If the name is already registered.
        """
        if name in self._handlers:
            raise ValueError(f"Action already registered: {name}")

        self._handlers[name] = handler
        log.debug("action_registered", name=name)

    def get(self, name: str) -> ActionHandler | None:
        """Look up an action handler by name.

        Args:
            name: Action name to look up.

        Returns:
            The handler function, or None if not found.
        """
        return self._handlers.get(name)

    def has(self, name: str) -> bool:
        """Check if an action is registered.

        Args:
            name: Action name to check.

        Returns:
            True if the action is registered.
        """
        return name in self._handlers

    @property
    def registered_actions(self) -> list[str]:
        """List all registered action names.

        Returns:
            Sorted list of registered action names.
        """
        return sorted(self._handlers.keys())

    def __len__(self) -> int:
        """Return the number of registered actions."""
        return len(self._handlers)

    def __repr__(self) -> str:
        """Return a string representation of the registry."""
        return f"ActionRegistry(actions={self.registered_actions})"
