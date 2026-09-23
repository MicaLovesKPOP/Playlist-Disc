import json
from pathlib import Path

from playlistdisc.cli import main

ROOT = Path(__file__).parents[1]


def test_export_catalog(tmp_path: Path):
    output = tmp_path / "catalog.json"
    assert main(["export-catalog", str(ROOT / "catalog"), "--output", str(output)]) == 0
    data = json.loads(output.read_text())
    assert data["format"] == "PDv1"
    assert len(data["entries"]) == 3
    assert data["entries"][0]["machine_id"].startswith("PD1-")
