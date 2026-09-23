# Roadmap

## Milestone 1 — physical format draft

- normative draft specification;
- reference Python library and CLI;
- deterministic TOC encoder/decoder;
- Damm validation;
- cdrdao bundle generator;
- experimental audio beacon;
- catalog schema and development vectors;
- CI validation.

## Milestone 2 — physical validation and PDv1.0

- burn development discs on multiple writers;
- structured compatibility profile/report schema, validator, deterministic export, and three planned reference profiles implemented in Draft 0.2;
- test reference cars and additional legacy players;
- settle TOC tolerance rules;
- settle audio-beacon profile;
- settle CD-R/CD-RW compatibility language;
- freeze PDv1.0 and open permanent public IDs.

## Milestone 3 — public library UX

- searchable static catalog — deterministic JSON snapshot, CLI search, and dependency-free static HTML browser implemented in Draft 0.2; hosted deployment remains optional future work;
- pack/wallet support — Draft 0.2 source schema, validation, 12/24/48/96 capacity metadata, ordered slot resolution, and CLI inspection implemented; print/layout UX remains future work;
- private/local disc creation — software allocation, validation, listing, and virtual-build lookup implemented in Draft 0.2;
- contribution workflow and generated catalog snapshots — schema/cross-file validation, deterministic exports, and protected-ID evolution guard implemented in Draft 0.2; review/issue templates remain future work;
- friendly desktop application.

## Milestone 4 — playback bridge

- transport-neutral logical message protocol, packaged JSON Schema, reference transcript, and validator implemented in Draft 0.2;
- BLE or equivalent transport profile;
- provider plugins;
- local-library resolver;
- cached/materialized cross-service collections.

## Milestone 5 — OEM vehicle integrations

- Alfa 937 family research;
- MINI Boost CD/RAD2 research;
- PSA RD4 family research;
- OEM controls and now-playing metadata where technically feasible.
