from pathlib import Path
import math
import random
import wave

import pytest

from playlistdisc.beacon import (
    FRAME_GAP_SECONDS,
    LEAD_SECONDS,
    SAMPLE_RATE,
    SYMBOL_GAP_SECONDS,
    TONE_SECONDS,
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


def _resample_linear(
    samples: list[float], source_rate: int, target_rate: int
) -> list[float]:
    if source_rate == target_rate:
        return list(samples)
    output_count = round(len(samples) * target_rate / source_rate)
    source_per_output = source_rate / target_rate
    output: list[float] = []
    for index in range(output_count):
        source_position = index * source_per_output
        left = int(source_position)
        fraction = source_position - left
        if left + 1 < len(samples):
            output.append(
                samples[left] * (1.0 - fraction) + samples[left + 1] * fraction
            )
        else:
            output.append(samples[-1])
    return output


def _frame_bounds(frame_index: int) -> tuple[int, int]:
    frame_seconds = 10 * (TONE_SECONDS + SYMBOL_GAP_SECONDS)
    start_seconds = LEAD_SECONDS + frame_index * (frame_seconds + FRAME_GAP_SECONDS)
    return (
        round(start_seconds * SAMPLE_RATE),
        round((start_seconds + frame_seconds) * SAMPLE_RATE),
    )


def _encode_pcm(samples: list[float], sample_width: int) -> bytes:
    if sample_width == 1:
        return bytes(
            max(0, min(255, round(max(-1.0, min(1.0, value)) * 127 + 128)))
            for value in samples
        )

    maximum = (1 << (sample_width * 8 - 1)) - 1
    minimum = -(1 << (sample_width * 8 - 1))
    return b"".join(
        max(minimum, min(maximum, round(value * maximum))).to_bytes(
            sample_width, "little", signed=True
        )
        for value in samples
    )


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


@pytest.mark.parametrize("number", [123456, 907856])
@pytest.mark.parametrize("sample_rate", [8_000, 16_000, 48_000])
def test_beacon_decoder_handles_common_synthetic_capture_rates(
    number: int, sample_rate: int
):
    identity = PDIdentity(number)
    resampled = _resample_linear(beacon_samples(identity), SAMPLE_RATE, sample_rate)
    result = decode_beacon_samples(resampled, sample_rate)
    assert result.identity == identity
    assert result.valid_frames == 2


def test_decode_wav_handles_mono_48khz_capture(tmp_path: Path):
    identity = PDIdentity(907856)
    samples = _resample_linear(beacon_samples(identity), SAMPLE_RATE, 48_000)
    path = tmp_path / "capture-48k-mono.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(48_000)
        wav.writeframes(_encode_pcm(samples, 2))

    result = decode_beacon_wav(path)
    assert result.identity == identity
    assert result.valid_frames == 2


@pytest.mark.parametrize("sample_width", [1, 2, 3, 4])
def test_decode_wav_handles_common_integer_pcm_widths(
    tmp_path: Path, sample_width: int
):
    identity = PDIdentity(123456)
    sample_rate = 16_000
    samples = _resample_linear(beacon_samples(identity), SAMPLE_RATE, sample_rate)
    path = tmp_path / f"capture-{sample_width * 8}bit.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(_encode_pcm(samples, sample_width))

    result = decode_beacon_wav(path)
    assert result.identity == identity
    assert result.valid_frames == 2


def test_conflicting_valid_beacon_frames_fail_closed():
    first = PDIdentity(123456)
    second = PDIdentity(907856)
    mixed = beacon_samples(first)
    other = beacon_samples(second)
    start, end = _frame_bounds(1)
    mixed[start:end] = other[start:end]

    with pytest.raises(ValueError, match="conflicting valid PDv1 beacon frames"):
        decode_beacon_samples(mixed, SAMPLE_RATE)


def test_corrupt_second_frame_cannot_satisfy_redundancy():
    identity = PDIdentity(123456)
    corrupted = beacon_samples(identity)
    second_start, _ = _frame_bounds(1)
    symbol_span = round((TONE_SECONDS + SYMBOL_GAP_SECONDS) * SAMPLE_RATE)
    tone_samples = round(TONE_SECONDS * SAMPLE_RATE)
    corrupt_start = second_start + 4 * symbol_span
    corrupted[corrupt_start : corrupt_start + tone_samples] = [0.0] * tone_samples

    with pytest.raises(ValueError, match="only 1 valid beacon frame"):
        decode_beacon_samples(corrupted, SAMPLE_RATE)


def test_representative_ids_survive_seeded_six_db_noise():
    for number in (123456, 907856):
        identity = PDIdentity(number)
        result = decode_beacon_samples(
            _add_noise(beacon_samples(identity), 6.0, seed=number),
            SAMPLE_RATE,
        )
        assert result.identity == identity
        assert result.valid_frames == 2
