# ADR 0010: Physical compatibility evidence pins exact mastering bundles

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-24

## Context

A logical PD machine ID identifies the disc's semantic/timing identity, not every byte used to master an experimental disc. Draft testing intentionally creates variants with the same PD ID but different optional CD-TEXT, and the draft beacon/generator may still evolve before PDv1.0.

If a compatibility report records only `PD1-999901-7`, a later reader may not know which exact mastering artifact was burned.

## Decision

Every verified build exposes a SHA-256 fingerprint over the exact bytes of `manifest.json`, `disc.toc`, and `beacon.wav`, framed with each filename and byte length.

Generated physical-test-kit manifests pin that fingerprint for every variant. Draft physical compatibility reports require the same `bundle_sha256`; an optional `test_variant` can additionally carry a human-friendly kit name.

The bundle fingerprint is provenance, not a replacement for PD identity. Changing harmless formatting intentionally changes the exact-artifact hash while leaving the PD machine ID untouched.

## Consequences

- Physical test evidence can be tied to exactly what was burned.
- Same-ID A/B variants remain distinguishable.
- Draft generator/waveform changes cannot silently inherit older physical results.
- Reproducing a byte-identical bundle can be checked independently of semantic identity.
- PDv1.0 may later define a more stable release-artifact scheme; Draft 0.2 deliberately favors exact evidence provenance.
