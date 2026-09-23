# ADR 0014: Valid recognition-channel disagreement always fails open

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

PDv1 intentionally carries the same checked identity redundantly through TOC timing, optional CD-TEXT, and an audio beacon. In real integrations a vehicle may expose one or several of those channels.

A priority rule such as "TOC always wins" would make corruption, stale metadata, or an adapter decoding bug look like a valid disc selection whenever another channel disagreed.

## Decision

Each strong channel is decoded and validated independently. One valid channel may recognize a disc. Multiple matching valid channels are corroborating evidence.

If two independently valid channels identify different PD IDs, runtime recognition returns `conflict` and no identity. The adapter fails open as ordinary CD behavior rather than choosing a winner.

Malformed or absent optional channels are diagnostics, not conflicting identities. They do not suppress another independent strong channel.

Coarse evidence such as track count or total duration is never promoted to a strong identity channel.

CD-TEXT machine IDs must appear as standalone identifier tokens rather than as prefixes embedded in longer alphanumeric/digit strings.

## Consequences

- There is no hidden channel-precedence policy for vehicle integrations to disagree about.
- Corrupt/stale redundant metadata cannot silently override another checked identity.
- A car exposing only one strong channel can still participate.
- Hardware compatibility reports can separately record which recognition channel was actually available.
