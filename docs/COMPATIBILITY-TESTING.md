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

## Coverage planning

The three reference profiles are architectural anchors, not the breadth limit. Broader desk research is tracked by reusable head-unit and integration family in `docs/COMPATIBILITY-COVERAGE.md`. A family research note can cover many vehicle models without claiming that each one has been physically tested.

Do not create concrete compatibility profiles merely to mirror commercial application lists. Add a profile when there is a specific head-unit/vehicle target that can eventually receive a structured physical report. The coverage plan defines P1/P2 research lanes and a stop rule so pre-hardware research spans the important direct-changer, vehicle-network, optical, and aftermarket integration classes without turning into an endless model catalog.

The first family-level note is `docs/research/VAG-LEGACY-QUADLOCK.md`. It maps reusable VAG changer/network architectures and explicit exclusions without converting those families into unearned physical-compatibility profiles.

## Test reports

A physical report records:

- exact PDv1 machine ID used;
- exact mastering-bundle SHA-256 printed by `pdv1 verify-build` (and optional test-kit variant name);
- CD-R vs CD-RW, finalization and CD-TEXT state;
- optional media brand/product and writer/speed;
- load/track-access behavior;
- TOC timing visibility/rounding;
- CD-TEXT behavior;
- cold-start and eject/reinsert behavior;
- whether TOC information is observed on the vehicle bus;
- audio-beacon outcome;
- optional repeated-attempt counts.

During Draft 0.2, physical reports must use IDs in the development/test namespace `999900-999999`. A report also requires the 64-character `bundle_sha256` of the exact three-file mastering bundle. This distinguishes experiments even when the logical PD ID is intentionally the same (for example the `999901` CD-TEXT on/off A/B pair) and pins evidence if a draft generator later changes.

## Unknown and negative results

Do not guess. `not_tested` and `not_observable` are valid outcomes. A reliable negative result is useful compatibility data.

## Minimum eventual matrix

For a reference head unit, aim to cover ordinary finalized CD-R, CD-RW where plausible, CD-TEXT on/off, cold start with the disc already inserted, eject/reinsert, visible timing behavior, any vehicle-network TOC exposure, and the analogue beacon path if relevant.

This schema does not claim that those tests have been performed; it only makes sure future results are comparable and reviewable.

## Pre-hardware research versus measured compatibility

A profile may include `research_evidence` sourced from owner manuals, service documentation, component vendors, standards/technical references, or community reverse engineering. That evidence is for planning only and does not change a profile from `planned` to `partial`/`tested`.

For related-platform reverse engineering, record exactly which source vehicles/protocol family produced the observation. Do not promote a CAN identifier or protocol detail into target-car fact until the target profile has a capture/report supporting it.
