from pathlib import Path

import yaml

from playlistdisc.catalog import validate_catalog

ROOT = Path(__file__).parents[1]
ENTRY_SCHEMA = ROOT / "catalog/schema/disc.schema.json"
MANIFEST_SCHEMA = ROOT / "catalog/schema/canonical-manifest.schema.json"
PACK_SCHEMA = ROOT / "catalog/schema/pack.schema.json"


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _base_entry(id6: str, *, status: str = "draft", definition: dict | None = None) -> dict:
    return {
        "schema_version": 1,
        "id": id6,
        "title": f"Entry {id6}",
        "short_title": f"ENTRY {id6}",
        "status": status,
        "definition": definition
        or {
            "type": "artist_catalog",
            "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555",
        },
        "provenance": {"authority": "community", "maintainers": ["tester"]},
        "lifecycle": "snapshot",
        "portability": "canonical",
        "playback": {"order": "ordered", "start": "first", "repeat": "off"},
        "tags": ["test"],
    }


def _validate(catalog: Path) -> list[str]:
    return validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
        pack_schema_path=PACK_SCHEMA,
    )


def test_permanent_public_activation_is_closed_while_format_is_draft(tmp_path: Path):
    catalog = tmp_path / "catalog"
    entry = _base_entry("042381", status="active")
    _write_yaml(catalog / "discs/042/042381.yaml", entry)

    errors = _validate(catalog)
    assert any("permanent public catalog activation is closed" in error for error in errors)


def test_successor_is_only_valid_on_retired_entries(tmp_path: Path):
    catalog = tmp_path / "catalog"
    first = _base_entry("999901", status="draft")
    first["successor"] = "999902"
    second = _base_entry("999902", status="draft")
    _write_yaml(catalog / "discs/999/999901.yaml", first)
    _write_yaml(catalog / "discs/999/999902.yaml", second)

    errors = _validate(catalog)
    assert any("only retired entries may declare a successor" in error for error in errors)


def test_provider_native_requires_concrete_native_resource(tmp_path: Path):
    catalog = tmp_path / "catalog"
    entry = _base_entry(
        "999901",
        definition={"type": "provider_native", "provider": "spotify"},
    )
    entry["portability"] = "provider_native"
    entry["providers"] = {"spotify": {"strategy": "direct"}}
    _write_yaml(catalog / "discs/999/999901.yaml", entry)

    errors = _validate(catalog)
    assert any("provider-native binding requires a resource" in error for error in errors)


def test_federated_bindings_require_concrete_resources(tmp_path: Path):
    catalog = tmp_path / "catalog"
    entry = _base_entry(
        "999901",
        definition={
            "type": "federated_collection",
            "concept": "Provider editorial current-hits collection.",
        },
    )
    entry["portability"] = "federated"
    entry["providers"] = {
        "spotify": {"strategy": "equivalent"},
        "apple_music": {"strategy": "best_available", "resource": "apple:playlist:one"},
    }
    _write_yaml(catalog / "discs/999/999901.yaml", entry)

    errors = _validate(catalog)
    assert any("federated binding requires a resource" in error for error in errors)
