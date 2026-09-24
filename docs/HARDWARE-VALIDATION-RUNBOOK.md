# First hardware validation runbook

This is the handoff from Draft 0.2 software validation to physical evidence.

The goal of the first hardware round is **not** to prove every vehicle integration at once. It is to answer the questions software cannot answer while keeping every observation tied to an exact mastering bundle.

## 1. Freeze the software input

Before generating media:

```bash
git status --short
git rev-parse HEAD
pdv1 build-test-kit --output build/test-kit
pdv1 verify-test-kit build/test-kit
```

Record the Git commit used for the session and preserve `build/test-kit/test-kit.json`. Do not edit a generated bundle after recording its fingerprint.

For every variant that may be burned, independently run:

```bash
pdv1 verify-build build/test-kit/variants/toc-cdtext
pdv1 verify-build build/test-kit/variants/toc-no-cdtext
pdv1 verify-build build/test-kit/variants/beacon-no-cdtext
pdv1 verify-build build/test-kit/variants/cdtext
```

If `cdrdao` is installed, also run `pdv1 cdrdao-preflight` on each exact `disc.toc`. A parser failure stops the physical session until the software/mastering issue is understood.

## 2. Reference variants

| Variant | Machine identity | CD-TEXT | Primary question |
| --- | --- | --- | --- |
| `toc-cdtext` | PD1-999901-7 | yes | Does the normal Draft 0.2 disc load/play, and what TOC/timing/metadata is visible? |
| `toc-no-cdtext` | PD1-999901-7 | no | Does removing optional CD-TEXT change behavior while keeping the physical PD identity the same? |
| `beacon-no-cdtext` | PD1-999902-5 | no | Does the repeated audio beacon survive the real optical/audio/capture path? |
| `cdtext` | PD1-999903-0 | yes | Dedicated CD-TEXT/display observation when more isolation is useful. |

The two `999901` variants are an intentional A/B pair. Never compare them without also recording their distinct `bundle_sha256` values from `test-kit.json`.

## 3. Media and writer order

Start with the least exotic condition:

1. finalized ordinary **CD-R**;
2. one known writer, DAO mode, known write speed if the tool exposes it;
3. only after the CD-R baseline is understood, repeat a useful variant on **CD-RW**;
4. only introduce a second writer when checking writer-specific behavior is actually useful.

Do not multiply writer × media × vehicle combinations before a baseline has loaded successfully.

Every physical report should record, when known:

- media type and nominal capacity;
- blank brand/product;
- finalized state;
- CD-TEXT state;
- writer model;
- DAO mode;
- write speed;
- test-kit variant;
- exact bundle SHA-256.

## 4. First-disc decision tree

Burn `toc-cdtext` on CD-R first.

For each head unit:

### A. Basic load

Observe whether the disc:

- is accepted rather than ejected/erroring;
- exposes eight tracks;
- allows selecting/advancing through those tracks;
- plays audio normally.

If it cannot load at all, do **not** immediately burn every other variant. Try `toc-no-cdtext` only if separating a CD-TEXT parser issue from a TOC/layout issue is useful. If both same-ID variants fail similarly, further metadata variants on that unit are low-value until the physical layout/media problem is understood.

### B. Timing / TOC behavior

If it loads, record what the user-facing unit exposes:

- total disc duration, if shown;
- per-track durations, if shown;
- exact versus rounded/offset timing;
- track count;
- any diagnostic or bus-observed disc timing information.

Do not infer a full TOC from a displayed total duration.

### C. CD-TEXT A/B

Compare `toc-cdtext` with `toc-no-cdtext` on the same head unit and media type.

Record whether CD-TEXT is:

- displayed;
- ignored;
- garbled;
- not observable.

If both variants otherwise behave identically, that is useful evidence. It is not necessary to keep repeating the dedicated `cdtext` variant unless the display behavior needs a cleaner isolated observation.

### D. Cold start and reinsert

For a variant that loads reliably:

1. leave the disc inserted;
2. perform the normal vehicle/head-unit power-off and cold-start sequence;
3. record whether the disc is accepted/resumed normally;
4. eject and reinsert it;
5. record whether behavior changes.

Do not substitute an ignition-cycle assumption for an actually observed cold start.

## 5. Beacon test

Use `beacon-no-cdtext` only after ordinary CD playback is established.

Capture audio as close to the real integration point as is practical. Preserve the original capture file before processing it.

Run the project decoder against the capture. Record separately:

- whether the beacon is audible;
- whether the reference decoder obtains two matching checksum-valid frames;
- capture format/sample rate/channel arrangement if known;
- any gain, filtering, resampling, Bluetooth/AUX or analogue path involved.

An audible beacon that does not decode is a valid result. Synthetic software stress tests are not a reason to reinterpret a physical failure as success.

## 6. CD-RW test

CD-RW is a compatibility question, not a prerequisite for PDv1.

If CD-R works, burn the **same exact variant bundle** to finalized CD-RW and repeat the minimum load/track/cold-start observations. This isolates media type from logical PD identity.

If the head unit rejects CD-RW, record the negative result and move on. Do not redesign the physical format merely to force CD-RW support.

## 7. Vehicle-bus observation

Bus/CAN/MOST/VAN work comes **after** the normal head-unit behavior is known.

When capture equipment is available:

1. establish a quiet baseline with no disc action;
2. insert/eject the same known test variant;
3. change tracks in a controlled sequence;
4. compare CD-TEXT on/off only when useful;
5. preserve raw captures before interpreting them.

Record only what was actually observed. Related-platform IDs from the research notes are hypotheses for finding traffic, not target-car facts.

For the three reference anchors:

- **Alfa 147 / ALFA-937:** investigate B-CAN versus the dedicated changer interface separately.
- **MINI R55 / RAD2:** keep K-CAN observation separate from MOST; OBD diagnostics are not assumed to be a MOST sniffer.
- **Citroen C3 II / RD4:** related AEE2004 frame classes are search hypotheses only until the target C3 confirms them.

## 8. Minimum report after each meaningful condition

Put measured results in the matching profile under `compatibility/vehicles/*.yaml`, or submit the compatibility issue form.

A structured report must contain:

- unique `report_id`;
- date;
- exact `disc_machine_id`;
- exact 64-character `bundle_sha256`;
- media type, finalized=true, and CD-TEXT state;
- results for load, tracks, TOC duration, CD-TEXT, cold start, reinsert, vehicle-bus TOC, and audio beacon.

Use `not_tested` or `not_observable` rather than filling gaps with inference.

When repeated attempts matter, record `attempts.total` and `attempts.successful_loads` instead of turning intermittent behavior into a single pass/fail anecdote.

After editing reports:

```bash
pdv1 validate-compatibility compatibility
pdv1 export-compatibility compatibility --output build/compatibility.json
```

## 9. Recommended first-session order

The highest-information first session is:

1. generate and verify the full test kit once;
2. burn `toc-cdtext` to CD-R;
3. test basic load/tracks/timing on the three reference head units available;
4. burn `toc-no-cdtext` only for the CD-TEXT A/B question or to diagnose a baseline failure;
5. run cold-start/eject-reinsert on units that load reliably;
6. burn/test `beacon-no-cdtext` where an actual capture path is available;
7. test CD-RW only after CD-R behavior is known;
8. begin target-vehicle bus captures only after ordinary optical behavior has been recorded.

This order deliberately front-loads evidence that can invalidate many later tests.

## 10. Stop conditions

Stop a branch of testing when:

- the disc cannot be read reliably enough to reach the question that variant is meant to answer;
- a lower-layer failure makes later metadata/beacon conclusions meaningless;
- the exact bundle/media/writer provenance is no longer known;
- the experiment would require guessing a vehicle-bus electrical detail;
- repeated testing is producing the same result without reducing uncertainty.

Preserve negative results. A reliable incompatibility is more useful than an improvised workaround that makes the evidence incomparable.

## 11. What not to freeze yet

Do not freeze PDv1.0 solely because the first disc works.

Physical evidence still needs to inform:

- practical TOC tolerance language;
- final audio-beacon profile;
- CD-R/CD-RW compatibility wording;
- which recognition channels are realistically available on representative legacy players.

Permanent public IDs remain closed until those questions are settled.
