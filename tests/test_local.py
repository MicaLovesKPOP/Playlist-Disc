import json
from pathlib import Path

import pytest
import yaml

from playlistdisc.cli import main
from playlistdisc.identity import PDIdentity
from playlistdisc.local import (
    allocate_private_identity,
    create_local_entry,
    find_local_entry,
    validate_local_entry,
    validate_local_library,
)


def test_create_allocates_lowest_free_private_ids(tmp_path: Path):
    library = tmp_path / "local"
    first, first_path, _ = create_local_entry(
        library,
        title="Morning drive",
        short_title="MORNING DRIVE",
        bindings={"spotify": "spotify:playlist:first"},
    )
    second, second_path, _ = create_local_entry(
        library,
        title="Evening drive",
        short_title="EVENING DRIVE",
        bindings={"apple_music": "library:playlist:second"},
    )

    assert first.id6 == "900000"
    assert second.id6 == "900001"
    assert first_path == library / "discs/900/900000.yaml"
    assert second_path == library / "discs/900/900001.yaml"
    assert validate_local_library(library) == []


def test_preferred_private_id_and_collision(tmp_path: Path):
    library = tmp_path / "local"
    ident, _, _ = create_local_entry(
        library,
        title="Pinned",
        short_title="PINNED",
        bindings={"local": "playlist:pinned"},
        preferred_id="901234",
    )
    assert ident == PDIdentity(901234)

    with pytest.raises(FileExistsError):
        allocate_private_identity(library, "901234")
    with pytest.raises(ValueError):
        allocate_private_identity(library, "999901")


def test_local_entry_requires_private_namespace():
    data = {
        "schema_version": 1,
        "id": "042381",
        "title": "Wrong namespace",
        "short_title": "WRONG",
        "bindings": {"local": {"resource": "playlist:test"}},
        "playback": {"order": "ordered", "start": "first", "repeat": "context"},
    }
    assert "id: local entry uses 'public' namespace" in validate_local_entry(data)


def test_library_rejects_wrong_shard_path(tmp_path: Path):
    library = tmp_path / "local"
    wrong = library / "discs/901/900000.yaml"
    wrong.parent.mkdir(parents=True)
    wrong.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "id": "900000",
                "title": "Wrong path",
                "short_title": "WRONG PATH",
                "bindings": {"local": {"resource": "playlist:test"}},
                "playback": {
                    "order": "ordered",
                    "start": "first",
                    "repeat": "context",
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    errors = validate_local_library(library)
    assert any("must live at discs/900/900000.yaml" in error for error in errors)


def test_find_local_entry_uses_deterministic_path(tmp_path: Path):
    library = tmp_path / "local"
    ident, path, data = create_local_entry(
        library,
        title="Find me",
        short_title="FIND ME",
        bindings={"local": "playlist:find-me"},
    )
    assert find_local_entry(library, ident) == (path, data)
    assert find_local_entry(library, PDIdentity(1)) is None


def test_cli_create_validate_list_and_virtual_build(tmp_path: Path, capsys):
    library = tmp_path / "local"
    assert (
        main(
            [
                "local-create",
                str(library),
                "--title",
                "Personal favourites",
                "--short-title",
                "FAVOURITES",
                "--binding",
                "spotify=spotify:playlist:test",
                "--binding",
                "local=library:playlist:favourites",
                "--tag",
                "personal",
            ]
        )
        == 0
    )
    created_output = capsys.readouterr().out
    assert "PD1-900000-" in created_output

    assert main(["local-validate", str(library)]) == 0
    assert "validated 1 local/private entries" in capsys.readouterr().out

    assert main(["local-list", str(library), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["id"] == "900000"
    assert set(listed[0]["bindings"]) == {"spotify", "local"}

    output = tmp_path / "bundle"
    assert (
        main(
            [
                "build",
                "900000",
                "--local-library",
                str(library),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    capsys.readouterr()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["namespace"] == "private"
    assert manifest["title"] == "Personal favourites"
    assert manifest["short_title"] == "FAVOURITES"


def test_cli_rejects_malformed_binding(tmp_path: Path, capsys):
    result = main(
        [
            "local-create",
            str(tmp_path / "local"),
            "--title",
            "Broken",
            "--short-title",
            "BROKEN",
            "--binding",
            "not-a-binding",
        ]
    )
    assert result == 2
    assert "PROVIDER=RESOURCE" in capsys.readouterr().err
