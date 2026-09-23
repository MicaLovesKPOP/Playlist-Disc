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


def test_selection_counter_cannot_be_reused_after_removal():
    messages = read_bridge_jsonl(VECTOR)
    messages.append(
        {
            "protocol": "pdbridge",
            "version": 1,
            "source": "adapter",
            "session": "adapter-boot-001",
            "seq": 6,
            "type": "disc_selected",
            "payload": {
                "machine_id": "PD1-999902-5",
                "selection_counter": 1,
                "evidence": "toc",
                "confidence": "strong",
            },
        }
    )
    errors = validate_bridge_transcript(messages)
    assert any("selection counter must increase" in error for error in errors)


def test_state_sync_cannot_regress_selection_counter():
    messages = read_bridge_jsonl(VECTOR)
    messages.append(
        {
            "protocol": "pdbridge",
            "version": 1,
            "source": "adapter",
            "session": "adapter-boot-001",
            "seq": 6,
            "type": "state_sync",
            "payload": {
                "power": "accessory",
                "disc": {
                    "machine_id": "PD1-999901-7",
                    "selection_counter": 0,
                    "evidence": "toc",
                },
                "streaming_source_active": False,
            },
        }
    )
    errors = validate_bridge_transcript(messages)
    assert any("state sync regressed" in error for error in errors)


def test_adapter_must_not_emit_unadvertised_detection_evidence():
    messages = read_bridge_jsonl(VECTOR)
    bad = copy.deepcopy(messages)
    bad[0]["payload"]["capabilities"]["disc_detection"] = ["toc"]
    bad[3]["payload"]["evidence"] = "audio_beacon"
    errors = validate_bridge_transcript(bad)
    assert any("was not advertised by adapter" in error for error in errors)


def test_adapter_must_not_emit_unadvertised_media_control():
    messages = read_bridge_jsonl(VECTOR)
    bad = copy.deepcopy(messages)
    bad[0]["payload"]["capabilities"]["media_controls"] = ["previous"]
    errors = validate_bridge_transcript(bad)
    assert any("payload.action" in error and "not advertised" in error for error in errors)


def test_source_request_respects_both_host_and_adapter_capabilities():
    messages = read_bridge_jsonl(VECTOR)

    bad_adapter = copy.deepcopy(messages)
    bad_adapter[0]["payload"]["capabilities"]["auto_source_switch"] = False
    errors = validate_bridge_transcript(bad_adapter)
    assert any("auto_source_switch=false" in error for error in errors)

    bad_host = copy.deepcopy(messages)
    bad_host[1]["payload"]["capabilities"]["source_request"] = False
    errors = validate_bridge_transcript(bad_host)
    assert any("source_request=false" in error for error in errors)


def test_now_playing_respects_host_capability():
    messages = read_bridge_jsonl(VECTOR)
    bad = copy.deepcopy(messages)
    bad[1]["payload"]["capabilities"]["now_playing"] = False
    errors = validate_bridge_transcript(bad)
    assert any("now_playing=false" in error for error in errors)


def test_display_capability_must_be_self_consistent():
    messages = read_bridge_jsonl(VECTOR)
    bad = copy.deepcopy(messages)
    bad[0]["payload"]["capabilities"]["metadata_display"]["supported"] = False
    errors = validate_bridge_transcript(bad)
    assert any("unsupported display must advertise no fields" in error for error in errors)


def test_reannounced_capabilities_cannot_change_inside_one_session():
    messages = read_bridge_jsonl(VECTOR)
    hello = copy.deepcopy(messages[0])
    hello["seq"] = 6
    hello["payload"]["capabilities"]["media_controls"] = ["next"]
    messages.append(hello)
    errors = validate_bridge_transcript(messages)
    assert any("adapter hello changed within session" in error for error in errors)


def test_ack_is_bound_to_peer_session_and_seen_sequence():
    messages = read_bridge_jsonl(VECTOR)
    messages.append(
        {
            "protocol": "pdbridge",
            "version": 1,
            "source": "host",
            "session": "host-001",
            "seq": 4,
            "type": "ack",
            "payload": {
                "ack_session": "adapter-boot-001",
                "ack_seq": 5,
            },
        }
    )
    assert validate_bridge_transcript(messages) == []

    bad = copy.deepcopy(messages)
    bad[-1]["payload"]["ack_seq"] = 99
    errors = validate_bridge_transcript(bad)
    assert any("acknowledgement target" in error for error in errors)


def test_ack_requires_target_session():
    message = {
        "protocol": "pdbridge",
        "version": 1,
        "source": "host",
        "session": "host-001",
        "seq": 4,
        "type": "ack",
        "payload": {"ack_seq": 5},
    }
    errors = validate_bridge_message(message)
    assert any("ack_session" in error for error in errors)


def test_error_related_sequence_and_session_are_a_pair():
    message = {
        "protocol": "pdbridge",
        "version": 1,
        "source": "host",
        "session": "host-001",
        "seq": 4,
        "type": "error",
        "payload": {
            "code": "request_failed",
            "message": "Example",
            "related_seq": 5,
        },
    }
    errors = validate_bridge_message(message)
    assert any("related_session" in error for error in errors)


def test_bridge_cli_validates_reference_vector(capsys):
    assert main(["bridge-validate", str(VECTOR)]) == 0
    output = capsys.readouterr().out
    assert "validated 10 bridge messages" in output
