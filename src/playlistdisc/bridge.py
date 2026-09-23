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
                raise ValueError(f"line {line_number}: bridge message must be a JSON object")
            messages.append(value)
    return messages


def validate_bridge_transcript(
    messages: Iterable[dict[str, Any]],
    schema: dict[str, Any] | None = None,
) -> list[str]:
    """Validate structure plus sequence/selection invariants across a transcript."""
    schema = schema or load_bridge_schema()
    errors: list[str] = []
    last_seq: dict[tuple[str, str], int] = {}
    active_selection: dict[str, int | None] = {}

    for index, message in enumerate(messages, start=1):
        message_errors = validate_bridge_message(message, schema)
        errors.extend(f"message {index}:{error}" for error in message_errors)
        if message_errors:
            continue

        source = message["source"]
        session = message["session"]
        seq = message["seq"]
        key = (source, session)
        if key in last_seq and seq <= last_seq[key]:
            errors.append(
                f"message {index}:seq: {source}/{session} sequence must increase "
                f"strictly ({seq} <= {last_seq[key]})"
            )
        last_seq[key] = seq

        if source != "adapter":
            continue

        msg_type = message["type"]
        payload = message["payload"]
        if msg_type == "state_sync":
            disc = payload["disc"]
            active_selection[session] = (
                None if disc is None else disc["selection_counter"]
            )
        elif msg_type == "disc_selected":
            counter = payload["selection_counter"]
            previous = active_selection.get(session)
            if previous is not None and counter <= previous:
                errors.append(
                    f"message {index}:payload.selection_counter: selection counter "
                    f"must increase ({counter} <= {previous})"
                )
            active_selection[session] = counter
        elif msg_type == "disc_removed":
            counter = payload["selection_counter"]
            previous = active_selection.get(session)
            if previous is None:
                errors.append(
                    f"message {index}:payload.selection_counter: no active disc "
                    "selection exists for removal"
                )
            elif counter != previous:
                errors.append(
                    f"message {index}:payload.selection_counter: removal counter "
                    f"{counter} does not match active selection {previous}"
                )
            else:
                active_selection[session] = None

    return errors
