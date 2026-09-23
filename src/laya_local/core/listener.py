"""Microphone listener with push-to-talk and voice activity detection.

Captures audio from the system microphone when a trigger key is held,
then returns the recorded audio for transcription.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np
import sounddevice as sd
import structlog

from laya_local.utils.audio import compute_rms, normalize_audio

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from laya_local.config import ListenerConfig

log = structlog.get_logger()


class Listener:
    """Microphone listener with push-to-talk trigger.

    Records audio while the trigger key is held, with automatic
    silence detection to stop recording early.

    Args:
        config: Listener configuration settings.
    """

    def __init__(self, config: ListenerConfig) -> None:
        self._config = config
        self._trigger_key = config.trigger_key
        self._sample_rate = config.sample_rate
        self._channels = config.channels
        self._silence_threshold = config.silence_threshold
        self._max_duration = config.max_duration

    def listen(self) -> NDArray[np.float32] | None:
        """Wait for trigger key press and record audio.

        Returns:
            Recorded audio as float32 array, or None if recording was
            too short or empty.
        """
        log.debug("waiting_for_trigger", key=self._trigger_key)
        self._wait_for_trigger()

        log.debug("recording_started")
        audio = self._record()
        log.debug("recording_stopped", samples=len(audio))

        if len(audio) < self._sample_rate * 0.3:
            log.debug("recording_too_short")
            return None

        return normalize_audio(audio)

    def _wait_for_trigger(self) -> None:
        """Block until the trigger key is pressed.

        Uses keyboard polling. On Windows, checks the key state
        via the keyboard module.
        """
        import keyboard

        keyboard.wait(self._trigger_key)
        # Small debounce delay
        time.sleep(0.05)

    def _record(self) -> NDArray[np.float32]:
        """Record audio while trigger key is held, with VAD.

        Stops recording when:
        - Trigger key is released
        - Silence exceeds threshold for 1.5 seconds
        - Max duration is reached

        Returns:
            Recorded audio as float32 array.
        """
        import keyboard

        frames: list[NDArray[np.float32]] = []
        silence_start: float | None = None
        start_time = time.monotonic()

        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="float32",
        ) as stream:
            while True:
                elapsed = time.monotonic() - start_time

                # Check max duration
                if elapsed >= self._max_duration:
                    log.debug("max_duration_reached")
                    break

                # Check trigger key release
                if not keyboard.is_pressed(self._trigger_key):
                    log.debug("trigger_released")
                    time.sleep(0.1)  # Debounce
                    break

                # Read audio chunk
                data, _overflowed = stream.read(self._sample_rate // 10)  # 100ms chunks
                chunk = data[:, 0] if data.ndim > 1 else data
                frames.append(chunk.copy())

                # Voice activity detection
                rms = compute_rms(chunk)
                if rms < self._silence_threshold / 10000:
                    if silence_start is None:
                        silence_start = time.monotonic()
                    elif time.monotonic() - silence_start > 1.5:
                        log.debug("silence_detected")
                        break
                else:
                    silence_start = None

        if not frames:
            return np.array([], dtype=np.float32)

        return np.concatenate(frames)

    def play_beep(self, frequency: float = 800, duration: float = 0.1) -> None:
        """Play a short beep to indicate recording start.

        Args:
            frequency: Beep frequency in Hz.
            duration: Beep duration in seconds.
        """
        t = np.linspace(0, duration, int(self._sample_rate * duration), False)
        beep = 0.3 * np.sin(2 * np.pi * frequency * t)
        sd.play(beep, self._sample_rate)
        sd.wait()
