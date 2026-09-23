# ADR 0005: Bridge semantics are transport-neutral

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

Shadow, Choco, Misty, and future cars expose radically different electrical interfaces. Hard-coding phone behavior around Alfa B-CAN, MINI MOST/K-CAN, PSA CAN, or a particular Bluetooth module would make provider and vehicle logic inseparable.

Likewise, choosing a BLE packet layout before any vehicle prototype exists would prematurely freeze constraints that belong to a transport rather than the user-visible behavior.

## Decision

Define a versioned logical PD Bridge protocol independently of transport and vehicle wiring.

The reference encoding is JSON/JSONL because it is inspectable, testable, and convenient for software simulators. Vehicle adapters normalize physical events into logical disc-selection, removal, control, source-state, and capability messages. The playback host returns playback state and now-playing metadata semantically.

Transport profiles may later encode the same messages more compactly, including BLE or USB implementations, without changing PDv1 physical disc identity.

## Consequences

- Vehicle-specific reverse engineering stays outside provider/playback logic.
- Phone/provider code can be tested before vehicle hardware exists.
- Reconnection and capability behavior can be specified and validated in software.
- Adapters must truthfully advertise missing capabilities rather than relying on car-specific assumptions.
- Transport security, framing, MTU, and retry behavior remain separate decisions.
