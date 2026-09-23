"""Audio utilities for format conversion and recording helpers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def resample_audio(
    audio: NDArray[np.floating[np.float32]],
    original_rate: int,
    target_rate: int,
) -> NDArray[np.float32]:
    """Resample audio to a target sample rate.

    Args:
        audio: Input audio array.
        original_rate: Original sample rate in Hz.
        target_rate: Target sample rate in Hz.

    Returns:
        Resampled audio array.
    """
    if original_rate == target_rate:
        return audio.astype(np.float32)

    from scipy.signal import resample

    num_samples = int(len(audio) * target_rate / original_rate)
    resampled = resample(audio.astype(np.float64), num_samples)
    return resampled.astype(np.float32)


def normalize_audio(audio: NDArray[np.floating]) -> NDArray[np.float32]:
    """Normalize audio to [-1.0, 1.0] range.

    Args:
        audio: Input audio array.

    Returns:
        Normalized audio as float32.
    """
    audio_f32 = audio.astype(np.float32)
    max_val = np.max(np.abs(audio_f32))
    if max_val == 0:
        return audio_f32
    return audio_f32 / max_val


def compute_rms(audio: NDArray[np.floating]) -> float:
    """Compute root mean square energy of audio.

    Args:
        audio: Input audio array.

    Returns:
        RMS energy value.
    """
    audio_f64 = audio.astype(np.float64)
    return float(np.sqrt(np.mean(audio_f64**2)))
