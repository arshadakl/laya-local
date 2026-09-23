"""Pre-download models for offline usage.

Downloads the faster-whisper and Laya models so they are
available without internet access on first run.

Usage:
    python scripts/download_models.py
    python scripts/download_models.py --whisper-model small
    python scripts/download_models.py --laya-model convaiinnovations/laya-multilingual
"""

from __future__ import annotations

import argparse
import sys


def download_whisper(model_name: str = "small") -> None:
    """Download a faster-whisper model.

    Args:
        model_name: Whisper model size (tiny, base, small, medium, large-v3).
    """
    print(f"\nDownloading faster-whisper model: {model_name}")

    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    print(f"  Model '{model_name}' downloaded and cached.")
    del model


def download_laya(model_name: str = "convaiinnovations/laya-multilingual") -> None:
    """Download a Laya model.

    Args:
        model_name: Laya model identifier from Hugging Face.
    """
    print(f"\nDownloading Laya model: {model_name}")

    from laya import Router

    # This triggers the download
    router = Router(preload=True)
    print(f"  Model '{model_name}' downloaded and cached.")
    del router


def main() -> None:
    """Main entry point for model download."""
    parser = argparse.ArgumentParser(
        description="Pre-download models for laya-local.",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="small",
        help="Whisper model size (default: small).",
    )
    parser.add_argument(
        "--laya-model",
        type=str,
        default="convaiinnovations/laya-multilingual",
        help="Laya model identifier (default: convaiinnovations/laya-multilingual).",
    )
    parser.add_argument(
        "--skip-whisper",
        action="store_true",
        help="Skip Whisper model download.",
    )
    parser.add_argument(
        "--skip-laya",
        action="store_true",
        help="Skip Laya model download.",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("laya-local Model Downloader")
    print("=" * 60)

    try:
        if not args.skip_whisper:
            download_whisper(args.whisper_model)

        if not args.skip_laya:
            download_laya(args.laya_model)

        print("\n" + "=" * 60)
        print("All models downloaded successfully!")
        print("You can now run laya-local without internet access.")
        print("=" * 60)

    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
