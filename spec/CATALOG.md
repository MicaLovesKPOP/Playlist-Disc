# Public catalog model

The public catalog is a registry of **meanings**, not a pile of streaming URLs.

A physical Playlist Disc identifies a stable semantic record. Providers, URLs, market availability, cached playlists, and pack membership are realization or curation details layered on top.

## Categories are facets, not ID ranges

The same entry can be community-maintained, living, canonical, K-pop, shuffled, and available on several providers at once. These properties are stored independently.

Numeric IDs do **not** encode category, provider, genre, ownership, curation authority, lifecycle, or pack membership.

## Definition types

Draft 0.2 recognizes these catalog definition types:

- `artist_catalog` — a service-neutral artist identity, anchored by a MusicBrainz artist MBID;
- `album` — a service-neutral release-group identity, anchored by a MusicBrainz release-group MBID;
- `canonical_manifest` — an explicit list of service-neutral recordings;
- `federated_collection` — a concept deliberately realized by different provider editorial collections;
- `provider_native` — a resource that intentionally belongs to one provider;
- `diagnostic` — development/test namespace entries.

A schema-valid record can still be semantically invalid. `pdv1 validate-catalog` therefore enforces cross-file and cross-field invariants in addition to JSON Schema.

## Portability classes

### Canonical

Canonical means the record has provider-independent meaning.

Artist and album entities can be canonical directly. Curated track sets use a canonical recording manifest. A canonical entry must not simply wrap a provider-native URL while claiming universality.

### Federated

Federated means the *concept* is shared but individual services are permitted to realize it differently.

Example: "current mainstream pop hits" could deliberately bind to each service's own current editorial list. A federated entry requires at least two provider bindings, and those bindings are marked `equivalent` or `best_available` rather than `direct`.

### Provider-native

Provider-native means the resource itself is part of one provider.

A provider-native record declares the provider and requires a matching `direct` binding. Unsupported services remain unsupported; the registry must not manufacture fake equivalence.

## Canonical recording manifests

A canonical manifest is JSON at the deterministic path:

```text
catalog/manifests/042/042381.json
```

for disc ID `042381`.

The catalog entry points to that path. The manifest repeats the disc ID and contains one or more recording records. Every JSON file below `catalog/manifests/` must belong to a matching `canonical_manifest` catalog entry; orphaned, misplaced, or malformed manifest files invalidate the catalog rather than being silently ignored.

Each recording must contain at least one service-neutral identifier:

- a MusicBrainz Recording MBID; and/or
- one or more uppercase ISRCs.

Optional human `title_hint` and `artist_hint` fields exist for review/debugging only. They are not identity.

Provider-specific exact-track overrides may be stored when automated resolution would otherwise be ambiguous. They are realization hints, not canonical identity.

Within one manifest, the same MBID or ISRC cannot identify two different recording rows. Ambiguous manifests are rejected by validation.

## Provider/local resolution

Canonical manifest membership is service-neutral. Provider and local-library adapters resolve each recording using explicit provider overrides or exact MusicBrainz Recording MBIDs / ISRCs. Title and artist hints are not identity and must not be used for fuzzy automatic substitution.

If exact identifiers produce contradictory candidate sets, the result is ambiguous. If multiple provider resources represent the same recording, an adapter/index may designate exactly one preferred resource; otherwise ambiguity remains visible. Missing recordings remain missing and reduce provider coverage rather than changing the canonical collection.

The Draft 0.2 reference `provider-index` format exists as an offline/testing interchange and can also represent local-library URIs. Live provider plugins may construct equivalent indexes in memory.

## Packs and wallet order

Packs are curated ordered views over existing catalog IDs. They do not allocate IDs and do not alter disc meaning. Pack YAML is discovered recursively for validation, so files placed outside the deterministic `catalog/packs/<slug>.yaml` location are rejected instead of escaping validation.

Source packs live at:

```text
catalog/packs/<slug>.yaml
```

Draft 0.2 supports declared wallet capacities of 12, 24, 48, and 96. A pack may be partially filled. Its ordered ID list maps directly to 1-based wallet slots in generated library data.

Validation rejects missing references, duplicate IDs, wrong paths, and membership larger than capacity. Updating a pack is a curation change, not a change to any referenced physical identity.

## Catalog file layout is normative

A catalog entry must live at:

```text
catalog/discs/<first three ID digits>/<six-digit ID>.yaml
```

A canonical manifest must live at:

```text
catalog/manifests/<first three ID digits>/<six-digit ID>.json
```

This makes IDs reviewable, prevents accidental duplicate locations, and keeps large registries reasonably sharded.

## Living and snapshot collections

A `snapshot` entry has membership intended to stabilize apart from corrections.

A `living` entry can gain newly qualifying music without changing semantic meaning—for example an artist's complete catalog or an ongoing genre collection.

Living does not mean "anything maintainers feel like adding." The semantic scope must remain stable enough that an old physical disc still means the same thing years later.

## Evolution after activation

A public proposal is freely editable while its status is `draft`. Once a permanent public ID becomes `active`, physical copies may exist and the semantic core becomes protected.

The evolution guard locks the canonical title/short title, definition, lifecycle, portability class, and default playback behavior. Active entries may only remain active or become retired; retired entries cannot be reactivated or deleted.

For `snapshot` canonical manifests, the service-neutral recording membership is protected. Human title/artist hints and provider-specific resolution overrides may still be corrected because they are not canonical identity. Shuffle manifests ignore row order for this comparison; ordered manifests treat sequence as semantic.

For `living` canonical manifests, membership may evolve, but the definition and membership policy remain locked. Human review is still required to ensure additions remain within that declared scope.

A provider-native entry additionally locks its native provider resource and market because those fields are part of what that physical disc means. Provider bindings for canonical/federated content remain realization details and may evolve.

Packs, tags, maintainers, notes, non-native provider bindings, and successors are not physical identity. They can evolve subject to ordinary catalog validation.

During PDv1 Draft 0.2, permanent public activation is deliberately closed; public IDs can only remain `draft`. The evolution machinery is tested now so it is already in place before PDv1.0 opens the permanent namespace.

## Successors and retirement

Public IDs are never recycled.

Only a retired entry may name a `successor`, and:

- it cannot point to itself;
- the successor must exist in the catalog;
- successor chains must be acyclic;
- retirement does not change the old entry's historical meaning.

## Export behavior

`pdv1 export-catalog` refuses to emit a generated snapshot if the source catalog is invalid.

For canonical-manifest entries, generated export metadata includes:

- SHA-256 of the manifest bytes;
- recording count.

`pdv1 export-library` adds validated packs, resolved wallet slots, and browsing facets on top of the catalog-entry snapshot. Generated export data is a client artifact rather than a second source of truth.

This allows clients and mirrors to detect changed living manifests and consume pack curation without treating provider URLs or wallet membership as physical-disc identity.

## Examples

### Artist catalog

A disc can mean "play aespa's catalog." Provider plugins resolve the stable artist identity to the user's selected service or local library.

### Canonical community collection

A community collection such as "K-Pop Girl Group Singles" can be an explicit service-neutral recording manifest. Spotify, Apple Music, local-library, and future-provider support all resolve from the same membership list.

### Federated editorial concept

"Current Global Pop Hits" may intentionally map to each service's own editorial equivalent. Those lists do not need to contain identical tracks because the catalog explicitly labels the record as federated.

### Provider-native record

A specific provider editorial playlist can still have a physical Playlist Disc, but its catalog page and machine metadata must state that it is provider-native.
