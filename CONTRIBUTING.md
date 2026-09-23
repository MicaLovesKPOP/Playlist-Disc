# Contributing

Playlist Disc is currently a physical-format draft. Contributions that improve tests, documentation, catalog modeling, burner compatibility, or measured vehicle behavior are welcome.

## Important draft rule

Do not submit permanent music entries in `000001-899999` yet. Until PDv1.0 is frozen, physical test discs belong in `999900-999999`.

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

Run:

```bash
python -m pip install -e '.[dev]'
pdv1 validate-catalog catalog
pdv1 export-catalog catalog --output /tmp/catalog.json
pytest
```

Export intentionally refuses an invalid registry.

## Compatibility reports

Record the exact radio/head-unit family and firmware when known, but do not include VINs, registration numbers, addresses, or other unnecessary personal identifiers.
