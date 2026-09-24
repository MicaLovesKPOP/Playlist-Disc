# Offline host runtime

PD Bridge defines what a vehicle adapter reports, and the playback-plan compiler defines what a selected disc means for one provider. Draft 0.2 now includes the missing deterministic layer between them: an offline host-runtime state machine.

It does **not** log into Spotify/Apple Music, stream audio, create Bluetooth packets, or touch vehicle hardware.

## Replay

```bash
pdv1 host-replay tests/vectors/host-adapter-session.jsonl \
  --plan tests/vectors/host-playback-plan.json
```

The output is JSONL using the packaged `PDv1-host-action` contract.

## Host actions

The reference runtime can emit:

- `source_request` — activate/deactivate the car's streaming source when the adapter advertised automatic source switching;
- `execute_plan` — hand a validated playback plan to the future provider plugin;
- `provider_control` — forward normalized next/previous/play-pause input;
- `stop_playback` — stop the selected playback context under the configured removal policy;
- `selection_blocked` — preserve an unavailable/ambiguous/unplayable outcome instead of guessing.

Every action carries the selected machine ID, adapter session and selection counter so logs/actions remain correlated across reconnects.

The action contract is deliberately discriminated rather than a bag of optional fields. A `source_request` may carry only its source-switch action, `execute_plan` carries only a validated playback plan, `provider_control` carries only a media-control action, `stop_playback` carries its reason, and `selection_blocked` carries only a non-executable status plus reason. Fields belonging to another action type are rejected. In particular, `ready` and `requires_lookup` cannot be serialized as `selection_blocked`, because the runtime treats both as executable states.

## Live session guardrails

`HostRuntime.consume()` validates more than the shape of each incoming bridge message. It keeps the safety-critical adapter session state needed when messages arrive one at a time rather than as a finished transcript:

- adapter sequence numbers must increase strictly inside one session;
- a repeated `hello` may not silently change the adapter identity/capability payload;
- `disc_selected` counters must increase strictly;
- `state_sync` may repeat the current counter only for the same still-active machine ID, and may neither regress nor reactivate a removed counter;
- detection evidence and media-control actions must have been advertised by the adapter when capabilities are known;
- once a newer adapter session has announced itself, the older observed session is retired: late messages from it, including a repeated `hello`, are ignored so buffered traffic cannot roll the runtime back to an old adapter boot or operate the current playback context;
- current-session removal messages must match the active selection counter rather than being silently accepted.

The offline `bridge-validate` transcript checker enforces the same counter/identity rule for `state_sync`, including rejecting a reused counter that is rebound to a different PD identity or resurrected after removal. These checks do not add transport security; they make replay, reconnect, and stale-message behavior deterministic before any BLE or vehicle implementation exists.

## Reconnect semantics

Within one adapter session, the tuple:

```text
(adapter_session, selection_counter, machine_id)
```

identifies one selection event.

If that selection later appears again in `state_sync`, the runtime updates source state but does not start the playlist twice.

A new adapter boot/session is different. Even if the same physical disc remains inserted, its new session/counter is treated as a new selection. The playback plan's own `start` policy (first/random/resume) remains available to the provider layer. Messages that arrive late from the older session no longer control the new session's playback context.

## Playback-plan policy

By default:

- `ready` is executable;
- `requires_lookup` is executable because provider lookup/materialization is explicitly a plugin responsibility;
- `partial` is blocked unless the user/host enables partial playback;
- `ambiguous`, `unavailable`, and `unplayable` are blocked.

This prevents the host from turning resolver uncertainty into silent substitutions.

## Source switching

A `source_request` is generated only after an adapter `hello` advertises `auto_source_switch=true`.

On selection, an activate request is emitted only when the latest source state is not active. On removal, a deactivate request is emitted only if the source was claimed by that selected context and removal policy asks for it.

If the adapter cannot switch source automatically, the runtime simply executes/blocks the provider plan and leaves source selection to the driver.

## Removal policy

The reference defaults mimic a physical-disc mental model: removing the selected Playlist Disc stops its playback context and, when possible, asks the car to leave the streaming source.

Both are configurable:

```text
--leave-playing-on-remove
--keep-source-on-remove
```

These are host UX choices, not properties of PDv1 identity.

## Boundary before hardware

The runtime proves state-machine semantics only. It does not establish whether any reference vehicle can actually detect a disc, switch source, expose controls, or render metadata. Those remain compatibility/capture questions.
