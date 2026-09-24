# PD Bridge — logical protocol Draft 0.1

**Status:** transport-neutral pre-hardware draft. This protocol is intentionally versioned separately from the PDv1 physical disc format.

## 1. Purpose

PD Bridge defines the logical messages exchanged between a vehicle adapter and playback host (normally a phone application). It lets Alfa, MINI, PSA, or future vehicle integrations expose the same semantics even when their electrical buses, radios, controls, and displays are completely different.

The protocol does not define BLE characteristics, USB framing, CAN frames, MOST messages, authentication, provider APIs, or audio transport. Those are implementation layers.

## 2. Reference encoding

The reference/debug encoding is UTF-8 JSON. A transcript uses one JSON object per line (JSONL). Future constrained transports may encode the same logical fields in CBOR or another compact representation without changing message semantics.

Every message contains:

- `protocol`: always `pdbridge`;
- `version`: logical protocol version, currently `1`;
- `source`: `adapter` or `host`;
- `session`: opaque sender session/boot identifier;
- `seq`: monotonically increasing integer within one `(source, session)` pair;
- `type`: message type;
- `payload`: type-specific object;
- optional `timestamp_ms`: sender-local diagnostic timestamp; never used as identity/order authority.

The machine-readable schema is shipped as `playlistdisc/schemas/bridge-message.schema.json`.

### Draft BLE transport profile

Draft 0.2 includes a non-normative-to-PDv1-physical-format BLE transport profile for carrying these same logical JSON messages. The adapter is the GATT peripheral/server and the phone/playback host is the central/client. Adapter→host traffic uses indications; host→adapter traffic uses writes with response. Each logical message is encoded as a four-byte unsigned big-endian payload length followed by canonical UTF-8 JSON, with a 16,384-byte payload maximum. The framed stream may be split across any number of GATT operations and does not assume a particular negotiated ATT MTU.

A framing or decoded-message validation error terminates the logical stream until reset/reconnect; implementations do not attempt byte-level resynchronization after a corrupted length prefix. On a fresh secure connection, normal logical startup remains `hello` → `hello_ack` → `state_sync`.

The current custom service/characteristic UUIDs and transport profile are Draft 0.1 and are versioned independently of PDv1 physical identity. See `docs/BLE-TRANSPORT.md`.

A transcript validator may be run on a partial capture. Capability-dependent checks are therefore applied only after the corresponding `hello` or `hello_ack` has appeared.

## 3. Adapter → host messages

### `hello`

Announces adapter identity and capabilities: available PD detection channels, physical media controls, automatic streaming-source switching, and whether/how the adapter can render metadata onto OEM displays.

If `metadata_display.supported` is true, at least one supported field must be advertised. If it is false, the field list must be empty.

Repeating `hello` in the same adapter session is allowed (for example after a transport reconnect), but the adapter identity/capabilities must not mutate until a new session identifier is used.

### `state_sync`

Sent after connection/reconnection to describe current vehicle power state, current strongly recognized disc (if any), its selection counter, and whether the streaming source is active.

This is important when a Playlist Disc is left inserted across an ignition cycle or phone reconnect.

A state-sync may repeat the current selection counter, but must never move that adapter session's counter backwards.

### `disc_selected`

Reports a strongly recognized PDv1 machine ID, monotonic selection counter, and evidence channel (`toc`, `cdtext`, `audio_beacon`, or `manual`). Weak/ambiguous recognition is deliberately not a bridge event; the vehicle layer must fail open as ordinary CD playback instead.

The evidence channel must have been advertised in the adapter's `disc_detection` capability when a `hello` is available in the transcript.

A new selection counter is strictly monotonic across the whole adapter session, including across remove/reinsert cycles. Removing a disc does not make its counter reusable.

### `disc_removed`

Clears the active selection. Its selection counter must match the selection being removed.

### `media_control`

Reports OEM user controls normalized to `next`, `previous`, or `play_pause`. When adapter capabilities have been observed, the adapter must not emit actions it did not advertise.

### `source_state`

Reports whether the car-side streaming source is currently active.

## 4. Host → adapter messages

### `hello_ack`

Announces host implementation and whether it can provide now-playing metadata and emit automatic source requests.

Repeating `hello_ack` with the same host session is allowed, but host identity/capabilities remain stable for that session.

### `source_request`

Requests `activate_streaming` or `deactivate_streaming`.

A host that advertised `source_request=false` must not emit this message. Likewise, after an adapter has advertised `auto_source_switch=false`, the host must degrade gracefully instead of sending a source request that the adapter said it cannot perform.

### `playback_state`

Reports normalized host playback state. An optional `context_id` ties playback to a PD machine ID; provider name is diagnostic/UX metadata only.

### `now_playing`

Carries semantic metadata such as title, artist, album, position, and duration. Vehicle integrations choose how much can be rendered on their OEM displays.

A host that advertised `now_playing=false` must not emit this message.

## 5. Bidirectional control messages

### `ack`

An acknowledgement contains both `ack_session` (the peer session identifier) and `ack_seq` (the sequence number within that peer session). The explicit session is required because sequence numbers restart when a sender creates a new session. In a chronological transcript, an acknowledgement target must already have been observed.

Logical protocol users must not assume every ordinary event receives an acknowledgement.

### `error`

An error carries a machine-readable code and human diagnostic message. It may refer to a peer message using `related_session` + `related_seq`; those two fields are a pair and neither is meaningful without the other.

In a chronological transcript, a referenced peer message must already have been observed.

## 6. Sequence and reconnect rules

`seq` is monotonic per sender session; it is not a global clock.

Adapter selection counters are monotonic within an adapter session. A fresh `disc_selected` event must increment beyond every earlier selection counter in that session, not merely the currently active disc. `disc_removed` must refer to the active counter.

After a reconnect, `state_sync` communicates current state rather than requiring the host to reconstruct it from old traffic. A newly booted adapter may use a new session identifier and begin its sequence/counter space again.

A disc left inserted may therefore be selected again after a new vehicle power/adapter session. Playback policy (restart, resume, or ignore repeated selection) belongs to the host/user settings, not the physical disc.

Once a `hello` from a previously unseen adapter session supersedes the current session, an already-observed older session is retired. Late traffic from that retired session, including a repeated `hello`, must not make it current again. Repeating `hello` for the still-current session remains valid reconnect behavior.

## 7. Safety and privacy

The bridge carries PD identities, controls, capability data, and playback metadata. It must not carry OAuth tokens, account passwords, cookies, or streaming-service secrets.

Transport pairing/encryption is the responsibility of the chosen transport profile. A vehicle adapter must not send a `disc_selected` event for weak recognition merely to make the experience feel automatic.

## 8. Capability negotiation

Adapters and hosts truthfully advertise what they can do. The validator treats observed capability announcements as contracts for the remainder of that sender session.

The reference vehicle profiles may eventually expose very different capabilities:

- an Alfa 147 adapter may initially have head-unit controls and changer audio but no writable metadata display;
- an R55/RAD2 adapter may eventually combine steering controls with MOST-backed source/display integration;
- a C3/RD4 adapter may eventually use steering-stalk controls and a separate multifunction display.

The logical host must degrade gracefully when a capability is absent.

## 9. Reference host behavior

The logical bridge protocol does not mandate playback policy, but Draft 0.2 includes a reference offline host runtime. It consumes validated adapter events and emits a separate `PDv1-host-action` contract for provider/source orchestration. This keeps transport sequencing, provider SDK calls, and user policy separate while making reconnect and selection behavior testable before hardware exists.

The reference host deduplicates the same `(adapter session, selection counter, machine ID)` when it reappears in `state_sync`, but treats the same physical disc under a new adapter session as a new selection. Disc-removal stop/deactivate behavior and partial-plan playback are configurable host policy.

See `docs/HOST-RUNTIME.md`.

## 10. Validation

`pdv1 bridge-validate <transcript.jsonl>` validates:

- JSON Schema and PD machine-ID check digits;
- per-session message sequence monotonicity, without letting an invalid lower/duplicate sequence rewrite the accepted sequence baseline;
- selection-counter monotonicity across remove/reinsert cycles, without letting an invalid reused counter replace the active selection;
- state-sync counter non-regression;
- declared detection/control/source/now-playing capabilities;
- stable repeated capability announcements within a session;
- display-capability self-consistency;
- acknowledgement and related-error references against explicit peer sessions.

The repository includes deterministic reference transcripts for software integration tests.
