"""Shared test fixtures for laya-local."""

from __future__ import annotations

import pytest

from laya_local.config import (
    ActionsConfig,
    AppConfig,
    LayaConfig,
    ListenerConfig,
    TTSConfig,
    WhisperConfig,
)


@pytest.fixture
def default_config() -> AppConfig:
    """Provide a default AppConfig for testing."""
    return AppConfig()


@pytest.fixture
def whisper_config() -> WhisperConfig:
    """Provide Whisper config for testing."""
    return WhisperConfig(model="tiny", device="cpu")


@pytest.fixture
def laya_config() -> LayaConfig:
    """Provide Laya config for testing."""
    return LayaConfig(device="cpu")


@pytest.fixture
def tts_config() -> TTSConfig:
    """Provide TTS config for testing (disabled)."""
    return TTSConfig(enabled=False)


@pytest.fixture
def listener_config() -> ListenerConfig:
    """Provide listener config for testing."""
    return ListenerConfig(trigger_key="ctrl", sample_rate=16000)


@pytest.fixture
def actions_config() -> ActionsConfig:
    """Provide actions config for testing."""
    return ActionsConfig()
