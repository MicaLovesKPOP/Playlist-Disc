from pathlib import Path
import math
import random
import wave

import pytest

from playlistdisc.beacon import (
    SAMPLE_RATE,
    beacon_samples,
    decode_beacon_samples,
    decode_beacon_wav,
    write_beacon_wav,
)
from playlistdisc.identity import PDIdentity


def _add_noise(samples: list[float], snr_db: float, seed: int = 7) -> list[float]:
    rng = random.Random(seed)
    signal_rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    noise_rms = signal_rms / (10 ** (snr_db / 20))
    return [value + rng.gauss(0.0, noise_rms) for value in samples]


def _clip(samples: list[float], gain: float, limit: float) -> list[float]:
    return [max(-limit, min(limit, value * gain)) for value in samples]


def _lowpass(samples: list[float], cutoff_hz: float) -> list[float]:
    dt = 1.0 / SAMPLE_RATE
    rc = 1.0 / (2.0 * math.pi * cutoff_hz)
    alpha = dt / (rc + dt)
    output: list[float] = []
    state = 0.0
    for value in samples:
        state += alpha * (value - state)
        output.append(state)
    return output


def _highpass(samples: list[float], cutoff_hz: float) -> list[float]:
    dt = 1.0 / SAMPLE_RATE
    rc = 1.0 / (2.0 * math.pi * cutoff_hz)
    alpha = rc / (rc + dt)
    output: list[float] = []
    state = 0.0
    previous = 0.0
    for value in samples:
        state = alpha * (state + value - previous)
        previous = value
        output.append(state)
    return output


def test_beacon_wav_is_exactly_four_seconds(tmp_path: Path):
    path = write_beacon_wav(PDIdentity(999902), tmp_path / "beacon.wav")
    with wave.open(str(path), "rb") as wav:
        assert wav.getnchannels() == 2
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == SAMPLE_RATE
        assert wav.getnframes() == SAMPLE_RATE * 4
    result = decode_beacon_wav(path)
    assert result.identity == PDIdentity(999902)
    assert result.valid_frames == 2


def test_beacon_decoder_survives_synthetic_analogue_stress():
    identity = PDIdentity(123456)
    clean = beacon_samples(identity)
    variants = [
        clean,
        [value * 0.05 for value in clean],
        _add_noise(clean, 12.0),
        _clip(clean, gain=4.0, limit=0.30),
        _highpass(_lowpass(clean, 2500.0), 300.0),
    ]
    for samples in variants:
        result = decode_beacon_samples(samples, SAMPLE_RATE)
        assert result.identity == identity
        assert result.valid_frames == 2


def test_beacon_requires_redundant_matching_frame_by_default():
    identity = PDIdentity(123456)
    first_frame_only = beacon_samples(identity)[: round(1.75 * SAMPLE_RATE)]
    with pytest.raises(ValueError, match="only 1 valid beacon frame"):
        decode_beacon_samples(first_frame_only, SAMPLE_RATE)


def test_silence_is_not_a_beacon():
    with pytest.raises(ValueError, match="no checksum-valid"):
        decode_beacon_samples([0.0] * (SAMPLE_RATE * 4), SAMPLE_RATE)
