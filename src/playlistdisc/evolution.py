"""Evolution policy for already-published public Playlist Disc identities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .catalog import iter_entries, load_json, load_yaml
from .identity import PDIdentity

_PROTECTED_STATUSES = {"active", "retired"}
_LOCKED_FIELDS = (
    "title",
    "short_title",
    "definition",
    "lifecycle",
    "portability",
    "playback",
)


def _entry_map(catalog_dir: str | Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in iter_entries(catalog_dir):
        data = load_yaml(path)
        id6 = str(data.get("id", ""))
        if len(id6) == 6 and id6.isascii() and id6.isdigit():
            result[id6] = data
    return result


def _canonical_manifest_path(
    catalog_dir: str | Path, entry: dict[str, Any]
) -> Path | None:
    definition = entry.get("definition", {})
    if definition.get("type") != "canonical_manifest":
        return None
    relative = definition.get("manifest")
    if not isinstance(relative, str):
        return None
    return Path(catalog_dir) / relative


def _recording_identity(recording: dict[str, Any]) -> dict[str, Any]:
    mbid = recording.get("musicbrainz_recording_id")
    isrcs = recording.get("isrcs", [])
    return {
        "musicbrainz_recording_id": mbid.lower() if isinstance(mbid, str) else None,
        "isrcs": sorted(
            value.upper() for value in isrcs if isinstance(value, str)
        ),
    }


def snapshot_membership_fingerprint(
    catalog_dir: str | Path, entry: dict[str, Any]
) -> str:
    """Hash service-neutral canonical membership, excluding hints/overrides."""
    path = _canonical_manifest_path(catalog_dir, entry)
    if path is None or not path.is_file():
        raise ValueError("canonical manifest is missing")
    manifest = load_json(path)
    recordings = [
        _recording_identity(recording)
        for recording in manifest.get("recordings", [])
        if isinstance(recording, dict)
    ]

    playback = entry.get("playback", {})
    if playback.get("order") == "shuffle":
        recordings.sort(
            key=lambda value: json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
        )

    payload = {
        "disc_id": str(entry.get("id", "")),
        "recordings": recordings,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _provider_native_identity(entry: dict[str, Any]) -> dict[str, Any] | None:
    definition = entry.get("definition", {})
    if definition.get("type") != "provider_native":
        return None
    provider = definition.get("provider")
    binding = entry.get("providers", {}).get(provider, {})
    return {
        "provider": provider,
        "strategy": binding.get("strategy"),
        "resource": binding.get("resource"),
        "market": binding.get("market"),
    }


def _status_transition_error(old: str, new: str) -> str | None:
    if old == "active" and new not in {"active", "retired"}:
        return f"status: active public entry cannot transition to {new!r}"
    if old == "retired" and new != "retired":
        return f"status: retired public entry cannot transition to {new!r}"
    return None


def check_catalog_evolution(
    baseline_catalog: str | Path,
    current_catalog: str | Path,
) -> list[str]:
    """Return violations of the physical/public identity evolution policy.

    Draft/test records and public records that were still draft in the baseline
    remain editable. Once a public record is active (or later retired), its
    semantic core is locked because physical copies may exist in the world.
    """
    baseline = _entry_map(baseline_catalog)
    current = _entry_map(current_catalog)
    errors: list[str] = []

    for id6, old in sorted(baseline.items()):
        try:
            identity = PDIdentity.parse(id6)
        except ValueError:
            continue
        if identity.namespace != "public":
            continue

        old_status = old.get("status")
        if old_status not in _PROTECTED_STATUSES:
            continue

        new = current.get(id6)
        prefix = f"PD1-{id6}"
        if new is None:
            errors.append(
                f"{prefix}: protected public entry cannot be deleted or renumbered"
            )
            continue

        new_status = str(new.get("status"))
        transition_error = _status_transition_error(str(old_status), new_status)
        if transition_error:
            errors.append(f"{prefix}:{transition_error}")

        for field in _LOCKED_FIELDS:
            if old.get(field) != new.get(field):
                errors.append(
                    f"{prefix}:{field}: semantic field is immutable after activation"
                )

        old_native = _provider_native_identity(old)
        if old_native is not None:
            new_native = _provider_native_identity(new)
            if old_native != new_native:
                errors.append(
                    f"{prefix}:providers: native provider resource/market is "
                    "immutable after activation"
                )

        if (
            old.get("definition", {}).get("type") == "canonical_manifest"
            and old.get("lifecycle") == "snapshot"
        ):
            try:
                old_fingerprint = snapshot_membership_fingerprint(
                    baseline_catalog, old
                )
                new_fingerprint = snapshot_membership_fingerprint(
                    current_catalog, new
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(
                    f"{prefix}:manifest: cannot compare snapshot membership: {exc}"
                )
            else:
                if old_fingerprint != new_fingerprint:
                    errors.append(
                        f"{prefix}:manifest: snapshot canonical membership is "
                        "immutable after activation"
                    )

    return errors
