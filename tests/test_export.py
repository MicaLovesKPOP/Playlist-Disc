import json
from pathlib import Path

import yaml

from playlistdisc.cli import main

ROOT = Path(__file__).parents[1]


def test_export_catalog(tmp_path: Path):
    output = tmp_path / "catalog.json"
    assert main(["export-catalog", str(ROOT / "catalog"), "--output", str(output)]) == 0
    data = json.loads(output.read_text())
    assert data["format"] == "PDv1"
    assert len(data["entries"]) == 3
    assert data["entries"][0]["machine_id"].startswith("PD1-")


def test_export_refuses_invalid_catalog(tmp_path: Path):
    catalog = tmp_path / "catalog"
    (catalog / "schema").mkdir(parents=True)
    (catalog / "schema/disc.schema.json").write_text(
        (ROOT / "catalog/schema/disc.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (catalog / "schema/canonical-manifest.schema.json").write_text(
        (ROOT / "catalog/schema/canonical-manifest.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    path = catalog / "discs/042/042381.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "id": "042381",
                "title": "Broken provider entry",
                "short_title": "BROKEN",
                "status": "draft",
                "definition": {"type": "provider_native", "provider": "spotify"},
                "provenance": {"authority": "community"},
                "lifecycle": "snapshot",
                "portability": "provider_native",
                "playback": {"order": "ordered", "start": "first", "repeat": "off"},
                "tags": ["test"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "catalog.json"
    assert main(["export-catalog", str(catalog), "--output", str(output)]) == 1
    assert not output.exists()
