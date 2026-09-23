"""Unit tests for the fine-tuning dataset builder."""

from __future__ import annotations

import json

from scripts.finetune.dataset_builder import (
    _build_item,
    _expand_template,
    generate_items,
)


class TestDatasetBuilder:
    """Tests for dataset generation."""

    def test_expand_template(self) -> None:
        result = _expand_template("open {app}", {"app": "chrome"})
        assert result == "open chrome"

    def test_build_item_includes_action(self) -> None:
        item = _build_item("open_app", "open chrome", "chrome")
        assert item["state"]["body"] == "open chrome"
        assert item["targets"]["action"]["choice"] == "open_app"
        assert item["targets"]["app_target"]["choice"] == "chrome"

    def test_build_item_includes_questions(self) -> None:
        item = _build_item("media", "play music")
        questions = item["questions"]
        assert "action" in questions
        assert "app_target" in questions

    def test_generate_items_are_json_serializable(self) -> None:
        items = generate_items(variations=1, seed=1)
        assert len(items) > 100
        for item in items:
            json.dumps(item, ensure_ascii=False)  # must not raise

    def test_generate_items_cover_all_actions(self) -> None:
        items = generate_items(variations=1, seed=1)
        actions = {item["targets"]["action"]["choice"] for item in items}
        assert "open_app" in actions
        assert "open_folder" in actions
        assert "system_control" in actions
        assert "media" in actions

    def test_generate_items_deterministic(self) -> None:
        a = generate_items(variations=2, seed=7)
        b = generate_items(variations=2, seed=7)
        assert a == b
