"""Compatibility-profile validation and deterministic export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

from .catalog import load_schema, load_yaml
from .identity import PDIdentity
from .testkit import VARIANTS

_TEST_VARIANTS = {variant.name: variant for variant in VARIANTS}


def iter_compatibility_profiles(root: str | Path) -> Iterable[Path]:
    base = Path(root) / "vehicles"
    if not base.exists():
        return
    yield from sorted(base.glob("*.yaml"))


def validate_compatibility_profile(
    data: dict[str, Any], schema: dict[str, Any]
) -> list[str]:
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

    reports = data["reports"]
    status = data["status"]
    if status == "planned" and reports:
        messages.append("status: planned profile cannot already contain test reports")
    if status in {"partial", "tested"} and not reports:
        messages.append(f"status: {status} profile requires at least one test report")

    seen: set[str] = set()
    for index, report in enumerate(reports):
        report_id = report["report_id"]
        if report_id in seen:
            messages.append(f"reports.{index}.report_id: duplicate report ID {report_id}")
        seen.add(report_id)

        try:
            identity = PDIdentity.parse(report["disc_machine_id"])
        except ValueError as exc:
            messages.append(f"reports.{index}.disc_machine_id: {exc}")
        else:
            if identity.namespace != "test":
                messages.append(
                    f"reports.{index}.disc_machine_id: physical Draft 0.2 tests "
                    "must use the development/test namespace"
                )

        test_variant = report.get("test_variant")
        if test_variant is not None:
            variant = _TEST_VARIANTS.get(test_variant)
            if variant is None:
                messages.append(
                    f"reports.{index}.test_variant: unknown Draft 0.2 test-kit variant {test_variant!r}"
                )
            else:
                expected_identity = PDIdentity(variant.id_number)
                if report["disc_machine_id"] != expected_identity.machine_id:
                    messages.append(
                        f"reports.{index}.disc_machine_id: does not match test variant {test_variant!r}"
                    )
                if report["media"]["cd_text"] is not variant.cd_text:
                    messages.append(
                        f"reports.{index}.media.cd_text: does not match test variant {test_variant!r}"
                    )

        attempts = report.get("attempts")
        if attempts and attempts["successful_loads"] > attempts["total"]:
            messages.append(
                f"reports.{index}.attempts: successful_loads cannot exceed total"
            )
    return messages


def validate_compatibility(root: str | Path) -> list[str]:
    base = Path(root)
    schema = load_schema(base / "schema" / "profile.schema.json")
    messages: list[str] = []
    seen_profiles: set[str] = set()

    for path in iter_compatibility_profiles(base):
        try:
            data = load_yaml(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            messages.append(f"{path}: {exc}")
            continue

        errors = validate_compatibility_profile(data, schema)
        messages.extend(f"{path}:{message}" for message in errors)
        if errors:
            continue

        profile_id = data["profile_id"]
        expected = base / "vehicles" / f"{profile_id}.yaml"
        if path.resolve() != expected.resolve():
            messages.append(
                f"{path}:path: profile must live at "
                f"vehicles/{profile_id}.yaml"
            )
        if profile_id in seen_profiles:
            messages.append(f"{path}:profile_id: duplicate {profile_id}")
        seen_profiles.add(profile_id)
    return messages


def compatibility_snapshot(root: str | Path) -> dict[str, Any]:
    errors = validate_compatibility(root)
    if errors:
        raise ValueError("invalid compatibility data: " + "; ".join(errors))

    profiles: list[dict[str, Any]] = []
    for path in iter_compatibility_profiles(root):
        data = load_yaml(path)
        item = dict(data)
        item["report_count"] = len(item["reports"])
        profiles.append(item)
    profiles.sort(key=lambda item: item["profile_id"])

    return {
        "schema_version": 1,
        "format": "PDv1-compatibility",
        "profiles": profiles,
        "summary": {
            "profile_count": len(profiles),
            "report_count": sum(item["report_count"] for item in profiles),
            "research_evidence_count": sum(
                len(item.get("research_evidence", [])) for item in profiles
            ),
            "statuses": {
                status: sum(1 for item in profiles if item["status"] == status)
                for status in ("planned", "partial", "tested")
            },
        },
    }


def write_compatibility_snapshot(root: str | Path, output: str | Path) -> Path:
    payload = compatibility_snapshot(root)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
