# ADR 0007: Cross-service resolution never uses fuzzy title matching

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

The same song title can refer to studio, live, remix, rerecorded, translated, clean/explicit, or entirely unrelated recordings. Artist/title text also varies by provider and locale.

A universal physical disc must not silently trade semantic correctness for a higher match percentage.

## Decision

Canonical manifest rows resolve through explicit provider overrides or service-neutral recording identifiers (MusicBrainz Recording MBIDs and ISRCs).

If exact identifiers produce conflicting or multiple provider candidates, resolution reports ambiguity. A provider index may mark one duplicate representation as `preferred`, but fuzzy title/artist matching is not part of the canonical resolver.

Unavailable or unresolved recordings remain missing rather than being substituted.

## Consequences

- Cross-service playback may have less than 100% coverage in some markets.
- Users can see honest missing/ambiguous counts.
- Provider plugins can add carefully reviewed overrides for hard cases.
- Human title/artist fields remain useful for review and UI without becoming identity.
- Local-library resolvers can participate using the same MBID/ISRC contract.
