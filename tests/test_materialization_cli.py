import json
from pathlib import Path

from playlistdisc.cli import main

ROOT = Path(__file__).parents[1]
PLAN = ROOT / "tests/vectors/materialization-plan.json"


def test_materialization_cli_hit_and_scope_miss(tmp_path: Path, capsys):
    cache = tmp_path / "cache"
    assert (
        main(
            [
                "materialization-put",
                str(PLAN),
                "--cache",
                str(cache),
                "--scope",
                "account-a",
                "--resource",
                "demo:playlist:generated",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(
            [
                "materialization-check",
                str(PLAN),
                "--cache",
                str(cache),
                "--scope",
                "account-a",
                "--json",
            ]
        )
        == 0
    )
    hit = json.loads(capsys.readouterr().out)
    assert hit["status"] == "hit"
    assert hit["record"]["materialized_resource"] == "demo:playlist:generated"

    assert (
        main(
            [
                "materialization-check",
                str(PLAN),
                "--cache",
                str(cache),
                "--scope",
                "account-b",
                "--json",
            ]
        )
        == 3
    )
    miss = json.loads(capsys.readouterr().out)
    assert miss["status"] == "miss"
