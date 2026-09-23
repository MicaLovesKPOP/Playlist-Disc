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

## 3. Adapter → host messages

### `hello`

Announces adapter identity and capabilities: available PD detection channels, physical media controls, automatic streaming-source switching, and whether/how the adapter can render metadata onto OEM displays.

### `state_sync`

Sent after connection/reconnection to describe current vehicle power state, current strongly recognized disc (if any), its selection counter, and whether the streaming source is active.

This is important when a Playlist Disc is left inserted across an ignition cycle or phone reconnect.

### `disc_selected`

Reports a strongly recognized PDv1 machine ID, monotonic selection counter, and evidence channel (`toc`, `cdtext`, `audio_beacon`, or `manual`). Weak/ambiguous recognition is deliberately not a bridge event; the vehicle layer must fail open as ordinary CD playback instead.

### `disc_removed`

Clears the active selection. Its selection counter must match the selection being removed.

### `media_control`

Reports OEM user controls normalized to `next`, `previous`, or `play_pause`.

### `source_state`

Reports whether the car-side streaming source is currently active.

## 4. Host → adapter messages

### `hello_ack`

Announces host implementation and whether it can provide now-playing metadata and accept automatic source requests.

### `source_request`

Requests `activate_streaming` or `deactivate_streaming`. An adapter without automatic source switching simply advertises that limitation in `hello` and need not pretend otherwise.

### `playback_state`

Reports normalized host playback state. An optional `context_id` ties playback to the selected PD machine ID; provider name is diagnostic/UX metadata only.

### `now_playing`

Carries semantic metadata such as title, artist, album, position, and duration. Vehicle integrations choose how much can be rendered on their OEM displays.

## 5. Bidirectional control messages

`ack` acknowledges a sender sequence number when a transport/integration wants explicit acknowledgements. `error` reports a machine-readable code and human diagnostic message. Logical protocol users must not assume every ordinary event receives an ack.

## 6. Sequence and reconnect rules

`seq` is monotonic per sender session; it is not a global clock.

Adapter selection counters are monotonic within an adapter session. A fresh `disc_selected` event must increment the counter. `disc_removed` must refer to the active counter.

After a reconnect, `state_sync` communicates current state rather than requiring the host to reconstruct it from old traffic. A newly booted adapter may use a new session identifier and begin its sequence/counter space again.

A disc left inserted may therefore be selected again after a new vehicle power/adapter session. Playback policy (restart, resume, or ignore repeated selection) belongs to the host/user settings, not the physical disc.

## 7. Safety and privacy

The bridge carries PD identities, controls, capability data, and playback metadata. It must not carry OAuth tokens, account passwords, cookies, or streaming-service secrets.

Transport pairing/encryption is the responsibility of the chosen transport profile. A vehicle adapter must not send a `disc_selected` event for weak recognition merely to make the experience feel automatic.

## 8. Capability negotiation

Adapters truthfully advertise what they can do. Examples:

- Shadow may initially provide head-unit controls and CDC audio but no metadata display;
- Choco may eventually support OEM steering controls, automatic source switching, and MOST-backed display metadata;
- Misty may support steering-stalk controls and metadata on the separate PSA multifunction display.

The host must degrade gracefully when a capability is absent.

## 9. Validation

`pdv1 bridge-validate <transcript.jsonl>` validates JSON Schema, PD machine-ID check digits, per-session sequence monotonicity, and adapter selection/removal counters.

The repository includes a deterministic reference transcript for software integration tests.
