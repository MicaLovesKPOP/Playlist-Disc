import json
from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.local import create_local_entry


def test_plan_playback_cli_handles_existing_diagnostic_catalog(capsys):
    assert main(["plan-playback", "999901", "--provider", "demo"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "unplayable"
    assert payload["mode"] == "none"


def test_plan_playback_cli_handles_private_binding(tmp_path: Path, capsys):
    library = tmp_path / "local"
    create_local_entry(
        library,
        title="Private favourites",
        short_title="FAVOURITES",
        bindings={"local": "library:playlist:favourites"},
        preferred_id="900000",
    )
    assert (
        main(
            [
                "plan-playback",
                "900000",
                "--provider",
                "local",
                "--local-library",
                str(library),
                "--require-ready",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready"
    assert payload["resource"] == "library:playlist:favourites"


def test_plan_playback_require_ready_has_distinct_exit_code(capsys):
    assert (
        main(
            [
                "plan-playback",
                "999901",
                "--provider",
                "demo",
                "--require-ready",
            ]
        )
        == 3
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "unplayable"
