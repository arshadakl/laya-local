"""Microphone listener with push-to-talk and wake-word modes.

Captures audio from the system microphone either on a trigger key
(push-to-talk) or on a wake word ("Hey Jarvis"), then returns the
recorded audio for transcription.
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

MODE_PUSH_TO_TALK = "push_to_talk"
MODE_WAKE_WORD = "wake_word"


class Listener:
    """Microphone listener with configurable trigger mode.

    In ``push_to_talk`` mode, records while the trigger key is held.
    In ``wake_word`` mode, continuously listens and records a command
    after the configured wake word is detected.

    Args:
        config: Listener configuration settings.
    """

    def __init__(self, config: ListenerConfig) -> None:
        self._config = config
        self._mode = config.mode
        self._trigger_key = config.trigger_key
        self._wake_word = config.wake_word
        self._wake_threshold = config.wake_threshold
        self._sample_rate = config.sample_rate
        self._channels = config.channels
        self._silence_threshold = config.silence_threshold
        self._max_duration = config.max_duration
        self._beep = config.beep
        self._wake_model: object | None = None

    @property
    def mode(self) -> str:
        """The listener trigger mode."""
        return self._mode

    @property
    def wake_word(self) -> str:
        """The configured wake word name."""
        return self._wake_word

    def listen(
        self,
        on_start: Callable[[], None] | None = None,
        on_audio: Callable[[NDArray[np.float32]], None] | None = None,
    ) -> NDArray[np.float32] | None:
        """Wait for the trigger and record audio.

        Args:
            on_start: Callback when recording starts.
            on_audio: Callback with audio chunks during recording.

        Returns:
            Recorded audio as float32 array, or None if recording was
            too short or empty.
        """
        if self._mode == MODE_WAKE_WORD:
            audio = self._listen_wake_word(on_audio)
        else:
            audio = self._listen_push_to_talk(on_start, on_audio)

        if audio is None or len(audio) < self._sample_rate * 0.3:
            log.debug("recording_too_short")
            return None

        return normalize_audio(audio)

    # ── Push-to-talk mode ─────────────────────────────────────────

    def _listen_push_to_talk(
        self,
        on_start: Callable[[], None] | None = None,
        on_audio: Callable[[NDArray[np.float32]], None] | None = None,
    ) -> NDArray[np.float32] | None:
        """Record audio while the trigger key is held.

        Args:
            on_start: Callback when recording starts.
            on_audio: Callback with audio chunks during recording.

        Returns:
            Recorded audio array, or None.
        """
        import keyboard

        log.debug("waiting_for_trigger", key=self._trigger_key)

        while True:
            if keyboard.is_pressed(self._trigger_key):
                break
            time.sleep(0.05)

        if on_start:
            on_start()

        if self._beep:
            self._play_beep(880, 0.08)

        log.debug("recording_started")
        audio = self._record(on_audio)
        log.debug("recording_stopped", samples=len(audio))

        if self._beep:
            self._play_beep(660, 0.06)

        return audio

    def _record(
        self,
        on_audio: Callable[[NDArray[np.float32]], None] | None = None,
    ) -> NDArray[np.float32]:
        """Record audio until the trigger key is released, silence, or max duration.

        Args:
            on_audio: Callback with each audio chunk.

        Returns:
            Recorded audio as float32 array.
        """
        import keyboard

        frames: list[NDArray[np.float32]] = []
        silent_streak = 0
        start_time = time.monotonic()

        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="float32",
        ) as stream:
            while True:
                elapsed = time.monotonic() - start_time

                if elapsed >= self._max_duration:
                    break

                if not keyboard.is_pressed(self._trigger_key):
                    time.sleep(0.1)  # Debounce
                    break

                data, _overflowed = stream.read(self._sample_rate // 10)
                chunk = data[:, 0] if data.ndim > 1 else data
                frames.append(chunk.copy())

                if on_audio:
                    on_audio(chunk)

                if self._is_silent(chunk):
                    silent_streak += 1
                    if silent_streak >= 15:  # ~1.5s of silence
                        break
                else:
                    silent_streak = 0

        if not frames:
            return np.array([], dtype=np.float32)

        return np.concatenate(frames)

    # ── Wake word mode ────────────────────────────────────────────

    def _ensure_wake_model(self) -> object:
        """Lazily load the wake word model.

        Returns:
            The openwakeword Model instance.
        """
        if self._wake_model is not None:
            return self._wake_model

        from openwakeword.model import Model

        log.info("loading_wake_word_model", wake_word=self._wake_word)
        self._wake_model = Model(inference_framework="onnx")
        log.info("wake_word_model_ready")
        return self._wake_model

    def _listen_wake_word(
        self,
        on_audio: Callable[[NDArray[np.float32]], None] | None = None,
    ) -> NDArray[np.float32] | None:
        """Continuously listen and record a command after the wake word.

        Args:
            on_audio: Callback with audio chunks during command recording.

        Returns:
            Recorded command audio array, or None.
        """
        import queue

        from openwakeword.utils import AudioStream

        model = self._ensure_wake_model()

        log.info("wake_word_listening", wake_word=self._wake_word)

        audio_q: queue.Queue[np.ndarray] = queue.Queue()
        mic_stream = AudioStream(
            mic_audio_q=audio_q,
            frames_per_buffer=128,
            sample_rate=self._sample_rate,
            channels=self._channels,
        )
        mic_stream.start()

        command_frames: list[NDArray[np.float32]] = []
        recording = False
        silent_streak = 0
        recording_start: float = 0.0

        try:
            while True:
                frame = audio_q.get()
                # Feed wake word model
                prediction = model.predict(frame)

                if (
                    not recording
                    and prediction[self._wake_word] >= self._wake_threshold
                ):
                    log.info("wake_word_detected", score=prediction[self._wake_word])
                    recording = True
                    recording_start = time.monotonic()
                    silent_streak = 0
                    if self._beep:
                        self._play_beep(880, 0.08)

                if recording:
                    command_frames.append(frame.astype(np.float32))
                    if on_audio:
                        on_audio(frame.astype(np.float32))

                    elapsed = time.monotonic() - recording_start

                    if self._is_silent(frame):
                        silent_streak += 1
                        # 128-sample frames: ~30 frames ≈ 0.25s of silence
                        if silent_streak >= 30:
                            break
                    else:
                        silent_streak = 0

                    if elapsed >= self._max_duration:
                        break
        finally:
            mic_stream.stop()

        if not command_frames:
            return np.array([], dtype=np.float32)

        return np.concatenate(command_frames)

    # ── Shared helpers ────────────────────────────────────────────

    def _is_silent(self, chunk: NDArray[np.float32]) -> bool:
        """Return True when a chunk's energy is below the silence threshold.

        Args:
            chunk: Audio chunk.

        Returns:
            True when the chunk is effectively silent.
        """
        rms = compute_rms(chunk)
        return rms < self._silence_threshold / 10000

    def _play_beep(self, frequency: float = 880, duration: float = 0.08) -> None:
        """Play a short feedback beep.

        Args:
            frequency: Tone frequency in Hz.
            duration: Tone duration in seconds.
        """
        try:
            t = np.linspace(0, duration, int(self._sample_rate * duration), False)
            tone = 0.25 * np.sin(2 * np.pi * frequency * t)
            sd.play(tone, self._sample_rate)
        except Exception as exc:
            log.debug("beep_failed", error=str(exc))
