"""Verify a generated PDv1 mastering bundle without optical hardware."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import wave

from .beacon import decode_beacon_wav
from .identity import (
    DRAFT_VERSION,
    FORMAT_NAME,
    PDIdentity,
    TRACK_COUNT,
    decode_track_durations,
)
from .mastering import BEACON_PROFILE

_MESSAGE_RE = re.compile(r'^\s*MESSAGE\s+"(PD1-\d{6}-\d)"\s*$', re.MULTILINE)
_SILENCE_RE = re.compile(r"^\s*SILENCE\s+(\d+):(\d+):(\d+)\s*$")
_AUDIOFILE_RE = re.compile(
    r'^\s*AUDIOFILE\s+"([^"]+)"\s+\S+(?:\s+(\d+):(\d+):(\d+))?\s*$'
)
_BUNDLE_FILES = ("manifest.json", "disc.toc", "beacon.wav")


@dataclass(frozen=True, slots=True)
class BuildVerificationReport:
    identity: PDIdentity
    manifest_identity: PDIdentity
    toc_identity: PDIdentity
    cdtext_identity: PDIdentity | None
    cd_text_present: bool
    beacon_identity: PDIdentity
    beacon_frames: int
    track_durations_seconds: tuple[float, ...]
    bundle_sha256: str

    @property
    def ok(self) -> bool:
        identities = {
            self.identity.number,
            self.manifest_identity.number,
            self.toc_identity.number,
            self.beacon_identity.number,
        }
        if self.cdtext_identity is not None:
            identities.add(self.cdtext_identity.number)
        return len(identities) == 1 and self.beacon_frames >= 2


def bundle_fingerprint(bundle: str | Path) -> str:
    """Hash the exact three-file mastering bundle with unambiguous framing."""
    root = Path(bundle)
    digest = hashlib.sha256()
    for name in _BUNDLE_FILES:
        path = root / name
        if not path.is_file():
            raise ValueError(f"missing build artifact: {name}")
        data = path.read_bytes()
        encoded_name = name.encode("utf-8")
        digest.update(len(encoded_name).to_bytes(2, "big"))
        digest.update(encoded_name)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _msf_seconds(minutes: str, seconds: str, frames: str) -> float:
    return int(minutes) * 60 + int(seconds) + int(frames) / 75.0


def _wav_seconds(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as wav:
            return wav.getnframes() / wav.getframerate()
    except (EOFError, wave.Error) as exc:
        detail = str(exc) or exc.__class__.__name__
        raise ValueError(f"invalid WAV artifact {path.name}: {detail}") from exc


def _toc_track_durations(toc_path: Path) -> tuple[float, ...]:
    text = toc_path.read_text(encoding="utf-8")
    blocks = text.split("TRACK AUDIO")[1:]
    if len(blocks) != TRACK_COUNT:
        raise ValueError(f"generated TOC has {len(blocks)} tracks, expected {TRACK_COUNT}")

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


def _load_manifest(path: Path) -> dict[str, object]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid build manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("build manifest must be a JSON object")
    return manifest


def verify_build(bundle: str | Path) -> BuildVerificationReport:
    root = Path(bundle)
    manifest_path = root / "manifest.json"
    toc_path = root / "disc.toc"
    beacon_path = root / "beacon.wav"
    for required in (manifest_path, toc_path, beacon_path):
        if not required.is_file():
            raise ValueError(f"missing build artifact: {required.name}")

    manifest = _load_manifest(manifest_path)
    if manifest.get("format") != FORMAT_NAME:
        raise ValueError(f"manifest format must be {FORMAT_NAME!r}")
    if manifest.get("draft") != DRAFT_VERSION:
        raise ValueError(f"manifest draft must be {DRAFT_VERSION!r}")
    if manifest.get("beacon_profile") != BEACON_PROFILE:
        raise ValueError(f"manifest beacon profile must be {BEACON_PROFILE!r}")
    if not isinstance(manifest.get("cd_text"), bool):
        raise ValueError("manifest cd_text must be a boolean")

    try:
        manifest_identity = PDIdentity.parse(str(manifest["machine_id"]))
        identity = PDIdentity.parse(str(manifest["id"]))
    except KeyError as exc:
        raise ValueError(f"build manifest is missing required field {exc.args[0]!r}") from exc
    if manifest_identity != identity:
        raise ValueError("manifest canonical ID and machine ID disagree")
    if manifest.get("namespace") != identity.namespace:
        raise ValueError("manifest namespace disagrees with identity")
    if manifest.get("check_digit") != identity.check_digit:
        raise ValueError("manifest check digit disagrees with identity")
    if manifest.get("total_seconds") != identity.total_seconds:
        raise ValueError("manifest total duration disagrees with identity")
    if manifest.get("toc_sha256") != identity.toc_signature:
        raise ValueError("manifest TOC signature disagrees with identity")

    raw_manifest_durations = manifest.get("track_durations_seconds")
    if not isinstance(raw_manifest_durations, list) or len(raw_manifest_durations) != TRACK_COUNT:
        raise ValueError(
            f"manifest track durations must contain exactly {TRACK_COUNT} values"
        )
    try:
        manifest_durations = tuple(float(value) for value in raw_manifest_durations)
    except (TypeError, ValueError) as exc:
        raise ValueError("manifest track durations must be numeric") from exc
    if any(
        abs(actual - expected) > 0.01
        for actual, expected in zip(
            manifest_durations, identity.track_durations, strict=True
        )
    ):
        raise ValueError("manifest track durations disagree with identity")

    toc_text = toc_path.read_text(encoding="utf-8")
    messages = _MESSAGE_RE.findall(toc_text)
    has_cdtext = "CD_TEXT {" in toc_text
    expects_cdtext = bool(manifest["cd_text"])
    cdtext_identity: PDIdentity | None

    if expects_cdtext:
        if not has_cdtext:
            raise ValueError("manifest declares CD-TEXT but mastering TOC omits it")
        if len(set(messages)) != 1:
            raise ValueError(
                "CD-TEXT build must contain exactly one unique PDv1 MESSAGE"
            )
        cdtext_identity = PDIdentity.parse(messages[0])
    else:
        if has_cdtext or messages:
            raise ValueError(
                "mastering TOC contains CD-TEXT but manifest declares it omitted"
            )
        cdtext_identity = None

    durations = _toc_track_durations(toc_path)
    toc_identity = decode_track_durations(durations, tolerance=0.01)

    beacon = decode_beacon_wav(beacon_path, required_matching_frames=2)
    beacon_identity = beacon.identity

    identities = [identity, manifest_identity, toc_identity, beacon_identity]
    if cdtext_identity is not None:
        identities.append(cdtext_identity)
    if any(candidate != identity for candidate in identities):
        details = [
            f"manifest={manifest_identity.machine_id}",
            f"toc={toc_identity.machine_id}",
            f"beacon={beacon_identity.machine_id}",
        ]
        if cdtext_identity is not None:
            details.append(f"cdtext={cdtext_identity.machine_id}")
        raise ValueError("build channels disagree: " + ", ".join(details))

    if any(
        abs(a - b) > 0.01
        for a, b in zip(manifest_durations, durations, strict=True)
    ):
        raise ValueError("manifest track durations disagree with mastering TOC")

    return BuildVerificationReport(
        identity=identity,
        manifest_identity=manifest_identity,
        toc_identity=toc_identity,
        cdtext_identity=cdtext_identity,
        cd_text_present=expects_cdtext,
        beacon_identity=beacon_identity,
        beacon_frames=beacon.valid_frames,
        track_durations_seconds=durations,
        bundle_sha256=bundle_fingerprint(root),
    )
