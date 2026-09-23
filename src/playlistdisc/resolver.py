"""Deterministic service-neutral recording resolution core."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .catalog import load_json
from .identity import PDIdentity


@dataclass(frozen=True, slots=True)
class ResolutionItem:
    position: int
    status: str
    method: str | None
    resource: str | None
    candidates: tuple[str, ...]
    musicbrainz_recording_id: str | None
    isrcs: tuple[str, ...]
    title_hint: str | None
    artist_hint: str | None


@dataclass(frozen=True, slots=True)
class ResolutionPlan:
    provider: str
    market: str | None
    disc_id: str
    machine_id: str
    total_recordings: int
    resolved_count: int
    missing_count: int
    ambiguous_count: int
    coverage: float
    playback: dict[str, Any]
    items: tuple[ResolutionItem, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["items"] = [asdict(item) for item in self.items]
        return payload


def load_provider_index_schema() -> dict[str, Any]:
    from importlib.resources import files

    resource = files("playlistdisc").joinpath("schemas/provider-index.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def validate_provider_index(
    data: dict[str, Any], schema: dict[str, Any] | None = None
) -> list[str]:
    schema = schema or load_provider_index_schema()
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

    seen_resources: set[str] = set()
    for index, track in enumerate(data["tracks"]):
        resource = track["resource"]
        if resource in seen_resources:
            messages.append(
                f"tracks.{index}.resource: duplicate provider resource {resource}"
            )
        seen_resources.add(resource)
    return messages


def load_provider_index(path: str | Path) -> dict[str, Any]:
    data = load_json(path)
    errors = validate_provider_index(data)
    if errors:
        raise ValueError("invalid provider index: " + "; ".join(errors))
    return data


def _canonical_ids(recording: dict[str, Any]) -> tuple[str | None, tuple[str, ...]]:
    mbid = recording.get("musicbrainz_recording_id")
    if isinstance(mbid, str):
        mbid = mbid.lower()
    else:
        mbid = None
    isrcs = tuple(
        sorted(
            value.upper()
            for value in recording.get("isrcs", [])
            if isinstance(value, str)
        )
    )
    return mbid, isrcs


def _provider_maps(index: dict[str, Any]) -> tuple[
    dict[str, set[str]],
    dict[str, set[str]],
    dict[str, dict[str, Any]],
]:
    by_mbid: dict[str, set[str]] = {}
    by_isrc: dict[str, set[str]] = {}
    tracks: dict[str, dict[str, Any]] = {}

    for track in index["tracks"]:
        resource = track["resource"]
        tracks[resource] = track
        if track.get("available", True) is False:
            continue
        mbid = track.get("musicbrainz_recording_id")
        if isinstance(mbid, str):
            by_mbid.setdefault(mbid.lower(), set()).add(resource)
        for isrc in track.get("isrcs", []):
            by_isrc.setdefault(isrc.upper(), set()).add(resource)
    return by_mbid, by_isrc, tracks


def _choose(
    candidates: set[str],
    tracks: dict[str, dict[str, Any]],
    method: str,
) -> tuple[str, str | None, tuple[str, ...]]:
    ordered = tuple(sorted(candidates))
    if not ordered:
        return "missing", None, ()
    if len(ordered) == 1:
        return "resolved", ordered[0], ordered

    preferred = tuple(
        resource for resource in ordered if tracks[resource].get("preferred") is True
    )
    if len(preferred) == 1:
        return "resolved", preferred[0], ordered
    return "ambiguous", None, ordered


def resolve_canonical_manifest(
    entry: dict[str, Any],
    manifest: dict[str, Any],
    provider_index: dict[str, Any],
) -> ResolutionPlan:
    """Resolve a canonical manifest without fuzzy artist/title matching."""
    if entry.get("definition", {}).get("type") != "canonical_manifest":
        raise ValueError("entry is not a canonical_manifest definition")
    id6 = str(entry["id"])
    if str(manifest.get("disc_id")) != id6:
        raise ValueError("manifest disc_id does not match catalog entry")

    index_errors = validate_provider_index(provider_index)
    if index_errors:
        raise ValueError("invalid provider index: " + "; ".join(index_errors))

    provider = provider_index["provider"]
    by_mbid, by_isrc, tracks = _provider_maps(provider_index)
    items: list[ResolutionItem] = []

    for position, recording in enumerate(manifest["recordings"], start=1):
        mbid, isrcs = _canonical_ids(recording)
        override = recording.get("provider_overrides", {}).get(provider)
        if isinstance(override, str) and override:
            items.append(
                ResolutionItem(
                    position=position,
                    status="resolved",
                    method="override",
                    resource=override,
                    candidates=(override,),
                    musicbrainz_recording_id=mbid,
                    isrcs=isrcs,
                    title_hint=recording.get("title_hint"),
                    artist_hint=recording.get("artist_hint"),
                )
            )
            continue

        mbid_candidates = set(by_mbid.get(mbid, set())) if mbid else set()
        isrc_candidates: set[str] = set()
        for isrc in isrcs:
            isrc_candidates.update(by_isrc.get(isrc, set()))

        method: str | None = None
        candidates: set[str]
        if mbid_candidates and isrc_candidates:
            intersection = mbid_candidates & isrc_candidates
            if intersection:
                candidates = intersection
                method = "mbid+isrc"
            else:
                candidates = mbid_candidates | isrc_candidates
                status = "ambiguous"
                resource = None
                method = "identifier_conflict"
                ordered = tuple(sorted(candidates))
                items.append(
                    ResolutionItem(
                        position=position,
                        status=status,
                        method=method,
                        resource=resource,
                        candidates=ordered,
                        musicbrainz_recording_id=mbid,
                        isrcs=isrcs,
                        title_hint=recording.get("title_hint"),
                        artist_hint=recording.get("artist_hint"),
                    )
                )
                continue
        elif mbid_candidates:
            candidates = mbid_candidates
            method = "mbid"
        elif isrc_candidates:
            candidates = isrc_candidates
            method = "isrc"
        else:
            candidates = set()

        status, resource, ordered = _choose(candidates, tracks, method or "none")
        if status == "resolved" and len(ordered) > 1:
            method = f"{method}+preferred"
        if status == "missing":
            method = None

        items.append(
            ResolutionItem(
                position=position,
                status=status,
                method=method,
                resource=resource,
                candidates=ordered,
                musicbrainz_recording_id=mbid,
                isrcs=isrcs,
                title_hint=recording.get("title_hint"),
                artist_hint=recording.get("artist_hint"),
            )
        )

    resolved = sum(item.status == "resolved" for item in items)
    missing = sum(item.status == "missing" for item in items)
    ambiguous = sum(item.status == "ambiguous" for item in items)
    total = len(items)
    identity = PDIdentity.parse(id6)
    return ResolutionPlan(
        provider=provider,
        market=provider_index.get("market"),
        disc_id=id6,
        machine_id=identity.machine_id,
        total_recordings=total,
        resolved_count=resolved,
        missing_count=missing,
        ambiguous_count=ambiguous,
        coverage=(resolved / total if total else 1.0),
        playback=dict(entry["playback"]),
        items=tuple(items),
    )
