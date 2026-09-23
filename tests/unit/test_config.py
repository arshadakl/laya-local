"""Unit tests for the configuration module."""

from __future__ import annotations

from pathlib import Path

import pytest

from laya_local.config import (
    AppConfig,
    load_config,
)


class TestAppConfig:
    """Tests for AppConfig dataclass defaults."""

    def test_default_config_creates_valid_instance(self) -> None:
        config = AppConfig()
        assert config.whisper.model == "small"
        assert config.whisper.device == "cpu"
        assert config.laya.model == "convaiinnovations/laya-multilingual"
        assert config.tts.enabled is False
        assert config.listener.trigger_key == "right ctrl"
        assert config.listener.sample_rate == 16000
        assert config.actions.custom == {}
        assert config.actions.confirm_destructive is True

    def test_config_is_frozen(self) -> None:
        config = AppConfig()
        with pytest.raises(AttributeError):
            config.whisper = None  # type: ignore[assignment]


class TestLoadConfig:
    """Tests for YAML config loading."""

    def test_load_nonexistent_file_returns_defaults(self) -> None:
        config = load_config(Path("nonexistent.yaml"))
        assert isinstance(config, AppConfig)
        assert config.whisper.model == "small"

    def test_load_empty_yaml_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text("", encoding="utf-8")

        config = load_config(config_file)
        assert isinstance(config, AppConfig)

    def test_load_custom_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
whisper:
  model: "large-v3"
  device: "cuda"
tts:
  enabled: true
listener:
  trigger_key: "shift"
""",
            encoding="utf-8",
        )

        config = load_config(config_file)
        assert config.whisper.model == "large-v3"
        assert config.whisper.device == "cuda"
        assert config.tts.enabled is True
        assert config.listener.trigger_key == "shift"

    def test_load_config_ignores_unknown_keys(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
whisper:
  model: "base"
  unknown_key: "should be ignored"
""",
            encoding="utf-8",
        )

        config = load_config(config_file)
        assert config.whisper.model == "base"
