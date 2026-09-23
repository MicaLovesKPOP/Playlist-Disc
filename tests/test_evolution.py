import copy
import json
from pathlib import Path

import yaml

from playlistdisc.evolution import (
    check_catalog_evolution,
    snapshot_membership_fingerprint,
)


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _entry(
    id6: str = "042381",
    *,
    status: str = "active",
    definition: dict | None = None,
    lifecycle: str = "snapshot",
    order: str = "shuffle",
) -> dict:
    return {
        "schema_version": 1,
        "id": id6,
        "title": "K-Pop Girl Group Singles",
        "short_title": "KGG SNGL",
        "status": status,
        "definition": definition
        or {
            "type": "artist_catalog",
            "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555",
        },
        "provenance": {
            "authority": "community",
            "maintainers": ["maintainer"],
        },
        "lifecycle": lifecycle,
        "portability": "canonical",
        "playback": {"order": order, "start": "random", "repeat": "context"},
        "tags": ["k-pop", "girl-group"],
    }


def _write_entry(root: Path, entry: dict) -> None:
    id6 = entry["id"]
    _write_yaml(root / f"discs/{id6[:3]}/{id6}.yaml", entry)


def _manifest(id6: str = "042381") -> dict:
    return {
        "schema_version": 1,
        "disc_id": id6,
        "recordings": [
            {
                "musicbrainz_recording_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "isrcs": ["KRABC2600001"],
                "title_hint": "Track A",
                "artist_hint": "Group A",
                "provider_overrides": {"spotify": "spotify:track:old"},
            },
            {
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                "isrcs": ["KRABC2600002"],
                "title_hint": "Track B",
                "artist_hint": "Group B",
            },
        ],
    }


def test_active_public_semantic_fields_are_locked(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    old = _entry()
    _write_entry(baseline, old)

    changed = copy.deepcopy(old)
    changed["title"] = "Something Else"
    changed["playback"]["order"] = "ordered"
    changed["definition"]["musicbrainz_artist_id"] = (
        "99999999-2222-3333-4444-555555555555"
    )
    _write_entry(current, changed)

    errors = check_catalog_evolution(baseline, current)
    assert any(":title:" in error for error in errors)
    assert any(":playback:" in error for error in errors)
    assert any(":definition:" in error for error in errors)


def test_active_can_retire_but_retired_cannot_reactivate(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    old = _entry(status="active")
    _write_entry(baseline, old)
    retired = copy.deepcopy(old)
    retired["status"] = "retired"
    _write_entry(current, retired)
    assert check_catalog_evolution(baseline, current) == []

    baseline2 = tmp_path / "baseline2"
    current2 = tmp_path / "current2"
    _write_entry(baseline2, retired)
    reactivated = copy.deepcopy(retired)
    reactivated["status"] = "active"
    _write_entry(current2, reactivated)
    errors = check_catalog_evolution(baseline2, current2)
    assert any("retired public entry cannot transition" in error for error in errors)


def test_protected_public_entry_cannot_be_deleted(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    _write_entry(baseline, _entry())
    errors = check_catalog_evolution(baseline, current)
    assert any("cannot be deleted or renumbered" in error for error in errors)


def test_draft_public_entry_remains_editable_and_deletable(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    _write_entry(baseline, _entry(status="draft"))
    assert check_catalog_evolution(baseline, current) == []


def test_canonical_provider_bindings_remain_mutable(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    old = _entry()
    old["providers"] = {
        "spotify": {"strategy": "materialize", "resource": "old"}
    }
    _write_entry(baseline, old)

    new = copy.deepcopy(old)
    new["providers"] = {
        "spotify": {"strategy": "materialize", "resource": "new"},
        "apple_music": {"strategy": "materialize"},
    }
    new["tags"].append("singles")
    new["provenance"]["maintainers"] = ["new-maintainer"]
    _write_entry(current, new)
    assert check_catalog_evolution(baseline, current) == []


def test_provider_native_resource_is_locked(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    definition = {"type": "provider_native", "provider": "spotify"}
    old = _entry(definition=definition)
    old["portability"] = "provider_native"
    old["providers"] = {
        "spotify": {
            "strategy": "direct",
            "resource": "spotify:playlist:one",
            "market": "NL",
            "notes": "old note",
        }
    }
    _write_entry(baseline, old)

    new = copy.deepcopy(old)
    new["providers"]["spotify"]["resource"] = "spotify:playlist:two"
    new["providers"]["spotify"]["notes"] = "new note"
    _write_entry(current, new)

    errors = check_catalog_evolution(baseline, current)
    assert any("native provider resource/market" in error for error in errors)


def test_snapshot_manifest_membership_locked_but_hints_are_mutable(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    definition = {
        "type": "canonical_manifest",
        "manifest": "manifests/042/042381.json",
        "membership_policy": "Exact singles set.",
    }
    old = _entry(definition=definition, lifecycle="snapshot", order="shuffle")
    _write_entry(baseline, old)
    _write_json(baseline / definition["manifest"], _manifest())

    _write_entry(current, copy.deepcopy(old))
    current_manifest = _manifest()
    current_manifest["recordings"].reverse()
    current_manifest["recordings"][0]["title_hint"] = "Corrected title"
    current_manifest["recordings"][1]["provider_overrides"] = {
        "spotify": "spotify:track:new"
    }
    _write_json(current / definition["manifest"], current_manifest)

    assert (
        snapshot_membership_fingerprint(baseline, old)
        == snapshot_membership_fingerprint(current, old)
    )
    assert check_catalog_evolution(baseline, current) == []

    changed = copy.deepcopy(current_manifest)
    changed["recordings"].pop()
    _write_json(current / definition["manifest"], changed)
    errors = check_catalog_evolution(baseline, current)
    assert any("snapshot canonical membership is immutable" in error for error in errors)


def test_order_is_part_of_snapshot_membership_when_playback_is_ordered(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    definition = {
        "type": "canonical_manifest",
        "manifest": "manifests/042/042381.json",
        "membership_policy": "Exact ordered sequence.",
    }
    old = _entry(definition=definition, lifecycle="snapshot", order="ordered")
    _write_entry(baseline, old)
    _write_json(baseline / definition["manifest"], _manifest())

    _write_entry(current, copy.deepcopy(old))
    reversed_manifest = _manifest()
    reversed_manifest["recordings"].reverse()
    _write_json(current / definition["manifest"], reversed_manifest)

    errors = check_catalog_evolution(baseline, current)
    assert any("snapshot canonical membership is immutable" in error for error in errors)


def test_living_manifest_membership_can_evolve(tmp_path: Path):
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    definition = {
        "type": "canonical_manifest",
        "manifest": "manifests/042/042381.json",
        "membership_policy": "All qualifying releases.",
    }
    old = _entry(definition=definition, lifecycle="living")
    _write_entry(baseline, old)
    _write_json(baseline / definition["manifest"], _manifest())

    _write_entry(current, copy.deepcopy(old))
    changed = _manifest()
    changed["recordings"].pop()
    _write_json(current / definition["manifest"], changed)

    assert check_catalog_evolution(baseline, current) == []
