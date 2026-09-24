from pathlib import Path

from playlistdisc.host import HostRuntime, validate_host_action
from playlistdisc.identity import PDIdentity
from playlistdisc.materialization import (
    read_materialization,
    validate_materialization_record,
    write_materialization,
)
from playlistdisc.playback import compile_catalog_playback, validate_playback_plan
from playlistdisc.recognition import recognize_observations, validate_recognition_result


def test_offline_disc_to_materialized_playback_vertical(tmp_path: Path):
    identity = PDIdentity(42381)
    recognition = recognize_observations(track_durations=identity.track_durations)
    assert recognition.status == "recognized"
    assert recognition.identity == identity
    assert validate_recognition_result(recognition.to_dict()) == []

    entry = {
        "id": identity.id6,
        "title": "Vertical integration fixture",
        "definition": {
            "type": "canonical_manifest",
            "manifest": f"manifests/{identity.id6[:3]}/{identity.id6}.json",
            "membership_policy": "Exact set.",
        },
        "playback": {
            "order": "ordered",
            "start": "first",
            "repeat": "context",
        },
    }
    manifest = {
        "schema_version": 1,
        "disc_id": identity.id6,
        "recordings": [
            {
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                "isrcs": ["KRABC2600001"],
            }
        ],
    }
    provider_index = {
        "schema_version": 1,
        "provider": "demo",
        "market": "NL",
        "tracks": [
            {
                "resource": "demo:track:vertical",
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                "isrcs": ["KRABC2600001"],
                "preferred": True,
            }
        ],
    }
    plan = compile_catalog_playback(
        entry,
        "demo",
        manifest=manifest,
        provider_index=provider_index,
    ).to_dict()
    assert plan["status"] == "ready"
    assert plan["mode"] == "track_list"
    assert plan["resources"] == ["demo:track:vertical"]
    assert validate_playback_plan(plan) == []

    planner_calls = []

    def planner(machine_id: str):
        planner_calls.append(machine_id)
        assert machine_id == recognition.identity.machine_id
        return plan

    runtime = HostRuntime(planner)
    hello = {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "vertical-adapter-1",
        "seq": 0,
        "type": "hello",
        "payload": {
            "adapter_id": "offline-vertical-fixture",
            "implementation": "pytest",
            "capabilities": {
                "disc_detection": ["toc"],
                "media_controls": ["next", "previous", "play_pause"],
                "auto_source_switch": True,
                "metadata_display": {
                    "supported": False,
                    "fields": [],
                    "targets": [],
                },
            },
        },
    }
    state = {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "vertical-adapter-1",
        "seq": 1,
        "type": "state_sync",
        "payload": {
            "power": "accessory",
            "disc": None,
            "streaming_source_active": False,
        },
    }
    selected = {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "vertical-adapter-1",
        "seq": 2,
        "type": "disc_selected",
        "payload": {
            "machine_id": recognition.identity.machine_id,
            "selection_counter": 1,
            "evidence": "toc",
            "confidence": "strong",
        },
    }

    assert runtime.consume(hello) == ()
    assert runtime.consume(state) == ()
    actions = runtime.consume(selected)
    assert planner_calls == [identity.machine_id]
    assert [action.type for action in actions] == ["source_request", "execute_plan"]
    assert actions[0].action == "activate_streaming"
    assert actions[1].plan == plan
    assert all(validate_host_action(action.to_dict()) == [] for action in actions)

    cache_path = write_materialization(
        tmp_path / "cache",
        actions[1].plan,
        scope="vertical-account",
        materialized_resource="demo:playlist:vertical",
        provider_revision="offline-fixture-v1",
    )
    assert cache_path.is_file()
    record, reasons = read_materialization(
        tmp_path / "cache",
        actions[1].plan,
        scope="vertical-account",
    )
    assert reasons == []
    assert record is not None
    assert record["materialized_resource"] == "demo:playlist:vertical"
    assert record["source_count"] == 1
    assert validate_materialization_record(record) == []
