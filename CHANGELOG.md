# Changelog

## 0.2.0a1 — software-complete physical-format validation pass

- Added an exhaustive 1,000,000-ID encode/decode audit with a golden physical-mapping digest.
- Established actual checksum-valid program-duration extrema (97–341 seconds).
- Added a pure-Python Goertzel DTMF decoder for the experimental repeated beacon.
- Added synthetic attenuation, noise, clipping, filtering, redundancy, and silence tests.
- Added `pdv1 verify-build` to independently cross-check manifest, TOC, CD-TEXT, and audio-beacon identity.
- CI now verifies generated bundles on Python 3.11–3.13 and runs the exhaustive encoding audit separately.
- Added a pre-hardware validation document separating software evidence from claims that still require physical testing.

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
