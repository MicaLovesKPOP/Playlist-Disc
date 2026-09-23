# ADR 0002: Canonical track collections use recording manifests

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

Curated collections such as "K-Pop Girl Group Singles" need a definition that is portable across services.

Artist/title text alone is ambiguous. Provider track IDs are not portable. Album/release identity is often too specific because the same recording can appear on several releases.

## Decision

Explicit canonical track collections use a JSON manifest whose rows identify **recordings**, not provider tracks.

Each row contains at least one of:

- MusicBrainz Recording MBID;
- ISRC.

Human title/artist fields are optional review hints only.

The same MBID or ISRC may not occur in multiple rows of one manifest because that makes provider resolution ambiguous.

Provider-specific exact-track overrides are permitted as resolution hints but do not alter canonical membership.

Manifest location is deterministic from the disc ID and the manifest repeats that ID.

## Consequences

- Cross-service materialization has a durable source of truth.
- Resolver implementations can prefer MBID relationships, ISRC matching, or explicit provider overrides.
- Regional catalog gaps can be reported honestly rather than silently changing the canonical collection.
- Living collections can update membership while preserving their semantic scope.
- The registry can hash manifests in generated catalog snapshots for cache invalidation and mirroring.
