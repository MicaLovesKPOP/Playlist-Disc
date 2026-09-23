from pathlib import Path

import yaml

from playlistdisc.catalog import load_schema, validate_catalog, validate_pack

ROOT = Path(__file__).parents[1]
ENTRY_SCHEMA = ROOT / "catalog/schema/disc.schema.json"
MANIFEST_SCHEMA = ROOT / "catalog/schema/canonical-manifest.schema.json"
PACK_SCHEMA = ROOT / "catalog/schema/pack.schema.json"


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _entry(id6: str) -> dict:
    return {
        "schema_version": 1,
        "id": id6,
        "title": f"Entry {id6}",
        "short_title": f"ENTRY {id6}",
        "status": "draft",
        "definition": {
            "type": "artist_catalog",
            "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555",
        },
        "provenance": {"authority": "community", "maintainers": ["tester"]},
        "lifecycle": "snapshot",
        "portability": "canonical",
        "playback": {"order": "ordered", "start": "first", "repeat": "off"},
        "tags": ["test"],
    }


def _pack(discs: list[str]) -> dict:
    return {
        "schema_version": 1,
        "slug": "starter-wallet",
        "title": "Starter wallet",
        "status": "draft",
        "capacity": 12,
        "discs": discs,
        "provenance": {"authority": "community", "maintainers": ["tester"]},
        "tags": ["starter"],
    }


def _validate(catalog: Path) -> list[str]:
    return validate_catalog(
        catalog,
        entry_schema_path=ENTRY_SCHEMA,
        manifest_schema_path=MANIFEST_SCHEMA,
        pack_schema_path=PACK_SCHEMA,
    )


def test_pack_schema_accepts_ordered_wallet_source():
    schema = load_schema(PACK_SCHEMA)
    assert validate_pack(_pack(["042381", "042382"]), schema) == []


def test_catalog_validates_pack_references_and_capacity(tmp_path: Path):
    catalog = tmp_path / "catalog"
    for id6 in ("042381", "042382"):
        _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", _entry(id6))
    _write_yaml(catalog / "packs/starter-wallet.yaml", _pack(["042382", "042381"]))

    assert _validate(catalog) == []


def test_pack_rejects_missing_reference_and_wrong_path(tmp_path: Path):
    catalog = tmp_path / "catalog"
    _write_yaml(catalog / "discs/042/042381.yaml", _entry("042381"))
    _write_yaml(
        catalog / "packs/wrong-name.yaml",
        _pack(["042381", "042399"]),
    )

    errors = _validate(catalog)
    assert any("pack must live at packs/starter-wallet.yaml" in error for error in errors)
    assert any("referenced catalog ID 042399 does not exist" in error for error in errors)


def test_pack_rejects_more_discs_than_declared_capacity(tmp_path: Path):
    catalog = tmp_path / "catalog"
    ids = [f"{number:06d}" for number in range(42381, 42394)]
    for id6 in ids:
        _write_yaml(catalog / f"discs/{id6[:3]}/{id6}.yaml", _entry(id6))
    _write_yaml(catalog / "packs/starter-wallet.yaml", _pack(ids))

    errors = _validate(catalog)
    assert any("pack has 13 discs but capacity is 12" in error for error in errors)


def test_pack_schema_rejects_duplicate_disc_slots():
    schema = load_schema(PACK_SCHEMA)
    errors = validate_pack(_pack(["042381", "042381"]), schema)
    assert any("non-unique elements" in error for error in errors)
