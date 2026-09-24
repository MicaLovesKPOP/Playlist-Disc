import json
from pathlib import Path

import yaml

from playlistdisc.catalog import (
    load_schema,
    load_yaml,
    validate_catalog,
    validate_entry,
    validate_manifest,
)

ROOT = Path(__file__).parents[1]
ENTRY_SCHEMA = ROOT / "catalog/schema/disc.schema.json"
MANIFEST_SCHEMA = ROOT / "catalog/schema/canonical-manifest.schema.json"
PACK_SCHEMA = ROOT / "catalog/schema/pack.schema.json"


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _base_entry(id6: str, definition: dict, portability: str = "canonical") -> dict:
    return {
        "schema_version": 1,
        "id": id6,
        "title": "Test collection",
        "short_title": "TEST",
        "status": "draft",
        "definition": definition,
        "provenance": {"authority": "community", "maintainers": ["tester"]},
        "lifecycle": "snapshot",
        "portability": portability,
        "playback": {"order": "shuffle", "start": "random", "repeat": "context"},
        "tags": ["test"],
    }


def test_draft_catalog_validates():
    assert validate_catalog(ROOT / "catalog") == []


def test_single_entry_schema_still_validates_test_vectors():
    schema = load_schema(ENTRY_SCHEMA)
    data = load_yaml(ROOT / "catalog/discs/999/999901.yaml")
    assert validate_entry(data, schema) == []


def test_canonical_manifest_schema_and_cross_file_validation(tmp_path: Path):
    catalog = tmp_path / "catalog"
    id6 = "042381"
    manifest_rel = f"manifests/{id6[:3]}/{id6}.json"
    entry = _base_entry(
        id6,
        {
            "type": "canonical_manifest",
            "manifest": manifest_rel,
            "membership_policy": "Exact service-neutral recording set.",
        },
    )
    _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", entry)
    _write_json(
        catalog / manifest_rel,
        {
            "schema_version": 1,
            "disc_id": id6,
            "recordings": [
                {
                    "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                    "title_hint": "Example A",
                },
                {
                    "isrcs": ["KRABC2600001"],
                    "title_hint": "Example B",
                },
            ],
        },
    )
    assert validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
    ) == []


def test_catalog_reports_unreadable_canonical_manifest_instead_of_crashing(tmp_path: Path):
    catalog = tmp_path / "catalog"
    id6 = "042381"
    manifest_rel = f"manifests/{id6[:3]}/{id6}.json"
    entry = _base_entry(
        id6,
        {
            "type": "canonical_manifest",
            "manifest": manifest_rel,
            "membership_policy": "Exact service-neutral recording set.",
        },
    )
    _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", entry)
    manifest_path = catalog / manifest_rel
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    for content in ("{not-json", "[]"):
        manifest_path.write_text(content, encoding="utf-8")
        errors = validate_catalog(
            catalog,
            entry_schema_path=ENTRY_SCHEMA,
            manifest_schema_path=MANIFEST_SCHEMA,
        )
        assert any(
            f"definition.manifest: cannot load {manifest_rel}" in error
            for error in errors
        )


def test_catalog_rejects_unreferenced_canonical_manifests(tmp_path: Path):
    catalog = tmp_path / "catalog"
    id6 = "042381"
    entry = _base_entry(
        id6,
        {
            "type": "artist_catalog",
            "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555",
        },
    )
    _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", entry)
    _write_json(
        catalog / f"manifests/{id6[:3]}/{id6}.json",
        {
            "schema_version": 1,
            "disc_id": id6,
            "recordings": [{"isrcs": ["KRABC2600001"]}],
        },
    )
    orphan_id = "042382"
    _write_json(
        catalog / f"manifests/{orphan_id[:3]}/{orphan_id}.json",
        {
            "schema_version": 1,
            "disc_id": orphan_id,
            "recordings": [{"isrcs": ["KRABC2600002"]}],
        },
    )

    errors = validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
    )
    assert any("is not a canonical_manifest definition" in error for error in errors)
    assert any("no catalog entry exists for canonical manifest 042382" in error for error in errors)


def test_catalog_rejects_malformed_unreferenced_manifest(tmp_path: Path):
    catalog = tmp_path / "catalog"
    path = catalog / "manifests/042/042381.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")

    errors = validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
    )
    assert any("unreferenced canonical manifest cannot be loaded" in error for error in errors)


def test_catalog_rejects_misplaced_manifest_and_pack(tmp_path: Path):
    catalog = tmp_path / "catalog"
    id6 = "042381"
    entry = _base_entry(
        id6,
        {
            "type": "artist_catalog",
            "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555",
        },
    )
    _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", entry)
    _write_json(
        catalog / "manifests/wrong/place.json",
        {
            "schema_version": 1,
            "disc_id": "042382",
            "recordings": [{"isrcs": ["KRABC2600002"]}],
        },
    )
    _write_yaml(
        catalog / "packs/nested/test-pack.yaml",
        {
            "schema_version": 1,
            "slug": "test-pack",
            "title": "Test pack",
            "status": "draft",
            "capacity": 12,
            "discs": [id6],
            "provenance": {"authority": "community", "maintainers": ["tester"]},
            "tags": ["test"],
        },
    )

    errors = validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
        pack_schema_path=PACK_SCHEMA,
    )
    assert any("canonical manifest must live at manifests/042/042382.json" in error for error in errors)
    assert any("pack must live at packs/test-pack.yaml" in error for error in errors)


def test_manifest_rejects_ambiguous_duplicate_recording_identifiers():
    schema = load_schema(MANIFEST_SCHEMA)
    manifest = {
        "schema_version": 1,
        "disc_id": "042381",
        "recordings": [
            {"isrcs": ["KRABC2600001"]},
            {"isrcs": ["KRABC2600001"]},
        ],
    }
    errors = validate_manifest(manifest, schema)
    assert any("appears in more than one recording" in error for error in errors)


def test_catalog_rejects_wrong_path_and_missing_successor(tmp_path: Path):
    catalog = tmp_path / "catalog"
    entry = _base_entry(
        "042381",
        {"type": "artist_catalog", "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555"},
    )
    entry["successor"] = "042382"
    _write_yaml(catalog / "discs/999/wrong.yaml", entry)

    errors = validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
    )
    assert any("catalog entry must live at discs/042/042381.yaml" in error for error in errors)
    assert any("successor: referenced catalog ID 042382 does not exist" in error for error in errors)


def test_catalog_rejects_successor_cycles(tmp_path: Path):
    catalog = tmp_path / "catalog"
    ids = ["042381", "042382", "042383"]
    for id6, successor in zip(ids, ids[1:] + ids[:1]):
        entry = _base_entry(
            id6,
            {
                "type": "artist_catalog",
                "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555",
            },
        )
        entry["status"] = "retired"
        entry["successor"] = successor
        _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", entry)

    errors = validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
    )
    cycle_errors = [error for error in errors if "successor cycle detected" in error]
    assert len(cycle_errors) == 1
    assert "042381 -> 042382 -> 042383 -> 042381" in cycle_errors[0]


def test_provider_native_requires_matching_direct_binding(tmp_path: Path):
    catalog = tmp_path / "catalog"
    id6 = "042381"
    entry = _base_entry(
        id6,
        {"type": "provider_native", "provider": "spotify"},
        portability="provider_native",
    )
    entry["providers"] = {
        "spotify": {"strategy": "equivalent", "resource": "spotify:playlist:test"}
    }
    _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", entry)

    errors = validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
    )
    assert any("provider-native binding must use 'direct'" in error for error in errors)


def test_federated_collection_requires_multiple_equivalent_bindings(tmp_path: Path):
    catalog = tmp_path / "catalog"
    id6 = "042381"
    entry = _base_entry(
        id6,
        {"type": "federated_collection", "concept": "Provider editorial current-hits collection."},
        portability="federated",
    )
    entry["providers"] = {
        "spotify": {"strategy": "direct", "resource": "spotify:playlist:test"}
    }
    _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", entry)

    errors = validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
    )
    assert any("requires at least two provider bindings" in error for error in errors)
    assert any("must use 'equivalent' or 'best_available'" in error for error in errors)
