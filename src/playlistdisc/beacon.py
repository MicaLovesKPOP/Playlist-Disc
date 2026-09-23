"""Generate the experimental PDv1 draft-a DTMF audio beacon."""

from __future__ import annotations

from array import array
import math
from pathlib import Path
import wave

from .identity import PDIdentity

SAMPLE_RATE = 44_100
CHANNELS = 2
SAMPLE_WIDTH = 2
BEACON_SECONDS = 4.0
TONE_SECONDS = 0.080
SYMBOL_GAP_SECONDS = 0.040
FRAME_GAP_SECONDS = 0.400
LEAD_SECONDS = 0.400
AMPLITUDE = 0.16  # per sine; summed peak is ~-9.9 dBFS before fades
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
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_WIDTH)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())
    return path
