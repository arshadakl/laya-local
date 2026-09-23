"""Unit tests for the action system."""

from __future__ import annotations

from typing import Any

import pytest

from laya_local.actions.apps import get_available_apps
from laya_local.actions.files import get_known_folders
from laya_local.actions.registry import ActionRegistry
from laya_local.config import ActionsConfig
from laya_local.core.executor import Executor


class TestActionRegistry:
    """Tests for the ActionRegistry class."""

    def test_register_and_get(self) -> None:
        registry = ActionRegistry()

        def dummy(**kwargs: Any) -> dict[str, Any]:
            return {"status": "success"}

        registry.register("test_action", dummy)
        assert registry.has("test_action")
        assert registry.get("test_action") is dummy

    def test_get_unknown_returns_none(self) -> None:
        registry = ActionRegistry()
        assert registry.get("nonexistent") is None

    def test_register_duplicate_raises(self) -> None:
        registry = ActionRegistry()

        def dummy(**kwargs: Any) -> dict[str, Any]:
            return {"status": "success"}

        registry.register("test", dummy)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", dummy)

    def test_registered_actions_sorted(self) -> None:
        registry = ActionRegistry()

        def dummy(**kwargs: Any) -> dict[str, Any]:
            return {"status": "success"}

        registry.register("zebra", dummy)
        registry.register("alpha", dummy)
        registry.register("middle", dummy)

        assert registry.registered_actions == ["alpha", "middle", "zebra"]

    def test_len(self) -> None:
        registry = ActionRegistry()
        assert len(registry) == 0

        def dummy(**kwargs: Any) -> dict[str, Any]:
            return {"status": "success"}

        registry.register("a", dummy)
        assert len(registry) == 1


class TestApps:
    """Tests for application launcher."""

    def test_available_apps_not_empty(self) -> None:
        apps = get_available_apps()
        assert len(apps) > 0
        assert "chrome" in apps
        assert "vscode" in apps

    def test_available_apps_sorted(self) -> None:
        apps = get_available_apps()
        assert apps == sorted(apps)


class TestFiles:
    """Tests for folder opener."""

    def test_known_folders_not_empty(self) -> None:
        folders = get_known_folders()
        assert len(folders) > 0
        assert "downloads" in folders
        assert "home" in folders


class TestExecutor:
    """Tests for the Executor dispatcher."""

    def test_executor_registers_builtin_actions(self) -> None:
        config = ActionsConfig()
        executor = Executor(config)

        assert "open_app" in executor.available_actions
        assert "close_app" in executor.available_actions
        assert "open_folder" in executor.available_actions
        assert "system_control" in executor.available_actions
        assert "media" in executor.available_actions

    def test_execute_unknown_action_returns_error(self) -> None:
        config = ActionsConfig()
        executor = Executor(config)

        result = executor.execute({"action": "nonexistent", "target": "test"})
        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    def test_execute_with_missing_action_defaults_to_unknown(self) -> None:
        config = ActionsConfig()
        executor = Executor(config)

        result = executor.execute({})
        assert result["status"] == "error"
