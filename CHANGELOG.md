# Changelog

## 0.2.0a1 — Draft 0.2 pre-hardware development

### Installability and contribution workflow

- Added source/pipx installation and packaging documentation while keeping `cdrdao` explicitly optional until physical burning.
- Added wheel/sdist build checks and installed-wheel smoke tests on Ubuntu, Windows, and macOS, including packaged schema loading.
- Added package project URLs, keywords, and a `release` dependency extra for reproducible artifact checks.
- Added structured GitHub issue forms for compatibility evidence, catalog proposals, and bugs plus a pull-request safety/review checklist.

### External mastering-tool preflight

- Added `pdv1 cdrdao-preflight`, which first verifies a bundle internally and then asks the installed cdrdao reference tool to parse (`toc-info`) and size (`toc-size`) its TOC without optical hardware.
- Added unit coverage for missing tools/parser failures and a Linux CI gate that installs cdrdao and checks every generated Draft 0.2 test-kit variant.
- Kept this evidence explicitly separate from real writer/media compatibility: parser acceptance is not a physical burn result.

### Physical-test-kit preparation

- Made CD-TEXT an explicitly optional mastering channel while preserving identical PDv1 TOC identity/timing.
- Hardened virtual verification so declared CD-TEXT presence/absence must match the mastering file and remaining identity channels still agree.
- Added a deterministic four-variant Draft 0.2 physical compatibility kit, including a same-ID CD-TEXT on/off A/B pair and a beacon-focused no-CD-TEXT variant.
- Added `pdv1 build-test-kit` / `verify-test-kit` and `pdv1 build --no-cdtext`.
- Restricted the official Draft 0.2 `pdv1 burn` path to verified test-namespace bundles so unfinished public/private physical identities cannot be minted accidentally.

### Runtime recognition

- Added a packaged `PDv1-recognition` result and runtime aggregator for independently strong TOC, CD-TEXT, and repeated-beacon evidence.
- One valid strong channel can recognize a disc; matching channels corroborate it; independently valid disagreement returns `conflict` and no identity rather than applying a hidden precedence rule.
- Invalid/missing optional channels remain diagnostics and do not suppress a different valid channel; coarse track-count/total-duration evidence is never treated as identity.
- Tightened CD-TEXT identifier token boundaries to avoid matching valid IDs as prefixes embedded inside longer values.
- Added `pdv1 recognize`, schema/package checks, tests, documentation, and ADR 0014.

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

### Physical evidence provenance

- Added a deterministic SHA-256 fingerprint over each exact three-file mastering bundle (`manifest.json`, `disc.toc`, `beacon.wav`) with unambiguous filename/length framing.
- `pdv1 verify-build` now prints the exact bundle fingerprint; generated test-kit manifests pin a fingerprint for every variant and verification detects artifact drift.
- Structured physical compatibility reports now require `bundle_sha256` and may record a test-kit variant name, preventing results from becoming detached from the exact draft artifact that was burned.
- Added regression tests proving identical bundles fingerprint identically and even harmless byte-level mastering drift changes the fingerprint.

### Compatibility-test preparation

- Replaced loose vehicle notes with schema-validated head-unit compatibility profiles.
- Added structured physical-test reports for media/finalization/CD-TEXT state, writer details, repeated attempts, load/track behavior, TOC timing, cold-start/reinsert behavior, vehicle-bus visibility, and beacon outcomes.
- Added Draft 0.2 safeguards requiring physical reports to use test-namespace PD IDs and preventing impossible attempt counts/status combinations.
- Migrated the Alfa 147 ALFA-937 SW3.17, MINI R55 Boost CD, and Citroen C3 RD4 reference profiles while keeping them honestly marked `planned`.
- Added deterministic compatibility JSON export plus `pdv1 validate-compatibility` / `export-compatibility` and CI coverage.
- Added schema-validated, source-typed pre-hardware research evidence that remains distinct from physical reports, plus an eight-item Alfa 147 / ALFA-937 SW3.17 research set covering documented CAN participation, changer support, commercial changer-emulator evidence, and the community-reported SW3.17 AUX boundary.
- Added a sourced MINI R55 Boost CD / RAD2 research set covering option-6FC/RAD2 identification, MOST/K-CAN gateway architecture, native CD/MP3/WMA support, optical MOST changer integration, factory steering-wheel controls/display targets, and the distinction between OBD diagnostics and direct MOST access.
- Added a sourced Citroen C3 II / RD4-family research set covering factory steering/media display surfaces, RD4 CD-TEXT/MP3 levels, Comfort CAN radio/display/changer architecture, AEE2004/2007 family compatibility evidence, and related-platform reverse-engineered CD text/tray/disc/timing/source/changer frame classes while explicitly keeping the target C3's exact IDs capture-gated.
- Added a `manufacturer_documentation_mirror` research source type so mirrored owner documentation is not mislabeled as a direct manufacturer-hosted source.

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

### Local-library resolution

- Added an optional Mutagen-backed scanner for local audio tagged with MusicBrainz Recording MBIDs and/or ISRCs.
- The scanner emits the standard `provider=local` index with private `file://` resources, skips unidentified files, records unreadable files, and never fuzzy-matches title/artist text.
- Duplicate local representations deliberately remain resolver candidates rather than being arbitrarily ranked by format/path.
- Added `pdv1 scan-local-library`, strict/error-reporting modes, real tagged-WAV integration coverage, documentation, optional dependency packaging, and ADR 0008.

### Playback-plan compiler

- Added a packaged `PDv1-playback-plan` schema and deterministic compiler that turns catalog/private meanings into one provider-facing contract before any live API is involved.
- Canonical manifests compile to ready/partial/ambiguous/unavailable track-list plans using the existing exact MBID/ISRC resolver, or to `requires_lookup` when no provider index is supplied.
- Provider-native and federated records compile to their selected provider resource; artist/album records fall back to service-neutral MusicBrainz entity lookup; diagnostic IDs are explicitly unplayable; private/local bindings use the same plan format.
- Added `pdv1 plan-playback` with JSON output and `--require-ready`, package-schema smoke coverage, tests, documentation, and ADR 0011.

### Cross-service resolution groundwork

- Added a packaged provider/local-library resolution-index schema using exact MusicBrainz Recording MBIDs and ISRCs.
- Added deterministic canonical-manifest resolution with explicit provider overrides, MBID/ISRC intersection, preferred duplicate resources, honest missing coverage, and explicit ambiguity on conflicting identifiers.
- Human title/artist hints are deliberately excluded from matching; no fuzzy substitution is performed.
- Added provider-index validation plus `pdv1 resolve-canonical` with machine-readable resolution plans and optional complete-coverage enforcement.
- Added offline fixtures/tests and ADR 0007 documenting the no-fuzzy-resolution rule.

### Deterministic materialization cache

- Added a packaged `PDv1-materialization` record for provider/local playlists generated from deterministic track-list playback plans.
- Cache validity is keyed by the complete canonical playback-plan SHA-256, provider, disc identity, resolved source count, and hashed local account/profile scope; plan evolution automatically produces a stale cache miss.
- Added atomic local cache writes plus `pdv1 materialization-put` / `materialization-check` commands and package/CI coverage.
- Restricted the generic cache to ready/partial `track_list` plans; direct resources do not need materialization and unresolved entity/provider lookups require provider-specific freshness rules.
- Added privacy/freshness documentation and ADR 0013.

### BLE transport profile

- Added a Draft 0.1 PD Bridge BLE GATT profile with one custom service, reliable adapter→host indications, and host→adapter writes with response.
- Added bounded 4-byte big-endian length-prefixed UTF-8 JSON framing so logical bridge messages are independent of ATT MTU and GATT chunk boundaries.
- Added a library-independent incremental framing codec that validates every decoded logical PD Bridge message and fails closed until reset after invalid length/UTF-8/JSON/schema input.
- Added exhaustive two-chunk split coverage, one-byte fragmentation, concatenated-frame, oversize/corruption/reset tests, a fixed profile vector, documentation, and ADR 0015.
- BLE link encryption is required by the draft profile, while actual pairing UX/security strength and phone/adapter interoperability remain hardware/mobile implementation evidence rather than software claims.

### Offline host orchestration

- Added a packaged `PDv1-host-action` contract and deterministic host-runtime state machine that consumes adapter-side PD Bridge events and emits source/provider actions.
- Reconnect/state-sync repeats of the same selection are deduplicated; new adapter sessions remain new selections.
- Automatic source requests honor advertised adapter capability/state, OEM media controls only forward with an active playback context, and disc-removal stop/source behavior is explicit host policy rather than physical-disc semantics.
- Ready and `requires_lookup` playback plans can execute automatically, partial plans are opt-in, and ambiguous/unavailable/unplayable selections are blocked without guessing.
- Added `pdv1 host-replay`, reference adapter/plan vectors, schema/package checks, tests, documentation, and ADR 0012.

### Playback bridge semantic hardening

- Extended transcript validation from structural sequencing into capability contracts: observed detection methods, media controls, source switching, and now-playing support must match the sender's announced session capabilities.
- Fixed selection-counter semantics so counters stay strictly monotonic across remove/reinsert cycles and state-sync cannot regress them.
- Repeated `hello` / `hello_ack` announcements may support reconnects but cannot silently mutate identity/capabilities within one sender session.
- Made acknowledgements reconnect-safe by requiring both peer `ack_session` and `ack_seq`; optional error references now use the same session+sequence pairing.
- Added display-capability self-consistency checks, expanded bridge tests, and ADR 0009.

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
