# Contributing

GitHub provides structured issue forms for bugs, compatibility observations, and catalog proposals, plus a pull-request checklist. Use the closest template so reports contain the evidence reviewers need without leaking personal data or credentials.

Playlist Disc is currently a physical-format draft. Contributions that improve tests, documentation, catalog modeling, burner compatibility, or measured vehicle behavior are welcome.

## Important draft rule

Do not activate permanent music entries in `000001-899999` yet. Draft public proposals may be modeled in that range, but repository validation rejects `active`/`retired` permanent public records until PDv1.0 is frozen. Physical test discs belong in `999900-999999`.

## Catalog changes

Every catalog entry must:

- use a six-digit string ID;
- live at `catalog/discs/<first3>/<id>.yaml`;
- validate against `catalog/schema/disc.schema.json`;
- declare lifecycle, portability, provenance, and playback behavior explicitly;
- avoid pretending provider-relative content is canonical;
- avoid copyrighted artwork/audio in the repository.

Canonical explicit track collections additionally use:

`catalog/manifests/<first3>/<id>.json`

and must validate against `catalog/schema/canonical-manifest.schema.json`.

For canonical recording rows, use a MusicBrainz Recording MBID and/or ISRC rather than artist/title text as identity. Human metadata can be supplied as hints for reviewers.

Provider-native entries must say so. Federated entries must provide multiple declared equivalent/best-available bindings. Numeric ID ranges do not encode providers or categories.

## Pack changes

Packs live at `catalog/packs/<slug>.yaml` and validate against `catalog/schema/pack.schema.json`.

A pack is curation only: it must reference existing catalog IDs rather than copying or redefining disc semantics. Keep its ID list ordered, duplicate-free, and within the declared 12/24/48/96 wallet capacity. During Draft 0.2, do not create permanent public music packs that imply the still-unopened public ID registry is frozen.

Run:

```bash
python -m pip install -e '.[dev]'
pdv1 validate-catalog catalog
# On an existing public registry, also compare against the target branch baseline:
pdv1 check-catalog-evolution /path/to/baseline/catalog catalog
pdv1 export-catalog catalog --output /tmp/catalog.json
pdv1 export-library catalog --output /tmp/library.json
pdv1 pack-list catalog
pytest
python -m build
```

Exports intentionally refuse an invalid registry.

## Compatibility reports

Record the exact radio/head-unit family and firmware when known, but do not include VINs, registration numbers, addresses, or other unnecessary personal identifiers.
