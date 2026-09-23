"""Static-library snapshots, pack resolution, and deterministic catalog search."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .catalog import (
    find_pack,
    iter_entries,
    iter_packs,
    load_yaml,
    manifest_metadata,
)
from .identity import PDIdentity


def entry_snapshot(catalog_dir: str | Path, data: dict[str, Any]) -> dict[str, Any]:
    """Add deterministic physical metadata to one validated catalog entry."""
    ident = PDIdentity.parse(str(data["id"]))
    item = dict(data)
    item["machine_id"] = ident.machine_id
    item["namespace"] = ident.namespace
    item["track_durations_seconds"] = list(ident.track_durations)
    item["toc_sha256"] = ident.toc_signature
    manifest = manifest_metadata(catalog_dir, data)
    if manifest is not None:
        item["canonical_manifest"] = manifest
    return item


def catalog_entries(catalog_dir: str | Path) -> list[dict[str, Any]]:
    entries = [entry_snapshot(catalog_dir, load_yaml(path)) for path in iter_entries(catalog_dir)]
    entries.sort(key=lambda item: item["id"])
    return entries


def resolved_pack(
    catalog_dir: str | Path,
    data: dict[str, Any],
    *,
    entries_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve an ordered source pack into wallet slots with catalog summaries."""
    if entries_by_id is None:
        entries_by_id = {entry["id"]: entry for entry in catalog_entries(catalog_dir)}

    item = dict(data)
    item["disc_count"] = len(data["discs"])
    item["slots"] = []
    for slot, id6 in enumerate(data["discs"], start=1):
        entry = entries_by_id[id6]
        item["slots"].append(
            {
                "slot": slot,
                "id": id6,
                "machine_id": entry["machine_id"],
                "title": entry["title"],
                "short_title": entry["short_title"],
                "status": entry["status"],
                "tags": entry["tags"],
            }
        )
    return item


def catalog_packs(
    catalog_dir: str | Path,
    *,
    entries: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if entries is None:
        entries = catalog_entries(catalog_dir)
    entries_by_id = {entry["id"]: entry for entry in entries}
    packs = [
        resolved_pack(catalog_dir, load_yaml(path), entries_by_id=entries_by_id)
        for path in iter_packs(catalog_dir)
    ]
    packs.sort(key=lambda item: item["slug"])
    return packs


def library_snapshot(catalog_dir: str | Path) -> dict[str, Any]:
    """Build the provider-neutral JSON payload intended for static-library clients."""
    entries = catalog_entries(catalog_dir)
    packs = catalog_packs(catalog_dir, entries=entries)
    return {
        "schema_version": 1,
        "format": "PDv1-library",
        "entries": entries,
        "packs": packs,
        "facets": {
            "statuses": sorted({entry["status"] for entry in entries}),
            "definition_types": sorted(
                {entry["definition"]["type"] for entry in entries}
            ),
            "portability": sorted({entry["portability"] for entry in entries}),
            "tags": sorted(
                {tag for entry in entries for tag in entry.get("tags", [])}
            ),
            "pack_tags": sorted(
                {tag for pack in packs for tag in pack.get("tags", [])}
            ),
        },
    }


def pack_by_slug(catalog_dir: str | Path, slug: str) -> dict[str, Any] | None:
    found = find_pack(catalog_dir, slug)
    if found is None:
        return None
    _, data = found
    entries = catalog_entries(catalog_dir)
    entries_by_id = {entry["id"]: entry for entry in entries}
    return resolved_pack(catalog_dir, data, entries_by_id=entries_by_id)


def _flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _flatten_strings(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _flatten_strings(nested)


def _searchable_text(entry: dict[str, Any]) -> str:
    fields = {
        "id": entry["id"],
        "machine_id": entry["machine_id"],
        "title": entry["title"],
        "short_title": entry["short_title"],
        "status": entry["status"],
        "family": entry.get("family", ""),
        "definition": entry["definition"],
        "provenance": entry["provenance"],
        "lifecycle": entry["lifecycle"],
        "portability": entry["portability"],
        "playback": entry["playback"],
        "tags": entry.get("tags", []),
        "providers": entry.get("providers", {}),
        "notes": entry.get("notes", ""),
    }
    return "\n".join(_flatten_strings(fields)).casefold()


def search_entries(
    entries: Iterable[dict[str, Any]],
    query: str,
    *,
    statuses: set[str] | None = None,
    tags: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic AND-token substring matches over semantic metadata."""
    tokens = [token.casefold() for token in query.split() if token.strip()]
    if not tokens:
        raise ValueError("search query must contain at least one non-whitespace token")

    required_tags = {tag.casefold() for tag in tags or set()}
    results: list[dict[str, Any]] = []
    for entry in entries:
        if statuses is not None and entry["status"] not in statuses:
            continue

        entry_tags = {tag.casefold() for tag in entry.get("tags", [])}
        if not required_tags.issubset(entry_tags):
            continue

        haystack = _searchable_text(entry)
        if all(token in haystack for token in tokens):
            results.append(entry)

    results.sort(key=lambda item: (item["title"].casefold(), item["id"]))
    return results


def search_catalog(
    catalog_dir: str | Path,
    query: str,
    *,
    statuses: set[str] | None = None,
    tags: set[str] | None = None,
) -> list[dict[str, Any]]:
    return search_entries(
        catalog_entries(catalog_dir),
        query,
        statuses=statuses,
        tags=tags,
    )
