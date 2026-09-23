# ADR 0001: Public IDs identify musical meaning, not providers

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

A physical Playlist Disc may outlive phones, streaming subscriptions, APIs, provider catalog IDs, and even entire streaming companies.

Allocating separate Spotify, Apple Music, or other provider number ranges would permanently bake today's services into physical media. It would also require multiple physical discs for the same musical concept and make migration difficult.

At the same time, not every collection is truly provider-independent. Provider editorial playlists can differ intentionally, and a user may explicitly want a particular provider-native resource.

## Decision

The six-digit PD identity namespace carries no provider meaning.

Public catalog records declare one of three portability modes:

1. **canonical** — provider-independent identity or explicit recording membership;
2. **federated** — a shared concept intentionally realized differently on multiple providers;
3. **provider_native** — a resource that intentionally belongs to one provider.

Canonical explicit track sets use service-neutral recording identifiers in a manifest. Provider-specific IDs are resolution data or overrides, not physical identity.

## Consequences

- One physical CD can remain useful when the user changes services.
- A future provider can add support without reburning public discs.
- Provider-native playlists remain possible without being mislabeled universal.
- Registry validation must enforce consistency between definition type, portability, and provider bindings.
- Public clients need a resolver layer rather than treating the catalog as a collection of URLs.
