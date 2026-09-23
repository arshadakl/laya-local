"""Unit tests for the hybrid command matcher."""

from __future__ import annotations

import pytest

from laya_local.core.matcher import CommandMatcher


class TestCommandMatcher:
    """Tests for deterministic command matching."""

    @pytest.fixture(autouse=True)
    def _matcher(self) -> None:
        self.matcher = CommandMatcher()

    def test_english_open_app(self) -> None:
        result = self.matcher.match("Open Chrome")
        assert result is not None
        assert result["action"] == "open_app"
        assert result["target"] == "chrome"
        assert result["confidence"] > 0.9

    def test_malayalam_open_app(self) -> None:
        result = self.matcher.match("Chrome തുറക്കൂ")
        assert result is not None
        assert result["action"] == "open_app"
        assert result["target"] == "chrome"

    def test_manglish_open_app(self) -> None:
        result = self.matcher.match("Chrome thurakku")
        assert result is not None
        assert result["action"] == "open_app"
        assert result["target"] == "chrome"

    def test_manglish_open_cheyy(self) -> None:
        result = self.matcher.match("Spotify open cheyy")
        assert result is not None
        assert result["action"] == "open_app"
        assert result["target"] == "spotify"

    def test_open_folder(self) -> None:
        result = self.matcher.match("Open Downloads")
        assert result is not None
        assert result["action"] == "open_folder"
        assert result["target"] == "downloads"

    def test_malayalam_folder(self) -> None:
        result = self.matcher.match("downloads തുറക്കൂ")
        assert result is not None
        assert result["action"] == "open_folder"
        assert result["target"] == "downloads"

    def test_shutdown(self) -> None:
        result = self.matcher.match("Shutdown")
        assert result is not None
        assert result["action"] == "system_control"
        assert result["target"] == "shutdown"

    def test_manglish_lock(self) -> None:
        result = self.matcher.match("lock cheyy")
        assert result is not None
        assert result["action"] == "system_control"
        assert result["target"] == "lock"

    def test_malayalam_volume_down(self) -> None:
        result = self.matcher.match("ശബ്ദം കുറയ്ക്കൂ")
        assert result is not None
        assert result["action"] == "system_control"
        assert result["target"] == "volume_down"

    def test_volume_manglish(self) -> None:
        result = self.matcher.match("volume kootu")
        assert result is not None
        assert result["action"] == "system_control"
        assert result["target"] == "volume_up"

    def test_media_play(self) -> None:
        result = self.matcher.match("Play music")
        assert result is not None
        assert result["action"] == "media"
        assert result["target"] == "play_pause"

    def test_media_next(self) -> None:
        result = self.matcher.match("Next song")
        assert result is not None
        assert result["action"] == "media"
        assert result["target"] == "next_track"

    def test_no_match_falls_through(self) -> None:
        assert self.matcher.match("random sentence") is None

    def test_empty_input(self) -> None:
        assert self.matcher.match("") is None
        assert self.matcher.match("   ") is None

    def test_rules_are_registered(self) -> None:
        assert self.matcher.rule_count > 20
