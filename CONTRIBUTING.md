# Contributing

Playlist Disc is currently a physical-format draft. Contributions that improve tests, documentation, catalog modeling, burner compatibility, or measured vehicle behavior are welcome.

## Important draft rule

Do not submit permanent music entries in `000001-899999` yet. Until PDv1.0 is frozen, physical test discs belong in `999900-999999`.

## Catalog changes

Every catalog entry must:

- use a six-digit string ID;
- validate against `catalog/schema/disc.schema.json`;
- declare lifecycle, portability, provenance, and playback behavior explicitly;
- avoid pretending that provider-relative content is canonical;
- avoid copyrighted artwork/audio in the repository.

Run:

```bash
python -m pip install -e '.[dev]'
pdv1 validate-catalog catalog
pytest
```

## Compatibility reports

Record the exact radio/head-unit family and firmware when known, but do not include VINs, registration numbers, addresses, or other unnecessary personal identifiers.
