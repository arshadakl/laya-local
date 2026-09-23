"""Voice response using Piper TTS.

Wraps the Piper text-to-speech engine for spoken feedback.
Only active when TTS is enabled in config.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import structlog

from laya_local.config import TTSConfig

log = structlog.get_logger()


class Responder:
    """Text-to-speech responder using Piper TTS.

    Generates spoken audio responses for action confirmations
    and error messages. Only active when TTS is enabled.

    Args:
        config: TTS configuration settings.
    """

    def __init__(self, config: TTSConfig) -> None:
        self._config = config
        self._enabled = config.enabled
        self._voice_model = config.model

    def respond(self, message: str) -> None:
        """Speak a response message aloud.

        If TTS is disabled, this is a no-op.

        Args:
            message: Text message to speak.
        """
        if not self._enabled:
            log.debug("tts_disabled", message=message)
            return

        log.info("speaking", message=message)

        try:
            self._speak_piper(message)
        except Exception as exc:
            log.error("tts_failed", error=str(exc))
            # Fall back to console output
            print(f"  [TTS Error] {message}")

    def _speak_piper(self, text: str) -> None:
        """Synthesize and play audio using Piper TTS.

        Args:
            text: Text to synthesize.
        """
        try:
            from piper import PiperVoice
            import sounddevice as sd
            import numpy as np

            voice = PiperVoice.load(self._voice_model)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            # Synthesize to temp file
            with open(tmp_path, "wb") as f:
                voice.synthesize(text, f)

            # Play the audio
            import scipy.io.wavfile as wavfile

            sample_rate, audio_data = wavfile.read(tmp_path)

            # Convert to float32 if needed
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0

            sd.play(audio_data, sample_rate)
            sd.wait()

            # Clean up
            Path(tmp_path).unlink(missing_ok=True)

        except ImportError:
            log.warning("piper_not_installed")
            print(f"  [TTS] {text}")
        except Exception as exc:
            log.error("piper_synthesis_failed", error=str(exc))
            raise

    def speak_confirmation(self, action: str, target: str) -> None:
        """Speak a confirmation message for an executed action.

        Args:
            action: Action type (e.g., "open_app").
            target: Target name (e.g., "chrome").
        """
        messages: dict[str, str] = {
            "open_app": f"Opening {target}",
            "close_app": f"Closing {target}",
            "open_folder": f"Opening {target} folder",
            "system_control": f"System control: {target}",
            "media": f"Media: {target}",
            "search": f"Searching for {target}",
        }

        message = messages.get(action, f"Executing {action}")
        self.respond(message)

    def speak_error(self, error_message: str) -> None:
        """Speak an error message.

        Args:
            error_message: Error description to speak.
        """
        self.respond(f"Error: {error_message}")
