"""Local/private PDv1 registry workflows.

Private IDs are intentionally not part of the public catalog. This module keeps
personal mappings in a user-selected directory without accounts, telemetry, or
central allocation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

from .catalog import load_yaml
from .identity import PRIVATE_MAX, PRIVATE_MIN, PDIdentity


LOCAL_ENTRY_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "PDv1 local/private entry",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "id",
        "title",
        "short_title",
        "bindings",
        "playback",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "id": {"type": "string", "pattern": "^[0-9]{6}$"},
        "title": {"type": "string", "minLength": 1, "maxLength": 160},
        "short_title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 32,
            "pattern": "^[ -~]+$",
        },
        "bindings": {
            "type": "object",
            "minProperties": 1,
            "propertyNames": {"pattern": "^[a-z0-9][a-z0-9_-]*$"},
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "required": ["resource"],
                "properties": {
                    "resource": {"type": "string", "minLength": 1},
                    "notes": {"type": "string"},
                },
            },
        },
        "playback": {
            "type": "object",
            "additionalProperties": False,
            "required": ["order", "start", "repeat"],
            "properties": {
                "order": {"enum": ["ordered", "shuffle"]},
                "start": {"enum": ["first", "random", "resume"]},
                "repeat": {"enum": ["off", "context", "one"]},
            },
        },
        "tags": {
            "type": "array",
            "items": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
            "uniqueItems": True,
        },
        "notes": {"type": "string"},
    },
}


def _schema_errors(data: dict[str, Any]) -> list[str]:
    errors = sorted(
        Draft202012Validator(LOCAL_ENTRY_SCHEMA).iter_errors(data),
        key=lambda error: [str(part) for part in error.path],
    )
    messages: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{location}: {error.message}")
    return messages


def iter_local_entries(library_dir: str | Path) -> Iterable[Path]:
    root = Path(library_dir) / "discs"
    if not root.exists():
        return
    yield from sorted(root.rglob("*.yaml"))


def _expected_entry_path(library_root: Path, id6: str) -> Path:
    return library_root / "discs" / id6[:3] / f"{id6}.yaml"


def validate_local_entry(data: dict[str, Any]) -> list[str]:
    """Validate one private record independently of its filesystem location."""
    messages = _schema_errors(data)
    if messages:
        return messages

    ident = PDIdentity.parse(data["id"])
    if ident.namespace != "private":
        messages.append(f"id: local entry uses {ident.namespace!r} namespace")
    return messages


def validate_local_library(library_dir: str | Path) -> list[str]:
    """Validate all records, paths, and duplicate IDs in a local library."""
    root = Path(library_dir)
    messages: list[str] = []
    seen: dict[str, Path] = {}

    for path in iter_local_entries(root):
        try:
            data = load_yaml(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            messages.append(f"{path}: {exc}")
            continue

        errors = validate_local_entry(data)
        if errors:
            messages.extend(f"{path}:{message}" for message in errors)
            continue

        id6 = data["id"]
        expected = _expected_entry_path(root, id6)
        if path.resolve() != expected.resolve():
            messages.append(
                f"{path}:path: local entry must live at "
                f"{expected.relative_to(root).as_posix()}"
            )

        if id6 in seen:
            messages.append(f"{path}:id: duplicate of {seen[id6]}")
        else:
            seen[id6] = path

    return messages


def find_local_entry(
    library_dir: str | Path, identity: PDIdentity
) -> tuple[Path, dict[str, Any]] | None:
    if identity.namespace != "private":
        return None
    path = _expected_entry_path(Path(library_dir), identity.id6)
    if not path.is_file():
        return None
    data = load_yaml(path)
    errors = validate_local_entry(data)
    if errors:
        raise ValueError(f"invalid local entry {path}: {'; '.join(errors)}")
    return path, data


def _used_private_numbers(library_dir: str | Path) -> set[int]:
    used: set[int] = set()
    for path in iter_local_entries(library_dir):
        if len(path.stem) == 6 and path.stem.isdigit():
            number = int(path.stem)
            if PRIVATE_MIN <= number <= PRIVATE_MAX:
                used.add(number)
        try:
            data = load_yaml(path)
            ident = PDIdentity.parse(str(data.get("id", "")))
        except (OSError, ValueError, yaml.YAMLError):
            continue
        if ident.namespace == "private":
            used.add(ident.number)
    return used


def allocate_private_identity(
    library_dir: str | Path, preferred: int | str | None = None
) -> PDIdentity:
    """Return an unused private identity, choosing the lowest free ID by default."""
    used = _used_private_numbers(library_dir)

    if preferred is not None:
        ident = PDIdentity.parse(preferred)
        if ident.namespace != "private":
            raise ValueError("local/private IDs must be in 900000-989999")
        if ident.number in used:
            raise FileExistsError(f"private ID {ident.id6} is already in use")
        return ident

    for number in range(PRIVATE_MIN, PRIVATE_MAX + 1):
        if number not in used:
            return PDIdentity(number)
    raise RuntimeError("local/private namespace is full")


def create_local_entry(
    library_dir: str | Path,
    *,
    title: str,
    short_title: str,
    bindings: dict[str, str],
    preferred_id: int | str | None = None,
    order: str = "ordered",
    start: str = "first",
    repeat: str = "context",
    tags: list[str] | None = None,
    notes: str | None = None,
) -> tuple[PDIdentity, Path, dict[str, Any]]:
    """Allocate and atomically create one local/private mapping."""
    ident = allocate_private_identity(library_dir, preferred_id)
    data: dict[str, Any] = {
        "schema_version": 1,
        "id": ident.id6,
        "title": title,
        "short_title": short_title,
        "bindings": {
            provider: {"resource": resource}
            for provider, resource in sorted(bindings.items())
        },
        "playback": {"order": order, "start": start, "repeat": repeat},
    }
    if tags:
        data["tags"] = tags
    if notes:
        data["notes"] = notes

    errors = validate_local_entry(data)
    if errors:
        raise ValueError("invalid local entry: " + "; ".join(errors))

    root = Path(library_dir)
    path = _expected_entry_path(root, ident.id6)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)
    except FileExistsError:
        raise FileExistsError(f"private ID {ident.id6} is already in use") from None
    return ident, path, data
