import copy
from pathlib import Path

from playlistdisc.bridge import (
    load_bridge_schema,
    read_bridge_jsonl,
    validate_bridge_message,
    validate_bridge_transcript,
)
from playlistdisc.cli import main

ROOT = Path(__file__).parents[1]
VECTOR = ROOT / "tests/vectors/bridge-session.jsonl"


def test_reference_bridge_transcript_validates():
    messages = read_bridge_jsonl(VECTOR)
    assert len(messages) == 10
    assert validate_bridge_transcript(messages) == []


def test_bridge_schema_is_packaged_and_rejects_wrong_source():
    schema = load_bridge_schema()
    message = read_bridge_jsonl(VECTOR)[0]
    bad = copy.deepcopy(message)
    bad["source"] = "host"
    errors = validate_bridge_message(bad, schema)
    assert any("adapter" in error for error in errors)


def test_bridge_rejects_invalid_pd_check_digit():
    message = read_bridge_jsonl(VECTOR)[3]
    bad = copy.deepcopy(message)
    bad["payload"]["machine_id"] = "PD1-999901-0"
    errors = validate_bridge_message(bad)
    assert any("check digit" in error for error in errors)


def test_bridge_rejects_non_increasing_sequence():
    messages = read_bridge_jsonl(VECTOR)
    bad = copy.deepcopy(messages)
    bad[9]["seq"] = 4
    errors = validate_bridge_transcript(bad)
    assert any("sequence must increase strictly" in error for error in errors)


def test_bridge_rejects_mismatched_removal_counter():
    messages = read_bridge_jsonl(VECTOR)
    bad = copy.deepcopy(messages)
    bad[-1]["payload"]["selection_counter"] = 2
    errors = validate_bridge_transcript(bad)
    assert any("does not match active selection" in error for error in errors)


def test_bridge_cli_validates_reference_vector(capsys):
    assert main(["bridge-validate", str(VECTOR)]) == 0
    output = capsys.readouterr().out
    assert "validated 10 bridge messages" in output
