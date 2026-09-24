"""Runtime recognition of Playlist Disc identity from independent strong channels."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.resources import files
import json
from pathlib import Path
import re
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .beacon import decode_beacon_wav
from .identity import PDIdentity, decode_track_durations

_MACHINE_ID_RE = re.compile(
    r"(?<![A-Z0-9])PD1-\d{6}-\d(?!\d)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class RecognitionEvidence:
    channel: str
    machine_id: str


@dataclass(frozen=True, slots=True)
class RecognitionResult:
    status: str
    identity: PDIdentity | None
    evidence: tuple[RecognitionEvidence, ...]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": 1,
            "format": "PDv1-recognition",
            "status": self.status,
            "evidence": [asdict(item) for item in self.evidence],
            "errors": list(self.errors),
        }
        if self.identity is not None:
            payload["id"] = self.identity.id6
            payload["machine_id"] = self.identity.machine_id
        return payload


def load_recognition_schema() -> dict[str, Any]:
    resource = files("playlistdisc").joinpath("schemas/recognition-result.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def validate_recognition_result(
    data: dict[str, Any], schema: dict[str, Any] | None = None
) -> list[str]:
    schema = schema or load_recognition_schema()
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda error: [str(part) for part in error.path],
    )
    messages: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{location}: {error.message}")
    if messages:
        return messages

    evidence_identities: dict[int, PDIdentity] = {}
    for index, item in enumerate(data["evidence"]):
        try:
            identity = PDIdentity.parse(item["machine_id"])
        except ValueError as exc:
            messages.append(f"evidence.{index}.machine_id: {exc}")
        else:
            evidence_identities[identity.number] = identity

    status = data["status"]
    has_identity = "machine_id" in data or "id" in data
    claimed_identity: PDIdentity | None = None
    if status == "recognized":
        if "machine_id" not in data or "id" not in data:
            messages.append("machine_id/id: recognized result requires identity")
        else:
            try:
                claimed_identity = PDIdentity.parse(data["machine_id"])
            except ValueError as exc:
                messages.append(f"machine_id: {exc}")
            else:
                if claimed_identity.id6 != data["id"]:
                    messages.append("id: does not match machine_id")
    elif has_identity:
        messages.append("machine_id/id: non-recognized result must not claim identity")

    if messages:
        return messages

    if not evidence_identities:
        expected_status = "unknown"
    elif len(evidence_identities) == 1:
        expected_status = "recognized"
    else:
        expected_status = "conflict"

    if status != expected_status:
        messages.append(
            f"status: {status!r} contradicts strong evidence; expected {expected_status!r}"
        )
    elif status == "recognized":
        evidence_identity = next(iter(evidence_identities.values()))
        if claimed_identity is None or claimed_identity.number != evidence_identity.number:
            messages.append(
                "machine_id/id: recognized identity does not match strong evidence"
            )
    return messages


def _cdtext_identities(values: Iterable[str]) -> tuple[list[PDIdentity], list[str]]:
    identities: list[PDIdentity] = []
    errors: list[str] = []
    for index, raw in enumerate(values):
        matches = _MACHINE_ID_RE.findall(str(raw).upper())
        if not matches:
            errors.append(f"cdtext[{index}]: no PDv1 machine ID found")
            continue
        for match in matches:
            try:
                identities.append(PDIdentity.parse(match))
            except ValueError as exc:
                errors.append(f"cdtext[{index}]: {exc}")
    return identities, errors


def _finish(
    evidence_pairs: list[tuple[str, PDIdentity]],
    errors: list[str],
) -> RecognitionResult:
    unique: dict[tuple[str, int], RecognitionEvidence] = {}
    identities: dict[int, PDIdentity] = {}
    for channel, identity in evidence_pairs:
        unique[(channel, identity.number)] = RecognitionEvidence(
            channel=channel,
            machine_id=identity.machine_id,
        )
        identities[identity.number] = identity

    if len(identities) == 1:
        status = "recognized"
        identity = next(iter(identities.values()))
    elif len(identities) > 1:
        status = "conflict"
        identity = None
    else:
        status = "unknown"
        identity = None

    result = RecognitionResult(
        status=status,
        identity=identity,
        evidence=tuple(unique[key] for key in sorted(unique)),
        errors=tuple(errors),
    )
    validation_errors = validate_recognition_result(result.to_dict())
    if validation_errors:
        raise ValueError(
            "generated recognition result is invalid: "
            + "; ".join(validation_errors)
        )
    return result


def recognize_observations(
    *,
    track_durations: Iterable[float] | None = None,
    toc_tolerance: float = 0.0,
    cdtext_values: Iterable[str] = (),
    beacon_wav: str | Path | None = None,
) -> RecognitionResult:
    """Combine independent PDv1 observations using fail-open conflict handling.

    Each accepted channel is already strong on its own:
    - the full eight-track TOC must decode and pass the Damm check;
    - CD-TEXT must contain a checksum-valid PD machine ID;
    - the audio beacon decoder requires its repeated matching frames.

    Invalid/missing channels are retained as diagnostic errors but do not suppress a
    different valid channel. Two valid channels that disagree produce conflict and
    therefore no identity.
    """
    if toc_tolerance < 0 or toc_tolerance >= 2:
        raise ValueError("TOC tolerance must be >= 0 and < 2 seconds")

    evidence: list[tuple[str, PDIdentity]] = []
    errors: list[str] = []

    if track_durations is not None:
        try:
            identity = decode_track_durations(
                track_durations,
                tolerance=toc_tolerance,
            )
        except (TypeError, ValueError) as exc:
            errors.append(f"toc: {exc}")
        else:
            evidence.append(("toc", identity))

    cdtext_identities, cdtext_errors = _cdtext_identities(cdtext_values)
    errors.extend(cdtext_errors)
    evidence.extend(("cdtext", identity) for identity in cdtext_identities)

    if beacon_wav is not None:
        try:
            beacon = decode_beacon_wav(
                beacon_wav,
                required_matching_frames=2,
            )
        except (OSError, ValueError) as exc:
            errors.append(f"audio_beacon: {exc}")
        else:
            evidence.append(("audio_beacon", beacon.identity))

    return _finish(evidence, errors)
