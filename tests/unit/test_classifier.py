"""Unit tests for the Laya classifier."""

from __future__ import annotations

from laya_local.intents.definitions import (
    ACTION_CRITERIA,
    APP_TARGET_CRITERIA,
    COMMAND_QUESTIONS,
    build_questions,
)


class TestIntentDefinitions:
    """Tests for intent schema definitions."""

    def test_action_criteria_not_empty(self) -> None:
        assert len(ACTION_CRITERIA) > 0
        assert "open_app" in ACTION_CRITERIA
        assert "unknown" in ACTION_CRITERIA

    def test_app_target_criteria_not_empty(self) -> None:
        assert len(APP_TARGET_CRITERIA) > 0
        assert "chrome" in APP_TARGET_CRITERIA

    def test_build_questions_returns_all_categories(self) -> None:
        questions = build_questions()
        assert "action" in questions
        assert "app_target" in questions
        assert "folder_target" in questions
        assert "system_target" in questions
        assert "media_target" in questions

    def test_command_questions_matches_build_questions(self) -> None:
        assert build_questions() == COMMAND_QUESTIONS

    def test_all_questions_have_required_fields(self) -> None:
        questions = build_questions()
        for name, question in questions.items():
            assert "type" in question, f"Missing 'type' in {name}"
            assert "instructions" in question, f"Missing 'instructions' in {name}"
            assert "criteria" in question, f"Missing 'criteria' in {name}"
            assert question["type"] == "choice"
