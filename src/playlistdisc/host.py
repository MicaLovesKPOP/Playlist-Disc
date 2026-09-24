"""Offline host-runtime state machine for PD Bridge adapter events."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json
from typing import Any, Callable

from jsonschema import Draft202012Validator

from .bridge import validate_bridge_message
from .identity import PDIdentity
from .playback import PlaybackPlan, validate_playback_plan

PlanLike = PlaybackPlan | dict[str, Any]
Planner = Callable[[str], PlanLike]


@dataclass(frozen=True, slots=True)
class SelectionContext:
    machine_id: str
    adapter_session: str
    selection_counter: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "machine_id": self.machine_id,
            "adapter_session": self.adapter_session,
            "selection_counter": self.selection_counter,
        }


@dataclass(frozen=True, slots=True)
class HostAction:
    type: str
    context: SelectionContext
    action: str | None = None
    plan: dict[str, Any] | None = None
    status: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": 1,
            "format": "PDv1-host-action",
            "type": self.type,
            "context": self.context.to_dict(),
        }
        if self.action is not None:
            data["action"] = self.action
        if self.plan is not None:
            data["plan"] = self.plan
        if self.status is not None:
            data["status"] = self.status
        if self.reason is not None:
            data["reason"] = self.reason
        return data


def load_host_action_schema() -> dict[str, Any]:
    resource = files("playlistdisc").joinpath("schemas/host-action.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def validate_host_action(
    data: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> list[str]:
    schema = schema or load_host_action_schema()
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda error: [str(part) for part in error.path],
    )
    messages: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{location}: {error.message}")
    if messages:
        return messages

    try:
        identity = PDIdentity.parse(data["context"]["machine_id"])
    except ValueError as exc:
        messages.append(f"context.machine_id: {exc}")
    else:
        if data["type"] == "execute_plan":
            plan = data.get("plan")
            if not isinstance(plan, dict):
                messages.append("plan: execute_plan requires a playback-plan object")
            else:
                plan_errors = validate_playback_plan(plan)
                messages.extend(f"plan:{message}" for message in plan_errors)
                if not plan_errors and plan["machine_id"] != identity.machine_id:
                    messages.append(
                        "plan.machine_id: does not match selected bridge context"
                    )

    action = data.get("action")
    if data["type"] == "source_request" and action not in {
        "activate_streaming",
        "deactivate_streaming",
    }:
        messages.append("action: source_request requires a source-switch action")
    if data["type"] == "provider_control" and action not in {
        "next",
        "previous",
        "play_pause",
    }:
        messages.append("action: provider_control requires a media-control action")
    return messages


def _plan_dict(plan: PlanLike) -> dict[str, Any]:
    if isinstance(plan, PlaybackPlan):
        data = plan.to_dict()
    elif isinstance(plan, dict):
        data = dict(plan)
    else:
        raise TypeError("planner must return PlaybackPlan or dict")
    errors = validate_playback_plan(data)
    if errors:
        raise ValueError("planner returned invalid playback plan: " + "; ".join(errors))
    return data


class HostRuntime:
    """Turn adapter-side bridge events into deterministic provider/vehicle actions."""

    def __init__(
        self,
        planner: Planner,
        *,
        allow_partial: bool = False,
        stop_on_remove: bool = True,
        deactivate_source_on_remove: bool = True,
    ) -> None:
        self._planner = planner
        self.allow_partial = allow_partial
        self.stop_on_remove = stop_on_remove
        self.deactivate_source_on_remove = deactivate_source_on_remove
        self._capabilities: dict[str, dict[str, Any]] = {}
        self._hello_fingerprints: dict[str, str] = {}
        self._last_seq: dict[str, int] = {}
        self._last_selection_counter: dict[str, int] = {}
        self._current_adapter_session: str | None = None
        self._source_active: dict[str, bool] = {}
        self._handled: set[tuple[str, int, str]] = set()
        self._active_selection: SelectionContext | None = None
        self._playback_context: SelectionContext | None = None
        self._source_owned_context: SelectionContext | None = None

    def _finish(self, *actions: HostAction) -> tuple[HostAction, ...]:
        for action in actions:
            errors = validate_host_action(action.to_dict())
            if errors:
                raise ValueError("generated host action is invalid: " + "; ".join(errors))
        return tuple(actions)

    def _auto_source_switch(self, session: str) -> bool:
        capabilities = self._capabilities.get(session)
        return bool(capabilities and capabilities.get("auto_source_switch") is True)

    def _require_advertised_evidence(self, session: str, evidence: str) -> None:
        capabilities = self._capabilities.get(session)
        if capabilities is not None and evidence not in capabilities["disc_detection"]:
            raise ValueError(
                f"adapter evidence {evidence!r} was not advertised for session {session!r}"
            )

    def _record_disc_selected(self, session: str, counter: int) -> None:
        previous = self._last_selection_counter.get(session)
        if previous is not None and counter <= previous:
            raise ValueError(
                "adapter selection counter must increase strictly "
                f"within session {session!r} ({counter} <= {previous})"
            )
        self._last_selection_counter[session] = counter

    def _record_state_sync_selection(self, context: SelectionContext) -> None:
        session = context.adapter_session
        counter = context.selection_counter
        previous = self._last_selection_counter.get(session)
        if previous is None or counter > previous:
            self._last_selection_counter[session] = counter
            return
        if counter < previous:
            raise ValueError(
                "adapter state-sync selection counter regressed "
                f"within session {session!r} ({counter} < {previous})"
            )

        active = self._active_selection
        if active is None or active.adapter_session != session:
            raise ValueError(
                "adapter state sync reused an inactive selection counter "
                f"within session {session!r}"
            )
        if active.selection_counter != counter or active.machine_id != context.machine_id:
            raise ValueError(
                "adapter state sync changed identity for an existing selection counter "
                f"within session {session!r}"
            )

    def _selection_actions(
        self,
        context: SelectionContext,
    ) -> tuple[HostAction, ...]:
        key = (
            context.adapter_session,
            context.selection_counter,
            context.machine_id,
        )
        self._active_selection = context
        if key in self._handled:
            return ()
        self._handled.add(key)

        try:
            plan = _plan_dict(self._planner(context.machine_id))
        except (KeyError, LookupError, TypeError, ValueError) as exc:
            return self._finish(
                HostAction(
                    "selection_blocked",
                    context,
                    status="unavailable",
                    reason=f"playback plan unavailable: {exc}",
                )
            )

        if plan["machine_id"] != context.machine_id:
            return self._finish(
                HostAction(
                    "selection_blocked",
                    context,
                    status="unavailable",
                    reason="playback plan machine_id does not match selected disc",
                )
            )

        status = plan["status"]
        executable = status in {"ready", "requires_lookup"} or (
            status == "partial" and self.allow_partial
        )
        if not executable:
            return self._finish(
                HostAction(
                    "selection_blocked",
                    context,
                    status=status,
                    reason=plan.get("reason")
                    or f"playback plan status {status!r} is not auto-executable",
                )
            )

        actions: list[HostAction] = []
        if self._auto_source_switch(context.adapter_session) and not self._source_active.get(
            context.adapter_session, False
        ):
            actions.append(
                HostAction(
                    "source_request",
                    context,
                    action="activate_streaming",
                )
            )
            self._source_owned_context = context
        actions.append(HostAction("execute_plan", context, plan=plan))
        self._playback_context = context
        return self._finish(*actions)

    def _remove_actions(
        self,
        context: SelectionContext,
    ) -> tuple[HostAction, ...]:
        actions: list[HostAction] = []
        if self.stop_on_remove and self._playback_context == context:
            actions.append(
                HostAction(
                    "stop_playback",
                    context,
                    reason="selected Playlist Disc was removed",
                )
            )
            self._playback_context = None

        if (
            self.deactivate_source_on_remove
            and self._source_owned_context == context
            and self._auto_source_switch(context.adapter_session)
        ):
            actions.append(
                HostAction(
                    "source_request",
                    context,
                    action="deactivate_streaming",
                )
            )
            self._source_owned_context = None

        if self._active_selection == context:
            self._active_selection = None
        return self._finish(*actions)

    def consume(self, message: dict[str, Any]) -> tuple[HostAction, ...]:
        errors = validate_bridge_message(message)
        if errors:
            raise ValueError("invalid bridge message: " + "; ".join(errors))
        if message["source"] != "adapter":
            return ()

        session = message["session"]
        seq = message["seq"]
        msg_type = message["type"]
        payload = message["payload"]

        if msg_type != "hello" and self._current_adapter_session is not None:
            if session != self._current_adapter_session:
                return ()

        previous_seq = self._last_seq.get(session)
        if previous_seq is not None and seq <= previous_seq:
            raise ValueError(
                "adapter sequence must increase strictly "
                f"within session {session!r} ({seq} <= {previous_seq})"
            )
        self._last_seq[session] = seq

        if msg_type == "hello":
            fingerprint = json.dumps(
                payload,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
            previous = self._hello_fingerprints.get(session)
            if previous is not None and previous != fingerprint:
                raise ValueError(
                    f"adapter hello changed within session {session!r}"
                )
            self._hello_fingerprints[session] = fingerprint
            self._capabilities[session] = dict(payload["capabilities"])
            self._current_adapter_session = session
            return ()

        if msg_type == "source_state":
            self._source_active[session] = bool(payload["active"])
            return ()

        if msg_type == "disc_selected":
            self._require_advertised_evidence(session, payload["evidence"])
            self._record_disc_selected(session, payload["selection_counter"])
            context = SelectionContext(
                machine_id=payload["machine_id"],
                adapter_session=session,
                selection_counter=payload["selection_counter"],
            )
            return self._selection_actions(context)

        if msg_type == "state_sync":
            self._source_active[session] = bool(payload["streaming_source_active"])
            disc = payload["disc"]
            if disc is None:
                active = self._active_selection
                if active is not None and active.adapter_session == session:
                    return self._remove_actions(active)
                return ()
            self._require_advertised_evidence(session, disc["evidence"])
            context = SelectionContext(
                machine_id=disc["machine_id"],
                adapter_session=session,
                selection_counter=disc["selection_counter"],
            )
            self._record_state_sync_selection(context)
            return self._selection_actions(context)

        if msg_type == "disc_removed":
            active = self._active_selection
            if active is None or active.adapter_session != session:
                raise ValueError(
                    f"adapter removal has no active selection in session {session!r}"
                )
            if active.selection_counter != payload["selection_counter"]:
                raise ValueError(
                    "adapter removal counter does not match active selection "
                    f"({payload['selection_counter']} != {active.selection_counter})"
                )
            return self._remove_actions(active)

        if msg_type == "media_control":
            capabilities = self._capabilities.get(session)
            if (
                capabilities is not None
                and payload["action"] not in capabilities["media_controls"]
            ):
                raise ValueError(
                    f"adapter media control {payload['action']!r} was not advertised "
                    f"for session {session!r}"
                )
            context = self._playback_context
            if context is None or context.adapter_session != session:
                return ()
            return self._finish(
                HostAction(
                    "provider_control",
                    context,
                    action=payload["action"],
                )
            )

        return ()
