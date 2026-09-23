from pathlib import Path

from playlistdisc.catalog import iter_entries, load_schema, load_yaml, validate_entry

ROOT = Path(__file__).parents[1]


def test_draft_catalog_validates():
    schema = load_schema(ROOT / "catalog/schema/disc.schema.json")
    paths = list(iter_entries(ROOT / "catalog"))
    assert paths
    for path in paths:
        assert validate_entry(load_yaml(path), schema) == []
