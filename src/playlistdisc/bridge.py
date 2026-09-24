"""Transport-neutral logical messages for the PD Bridge Draft 0.1."""

from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .identity import PDIdentity


def load_bridge_schema() -> dict[str, Any]:
    resource = files("playlistdisc").joinpath("schemas/bridge-message.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def _schema_errors(
    message: dict[str, Any], schema: dict[str, Any]
) -> list[str]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(message),
        key=lambda error: [str(part) for part in error.path],
    )
    result: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        result.append(f"{location}: {error.message}")
    return result


def _machine_ids(message: dict[str, Any]) -> Iterable[tuple[str, str]]:
    payload = message.get("payload")
    if not isinstance(payload, dict):
        return

    msg_type = message.get("type")
    if msg_type == "disc_selected" and isinstance(payload.get("machine_id"), str):
        yield "payload.machine_id", payload["machine_id"]
    elif msg_type == "state_sync":
        disc = payload.get("disc")
        if isinstance(disc, dict) and isinstance(disc.get("machine_id"), str):
            yield "payload.disc.machine_id", disc["machine_id"]
    elif msg_type == "playback_state" and isinstance(payload.get("context_id"), str):
        yield "payload.context_id", payload["context_id"]


def validate_bridge_message(
    message: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> list[str]:
    """Validate one logical bridge message, including PD check digits."""
    schema = schema or load_bridge_schema()
    errors = _schema_errors(message, schema)
    if errors:
        return errors

    for location, machine_id in _machine_ids(message):
        try:
            PDIdentity.parse(machine_id)
        except ValueError as exc:
            errors.append(f"{location}: {exc}")

    if message["type"] == "hello":
        display = message["payload"]["capabilities"]["metadata_display"]
        if display["supported"] and not display["fields"]:
            errors.append(
                "payload.capabilities.metadata_display.fields: "
                "supported display must advertise at least one field"
            )
        if not display["supported"] and display["fields"]:
            errors.append(
                "payload.capabilities.metadata_display.fields: "
                "unsupported display must advertise no fields"
            )
    return errors


def read_bridge_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load non-empty, non-comment JSON lines from a bridge transcript."""
    messages: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"line {line_number}: bridge message must be a JSON object"
                )
            messages.append(value)
    return messages


def _payload_fingerprint(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _peer(source: str) -> str:
    return "host" if source == "adapter" else "adapter"


def validate_bridge_transcript(
    messages: Iterable[dict[str, Any]],
    schema: dict[str, Any] | None = None,
) -> list[str]:
    """Validate sequence, selection, capability, and reply invariants.

    Transcript validation remains useful for partial captures: capability checks are
    applied only after the corresponding hello or hello_ack has been observed.
    """
    schema = schema or load_bridge_schema()
    errors: list[str] = []

    last_seq: dict[tuple[str, str], int] = {}
    seen_seq: set[tuple[str, str, int]] = set()

    active_selection: dict[str, tuple[int, str] | None] = {}
    last_selection_counter: dict[str, int] = {}

    adapter_hello: dict[str, str] = {}
    adapter_capabilities: dict[str, dict[str, Any]] = {}
    latest_adapter_session: str | None = None

    host_hello: dict[str, str] = {}
    host_capabilities: dict[str, dict[str, Any]] = {}

    for index, message in enumerate(messages, start=1):
        message_errors = validate_bridge_message(message, schema)
        errors.extend(f"message {index}:{error}" for error in message_errors)
        if message_errors:
            continue

        source = message["source"]
        session = message["session"]
        seq = message["seq"]
        msg_type = message["type"]
        payload = message["payload"]

        key = (source, session)
        message_error_start = len(errors)
        previous_seq = last_seq.get(key)
        sequence_valid = True
        if previous_seq is not None and seq <= previous_seq:
            errors.append(
                f"message {index}:seq: {source}/{session} sequence must increase "
                f"strictly ({seq} <= {previous_seq})"
            )
            sequence_valid = False
        seen_seq.add((source, session, seq))

        if msg_type == "hello":
            first_hello_for_session = session not in adapter_hello
            fingerprint = _payload_fingerprint(payload)
            previous = adapter_hello.get(session)
            if previous is not None and previous != fingerprint:
                errors.append(
                    f"message {index}:payload: adapter hello changed within "
                    f"session {session!r}"
                )
            elif sequence_valid:
                adapter_hello[session] = fingerprint
                capabilities = payload["capabilities"]
                adapter_capabilities[session] = capabilities
                if (
                    latest_adapter_session is None
                    or session == latest_adapter_session
                    or first_hello_for_session
                ):
                    latest_adapter_session = session

        elif msg_type == "hello_ack":
            fingerprint = _payload_fingerprint(payload)
            previous = host_hello.get(session)
            if previous is not None and previous != fingerprint:
                errors.append(
                    f"message {index}:payload: host hello_ack changed within "
                    f"session {session!r}"
                )
            elif sequence_valid:
                host_hello[session] = fingerprint
                host_capabilities[session] = payload["capabilities"]

        if source == "adapter":
            capabilities = adapter_capabilities.get(session)

            if msg_type == "state_sync":
                disc = payload["disc"]
                if disc is None:
                    if sequence_valid:
                        active_selection[session] = None
                else:
                    evidence = disc["evidence"]
                    evidence_valid = True
                    if (
                        capabilities is not None
                        and evidence not in capabilities["disc_detection"]
                    ):
                        errors.append(
                            f"message {index}:payload.disc.evidence: {evidence!r} "
                            "was not advertised by adapter"
                        )
                        evidence_valid = False
                    counter = disc["selection_counter"]
                    machine_id = disc["machine_id"]
                    previous_counter = last_selection_counter.get(session)
                    counter_valid = True
                    counter_advances = (
                        previous_counter is None or counter > previous_counter
                    )
                    if previous_counter is not None and counter < previous_counter:
                        errors.append(
                            f"message {index}:payload.disc.selection_counter: "
                            f"state sync regressed ({counter} < {previous_counter})"
                        )
                        counter_valid = False
                    elif previous_counter is not None and counter == previous_counter:
                        active = active_selection.get(session)
                        if active is None:
                            errors.append(
                                f"message {index}:payload.disc.selection_counter: "
                                "state sync reused an inactive selection counter"
                            )
                            counter_valid = False
                        elif active != (counter, machine_id):
                            errors.append(
                                f"message {index}:payload.disc.machine_id: state sync "
                                "changed identity for an existing selection counter"
                            )
                            counter_valid = False

                    if sequence_valid and evidence_valid and counter_valid:
                        if counter_advances:
                            last_selection_counter[session] = counter
                        active_selection[session] = (counter, machine_id)

            elif msg_type == "disc_selected":
                evidence = payload["evidence"]
                evidence_valid = True
                if (
                    capabilities is not None
                    and evidence not in capabilities["disc_detection"]
                ):
                    errors.append(
                        f"message {index}:payload.evidence: {evidence!r} "
                        "was not advertised by adapter"
                    )
                    evidence_valid = False

                counter = payload["selection_counter"]
                previous_counter = last_selection_counter.get(session)
                counter_valid = True
                if previous_counter is not None and counter <= previous_counter:
                    errors.append(
                        f"message {index}:payload.selection_counter: selection counter "
                        f"must increase ({counter} <= {previous_counter})"
                    )
                    counter_valid = False
                if sequence_valid and evidence_valid and counter_valid:
                    last_selection_counter[session] = counter
                    active_selection[session] = (counter, payload["machine_id"])

            elif msg_type == "disc_removed":
                counter = payload["selection_counter"]
                active = active_selection.get(session)
                if active is None:
                    errors.append(
                        f"message {index}:payload.selection_counter: no active disc "
                        "selection exists for removal"
                    )
                elif counter != active[0]:
                    errors.append(
                        f"message {index}:payload.selection_counter: removal counter "
                        f"{counter} does not match active selection {active[0]}"
                    )
                elif sequence_valid:
                    active_selection[session] = None

            elif msg_type == "media_control" and capabilities is not None:
                action = payload["action"]
                if action not in capabilities["media_controls"]:
                    errors.append(
                        f"message {index}:payload.action: {action!r} was not "
                        "advertised by adapter"
                    )

        else:
            capabilities = host_capabilities.get(session)

            if msg_type == "now_playing" and capabilities is not None:
                if not capabilities["now_playing"]:
                    errors.append(
                        f"message {index}:type: host emitted now_playing after "
                        "advertising now_playing=false"
                    )

            elif msg_type == "source_request":
                if capabilities is not None and not capabilities["source_request"]:
                    errors.append(
                        f"message {index}:type: host emitted source_request after "
                        "advertising source_request=false"
                    )

                if latest_adapter_session is not None:
                    adapter_caps = adapter_capabilities.get(latest_adapter_session)
                    if (
                        adapter_caps is not None
                        and not adapter_caps["auto_source_switch"]
                    ):
                        errors.append(
                            f"message {index}:type: source_request targets an adapter "
                            "that advertised auto_source_switch=false"
                        )

        if msg_type == "ack":
            target = (_peer(source), payload["ack_session"], payload["ack_seq"])
            if target not in seen_seq:
                errors.append(
                    f"message {index}:payload.ack_seq: acknowledgement target "
                    f"{target[0]}/{target[1]} seq {target[2]} has not been seen"
                )

        elif msg_type == "error" and "related_seq" in payload:
            target = (
                _peer(source),
                payload["related_session"],
                payload["related_seq"],
            )
            if target not in seen_seq:
                errors.append(
                    f"message {index}:payload.related_seq: error target "
                    f"{target[0]}/{target[1]} seq {target[2]} has not been seen"
                )

        if sequence_valid and len(errors) == message_error_start:
            last_seq[key] = seq

    return errors
