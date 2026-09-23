"""Fast rule-based command matcher.

Handles the common case (known commands in Malayalam, English, or Manglish)
with high precision, before falling back to the slower Laya classifier for
novel phrasing.

This is the reliability layer: the base Laya model is only ~40% accurate
zero-shot, so deterministic matching carries the bulk of real usage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger()


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for matching."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u0d00-\u0d7f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Action verbs per language (Manglish tokens included)
_OPEN_VERBS = (
    "open",
    "launch",
    "start",
    "run",
    "thurakku",
    "thurakkoo",
    "turakku",
    "തുറക്ക",
    "തുറക്കൂ",
    "തുറക്കു",
    "open cheyy",
    "open chey",
    "thurakkanam",
)
_CLOSE_VERBS = (
    "close",
    "quit",
    "exit",
    "kill",
    "band",
    "bandakku",
    "ബന്ധ",
    "close cheyy",
    "close chey",
    "poo",
    "poku",
)
_SEARCH_VERBS = ("search", "google", "തിരയ", "തിരയൂ", "search cheyy", "google cheyy")
_SYSTEM_VERBS = ("shutdown", "shut down", "restart", "reboot", "lock", "sleep")
_MEDIA_VERBS = ("play", "pause", "next", "previous", "stop")


@dataclass(frozen=True)
class TargetRule:
    """A target (app/folder/system action) with its trigger phrases."""

    action: str
    target: str
    phrases: tuple[str, ...]
    verbs: tuple[str, ...] = field(default_factory=tuple)
    requires_verb: bool = True


# ── App targets ───────────────────────────────────────────────────
_APP_RULES: tuple[TargetRule, ...] = (
    TargetRule(
        "open_app",
        "chrome",
        ("chrome", "ക്രോം", "google chrome", "ഗൂഗിൾ ക്രോം"),
        _OPEN_VERBS,
    ),
    TargetRule("open_app", "firefox", ("firefox", "ഫയർഫോക്സ്"), _OPEN_VERBS),
    TargetRule("open_app", "edge", ("edge", "എഡ്ജ്", "microsoft edge"), _OPEN_VERBS),
    TargetRule(
        "open_app",
        "vscode",
        ("vs code", "vscode", "visual studio code", "കോഡ്"),
        _OPEN_VERBS,
    ),
    TargetRule(
        "open_app",
        "terminal",
        ("terminal", "ടെർമിനൽ", "command prompt", "cmd"),
        _OPEN_VERBS,
    ),
    TargetRule("open_app", "powershell", ("powershell", "പവർഷെൽ"), _OPEN_VERBS),
    TargetRule("open_app", "discord", ("discord", "ഡിസ്കോർഡ്"), _OPEN_VERBS),
    TargetRule("open_app", "spotify", ("spotify", "സ്പോട്ടിഫൈ"), _OPEN_VERBS),
    TargetRule("open_app", "notepad", ("notepad", "നോട്ട്പാഡ്"), _OPEN_VERBS),
    TargetRule(
        "open_app", "explorer", ("explorer", "file explorer", "എക്സ്പ്ലോറർ"), _OPEN_VERBS
    ),
    TargetRule("open_app", "settings", ("settings", "സെറ്റിംഗ്സ്"), _OPEN_VERBS),
    TargetRule("open_app", "task_manager", ("task manager", "ടാസ്ക് മാനേജർ"), _OPEN_VERBS),
    TargetRule(
        "open_app", "calculator", ("calculator", "കാൽക്കുലേറ്റർ", "calc"), _OPEN_VERBS
    ),
    TargetRule("open_app", "paint", ("paint", "പെയിന്റ്", "mspaint"), _OPEN_VERBS),
    TargetRule("open_app", "word", ("word", "വേഡ്", "ms word"), _OPEN_VERBS),
    TargetRule("open_app", "excel", ("excel", "എക്സൽ"), _OPEN_VERBS),
    TargetRule("open_app", "powerpoint", ("powerpoint", "പവർപോയിന്റ്"), _OPEN_VERBS),
    TargetRule("open_app", "slack", ("slack", "സ്ലാക്ക്"), _OPEN_VERBS),
    TargetRule("open_app", "teams", ("teams", "ടീംസ്", "microsoft teams"), _OPEN_VERBS),
    TargetRule("open_app", "zoom", ("zoom", "സൂം"), _OPEN_VERBS),
    TargetRule("open_app", "obs", ("obs", "ഒബിഎസ്", "obs studio"), _OPEN_VERBS),
    TargetRule("open_app", "steam", ("steam", "സ്റ്റീം"), _OPEN_VERBS),
)

# ── Folder targets ────────────────────────────────────────────────
_FOLDER_RULES: tuple[TargetRule, ...] = (
    TargetRule(
        "open_folder", "downloads", ("downloads", "ഡൗൺലോഡ്", "ഡൗൺലോഡ്സ്"), _OPEN_VERBS
    ),
    TargetRule(
        "open_folder", "documents", ("documents", "ഡോക്യുമെന്റ്സ്", "ഡോക്യുമെന്റ്"), _OPEN_VERBS
    ),
    TargetRule("open_folder", "desktop", ("desktop", "ഡെസ്ക്ടോപ്പ്"), _OPEN_VERBS),
    TargetRule(
        "open_folder",
        "pictures",
        ("pictures", "photos", "ഫോട്ടോസ്", "ചിത്രങ്ങൾ"),
        _OPEN_VERBS,
    ),
    TargetRule("open_folder", "music", ("music folder", "മ്യൂസിക് ഫോൾഡർ"), _OPEN_VERBS),
    TargetRule("open_folder", "videos", ("videos", "വീഡിയോസ്"), _OPEN_VERBS),
)

# ── System targets ────────────────────────────────────────────────
_SYSTEM_RULES: tuple[TargetRule, ...] = (
    TargetRule(
        "system_control",
        "shutdown",
        ("shutdown", "shut down", "ഷട്ട്ഡൗൺ", "ഷട്ട് ഡൗൺ", "off cheyy"),
        _SYSTEM_VERBS,
        requires_verb=False,
    ),
    TargetRule(
        "system_control",
        "restart",
        ("restart", "reboot", "റീസ്റ്റാർട്ട്", "വീണ്ടും തുടങ്ങ"),
        _SYSTEM_VERBS,
        requires_verb=False,
    ),
    TargetRule(
        "system_control",
        "lock",
        ("lock", "ലോക്ക്", "lock cheyy", "lock chey"),
        _SYSTEM_VERBS,
        requires_verb=False,
    ),
    TargetRule(
        "system_control", "sleep", ("sleep", "സ്ലീപ്"), _SYSTEM_VERBS, requires_verb=False
    ),
    TargetRule(
        "system_control",
        "volume_up",
        (
            "volume up",
            "increase volume",
            "louder",
            "ശബ്ദം കൂട്ട",
            "ശബ്ദം കൂട്ടൂ",
            "കൂട്ടൂ",
            "volume kootu",
            "volume koodu",
        ),
        _SYSTEM_VERBS,
        requires_verb=False,
    ),
    TargetRule(
        "system_control",
        "volume_down",
        (
            "volume down",
            "decrease volume",
            "quieter",
            "ശബ്ദം കുറയ്ക്ക",
            "ശബ്ദം കുറയ്ക്കൂ",
            "കുറയ്ക്കൂ",
            "volume kurakku",
            "volume kuraykku",
        ),
        _SYSTEM_VERBS,
        requires_verb=False,
    ),
    TargetRule(
        "system_control",
        "mute",
        ("mute", "unmute", "മ്യൂട്ട്"),
        _SYSTEM_VERBS,
        requires_verb=False,
    ),
)

# ── Media targets ─────────────────────────────────────────────────
_MEDIA_RULES: tuple[TargetRule, ...] = (
    TargetRule(
        "media",
        "play_pause",
        ("play music", "pause music", "play", "pause", "പ്ലേ", "പോസ്"),
        _MEDIA_VERBS,
        requires_verb=False,
    ),
    TargetRule(
        "media",
        "next_track",
        ("next song", "next track", "skip", "അടുത്ത പാട്ട്"),
        _MEDIA_VERBS,
        requires_verb=False,
    ),
    TargetRule(
        "media",
        "previous_track",
        ("previous song", "previous track", "മുൻപത്തെ പാട്ട്"),
        _MEDIA_VERBS,
        requires_verb=False,
    ),
)

_ALL_RULES: tuple[TargetRule, ...] = (
    *_APP_RULES,
    *_FOLDER_RULES,
    *_SYSTEM_RULES,
    *_MEDIA_RULES,
)


class CommandMatcher:
    """Fast deterministic matcher for known commands.

    Scans normalized input for a target phrase and, when required, an
    action verb. Returns a high-confidence intent on a match, or None
    to signal that the Laya classifier should handle it.
    """

    def __init__(self) -> None:
        self._rules = _ALL_RULES

    def match(self, text: str) -> dict[str, Any] | None:
        """Attempt to match a command deterministically.

        Args:
            text: Raw command text (any supported language).

        Returns:
            Intent dict on match, otherwise None.
        """
        if not text or not text.strip():
            return None

        normalized = _normalize(text)

        best: tuple[int, TargetRule] | None = None

        for rule in self._rules:
            # Find the longest matching target phrase
            target_len = 0
            for phrase in rule.phrases:
                if phrase in normalized:
                    target_len = max(target_len, len(phrase))

            if target_len == 0:
                continue

            # Verify a verb when the rule requires one
            has_verb = any(verb in normalized for verb in rule.verbs)
            if rule.requires_verb and not has_verb:
                continue

            # Score: longer phrase + verb present wins
            score = target_len * 10 + (5 if has_verb else 0)
            if best is None or score > best[0]:
                best = (score, rule)

        if best is None:
            return None

        rule = best[1]
        log.debug("matched_rule", action=rule.action, target=rule.target, text=text)

        return {
            "action": rule.action,
            "target": rule.target,
            "confidence": 0.99,
            "source": "matcher",
            "text": text,
        }

    @property
    def rule_count(self) -> int:
        """Number of registered matching rules."""
        return len(self._rules)
