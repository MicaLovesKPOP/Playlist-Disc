# ADR 0009: Bridge capability announcements are session contracts

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

The logical bridge already advertised capabilities, sender sessions and per-session sequence numbers, but the first validator treated most of those fields as descriptive metadata.

That left several classes of software bug undetectable before vehicle work: reusing a disc-selection counter after removal, emitting controls that an adapter never advertised, requesting automatic source switching from an adapter that explicitly lacks it, or acknowledging an ambiguous bare sequence number after a session restart.

## Decision

Observed `hello` and `hello_ack` capability announcements are treated as contracts for the remainder of that sender session.

The transcript validator checks capability use whenever the relevant announcement is available, but still accepts partial captures that begin mid-session.

Selection counters remain strictly monotonic for the complete adapter session, even after a disc is removed. `state_sync` may repeat the current counter but cannot regress it.

Acknowledgements now identify a peer message by both session and sequence. Optional error references use the same session+sequence pairing.

Repeated hello/hello_ack messages are allowed for reconnects but cannot silently change identity or capabilities within the same session.

## Consequences

- Logical integration bugs can be found with synthetic transcripts before any BLE/CAN/MOST implementation exists.
- Adapters and hosts must degrade rather than emit operations they said were unsupported.
- Session rollover no longer makes acknowledgement targets ambiguous.
- Partial diagnostic captures remain valid input; only capabilities actually observed are enforced.
- A genuine capability change requires a new sender session identifier.
