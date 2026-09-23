import json
from pathlib import Path
import shutil

import yaml

from playlistdisc.cli import main

ROOT = Path(__file__).parents[1]


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_resolve_canonical_cli_writes_plan(tmp_path: Path, capsys):
    catalog = tmp_path / "catalog"
    shutil.copytree(ROOT / "catalog/schema", catalog / "schema")

    id6 = "042381"
    manifest_rel = "manifests/042/042381.json"
    entry = {
        "schema_version": 1,
        "id": id6,
        "title": "Resolution CLI fixture",
        "short_title": "RESOLVE",
        "status": "draft",
        "definition": {
            "type": "canonical_manifest",
            "manifest": manifest_rel,
            "membership_policy": "Exact fixture recording.",
        },
        "provenance": {"authority": "project", "maintainers": []},
        "lifecycle": "snapshot",
        "portability": "canonical",
        "playback": {"order": "ordered", "start": "first", "repeat": "off"},
        "tags": ["test"],
    }
    _write_yaml(catalog / "discs/042/042381.yaml", entry)
    manifest_path = catalog / manifest_rel
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "disc_id": id6,
                "recordings": [
                    {
                        "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                        "title_hint": "Fixture Track",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    provider_index = tmp_path / "provider.json"
    provider_index.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "demo",
                "tracks": [
                    {
                        "resource": "demo:track:1",
                        "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "plan.json"
    assert main(
        [
            "resolve-canonical",
            id6,
            "--catalog",
            str(catalog),
            "--provider-index",
            str(provider_index),
            "--output",
            str(output),
            "--require-complete",
        ]
    ) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["resolved_count"] == 1
    assert payload["coverage"] == 1.0
    assert payload["items"][0]["resource"] == "demo:track:1"
    assert str(output) in capsys.readouterr().out


def test_validate_provider_index_cli(tmp_path: Path, capsys):
    path = tmp_path / "provider.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "local",
                "tracks": [
                    {
                        "resource": "file:///music/example.flac",
                        "isrcs": ["KRABC2600001"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert main(["validate-provider-index", str(path)]) == 0
    assert "provider index: PASS" in capsys.readouterr().out
