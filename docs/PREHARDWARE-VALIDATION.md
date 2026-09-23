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
- large attenuation;
- additive seeded noise;
- hard clipping;
- simple high-pass/low-pass filtering;
- the two-frame redundancy rule;
- silence rejection.

These are synthetic tests, not evidence that a particular car's analogue path will preserve the beacon. Physical testing is still required before the waveform can be frozen.

## Virtual build verification

`pdv1 verify-build <bundle>` independently reconstructs the identity from:

- manifest data;
- generated TOC durations;
- CD-TEXT MESSAGE;
- decoded audio beacon.

All channels must agree and the beacon must contain at least two matching checksum-valid frames.

This catches generator regressions before a blank disc is consumed.

## What software cannot prove

Draft 0.2 intentionally does **not** claim to establish:

- whether a particular old optical drive accepts the short eight-track layout;
- whether CD-RW works in a particular head unit;
- how an actual head unit rounds or exposes TOC durations;
- whether its CD-TEXT implementation is correct;
- whether the DTMF beacon survives a real radio/DAC/analogue signal path;
- whether cdrdao plus a specific writer produces the intended physical TOC on media.

Those remain the purpose of the eventual physical compatibility round.
