# Changelog

## 0.2.0a1 — Draft 0.2 pre-hardware development

### Physical-format software validation

- Added an exhaustive 1,000,000-ID encode/decode audit with a golden physical-mapping digest.
- Established actual checksum-valid program-duration extrema (97–341 seconds).
- Added a pure-Python Goertzel DTMF decoder for the experimental repeated beacon.
- Added synthetic attenuation, noise, clipping, filtering, redundancy, and silence tests.
- Added `pdv1 verify-build` to independently cross-check manifest, TOC, CD-TEXT, and audio-beacon identity.
- Centralized Draft 0.2 build metadata and hardened virtual verification against stale draft labels, namespace/checksum/total-duration mismatches, duration-vector drift, TOC-signature drift, and the wrong beacon profile.
- CI verifies generated bundles on Python 3.11–3.13 and runs the exhaustive encoding audit separately.
- Added a pre-hardware validation document separating software evidence from claims that still require physical testing.

### Catalog hardening

- Added a schema for service-neutral canonical recording manifests using MusicBrainz Recording MBIDs and/or ISRCs.
- Replaced permissive definition objects with typed artist, album, manifest, federated, provider-native, and diagnostic definitions.
- Added whole-catalog semantic validation for deterministic file paths, portability/definition consistency, provider binding rules, successor integrity, manifest identity, and duplicate canonical recording identifiers.
- Catalog export now refuses invalid source data and includes canonical-manifest content hashes/counts.
- Added architecture decisions documenting provider-neutral public IDs and canonical recording manifests.

### Catalog evolution safety

- Added a baseline/current catalog evolution guard for activated and retired permanent public IDs.
- Locked canonical title, short title, definition, lifecycle, portability, and default playback semantics after activation.
- Snapshot canonical manifests now protect service-neutral recording membership while still allowing hint/provider-override corrections; living manifests may evolve within their immutable membership policy.
- Provider-native direct resource/market identity is protected after activation, while ordinary provider resolution bindings remain mutable.
- Draft public proposals remain editable/deletable; active/retired public entries cannot yet be created while PDv1 remains a physical-format draft.
- CI compares pull requests and main pushes with their baseline commit so protected physical meanings cannot drift silently.
- Tightened successor, provider-native resource, and federated-resource validation; added ADR 0006 and catalog-evolution documentation.

### Local/private workflow

- Added a user-owned private registry for IDs `900000-989999` with deterministic sharding and local-only provider/resource bindings.
- Added lowest-free-ID allocation with optional explicit private IDs and exclusive, non-overwriting file creation.
- Added `pdv1 local-create`, `pdv1 local-validate`, and `pdv1 local-list` commands.
- `pdv1 build --local-library` can resolve private title/CD-TEXT metadata before virtual bundle verification.
- Added validation/tests for namespace isolation, deterministic paths, allocation collisions, binding syntax, CLI round-trips, and private virtual builds.
- Added ADR 0003 documenting the privacy boundary, lack of central private allocation, multi-device collision behavior, and non-recycling guidance.

### Library, packs, and search

- Added a Draft 0.2 pack schema for ordered 12/24/48/96-capacity wallet views over existing catalog IDs.
- Whole-catalog validation now checks pack paths, duplicate slots, capacity limits, and missing catalog references.
- Added a development test-vector pack to exercise pack validation and slot resolution without opening permanent public IDs.
- Added deterministic catalog search with status/tag filters plus `pdv1 search-catalog`.
- Added `pdv1 pack-list` and `pdv1 pack-show` with resolved 1-based wallet slots.
- Added `pdv1 export-library`, a validated static JSON snapshot containing entries, resolved packs, and browsing facets.
- Added ADR 0004 documenting that packs are mutable curation views rather than physical identities.
- Added a deterministic, dependency-free static HTML library generator with client-side search/filtering, individual disc pages, pack/wallet pages, machine-readable JSON, and internal-link verification.

### Playback bridge groundwork

- Replaced the bridge sketch with a versioned transport-neutral logical protocol.
- Added a packaged JSON Schema covering capability negotiation, state sync, disc selection/removal, OEM media controls, source switching, playback state, now-playing metadata, acknowledgements, and errors.
- Added transcript validation for PD machine-ID checksums, per-session sequence monotonicity, and adapter selection/removal counters.
- Added a deterministic reference JSONL session plus CLI/CI validation.
- Added ADR 0005 documenting the separation between logical bridge semantics and BLE/USB/vehicle-specific transport layers.

## 0.1.0a1 — initial draft

- PDv1 Draft 0.1 physical-format proposal.
- Six-digit identity plus Damm check digit.
- Deterministic eight-track TOC encoding with four-second digit spacing.
- Experimental repeated DTMF audio beacon.
- Optional conservative ASCII CD-TEXT.
- cdrdao bundle generator.
- Public/private/reserved/test namespace draft.
- Public catalog schema with portability, provenance, lifecycle, and playback axes.
- Three development catalog vectors and initial vehicle compatibility placeholders.
