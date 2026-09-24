import json

from playlistdisc.cli import main
from playlistdisc.identity import PDIdentity


def test_recognize_cli_reports_checked_identity(capsys):
    identity = PDIdentity(999901)
    args = [
        "recognize",
        "--toc",
        *[str(value) for value in identity.track_durations],
        "--cdtext",
        identity.machine_id,
        "--require-recognized",
    ]
    assert main(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "recognized"
    assert payload["machine_id"] == identity.machine_id
    assert {item["channel"] for item in payload["evidence"]} == {"toc", "cdtext"}


def test_recognize_cli_conflict_has_no_identity_and_distinct_exit(capsys):
    first = PDIdentity(999901)
    second = PDIdentity(999902)
    args = [
        "recognize",
        "--toc",
        *[str(value) for value in first.track_durations],
        "--cdtext",
        second.machine_id,
        "--require-recognized",
    ]
    assert main(args) == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "conflict"
    assert "machine_id" not in payload


def test_recognize_cli_requires_observation(capsys):
    assert main(["recognize"]) == 2
    assert "provide at least one" in capsys.readouterr().err
