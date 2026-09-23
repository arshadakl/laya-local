"""CLI entry point for laya-local.

Usage:
    laya-local                    # default: voice mode
    laya-local --text             # text-only mode
    laya-local --voice            # voice mode with push-to-talk
    laya-local --config path.yaml # custom config file
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
        help="Text-only mode (type commands instead of speaking).",
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Voice mode with push-to-talk.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.yaml (default: project root config.yaml).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: INFO).",
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

    log.info(
        "starting", version=__version__, text_mode=args.text, voice_mode=args.voice
    )

    # Determine input mode
    use_voice = args.voice or not args.text

    if use_voice:
        _run_voice_mode(config)
    else:
        _run_text_mode(config)


def _run_voice_mode(config: object) -> None:
    """Run the assistant in voice mode with push-to-talk.

    Args:
        config: Application configuration.
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

    log.info("ready", mode="voice", trigger=config.listener.trigger_key)  # type: ignore[union-attr]
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

            log.info("heard", text=text)

            intent = classifier.classify(text)
            if intent is None:
                log.warning("could_not_classify", text=text)
                continue

            result = executor.execute(intent)
            log.info("executed", action=intent.get("action"), result=result)  # type: ignore[union-attr]
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

            log.info("input", text=text)

            intent = classifier.classify(text)
            if intent is None:
                print("  Could not understand that command.\n")
                continue

            result = executor.execute(intent)
            action = intent.get("action", "unknown")  # type: ignore[union-attr]
            print(f"  -> {action}: {result}\n")
    except KeyboardInterrupt:
        log.info("shutting_down")
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
