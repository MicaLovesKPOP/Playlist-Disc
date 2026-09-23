import json
from pathlib import Path

from playlistdisc.cli import main

ROOT = Path(__file__).parents[1]


def test_host_replay_cli_emits_expected_actions(capsys):
    assert (
        main(
            [
                "host-replay",
                str(ROOT / "tests/vectors/host-adapter-session.jsonl"),
                "--plan",
                str(ROOT / "tests/vectors/host-playback-plan.json"),
            ]
        )
        == 0
    )
    lines = [
        json.loads(line)
        for line in capsys.readouterr().out.splitlines()
        if line.strip()
    ]
    assert [item["type"] for item in lines] == [
        "source_request",
        "execute_plan",
        "provider_control",
        "stop_playback",
        "source_request",
    ]
    assert lines[0]["action"] == "activate_streaming"
    assert lines[-1]["action"] == "deactivate_streaming"


def test_host_replay_without_plan_blocks_selection(capsys):
    assert (
        main(
            [
                "host-replay",
                str(ROOT / "tests/vectors/host-adapter-session.jsonl"),
            ]
        )
        == 0
    )
    lines = [
        json.loads(line)
        for line in capsys.readouterr().out.splitlines()
        if line.strip()
    ]
    assert [item["type"] for item in lines] == ["selection_blocked"]
    assert lines[0]["status"] == "unavailable"
