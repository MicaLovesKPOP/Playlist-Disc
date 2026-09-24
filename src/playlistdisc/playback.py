"""Compile catalog/private records into provider-neutral playback plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.resources import files
import json
from typing import Any

from jsonschema import Draft202012Validator

from .identity import PDIdentity
from .resolver import ResolutionPlan, resolve_canonical_manifest


@dataclass(frozen=True, slots=True)
class PlaybackPlan:
    disc_id: str
    machine_id: str
    title: str
    provider: str
    status: str
    mode: str
    playback: dict[str, Any]
    strategy: str | None = None
    resource: str | None = None
    resources: tuple[str, ...] = ()
    lookup: dict[str, Any] | None = None
    resolution: dict[str, Any] | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": 1,
            "format": "PDv1-playback-plan",
            "disc_id": self.disc_id,
            "machine_id": self.machine_id,
            "title": self.title,
            "provider": self.provider,
            "status": self.status,
            "mode": self.mode,
            "playback": dict(self.playback),
        }
        if self.strategy is not None:
            payload["strategy"] = self.strategy
        if self.resource is not None:
            payload["resource"] = self.resource
        if self.resources:
            payload["resources"] = list(self.resources)
        if self.lookup is not None:
            payload["lookup"] = dict(self.lookup)
        if self.resolution is not None:
            payload["resolution"] = self.resolution
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def load_playback_plan_schema() -> dict[str, Any]:
    resource = files("playlistdisc").joinpath("schemas/playback-plan.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def validate_playback_plan(
    data: dict[str, Any], schema: dict[str, Any] | None = None
) -> list[str]:
    schema = schema or load_playback_plan_schema()
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

    try:
        identity = PDIdentity.parse(data["machine_id"])
    except ValueError as exc:
        messages.append(f"machine_id: {exc}")
    else:
        if identity.id6 != data["disc_id"]:
            messages.append("disc_id: does not match machine_id")

    status = data["status"]
    mode = data["mode"]
    if status == "ready" and mode == "none":
        messages.append("mode: ready plan cannot use mode='none'")
    if mode == "direct_resource" and "resource" not in data:
        messages.append("resource: direct_resource plan requires resource")
    if mode == "track_list" and "resources" not in data:
        messages.append("resources: track_list plan requires resources")
    if mode in {"entity_lookup", "recording_resolution"} and "lookup" not in data:
        messages.append(f"lookup: {mode} plan requires lookup")

    if mode == "recording_resolution" and isinstance(data.get("lookup"), dict):
        lookup = data["lookup"]
        recordings = lookup.get("recordings")
        count = lookup.get("recording_count")
        if isinstance(recordings, list) and isinstance(count, int):
            if count != len(recordings):
                messages.append(
                    "lookup.recording_count: does not match lookup.recordings length"
                )

            seen_mbids: set[str] = set()
            seen_isrcs: set[str] = set()
            for index, recording in enumerate(recordings):
                if not isinstance(recording, dict):
                    continue
                mbid = recording.get("musicbrainz_recording_id")
                if isinstance(mbid, str):
                    normalized = mbid.lower()
                    if normalized in seen_mbids:
                        messages.append(
                            f"lookup.recordings.{index}.musicbrainz_recording_id: "
                            f"duplicate recording MBID {mbid}"
                        )
                    seen_mbids.add(normalized)
                for isrc in recording.get("isrcs", []):
                    normalized = str(isrc).upper()
                    if normalized in seen_isrcs:
                        messages.append(
                            f"lookup.recordings.{index}.isrcs: "
                            f"ISRC {isrc} appears in more than one recording"
                        )
                    seen_isrcs.add(normalized)
    return messages


def _identity_and_playback(
    entry: dict[str, Any], provider: str
) -> tuple[PDIdentity, dict[str, Any]]:
    identity = PDIdentity.parse(str(entry["id"]))
    playback = entry.get("playback")
    if not isinstance(playback, dict):
        raise ValueError("entry is missing playback policy")
    if not provider:
        raise ValueError("provider must be non-empty")
    return identity, dict(playback)


def _finish(plan: PlaybackPlan) -> PlaybackPlan:
    errors = validate_playback_plan(plan.to_dict())
    if errors:
        raise ValueError("generated playback plan is invalid: " + "; ".join(errors))
    return plan


def _binding_plan(
    entry: dict[str, Any],
    provider: str,
    *,
    fallback_lookup: dict[str, Any] | None = None,
) -> PlaybackPlan:
    identity, playback = _identity_and_playback(entry, provider)
    binding = entry.get("providers", {}).get(provider)

    if isinstance(binding, dict):
        strategy = binding.get("strategy")
        if strategy == "unsupported":
            return _finish(
                PlaybackPlan(
                    identity.id6,
                    identity.machine_id,
                    str(entry["title"]),
                    provider,
                    "unavailable",
                    "none",
                    playback,
                    strategy="unsupported",
                    reason="catalog explicitly marks this provider unsupported",
                )
            )
        resource = binding.get("resource")
        if isinstance(resource, str) and resource:
            return _finish(
                PlaybackPlan(
                    identity.id6,
                    identity.machine_id,
                    str(entry["title"]),
                    provider,
                    "ready",
                    "direct_resource",
                    playback,
                    strategy=str(strategy) if strategy is not None else None,
                    resource=resource,
                )
            )

    if fallback_lookup is not None:
        return _finish(
            PlaybackPlan(
                identity.id6,
                identity.machine_id,
                str(entry["title"]),
                provider,
                "requires_lookup",
                "entity_lookup",
                playback,
                lookup=fallback_lookup,
                reason="no concrete provider resource is currently bound",
            )
        )

    return _finish(
        PlaybackPlan(
            identity.id6,
            identity.machine_id,
            str(entry["title"]),
            provider,
            "unavailable",
            "none",
            playback,
            reason="no provider binding is available",
        )
    )


def _canonical_lookup(manifest: dict[str, Any], provider: str) -> dict[str, Any]:
    """Embed exact canonical recording identity needed by a live provider resolver."""
    raw_recordings = manifest.get("recordings")
    if not isinstance(raw_recordings, list) or not raw_recordings:
        raise ValueError("canonical manifest must contain at least one recording")

    recordings: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_recordings):
        if not isinstance(raw, dict):
            raise ValueError(f"canonical manifest recording {index} is not an object")
        item: dict[str, Any] = {}

        mbid = raw.get("musicbrainz_recording_id")
        if isinstance(mbid, str) and mbid:
            item["musicbrainz_recording_id"] = mbid.lower()

        isrcs = raw.get("isrcs")
        if isinstance(isrcs, list) and isrcs:
            item["isrcs"] = sorted(
                {
                    value.upper()
                    for value in isrcs
                    if isinstance(value, str) and value
                }
            )

        overrides = raw.get("provider_overrides")
        if isinstance(overrides, dict):
            override = overrides.get(provider)
            if isinstance(override, str) and override:
                item["provider_override"] = override

        if "musicbrainz_recording_id" not in item and not item.get("isrcs"):
            raise ValueError(
                f"canonical manifest recording {index} has no service-neutral identity"
            )
        recordings.append(item)

    return {
        "type": "canonical_manifest",
        "recording_count": len(recordings),
        "recordings": recordings,
    }


def _canonical_plan(
    entry: dict[str, Any],
    provider: str,
    manifest: dict[str, Any],
    provider_index: dict[str, Any] | None,
) -> PlaybackPlan:
    identity, playback = _identity_and_playback(entry, provider)
    binding = entry.get("providers", {}).get(provider)
    if isinstance(binding, dict) and binding.get("strategy") == "unsupported":
        return _finish(
            PlaybackPlan(
                identity.id6,
                identity.machine_id,
                str(entry["title"]),
                provider,
                "unavailable",
                "none",
                playback,
                strategy="unsupported",
                reason="catalog explicitly marks this provider unsupported",
            )
        )

    if str(manifest.get("disc_id")) != identity.id6:
        raise ValueError("canonical manifest disc_id does not match entry")

    if provider_index is None:
        return _finish(
            PlaybackPlan(
                identity.id6,
                identity.machine_id,
                str(entry["title"]),
                provider,
                "requires_lookup",
                "recording_resolution",
                playback,
                strategy=(
                    str(binding.get("strategy"))
                    if isinstance(binding, dict) and binding.get("strategy") is not None
                    else None
                ),
                lookup=_canonical_lookup(manifest, provider),
                reason="a provider/local index is required to resolve canonical recordings",
            )
        )

    if provider_index.get("provider") != provider:
        raise ValueError(
            f"provider index is for {provider_index.get('provider')!r}, "
            f"not requested provider {provider!r}"
        )

    resolution: ResolutionPlan = resolve_canonical_manifest(
        entry, manifest, provider_index
    )
    resolved_resources = tuple(
        item.resource
        for item in resolution.items
        if item.status == "resolved" and item.resource is not None
    )

    if resolution.ambiguous_count:
        status = "ambiguous"
    elif resolution.resolved_count == resolution.total_recordings:
        status = "ready"
    elif resolution.resolved_count:
        status = "partial"
    else:
        status = "unavailable"

    return _finish(
        PlaybackPlan(
            identity.id6,
            identity.machine_id,
            str(entry["title"]),
            provider,
            status,
            "track_list" if resolved_resources else "none",
            playback,
            strategy=(
                str(binding.get("strategy"))
                if isinstance(binding, dict) and binding.get("strategy") is not None
                else "resolve"
            ),
            resources=resolved_resources,
            resolution=resolution.to_dict(),
            reason=(
                None
                if status == "ready"
                else "canonical provider coverage is incomplete or ambiguous"
            ),
        )
    )


def compile_catalog_playback(
    entry: dict[str, Any],
    provider: str,
    *,
    manifest: dict[str, Any] | None = None,
    provider_index: dict[str, Any] | None = None,
) -> PlaybackPlan:
    """Compile one catalog entry into an offline provider-specific playback plan."""
    definition = entry.get("definition")
    if not isinstance(definition, dict):
        raise ValueError("entry is missing definition")
    definition_type = definition.get("type")

    if definition_type == "canonical_manifest":
        if manifest is None:
            raise ValueError("canonical_manifest entry requires its manifest")
        return _canonical_plan(entry, provider, manifest, provider_index)

    if definition_type == "provider_native":
        native_provider = definition.get("provider")
        if native_provider != provider:
            identity, playback = _identity_and_playback(entry, provider)
            return _finish(
                PlaybackPlan(
                    identity.id6,
                    identity.machine_id,
                    str(entry["title"]),
                    provider,
                    "unavailable",
                    "none",
                    playback,
                    reason=f"entry is native to provider {native_provider!r}",
                )
            )
        return _binding_plan(entry, provider)

    if definition_type == "federated_collection":
        return _binding_plan(entry, provider)

    if definition_type == "artist_catalog":
        return _binding_plan(
            entry,
            provider,
            fallback_lookup={
                "type": "artist",
                "musicbrainz_id": definition["musicbrainz_artist_id"],
            },
        )

    if definition_type == "album":
        return _binding_plan(
            entry,
            provider,
            fallback_lookup={
                "type": "release_group",
                "musicbrainz_id": definition["musicbrainz_release_group_id"],
            },
        )

    if definition_type == "diagnostic":
        identity, playback = _identity_and_playback(entry, provider)
        return _finish(
            PlaybackPlan(
                identity.id6,
                identity.machine_id,
                str(entry["title"]),
                provider,
                "unplayable",
                "none",
                playback,
                reason="diagnostic catalog entries do not identify user music",
            )
        )

    raise ValueError(f"unsupported catalog definition type {definition_type!r}")


def compile_local_playback(
    entry: dict[str, Any],
    provider: str,
) -> PlaybackPlan:
    """Compile one private/local mapping into the same playback-plan contract."""
    identity, playback = _identity_and_playback(entry, provider)
    binding = entry.get("bindings", {}).get(provider)
    if isinstance(binding, dict):
        resource = binding.get("resource")
        if isinstance(resource, str) and resource:
            return _finish(
                PlaybackPlan(
                    identity.id6,
                    identity.machine_id,
                    str(entry["title"]),
                    provider,
                    "ready",
                    "direct_resource",
                    playback,
                    strategy="local_binding",
                    resource=resource,
                )
            )

    return _finish(
        PlaybackPlan(
            identity.id6,
            identity.machine_id,
            str(entry["title"]),
            provider,
            "unavailable",
            "none",
            playback,
            reason="private/local entry has no binding for the requested provider",
        )
    )
