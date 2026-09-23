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
