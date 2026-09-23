"""Verify a generated PDv1 mastering bundle without optical hardware."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import wave

from .beacon import decode_beacon_wav
from .identity import PDIdentity, decode_track_durations

_MESSAGE_RE = re.compile(r'^\s*MESSAGE\s+"(PD1-\d{6}-\d)"\s*$', re.MULTILINE)
_SILENCE_RE = re.compile(r"^\s*SILENCE\s+(\d+):(\d+):(\d+)\s*$")
_AUDIOFILE_RE = re.compile(
    r'^\s*AUDIOFILE\s+"([^"]+)"\s+\S+(?:\s+(\d+):(\d+):(\d+))?\s*$'
)


@dataclass(frozen=True, slots=True)
class BuildVerificationReport:
    identity: PDIdentity
    manifest_identity: PDIdentity
    toc_identity: PDIdentity
    cdtext_identity: PDIdentity
    beacon_identity: PDIdentity
    beacon_frames: int
    track_durations_seconds: tuple[float, ...]

    @property
    def ok(self) -> bool:
        identities = {
            self.identity.number,
            self.manifest_identity.number,
            self.toc_identity.number,
            self.cdtext_identity.number,
            self.beacon_identity.number,
        }
        return len(identities) == 1 and self.beacon_frames >= 2


def _msf_seconds(minutes: str, seconds: str, frames: str) -> float:
    return int(minutes) * 60 + int(seconds) + int(frames) / 75.0


def _wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def _toc_track_durations(toc_path: Path) -> tuple[float, ...]:
    text = toc_path.read_text(encoding="utf-8")
    blocks = text.split("TRACK AUDIO")[1:]
    if len(blocks) != 8:
        raise ValueError(f"generated TOC has {len(blocks)} tracks, expected 8")

    durations: list[float] = []
    for block in blocks:
        total = 0.0
        for line in block.splitlines():
            silence = _SILENCE_RE.match(line)
            if silence:
                total += _msf_seconds(*silence.groups())
                continue
            audiofile = _AUDIOFILE_RE.match(line)
            if audiofile:
                filename, minutes, seconds, frames = audiofile.groups()
                if minutes is not None:
                    total += _msf_seconds(minutes, seconds, frames)
                else:
                    total += _wav_seconds(toc_path.parent / filename)
        if total <= 0:
            raise ValueError("generated TOC contains a zero-length/unreadable track")
        durations.append(total)
    return tuple(durations)


def verify_build(bundle: str | Path) -> BuildVerificationReport:
    root = Path(bundle)
    manifest_path = root / "manifest.json"
    toc_path = root / "disc.toc"
    beacon_path = root / "beacon.wav"
    for required in (manifest_path, toc_path, beacon_path):
        if not required.is_file():
            raise ValueError(f"missing build artifact: {required.name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_identity = PDIdentity.parse(str(manifest["machine_id"]))
    identity = PDIdentity.parse(str(manifest["id"]))
    if manifest_identity != identity:
        raise ValueError("manifest canonical ID and machine ID disagree")
    if manifest.get("check_digit") != identity.check_digit:
        raise ValueError("manifest check digit disagrees with identity")
    if manifest.get("toc_sha256") != identity.toc_signature:
        raise ValueError("manifest TOC signature disagrees with identity")

    toc_text = toc_path.read_text(encoding="utf-8")
    messages = _MESSAGE_RE.findall(toc_text)
    if len(set(messages)) != 1:
        raise ValueError("generated TOC must contain exactly one unique PDv1 MESSAGE")
    cdtext_identity = PDIdentity.parse(messages[0])

    durations = _toc_track_durations(toc_path)
    toc_identity = decode_track_durations(durations, tolerance=0.01)

    beacon = decode_beacon_wav(beacon_path, required_matching_frames=2)
    beacon_identity = beacon.identity

    if not (
        identity
        == manifest_identity
        == toc_identity
        == cdtext_identity
        == beacon_identity
    ):
        raise ValueError(
            "build channels disagree: "
            f"manifest={manifest_identity.machine_id}, "
            f"toc={toc_identity.machine_id}, "
            f"cdtext={cdtext_identity.machine_id}, "
            f"beacon={beacon_identity.machine_id}"
        )

    manifest_durations = tuple(float(x) for x in manifest["track_durations_seconds"])
    if any(abs(a - b) > 0.01 for a, b in zip(manifest_durations, durations, strict=True)):
        raise ValueError("manifest track durations disagree with mastering TOC")

    return BuildVerificationReport(
        identity=identity,
        manifest_identity=manifest_identity,
        toc_identity=toc_identity,
        cdtext_identity=cdtext_identity,
        beacon_identity=beacon_identity,
        beacon_frames=beacon.valid_frames,
        track_durations_seconds=durations,
    )
