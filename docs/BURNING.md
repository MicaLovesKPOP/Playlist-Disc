# Burning draft discs

PDv1 draft discs require **Disc-At-Once (DAO)** recording because their identity lives in the exact TOC. Track-At-Once software that inserts automatic gaps will produce a different disc.

The reference backend is `cdrdao`.

## Draft safety rule

During Draft 0.2, the official `pdv1 burn` command only accepts:

- a complete bundle that first passes `pdv1 verify-build`; and
- an identity in the development/test namespace `999900-999999`.

Public and private IDs can be generated and verified virtually, but the official CLI will not burn them until the physical format is frozen as PDv1.0.

Direct use of external burning software is outside the tool's control; the project documentation still asks contributors not to create permanent non-test physical IDs during the draft.

## One test bundle

```bash
pdv1 build 999901 --output build/PD1-999901
pdv1 verify-build build/PD1-999901
pdv1 burn build/PD1-999901/disc.toc
```

To intentionally omit optional CD-TEXT while preserving the exact same PD identity/timing:

```bash
pdv1 build 999901 --no-cdtext --output build/PD1-999901-no-cdtext
pdv1 verify-build build/PD1-999901-no-cdtext
```

Verification reports `CD-TEXT: OMITTED (intentional)` and still independently checks the manifest, canonical TOC timing and repeated audio beacon.

## Reference physical-test kit

Before hardware testing:

```bash
pdv1 build-test-kit --output build/test-kit
pdv1 verify-test-kit build/test-kit
```

The generated kit contains:

| Variant | ID | CD-TEXT | Purpose |
| --- | --- | --- | --- |
| `toc-cdtext` | `999901` | yes | baseline TOC behavior with metadata present |
| `toc-no-cdtext` | `999901` | no | same identity, isolates CD-TEXT compatibility |
| `beacon-no-cdtext` | `999902` | no | fallback beacon path without CD-TEXT |
| `cdtext` | `999903` | yes | dedicated CD-TEXT/display observation |

The two `999901` variants deliberately have the same machine identity. Their only intended difference is the optional CD-TEXT mastering layer, allowing an A/B test without changing the PDv1 TOC fingerprint.

When physical work begins, burn only the variants actually needed for the next experiment rather than consuming the entire kit automatically.

## Practical labeling

A handwritten test label is sufficient. Include both the machine ID and variant name, for example:

```text
PD1-999901-7
toc-no-cdtext
```

Avoid adhesive labels in slot-loading automotive mechanisms.
