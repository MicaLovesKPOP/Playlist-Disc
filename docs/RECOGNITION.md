# Runtime disc recognition

The mastering verifier proves that generated artifacts agree before burning. Runtime recognition is a different problem: an adapter may observe only some channels, may see rounded timing, or may receive a damaged/irrelevant optional metadata field.

`playlistdisc.recognition` turns those observations into one explicit result: `recognized`, `unknown`, or `conflict`.

## CLI

```bash
pdv1 recognize \
  --toc 9 48 48 48 48 12 16 40 \
  --cdtext PD1-999901-7 \
  --require-recognized
```

An adapter with an analogue beacon capture can additionally pass `--beacon-wav capture.wav`.

## Strong channels

The reference recognizer only accepts evidence that already satisfies the Draft 0.2 strong-evidence rules:

- **TOC:** all eight observed track durations must decode to the duration lattice and pass the Damm check. An explicitly configured tolerance below two seconds may accommodate a legacy reader that rounds durations.
- **CD-TEXT:** an observed field must contain a syntactically valid `PD1-DDDDDD-C` machine ID whose check digit validates.
- **Audio beacon:** the existing decoder must find the required repeated matching checksum-valid frames.

Track count, total disc duration, or a few matching track lengths are not accepted as identity evidence.

## Fail-open combination

One valid strong channel is sufficient because each channel contains the full checked identity. More than one matching channel is useful corroboration.

If two valid channels identify different discs, the result is `conflict` and contains **no chosen identity**. The recognizer never resolves that situation by priority such as 'trust TOC over CD-TEXT'. That makes corruption or a future integration bug visible instead of silently selecting music.

A malformed optional channel does not invalidate a different strong channel. For example, a valid TOC plus unrelated ordinary CD-TEXT still recognizes from the TOC while preserving a diagnostic CD-TEXT error.

## Result format

The packaged `PDv1-recognition` JSON schema carries:

- status;
- recognized ID/machine ID only when status is `recognized`;
- deduplicated strong evidence channels and their machine IDs;
- diagnostic errors from invalid supplied observations.

This is suitable as the disc-recognition input to a future vehicle adapter/PD Bridge implementation.

## Hardware boundary

Software can prove that the aggregation logic is conservative; it cannot prove which observations any particular head unit exposes. The reference-vehicle compatibility phase still needs to establish whether TOC, CD-TEXT, or analogue beacon evidence is actually available in Shadow, Choco, Misty, and other cars.
