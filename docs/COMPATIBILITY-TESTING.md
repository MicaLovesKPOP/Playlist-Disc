# Compatibility profiles and physical-test reports

Compatibility testing is deliberately structured before any blank media is consumed.

The repository stores **head-unit/vehicle profiles**, not personal vehicle records. Do not include VINs, registration numbers, addresses, account identifiers, or other unnecessary personal data.

## Validate and export

```bash
pdv1 validate-compatibility compatibility
pdv1 export-compatibility compatibility --output build/compatibility.json
```

The source of truth lives in `compatibility/vehicles/*.yaml`. The generated JSON snapshot is deterministic and intended for a future compatibility browser or static-site integration.

## Profile lifecycle

- `planned`: test matrix defined, no physical PDv1 report recorded yet.
- `partial`: at least one structured test report exists, but the profile is not considered broadly characterized.
- `tested`: at least one report exists and maintainers consider the current matrix sufficiently exercised.

Draft 0.2 repository profiles for the Alfa 147 ALFA-937 SW3.17, MINI R55 Boost CD, and Citroen C3 RD4 remain `planned`. Existing ordinary-radio observations are kept separate from PDv1 test results.

## Research evidence

A profile may contain `research_evidence` gathered before hardware testing. Each item records a bounded claim, its design implication, a topic, and a structured source with source type, publisher, HTTPS URL, access date, and optional locator. The compatibility export counts these items separately from physical reports.

Research never changes a profile from `planned` to `partial`/`tested`, and it must not be rewritten as if it were a measured result. Prefer manufacturer/service documentation and component-vendor documentation. Mirrored manuals must be labeled as mirrors; community material may document a hypothesis or compatibility warning but should remain visibly lower-authority.

The first populated research set is `docs/research/ALFA-937.md`, mirrored into the Alfa 937 profile so future compatibility tooling can consume the same evidence machine-readably. Its conclusions deliberately stop before CAN IDs, changer frames, bus speeds, or other facts that require captures.

## Test reports

A physical report records:

- exact PDv1 machine ID used;
- CD-R vs CD-RW, finalization and CD-TEXT state;
- optional media brand/product and writer/speed;
- load/track-access behavior;
- TOC timing visibility/rounding;
- CD-TEXT behavior;
- cold-start and eject/reinsert behavior;
- whether TOC information is observed on the vehicle bus;
- audio-beacon outcome;
- optional repeated-attempt counts.

During Draft 0.2, physical reports must use IDs in the development/test namespace `999900-999999`.

## Unknown and negative results

Do not guess. `not_tested` and `not_observable` are valid outcomes. A reliable negative result is useful compatibility data.

## Minimum eventual matrix

For a reference head unit, aim to cover ordinary finalized CD-R, CD-RW where plausible, CD-TEXT on/off, cold start with the disc already inserted, eject/reinsert, visible timing behavior, any vehicle-network TOC exposure, and the analogue beacon path if relevant.

This schema does not claim that those tests have been performed; it only makes sure future results are comparable and reviewable.

## Pre-hardware research versus measured compatibility

A profile may include `research_evidence` sourced from owner manuals, service documentation, component vendors, standards/technical references, or community reverse engineering. That evidence is for planning only and does not change a profile from `planned` to `partial`/`tested`.

For related-platform reverse engineering, record exactly which source vehicles/protocol family produced the observation. Do not promote a CAN identifier or protocol detail into target-car fact until the target profile has a capture/report supporting it.
