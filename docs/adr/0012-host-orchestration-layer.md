# ADR 0012: Host orchestration is a deterministic layer between bridge and provider

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

The project already has three separate contracts:

1. PD Bridge events from a vehicle adapter;
2. provider-neutral playback plans;
3. future provider APIs that will actually resolve/materialize/play content.

Without an explicit host orchestration layer, reconnect behavior, repeated state sync, disc removal, source switching, and OEM media controls would be reimplemented independently in every phone/provider integration.

## Decision

Define a small deterministic host-runtime state machine that consumes adapter-side bridge events and emits normalized host actions.

Selection identity is the tuple of adapter session, selection counter and PD machine ID. Repeated state sync for the same tuple is idempotent. A new adapter session is a new selection.

The runtime may request source activation only when the adapter advertised that capability. Playback-plan uncertainty remains visible: ready/requires-lookup are executable, partial is policy-gated, and ambiguous/unavailable/unplayable are blocked by default.

Disc-removal stop/source behavior is configurable host policy rather than physical-format semantics.

## Consequences

- Reconnect behavior can be regression-tested without BLE, provider accounts, or a car.
- Vehicle adapters stay unaware of provider semantics.
- Provider plugins receive one execution action instead of interpreting raw bridge traffic.
- User preferences such as continuing playback after disc removal can vary without redefining PDv1.
- The eventual mobile implementation can port the state machine to another language while preserving the same action contract.
