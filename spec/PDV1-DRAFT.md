# Playlist Disc v1 — Draft 0.2

**Status:** experimental. Do not allocate permanent public music IDs from this document yet.

## 1. Scope

PDv1 defines a provider-neutral physical token encoded as an ordinary CD-DA disc. The disc identifies a musical intent or catalog record. It does **not** encode a streaming-service URL, vehicle type, phone type, or Bluetooth implementation.

A vehicle adapter resolves a physical disc to a PD identifier. Playback software then resolves that identifier to the user's chosen provider or local library.

## 2. Canonical identifier

A PDv1 identity is a six-digit decimal number and format version:

`PD1-123456`

The machine form appends one Damm check digit calculated over the seven decimal digits `1` + `123456`:

`PD1-123456-3`

The check digit is validation data and is not part of the six-digit allocation namespace.

### 2.1 Draft namespace

- `000000`: invalid; never allocated.
- `000001-899999`: future public registry.
- `900000-989999`: permanently local/private use.
- `990000-999899`: reserved.
- `999900-999999`: development and test vectors.

Only the development range should be burnt while PDv1 is still a draft.

## 3. Physical disc profile

A conforming draft disc is:

- 12 cm CD-R or CD-RW capable of CD-DA recording;
- one finalized, single-session CD-DA session;
- exactly eight audio tracks;
- written in Disc-At-Once mode;
- no data track and no multisession data;
- no required adhesive label or specialist blank media.

CD-R is the interoperability default. Finalized CD-RW is permitted for development and reusable personal discs, with the understanding that legacy-player compatibility may be lower.

## 4. TOC encoding

Track 1 is the format marker and beacon carrier:

`T1 = 9 seconds`

Tracks 2 through 7 encode the six ID digits. Track 8 encodes the Damm check digit. Every encoded digit `d` has duration:

`T = 12 + 4*d seconds`

Therefore legal digit-track durations are exactly:

`12, 16, 20, 24, 28, 32, 36, 40, 44, 48 seconds`

Example `PD1-123456-3`:

`9, 16, 20, 24, 28, 32, 36, 24 seconds`

The raw duration lattice has a theoretical 93–345 second envelope. Exhaustive Draft 0.2 validation of all one million six-digit identities shows that checksum-valid identities actually span 97 seconds (PD1-010000) through 341 seconds (PD1-999899).

### 4.1 Fuzzy readers

Implementations that receive integer/rounded duration reports may decode to the nearest legal digit duration only when the configured tolerance is strictly less than two seconds. Exact-TOC readers should use exact durations.

The Damm check must validate before a TOC-derived identity is considered strong evidence. Because legal digit durations are four seconds apart, any tolerance below two seconds preserves a unique nearest lattice point.

### 4.2 Reference mapping audit

The reference implementation exhaustively round-trips every identity 000000–999999 and hashes the complete mapping. Draft 0.2's golden mapping digest is:

`5048cb0d893e1949573c28ea10ef480bd9dd81bfdda0fdd3afc95e1c1825f618`

Changing this digest before PDv1.0 is permitted only as an explicit physical-format revision, never accidentally.

## 5. CD-TEXT

CD-TEXT is an optional redundant identity channel. Lack of CD-TEXT does not make a disc nonconforming.

The reference generator writes conservative ASCII CD-TEXT:

- global `TITLE`: short human title;
- global `PERFORMER`: `PLAYLIST DISC`;
- global `MESSAGE`: machine ID, e.g. `PD1-123456-3`;
- track title/performer fields repeated for compatibility with authoring tools.

PDv1 does not manufacture ISRC or UPC/EAN identifiers solely to carry PD metadata.

## 6. Audio beacon

Draft 0.2 retains the **experimental** `dtmf-draft-a` fallback beacon in the first four seconds of track 1. The waveform is not frozen until physical analogue-path testing.

Frame symbols are:

`* V DDDDDD C #`

where `V` is version (`1`), `DDDDDD` is the six-digit identity, and `C` is the Damm digit. The reference waveform sends two identical frames. Track 1 remains exactly nine seconds long.

Strong beacon recognition requires at least two matching, checksum-valid frames. The reference decoder uses activity segmentation plus Goertzel analysis and is tested against synthetic attenuation, noise, clipping, and basic band-limiting. Those software tests do not replace physical car-path validation.

## 7. Recognition safety

PD integrations must fail open as ordinary CD players. An uncertain disc must never be hijacked as a Playlist Disc.

Strong evidence includes:

- exact canonical eight-track TOC plus valid check digit;
- valid PDv1 CD-TEXT machine ID plus check digit;
- two matching valid audio-beacon frames.

Track count, total duration, or a vaguely similar TOC alone are not sufficient for automatic activation.

The Draft 0.2 reference recognizer implements these rules directly. Any one accepted strong channel can identify a disc. If multiple accepted channels resolve to the same identity they are combined as corroborating evidence. If two checksum-valid/strong channels resolve to different identities, recognition returns a conflict and **no disc identity**; implementations must fail open rather than pick a preferred channel. A malformed optional channel may be recorded diagnostically while another independent strong channel remains usable.

## 8. Catalog semantics

A physical PD ID identifies a musical intent, not a streaming provider, except when a record explicitly declares itself provider-native.

Public records classify independent axes including:

- definition type: artist catalog, album, canonical manifest, ruleset, provider-native resource, diagnostic;
- provenance: project, community, artist, label, provider;
- lifecycle: snapshot or living;
- portability: canonical, federated, provider-native;
- playback: ordered/shuffle, first/random/resume, repeat policy.

Provider bindings are mutable realization details. The semantic identity of an allocated public disc is immutable.

## 9. Portability classes

**Canonical:** service-neutral content definition. Provider plugins resolve the same intended recordings or artist/release entities.

**Federated:** service-relative concept where each service may supply a deliberately equivalent but non-identical editorial collection.

**Provider-native:** explicitly identifies a resource native to one provider. Other providers may be unsupported or offer declared fallbacks.

No provider receives its own numeric namespace.

## 10. Catalog immutability

Once PDv1.0 allocates a public ID, it is never recycled. Provider links, tags, maintainers, and availability may change; the underlying semantic identity must not silently change. Retired entries remain in the registry and may point to a successor.

## 11. Software verification

A generated mastering bundle should be verifiable before consuming optical media. The reference `verify-build` operation reconstructs identity independently from the manifest, TOC durations, CD-TEXT message, and decoded repeated beacon. All channels must agree.

## 12. Draft freeze criteria

PDv1.0 is not frozen until physical test discs have been checked in multiple burners and legacy car players, including at minimum:

- ordinary modern CD-R;
- at least one CD-RW where supported;
- CD-TEXT on/off;
- exact and rounded TOC reporting;
- the eight-track short-disc layout;
- audio-beacon survival through a real analogue path;
- deterministic regeneration of the same physical TOC.

See `docs/PREHARDWARE-VALIDATION.md` for what Draft 0.2 proves in software and what remains deliberately unclaimed.
