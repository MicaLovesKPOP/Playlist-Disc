"""Deterministic local cache records for materialized track-list playback plans."""

from __future__ import annotations

from importlib.resources import files
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from jsonschema import Draft202012Validator

from .identity import PDIdentity
from .playback import validate_playback_plan


def load_materialization_schema() -> dict[str, Any]:
    resource = files("playlistdisc").joinpath("schemas/materialization.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def _canonical_json(data: dict[str, Any]) -> bytes:
    return json.dumps(
        data,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def plan_fingerprint(plan: dict[str, Any]) -> str:
    """Return the cache key for the complete provider-facing playback plan."""
    errors = validate_playback_plan(plan)
    if errors:
        raise ValueError("invalid playback plan: " + "; ".join(errors))
    return hashlib.sha256(_canonical_json(plan)).hexdigest()


def scope_fingerprint(scope: str) -> str:
    """Hash a local account/profile scope without storing it in plaintext."""
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("materialization scope must be a non-empty string")
    return hashlib.sha256(scope.encode("utf-8")).hexdigest()


def _cacheable_plan(plan: dict[str, Any]) -> None:
    errors = validate_playback_plan(plan)
    if errors:
        raise ValueError("invalid playback plan: " + "; ".join(errors))
    if plan["mode"] != "track_list":
        raise ValueError(
            "materialization cache currently supports only deterministic track_list plans"
        )
    if plan["status"] not in {"ready", "partial"}:
        raise ValueError(
            "materialization cache requires a ready or partial track_list plan"
        )
    resources = plan.get("resources")
    if not isinstance(resources, list) or not resources:
        raise ValueError("track_list materialization requires at least one source resource")


def materialization_path(
    cache_root: str | Path,
    plan: dict[str, Any],
    scope: str,
) -> Path:
    _cacheable_plan(plan)
    provider = str(plan["provider"])
    disc_id = str(plan["disc_id"])
    scope_sha = scope_fingerprint(scope)
    return Path(cache_root) / provider / scope_sha / f"{disc_id}.json"


def make_materialization_record(
    plan: dict[str, Any],
    *,
    scope: str,
    materialized_resource: str,
    provider_revision: str | None = None,
) -> dict[str, Any]:
    _cacheable_plan(plan)
    if not isinstance(materialized_resource, str) or not materialized_resource.strip():
        raise ValueError("materialized resource must be a non-empty string")

    record: dict[str, Any] = {
        "schema_version": 1,
        "format": "PDv1-materialization",
        "provider": plan["provider"],
        "disc_id": plan["disc_id"],
        "machine_id": plan["machine_id"],
        "scope_sha256": scope_fingerprint(scope),
        "plan_sha256": plan_fingerprint(plan),
        "plan_status": plan["status"],
        "mode": "track_list",
        "source_count": len(plan["resources"]),
        "materialized_resource": materialized_resource,
    }
    if provider_revision is not None:
        if not provider_revision.strip():
            raise ValueError("provider_revision must be non-empty when supplied")
        record["provider_revision"] = provider_revision
    errors = validate_materialization_record(record)
    if errors:
        raise ValueError("generated materialization record is invalid: " + "; ".join(errors))
    return record


def validate_materialization_record(
    data: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> list[str]:
    schema = schema or load_materialization_schema()
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
    return messages


def compare_materialization(
    record: dict[str, Any],
    plan: dict[str, Any],
    *,
    scope: str,
) -> list[str]:
    """Return stale/invalid reasons. Empty means the cache record is reusable."""
    record_errors = validate_materialization_record(record)
    if record_errors:
        return [f"record:{message}" for message in record_errors]

    try:
        _cacheable_plan(plan)
    except ValueError as exc:
        return [f"plan:{exc}"]

    expected = {
        "provider": plan["provider"],
        "disc_id": plan["disc_id"],
        "machine_id": plan["machine_id"],
        "scope_sha256": scope_fingerprint(scope),
        "plan_sha256": plan_fingerprint(plan),
        "plan_status": plan["status"],
        "source_count": len(plan["resources"]),
    }
    messages: list[str] = []
    for field, value in expected.items():
        if record.get(field) != value:
            messages.append(
                f"{field}: cached value {record.get(field)!r} != current {value!r}"
            )
    return messages


def write_materialization(
    cache_root: str | Path,
    plan: dict[str, Any],
    *,
    scope: str,
    materialized_resource: str,
    provider_revision: str | None = None,
) -> Path:
    """Atomically create/replace the cache record for one provider/scope/disc."""
    record = make_materialization_record(
        plan,
        scope=scope,
        materialized_resource=materialized_resource,
        provider_revision=provider_revision,
    )
    path = materialization_path(cache_root, plan, scope)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return path


def read_materialization(
    cache_root: str | Path,
    plan: dict[str, Any],
    *,
    scope: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Return (record, reasons). Missing/stale records are never treated as hits."""
    path = materialization_path(cache_root, plan, scope)
    if not path.is_file():
        return None, ["cache record does not exist"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"cache record is unreadable: {exc}"]
    if not isinstance(data, dict):
        return None, ["cache record is not a JSON object"]
    reasons = compare_materialization(data, plan, scope=scope)
    return (data if not reasons else None), reasons
