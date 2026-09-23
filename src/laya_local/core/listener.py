"""Microphone listener with push-to-talk and voice activity detection.

Captures audio from the system microphone when a trigger key is held,
then returns the recorded audio for transcription.
"""

from __future__ import annotations

import time
from collections.abc import Callable
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

    def listen(
        self,
        on_start: Callable[[], None] | None = None,
        on_audio: Callable[[NDArray[np.float32]], None] | None = None,
    ) -> NDArray[np.float32] | None:
        """Wait for trigger key press and record audio.

        Args:
            on_start: Callback when recording starts.
            on_audio: Callback with audio chunks during recording.

        Returns:
            Recorded audio as float32 array, or None if recording was
            too short or empty.
        """
        import keyboard

        log.debug("waiting_for_trigger", key=self._trigger_key)

        # Non-blocking poll for trigger key
        while True:
            if keyboard.is_pressed(self._trigger_key):
                break
            time.sleep(0.05)

        if on_start:
            on_start()

        log.debug("recording_started")
        audio = self._record(on_audio)
        log.debug("recording_stopped", samples=len(audio))

        if len(audio) < self._sample_rate * 0.3:
            log.debug("recording_too_short")
            return None

        return normalize_audio(audio)

    def _record(
        self,
        on_audio: Callable[[NDArray[np.float32]], None] | None = None,
    ) -> NDArray[np.float32]:
        """Record audio while trigger key is held, with VAD.

        Stops recording when:
        - Trigger key is released
        - Silence exceeds threshold for 1.5 seconds
        - Max duration is reached

        Args:
            on_audio: Callback with each audio chunk.

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

                # Send chunk to callback for real-time visualization
                if on_audio:
                    on_audio(chunk)

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
