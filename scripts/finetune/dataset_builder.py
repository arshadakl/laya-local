"""Build a fine-tuning dataset for laya-local commands.

Generates JSONL training examples that teach the Laya multilingual model
to classify Windows voice/text commands into structured intents across
Malayalam, English, and Manglish.

Each line is one training item:

    {
      "state": {"body": "<command text>"},
      "questions": { ...the standard command questions... },
      "targets": {
        "action": {"choice": "<action>"},
        "app_target": {"choice": "<target>"}
      }
    }

Usage:
    python scripts/finetune/dataset_builder.py [--output data.jsonl] [--variations 6]
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from laya_local.intents.definitions import build_questions

# ── Command templates per (action, target) ────────────────────────
# Each template may contain {app} / {folder} / {system} placeholders.
# Verbatim phrase templates are marked with a leading "=" and used as-is.

_TEMPLATES: dict[str, list[str]] = {
    "open_app": [
        "open {app}",
        "open {app} please",
        "please open {app}",
        "launch {app}",
        "start {app}",
        "open up {app}",
        "can you open {app}",
        "run {app}",
        "{app} thurakku",
        "{app} thurakkoo",
        "{app} open cheyy",
        "{app} open chey",
        "{app} തുറക്കൂ",
        "{app} തുറക്കു",
        "{app} തുറക്കുക",
        "doy {app} open cheyyu",
        "{app} start cheyyu",
    ],
    "close_app": [
        "close {app}",
        "quit {app}",
        "exit {app}",
        "close {app} please",
        "{app} band cheyy",
        "{app} bandakku",
        "{app} അടയ്ക്കൂ",
        "{app} അടയ്ക്കുക",
        "kill {app}",
    ],
    "open_folder": [
        "open {folder}",
        "open the {folder} folder",
        "open {folder} folder",
        "show {folder}",
        "go to {folder}",
        "{folder} thurakku",
        "{folder} open cheyy",
        "{folder} തുറക്കൂ",
        "{folder} ഫോൾഡർ തുറക്കൂ",
        "open my {folder}",
    ],
    "open_url": [
        "open {url}",
        "go to {url}",
        "open website {url}",
        "browse to {url}",
        "{url} തുറക്കൂ",
        "{url} open cheyy",
    ],
    "search": [
        "search for {query}",
        "google {query}",
        "search {query}",
        "find {query} online",
        "{query} തിരയൂ",
        "{query} search cheyy",
        "web search for {query}",
    ],
    "system_control": [
        "shutdown",
        "shut down",
        "shut down the computer",
        "shutdown the pc",
        "turn off the computer",
        "ഷട്ട് ഡൗൺ ചെയ്യൂ",
        "കമ്പ്യൂട്ടർ ഓഫ് ചെയ്യൂ",
        "shutdown cheyy",
        "off cheyy",
        "restart",
        "reboot",
        "restart the computer",
        "റീസ്റ്റാർട്ട് ചെയ്യൂ",
        "restart cheyy",
        "lock",
        "lock the computer",
        "lock the screen",
        "കമ്പ്യൂട്ടർ ലോക്ക് ചെയ്യൂ",
        "lock cheyy",
        "lock chey",
        "sleep",
        "sleep mode",
        "put the computer to sleep",
        "സ്ലീപ് ചെയ്യൂ",
    ],
    "media": [
        "play music",
        "play",
        "pause",
        "pause music",
        "play the music",
        "സംഗീതം പ്ലേ ചെയ്യൂ",
        "play cheyy",
        "next song",
        "next track",
        "skip",
        "skip to next",
        "അടുത്ത പാട്ട്",
        "next song cheyy",
        "previous song",
        "previous track",
        "go back a song",
        "മുൻപത്തെ പാട്ട്",
        "stop music",
        "stop the music",
    ],
}

# ── Target values ─────────────────────────────────────────────────
_APPS: dict[str, list[str]] = {
    "chrome": ["chrome", "google chrome", "ക്രോം", "ഗൂഗിൾ ക്രോം"],
    "firefox": ["firefox", "ഫയർഫോക്സ്"],
    "edge": ["edge", "microsoft edge", "എഡ്ജ്"],
    "vscode": ["vs code", "vscode", "visual studio code", "കോഡ്"],
    "terminal": ["terminal", "windows terminal", "command prompt", "cmd", "ടെർമിനൽ"],
    "discord": ["discord", "ഡിസ്കോർഡ്"],
    "spotify": ["spotify", "സ്പോട്ടിഫൈ"],
    "notepad": ["notepad", "നോട്ട്പാഡ്"],
    "explorer": ["file explorer", "explorer", "എക്സ്പ്ലോറർ"],
    "calculator": ["calculator", "calc", "കാൽക്കുലേറ്റർ"],
}

_FOLDERS: dict[str, list[str]] = {
    "downloads": ["downloads", "ഡൗൺലോഡ്സ്", "ഡൗൺലോഡ്"],
    "documents": ["documents", "ഡോക്യുമെന്റ്സ്", "ഡോക്യുമെന്റ്"],
    "desktop": ["desktop", "ഡെസ്ക്ടോപ്പ്"],
    "pictures": ["pictures", "photos", "ചിത്രങ്ങൾ", "ഫോട്ടോസ്"],
    "music": ["music", "മ്യൂസിക്"],
    "videos": ["videos", "വീഡിയോസ്"],
}

_URLS: list[str] = ["github.com", "youtube.com", "gmail.com", "google.com"]
_QUERIES: list[str] = [
    "weather today",
    "latest news",
    "python tutorial",
    "best restaurants",
]

# Map a target label to the question it belongs to.
_TARGET_QUESTION: dict[str, str] = {
    "chrome": "app_target",
    "firefox": "app_target",
    "edge": "app_target",
    "vscode": "app_target",
    "terminal": "app_target",
    "discord": "app_target",
    "spotify": "app_target",
    "notepad": "app_target",
    "explorer": "app_target",
    "calculator": "app_target",
    "downloads": "folder_target",
    "documents": "folder_target",
    "desktop": "folder_target",
    "pictures": "folder_target",
    "music": "folder_target",
    "videos": "folder_target",
}


def _build_item(action: str, state: str, target: str | None = None) -> dict[str, Any]:
    """Build one JSONL training item."""
    questions = build_questions()
    targets: dict[str, dict[str, str]] = {"action": {"choice": action}}

    if target and target in _TARGET_QUESTION:
        qname = _TARGET_QUESTION[target]
        targets[qname] = {"choice": target}

    return {
        "state": {"body": state},
        "questions": questions,
        "targets": targets,
    }


def _expand_template(template: str, placeholders: dict[str, str]) -> str:
    """Fill {placeholders} in a template string."""
    for key, value in placeholders.items():
        template = template.replace(f"{{{key}}}", value)
    return template


def generate_items(variations: int = 6, seed: int = 42) -> list[dict[str, Any]]:
    """Generate the full training item set.

    Args:
        variations: Number of app name variants to use per app.
        seed: Random seed for reproducibility.

    Returns:
        List of training item dictionaries.
    """
    rng = random.Random(seed)
    items: list[dict[str, Any]] = []

    # open_app / close_app
    for action in ("open_app", "close_app"):
        for label, names in _APPS.items():
            for name in names:
                for template in _TEMPLATES[action]:
                    items.append(
                        _build_item(
                            action, _expand_template(template, {"app": name}), label
                        )
                    )

    # open_folder
    for label, names in _FOLDERS.items():
        for name in names:
            for template in _TEMPLATES["open_folder"]:
                items.append(
                    _build_item(
                        "open_folder",
                        _expand_template(template, {"folder": name}),
                        label,
                    )
                )

    # open_url (target: none — no classifier question, keep action only)
    for url in _URLS:
        for template in _TEMPLATES["open_url"]:
            items.append(
                _build_item("open_url", _expand_template(template, {"url": url}))
            )

    # search
    for query in _QUERIES:
        for template in _TEMPLATES["search"]:
            items.append(
                _build_item("search", _expand_template(template, {"query": query}))
            )

    # system_control (verbatim phrases)
    for template in _TEMPLATES["system_control"]:
        items.append(_build_item("system_control", _expand_template(template, {})))

    # media (verbatim phrases)
    for template in _TEMPLATES["media"]:
        items.append(_build_item("media", _expand_template(template, {})))

    rng.shuffle(items)
    return items


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build the laya-local fine-tuning dataset."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data.jsonl",
        help="Output JSONL path (default: data.jsonl).",
    )
    parser.add_argument(
        "--variations",
        type=int,
        default=6,
        help="App name variants per app (default: 6).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42).",
    )
    args = parser.parse_args()

    items = generate_items(variations=args.variations, seed=args.seed)

    out = Path(args.output)
    with out.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {len(items)} training items to {out}")

    # Quick stats
    counts: dict[str, int] = {}
    for item in items:
        action = item["targets"]["action"]["choice"]
        counts[action] = counts.get(action, 0) + 1
    print("Per-action counts:")
    for action, count in sorted(counts.items()):
        print(f"  {action}: {count}")


if __name__ == "__main__":
    main()
