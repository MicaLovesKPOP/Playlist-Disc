"""PDv1 catalog loading and JSON Schema validation."""

from __future__ import annotations

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


def load_schema(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_entry(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    messages = []
    for error in errors:
        location = ".".join(str(x) for x in error.path) or "<root>"
        messages.append(f"{location}: {error.message}")
    if not messages and "id" in data:
        ident = PDIdentity.parse(str(data["id"]))
        if ident.namespace not in {"public", "test"}:
            messages.append(f"id: registry entry uses {ident.namespace!r} namespace")
    return messages


def iter_entries(catalog_dir: str | Path) -> Iterable[Path]:
    root = Path(catalog_dir) / "discs"
    yield from sorted(root.rglob("*.yaml"))


def find_entry(catalog_dir: str | Path, identity: PDIdentity) -> tuple[Path, dict[str, Any]] | None:
    for path in iter_entries(catalog_dir):
        data = load_yaml(path)
        if str(data.get("id", "")).zfill(6) == identity.id6:
            return path, data
    return None
