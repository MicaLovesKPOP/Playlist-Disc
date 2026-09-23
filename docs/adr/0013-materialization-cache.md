# ADR 0013: Materialization caches are keyed by exact playback plans

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

Canonical collections may need to be materialized as provider playlists. Recreating them on every disc insertion is unnecessary, but reusing a stale provider playlist after canonical membership or resolution changes would violate the physical disc's current declared meaning.

Artist/entity lookups also have different freshness semantics from explicit resolved track lists.

## Decision

The generic cache supports only deterministic ready/partial `track_list` playback plans.

The entire normalized playback plan is SHA-256 fingerprinted. A cache record additionally binds provider, disc identity, source count, and a hashed local account/profile scope to the materialized provider resource.

Any playback-plan change makes the old record stale. Direct resources bypass materialization. Entity lookups and unresolved recording lookups remain provider-plugin responsibilities because they need provider-specific refresh semantics.

Cache files never contain provider credentials.

## Consequences

- Living collections automatically invalidate provider playlists when their compiled track list changes.
- Provider/account caches cannot accidentally bleed across configured local scopes.
- Partial materializations are possible but cannot masquerade as later complete plans.
- Provider plugins can reuse a simple local cache without controlling canonical semantics.
- Artist catalogs still need explicit provider freshness/refresh behavior rather than an unsafe forever-cache.
