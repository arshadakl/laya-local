"""Speech-to-text transcriber using faster-whisper.

Wraps the faster-whisper library for local speech recognition
with support for Malayalam, English, and mixed-language input.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import structlog

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from laya_local.config import WhisperConfig

log = structlog.get_logger()


class Transcriber:
    """Local speech-to-text using faster-whisper.

    Loads a Whisper model and transcribes audio segments to text
    with automatic language detection.

    Args:
        config: Whisper configuration settings.
    """

    def __init__(self, config: WhisperConfig) -> None:
        self._config = config
        self._model: Any = None

    def _ensure_model(self) -> Any:
        """Lazy-load the Whisper model on first use.

        Returns:
            The loaded WhisperModel instance.
        """
        if self._model is not None:
            return self._model

        from faster_whisper import WhisperModel

        log.info(
            "loading_whisper",
            model=self._config.model,
            device=self._config.device,
        )

        compute_type = self._config.compute_type
        if self._config.device != "cpu" and compute_type == "int8":
            compute_type = "float16"

        self._model = WhisperModel(
            self._config.model,
            device=self._config.device,
            compute_type=compute_type,
        )

        log.info("whisper_ready", model=self._config.model)
        return self._model

    def transcribe(self, audio: NDArray[np.float32]) -> str | None:
        """Transcribe audio to text.

        Args:
            audio: Audio array as float32, expected at 16kHz mono.

        Returns:
            Transcribed text, or None if transcription is empty.
        """
        if len(audio) == 0:
            return None

        model = self._ensure_model()

        # faster-whisper expects float32 numpy array
        audio_f32 = audio.astype(np.float32)

        # Normalize if needed (ensure [-1, 1] range)
        max_val = np.max(np.abs(audio_f32))
        if max_val > 1.0:
            audio_f32 = audio_f32 / max_val

        segments, info = model.transcribe(
            audio_f32,
            beam_size=5,
            language=self._config.language,
            vad_filter=True,
        )

        log.debug(
            "transcription_info",
            language=info.language,
            probability=f"{info.language_probability:.2f}",
        )

        # Collect all segment texts
        texts = [segment.text.strip() for segment in segments]
        full_text = " ".join(texts).strip()

        if not full_text:
            return None

        log.info(
            "transcribed",
            text=full_text,
            language=info.language,
        )

        return full_text

    def transcribe_file(self, file_path: str) -> str | None:
        """Transcribe an audio file to text.

        Args:
            file_path: Path to the audio file.

        Returns:
            Transcribed text, or None if transcription is empty.
        """
        model = self._ensure_model()

        segments, _info = model.transcribe(
            file_path,
            beam_size=5,
            language=self._config.language,
        )

        texts = [segment.text.strip() for segment in segments]
        full_text = " ".join(texts).strip()

        return full_text if full_text else None
