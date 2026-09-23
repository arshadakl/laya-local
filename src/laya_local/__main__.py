"""CLI entry point for laya-local.

Usage:
    python -m laya_local               # voice mode with GUI (default)
    python -m laya_local --text        # text mode in terminal
    python -m laya_local --no-gui      # voice mode in terminal (no GUI)
    python -m laya_local --config x.yaml
"""

from __future__ import annotations

import argparse

import structlog

from laya_local import __version__
from laya_local.config import load_config
from laya_local.logging_config import configure_logging

log = structlog.get_logger()


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="laya-local",
        description="A local-first Malayalam/English assistant for Windows.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Text mode — type commands in the terminal.",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Voice mode without GUI — terminal output only.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.yaml.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the application.

    Args:
        argv: Command-line arguments. Defaults to sys.argv.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    from pathlib import Path

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    log.info("starting", version=__version__)

    if args.text:
        _run_text_mode(config)
    elif args.no_gui:
        _run_voice_terminal(config)
    else:
        _run_voice_gui(config)


def _init_components(config: object) -> tuple[object, object, object, object]:
    """Initialize all pipeline components.

    Args:
        config: Application configuration.

    Returns:
        Tuple of (listener, transcriber, classifier, executor).
    """
    from laya_local.core.classifier import Classifier
    from laya_local.core.executor import Executor
    from laya_local.core.listener import Listener
    from laya_local.core.transcriber import Transcriber

    log.info("loading_models")

    listener = Listener(config.listener)  # type: ignore[arg-type]
    transcriber = Transcriber(config.whisper)  # type: ignore[arg-type]
    classifier = Classifier(config.laya)  # type: ignore[arg-type]
    executor = Executor(config.actions)  # type: ignore[arg-type]

    return listener, transcriber, classifier, executor


def _run_voice_gui(config: object) -> None:
    """Run the assistant in voice mode with GUI window.

    Args:
        config: Application configuration.
    """
    listener, transcriber, classifier, executor = _init_components(config)

    log.info("ready", mode="voice_gui")

    from laya_local.ui.assistant import AssistantUI

    ui = AssistantUI(listener, transcriber, classifier, executor)
    ui.run()


def _run_voice_terminal(config: object) -> None:
    """Run the assistant in voice mode with terminal output.

    Args:
        config: Application configuration.
    """
    listener, transcriber, classifier, executor = _init_components(config)

    log.info("ready", mode="voice_terminal")
    print("\n🎤 Voice mode ready. Hold right Ctrl and speak. Press Ctrl+C to exit.\n")

    try:
        while True:
            audio = listener.listen()
            if audio is None:
                continue

            text = transcriber.transcribe(audio)
            if not text:
                log.debug("empty_transcription")
                continue

            print(f"\n  Heard: {text}")

            intent = classifier.classify(text)
            if intent is None:
                print("  Could not understand that command.")
                continue

            result = executor.execute(intent)
            action = intent.get("action", "unknown")  # type: ignore[union-attr]
            target = intent.get("target", "")  # type: ignore[union-attr]
            status = result.get("status", "error")

            icon = "✓" if status == "success" else "✗"
            print(f"  {icon} {action} → {target}: {result.get('message', '')}")

    except KeyboardInterrupt:
        log.info("shutting_down")
        print("\nGoodbye!")


def _run_text_mode(config: object) -> None:
    """Run the assistant in text mode (type commands).

    Args:
        config: Application configuration.
    """
    from laya_local.core.classifier import Classifier
    from laya_local.core.executor import Executor

    log.info("loading_models")

    classifier = Classifier(config.laya)  # type: ignore[arg-type]
    executor = Executor(config.actions)  # type: ignore[arg-type]

    log.info("ready", mode="text")
    print("\n⌨️  Text mode ready. Type a command. Press Ctrl+C to exit.\n")

    try:
        while True:
            try:
                text = input("Command: ").strip()
            except EOFError:
                break

            if not text:
                continue

            intent = classifier.classify(text)
            if intent is None:
                print("  Could not understand that command.\n")
                continue

            result = executor.execute(intent)
            action = intent.get("action", "unknown")  # type: ignore[union-attr]
            target = intent.get("target", "")  # type: ignore[union-attr]
            print(f"  -> {action} → {target}: {result}\n")
    except KeyboardInterrupt:
        log.info("shutting_down")
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
