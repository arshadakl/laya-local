"""Whitelist-based action dispatcher.

Takes classified intents and routes them to the appropriate
action handler. Only pre-registered actions can be executed.
"""

from __future__ import annotations

from typing import Any

import structlog

from laya_local.actions.registry import ActionRegistry
from laya_local.config import ActionsConfig

log = structlog.get_logger()


class Executor:
    """Dispatches classified intents to whitelisted action handlers.

    Maintains an ActionRegistry with all allowed actions and routes
    incoming intents to the correct handler based on action type.

    Args:
        config: Actions configuration with custom action definitions.
    """

    def __init__(self, config: ActionsConfig) -> None:
        self._registry = ActionRegistry()
        self._register_builtin_actions()

        if config.custom:
            self._register_custom_actions(config.custom)

    def _register_builtin_actions(self) -> None:
        """Register all built-in action handlers."""
        from laya_local.actions.apps import close_application, open_application
        from laya_local.actions.browser import open_url, search_web
        from laya_local.actions.files import open_file, open_folder
        from laya_local.actions.media import execute_media_control
        from laya_local.actions.system import execute_system_control

        # App actions
        self._registry.register("open_app", open_application)
        self._registry.register("close_app", close_application)

        # Folder/file actions
        self._registry.register("open_folder", open_folder)
        self._registry.register("open_file", open_file)

        # Browser actions
        self._registry.register("open_url", open_url)
        self._registry.register("search", search_web)

        # System actions
        self._registry.register("system_control", execute_system_control)

        # Media actions
        self._registry.register("media", execute_media_control)

        log.info(
            "builtin_actions_registered",
            count=len(self._registry),
            actions=self._registry.registered_actions,
        )

    def _register_custom_actions(
        self, custom_config: dict[str, dict[str, str]]
    ) -> None:
        """Register user-defined custom actions from config.

        Args:
            custom_config: Custom action definitions from config.yaml.
        """
        from laya_local.actions.custom import load_custom_actions

        custom_actions = load_custom_actions(custom_config)

        for name, handler in custom_actions:
            self._registry.register(name, handler)

        log.info("custom_actions_registered", count=len(custom_actions))

    def execute(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Execute an action based on a classified intent.

        Args:
            intent: Classified intent from the Laya classifier.
                    Must contain "action" and "target" keys.

        Returns:
            Dictionary with execution status and details.
        """
        action = intent.get("action", "unknown")
        target = intent.get("target", "none")
        confidence = intent.get("confidence", 0.0)
        text = intent.get("text", "")

        log.info(
            "executing_intent",
            action=action,
            target=target,
            confidence=f"{confidence:.2f}",
            text=text,
        )

        handler = self._registry.get(action)

        if handler is None:
            log.warning("unregistered_action", action=action)
            return {
                "status": "error",
                "message": f"Unknown action: {action}",
            }

        try:
            result = handler(target=target)
            return result
        except Exception as exc:
            log.error("action_execution_failed", action=action, error=str(exc))
            return {
                "status": "error",
                "message": f"Execution failed: {exc}",
            }

    @property
    def available_actions(self) -> list[str]:
        """List all available action names.

        Returns:
            Sorted list of registered action names.
        """
        return self._registry.registered_actions
