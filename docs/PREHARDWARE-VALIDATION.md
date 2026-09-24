# Pre-hardware validation

PDv1 should spend physical testing time only on questions software cannot answer.

Draft 0.2 therefore adds three software-only gates.

## Exhaustive identity/TOC audit

`pdv1 audit-encoding` enumerates every six-digit value from 000000 through 999999. For every value it:

- calculates the Damm digit;
- produces the eight-track TOC;
- decodes that TOC back to the same identity;
- parses the machine ID back to the same identity;
- checks the namespace partition;
- contributes the complete mapping to a golden SHA-256 digest.

Draft 0.2's reference mapping has SHA-256:

`5048cb0d893e1949573c28ea10ef480bd9dd81bfdda0fdd3afc95e1c1825f618`

The exhaustive audit also establishes the actual valid-ID program-duration extrema: 97 seconds at PD1-010000 and 341 seconds at PD1-999899. The looser 93–345 second figures are only the theoretical envelope of the duration lattice before checksum validity is considered.

## Audio-beacon software loopback

The reference implementation can decode its own DTMF beacon using block-level activity detection and Goertzel frequency analysis. Tests exercise:

- normal generated audio;
- large attenuation and seeded additive noise;
- hard clipping and simple high-pass/low-pass filtering;
- linear resampling to common synthetic capture rates (8, 16, and 48 kHz);
- decoding mono 48 kHz captures and 8/16/24/32-bit uncompressed integer PCM WAV input rather than only the generated 16-bit stereo master;
- the two-frame redundancy rule, including corruption of one repeated frame;
- conflicting individually valid frames fail closed instead of choosing a winner;
- silence rejection.

Malformed or truncated WAV captures are treated as ordinary decode failures rather than escaping the recognition layer, so another valid strong channel can still recognize the disc. These are synthetic tests, not evidence that a particular car's analogue path will preserve the beacon. Physical testing is still required before the waveform can be frozen.

## Virtual build verification

`pdv1 verify-build <bundle>` independently reconstructs the identity from:

- manifest data;
- generated TOC durations;
- CD-TEXT MESSAGE;
- decoded audio beacon.

It also verifies that the generated manifest declares the current PDv1 format/draft, the correct namespace, checksum, total duration, exact duration vector, TOC signature, and beacon profile. This prevents a stale generator or hand-edited manifest from passing merely because the redundant identity channels still agree.

All identity channels that the bundle declares present must agree and the beacon must contain at least two matching checksum-valid frames. CD-TEXT is optional: a bundle that deliberately declares `cd_text: false` must contain no CD-TEXT blocks and is verified through manifest + TOC + beacon instead.

This catches generator regressions before a blank disc is consumed.

Every verified bundle also receives a SHA-256 fingerprint over the exact `manifest.json`, `disc.toc`, and `beacon.wav` bytes using filename/length framing. Test-kit manifests pin that value. Future physical compatibility reports require it so measured evidence cannot become detached from the exact draft mastering artifact that was burned.

## Physical-test-kit generation

`pdv1 build-test-kit` deterministically creates and verifies the Draft 0.2 compatibility bundles required for the first hardware phase, including a controlled same-ID CD-TEXT on/off pair. This closes a software gap in the planned compatibility matrix: CD-TEXT absence can now be intentional rather than simulated by hand-editing a mastering file.

The official `pdv1 burn` path also verifies the bundle and refuses any non-test namespace while the format remains a draft.

## External mastering-tool parser gate

The project also tests the generated mastering syntax against the actual `cdrdao` parser. A dedicated CI job installs cdrdao, regenerates the physical test kit, and runs `toc-info` plus `toc-size` on every variant through `pdv1 cdrdao-preflight`.

This is deliberately a separate layer from `verify-build`: our verifier proves PDv1's own invariants, while cdrdao preflight proves that the external reference mastering tool accepts the file it will later be asked to write. No optical drive is needed for this check.

## Offline vertical integration gate

The test suite also carries one deliberately cross-layer path rather than testing every component only in isolation. It:

1. recognizes a checksum-valid PD identity from deterministic TOC durations;
2. resolves a canonical manifest through an exact provider index into a ready playback plan;
3. feeds the recognized machine ID through the live PD Bridge host runtime;
4. validates the resulting source-switch and execute-plan actions;
5. materializes the resolved track-list plan into the local cache and reads it back through the cache-validation path.

The fixture is entirely synthetic and offline. It does not prove provider authentication/playback, BLE interoperability, vehicle electronics, or audio routing; it proves that the software contracts on either side of those future hardware/network boundaries compose without a hidden side channel.

## What software cannot prove

Draft 0.2 intentionally does **not** claim to establish:

- whether a particular old optical drive accepts the short eight-track layout;
- whether CD-RW works in a particular head unit;
- how an actual head unit rounds or exposes TOC durations;
- whether its CD-TEXT implementation is correct;
- whether the DTMF beacon survives a real radio/DAC/analogue signal path;
- whether cdrdao plus a specific writer produces the intended physical TOC on media (the parser gate only proves the mastering file is accepted and sizeable by cdrdao).

Those remain the purpose of the eventual physical compatibility round.
## Pre-hardware readiness conclusion

The software-only gates needed before the **first controlled physical validation round** are complete for Draft 0.2:

- the complete six-digit identity/TOC space is exhaustively audited and pinned;
- generated mastering bundles and the four-variant physical test kit are independently verified and fingerprinted;
- the reference mastering syntax is exercised by the real `cdrdao` parser in CI;
- beacon decoding covers realistic synthetic capture formats/failures without treating those tests as vehicle evidence;
- catalog, playback-plan, bridge, host-runtime, materialization, compatibility-report, library/site, and pack/wallet artifacts have fail-closed validation at their software boundaries;
- one offline vertical test proves recognition -> exact provider resolution -> host execution -> materialization composition;
- the bounded P1 head-unit/integration-family research sweep is complete, with exact bus/protocol claims left capture-gated;
- `docs/HARDWARE-VALIDATION-RUNBOOK.md` defines the evidence order and stop conditions for the first burns.

The following work is intentionally **not a prerequisite** for first physical validation: P2 vehicle-family expansion, live Spotify/Apple/provider authentication and playback, standalone desktop binaries, hosted-site deployment, physical wallet/label/artwork ergonomics, and speculative vehicle-bus implementations without captures. Those can proceed after real hardware evidence identifies which paths are worth productizing.

Further software-only changes should now require a concrete defect or a new constraint revealed by physical evidence. Otherwise, the next highest-information step is hardware.
