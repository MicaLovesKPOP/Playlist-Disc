# ADR 0015: BLE carries a bounded framed bridge stream, not GATT-sized messages

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

PD Bridge messages need a practical phone↔vehicle-adapter transport. BLE is widely available, but ATT MTU and GATT value sizes vary by platform, connection and implementation.

Making one logical message equal one notification/write would bake a negotiated transport size into the logical protocol. Using unreliable notification/write-without-response operations would also add avoidable recovery complexity for tiny control messages.

## Decision

Define PD Bridge BLE Draft 0.1 with the adapter as GATT peripheral/server and phone as central/client.

Adapter→host uses indications. Host→adapter uses writes with response.

The two characteristics carry a byte stream framed as:

- 4-byte unsigned big-endian payload length;
- 1–16,384 bytes of UTF-8 JSON containing one validated logical PD Bridge message.

Logical frames may be fragmented/coalesced across arbitrary GATT operations. A decoding/framing error fails closed until reset/reconnect rather than attempting byte resynchronization.

BLE link encryption is required before bridge traffic. Provider credentials never belong in bridge messages.

## Consequences

- The logical PD Bridge schema stays independent of ATT MTU.
- Very small or larger negotiated BLE payload sizes use the same framing.
- Reliable ATT operations are slower than unacknowledged ones but appropriate for low-rate controls/state.
- A corrupted stream causes a reconnect/state-sync rather than risky heuristic recovery.
- The framing codec is testable without a BLE radio or phone SDK.
- Real pairing strength, mobile background behavior and adapter interoperability remain hardware/platform tests.
