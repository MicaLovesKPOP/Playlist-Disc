# Static library, search, packs, and wallets

Draft 0.2 includes provider-neutral library tooling that can be validated entirely in software. It deliberately stops short of a hosted web application or provider login flow.

## Validate first

All library-facing commands operate on the same source catalog and should start from a valid registry:

```bash
pdv1 validate-catalog catalog
```

Catalog validation includes disc entries, canonical manifests, and pack cross-references.

## Search

```bash
pdv1 search-catalog "audio beacon" --catalog catalog
pdv1 search-catalog diagnostic --tag beacon --catalog catalog --json
```

Search uses case-insensitive AND-token substring matching over semantic catalog metadata: IDs, titles, definition/provenance fields, lifecycle/portability/playback values, tags, provider bindings, and notes. Results are deterministic and may be filtered by status or required tags.

Search refuses an invalid catalog rather than indexing broken source data.

## Packs and wallet slots

```bash
pdv1 pack-list catalog
pdv1 pack-show draft-0-2-test-vectors --catalog catalog
```

A source pack is an ordered list of existing IDs. `pack-show` resolves that order into 1-based wallet slots and adds the referenced disc's machine ID and display metadata.

Pack capacity is descriptive organization data, not part of PDv1's physical identity encoding.

## Static-library export

```bash
pdv1 export-library catalog --output build/library.json
```

The generated `PDv1-library` JSON contains:

- validated catalog entries with deterministic machine/TOC metadata;
- validated packs with resolved wallet slots;
- simple facets for status, definition type, portability, entry tags, and pack tags.

This file is designed as deterministic input for a future static website, offline browser, mirror, or desktop application. Generated JSON is not source-of-truth data and should not be hand-edited.

`pdv1 export-catalog` remains available for clients that need only disc entries.

## Deliberate boundaries

This work does not claim anything about physical wallet ergonomics, label readability, optical compatibility, vehicle behavior, streaming-provider availability, or bridge behavior. Those are separate layers. It also introduces no telemetry, accounts, hosted search service, JavaScript framework, or provider credentials.
