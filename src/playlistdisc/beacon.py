"""Generate and decode the experimental PDv1 Draft 0.2 DTMF beacon."""

from __future__ import annotations

from array import array
from dataclasses import dataclass
import math
from pathlib import Path
import statistics
import sys
from typing import Iterable
import wave

from .identity import FORMAT_VERSION, PDIdentity

SAMPLE_RATE = 44_100
CHANNELS = 2
SAMPLE_WIDTH = 2
BEACON_SECONDS = 4.0
TONE_SECONDS = 0.080
SYMBOL_GAP_SECONDS = 0.040
FRAME_GAP_SECONDS = 0.400
LEAD_SECONDS = 0.400
AMPLITUDE = 0.16
FADE_SECONDS = 0.005

_DTMF_ROWS = {
    "1": 697,
    "2": 697,
    "3": 697,
    "4": 770,
    "5": 770,
    "6": 770,
    "7": 852,
    "8": 852,
    "9": 852,
    "*": 941,
    "0": 941,
    "#": 941,
}
_DTMF_COLS = {
    "1": 1209,
    "4": 1209,
    "7": 1209,
    "*": 1209,
    "2": 1336,
    "5": 1336,
    "8": 1336,
    "0": 1336,
    "3": 1477,
    "6": 1477,
    "9": 1477,
    "#": 1477,
}
_ROW_FREQS = (697, 770, 852, 941)
_COL_FREQS = (1209, 1336, 1477)
_DTMF_GRID = {
    (697, 1209): "1",
    (697, 1336): "2",
    (697, 1477): "3",
    (770, 1209): "4",
    (770, 1336): "5",
    (770, 1477): "6",
    (852, 1209): "7",
    (852, 1336): "8",
    (852, 1477): "9",
    (941, 1209): "*",
    (941, 1336): "0",
    (941, 1477): "#",
}
_FRAME_SYMBOL_COUNT = 10


@dataclass(frozen=True, slots=True)
class BeaconDecodeResult:
    identity: PDIdentity
    valid_frames: int
    tokens: tuple[str, ...]


def _silence(samples: list[float], seconds: float) -> None:
    samples.extend([0.0] * round(seconds * SAMPLE_RATE))


def _tone(samples: list[float], symbol: str) -> None:
    count = round(TONE_SECONDS * SAMPLE_RATE)
    fade = max(1, round(FADE_SECONDS * SAMPLE_RATE))
    f1, f2 = _DTMF_ROWS[symbol], _DTMF_COLS[symbol]
    for i in range(count):
        envelope = 1.0
        if i < fade:
            envelope = i / fade
        elif i >= count - fade:
            envelope = (count - 1 - i) / fade
        value = AMPLITUDE * envelope * (
            math.sin(2 * math.pi * f1 * i / SAMPLE_RATE)
            + math.sin(2 * math.pi * f2 * i / SAMPLE_RATE)
        )
        samples.append(value)
    _silence(samples, SYMBOL_GAP_SECONDS)


def beacon_samples(identity: PDIdentity) -> list[float]:
    samples: list[float] = []
    _silence(samples, LEAD_SECONDS)
    for repeat in range(2):
        for symbol in identity.beacon_symbols:
            _tone(samples, symbol)
        if repeat == 0:
            _silence(samples, FRAME_GAP_SECONDS)
    target = round(BEACON_SECONDS * SAMPLE_RATE)
    if len(samples) > target:
        raise RuntimeError("beacon timing no longer fits the four-second reference WAV")
    samples.extend([0.0] * (target - len(samples)))
    return samples


def write_beacon_wav(identity: PDIdentity, path: str | Path) -> Path:
    path = Path(path)
    mono = beacon_samples(identity)
    pcm = array("h")
    for value in mono:
        sample = max(-32768, min(32767, round(value * 32767)))
        pcm.extend((sample, sample))
    if sys.byteorder != "little":
        pcm.byteswap()
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_WIDTH)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())
    return path


def _goertzel_power(samples: list[float], sample_rate: int, frequency: int) -> float:
    coefficient = 2.0 * math.cos(2.0 * math.pi * frequency / sample_rate)
    s1 = 0.0
    s2 = 0.0
    for value in samples:
        s0 = value + coefficient * s1 - s2
        s2, s1 = s1, s0
    return s1 * s1 + s2 * s2 - coefficient * s1 * s2


def _classify_dtmf(samples: list[float], sample_rate: int) -> str | None:
    if len(samples) < max(64, round(0.025 * sample_rate)):
        return None
    mean_square = sum(value * value for value in samples) / len(samples)
    if mean_square < 1e-10:
        return None

    rows = sorted(
        ((_goertzel_power(samples, sample_rate, freq), freq) for freq in _ROW_FREQS),
        reverse=True,
    )
    cols = sorted(
        ((_goertzel_power(samples, sample_rate, freq), freq) for freq in _COL_FREQS),
        reverse=True,
    )

    if rows[0][0] < rows[1][0] * 1.8 or cols[0][0] < cols[1][0] * 1.8:
        return None
    if rows[0][0] + cols[0][0] < mean_square * len(samples) ** 2 * 0.12:
        return None
    return _DTMF_GRID.get((rows[0][1], cols[0][1]))


def _active_regions(
    samples: list[float], sample_rate: int, *, block_seconds: float = 0.010
) -> list[tuple[int, int]]:
    block = max(1, round(block_seconds * sample_rate))
    rms_values: list[float] = []
    for start in range(0, len(samples), block):
        chunk = samples[start : start + block]
        if not chunk:
            break
        rms_values.append(
            math.sqrt(sum(value * value for value in chunk) / len(chunk))
        )
    if not rms_values:
        return []

    baseline = statistics.median(rms_values)
    ordered = sorted(rms_values)
    peak = ordered[round(0.95 * (len(ordered) - 1))]
    if peak < 1e-5:
        return []
    threshold = baseline + 0.35 * max(0.0, peak - baseline)

    active = [value >= max(1e-5, threshold) for value in rms_values]
    regions: list[tuple[int, int]] = []
    index = 0
    while index < len(active):
        if not active[index]:
            index += 1
            continue
        end = index + 1
        while end < len(active) and active[end]:
            end += 1
        start_sample = index * block
        end_sample = min(end * block, len(samples))
        if (end_sample - start_sample) / sample_rate >= 0.035:
            regions.append((start_sample, end_sample))
        index = end
    return regions


def detect_dtmf_tokens(samples: Iterable[float], sample_rate: int) -> tuple[str, ...]:
    """Return stable DTMF tone runs found in a beacon-sized audio sample."""
    values = list(float(value) for value in samples)
    tokens: list[str] = []
    margin = round(0.010 * sample_rate)
    for start, end in _active_regions(values, sample_rate):
        if end - start > 2 * margin + round(0.030 * sample_rate):
            start += margin
            end -= margin
        symbol = _classify_dtmf(values[start:end], sample_rate)
        if symbol is not None:
            tokens.append(symbol)
    return tuple(tokens)


def decode_beacon_samples(
    samples: Iterable[float],
    sample_rate: int,
    *,
    required_matching_frames: int = 2,
) -> BeaconDecodeResult:
    """Decode the draft beacon and require repeated, checksum-valid agreement."""
    if required_matching_frames < 1:
        raise ValueError("required_matching_frames must be at least 1")
    tokens = detect_dtmf_tokens(samples, sample_rate)
    frames: list[PDIdentity] = []

    for index in range(len(tokens) - _FRAME_SYMBOL_COUNT + 1):
        candidate = tokens[index : index + _FRAME_SYMBOL_COUNT]
        if candidate[0] != "*" or candidate[-1] != "#":
            continue
        payload = "".join(candidate[1:-1])
        if len(payload) != 8 or not payload.isascii() or not payload.isdigit():
            continue
        if payload[0] != str(FORMAT_VERSION):
            continue
        identity = PDIdentity(int(payload[1:7]))
        if payload[7] != str(identity.check_digit):
            continue
        frames.append(identity)

    if not frames:
        raise ValueError("no checksum-valid PDv1 beacon frame found")
    identities = {frame.number for frame in frames}
    if len(identities) != 1:
        raise ValueError("conflicting valid PDv1 beacon frames found")
    if len(frames) < required_matching_frames:
        raise ValueError(
            f"only {len(frames)} valid beacon frame(s); "
            f"{required_matching_frames} required"
        )
    return BeaconDecodeResult(frames[0], len(frames), tokens)


def _decode_pcm_samples(raw: bytes, sample_width: int) -> list[float]:
    if sample_width not in {1, 2, 3, 4}:
        raise ValueError(
            "beacon decoder supports 8/16/24/32-bit uncompressed integer PCM WAV"
        )
    if len(raw) % sample_width:
        raise ValueError("WAV PCM byte count is not divisible by sample width")

    if sample_width == 1:
        # WAV 8-bit PCM is unsigned; wider integer PCM is signed little-endian.
        return [(value - 128) / 128.0 for value in raw]

    denominator = float(1 << (sample_width * 8 - 1))
    return [
        int.from_bytes(
            raw[offset : offset + sample_width],
            byteorder="little",
            signed=True,
        )
        / denominator
        for offset in range(0, len(raw), sample_width)
    ]


def read_wav_mono(path: str | Path) -> tuple[list[float], int]:
    """Read uncompressed integer-PCM WAV into normalized mono floats."""
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        compression = wav.getcomptype()
        raw = wav.readframes(wav.getnframes())

    if compression != "NONE":
        raise ValueError("beacon decoder requires uncompressed integer PCM WAV")
    if channels < 1:
        raise ValueError("WAV has no audio channels")

    pcm = _decode_pcm_samples(raw, sample_width)
    if len(pcm) % channels:
        raise ValueError("WAV sample count is not divisible by channel count")

    mono: list[float] = []
    for index in range(0, len(pcm), channels):
        mono.append(sum(pcm[index : index + channels]) / channels)
    return mono, sample_rate


def decode_beacon_wav(
    path: str | Path, *, required_matching_frames: int = 2
) -> BeaconDecodeResult:
    samples, sample_rate = read_wav_mono(path)
    return decode_beacon_samples(
        samples,
        sample_rate,
        required_matching_frames=required_matching_frames,
    )
