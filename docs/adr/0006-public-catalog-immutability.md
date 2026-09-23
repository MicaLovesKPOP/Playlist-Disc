# ADR 0006: Activated public identities are historically immutable

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

A Playlist Disc is physical media. After a public ID is activated, copies may exist outside the repository and may be used years later without consulting Git history.

Schema validation alone only describes whether the current catalog is valid. It cannot detect that a previously active ID has been deleted, repurposed, or had its musical definition changed.

At the same time, service URLs, metadata hints, maintainers, tags, and living-collection membership legitimately need to evolve.

## Decision

Public records remain freely editable while `draft`. Once a public record has been `active`, historical comparison protects its semantic core permanently.

Locked fields are title, short title, definition, lifecycle, portability, and playback defaults. Active may transition to retired; retired cannot be reactivated or deleted.

Snapshot canonical manifests additionally lock service-neutral recording membership. Resolution hints and provider overrides are excluded from that membership fingerprint. Ordered collections preserve sequence; shuffled collections do not.

Living manifests may change membership while their immutable definition/membership policy remains the stable semantic contract.

Provider-native records lock their native direct resource/market. Non-native or service-resolution bindings remain mutable.

CI compares the proposed catalog with the target-branch baseline. No generic bypass file is provided: if a protected snapshot's canonical meaning is actually wrong, the conservative remedy is a successor/new ID.

Permanent public activation stays disabled until the physical PDv1 format is frozen.

## Consequences

- Existing physical discs cannot be silently repurposed by a valid-looking catalog edit.
- Provider/API churn remains maintainable for canonical/federated content.
- Living collections can actually remain living.
- True semantic corrections to an activated snapshot are intentionally expensive and visible: retire/succeed rather than rewrite history.
- CI needs Git history/base checkout in addition to ordinary source validation.
