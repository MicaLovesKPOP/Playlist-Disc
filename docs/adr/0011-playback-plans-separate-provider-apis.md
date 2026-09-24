# ADR 0011: Playback planning is separate from provider APIs

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

The catalog and exact recording resolver already define provider-neutral musical meaning, but a future phone/provider implementation still needs one consistent answer to: what should happen after this disc ID is selected on this provider?

Embedding that decision separately inside Spotify, Apple Music, local-library, and vehicle integrations would duplicate semantics and invite provider-specific divergence.

## Decision

Compile catalog/private records into a versioned `PDv1-playback-plan` before invoking a live provider.

The plan distinguishes direct resources, exact canonical track lists, service-neutral entity lookups, unresolved canonical-recording lookup, unavailable content, and deliberately unplayable diagnostics. It carries the disc's playback policy unchanged.

Exact canonical resolution remains the resolver's job; provider authentication, remote search, playlist materialization, caching, and actual playback remain provider-plugin responsibilities.

## Consequences

- Provider plugins get one stable semantic input contract.
- Private/local and public discs can share host-side playback orchestration.
- Partial and ambiguous provider coverage cannot be hidden by plugin-specific guessing.
- Artist/album support can exist before every provider binding is precomputed.
- The planner is entirely testable offline and does not require provider credentials.

## Follow-up: self-contained canonical lookup

Draft 0.2 later tightened this decision: a `recording_resolution` plan embeds the exact ordered MBID/ISRC identity rows required for provider resolution, plus only the selected provider's explicit overrides. Provider plugins must not reach back into catalog source files to discover what a plan meant. This preserves the playback plan as the complete semantic handoff and is recorded separately in ADR 0016.
