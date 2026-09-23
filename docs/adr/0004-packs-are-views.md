# ADR 0004: Packs are ordered views, not identities

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

Users may want starter sets, genre collections, test sets, or a list arranged to match pockets in a physical CD wallet. It would be tempting to give packs their own physical identity semantics or duplicate disc definitions inside pack files.

That would couple curation to the permanent six-digit namespace and create two places where a disc's meaning could drift.

## Decision

A pack is an ordered list of existing catalog IDs plus descriptive curation metadata.

Packs:

- do not allocate Playlist Disc IDs;
- do not redefine referenced entries;
- use list order as 1-based wallet-slot order;
- reject duplicate IDs and missing references;
- may contain fewer discs than their declared 12/24/48/96 capacity;
- may change or retire independently of the immutable meaning of referenced public IDs.

Generated static-library snapshots may denormalize title and machine-ID data into resolved slots for convenient clients, but source pack files contain only the referenced IDs.

## Consequences

The same disc can appear in many packs without identity duplication. Wallet organization can evolve without reburning discs. Static clients can resolve a self-contained view after validation, while the source catalog remains authoritative.

Physical wallet artwork, label templates, and ergonomic claims remain future UX work rather than part of the Draft 0.2 physical format.
