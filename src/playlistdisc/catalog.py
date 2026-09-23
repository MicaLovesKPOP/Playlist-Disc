"""PDv1 catalog loading, schema validation, and cross-file invariants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

from .identity import PDIdentity


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML object")
    return data


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def load_schema(path: str | Path) -> dict[str, Any]:
    return load_json(path)


def _schema_errors(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda error: [str(part) for part in error.path],
    )
    messages: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{location}: {error.message}")
    return messages


def validate_entry(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate one registry entry without requiring access to sibling files."""
    messages = _schema_errors(data, schema)
    if not messages and "id" in data:
        ident = PDIdentity.parse(str(data["id"]))
        if ident.namespace not in {"public", "test"}:
            messages.append(f"id: registry entry uses {ident.namespace!r} namespace")
    return messages


def validate_manifest(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate one canonical recording manifest, including ambiguity checks."""
    messages = _schema_errors(data, schema)
    if messages:
        return messages

    seen_mbids: set[str] = set()
    seen_isrcs: set[str] = set()
    for index, recording in enumerate(data.get("recordings", [])):
        mbid = recording.get("musicbrainz_recording_id")
        if mbid:
            normalized = mbid.lower()
            if normalized in seen_mbids:
                messages.append(
                    f"recordings.{index}.musicbrainz_recording_id: duplicate recording MBID {mbid}"
                )
            seen_mbids.add(normalized)

        for isrc in recording.get("isrcs", []):
            normalized = isrc.upper()
            if normalized in seen_isrcs:
                messages.append(
                    f"recordings.{index}.isrcs: ISRC {isrc} appears in more than one recording"
                )
            seen_isrcs.add(normalized)
    return messages


def iter_entries(catalog_dir: str | Path) -> Iterable[Path]:
    root = Path(catalog_dir) / "discs"
    yield from sorted(root.rglob("*.yaml"))


def find_entry(
    catalog_dir: str | Path, identity: PDIdentity
) -> tuple[Path, dict[str, Any]] | None:
    for path in iter_entries(catalog_dir):
        data = load_yaml(path)
        if str(data.get("id", "")).zfill(6) == identity.id6:
            return path, data
    return None


def _expected_entry_path(catalog_root: Path, id6: str) -> Path:
    return catalog_root / "discs" / id6[:3] / f"{id6}.yaml"


def _expected_manifest_path(catalog_root: Path, id6: str) -> Path:
    return catalog_root / "manifests" / id6[:3] / f"{id6}.json"


def _safe_catalog_relative_path(catalog_root: Path, value: str) -> Path | None:
    candidate = (catalog_root / value).resolve()
    root = catalog_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _entry_semantic_errors(
    data: dict[str, Any],
    *,
    path: Path,
    catalog_root: Path,
    entries_by_id: dict[str, tuple[Path, dict[str, Any]]],
    manifest_schema: dict[str, Any],
) -> list[str]:
    messages: list[str] = []
    id6 = str(data["id"])
    definition = data["definition"]
    definition_type = definition["type"]
    portability = data["portability"]

    expected_path = _expected_entry_path(catalog_root, id6)
    if path.resolve() != expected_path.resolve():
        messages.append(
            "path: catalog entry must live at "
            f"{expected_path.relative_to(catalog_root).as_posix()}"
        )

    if portability == "canonical" and definition_type in {
        "provider_native",
        "federated_collection",
    }:
        messages.append(
            f"portability: {definition_type!r} cannot be declared canonical"
        )
    if portability == "federated" and definition_type != "federated_collection":
        messages.append(
            "portability: federated entries must use definition.type "
            "'federated_collection'"
        )
    if portability == "provider_native" and definition_type != "provider_native":
        messages.append(
            "portability: provider_native entries must use definition.type "
            "'provider_native'"
        )

    providers = data.get("providers", {})
    if definition_type == "provider_native":
        provider = definition["provider"]
        binding = providers.get(provider)
        if not binding:
            messages.append(
                f"providers: provider-native entry must define binding for {provider!r}"
            )
        elif binding.get("strategy") != "direct":
            messages.append(
                f"providers.{provider}.strategy: provider-native binding must use 'direct'"
            )

    if definition_type == "federated_collection":
        if len(providers) < 2:
            messages.append(
                "providers: federated collection requires at least two provider bindings"
            )
        for provider, binding in providers.items():
            if binding.get("strategy") not in {"equivalent", "best_available"}:
                messages.append(
                    f"providers.{provider}.strategy: federated collection must use "
                    "'equivalent' or 'best_available'"
                )

    if definition_type == "canonical_manifest":
        relative_manifest = definition["manifest"]
        manifest_path = _safe_catalog_relative_path(catalog_root, relative_manifest)
        expected_manifest = _expected_manifest_path(catalog_root, id6)
        if manifest_path is None:
            messages.append("definition.manifest: path escapes the catalog directory")
        elif manifest_path.resolve() != expected_manifest.resolve():
            messages.append(
                "definition.manifest: canonical manifest must live at "
                f"{expected_manifest.relative_to(catalog_root).as_posix()}"
            )
        elif not manifest_path.is_file():
            messages.append(f"definition.manifest: missing file {relative_manifest}")
        else:
            manifest = load_json(manifest_path)
            manifest_errors = validate_manifest(manifest, manifest_schema)
            messages.extend(
                f"manifest:{message}" for message in manifest_errors
            )
            if not manifest_errors and manifest["disc_id"] != id6:
                messages.append(
                    "manifest:disc_id: manifest identity does not match catalog entry"
                )

    successor = data.get("successor")
    if successor:
        if successor == id6:
            messages.append("successor: entry cannot succeed itself")
        elif successor not in entries_by_id:
            messages.append(f"successor: referenced catalog ID {successor} does not exist")

    return messages


def validate_catalog(
    catalog_dir: str | Path,
    *,
    entry_schema_path: str | Path | None = None,
    manifest_schema_path: str | Path | None = None,
) -> list[str]:
    """Validate the whole public catalog, including cross-file invariants."""
    catalog_root = Path(catalog_dir)
    entry_schema = load_schema(
        entry_schema_path or catalog_root / "schema" / "disc.schema.json"
    )
    manifest_schema = load_schema(
        manifest_schema_path
        or catalog_root / "schema" / "canonical-manifest.schema.json"
    )

    messages: list[str] = []
    parsed: list[tuple[Path, dict[str, Any]]] = []
    entries_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}

    for path in iter_entries(catalog_root):
        try:
            data = load_yaml(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            messages.append(f"{path}: {exc}")
            continue

        errors = validate_entry(data, entry_schema)
        if errors:
            messages.extend(f"{path}:{message}" for message in errors)
            continue

        id6 = str(data["id"])
        if id6 in entries_by_id:
            previous = entries_by_id[id6][0]
            messages.append(f"{path}:id: duplicate of {previous}")
            continue
        entries_by_id[id6] = (path, data)
        parsed.append((path, data))

    for path, data in parsed:
        for message in _entry_semantic_errors(
            data,
            path=path,
            catalog_root=catalog_root,
            entries_by_id=entries_by_id,
            manifest_schema=manifest_schema,
        ):
            messages.append(f"{path}:{message}")

    return messages


def manifest_metadata(catalog_dir: str | Path, data: dict[str, Any]) -> dict[str, Any] | None:
    """Return generated immutable-ish metadata for a canonical manifest entry."""
    if data.get("definition", {}).get("type") != "canonical_manifest":
        return None
    root = Path(catalog_dir)
    path = _safe_catalog_relative_path(root, data["definition"]["manifest"])
    if path is None or not path.is_file():
        return None
    raw = path.read_bytes()
    manifest = load_json(path)
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "recording_count": len(manifest.get("recordings", [])),
    }
