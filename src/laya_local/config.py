"""Configuration loader for laya-local.

Loads settings from config.yaml with sensible defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


_CONFIG_FILENAME = "config.yaml"
_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / _CONFIG_FILENAME


@dataclass(frozen=True)
class WhisperConfig:
    """Speech-to-text configuration."""

    model: str = "small"
    device: str = "cpu"
    language: str | None = None


@dataclass(frozen=True)
class LayaConfig:
    """Laya classification engine configuration."""

    model: str = "convaiinnovations/laya-multilingual"
    device: str = "auto"
    max_loaded: int = 1


@dataclass(frozen=True)
class TTSConfig:
    """Text-to-speech configuration."""

    enabled: bool = False
    language: str = "en"
    model: str = "en_US-lessac-medium"


@dataclass(frozen=True)
class ListenerConfig:
    """Microphone listener configuration."""

    trigger_key: str = "ctrl"
    sample_rate: int = 16000
    channels: int = 1
    silence_threshold: int = 500
    max_duration: int = 10


@dataclass(frozen=True)
class ActionsConfig:
    """Action system configuration."""

    custom: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    """Root application configuration."""

    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    laya: LayaConfig = field(default_factory=LayaConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    listener: ListenerConfig = field(default_factory=ListenerConfig)
    actions: ActionsConfig = field(default_factory=ActionsConfig)


def _merge_dataclass(cls: type, data: dict[str, object]) -> object:
    """Create a dataclass instance from a dict, ignoring unknown keys."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    return cls(**filtered)


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from a YAML file.

    If the file does not exist or is empty, returns default config.

    Args:
        path: Path to config.yaml. Defaults to project root config.yaml.

    Returns:
        Fully populated AppConfig instance.
    """
    config_path = path or _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        return AppConfig()

    raw = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}

    return AppConfig(
        whisper=_merge_dataclass(WhisperConfig, data.get("whisper", {})),
        laya=_merge_dataclass(LayaConfig, data.get("laya", {})),
        tts=_merge_dataclass(TTSConfig, data.get("tts", {})),
        listener=_merge_dataclass(ListenerConfig, data.get("listener", {})),
        actions=_merge_dataclass(ActionsConfig, data.get("actions", {})),
    )
