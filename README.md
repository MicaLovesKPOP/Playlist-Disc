# Playlist Disc

**Playlist Disc (PDv1)** is an experimental open physical format that turns an ordinary audio CD into a provider-neutral playlist token for older cars.

Insert one physical disc and a compatible vehicle/phone integration can interpret it as an intent such as an artist catalog, a genre/year collection, a community-curated collection, a provider-relative editorial collection, or a private personal playlist.

The same disc is intended to work across different cars and playback services. The disc itself does not contain Spotify, Apple Music, vehicle, or phone-specific identifiers.

> [!WARNING]
> PDv1 is currently **Draft 0.2**. Only IDs `999900-999999` are for physical experiments. Do not mint permanent public music discs until PDv1.0 is frozen after real-world compatibility testing.

## Redundant physical identity

A Playlist Disc carries the same logical identity through:

1. a deterministic eight-track table of contents;
2. an optional conservative CD-TEXT machine ID;
3. an experimental repeated DTMF audio beacon;
4. a human-readable printed ID.

The integration uses the strongest channel available in a particular car. Ambiguous recognition must fail open and leave the disc behaving like an ordinary audio CD.

## Quick start

```bash
python -m pip install -e '.[dev]'

pdv1 inspect 999901
pdv1 audit-encoding
pdv1 build 999901 --output build/PD1-999901
pdv1 verify-build build/PD1-999901
pdv1 validate-catalog catalog
pdv1 search-catalog diagnostic --catalog catalog
pdv1 pack-list catalog
pdv1 pack-show draft-0-2-test-vectors --catalog catalog
pdv1 export-library catalog --output build/library.json
pdv1 build-site catalog --output build/site
pdv1 verify-site build/site
pdv1 bridge-validate tests/vectors/bridge-session.jsonl
pytest
```

Draft 0.2's exhaustive audit checks all **1,000,000** six-digit identities and pins the complete physical mapping to a golden SHA-256 digest. The generated bundle verifier independently reconstructs identity from the manifest, TOC, CD-TEXT, and decoded repeated beacon before any blank media is used.

Example:

```text
PD1-123456-3
namespace: public
check digit: 3
tracks: 0:09, 0:16, 0:20, 0:24, 0:28, 0:32, 0:36, 0:24
total: 3:09
```

## Library, search, packs, and wallets

The validated public/test catalog can be searched locally and exported as deterministic static JSON. Packs are ordered views of existing disc IDs and resolve to explicit 1-based wallet slots; they never redefine disc identity.

`pdv1 export-library` produces a provider-neutral payload suitable for a future static website, offline browser, mirror, or desktop client without adding accounts, telemetry, or a hosted search dependency. See `docs/LIBRARY.md` and `catalog/packs/README.md`.

Draft 0.2 can also generate a dependency-free static HTML library with `pdv1 build-site`. It includes searchable/filterable disc cards, individual disc pages, pack/wallet pages, and the machine-readable `library.json`; `pdv1 verify-site` checks required files and all internal links. See `docs/STATIC-SITE.md`.

## Local/private workflow

Private IDs `900000-989999` can be allocated and mapped entirely in a user-owned local registry, with no account or central registration:

```bash
pdv1 local-create ~/.playlistdisc \
  --title "Personal favourites" \
  --short-title "FAVOURITES" \
  --binding local=library:playlist:favourites

pdv1 local-validate ~/.playlistdisc
pdv1 local-list ~/.playlistdisc

pdv1 build 900000 \
  --local-library ~/.playlistdisc \
  --output build/PD1-900000
pdv1 verify-build build/PD1-900000
```

This is a software workflow during Draft 0.2, not permission to burn private IDs yet. See `docs/LOCAL-DISCS.md` for the storage model, privacy boundary, multi-device collision warning, and virtual-build workflow.

## Vehicle/phone bridge

Draft 0.2 now includes a transport-neutral logical PD Bridge Draft 0.1 plus a machine-readable schema and reference JSONL transcript. Vehicle adapters normalize disc selection, OEM media controls, source state, and display capabilities; playback hosts return playback state and now-playing metadata. BLE/USB framing and vehicle wiring remain deliberately separate. See `spec/BRIDGE-PROTOCOL.md`.

## Design principles

- **Cheap and cheerful:** ordinary CD-R is the default; finalized CD-RW is allowed for reusable/test discs.
- **Provider-neutral:** public IDs represent musical intent, not a provider URL, unless explicitly provider-native.
- **Car-neutral:** vehicle integrations translate their own electronics into common disc-selection events.
- **Fail open:** an unrecognized or ambiguous disc behaves as a normal audio CD.
- **Immutable physical meaning:** once PDv1.0 allocates a public ID, it is never recycled or silently repurposed.
- **Private by default when desired:** a local-only namespace requires no account, registration, or telemetry.
- **Packs are views:** wallet organization can evolve without changing or duplicating disc identity.
- **Prove software claims in software:** physical tests should answer only hardware questions that cannot be settled beforehand.

## Repository layout

- `spec/` — physical format, catalog model, future bridge protocol
- `catalog/` — public/test registry, canonical manifests, packs, and schemas
- `compatibility/` — measured legacy-player/vehicle results
- `src/playlistdisc/` — reference library and CLI
- `tests/` — algorithm tests and golden vectors
- `docs/` — burning, validation, compatibility testing, library/local workflows, ADRs, and roadmap

## Planned namespace

| Range | Meaning |
| --- | --- |
| `000000` | invalid / never allocated |
| `000001-899999` | future public registry |
| `900000-989999` | private/local use |
| `990000-999899` | reserved |
| `999900-999999` | development/test |

The exact ranges remain draft until PDv1.0.

## Current boundary

Draft 0.2 can prove deterministic encoding, checksum behavior, synthetic beacon loopback, internal mastering-bundle consistency, catalog/pack invariants, deterministic library/search behavior, and local/private allocation/lookup behavior without hardware. It **cannot** prove optical-drive compatibility, actual CD-RW support, real head-unit timing behavior, physical wallet ergonomics, or analogue-path beacon survival. Those remain explicit physical-test gates.

## Licensing

- software: Apache-2.0;
- specification/documentation: intended CC BY 4.0;
- catalog metadata: intended CC0 1.0.

See `LICENSE` and `LICENSES/README.md`.
