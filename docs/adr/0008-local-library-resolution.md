# ADR 0008: Local libraries use the same exact-identifier resolver

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

A provider-neutral Playlist Disc should not need a separate semantic model for local files. Local libraries also contain duplicate releases, live/remix variants, retagged files, and incomplete metadata.

Automatically matching artist/title strings would recreate the same ambiguity rejected for streaming providers.

## Decision

The optional local-library scanner emits the standard provider-index contract with `provider=local` and `file://` resources.

Only files carrying a MusicBrainz Recording MBID and/or ISRC are indexed. Files with no service-neutral identifier are skipped rather than fuzzy matched.

Duplicate local representations remain multiple candidates. The resolver requires explicit preference rather than guessing a format/master.

## Consequences

- Local and streaming resolution share one tested algorithm.
- Correctly tagged personal libraries can participate without any network account.
- Untagged collections need metadata enrichment before automatic canonical resolution.
- Local index files contain private filesystem paths and should not be committed publicly.
- Audio tag parsing is an optional dependency; core PDv1 tooling remains lightweight.
