# Playlist Disc

**Playlist Disc (PDv1)** is an experimental open physical format that turns an ordinary audio CD into a provider-neutral playlist token for older cars.

Insert one physical disc and a compatible vehicle/phone integration can interpret it as an intent such as an artist catalog, a genre/year collection, a community-curated collection, a provider-relative editorial collection, or a private personal playlist.

The same disc is intended to work across different cars and playback services. The disc itself does not contain Spotify, Apple Music, vehicle, or phone-specific identifiers.

> [!WARNING]
> PDv1 is currently **Draft 0.2**. Only IDs `999900-999999` are for physical experiments. Do not mint permanent public music discs until PDv1.0 is frozen after real-world compatibility testing.

## Installation

The project is not published to PyPI yet. Install from a checkout or directly from GitHub; Python 3.11–3.13 is supported. `cdrdao` is only required for actual physical writing, not for generating or validating discs/catalogs.

```bash
pipx install "git+https://github.com/MicaLovesKPOP/Playlist-Disc.git"
pdv1 --help
```

CI builds and installs the wheel on Ubuntu, Windows, and macOS. See `docs/INSTALLATION.md` for development and packaging details.

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
pdv1 recognize --toc 9 48 48 48 48 12 16 40 \\
  --cdtext PD1-999901-7 --require-recognized
pdv1 build-test-kit --output build/test-kit
pdv1 verify-test-kit build/test-kit
# Optional when cdrdao is installed: parse the exact mastering file with the real tool
pdv1 cdrdao-preflight build/test-kit/variants/toc-cdtext/disc.toc
pdv1 validate-catalog catalog
pdv1 check-catalog-evolution /path/to/baseline/catalog catalog
pdv1 search-catalog diagnostic --catalog catalog
pdv1 pack-list catalog
pdv1 pack-show draft-0-2-test-vectors --catalog catalog
pdv1 export-library catalog --output build/library.json
pdv1 build-site catalog --output build/site
pdv1 verify-site build/site
pdv1 bridge-validate tests/vectors/bridge-session.jsonl
pdv1 host-replay tests/vectors/host-adapter-session.jsonl \\
  --plan tests/vectors/host-playback-plan.json
pdv1 materialization-put tests/vectors/materialization-plan.json \\
  --cache ~/.playlistdisc/materializations --scope default \\
  --resource demo:playlist:generated
pdv1 validate-compatibility compatibility
pdv1 export-compatibility compatibility --output build/compatibility.json
pdv1 validate-provider-index tests/vectors/provider-index-demo.json
pdv1 plan-playback 999901 --provider demo
pdv1 scan-local-library ~/Music --output build/local-provider-index.json
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

## Runtime disc recognition

Draft 0.2 now has a conservative runtime recognizer for the three strong identity channels: full checked TOC timing, checksum-valid PDv1 CD-TEXT identifiers, and the repeated audio beacon. One strong channel can recognize a disc; matching channels corroborate it; two independently valid channels that disagree return `conflict` with **no selected identity**. Malformed optional metadata remains diagnostic rather than suppressing another valid channel. Coarse evidence such as track count or total duration is never promoted to identity. See `docs/RECOGNITION.md`.

## Vehicle/phone bridge

Draft 0.2 now includes a transport-neutral logical PD Bridge Draft 0.1 plus a machine-readable schema and reference JSONL transcript. Vehicle adapters normalize disc selection, OEM media controls, source state, and display capabilities; playback hosts return playback state and now-playing metadata. The transcript validator also enforces session-stable capability contracts, strictly monotonic disc-selection counters across remove/reinsert cycles, and unambiguous session+sequence acknowledgements. BLE/USB framing and vehicle wiring remain deliberately separate. See `spec/BRIDGE-PROTOCOL.md`.

## Offline host runtime

Draft 0.2 now has a deterministic host-side state machine between PD Bridge adapter events and provider execution. It deduplicates reconnect/state-sync selections, requests OEM source switching only when the adapter advertises it, forwards normalized media controls only for an active playback context, blocks unavailable/ambiguous plans instead of guessing, and applies configurable disc-removal policy. `pdv1 host-replay` replays a bridge transcript against playback-plan fixtures entirely offline. See `docs/HOST-RUNTIME.md`.

## Draft physical test kit

The software can prepare and verify the future hardware-validation media before a burner or car is involved. Verified bundles receive an exact three-file SHA-256 fingerprint, and test-kit manifests pin that fingerprint so later physical reports can identify precisely what was burned. `pdv1 build-test-kit` generates four verified bundles: a TOC baseline with CD-TEXT, the same ID without CD-TEXT, a beacon-focused no-CD-TEXT variant, and a dedicated CD-TEXT vector. CD-TEXT is explicitly optional and does not change the canonical TOC identity. During Draft 0.2, `pdv1 burn` refuses public/private IDs and only accepts verified test-namespace bundles. When `cdrdao` is installed, `pdv1 cdrdao-preflight` additionally asks the actual mastering tool to parse and size a generated TOC without needing an optical drive; CI runs that external parser over every test-kit variant. See `docs/BURNING.md`.

## Compatibility test preparation

Draft 0.2 includes a structured compatibility schema and deterministic export so eventual physical testing produces comparable evidence instead of free-form anecdotes. The three reference profiles (Alfa 147 ALFA-937 SW3.17, MINI R55 Boost CD, and Citroen C3 RD4) are deliberately still marked `planned`; existing ordinary-radio observations and sourced pre-hardware research are separated from PDv1 test reports. Physical Draft 0.2 reports must use development/test IDs and record the exact verified mastering-bundle SHA-256. Source-typed integration research now covers the Alfa 937 radio/CAN/changer architecture (`docs/research/ALFA-937.md`), the MINI R55 Boost CD / RAD2 K-CAN/MOST architecture (`docs/research/MINI-R55-RAD2.md`), and the Citroen C3 II / RD4-family display, Comfort CAN, changer, and related AEE2004 reverse-engineering groundwork (`docs/research/CITROEN-C3-RD4.md`). See `docs/COMPATIBILITY-TESTING.md`.

## Cross-service resolution core

Draft 0.2 now includes deterministic canonical-recording resolution that can be tested without provider accounts or network access. Provider/local-library indexes map exact MusicBrainz Recording MBIDs and ISRCs to playable resources; explicit provider overrides win, contradictory or duplicate matches stay ambiguous, and missing recordings stay missing. Human title/artist text is never fuzzy identity. This gives future Spotify/Apple/local plugins a common semantic core instead of letting each service silently interpret a physical disc differently. See `docs/RESOLUTION.md`.

## Provider-neutral playback plans

Draft 0.2 can compile any catalog/private disc into one normalized offline playback-plan contract before a streaming SDK, phone UI, BLE transport, or vehicle adapter is involved. Canonical manifests become exact resolved track lists (or honest partial/ambiguous/missing plans), provider-native/federated records become direct resources, artist/album records can fall back to service-neutral MusicBrainz entity lookups, private bindings use the same contract, and diagnostics are explicitly unplayable. Future provider plugins can therefore focus on authentication, lookup/materialization, and actual playback instead of redefining what each physical disc means. See `docs/PLAYBACK-PLANS.md`.

## Local music libraries

With the optional `local-library` extra, Draft 0.2 can scan tagged local audio into the same provider-index contract used by the cross-service resolver. Only MusicBrainz Recording MBIDs and/or ISRCs are accepted as identity; title/artist-only files are skipped rather than fuzzy-matched. Duplicate local representations remain ambiguous until explicitly preferred. The generated index contains local `file://` paths and should remain private. See `docs/LOCAL-LIBRARY.md`.

## Materialization cache contract

Draft 0.2 includes a local cache contract for provider playlists/resources created from deterministic `track_list` playback plans. The complete playback plan is SHA-256 fingerprinted, so changes to canonical membership, provider resolution, coverage, or playback policy automatically stale the cached result. Cache scope is separated per local provider/account profile using a hashed scope; no OAuth tokens are stored. Direct provider resources and unresolved entity lookups are deliberately not cached by this generic layer. See `docs/MATERIALIZATION-CACHE.md`.

## Public-ID evolution guard

Draft 0.2 includes a catalog-evolution guard for the future permanent public registry. Public proposals remain freely editable while `draft`; after activation, identity-defining fields cannot be deleted, renumbered, or silently repurposed. Snapshot canonical membership is locked, while provider resolution metadata and living-collection membership may evolve within the original semantic scope. CI compares pull requests (and main pushes) against their baseline commit. Permanent public activation itself remains disabled until PDv1.0. See `docs/CATALOG-EVOLUTION.md`.

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
- `compatibility/` — vehicle/head-unit profiles, sourced research evidence, and measured results
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
