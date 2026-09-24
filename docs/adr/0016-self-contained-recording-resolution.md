# ADR 0016: Recording-resolution plans are self-contained

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

A canonical manifest can be compiled before a provider index exists. Earlier Draft 0.2 playback plans represented this as `recording_resolution` but carried only `recording_count`.

That was sufficient to describe *why* the plan was unresolved but insufficient for a provider plugin to actually resolve it. A live plugin would have needed an undocumented side channel back into the public catalog/manifest files.

That undermines the playback-plan boundary and would make mobile/provider implementations depend on repository storage details.

## Decision

A `recording_resolution` playback plan must contain the complete ordered service-neutral recording identity needed for exact provider resolution.

Each lookup row carries:

- MusicBrainz Recording MBID and/or ISRC;
- the exact selected-provider override when one exists.

Title/artist hints are deliberately omitted because they are not identity and must not become an accidental fuzzy fallback.

The plan repeats `recording_count` for readable diagnostics, and validation requires it to equal the row count. Duplicate MBIDs/ISRCs across rows are rejected.

Provider-specific overrides for **other** services are not copied into a selected-provider plan.

## Consequences

- A provider plugin can resolve the plan using only the plan plus its own provider API/index.
- Phone applications do not need direct catalog filesystem/repository access at runtime.
- The plan remains portable across implementation languages.
- Ordered canonical membership survives the handoff; shuffle remains playback policy rather than plan mutation.
- Exact provider overrides remain available without leaking irrelevant provider bindings.
- Fuzzy title/artist resolution remains outside the canonical path.
