import copy

from playlistdisc.host import HostRuntime, validate_host_action
from playlistdisc.identity import PDIdentity


MACHINE_ID = PDIdentity(900000).machine_id


def _plan(*, status: str = "ready") -> dict:
    data = {
        "schema_version": 1,
        "format": "PDv1-playback-plan",
        "disc_id": "900000",
        "machine_id": MACHINE_ID,
        "title": "Private drive mix",
        "provider": "local",
        "status": status,
        "mode": "direct_resource" if status == "ready" else "none",
        "playback": {"order": "shuffle", "start": "random", "repeat": "context"},
    }
    if status == "ready":
        data["resource"] = "library:playlist:drive"
    else:
        data["reason"] = f"fixture status {status}"
    return data


def _hello(auto_source_switch: bool = True) -> dict:
    return {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "car-1",
        "seq": 0,
        "type": "hello",
        "payload": {
            "adapter_id": "fixture-adapter",
            "implementation": "host-runtime-test",
            "capabilities": {
                "disc_detection": ["toc"],
                "media_controls": ["next", "previous", "play_pause"],
                "auto_source_switch": auto_source_switch,
                "metadata_display": {
                    "supported": False,
                    "fields": [],
                    "targets": [],
                },
            },
        },
    }


def _state_sync(disc=None, source=False, seq=1) -> dict:
    return {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "car-1",
        "seq": seq,
        "type": "state_sync",
        "payload": {
            "power": "accessory",
            "disc": disc,
            "streaming_source_active": source,
        },
    }


def _selected(counter=1, seq=2) -> dict:
    return {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "car-1",
        "seq": seq,
        "type": "disc_selected",
        "payload": {
            "machine_id": MACHINE_ID,
            "selection_counter": counter,
            "evidence": "toc",
            "confidence": "strong",
        },
    }


def _source(active=True, seq=3) -> dict:
    return {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "car-1",
        "seq": seq,
        "type": "source_state",
        "payload": {"active": active},
    }


def _control(action="next", seq=4) -> dict:
    return {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "car-1",
        "seq": seq,
        "type": "media_control",
        "payload": {"action": action},
    }


def _removed(counter=1, seq=5) -> dict:
    return {
        "protocol": "pdbridge",
        "version": 1,
        "source": "adapter",
        "session": "car-1",
        "seq": seq,
        "type": "disc_removed",
        "payload": {"selection_counter": counter},
    }


def test_selection_executes_plan_and_requests_source_once():
    runtime = HostRuntime(lambda machine_id: _plan())
    assert runtime.consume(_hello()) == ()
    assert runtime.consume(_state_sync()) == ()

    actions = runtime.consume(_selected())
    assert [action.type for action in actions] == ["source_request", "execute_plan"]
    assert actions[0].action == "activate_streaming"
    assert actions[1].plan["machine_id"] == MACHINE_ID
    assert all(validate_host_action(action.to_dict()) == [] for action in actions)

    duplicate_sync = _state_sync(
        {
            "machine_id": MACHINE_ID,
            "selection_counter": 1,
            "evidence": "toc",
        },
        source=True,
        seq=6,
    )
    assert runtime.consume(duplicate_sync) == ()


def test_media_control_and_removal_are_normalized():
    runtime = HostRuntime(lambda machine_id: _plan())
    runtime.consume(_hello())
    runtime.consume(_state_sync())
    runtime.consume(_selected())
    runtime.consume(_source(True))

    control = runtime.consume(_control())
    assert len(control) == 1
    assert control[0].type == "provider_control"
    assert control[0].action == "next"

    removed = runtime.consume(_removed())
    assert [action.type for action in removed] == [
        "stop_playback",
        "source_request",
    ]
    assert removed[1].action == "deactivate_streaming"


def test_already_active_source_is_not_claimed_or_deactivated():
    runtime = HostRuntime(lambda machine_id: _plan())
    runtime.consume(_hello())
    runtime.consume(_state_sync(source=True))
    actions = runtime.consume(_selected())
    assert [action.type for action in actions] == ["execute_plan"]
    removed = runtime.consume(_removed())
    assert [action.type for action in removed] == ["stop_playback"]


def test_no_auto_source_request_when_adapter_does_not_support_it():
    runtime = HostRuntime(lambda machine_id: _plan())
    runtime.consume(_hello(auto_source_switch=False))
    runtime.consume(_state_sync())
    actions = runtime.consume(_selected())
    assert [action.type for action in actions] == ["execute_plan"]


def test_requires_lookup_is_executable_but_partial_is_policy_gated():
    lookup = _plan(status="requires_lookup")
    lookup["mode"] = "entity_lookup"
    lookup["lookup"] = {
        "type": "artist",
        "musicbrainz_id": "11111111-2222-3333-4444-555555555555",
    }
    lookup.pop("reason")

    runtime = HostRuntime(lambda machine_id: lookup)
    runtime.consume(_hello(False))
    assert runtime.consume(_selected())[0].type == "execute_plan"

    partial = _plan(status="partial")
    partial["mode"] = "track_list"
    partial["resources"] = ["local:a"]
    partial.pop("reason")

    blocked = HostRuntime(lambda machine_id: partial)
    blocked.consume(_hello(False))
    actions = blocked.consume(_selected())
    assert actions[0].type == "selection_blocked"
    assert actions[0].status == "partial"

    allowed = HostRuntime(lambda machine_id: partial, allow_partial=True)
    allowed.consume(_hello(False))
    assert allowed.consume(_selected())[0].type == "execute_plan"


def test_missing_plan_blocks_selection_without_guessing():
    def missing(machine_id: str):
        raise KeyError(machine_id)

    runtime = HostRuntime(missing)
    runtime.consume(_hello(False))
    actions = runtime.consume(_selected())
    assert actions[0].type == "selection_blocked"
    assert actions[0].status == "unavailable"


def test_new_adapter_session_is_a_new_selection_even_for_same_disc():
    runtime = HostRuntime(lambda machine_id: _plan())
    runtime.consume(_hello(False))
    assert runtime.consume(_selected())[0].type == "execute_plan"

    hello2 = copy.deepcopy(_hello(False))
    hello2["session"] = "car-2"
    runtime.consume(hello2)
    selected2 = copy.deepcopy(_selected())
    selected2["session"] = "car-2"
    selected2["seq"] = 1
    assert runtime.consume(selected2)[0].type == "execute_plan"


def test_removal_policy_can_leave_playing_and_keep_source():
    runtime = HostRuntime(
        lambda machine_id: _plan(),
        stop_on_remove=False,
        deactivate_source_on_remove=False,
    )
    runtime.consume(_hello())
    runtime.consume(_state_sync())
    runtime.consume(_selected())
    runtime.consume(_source(True))
    assert runtime.consume(_removed()) == ()
    assert runtime.consume(_control(seq=6))[0].type == "provider_control"

def _host_action(action_type: str, **fields) -> dict:
    data = {
        "schema_version": 1,
        "format": "PDv1-host-action",
        "type": action_type,
        "context": {
            "machine_id": MACHINE_ID,
            "adapter_session": "car-1",
            "selection_counter": 1,
        },
    }
    data.update(fields)
    return data


def test_host_action_contract_rejects_cross_type_payloads():
    plan = _plan()

    assert validate_host_action(
        _host_action(
            "source_request",
            action="activate_streaming",
            plan=plan,
        )
    )
    assert validate_host_action(
        _host_action(
            "execute_plan",
            plan=plan,
            action="next",
        )
    )
    assert validate_host_action(
        _host_action(
            "provider_control",
            action="next",
            reason="contradictory extra payload",
        )
    )
    assert validate_host_action(
        _host_action(
            "stop_playback",
            reason="disc removed",
            status="unavailable",
        )
    )
    assert validate_host_action(
        _host_action(
            "selection_blocked",
            status="unavailable",
            reason="no provider mapping",
            action="play_pause",
        )
    )


def test_host_action_contract_rejects_wrong_action_and_blocked_status_domains():
    assert validate_host_action(
        _host_action("source_request", action="next")
    )
    assert validate_host_action(
        _host_action("provider_control", action="activate_streaming")
    )
    assert validate_host_action(
        _host_action(
            "selection_blocked",
            status="ready",
            reason="ready plans must execute rather than be blocked",
        )
    )
    assert validate_host_action(
        _host_action(
            "selection_blocked",
            status="requires_lookup",
            reason="lookup plans are executable by the provider layer",
        )
    )


def test_host_action_contract_accepts_each_runtime_shape():
    plan = _plan()
    valid = [
        _host_action("source_request", action="activate_streaming"),
        _host_action("source_request", action="deactivate_streaming"),
        _host_action("execute_plan", plan=plan),
        _host_action("provider_control", action="previous"),
        _host_action("stop_playback", reason="disc removed"),
        _host_action(
            "selection_blocked",
            status="partial",
            reason="partial playback disabled",
        ),
        _host_action(
            "selection_blocked",
            status="ambiguous",
            reason="provider resolution ambiguous",
        ),
        _host_action(
            "selection_blocked",
            status="unavailable",
            reason="provider resource unavailable",
        ),
        _host_action(
            "selection_blocked",
            status="unplayable",
            reason="diagnostic disc",
        ),
    ]
    assert all(validate_host_action(item) == [] for item in valid)

