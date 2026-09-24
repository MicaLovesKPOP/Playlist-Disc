# Roadmap

## Milestone 1 — physical format draft

- normative draft specification;
- reference Python library and CLI;
- deterministic TOC encoder/decoder;
- Damm validation;
- cdrdao bundle generator plus real-tool `toc-info`/`toc-size` parser preflight in CI;
- experimental audio beacon;
- fail-open runtime recognition aggregator for strong TOC/CD-TEXT/beacon evidence implemented in Draft 0.2;
- catalog schema and development vectors;
- CI validation.

## Milestone 2 — physical validation and PDv1.0

- deterministic Draft 0.2 physical-test kit, optional CD-TEXT A/B mastering, virtual verification, and test-namespace burn guard implemented; burn development discs on multiple writers;
- structured compatibility profile/report schema, exact mastering-bundle fingerprints, validator, deterministic export, and three planned reference profiles implemented in Draft 0.2;
- test reference cars and additional legacy players;
- settle TOC tolerance rules;
- settle audio-beacon profile;
- settle CD-R/CD-RW compatibility language;
- freeze PDv1.0 and open permanent public IDs.

## Milestone 3 — public library UX

- searchable static catalog — deterministic JSON snapshot, CLI search, and dependency-free static HTML browser implemented in Draft 0.2; hosted deployment remains optional future work;
- pack/wallet support — Draft 0.2 source schema, validation, 12/24/48/96 capacity metadata, ordered slot resolution, and CLI inspection implemented; print/layout UX remains future work;
- private/local disc creation — software allocation, validation, listing, and virtual-build lookup implemented in Draft 0.2;
- contribution workflow and generated catalog snapshots — schema/cross-file validation, deterministic exports, protected-ID evolution guard, PR checklist, and structured issue forms implemented in Draft 0.2;
- Python wheel/sdist packaging plus Ubuntu/Windows/macOS install smoke tests implemented in Draft 0.2; standalone binaries/desktop application remain future work.

## Milestone 4 — playback bridge

- transport-neutral logical message protocol, packaged JSON Schema, reference transcript, and semantic validator implemented in Draft 0.2, including capability contracts, reconnect-safe selection counters, counter/identity-consistent state sync, and explicit acknowledgement targets;
- offline host-runtime state machine and replay harness implemented in Draft 0.2, covering reconnect deduplication, live per-session sequence/capability/counter guards, stale-session isolation, source requests, playback-plan execution, controls, and removal policy;
- Draft 0.1 BLE GATT transport profile and fully software-tested fragmentation/reassembly framing implemented in Draft 0.2; real mobile/adapter interoperability and link-security behavior remain hardware-gated;
- deterministic canonical-recording resolution core and provider/local index contract implemented in Draft 0.2;
- normalized provider-neutral playback-plan compiler implemented in Draft 0.2 across canonical manifests, artist/album entities, federated/provider-native resources, diagnostics, and private mappings; unresolved canonical plans now embed their exact recording identities so provider plugins need no side-channel manifest access;
- live provider plugins (Spotify/Apple/etc. authentication/catalog lookup/materialization);
- optional tagged local-library scanner/index implementation using the same exact MBID/ISRC resolution contract implemented in Draft 0.2;
- deterministic local materialization-cache contract for exact `track_list` plans implemented in Draft 0.2; live provider-created playlist refresh/materialization remains plugin work.

## Milestone 5 — OEM vehicle integrations

- Alfa 147 / 937 pre-hardware research — sourced CAN/changer/control groundwork implemented; exact bus/changer protocol remains capture-gated;
- MINI R55 Boost CD/RAD2 pre-hardware research — sourced K-CAN/MOST/gateway/changer/control groundwork implemented; exact bus/MOST behavior remains capture-gated;
- Citroen C3 II / PSA RD4-family pre-hardware research — sourced C3 UI, RD4 Comfort-CAN/display/changer architecture, and related AEE2004 CAN groundwork implemented; exact target-car frames remain capture-gated;
- family-first compatibility breadth plan established in `docs/COMPATIBILITY-COVERAGE.md`: research reusable head-unit/interface families rather than enumerating every car, with P1 coverage for major VAG, BMW/MINI legacy, PSA expansion, Fiat/Alfa/Lancia, Renault, Ford Europe, Opel/Vauxhall, Toyota/Lexus, Honda/Acura, Mazda, and aftermarket-head-unit lanes;
- VAG legacy/Quadlock family research implemented: direct-CDC Gamma generations, CAN-connected RCD 300 with a separate CDC bus/audio path, later RCD/BAP/MDI boundaries, Audi copper subfamily separation, Skoda pinout caveats, and Audi MMI kept as a distinct optical lane; exact protocols remain capture-gated;
- before declaring pre-hardware compatibility breadth complete, either source or explicitly defer every P1 lane and characterize at least one reusable direct-CDC, vehicle-network-mediated, optical, and aftermarket integration class;
- OEM controls and now-playing metadata where technically feasible.
