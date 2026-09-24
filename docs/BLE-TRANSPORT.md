# PD Bridge BLE transport — Draft 0.1

This profile carries the existing **logical PD Bridge messages** over Bluetooth Low Energy without changing their semantics.

It is pre-hardware work: the GATT contract and byte framing can be specified and exhaustively tested in software, while real phone/adapter interoperability, radio conditions, pairing UX, and platform BLE behavior remain future evidence.

## Roles

- **Vehicle adapter:** BLE peripheral / GATT server.
- **Playback host:** BLE central / GATT client, normally the phone.

The adapter advertises the custom PD Bridge service.

## GATT profile

| Item | UUID | Properties |
| --- | --- | --- |
| PD Bridge service | `5c1d3a30-1f5b-4f6a-9d3e-3b8c77e2d001` | primary service |
| Adapter → host | `5c1d3a30-1f5b-4f6a-9d3e-3b8c77e2d002` | **indicate** |
| Host → adapter | `5c1d3a30-1f5b-4f6a-9d3e-3b8c77e2d003` | **write with response** |

The machine-readable reference lives in `tests/vectors/ble-profile.yaml` and the same values are exposed by `playlistdisc.ble_transport.ble_profile()`.

These UUIDs belong to **PD Bridge BLE Draft 0.1**. They are not part of the permanent physical disc identity and may be revised before a stable transport release if real interoperability testing exposes a problem.

## Why reliable GATT operations

Bridge traffic is tiny and control-oriented rather than high-throughput audio.

Adapter → host uses indications so the ATT layer confirms delivery before the next indication.

Host → adapter uses writes with response for the same reason.

PD Bridge's own session/sequence fields remain useful above BLE for reconnect semantics and diagnostics; they are not a replacement for transport delivery.

Actual music audio is **not** carried in these characteristics.

## Framing

GATT value boundaries are treated only as transport chunks. A logical PD Bridge message is:

```text
+----------------------+--------------------------+
| uint32 big-endian N  | N bytes UTF-8 JSON      |
+----------------------+--------------------------+
```

Rules:

- N is the UTF-8 JSON payload length, excluding the four-byte prefix.
- N must be 1–16,384 bytes.
- JSON is the same logical PD Bridge object validated by the packaged bridge schema.
- The reference encoder uses sorted-key compact JSON for deterministic bytes.
- A frame may be split at **any byte boundary** across GATT operations.
- Several complete frames may arrive in one accumulated byte chunk.
- No delimiter, newline, ATT MTU, or single-GATT-operation message boundary is assumed.

A 16 KiB limit is comfortably above current bridge messages while bounding memory allocation and corrupted-length damage.

There is no additional application CRC. BLE already protects link frames, reliable GATT operations acknowledge delivery, and every decoded payload must also pass UTF-8, JSON, JSON Schema, and PD machine-ID validation.

## Decoder failure behavior

An invalid length, UTF-8 payload, JSON payload, or logical bridge message puts the reference decoder into a failed state.

It does **not** scan forward looking for a plausible next frame after an invalid length prefix. Byte-level resynchronization could turn corrupted bytes into a different valid control message.

The integration should instead discard/reset that stream, normally by reconnecting. A new connection begins with an empty decoder.

## Connection startup

After the BLE link is secured and the host has subscribed to adapter indications:

1. adapter sends `hello`;
2. host sends `hello_ack`;
3. adapter sends `state_sync`;
4. ordinary PD Bridge events continue.

A reconnect repeats this logical synchronization. The host runtime already deduplicates a repeated current selection within the same adapter session.

## Security and privacy

The transport profile requires the BLE link to be encrypted before application PD Bridge traffic is exchanged.

Where adapter hardware supports an authenticated pairing method, implementations should use it. Hardware with no secure input/output may be limited to a platform's weaker pairing method; Draft 0.1 does not pretend software-only tests can establish the resulting MITM resistance.

The bridge still must not carry:

- OAuth access/refresh tokens;
- passwords;
- provider cookies;
- private provider credentials.

Only PD identity, controls, capability/state, and playback metadata belong on the bridge.

Bond storage, re-pair/reset UX, multi-phone policy, and exact mobile background-reconnection behavior remain implementation/hardware work.

## Reference codec

`playlistdisc.ble_transport` provides:

- `encode_bridge_frame(message)`;
- `BridgeFrameDecoder.feed(chunk)`;
- `fragment_frame(frame, max_chunk_bytes)`;
- profile constants and `ble_profile()`.

The implementation depends on no BLE package, so firmware/mobile developers can port the framing independently.

Tests cover every possible two-piece split of a reference message, single-byte chunks, multiple frames in one chunk, small 20-byte chunks, malformed lengths, invalid UTF-8/JSON/logical messages, failed-state behavior, and reset recovery.

## What remains hardware-gated

This draft does **not** establish:

- Android/iOS background reconnect reliability;
- practical advertising/connection latency in a car;
- negotiated ATT MTU/data length on any phone/adapter;
- pairing/bond persistence across power cycles;
- radio coexistence/interference behavior;
- how quickly an adapter wakes on ACC/accessory power;
- multi-phone ownership/selection UX;
- whether an individual MCU BLE stack implements indications/writes correctly.

Those belong in later adapter/mobile integration testing, not in the logical protocol.
