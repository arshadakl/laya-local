"""Laya multilingual classifier for intent recognition.

Wraps the Laya decision engine to classify user commands
into structured intents across Malayalam, English, and Manglish.
"""

from __future__ import annotations

from typing import Any

import structlog

from laya_local.config import LayaConfig
from laya_local.core.matcher import CommandMatcher
from laya_local.intents.definitions import build_questions

log = structlog.get_logger()

# Confidence threshold below which we reject a classification
_CONFIDENCE_THRESHOLD = 0.40


class Classifier:
    """Hybrid intent classifier for multilingual commands.

    First tries a fast deterministic matcher for known commands, then
    falls back to the Laya multilingual model for novel phrasing.

    Args:
        config: Laya configuration settings.
    """

    def __init__(self, config: LayaConfig) -> None:
        self._config = config
        self._router: Any = None
        self._questions = build_questions()
        self._matcher = CommandMatcher()

    def _ensure_model(self) -> Any:
        """Lazy-load the Laya agent on first use.

        Uses the multilingual model directly (supports Malayalam + English)
        instead of the Router which may misroute non-Latin scripts.

        Returns:
            The loaded Laya agent instance.
        """
        if self._router is not None:
            return self._router

        import laya

        log.info(
            "loading_laya",
            model=self._config.model,
            device=self._config.device,
        )

        self._router = laya.load(
            "convaiinnovations/laya",
            subfolder="multilingual",
        )

        log.info("laya_ready")
        return self._router

    def classify(self, text: str) -> dict[str, str | float] | None:
        """Classify a text command into a structured intent.

        Tries the deterministic matcher first (fast + precise), then
        falls back to Laya for commands it does not recognize.

        Args:
            text: The user's command text.

        Returns:
            Dictionary with action, targets, and confidence, or None
            if classification confidence is too low.
        """
        if not text or not text.strip():
            return None

        # ── Fast path: deterministic matcher ──────────────────────
        matched = self._matcher.match(text)
        if matched is not None:
            log.info(
                "classified",
                source="matcher",
                action=matched["action"],
                target=matched["target"],
            )
            return matched

        # ── Slow path: Laya model ─────────────────────────────────
        log.debug("matcher_miss", text=text)
        return self._classify_with_laya(text)

    def _classify_with_laya(self, text: str) -> dict[str, str | float] | None:
        """Classify using the Laya model.

        Args:
            text: The user's command text.

        Returns:
            Intent dict or None if confidence is too low.
        """
        agent = self._ensure_model()

        state = {"body": text}

        result = agent.predict(state, self._questions)

        answers = result.get("answers", {})

        # Extract primary action
        action_answer = answers.get("action", {})
        action = action_answer.get("choice", "unknown")
        confidence = action_answer.get("confidence", 0.0)

        log.debug(
            "laya_result",
            action=action,
            confidence=f"{confidence:.2f}",
        )

        if confidence < _CONFIDENCE_THRESHOLD:
            log.info(
                "low_confidence",
                action=action,
                confidence=f"{confidence:.2f}",
                threshold=f"{_CONFIDENCE_THRESHOLD:.2f}",
            )
            return None

        # Build intent result
        intent: dict[str, str | float] = {
            "action": action,
            "confidence": confidence,
            "source": "laya",
            "text": text,
        }

        # Add target based on action type
        if action == "open_app":
            app_target = answers.get("app_target", {})
            intent["target"] = app_target.get("choice", "unknown_app")
            intent["target_confidence"] = app_target.get("confidence", 0.0)

        elif action == "open_folder":
            folder_target = answers.get("folder_target", {})
            intent["target"] = folder_target.get("choice", "unknown_folder")
            intent["target_confidence"] = folder_target.get("confidence", 0.0)

        elif action == "system_control":
            system_target = answers.get("system_target", {})
            intent["target"] = system_target.get("choice", "unknown_system")
            intent["target_confidence"] = system_target.get("confidence", 0.0)

        elif action == "media":
            media_target = answers.get("media_target", {})
            intent["target"] = media_target.get("choice", "unknown_media")
            intent["target_confidence"] = media_target.get("confidence", 0.0)

        else:
            intent["target"] = "none"

        return intent

    def classify_with_raw(self, text: str) -> dict[str, Any] | None:
        """Classify with full Laya response for debugging.

        Args:
            text: The user's command text.

        Returns:
            Full Laya result with all answers and routing info, or None.
        """
        if not text or not text.strip():
            return None

        router = self._ensure_model()
        state = {"body": text}
        return router.predict(state, self._questions)
